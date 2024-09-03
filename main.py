import sys
import json
from time import sleep

from PySide6.QtCore import QSize, Qt, QThreadPool, Slot, Signal, QObject
from PySide6.QtGui import (
    QAction,
    QIcon,
    QPixmap,
    QFont,
    QShortcut,
    QKeySequence,
    QIntValidator,
    QKeyEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy,
    QLineEdit,
)

from controllers.sat_controller import ElectronicLoadController
from controllers.arduino_controller import ArduinoController
from models.test_file_model import *
from widgets.channel_monitor import ChannelMonitor
from widgets.steps_table import StepsTable
from widgets.data_input_dialog import DataInputDialog
from utils.delay_manager import DelayManager
from utils.enums import *
from utils.monitor_worker import MonitorWorker


class CurrentTestSetup:
    active_test: Test = None
    serial_number: str = None
    operator_name: str = ""
    channels: list[ChannelMonitor] = []
    serial_number_changed: bool = False
    is_single_step: bool = False
    selected_step_index: int = -1
    active_input_source: int = 0
    current_index: int = 0
    test_result_data = dict()
    test_sequence_status: list[bool] = []

    def set_next_serial_number(self):
        self.serial_number = str(int(self.serial_number) + 1).zfill(8)

    def get_active_channel_ids(self) -> list[int]:
        return list(map(lambda channel: channel.id, self.active_test.active_channels))


class WorkerSignals(QObject):
    update_output = Signal()


