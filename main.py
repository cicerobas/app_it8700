import os
import sys
from time import sleep

import yaml
from PySide6.QtCore import QSize, Qt, QTimer, QThreadPool, Slot, Signal, QObject
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
    QLineEdit,
    QFrame,
)

from controllers.arduino_controller import ArduinoController
from controllers.sat_controller import ElectronicLoadController
from models.test_file_model import *
from utils.delay_manager import DelayManager
from utils.enums import *
from utils.monitor_worker import MonitorWorker
from utils.report_file import *
from widgets.channel_monitor import ChannelMonitor
from widgets.data_input_dialog import DataInputDialog
from widgets.steps_table import StepsTable
from widgets.test_edit_view import TestEditView
from widgets.test_result_view import TestResultView
from widgets.test_setup_view import TestSetupView


class CurrentTestSetup:
    def __init__(self):
        self.active_test: TestData | None = None
        self.directory_path: str = ""
        self.serial_number: str | None = None
        self.operator_name: str = ""
        self.channels: list[ChannelMonitor] = []
        self.serial_number_changed: bool = False
        self.is_single_step: bool = False
        self.selected_step_index: int = -1
        self.current_index: int = 0
        self.test_result_data = dict()
        self.test_sequence_status: list[bool] = []

    def set_next_serial_number(self):
        self.serial_number = str(int(self.serial_number) + 1).zfill(8)

    def get_active_channel_ids(self) -> list[int]:
        return list(map(lambda channel: channel.id, self.active_test.active_channels))


