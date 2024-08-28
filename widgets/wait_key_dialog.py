from PySide6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent


class WaitKeyDialog(QDialog):
    def __init__(self, description: str):
        super().__init__()
        self.description = description
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(500, 120)

        layout = QVBoxLayout()
        self.message_label = QLabel(
            f"{self.description}\nAperte ENTER para continuar", self
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)
        self.setLayout(layout)

        self.setStyleSheet(
            """background-color: #FFE082;border: 2px solid black;font-size: 28px;font-weight: 600;"""
        )

        self.center()

    def center(self):
        # Obtém a geometria da tela e calcula a posição central
        screen_geometry = QApplication.primaryScreen().geometry()
        dialog_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        dialog_geometry.moveCenter(center_point)
        self.move(dialog_geometry.topLeft())

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return:
            self.accept()
        else:
            super().keyPressEvent(event)
