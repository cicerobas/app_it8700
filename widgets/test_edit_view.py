from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QWidget,
    QMainWindow,
    QLabel,
    QLineEdit,
    QGroupBox,
    QRadioButton,
    QCheckBox,
    QComboBox,
    QDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialogButtonBox,
    QSpinBox,
    QDoubleSpinBox,
    QFileDialog,
)
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon

import yaml


class TestSetup:
    _group: str = ""
    _model: str = ""
    _customer: str = ""
    _input_type: str = "CC"
    _notes: str = ""
    _input_sources: list = [0, 0, 0]
    _step_list: list = []
    _active_channels: dict = {}
    _params_list: list = []

    @classmethod
    def set_group(cls, value: str):
        cls._group = value

    @classmethod
    def get_group(cls):
        return cls._group

    @classmethod
    def set_model(cls, value: str):
        cls._model = value

    @classmethod
    def get_model(cls):
        return cls._model

    @classmethod
    def set_customer(cls, value: str):
        cls._customer = value

    @classmethod
    def get_customer(cls):
        return cls._customer

    @classmethod
    def set_input_type(cls, value: str):
        cls._input_type = value

    @classmethod
    def get_input_type(cls):
        return cls._input_type

    @classmethod
    def set_input_sources(cls, values: list[str]):
        cls._input_sources = values

    @classmethod
    def get_input_sources(cls):
        return cls._input_sources

    @classmethod
    def toggle_active_channels(cls, ch1: bool, ch3: bool, ch4: bool, labels: list[str]):
        cls._active_channels.clear()
        if ch1:
            cls._active_channels.update({"1": labels[0]})
        if ch3:
            cls._active_channels.update({"3": labels[1]})
        if ch4:
            cls._active_channels.update({"4": labels[2]})

    @classmethod
    def add_step(cls, step, index=-1):
        if index != -1:
            cls._step_list.insert(index, step)
        else:
            cls._step_list.append(step)

    @classmethod
    def add_param(cls, param, index=-1):
        if index != -1:
            param.update({"id": index + 1, "increase_delay": 0.5})
            cls._params_list.insert(index, param)
        else:
            id = len(cls._params_list) + 1
            param.update({"id": id, "increase_delay": 0.5})
            cls._params_list.append(param)

    @classmethod
    def remove_step(cls, index):
        cls._step_list.remove(cls._step_list[index])

    @classmethod
    def remove_param(cls, index):
        cls._params_list.remove(cls._params_list[index])

    @classmethod
    def pop_step(cls, index):
        return cls._step_list.pop(index)

    @classmethod
    def pop_param(cls, index):
        return cls._params_list.pop(index)

    @classmethod
    def get_step_list(cls):
        return cls._step_list

    @classmethod
    def get_params_list(cls):
        return cls._params_list

    @classmethod
    def get_active_channels_list(cls):
        return cls._active_channels

    @classmethod
    def get_data(cls):
        return {
            "group": cls._group,
            "model": cls._model,
            "customer": cls._customer,
            "input_type": cls._input_type,
            "input_sources": cls._input_sources,
            "active_channels": [
                {"id": int(key), "label": value}
                for key, value in cls._active_channels.items()
            ],
            "load_parameters": cls._params_list,
            "steps": cls._step_list,
            "notes": cls._notes,
        }


