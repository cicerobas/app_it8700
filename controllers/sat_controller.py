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

    def setup_connection(self):
        if DEFAULT_INST_PATH in self.rm.list_resources():
            inst = self.rm.open_resource(DEFAULT_INST_PATH)
            inst.baud_rate = 115200
            self.conn_status = True
            id_response = inst.query(INST_ID)
            self.inst_id = id_response.strip()
            inst.write(SYSTEM_REMOTE)
            inst.write(CLEAR_STATUS)
            inst.write(ALL_INPUTS_ON) #TESTE APENAS
            return inst

        return None

    def _sat_write(self, command: str) -> None:
        self.inst_resource.write(command)

    def _sat_query(self, command: str) -> str:
        result = self.inst_resource.query(command)
        return result

    def set_active_channel(self, channel_id: int) -> None:
        self._sat_write(f"{SELECT_CHANNEL}{channel_id}")

    def get_channel_value(self, channel_id: int) -> str:
        self.set_active_channel(channel_id)
        result = self._sat_query(FETCH_VOLT)
        return result
