from time import sleep

import pyvisa

from utils.scpi_commands import *

# Default instrument path using a USB/RS-232 adapter.
DEFAULT_INST_PATH = "ASRL/dev/ttyUSB0::INSTR"


class ElectronicLoadController:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.conn_status = False
        self.inst_id = ""
        self.inst_resource = self.setup_connection()
        self.active_channel = 0

    def setup_connection(self):
        if DEFAULT_INST_PATH in self.rm.list_resources():
            inst = self.rm.open_resource(DEFAULT_INST_PATH)
            inst.baud_rate = 115200
            self.conn_status = True
            id_response = inst.query(INST_ID)
            self.inst_id = id_response.strip()
            inst.write(SYSTEM_REMOTE)
            inst.write(CLEAR_STATUS)

            return inst

        return None

    def _sat_write(self, command: str) -> None:
        self.inst_resource.write(command)

    def _sat_query(self, command: str) -> str:
        return self.inst_resource.query(command)

    def select_channel(self, channel_id: int) -> None:
        if self.active_channel == channel_id:
            return
        self.active_channel = channel_id
        self._sat_write(f"{SELECT_CHANNEL}{channel_id}")

    def toggle_active_channels_input(self, channels: list[int], state: bool) -> None:
        for channel in channels:
            self.select_channel(channel)
            self._sat_write(INPUT_ON if state else INPUT_OFF)

    def get_channel_value(self, channel_id: int) -> str:
        self.select_channel(channel_id)
        return self._sat_query(FETCH_VOLT)

    def set_channel_current(self, channel_id: int, load: float) -> None:
        self.select_channel(channel_id)
        self._sat_write(f"{SET_CURR}{load}")
        sleep(0.1)

    def toggle_short_mode(self, channel_id: int, state: bool) -> None:
        self.select_channel(channel_id)
        self._sat_write(SHORT_ON if state else SHORT_OFF)
