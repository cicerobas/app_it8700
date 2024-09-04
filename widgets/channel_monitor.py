from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel
from PySide6.QtGui import QFont


class Data:
    output: float = 0
    vmax: float = 0
    vmin: float = 0
    load: float = 0
    power: float = 0


class ChannelMonitor(QGroupBox):
    def __init__(self, channel: int):
        super().__init__()
        self.channel_id = channel
        self.data = Data()

        self.setTitle(f"Canal {self.channel_id}")
        self.setFixedSize(QSize(500, 150))
        self.setStyleSheet(
            "QGroupBox { border: 2px solid gray; border-radius: 5px; padding: 10px; }"
            "QGroupBox:title { subcontrol-position: top center; padding: 0 10px; }"
        )

        # Layouts
        h_container_layout = QHBoxLayout()
        v_output_field_layout = QVBoxLayout()
        g_fixed_values_layout = QGridLayout()

        self.setLayout(h_container_layout)

        # Labels
        self.output_label = QLabel("Saída:")
        self.output_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.output_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        vmax_label = defaut_field_name_label("V Max")
        vmin_label = defaut_field_name_label("V Min")
        load_label = defaut_field_name_label("Carga")
        power_label = defaut_field_name_label("Potência")

        # Value Fields
        self.output_value = QLabel("00.00 V")
        self.output_value.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.output_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.output_value.setStyleSheet("border: 1px solid gray; padding: 5px;")
        self.output_value.setScaledContents(True)
        self.output_value.setFixedHeight(80)

        self.vmax_value = defaut_field_value_label()
        self.vmin_value = defaut_field_value_label()
        self.load_value = defaut_field_value_label()
        self.power_value = defaut_field_value_label()

        # Layouts Setup
        v_output_field_layout.addWidget(self.output_label)
        v_output_field_layout.addWidget(self.output_value)

        g_fixed_values_layout.addWidget(vmax_label, 0, 0, Qt.AlignmentFlag.AlignRight)
        g_fixed_values_layout.addWidget(self.vmax_value, 0, 1)
        g_fixed_values_layout.addWidget(vmin_label, 1, 0, Qt.AlignmentFlag.AlignRight)
        g_fixed_values_layout.addWidget(self.vmin_value, 1, 1)
        g_fixed_values_layout.addWidget(load_label, 2, 0, Qt.AlignmentFlag.AlignRight)
        g_fixed_values_layout.addWidget(self.load_value, 2, 1)
        g_fixed_values_layout.addWidget(power_label, 3, 0, Qt.AlignmentFlag.AlignRight)
        g_fixed_values_layout.addWidget(self.power_value, 3, 1)

        h_container_layout.addLayout(v_output_field_layout)
        h_container_layout.addLayout(g_fixed_values_layout)

    def update_fixed_values(self, values: list[str]) -> None:
        # values = ['Vmax', 'Vmin', 'Load']
        self.data.vmax = float(values[0])
        self.data.vmin = float(values[1])
        self.data.load = float(values[2])
        self.set_fixed_value_fields()

    def set_fixed_value_fields(self):
        self.vmax_value.setText(f"{self.data.vmax} V")
        self.vmin_value.setText(f"{self.data.vmin} V")
        self.load_value.setText(f"{self.data.load} A")

    def update_output_value(self, value: str):
        self.data.output = float(value)
        background_color = "#81C784"
        self.output_value.setText(f'{"%.2f" % self.data.output} V')
        if self.data.output > self.data.vmax:
            background_color = "#E57373"
        elif self.data.output < self.data.vmin:
            background_color = "#FFF176"

        self.output_value.setStyleSheet(f"background-color:{background_color};")
        self.update_power_value()

    def update_power_value(self):
        self.data.power = self.data.load * self.data.output
        if self.data.power > 100:
            fmt_value = str(int(self.data.power))

        fmt_value = "%.2f" % self.data.power
        self.power_value.setText(f"{fmt_value} W")


def defaut_field_name_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setFont(QFont("Arial", 12))
    return label


def defaut_field_value_label() -> QLabel:
    label = QLabel("0.0")
    label.setFont(QFont("Arial", 12))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFixedHeight(25)
    label.setStyleSheet("border: 1px solid gray; padding: 5px;")
    return label
