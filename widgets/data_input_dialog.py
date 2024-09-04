from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QLabel, QDialogButtonBox
from PySide6.QtGui import QIntValidator

class DataInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Informe os dados")

        layout = QFormLayout(self)

        self.number_input = QLineEdit()
        self.number_input.setValidator(QIntValidator(0, 99999999, self))  # Aceita números até 8 dígitos
        self.operator_input = QLineEdit()

        layout.addRow(QLabel("Nº de série:"), self.number_input)
        layout.addRow(QLabel("Operador:"), self.operator_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)

    def get_values(self):
        return self.number_input.text(), self.operator_input.text()