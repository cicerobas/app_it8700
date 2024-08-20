import sys
import json

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont
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
    QSizePolicy
)

from controllers.sat_controller import ElectronicLoadController
from models.test_file_model import Test
from widgets.channel_monitor import ChannelMonitor
from widgets.steps_table import StepsTable

active_test = None


def info_label(text: str) -> QLabel:
    font = QFont()
    font.setPointSize(16)
    label = QLabel(text)
    label.setFont(font)
    return label


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sat_controller = ElectronicLoadController()
        self.setMinimumSize(QSize(800, 600))
        self.setWindowTitle(
            f"CEBRA - {self.sat_controller.inst_id}"
            if self.sat_controller.conn_status
            else "CEBRA - IT8700 Sem Conexão"
        )

        # Actions
        open_file_action = QAction(
            QIcon("assets/icons/file_open.png"), "Open File", self
        )
        open_file_action.triggered.connect(self.open_test_file)

        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
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

    def update_test_info(self):
        self.group_value.setText(active_test.group)
        self.model_value.setText(active_test.model)
        self.steps_table.update_step_list(active_test.steps)
        
        for channel in active_test.active_channels:
            self.channels_layout.addWidget(ChannelMonitor(f"Canal {channel.id}"))

        self.steps_table.resizeColumnsToContents()
        total_width = sum(self.steps_table.columnWidth(i) for i in range(self.steps_table.columnCount()))
        self.steps_table.setFixedWidth(total_width+30)
        self.steps_table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        

    def open_test_file(self):
        global active_test
        fileName = QFileDialog.getOpenFileName(
            self, filter="*.json", caption="Abrir arquivo de teste..."
        )[0]
        if fileName != "":
            print(fileName)
            with open(fileName) as loaded_file:
                test_data = json.load(loaded_file)
            try:
                active_test = Test(**test_data)
            except:
                print("ERRO, arquivo inválido!")

        if active_test is not None:
            self.update_test_info()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()  # .showFullScreen()
    sys.exit(app.exec())