class MainWindow(QMainWindow):
    def __init__(self, test_setup: CurrentTestSetup):
        super().__init__()
        self.test_setup = test_setup
        self.state = TestState.NONE
        self.sat_controller = ElectronicLoadController()
        self.arduino_controller = ArduinoController()
        self.thread_pool = QThreadPool()
        self.worker_signals = WorkerSignals()
        self.delay_manager = DelayManager()
        self.monitoring_worker = None
        self.delay_manager.delay_completed.connect(self.on_delay_completed)
        self.delay_manager.remaining_time_changed.connect(self.update_timer)
        self.worker_signals.update_output.connect(self.update_output_display)

        self.setMinimumSize(QSize(1200, 600))
        self.setWindowTitle(
            f"CEBRA - {self.sat_controller.inst_id}"
            if self.sat_controller.conn_status
            else "CEBRA - IT8700 Sem Conexão"
        )

        # Shortcuts
        self.start_shortcut = QShortcut(QKeySequence("Alt+R"), self)
        self.pause_shortcut = QShortcut(QKeySequence("Alt+P"), self)
        self.stop_shortcut = QShortcut(QKeySequence("Alt+S"), self)
        self.single_run_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.start_shortcut.activated.connect(self.start_test_sequence)
        self.pause_shortcut.activated.connect(self.pause_test_sequence)
        self.stop_shortcut.activated.connect(self.cancel_test_sequence)
        self.single_run_shortcut.activated.connect(self.handle_single__run)

        # Actions
        self.open_file_action = QAction(
            QIcon("assets/icons/file_open.png"), "Abrir Arquivo", self
        )
        self.open_file_action.triggered.connect(self.open_test_file)

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("&Arquivo")
        file_menu.addAction(self.open_file_action)

        # Logo
        logo = QLabel()
        logo.setPixmap(QPixmap("assets/logo.png"))
        logo.setScaledContents(True)
        logo.setFixedSize(150, 100)

        # Labels
        group_label = QLabel("Grupo: ")
        model_label = QLabel("Modelo: ")
        sn_label = QLabel("Nº de Serie: ")
        operator_label = QLabel("Operador: ")
        self.status_label = QLabel("---")

        self.group_value = QLineEdit()
        self.model_value = QLineEdit()
        self.sn_value = QLineEdit()
        self.operator_name = QLineEdit()

        label_font = QFont("Arial", 16)
        group_label.setFont(label_font)
        model_label.setFont(label_font)
        sn_label.setFont(label_font)
        operator_label.setFont(label_font)
        self.status_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.status_label.setContentsMargins(50, 0, 50, 0)
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.group_value.setReadOnly(True)
        self.group_value.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.model_value.setReadOnly(True)
        self.model_value.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sn_value.setValidator(QIntValidator(0, 99999999, self))
        self.sn_value.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.operator_name.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.sn_value.textEdited.connect(self.sn_changed)
        self.operator_name.textEdited.connect(self.op_name_changed)

        # Test Details Layout
        info_panel = QGridLayout()
        info_panel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_panel.setColumnMinimumWidth(2, 50)
        info_panel.addWidget(group_label, 0, 0)
        info_panel.addWidget(self.group_value, 0, 1)
        info_panel.addWidget(model_label, 1, 0)
        info_panel.addWidget(self.model_value, 1, 1)
        info_panel.addWidget(sn_label, 0, 3)
        info_panel.addWidget(self.sn_value, 0, 4)
        info_panel.addWidget(operator_label, 1, 3)
        info_panel.addWidget(self.operator_name, 1, 4)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(logo)
        header_layout.addSpacing(20)
        header_layout.addLayout(info_panel)
        header_layout.addWidget(self.status_label, Qt.AlignmentFlag.AlignRight)

        # Body and Main Layouts
        self.steps_table = StepsTable()
        self.body_layout = QHBoxLayout()
        self.channels_layout = QVBoxLayout()
        self.channels_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.channels_layout.setSpacing(20)
        self.body_layout.addWidget(self.steps_table)
        self.body_layout.addLayout(self.channels_layout)
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.addLayout(header_layout)
        main_layout.addLayout(self.body_layout)
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def start_test_sequence(self):
        if self.state in [TestState.RUNNING, TestState.PAUSED, TestState.WAITKEY]:
            return
        if not self.sat_controller.conn_status:
            show_custom_dialog(self, "SAT IT8700 - Sem Conexão", QMessageBox.Critical)
            return
        if not self.arduino_controller.check_connection():
            show_custom_dialog(self, "Arduino - Sem Conexão", QMessageBox.Critical)
            return
        if self.test_setup.active_test is None:
            show_custom_dialog(
                self, "Carregue um Arquivo de Teste", QMessageBox.Information
            )
            return
        if self.test_setup.serial_number is None:
            if not self.show_test_info_input_dialog():
                return

        if (
            self.state is TestState.PASSED
            and not self.test_setup.is_single_step
            and not self.test_setup.serial_number_changed
        ):
            self.test_setup.set_next_serial_number()
            self.update_test_info()

        # Start setup
        self.test_setup.test_result_data.update(
            group=self.test_setup.active_test.group,
            model=self.test_setup.active_test.model,
            customer=self.test_setup.active_test.customer,
            operator=self.operator_name.text(),
            series_number=self.sn_value.text(),
            steps=[],
        )

        self.sat_controller.toggle_active_channels_input(
            self.test_setup.get_active_channel_ids(), True
        )
        if self.state is not TestState.NONE:
            self.steps_table.reset_table()

        self.open_file_action.setDisabled(True)
        self.state = TestState.RUNNING
        self.update_status_label()
        self.start_monitoring()
        self.test_setup.current_index = 0
        self.run_steps()

    def pause_test_sequence(self):
        if self.state not in [TestState.RUNNING, TestState.PAUSED]:
            return
        self.delay_manager.pause_resume()
        match self.state:
            case TestState.PAUSED:
                self.state = TestState.RUNNING
            case TestState.RUNNING:
                self.state = TestState.PAUSED

        self.update_status_label()

    def cancel_test_sequence(self):
        if self.state not in [TestState.RUNNING, TestState.PAUSED, TestState.WAITKEY]:
            return

        self.state = TestState.CANCELED
        self.update_status_label()
        self.reset_setup()

    def run_steps(self):
        steps: list = []
        if self.test_setup.is_single_step:
            steps = [
                self.test_setup.active_test.steps[self.test_setup.selected_step_index]
            ]
        else:
            steps = self.test_setup.active_test.steps

        if self.test_setup.current_index < len(steps):
            step: Step = steps[self.test_setup.current_index]

            if not self.test_setup.is_single_step:
                self.steps_table.set_selected_step(self.test_setup.current_index)

            self.set_fixed_step_values(step)
            self.set_input_source(step.input_source)
            match step.type:
                case 1:
                    self.set_channels_load(step)

            self.handle_step_delay(step)
        else:
            if self.state is not TestState.CANCELED:
                self.state = (
                    TestState.PASSED
                    if False not in self.test_setup.test_sequence_status
                    and not self.test_setup.is_single_step
                    else TestState.FAILED
                )

            self.update_status_label()
            self.reset_setup()
            # GERAR ARQUIVO

            print("Teste Encerrado")  # FIM

    def set_fixed_step_values(self, step: Step):
        for monitor in self.test_setup.channels:
            for channel in step.channels_setup:
                if monitor.channel_id == channel.id:
                    monitor.update_fixed_values(
                        [channel.maxVolt, channel.minVolt, channel.load]
                    )

    def set_input_source(self, input_source: int) -> None:
        """
        - Pino 4: CA1
        - Pino 5: CA2
        - Pino 6: CA3
        - Pino 7: CC1
        - Pino 8: CC2
        - Pino 9: CC3
        - Pino 10: Buzzer
        """
        if self.test_setup.active_input_source != input_source:
            input_type = self.test_setup.active_test.input_type
            match input_source:
                case 1:
                    self.arduino_controller.change_output(
                        "4" if input_type == "CA" else "7"
                    )
                case 2:
                    self.arduino_controller.change_output(
                        "5" if input_type == "CA" else "8"
                    )
                case 3:
                    self.arduino_controller.change_output(
                        "6" if input_type == "CA" else "9"
                    )
            self.test_setup.active_input_source = input_source

    def set_channels_load(self, step: Step):
        for channel in step.channels_setup:
            self.sat_controller.set_channel_current(channel.id, channel.load)

    def handle_step_delay(self, step: Step) -> None:
        if step.duration == 0:
            self.state = TestState.WAITKEY
            self.update_status_label(step.description)
        else:
            self.delay_manager.start_delay(step.duration * 1000)

    def on_delay_completed(self):
        if self.state is not TestState.CANCELED:
            self.handle_test_data(self.validate_step_values())
            self.test_setup.current_index += 1
            self.run_steps()

    def handle_test_data(self, data: tuple):
        self.test_setup.test_result_data["steps"].append(
            dict(
                description=self.test_setup.active_test.steps[
                    self.test_setup.current_index
                ].description,
                channels=data,
            )
        )

    def validate_step_values(self) -> tuple:
        step_pass = True
        current_step_data = []

        for channel in self.test_setup.channels:
            step_pass = (
                channel.data.vmin <= channel.data.output <= channel.data.vmax
            ) and step_pass
            current_step_data.append(
                dict(
                    channel_id=str(channel.channel_id),
                    output=str(channel.data.output),
                    vmax=str(channel.data.vmax),
                    vmin=str(channel.data.vmin),
                    load=str(channel.data.load),
                    power=str(channel.data.power),
                )
            )

        self.steps_table.set_step_status(step_pass)
        self.test_setup.test_sequence_status.append(step_pass)
        channels_data = tuple((current_step_data))
        current_step_data.clear()
        return channels_data

    def handle_single__run(self):
        if self.steps_table.currentRow() >= 0:
            self.test_setup.is_single_step = True
            self.test_setup.selected_step_index = self.steps_table.currentRow()
            self.start_test_sequence()

    def reset_setup(self):
        self.sat_controller.toggle_active_channels_input(
            self.test_setup.get_active_channel_ids(), False
        )
        self.arduino_controller.set_acctive_pin(True)
        self.monitoring_worker.pause()
        self.delay_manager.paused = False
        self.delay_manager.remaining_time = 0
        self.open_file_action.setDisabled(False)
        self.test_setup.test_sequence_status.clear()
        self.test_setup.serial_number_changed = False
        self.test_setup.is_single_step = False
        self.test_setup.selected_step_index = -1
        self.test_setup.active_input_source = 0
        self.test_setup.current_index = 0
        self.steps_table.clearSelection()
        self.steps_table.reset_table()

        self.arduino_controller.buzzer()

    @Slot()
    def start_monitoring(self):
        if self.monitoring_worker is None:
            self.monitoring_worker = MonitorWorker(self.worker_signals)
            self.thread_pool.start(self.monitoring_worker)
        else:
            self.monitoring_worker.resume()

    @Slot(int)
    def update_timer(self, remaining_time):
        self.steps_table.update_duration(str(remaining_time / 1000))

    @Slot()
    def update_output_display(self):
        for channel in self.test_setup.channels:
            channel.update_output(
                self.sat_controller.get_channel_value(channel.channel_id)
            )

    def sn_changed(self):
        self.test_setup.serial_number = str(int(self.sn_value.text())).zfill(8)
        self.sn_value.setText(self.test_setup.serial_number)
        self.test_setup.serial_number_changed = True

    def op_name_changed(self):
        self.test_setup.operator_name = self.operator_name.text()

    def update_test_info(self):
        self.sn_value.setText(self.test_setup.serial_number)
        self.operator_name.setText(self.test_setup.operator_name)

    def show_test_info_input_dialog(self) -> bool:
        dlg = DataInputDialog(self)
        if dlg.exec():
            sn, name = dlg.get_values()
            self.test_setup.serial_number = sn.zfill(8)
            self.test_setup.operator_name = name
            self.update_test_info()
            return True
        return False

    def setup_test_details(self):
        self.group_value.setText(self.test_setup.active_test.group)
        self.model_value.setText(self.test_setup.active_test.model)
        self.steps_table.update_step_list(self.test_setup.active_test.steps)

        for channel in self.test_setup.active_test.active_channels:
            channel_monitor = ChannelMonitor(channel.id)
            self.test_setup.channels.append(channel_monitor)
            self.channels_layout.addWidget(channel_monitor)

        self.steps_table.resizeColumnsToContents()
        total_width = sum(
            self.steps_table.columnWidth(i)
            for i in range(self.steps_table.columnCount())
        )
        self.steps_table.setFixedWidth(total_width + 30)
        self.steps_table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def open_test_file(self):
        fileName = QFileDialog.getOpenFileName(
            self, filter="*.json", caption="Abrir arquivo de teste..."
        )[0]
        if fileName != "":
            with open(fileName) as loaded_file:
                test_data = json.load(loaded_file)
            try:
                self.test_setup.active_test = Test(**test_data)
            except:
                show_custom_dialog(
                    self, f"Arquivo inválido\n{fileName}", QMessageBox.Critical
                )

        if self.test_setup.active_test is not None:
            self.setup_test_details()

    def update_status_label(self, step_description: str = ""):
        if self.state is TestState.WAITKEY:
            self.status_label.setText(f"{step_description}\n{self.state.value}")
            self.status_label.setStyleSheet("color:blue;")
        else:
            self.status_label.setText(self.state.value)
            match self.state:
                case TestState.PASSED | TestState.RUNNING:
                    color = "green"
                case TestState.FAILED | TestState.CANCELED:
                    color = "red"
                case TestState.PAUSED:
                    color = "orange"
                case _:
                    color = "black"
            self.status_label.setStyleSheet(f"color:{color};")

    def keyPressEvent(self, event: QKeyEvent):
        if self.state is TestState.WAITKEY and event.key() in [
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ]:
            self.state = TestState.RUNNING
            self.update_status_label()
            self.on_delay_completed()

    def closeEvent(self, event):
        if self.monitoring_worker is not None:
            self.monitoring_worker.stop()
        # if self.sat_controller.conn_status:
        #     self.sat_controller.inst_resource.close()
        # if self.arduino_controller.arduino is not None:
        #     self.arduino_controller.arduino.conn.close()

        event.accept()


def show_custom_dialog(self, text: str, type: QMessageBox.Icon) -> None:
    dlg = QMessageBox(self)
    dlg.setWindowTitle("Informação" if type == QMessageBox.Information else "Erro")
    dlg.setText(text)
    dlg.setFont(QFont("Arial", 14))
    dlg.setStandardButtons(
        QMessageBox.Ok if type == QMessageBox.Information else QMessageBox.Close
    )
    dlg.setIcon(type)
    dlg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(test_setup=CurrentTestSetup())
    window.showMaximized()  # .showFullScreen()
    sys.exit(app.exec())
