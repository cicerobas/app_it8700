import sys
import os
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
from utils.monitor_worker import MonitorWorker
from utils.enums import *
from utils.report_file import *


class CurrentTestSetup:
    active_test: Test = None
    directory_path: str = ""
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
        self.steps_table = StepsTable()
        self.monitoring_worker = None

        self.setMinimumSize(QSize(1200, 600))
        self.setWindowTitle(
            f"CEBRA - {self.sat_controller.inst_id}"
            if self.sat_controller.conn_status
            else "CEBRA - IT8700 Sem Conexão"
        )

        # Signals
        self.delay_manager.delay_completed.connect(self.on_delay_completed)
        self.delay_manager.remaining_time_changed.connect(self.update_timer)
        self.worker_signals.update_output.connect(self.update_output_display)

        # Shortcuts
        self.start_shortcut = QShortcut(QKeySequence("Alt+R"), self)
        self.pause_shortcut = QShortcut(QKeySequence("Alt+P"), self)
        self.stop_shortcut = QShortcut(QKeySequence("Alt+S"), self)
        self.single_run_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.start_shortcut.activated.connect(self.start_test_sequence)
        self.pause_shortcut.activated.connect(self.toggle_test_pause)
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
        group_label = default_header_label("Grupo: ")
        model_label = default_header_label("Modelo: ")
        serial_number_label = default_header_label("Nº de Serie: ")
        operator_name_label = default_header_label("Operador: ")
        self.test_status_label = QLabel("---")
        self.test_status_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.test_status_label.setContentsMargins(50, 0, 50, 0)
        self.test_status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        # Fields
        self.group_value_field = default_header_field(True, Qt.FocusPolicy.NoFocus)
        self.model_value_field = default_header_field(True, Qt.FocusPolicy.NoFocus)
        self.serial_number_value_field = default_header_field(
            False, Qt.FocusPolicy.ClickFocus
        )
        self.operator_name_value_field = default_header_field(
            False, Qt.FocusPolicy.ClickFocus
        )
        self.serial_number_value_field.setValidator(QIntValidator(0, 99999999, self))

        self.serial_number_value_field.textEdited.connect(self.serial_number_changed)
        self.operator_name_value_field.textEdited.connect(self.operator_name_changed)

        # Test Details Layout
        g_info_panel_layout = QGridLayout()
        g_info_panel_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        g_info_panel_layout.setColumnMinimumWidth(2, 50)
        g_info_panel_layout.addWidget(group_label, 0, 0)
        g_info_panel_layout.addWidget(self.group_value_field, 0, 1)
        g_info_panel_layout.addWidget(model_label, 1, 0)
        g_info_panel_layout.addWidget(self.model_value_field, 1, 1)
        g_info_panel_layout.addWidget(serial_number_label, 0, 3)
        g_info_panel_layout.addWidget(self.serial_number_value_field, 0, 4)
        g_info_panel_layout.addWidget(operator_name_label, 1, 3)
        g_info_panel_layout.addWidget(self.operator_name_value_field, 1, 4)

        # Header
        h_header_layout = QHBoxLayout()
        h_header_layout.addWidget(logo)
        h_header_layout.addSpacing(20)
        h_header_layout.addLayout(g_info_panel_layout)
        h_header_layout.addWidget(self.test_status_label, Qt.AlignmentFlag.AlignRight)

        # Main Container Layouts
        main_container_widget = QWidget()
        h_content_layout = QHBoxLayout()
        self.v_channels_display_layout = QVBoxLayout()
        v_main_container_layout = QVBoxLayout()

        self.v_channels_display_layout.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        self.v_channels_display_layout.setSpacing(20)

        h_content_layout.addWidget(self.steps_table)
        h_content_layout.addLayout(self.v_channels_display_layout)

        v_main_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_main_container_layout.addLayout(h_header_layout)
        v_main_container_layout.addLayout(h_content_layout)

        main_container_widget.setLayout(v_main_container_layout)
        self.setCentralWidget(main_container_widget)

    def start_test_sequence(self):
        if self.state in [TestState.RUNNING, TestState.PAUSED, TestState.WAITKEY]:
            return
        if not self.sat_controller.conn_status:
            show_custom_dialog(
                self, "SAT IT8700 - Sem Conexão", QMessageBox.Icon.Critical
            )
            return
        if not self.arduino_controller.check_connection():
            show_custom_dialog(self, "Arduino - Sem Conexão", QMessageBox.Icon.Critical)
            return
        if self.test_setup.active_test is None:
            show_custom_dialog(
                self, "Carregue um Arquivo de Teste", QMessageBox.Icon.Information
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
            operator=self.operator_name_value_field.text(),
            serial_number=self.serial_number_value_field.text(),
            steps=[],
        )

        self.sat_controller.toggle_active_channels_input(
            self.test_setup.get_active_channel_ids(), True
        )
        if self.state is not TestState.NONE:
            self.steps_table.reset_table_status_fields()

        self.open_file_action.setDisabled(True)
        self.serial_number_value_field.setReadOnly(True)
        self.operator_name_value_field.setReadOnly(True)
        self.state = TestState.RUNNING
        self.test_setup.current_index = 0
        self.update_status_label()
        self.start_monitoring()
        self.run_steps()

    def toggle_test_pause(self):
        if self.state not in [TestState.RUNNING, TestState.PAUSED]:
            return
        self.delay_manager.pause_resume()
        self.state = (
            TestState.RUNNING if self.state is TestState.PAUSED else TestState.PAUSED
        )
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
                    else TestState.FAILED
                )

            if self.state is TestState.PASSED and not self.test_setup.is_single_step:
                generate_report_file(
                    f"{self.test_setup.directory_path}{self.test_setup.serial_number}.txt",
                    self.test_setup.test_result_data,
                )  # TODO:CRIAR LOG PARA EXIBIR RESULTADOS FALHOS
            
            self.update_status_label()
            self.reset_setup()

    def set_fixed_step_values(self, step: Step):
        channel_dict = {channel.id: channel for channel in step.channels_setup}
        for monitor in self.test_setup.channels:
            if monitor.channel_id in channel_dict:
                channel = channel_dict[monitor.channel_id]
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
        if self.test_setup.active_input_source == input_source:
            return

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

    def handle_test_data(self, data: tuple) -> None:
        current_step = self.test_setup.active_test.steps[self.test_setup.current_index]
        step_data = {
            "description": current_step.description,
            "channels": data,
        }
        self.test_setup.test_result_data["steps"].append(step_data)

    def validate_step_values(self) -> tuple:
        step_pass = True
        current_step_data = []

        for channel in self.test_setup.channels:
            channel_data = {
                "channel_id": str(channel.channel_id),
                "output": channel.data.output,
                "vmax": channel.data.vmax,
                "vmin": channel.data.vmin,
                "load": channel.data.load,
                "power": channel.data.power,
            }

            current_step_data.append(channel_data)
            if not (channel.data.vmin <= channel.data.output <= channel.data.vmax):
                step_pass = False

        self.steps_table.set_step_status(step_pass)
        self.test_setup.test_sequence_status.append(step_pass)

        return tuple(current_step_data)

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
        self.serial_number_value_field.setReadOnly(False)
        self.operator_name_value_field.setReadOnly(False)
        self.test_setup.test_sequence_status.clear()
        self.test_setup.serial_number_changed = False
        self.test_setup.is_single_step = False
        self.test_setup.selected_step_index = -1
        self.test_setup.active_input_source = 0
        self.test_setup.current_index = 0
        self.steps_table.clearSelection()
        self.steps_table.reset_table_status_fields()

        while not self.arduino_controller.buzzer():
            sleep(0.1)  # VERIFICAR DELAY

    @Slot()
    def start_monitoring(self):
        if self.monitoring_worker is None:
            self.monitoring_worker = MonitorWorker(self.worker_signals)
            self.thread_pool.start(self.monitoring_worker)
        else:
            self.monitoring_worker.resume()

    @Slot(int)
    def update_timer(self, remaining_time):
        self.steps_table.update_duration(remaining_time / 1000)

    @Slot()
    def update_output_display(self):
        for channel in self.test_setup.channels:
            channel.update_output_value(
                self.sat_controller.get_channel_value(channel.channel_id)
            )

    def serial_number_changed(self):
        self.test_setup.serial_number = str(
            int(self.serial_number_value_field.text())
        ).zfill(8)
        self.update_test_info()
        self.test_setup.serial_number_changed = True

    def operator_name_changed(self):
        self.test_setup.operator_name = self.operator_name_value_field.text()

    def update_test_info(self):
        self.serial_number_value_field.setText(self.test_setup.serial_number)
        self.operator_name_value_field.setText(self.test_setup.operator_name)

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
        self.group_value_field.setText(self.test_setup.active_test.group)
        self.model_value_field.setText(self.test_setup.active_test.model)
        self.steps_table.update_step_list(self.test_setup.active_test.steps)

        for channel in self.test_setup.active_test.active_channels:
            channel_monitor = ChannelMonitor(channel.id)
            self.test_setup.channels.append(channel_monitor)
            self.v_channels_display_layout.addWidget(channel_monitor)

        self.steps_table.resizeColumnsToContents()
        total_width = sum(
            self.steps_table.columnWidth(i)
            for i in range(self.steps_table.columnCount())
        )
        self.steps_table.setFixedWidth(total_width + 50)
        self.steps_table.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

    def open_test_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir arquivo de teste...", "", "Arquivos JSON (*.json)"
        )

        if file_path:
            try:
                with open(file_path, "r") as loaded_file:
                    test_data = json.load(loaded_file)
                self.test_setup.active_test = Test(**test_data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                show_custom_dialog(
                    self,
                    f"Falha ao abrir arquivo\n{file_path}\nErro: {str(e)}",
                    QMessageBox.Icon.Critical,
                )
            except Exception as e:
                show_custom_dialog(
                    self,
                    f"Falha ao abrir arquivo\n{file_path}\nErro inesperado: {str(e)}",
                    QMessageBox.Icon.Critical,
                )
            else:
                self.test_setup.directory_path = (
                    os.path.dirname(file_path) + os.path.sep
                )
                self.setup_test_details()

    def update_status_label(self, step_description: str = ""):
        status_text = f"{step_description}\n{self.state.value}"
        self.test_status_label.setText(status_text.lstrip())
        match self.state:
            case TestState.PASSED | TestState.RUNNING:
                color = "green"
            case TestState.FAILED | TestState.CANCELED:
                color = "red"
            case TestState.PAUSED:
                color = "orange"
            case TestState.WAITKEY:
                color = "blue"
            case _:
                color = "black"
        self.test_status_label.setStyleSheet(f"color:{color};")

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

        event.accept()


def default_header_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(QFont("Arial", 16))
    return label


def default_header_field(read_only: bool, focus_policy: Qt.FocusPolicy) -> QLineEdit:
    field = QLineEdit()
    field.setReadOnly(read_only)
    field.setFocusPolicy(focus_policy)
    return field


def show_custom_dialog(self, text: str, type: QMessageBox.Icon) -> None:
    dlg = QMessageBox(self)
    dlg.setWindowTitle("Informação" if type == QMessageBox.Icon.Information else "Erro")
    dlg.setText(text)
    dlg.setFont(QFont("Arial", 14))
    dlg.setStandardButtons(
        QMessageBox.StandardButton.Ok
        if type == QMessageBox.Icon.Information
        else QMessageBox.StandardButton.Close
    )
    dlg.setIcon(type)
    dlg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(test_setup=CurrentTestSetup())
    window.showMaximized()  # .showFullScreen()
    sys.exit(app.exec())
