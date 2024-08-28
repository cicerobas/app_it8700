from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from models.test_file_model import Step


class StepsTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Arial", 14))
        self.setRowCount(0)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Descrição", "Tempo", "Status"])
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        
    def update_step_list(self, steps: list[Step]) -> None:
        self.setRowCount(0)
        for row, step in enumerate(steps):
            self.insertRow(row)
            duration = QTableWidgetItem(str(step.duration))
            duration.setTextAlignment(Qt.AlignCenter)
            status = QTableWidgetItem("---")
            status.setTextAlignment(Qt.AlignCenter)

            self.setItem(row, 0, QTableWidgetItem(step.description))
            self.setItem(row, 1, duration)
            self.setItem(row, 2, status)

    def set_selected_step(self, index: int):
        self.selectRow(index)

    def update_duration(self, new_value: str):
        self.setItem(self.currentRow(), 1, QTableWidgetItem(new_value))
        
        
