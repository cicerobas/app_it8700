import yaml
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCloseEvent, QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPlainTextEdit,
    QGroupBox,
    QRadioButton,
    QPushButton,
    QLabel,
    QFrame,
)

from controllers.arduino_controller import ArduinoController


def custom_channel_label(channel_id: int, text: str) -> QLabel:
    label = QLabel(f"Canal {channel_id}\n{text}")
    label.setFont(QFont("Arial", 18, 600))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setMinimumWidth(150)
    label.setStyleSheet("border: 2px solid grey; padding: 5px;border-radius: 10px;")
    return label


def custom_group_box(box_title: str, fixed_height: int) -> QGroupBox:
    custom_gb = QGroupBox(title=box_title)
    custom_gb.setFont(QFont("Arial", 16))
    custom_gb.setFixedHeight(fixed_height)
    return custom_gb


class TestSetupView(QWidget):
    def __init__(self, arduino: ArduinoController, main_window: QMainWindow):
        super().__init__()
        self.main_window = main_window
        self.arduino_controller = arduino
        self.file_path = None
        self.data = None
        self.selected_input = None

        self.setWindowTitle("CEBRA - Test Setup")
        self.setMinimumSize(QSize(900, 600))
        # Header
        self.header_info_label = QLabel()
        self.header_info_label.setFont(QFont("Arial", 18, 500))

        # Entradas
        self.input_sources_gb = custom_group_box("Entradas", 200)
        self.input_sources_gb.setFixedWidth(250)
        self.input_1 = QRadioButton()
        self.input_2 = QRadioButton()
        self.input_3 = QRadioButton()
        self.test_input_button = QPushButton(QIcon("assets/icons/bolt.png"), "Testar")
        self.test_input_button.clicked.connect(self.test_input_source)

        self.v_inputs_layout = QVBoxLayout()
        self.v_inputs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_inputs_layout.addWidget(self.input_1)
        self.v_inputs_layout.addWidget(self.input_2)
        self.v_inputs_layout.addWidget(self.input_3)
        self.v_inputs_layout.addWidget(self.test_input_button)

        self.input_sources_gb.setLayout(self.v_inputs_layout)

        # Canais
        self.channels_gb = custom_group_box("Canais", 200)
        self.h_channels_layout = QHBoxLayout()
        self.h_channels_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.channels_gb.setLayout(self.h_channels_layout)

        # Observações
        self.notes_gb = QGroupBox("Observações")
        self.notes_gb.setFont(QFont("Arial", 16))

        self.v_notes_layout = QVBoxLayout()
        self.text_edit = QPlainTextEdit()
        self.text_edit.setFont(QFont("Courier New", 14))
        self.save_button = QPushButton(QIcon("assets/icons/save.png"), "Salvar")
        self.save_button.setFixedWidth(100)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_changes)
        self.v_notes_layout.addWidget(self.text_edit)
        self.v_notes_layout.addWidget(self.save_button)
        self.notes_gb.setLayout(self.v_notes_layout)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        divider.setStyleSheet("background-color: black;")

        v_primary_layout = QVBoxLayout()
        v_primary_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        h_secondary_layout = QHBoxLayout()
        h_secondary_layout.addWidget(self.input_sources_gb)
        h_secondary_layout.addWidget(self.channels_gb)
        v_primary_layout.addWidget(self.header_info_label)
        v_primary_layout.addWidget(divider)
        v_primary_layout.addLayout(h_secondary_layout)
        v_primary_layout.addWidget(self.notes_gb)
        self.setLayout(v_primary_layout)

    def load_file(self):
        with open(self.file_path, "r") as file:
            self.data = yaml.safe_load(file.read())

        self.set_input_radio_buttons()
        self.set_channel_labels()
        self.set_notes_text()
        self.set_header_info()

    def set_header_info(self):
        self.header_info_label.setText(
            f"Grupo: {self.data["group"]} | Modelo: {self.data["model"]} | Cliente: {self.data["customer"]}"
        )

    def set_input_radio_buttons(self) -> None:
        self.input_1.setText(
            f' {self.data["input_sources"][0]}V {self.data["input_type"]}'
        )
        self.input_2.setText(
            f' {self.data["input_sources"][1]}V {self.data["input_type"]}'
        )
        self.input_3.setText(
            f' {self.data["input_sources"][2]}V {self.data["input_type"]}'
        )

    def set_channel_labels(self):
        while self.h_channels_layout.count():
            item = self.h_channels_layout.takeAt(0)
            item.widget().deleteLater()

        for channel in self.data["active_channels"]:
            self.h_channels_layout.addWidget(
                custom_channel_label(channel["id"], channel["label"])
            )

    def set_notes_text(self):
        self.text_edit.setPlainText(self.data["notes"])
        self.text_edit.modificationChanged.connect(self.toggle_save_button)

    def test_input_source(self):
        if self.arduino_controller is None:
            return
        for index, input_source in enumerate(
            [self.input_1, self.input_2, self.input_3], 1
        ):
            if input_source.isChecked():
                self.arduino_controller.set_input_source(index, self.data["input_type"])
                self.selected_input = index

    def toggle_save_button(self, changed: bool):
        self.save_button.setEnabled(changed)

    def save_changes(self):
        self.data["notes"] = self.text_edit.toPlainText()
        self.save_button.setEnabled(False)

        with open(self.file_path, "w") as file:
            yaml.dump(self.data, file, default_flow_style=False, sort_keys=False)

    def showMaximized(self) -> None:
        if self.file_path:
            self.load_file()
        return super().show()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.selected_input is not None:
            self.arduino_controller.set_active_pin(True)

        self.main_window.show()
        event.accept()
