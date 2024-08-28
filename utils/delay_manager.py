from PySide6.QtCore import QTimer, Signal, QObject

class DelayManager(QObject):
    delay_completed = Signal()
    remaining_time_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_complete)
        self.remaining_time = 0
    
    def start_delay(self, delay):
        self.remaining_time  = delay
        self.timer.start(delay)
        self.update_timer()

    def update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 100
            QTimer.singleShot(100, self.update_timer)
        self.remaining_time_changed.emit(self.remaining_time)

    def on_complete(self):
        self.delay_completed.emit()