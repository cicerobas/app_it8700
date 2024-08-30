from PySide6.QtCore import QRunnable, QMutex, QWaitCondition, QMutexLocker
from time import sleep

from widgets.channel_monitor import ChannelMonitor
from controllers.sat_controller import ElectronicLoadController


class MonitorWorker(QRunnable):
    def __init__(
        self,
        channels: list[ChannelMonitor],
        sat_controller: ElectronicLoadController,
    ):
        super().__init__()
        self.channels = channels
        self.sat_controller = sat_controller
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.paused = False
        self.running = True

    def run(self):
        while self.running:
            self.mutex.lock()
            while self.paused:
                self.wait_condition.wait(
                    self.mutex
                )  # Pausa até que seja sinalizado para continuar
            self.mutex.unlock()

            for channel in self.channels:
                result = self.sat_controller.get_channel_value(channel.channel_id)
                channel.update_output(result)
                sleep(0.1)

    def pause(self):
        with QMutexLocker(self.mutex):
            self.paused = True

    def resume(self):
        with QMutexLocker(self.mutex):
            self.paused = False
            self.wait_condition.wakeAll()  # Notifica a thread para continuar

    def stop(self):
        with QMutexLocker(self.mutex):
            self.running = False
            self.paused = False
            self.wait_condition.wakeAll()  # Garante que a thread saia do estado de pausa
