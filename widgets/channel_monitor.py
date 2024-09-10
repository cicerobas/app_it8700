from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QGroupBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont


class Data:
    voltage_output: float = 0
    voltage_upper: float = 0
    voltage_lower: float = 0
    load: float = 0
    load_upper: float = 0
    load_lower: float = 0
    power: float = 0


class ChannelMonitor(QGroupBox):
    def __init__(self, channel_id:int, channel_label:str):
        super().__init__()
        self.channel_id = channel_id
        self.channel_label = channel_label
        self.data = Data()
        self.setFixedSize(QSize(500, 160))
        self.setStyleSheet("QGroupBox { border: 2px solid gray; border-radius: 5px; }")

        self.channel_id_label = custom_label(f"Canal {self.channel_id}", 14, 500)
        self.channel_description_label = custom_label(self.channel_label, 14, 500)
        self.voltage_value_label = custom_label("0.00 V", 36, 700)
        self.load_value_label = custom_label("0.00 A", 36, 700)
        self.step_info_label = custom_label(
            "V (0.00 ~ 0.00)  |  A (0.00 ~ 0.00)  |  Potência: 0.00W", 12, 400
        )

        h_header_layout = QHBoxLayout()
        h_header_layout.addWidget(self.channel_id_label, 0, Qt.AlignmentFlag.AlignLeft)
        h_header_layout.addWidget(
            self.channel_description_label, 0, Qt.AlignmentFlag.AlignRight
        )
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Raised)

        h_values_layout = QHBoxLayout()
        h_values_layout.addWidget(
            self.voltage_value_label, 0, Qt.AlignmentFlag.AlignLeft
        )
        h_values_layout.addWidget(separator)
        h_values_layout.addWidget(self.load_value_label, 0, Qt.AlignmentFlag.AlignRight)
        values_frame = QFrame()
        values_frame.setFrameShape(QFrame.StyledPanel)
        values_frame.setFrameShadow(QFrame.Raised)
        values_frame.setLayout(h_values_layout)
        values_frame.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        v_main_layout = QVBoxLayout()
        v_main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_main_layout.addLayout(h_header_layout)
        v_main_layout.addWidget(values_frame)
        v_main_layout.addWidget(self.step_info_label, 0, Qt.AlignmentFlag.AlignJustify)

        self.setLayout(v_main_layout)
    
    def update_step_values(self, values: list[str]) -> None:
        # values = ['VoltageUpper', 'VoltageLower', 'LoadUpper', 'LoadLower']
        self.data.voltage_upper = float(values[0]) if values[0] else 0.0
        self.data.voltage_lower = float(values[1]) if values[1] else 0.0
        self.data.load_upper = float(values[2]) if values[2] else 0.0
        self.data.load_lower = float(values[3]) if values[3] else 0.0
        self.set_info_label_values()

    def set_info_label_values(self):
        self.step_info_label.setText(f"V ({self.data.voltage_upper} ~ {self.data.voltage_lower})  |  A ({self.data.load_upper} ~ {self.data.load_lower})  |  Potência: {"%.2f" % self.data.power}W")

    def update_load_value(self, value):
        self.data.load = float(value)
        self.load_value_label.setText(f'{"%.2f" % self.data.load} A')

    def update_voltage_value(self, value):
        self.data.voltage_output = float(value)
        self.voltage_value_label.setText(f'{"%.2f" % self.data.voltage_output} V')
        self.update_power_value()
    
    def update_power_value(self):
        self.data.power = self.data.load * self.data.voltage_output
        self.set_info_label_values()

def custom_label(text: str, font_size: int, weight: int) -> QLabel:
    label = QLabel(text)
    label.setFont(QFont("Arial", font_size, weight))
    return label
