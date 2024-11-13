from time import sleep

import pyvisa

from utils.arduino_interface import Arduino

# Default instrument path for Arduino.
ARDU_INST_PATH = "ASRL/dev/ttyACM0::INSTR"


class ArduinoController:
    """
    Used to control the connection with Arduino and run commands using pyduino interface.
    """

    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.arduino = None
        if ARDU_INST_PATH in self.rm.list_resources():
            self.arduino = Arduino()

        self.output_pins = {
            "4": False,
            "5": False,
            "6": False,
            "7": False,
            "8": False,
            "9": False,
        }
        self.input_pins = ["3"]
        self.active_input_source = 0

    def check_connection(self) -> bool:
        """
        Checks the connection status with the Arduino.
        Returns the connection status(bool).
        """
        return True if self.arduino is not None else False

    def set_active_pin(self, reset: bool) -> None:
        """
        Receives a reset(bool) value, if reset is true, set all pins to off,
         else sets any true value pin in output_pins(dict) to on.
        No return.
        """
        for pin in self.output_pins:
            if self.output_pins[pin]:
                self.arduino.set_pin_mode(pin, "O")
                sleep(0.3)
                if reset:
                    self.arduino.digital_write(pin, 0)
                else:
                    self.arduino.digital_write(pin, 1)
            sleep(0.2)

    def set_input_source(self, input_source: int, input_type: str) -> None:
        """
        - Pino 4: CA1
        - Pino 5: CA2
        - Pino 6: CA3
        - Pino 7: CC1
        - Pino 8: CC2
        - Pino 9: CC3
        - Pino 10: Buzzer
        """
        if self.active_input_source == input_source:
            return

        match input_source:
            case 1:
                self.change_output("4" if input_type == "CA" else "7")
            case 2:
                self.change_output("5" if input_type == "CA" else "8")
            case 3:
                self.change_output("6" if input_type == "CA" else "9")
        self.active_input_source = input_source

    def change_output(self, active_pin: str) -> None:
        """
        Receives active_pin(str) and set its equivalent value to true in output_pins(dict).
        No return.
        """
        self.set_active_pin(True)
        for pin in self.output_pins:
            self.output_pins[pin] = pin == active_pin
        self.set_active_pin(False)

    def buzzer(self) -> bool:
        self.arduino.set_pin_mode("10", "O")
        sleep(0.5)
        self.arduino.digital_write("10", 1)
        sleep(0.5)
        self.arduino.digital_write("10", 0)
        return True