class TestEditView(QWidget):
    def __init__(self, main_window: QMainWindow = None):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("CEBRA - Test Configuration")
        self.setFont(QFont("Arial", 14))
        self.setMinimumSize(QSize(1280, 600))

        # Fields
        self.group_field = QLineEdit()
        self.model_field = QLineEdit()
        self.customer_field = QLineEdit()
        self.group_field.textChanged.connect(TestSetup.set_group)
        self.model_field.textChanged.connect(TestSetup.set_model)
        self.customer_field.textChanged.connect(TestSetup.set_customer)
        self.v1_input_field = QLineEdit()
        self.v2_input_field = QLineEdit()
        self.v3_input_field = QLineEdit()
        self.v1_input_field.textChanged.connect(self.set_input_sources_labels)
        self.v2_input_field.textChanged.connect(self.set_input_sources_labels)
        self.v3_input_field.textChanged.connect(self.set_input_sources_labels)
        self.ch1_cb = QCheckBox("Canal 1")
        self.ch3_cb = QCheckBox("Canal 3")
        self.ch4_cb = QCheckBox("Canal 4")
        self.ch1_cb.clicked.connect(self.toggle_active_channels)
        self.ch3_cb.clicked.connect(self.toggle_active_channels)
        self.ch4_cb.clicked.connect(self.toggle_active_channels)
        self.ch1_field = QLineEdit()
        self.ch3_field = QLineEdit()
        self.ch4_field = QLineEdit()
        self.input_type_ca = QRadioButton("CA")
        self.input_type_cc = QRadioButton("CC")
        self.input_type_cc.setChecked(True)
        self.input_type_ca.toggled.connect(self.input_type_toggled)
        self.input_type_cc.toggled.connect(self.input_type_toggled)
        self.save_button = QPushButton("Salvar Arquivo")
        self.save_button.clicked.connect(self.save_file)

        # Details Group
        details_gb = QGroupBox("Detalhes")
        details_gb.setFixedWidth(400)
        details_layout = QVBoxLayout()
        info_layout = QFormLayout()
        info_layout.addRow("Grupo", self.group_field)
        info_layout.addRow("Modelo", self.model_field)
        info_layout.addRow("Cliente", self.customer_field)
        details_layout.addLayout(info_layout)

        # Inputs Group
        inputs_gb = QGroupBox("Entrada")
        inputs_layout = QFormLayout()
        input_type_layout = QHBoxLayout()
        input_type_layout.addWidget(self.input_type_ca)
        input_type_layout.addWidget(self.input_type_cc)
        inputs_layout.addRow("Tipo", input_type_layout)
        inputs_layout.addRow("V1", self.v1_input_field)
        inputs_layout.addRow("V2", self.v2_input_field)
        inputs_layout.addRow("V3", self.v3_input_field)
        inputs_gb.setLayout(inputs_layout)
        details_layout.addWidget(inputs_gb)

        # Channels Group
        channels_gb = QGroupBox("Canais")
        channels_layout = QVBoxLayout()
        ch1_layout = QHBoxLayout()
        ch1_layout.addWidget(self.ch1_cb)
        ch1_layout.addWidget(self.ch1_field)
        ch3_layout = QHBoxLayout()
        ch3_layout.addWidget(self.ch3_cb)
        ch3_layout.addWidget(self.ch3_field)
        ch4_layout = QHBoxLayout()
        ch4_layout.addWidget(self.ch4_cb)
        ch4_layout.addWidget(self.ch4_field)
        channels_layout.addLayout(ch1_layout)
        channels_layout.addLayout(ch3_layout)
        channels_layout.addLayout(ch4_layout)
        channels_gb.setLayout(channels_layout)
        details_layout.addWidget(channels_gb)

        details_layout.addWidget(self.save_button)
        details_gb.setLayout(details_layout)

        # Steps Group
        steps_gb = QGroupBox("Etapas")
        steps_gb.setFixedWidth(500)
        steps_layout = QVBoxLayout()
        steps_actions_layout = QHBoxLayout()
        self.new_step_action = QPushButton("Adicionar")
        self.new_step_action.setEnabled(False)
        self.new_step_action.clicked.connect(self.show_add_step_dialog)
        self.steps_table = StepsTable()
        steps_actions_layout.addWidget(self.new_step_action)
        steps_layout.addLayout(steps_actions_layout)
        steps_layout.addWidget(self.steps_table)
        steps_gb.setLayout(steps_layout)

        # Params Group
        params_gb = QGroupBox("Parâmetros")
        params_layout = QVBoxLayout()
        self.new_param_action = QPushButton("Adicionar")
        self.new_param_action.clicked.connect(self.show_add_param_dialog)
        self.params_table = ParamsTable()
        params_layout.addWidget(self.new_param_action)
        params_layout.addWidget(self.params_table)
        params_gb.setLayout(params_layout)

        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(details_gb)
        main_layout.addWidget(steps_gb)
        main_layout.addWidget(params_gb)
        self.setLayout(main_layout)

    def save_file(self):
        self.toggle_active_channels()
        directory_path = QFileDialog.getExistingDirectory(
            self,
            "Selecione um Diretório",
            "",
        )

        if directory_path:
            with open(f"{directory_path}/{TestSetup.get_group()}.yaml", "w") as file:
                yaml.dump(
                    TestSetup.get_data(),
                    file,
                    default_flow_style=False,
                    sort_keys=False,
                )

    def closeEvent(self, event) -> None:
        self.main_window.show()

    def input_type_toggled(self):
        if self.input_type_ca.isChecked():
            TestSetup.set_input_type("CA")
        elif self.input_type_cc.isChecked():
            TestSetup.set_input_type("CC")

    def toggle_active_channels(self):
        TestSetup.toggle_active_channels(
            self.ch1_cb.isChecked(),
            self.ch3_cb.isChecked(),
            self.ch4_cb.isChecked(),
            [self.ch1_field.text(), self.ch3_field.text(), self.ch4_field.text()],
        )
        if len(list(TestSetup.get_active_channels_list().keys())) > 0:
            self.new_step_action.setEnabled(True)
        else:
            self.new_step_action.setEnabled(False)

    def set_input_sources_labels(self):
        TestSetup.set_input_sources(
            [
                (
                    int(self.v1_input_field.text())
                    if self.v1_input_field.text() != ""
                    else 0
                ),
                (
                    int(self.v2_input_field.text())
                    if self.v2_input_field.text() != ""
                    else 0
                ),
                (
                    int(self.v3_input_field.text())
                    if self.v3_input_field.text() != ""
                    else 0
                ),
            ]
        )

    def show_add_step_dialog(self):
        dlg = StepDetailsDialog()
        if dlg.exec():
            data = dlg.get_data()
            self.steps_table.add_item(data)

    def show_add_param_dialog(self):
        dlg = ParamDetailsDialog()
        if dlg.exec():
            data = dlg.get_data()
            self.params_table.add_param(data)


class StepsTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setRowCount(0)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Descrição", "Ações"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.verticalHeader().setDefaultSectionSize(40)

    def refresh_table(self) -> None:
        self.setRowCount(0)
        for row, step in enumerate(TestSetup.get_step_list()):
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(step.get("description")))
            actions_item = self.custom_actions_widget()
            actions_item.setProperty("row", row)
            self.setCellWidget(row, 1, actions_item)

    def add_item(self, step: dict) -> None:
        TestSetup.add_step(step)
        self.refresh_table()

    def remove_item(self) -> None:
        index = self.sender().parent().property("row")
        TestSetup.remove_step(index)
        self.refresh_table()

    def edit_item(self) -> None:
        index = self.sender().parent().property("row")
        dlg = StepDetailsDialog(True, index)
        if dlg.exec():
            data = dlg.get_data()
            TestSetup.add_step(data, index)
        else:
            TestSetup.add_step(dlg.get_old_data(), index)
        self.refresh_table()

    def update_item_position(self, index: int, new_index: int) -> None:
        item = TestSetup.pop_step(index)
        TestSetup.add_step(item, new_index)
        self.refresh_table()

    def show_position_swap_dialog(self):
        index = self.sender().parent().property("row")
        dlg = SelectPositionDialog(len(TestSetup.get_step_list()))
        if dlg.exec():
            new_index = dlg.get_data()
            self.update_item_position(index, new_index)

    def custom_actions_widget(self) -> QWidget:
        actions_widget = QWidget()
        layout = QHBoxLayout()
        edit_bt = self.custom_action_button(QIcon("assets/icons/edit.png"))
        remove_bt = self.custom_action_button(QIcon("assets/icons/delete.png"))
        swapt_bt = self.custom_action_button(QIcon("assets/icons/swap_vert.png"))
        remove_bt.clicked.connect(self.remove_item)
        swapt_bt.clicked.connect(self.show_position_swap_dialog)
        edit_bt.clicked.connect(self.edit_item)
        layout.addWidget(edit_bt)
        layout.addWidget(remove_bt)
        layout.addWidget(swapt_bt)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        actions_widget.setLayout(layout)
        return actions_widget

    def custom_action_button(self, icon: QIcon) -> QPushButton:
        button = QPushButton()
        button.setFixedSize(QSize(32, 32))
        button.setFlat(True)
        button.setIconSize(button.sizeHint())
        button.setIcon(icon)
        return button


class ParamsTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setRowCount(0)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Descrição", "Ações"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.verticalHeader().setDefaultSectionSize(40)

    def refresh_table(self):
        self.setRowCount(0)
        for row, param in enumerate(TestSetup.get_params_list()):
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(param.get("tag")))
            actions_item = self.custom_actions_widget()
            actions_item.setProperty("row", row)
            self.setCellWidget(row, 1, actions_item)

    def add_param(self, param: dict):
        TestSetup.add_param(param)
        self.refresh_table()

    def remove_param(self):
        index = self.sender().parent().property("row")
        TestSetup.remove_param(index)
        self.refresh_table()

    def edit_param(self):
        index = self.sender().parent().property("row")
        dlg = ParamDetailsDialog(True, index)
        if dlg.exec():
            data = dlg.get_data()
            TestSetup.add_param(data, index)
        else:
            TestSetup.add_param(dlg.get_old_data(), index)
        self.refresh_table()

    def custom_actions_widget(self) -> QWidget:
        actions_widget = QWidget()
        layout = QHBoxLayout()
        edit_bt = self.custom_action_button(QIcon("assets/icons/edit.png"))
        remove_bt = self.custom_action_button(QIcon("assets/icons/delete.png"))
        remove_bt.clicked.connect(self.remove_param)
        edit_bt.clicked.connect(self.edit_param)
        layout.addWidget(edit_bt)
        layout.addWidget(remove_bt)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        actions_widget.setLayout(layout)
        return actions_widget

    def custom_action_button(self, icon: QIcon) -> QPushButton:
        button = QPushButton()
        button.setFixedSize(QSize(32, 32))
        button.setFlat(True)
        button.setIconSize(button.sizeHint())
        button.setIcon(icon)
        return button


