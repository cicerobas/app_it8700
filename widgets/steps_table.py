from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from models.test_file_model import Step


class StepsTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Arial", 14))
        self.setRowCount(0)
        self.setColumnCount(3)
        self.setFixedWidth(520)
        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 100)
        self.setColumnWidth(2, 100)
        self.setHorizontalHeaderLabels(["Descrição", "Tempo", "Status"])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    def update_step_list(self, steps: list[Step]) -> None:
        self.setRowCount(0)
        for row, step in enumerate(steps):
            self.insertRow(row)
            duration = QTableWidgetItem(str(step.duration))
            status = QTableWidgetItem("---")
            duration.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.setItem(row, 0, QTableWidgetItem(step.description))
            self.setItem(row, 1, duration)
            self.setItem(row, 2, status)

    def set_selected_step(self, index: int):
        self.selectRow(index)

    def update_duration(self, new_value):
        item = QTableWidgetItem(str(new_value))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(self.currentRow(), 1, item)

    def set_step_status(self, status: bool):
        item = QTableWidgetItem("PASS" if status else "FAIL")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setForeground(QBrush(QColor("green" if status else "red")))
        self.setItem(self.currentRow(), 2, item)

    def reset_table_status_fields(self):
        row = 0
        self.clearSelection()
        while row < self.rowCount():
            status = QTableWidgetItem("---")
            status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status.setForeground(QBrush(QColor("black")))
            self.setItem(row, 2, status)
            row += 1
