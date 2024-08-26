import sys
import json
from time import sleep

from PySide6.QtCore import (
    QSize,
    Qt,
    QRunnable,
    QThreadPool,
    QMutex,
    QWaitCondition,
    QMutexLocker,
    Signal,
    Slot,
    QObject,
    QTimer,
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QFileDialog,
    QLabel,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy,
)

from controllers.sat_controller import ElectronicLoadController
from controllers.arduino_controller import ArduinoController
from models.test_file_model import Test
from widgets.channel_monitor import ChannelMonitor
from widgets.steps_table import StepsTable
from widgets.test_info_dialog import CustomDialog


class CurrentTestSetup:
    active_test: Test = None
    serial_number: str = None
    operator_name: str = ""
    channels: list[ChannelMonitor] = []
    is_running: bool = False
    is_single_step: bool = False
    selected_step_index: int = 0
    active_input_source: int = 0

    def increase_serial_number(self):
        self.serial_number = self.serial_number + 1


class MonitorWorker(QRunnable):
    def __init__(
        self,
        channels: list[ChannelMonitor],
        sat_controller: ElectronicLoadController,
    ):
        super().__init__()
        self.channels = channels
        self.sat_controller = sat_controller
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.paused = False
        self.running = True

    def run(self):
        while self.running:
            self.mutex.lock()
            while self.paused:
                self.wait_condition.wait(
                    self.mutex
                )  # Pausa até que seja sinalizado para continuar
            self.mutex.unlock()

            for channel in self.channels:
                channel.update_output(
                    self.sat_controller.get_channel_value(channel.channel_id)
                )
                sleep(0.1)

    def pause(self):
        with QMutexLocker(self.mutex):
            self.paused = True

    def resume(self):
        with QMutexLocker(self.mutex):
            self.paused = False
            self.wait_condition.wakeAll()  # Notifica a thread para continuar

    def stop(self):
        with QMutexLocker(self.mutex):
            self.running = False
            self.paused = False
            self.wait_condition.wakeAll()  # Garante que a thread saia do estado de pausa


class MainWindow(QMainWindow):
    def __init__(self, test_setup: CurrentTestSetup):
        super().__init__()
        self.test_setup = test_setup
        self.sat_controller = ElectronicLoadController()
        self.arduino_controller = ArduinoController()
        self.thread_pool = QThreadPool()
        self.monitoring_worker = None

        self.setMinimumSize(QSize(1000, 600))
        self.setWindowTitle(
            f"CEBRA - {self.sat_controller.inst_id}"
            if self.sat_controller.conn_status
            else "CEBRA - IT8700 Sem Conexão"
        )

        # Shortcuts
        self.run_sequence = QShortcut(QKeySequence("Alt+R"), self)
        self.run_sequence.activated.connect(self.run_test_sequence)

        # Actions
        open_file_action = QAction(
            QIcon("assets/icons/file_open.png"), "Abrir Arquivo", self
        )
        open_file_action.triggered.connect(self.open_test_file)

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("&Arquivo")
        file_menu.addAction(open_file_action)

        logo = QLabel()
        logo.setPixmap(QPixmap("assets/logo.png"))
        logo.setScaledContents(True)
        logo.setFixedSize(150, 100)

        # Labels
        group_label = info_label("Grupo: ")
        self.group_value = info_label("")
        model_label = info_label("Modelo: ")
        self.model_value = info_label("")
        sn_label = info_label("Nº: ")
        self.sn_value = info_label("")
        operator_label = info_label("Operador: ")
        self.operator_value = info_label("")

        # info panel
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
        info_panel.addWidget(self.operator_value, 1, 4)

        # header
        header_layout = QHBoxLayout()
        header_layout.addWidget(logo)
        header_layout.addLayout(info_panel)

        self.steps_table = StepsTable()
        self.body_layout = QHBoxLayout()
        self.channels_layout = QVBoxLayout()
        self.channels_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.channels_layout.setSpacing(20)
        self.body_layout.addWidget(self.steps_table)
        self.body_layout.addLayout(self.channels_layout)

        # main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.addLayout(header_layout)
        main_layout.addLayout(self.body_layout)
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def set_input_source(self, input_source: int) -> None:
        """
        Receives input_source(int) and send it to arduino_ctrl using the predefined pins configuration and input_type.
            - Pin 4: CA1
            - Pin 5: CA2
            - Pin 6: CA3
            - Pin 7: CC1
            - Pin 8: CC2
            - Pin 9: CC3
            - Pin 10: Buzzer
        No return.
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

    @Slot()
    def start_monitoring(self):
        print("Monitorando...")
        if self.monitoring_worker is None:
            self.monitoring_worker = MonitorWorker(
                self.test_setup.channels, self.sat_controller
            )
            self.thread_pool.start(self.monitoring_worker)

    def run_test_sequence(self):
        if (
            not self.sat_controller.conn_status
            or not self.arduino_controller.check_connection()
        ):
            return
        if self.test_setup.active_test is None or self.test_setup.is_running:
            return
        if (
            self.test_setup.serial_number is None
            or self.test_setup.operator_name is None
        ):
            if not self.show_test_info_dialog():
                return

        # Start setup
        self.test_setup.is_running = True
        self.start_monitoring()

        if self.test_setup.is_single_step:
            step_list = [
                self.test_setup.active_test.steps[self.test_setup.selected_step_index]
            ]
        else:
            step_list = self.test_setup.active_test.steps

        for index, step in enumerate(step_list):
            step_done = False
            while self.test_setup.is_running and not step_done:
                self.set_input_source(step.input)
                step_done = True

        self.arduino_controller.buzzer()

    def show_test_info_dialog(self) -> bool:
        dlg = CustomDialog(self)
        if dlg.exec():
            sn, name = dlg.get_values()
            self.test_setup.serial_number = sn.zfill(8)
            self.test_setup.operator_name = name
            self.sn_value.setText(self.test_setup.serial_number)
            self.operator_value.setText(self.test_setup.operator_name)
            return True
        return False

    def update_test_info(self):
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
            print(fileName)
            with open(fileName) as loaded_file:
                test_data = json.load(loaded_file)
            try:
                self.test_setup.active_test = Test(**test_data)
            except:
                print("ERRO, arquivo inválido!")

        if self.test_setup.active_test is not None:
            self.update_test_info()


def info_label(text: str) -> QLabel:
    font = QFont()
    font.setPointSize(16)
    label = QLabel(text)
    label.setFont(font)
    return label


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(test_setup=CurrentTestSetup())
    window.showMaximized()  # .showFullScreen()
    sys.exit(app.exec())
