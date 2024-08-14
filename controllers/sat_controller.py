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
            return inst
        
        return None