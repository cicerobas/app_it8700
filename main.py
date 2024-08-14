import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton

from controllers.sat_controller import ElectronicLoadController


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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized() # .showFullScreen()
    sys.exit(app.exec())