class SelectPositionDialog(QDialog):
    def __init__(self, list_length: int):
        super().__init__()
        layout = QVBoxLayout()
        self.setFont(QFont("Arial", 14))
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(1)
        self.spinbox.setMaximum(list_length)
        self.spinbox.lineEdit().setReadOnly(True)

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout.addWidget(QLabel("Mover para qual posição?"))
        layout.addWidget(self.spinbox)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def get_data(self) -> int:
        return self.spinbox.value() - 1


class ParamDetailsDialog(QDialog):
    def __init__(
        self,
        is_edit: bool = False,
        edit_index: int = -1,
    ):
        super().__init__()
        self.params_list = TestSetup.get_params_list()
        self.is_edit = is_edit
        self.edit_index = edit_index
        self.setWindowTitle("Detalhes")
        self.setFont(QFont("Arial", 14))

        self.tag_field = QLineEdit()
        self.voltage_under_sb = self.custom_spinbox("V")
        self.voltage_upper_sb = self.custom_spinbox("V")
        self.voltage_lower_sb = self.custom_spinbox("V")
        self.static_load_sb = self.custom_spinbox("A")
        self.end_load_sb = self.custom_spinbox("A")
        self.load_upper_sb = self.custom_spinbox("A")
        self.load_lower_sb = self.custom_spinbox("A")
        self.load_increase_step_sb = self.custom_spinbox("A")

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        voltage_gb = QGroupBox("Tensão")
        load_gb = QGroupBox("Carga")
        voltage_layout = QFormLayout()
        load_layout = QFormLayout()
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Descrição"))
        tag_layout.addWidget(self.tag_field)
        voltage_layout.addRow("Máxima", self.voltage_upper_sb)
        voltage_layout.addRow("Minima", self.voltage_lower_sb)
        voltage_layout.addRow("Limite Inferior", self.voltage_under_sb)
        load_layout.addRow("Base", self.static_load_sb)
        load_layout.addRow("Máxima", self.load_upper_sb)
        load_layout.addRow("Minima", self.load_lower_sb)
        load_layout.addRow("Limite Superior", self.end_load_sb)
        load_layout.addRow("Incremento", self.load_increase_step_sb)

        voltage_gb.setLayout(voltage_layout)
        load_gb.setLayout(load_layout)

        layout.addLayout(tag_layout)
        layout.addWidget(voltage_gb)
        layout.addWidget(load_gb)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        if self.is_edit:
            self.set_values()

    def set_values(self):
        self.old_data = TestSetup.pop_param(self.edit_index)
        self.tag_field.setText(self.old_data.get("tag"))
        self.voltage_upper_sb.setValue(self.old_data.get("voltage_upper"))
        self.voltage_lower_sb.setValue(self.old_data.get("voltage_lower"))
        self.voltage_under_sb.setValue(self.old_data.get("voltage_under_limit"))
        self.static_load_sb.setValue(self.old_data.get("static_load"))
        self.load_upper_sb.setValue(self.old_data.get("load_upper"))
        self.load_lower_sb.setValue(self.old_data.get("load_lower"))
        self.end_load_sb.setValue(self.old_data.get("end_load"))
        self.load_increase_step_sb.setValue(self.old_data.get("increase_step"))

    def get_old_data(self):
        return self.old_data

    def get_data(self):
        return {
            "tag": self.tag_field.text(),
            "voltage_under_limit": self.voltage_under_sb.value(),
            "voltage_upper": self.voltage_upper_sb.value(),
            "voltage_lower": self.voltage_lower_sb.value(),
            "static_load": self.static_load_sb.value(),
            "end_load": self.end_load_sb.value(),
            "load_upper": self.load_upper_sb.value(),
            "load_lower": self.load_lower_sb.value(),
            "increase_step": self.load_increase_step_sb.value(),
        }

    def custom_spinbox(self, suffix: str) -> QDoubleSpinBox:
        spinbox = QDoubleSpinBox()
        spinbox.setMinimum(0)
        spinbox.setMaximum(80)
        spinbox.setSuffix(suffix)

        return spinbox


