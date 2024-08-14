import sys
import json

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog

from controllers.sat_controller import ElectronicLoadController
from models.test_file_model import Test

active_test = None

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

        open_file_action = QAction(QIcon("assets/icons/file_open.png"), "Open File", self)
        open_file_action.triggered.connect(self.open_test_file)

        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(open_file_action)

    def open_test_file(self):
        fileName = QFileDialog.getOpenFileName(self, filter="*.json", caption="Abrir arquivo de teste...")[0]
        if fileName != "":
            print(fileName)
            with open(fileName) as loaded_file:
                test_data = json.load(loaded_file)
            try:
                active_test = Test(**test_data)
                print(active_test.customer) # Teste
            except:
                print("ERRO, arquivo inválido!")
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized() # .showFullScreen()
    sys.exit(app.exec())
