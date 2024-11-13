from PySide6.QtCore import QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QVBoxLayout, QWidget, QPlainTextEdit


class TestResultView(QWidget):
    def __init__(self, text: str = ""):
        super().__init__()
        self.text = text
        self.text_edit = QPlainTextEdit()
        self.text_edit.setFont(QFont("Courier New", 14))
        self.setWindowTitle("CEBRA - Power Supply Test Report")
        self.setMinimumSize(QSize(900, 600))

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def show(self) -> None:
        self.text_edit.setPlainText(self.text)
        return super().show()