class StepDetailsDialog(QDialog):
    def __init__(
        self,
        is_edit: bool = False,
        edit_index: int = -1,
    ):
        super().__init__()
        self.params_list = TestSetup.get_params_list()
        self.active_channels = TestSetup.get_active_channels_list().keys()
        self.is_edit = is_edit
        self.edit_index = edit_index
        self.setWindowTitle("Detalhes")
        self.setFont(QFont("Arial", 14))

        self.description_field = QLineEdit()
        self.duration_sb = QDoubleSpinBox()
        self.duration_sb.setMinimum(0)
        self.duration_sb.setMaximum(60)
        self.duration_sb.setSuffix("s")
        self.type_cb = QComboBox()
        self.type_cb.addItems(
            ["Corrente Continua", "Limitação de Corrente", "Curto Automático"]
        )
        self.type_cb.currentIndexChanged.connect(self.handle_step_type_change)

        self.inputs_cb = QComboBox()
        input_labels = TestSetup.get_input_sources()
        self.inputs_cb.addItems(
            [
                f"V1 - {input_labels[0]}",
                f"V2 - {input_labels[1]}",
                f"V3 - {input_labels[2]}",
            ]
        )
        params_list = [
            f"P{param.get("id")} - {param.get("tag")}" for param in self.params_list
        ]
        self.ch1_param_cb = QComboBox()
        self.ch3_param_cb = QComboBox()
        self.ch4_param_cb = QComboBox()
        self.ch1_param_cb.addItems(params_list)
        self.ch3_param_cb.addItems(params_list)
        self.ch4_param_cb.addItems(params_list)

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QFormLayout()
        layout.addRow("Descrição", self.description_field)
        layout.addRow("Tipo", self.type_cb)
        layout.addRow("Duração (s)", self.duration_sb)
        layout.addRow("Entrada", self.inputs_cb)

        if self.is_edit:
            self.set_values()
        else:
            self.ch1_param_cb.setVisible("1" in self.active_channels)
            self.ch3_param_cb.setVisible("3" in self.active_channels)
            self.ch4_param_cb.setVisible("4" in self.active_channels)

        if self.ch1_param_cb.isVisible():
            layout.addRow("Canal 1", self.ch1_param_cb)
        if self.ch3_param_cb.isVisible():
            layout.addRow("Canal 3", self.ch3_param_cb)
        if self.ch4_param_cb.isVisible():
            layout.addRow("Canal 4", self.ch4_param_cb)
        layout.addRow(self.buttonBox)

        self.setLayout(layout)

    def handle_step_type_change(self):
        if self.type_cb.currentIndex() != 0:
            self.duration_sb.setValue(0)
            self.duration_sb.setReadOnly(True)
        else:
            self.duration_sb.setReadOnly(False)

    def set_values(self):
        self.old_data = TestSetup.pop_step(self.edit_index)
        self.type_cb.setCurrentIndex(self.old_data.get("step_type") - 1)
        self.description_field.setText(self.old_data.get("description"))
        self.duration_sb.setValue(self.old_data.get("duration"))
        self.inputs_cb.setCurrentIndex(self.old_data.get("input_source") - 1)
        for channel in self.old_data.get("channels_configuration"):
            match channel["channel_id"]:
                case 1:
                    self.ch1_param_cb.setVisible(True)
                    self.ch1_param_cb.setCurrentIndex(channel["parameters_id"] - 1)
                case 3:
                    self.ch3_param_cb.setVisible(True)
                    self.ch3_param_cb.setCurrentIndex(channel["parameters_id"] - 1)
                case 4:
                    self.ch4_param_cb.setVisible(True)
                    self.ch4_param_cb.setCurrentIndex(channel["parameters_id"] - 1)

    def get_old_data(self):
        return self.old_data

    def get_data(self):
        channels_config = []
        if "1" in self.active_channels:
            channels_config.append(
                {"channel_id": 1, "parameters_id": self.ch1_param_cb.currentIndex() + 1}
            )
        if "3" in self.active_channels:
            channels_config.append(
                {"channel_id": 3, "parameters_id": self.ch3_param_cb.currentIndex() + 1}
            )
        if "4" in self.active_channels:
            channels_config.append(
                {"channel_id": 4, "parameters_id": self.ch4_param_cb.currentIndex() + 1}
            )

        return {
            "step_type": self.type_cb.currentIndex() + 1,
            "description": self.description_field.text(),
            "duration": self.duration_sb.value(),
            "input_source": self.inputs_cb.currentIndex() + 1,
            "channels_configuration": channels_config,
        }
