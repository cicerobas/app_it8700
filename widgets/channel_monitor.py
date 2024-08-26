from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel
from PySide6.QtGui import QFont


class ChannelMonitor(QGroupBox):
    def __init__(self, title: str):
        super().__init__()
        self.setTitle(title)
        self.setFixedSize(QSize(500, 150))
        self.setStyleSheet(
            "QGroupBox { border: 2px solid gray; border-radius: 5px; padding: 10px; }"
            "QGroupBox:title { subcontrol-position: top center; padding: 0 10px; }"
        )

        h_layout = QHBoxLayout()
        self.setLayout(h_layout)

        v_output_layout = QVBoxLayout()
        self.v_output_label = QLabel("Saída:")
        self.v_output_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.v_output_label.setAlignment(Qt.AlignTop)

        self.v_output_value = QLabel("00.00 V")
        self.v_output_value.setFont(QFont("Arial", 24, QFont.Bold))
        self.v_output_value.setAlignment(Qt.AlignCenter)
        self.v_output_value.setStyleSheet("border: 1px solid gray; padding: 5px;")
        self.v_output_value.setScaledContents(True)
        self.v_output_value.setFixedHeight(80)

        v_output_layout.addWidget(self.v_output_label)
        v_output_layout.addWidget(self.v_output_value)

        h_layout.addLayout(v_output_layout)

        grid_layout = QGridLayout()

        self.vmax_value = defaut_value_field()
        self.vmin_value = defaut_value_field()
        self.load_value = defaut_value_field()
        self.power_value = defaut_value_field()

        label_font = QFont("Arial", 12)
        vmax_label = QLabel("V Max")
        vmax_label.setFont(label_font)
        vmin_label = QLabel("V Min")
        vmin_label.setFont(label_font)
        load_label = QLabel("Carga")
        load_label.setFont(label_font)
        power_label = QLabel("Potência")
        power_label.setFont(label_font)

        grid_layout.addWidget(vmax_label, 0, 0, Qt.AlignRight)
        grid_layout.addWidget(self.vmax_value, 0, 1)
        grid_layout.addWidget(vmin_label, 1, 0, Qt.AlignRight)
        grid_layout.addWidget(self.vmin_value, 1, 1)
        grid_layout.addWidget(load_label, 2, 0, Qt.AlignRight)
        grid_layout.addWidget(self.load_value, 2, 1)
        grid_layout.addWidget(power_label, 3, 0, Qt.AlignRight)
        grid_layout.addWidget(self.power_value, 3, 1)

        h_layout.addLayout(grid_layout)

    def update_fixed_values(self, values:list[str]) -> None:
        # values = ['Vmax', 'Vmin', 'Load']
        self.vmax_value.setText(f'{values[0]} V')
        self.vmin_value.setText(f'{values[1]} V')
        self.load_value.setText(f'{values[2]} A')


def defaut_value_field() -> QLabel:
    label = QLabel("0.0")
    label.setFont(QFont("Arial", 12))
    label.setAlignment(Qt.AlignCenter)
    label.setFixedHeight(25)
    label.setStyleSheet("border: 1px solid gray; padding: 5px;")
    return label