class WorkerSignals(QObject):
    update_output = Signal()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cl_channel_id = None
        self.cl_step_params = None
        self.current_load = None
        self.cl_step_done = None
        self.short_test_channel = None
        self.short_test_cycle = None
        self.short_test_params = None
        self.shutdown_state = None
        self.recovery_state = None
        self.test_setup = CurrentTestSetup()
        self.state = TestState.NONE
        self.sat_controller = ElectronicLoadController()
        self.arduino_controller = ArduinoController()
        self.thread_pool = QThreadPool()
        self.worker_signals = WorkerSignals()
        self.delay_manager = DelayManager()
        self.steps_table = StepsTable()
        self.steps_table.setVisible(False)
        self.test_result_view = TestResultView()
        self.test_edit_view = TestEditView(self)
        self.test_setup_view = TestSetupView(self.arduino_controller, self)
        self.monitoring_worker = None
        self.temp_file = None
        self.temp_file_name = ""

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
        self.single_run_shortcut.activated.connect(self.handle_single_run)

        # Actions
        self.open_file_action = QAction(
            QIcon("assets/icons/file_open.png"), "Abrir...", self
        )
        self.new_file_action = QAction(
            QIcon("assets/icons/file_add.png"), "Novo...", self
        )
        self.edit_file_action = QAction(
            QIcon("assets/icons/file_edit.png"), "Editar...", self
        )
        self.test_result_action = QAction(
            QIcon("assets/icons/description.png"), "Resultado", self
        )
        self.test_setup_action = QAction(
            QIcon("assets/icons/settings.png"), "Configuração", self
        )
        self.test_setup_action.setEnabled(False)

        self.open_file_action.setShortcut(Qt.Key.Key_F3)
        self.test_result_action.setShortcut(Qt.Key.Key_F8)
        self.test_setup_action.setShortcut(Qt.Key.Key_F4)

        self.open_file_action.triggered.connect(self.open_test_file)
        self.new_file_action.triggered.connect(lambda e: self.open_window(0))
        self.edit_file_action.triggered.connect(lambda e: self.open_window(1))
        self.test_result_action.triggered.connect(self.test_result_view.show)
        self.test_setup_action.triggered.connect(lambda e: self.open_window(2))

        # Menu
        menu = self.menuBar()
        file_menu = menu.addMenu("&Arquivo")
        file_menu.addAction(self.open_file_action)
        file_menu.addAction(self.new_file_action)
        file_menu.addAction(self.edit_file_action)

        test_menu = menu.addMenu("&Teste")
        test_menu.addAction(self.test_result_action)
        test_menu.addAction(self.test_setup_action)

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
        g_info_panel_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
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

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("background-color: grey;")

        self.v_channels_display_layout.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        self.v_channels_display_layout.setSpacing(20)

        h_content_layout.addWidget(self.steps_table)
        h_content_layout.addLayout(self.v_channels_display_layout)

        v_main_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_main_container_layout.setSpacing(15)
        v_main_container_layout.addLayout(h_header_layout)
        v_main_container_layout.addWidget(divider)
        v_main_container_layout.addLayout(h_content_layout)

        main_container_widget.setLayout(v_main_container_layout)
        self.setCentralWidget(main_container_widget)

    def reset_window(self):
        self.test_setup = CurrentTestSetup()

    def open_window(self, window_id: int) -> None:
        self.hide()
        match window_id:
            case 0:
                self.test_edit_view = TestEditView(self)
                self.test_edit_view.show()
                self.reset_window()
            case 1:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Abrir arquivo de teste...", "", "Arquivos YAML (*.yaml)"
                )
                if file_path:
                    self.test_edit_view = TestEditView(self)
                    self.test_edit_view.show(file_path)
                    self.reset_window()
                else:
                    self.show()
            case 2:
                self.test_setup_view.showMaximized()

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

            self.arduino_controller.set_input_source(
                step.input_source, self.test_setup.active_test.input_type
            )

            self.set_fixed_step_values(step)
            match step.step_type:
                case 1:
                    self.cc_test_mode(step)
                case 2:
                    self.cl_test_mode(step)
                case 3:
                    self.short_test_mode(step)
        else:
            if self.temp_file:
                self.temp_file.close()
                os.remove(self.temp_file.name)

            if self.state is not TestState.CANCELED:
                self.state = (
                    TestState.PASSED
                    if False not in self.test_setup.test_sequence_status
                    else TestState.FAILED
                )
            self.temp_file = generate_report_file(self.test_setup.test_result_data)
            self.temp_file_name = self.temp_file.name
            self.test_result_view.text = self.read_temp_file()

            if self.state is TestState.PASSED and not self.test_setup.is_single_step:
                with open(
                    file=f"{self.test_setup.directory_path}{self.test_setup.serial_number}.txt",
                    mode="w",
                    encoding="utf-8",
                ) as test_file:
                    test_file.write(self.read_temp_file())

            self.update_status_label()
            self.reset_setup()

    def cc_test_mode(self, step: Step):
        for channel_id, params in step.channels_configuration.items():
            self.update_current_load(channel_id, params.static_load)
        if step.duration == 0:
            self.state = TestState.WAITKEY
            self.update_status_label(step.description)
        else:
            self.delay_manager.start_delay(step.duration * 1000)

    def cl_test_mode(self, step: Step):
        self.cl_step_done = False
        self.cl_channel_id = self.test_setup.get_active_channel_ids()[0]
        self.cl_step_params = step.channels_configuration.get(self.cl_channel_id)
        self.current_load = self.cl_step_params.static_load
        self.update_current_load(self.cl_channel_id, self.cl_step_params.static_load)
        self.handle_increase_steps()

    def handle_increase_steps(self):
        if self.state is TestState.CANCELED:
            return
        channel = next(
            (c for c in self.test_setup.channels if c.channel_id == self.cl_channel_id),
            None,
        )
        if not self.cl_step_done:
            if (
                channel.data.voltage_output >= self.cl_step_params.voltage_under_limit
                and self.current_load <= self.cl_step_params.end_load
            ):
                self.current_load += self.cl_step_params.increase_step
                self.update_current_load(self.cl_channel_id, self.current_load)
                QTimer.singleShot(
                    int(self.cl_step_params.increase_delay * 1000),
                    self.handle_increase_steps,
                )
            else:
                self.update_current_load(
                    self.cl_channel_id, self.cl_step_params.static_load
                )
                self.cl_step_done = True
                QTimer.singleShot(100, self.handle_increase_steps)
        else:
            if channel.data.voltage_output <= self.cl_step_params.voltage_under_limit:
                QTimer.singleShot(100, self.handle_increase_steps)
            else:
                self.validate_cl_step_values()
                self.test_setup.current_index += 1
                self.run_steps()

    def short_test_mode(self, step: Step):
        self.short_test_channel = self.test_setup.get_active_channel_ids()[0]
        self.short_test_cycle = 0
        self.short_test_params = step.channels_configuration.get(
            self.short_test_channel
        )
        self.shutdown_state = False
        self.recovery_state = False
        self.sat_controller.toggle_short_mode(self.short_test_channel, True)
        self.update_current_load(
            self.short_test_channel, self.short_test_params.static_load
        )
        self.check_short_state()

    def check_short_state(self):
        voltage_shutdown_factor = 0.2
        short_test_max_cycle = 30

        if self.short_test_cycle >= short_test_max_cycle:
            self.validade_short_test(False)
            return
        channel = next(
            (
                c
                for c in self.test_setup.channels
                if c.channel_id == self.short_test_channel
            ),
            None,
        )

        voltage_output = channel.data.voltage_output
        voltage_lower = self.short_test_params.voltage_lower

        if voltage_output < voltage_lower and self.short_test_cycle == 0:
            QTimer.singleShot(500, self.check_short_state)
            return

        if (
            not self.shutdown_state
            and voltage_output < voltage_lower * voltage_shutdown_factor
        ):
            self.shutdown_state = True
            self.sat_controller.toggle_short_mode(self.short_test_channel, False)

        if self.shutdown_state and voltage_output > voltage_lower:
            self.recovery_state = True

        if self.recovery_state and self.shutdown_state:
            self.validade_short_test(True)
        else:
            self.short_test_cycle += 1
            QTimer.singleShot(500, self.check_short_state)

    def set_fixed_step_values(self, step: Step):
        for monitor in self.test_setup.channels:
            if monitor.channel_id in step.channels_configuration:
                params = step.channels_configuration[monitor.channel_id]
                monitor.update_step_values(
                    [
                        params.voltage_upper,
                        params.voltage_lower,
                        params.load_upper,
                        params.load_lower,
                    ]
                )

    def on_delay_completed(self):
        if self.state is not TestState.CANCELED:
            self.validate_cc_step_values()
            self.test_setup.current_index += 1
            self.run_steps()

    def validate_cc_step_values(self) -> None:
        step_pass = True
        current_step_data = []

        for channel in self.test_setup.channels:
            channel_data = {
                "channel_id": str(channel.channel_id),
                "voltage_output": channel.data.voltage_output,
                "voltage_upper": channel.data.voltage_upper,
                "voltage_lower": channel.data.voltage_lower,
                "load": channel.data.load,
                "power": channel.data.power,
            }

            current_step_data.append(channel_data)
            if not (
                channel.data.voltage_lower
                <= channel.data.voltage_output
                <= channel.data.voltage_upper
            ):
                step_pass = False

        self.steps_table.set_step_status(step_pass)
        self.test_setup.test_sequence_status.append(step_pass)
        self.handle_test_data(tuple(current_step_data), step_pass)

    def validate_cl_step_values(self) -> None:
        step_pass = True
        current_step_data = []

        for channel in self.test_setup.channels:
            channel_data = {
                "channel_id": str(channel.channel_id),
                "under_voltage": self.cl_step_params.voltage_under_limit,
                "load_upper": channel.data.load_upper,
                "load_lower": channel.data.load_lower,
                "load": self.current_load,
            }

            current_step_data.append(channel_data)
            if not (
                channel.data.load_lower <= channel.data.load <= channel.data.load_upper
            ):
                step_pass = False

        self.steps_table.set_step_status(step_pass)
        self.test_setup.test_sequence_status.append(step_pass)
        self.handle_test_data(tuple(current_step_data), step_pass)

    def validade_short_test(self, step_pass: bool):
        current_step_data = []

        for channel in self.test_setup.channels:
            channel_data = {
                "channel_id": str(channel.channel_id),
                "voltage_ref": self.short_test_params.voltage_lower,
                "shutdown": self.shutdown_state,
                "recovery": self.recovery_state,
                "load": self.short_test_params.static_load,
            }

            current_step_data.append(channel_data)

        self.steps_table.set_step_status(step_pass)
        self.test_setup.test_sequence_status.append(step_pass)
        self.handle_test_data(tuple(current_step_data), step_pass)
        self.test_setup.current_index += 1
        self.run_steps()

    def handle_test_data(self, data: tuple, step_status: bool) -> None:
        current_step = self.test_setup.active_test.steps[self.test_setup.current_index]
        step_data = {
            "description": current_step.description,
            "status": step_status,
            "type": current_step.step_type,
            "channels": data,
        }
        self.test_setup.test_result_data["steps"].append(step_data)

    def handle_single_run(self):
        if self.steps_table.currentRow() >= 0:
            self.test_setup.is_single_step = True
            self.test_setup.selected_step_index = self.steps_table.currentRow()
            self.start_test_sequence()

    def reset_setup(self):
        self.sat_controller.toggle_active_channels_input(
            self.test_setup.get_active_channel_ids(), False
        )
        self.arduino_controller.set_active_pin(True)
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
        self.arduino_controller.active_input_source = 0
        self.test_setup.current_index = 0
        self.steps_table.clearSelection()

        while not self.arduino_controller.buzzer():
            sleep(0.1)

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
            channel.update_voltage_value(
                self.sat_controller.get_channel_value(channel.channel_id)
            )

    def update_current_load(self, channel_id, load):
        for channel in self.test_setup.channels:
            if channel.channel_id == channel_id:
                channel.update_load_value(load)
                self.sat_controller.set_channel_current(channel_id, load)

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
        self.steps_table.setVisible(True)

        for channel in self.test_setup.active_test.active_channels:
            channel_monitor = ChannelMonitor(channel.id, channel.label)
            self.test_setup.channels.append(channel_monitor)
            self.v_channels_display_layout.addWidget(channel_monitor)

    def open_test_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir arquivo de teste...", "", "Arquivos YAML (*.yaml)"
        )

        if file_path:
            self.reset_current_test()
            self.test_setup_view.file_path = file_path
            try:
                with open(file_path, "r") as loaded_file:
                    test_data = yaml.safe_load(loaded_file.read())
                self.test_setup.active_test = TestData(**test_data)
                self.test_setup_action.setEnabled(True)
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

    def reset_current_test(self):
        self.test_setup = CurrentTestSetup()
        self.update_test_info()
        while self.v_channels_display_layout.count():
            item = self.v_channels_display_layout.takeAt(0)
            item.widget().deleteLater()

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

    def read_temp_file(self) -> str:
        if self.temp_file:
            with open(self.temp_file_name, "r", encoding="utf-8") as file:
                return file.read()

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
    text_field = QLineEdit()
    text_field.setReadOnly(read_only)
    text_field.setFocusPolicy(focus_policy)
    return text_field


def show_custom_dialog(self, text: str, message_type: QMessageBox.Icon) -> None:
    dlg = QMessageBox(self)
    dlg.setWindowTitle(
        "Informação" if message_type == QMessageBox.Icon.Information else "Erro"
    )
    dlg.setText(text)
    dlg.setFont(QFont("Arial", 14))
    dlg.setStandardButtons(
        QMessageBox.StandardButton.Ok
        if message_type == QMessageBox.Icon.Information
        else QMessageBox.StandardButton.Close
    )
    dlg.setIcon(message_type)
    dlg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
