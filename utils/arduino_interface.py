import serial


class Arduino:
    """
    Models an Arduino connection
    """

    def __init__(self, serial_port="/dev/ttyACM0", baud_rate=9600, read_timeout=5):
        """
        Initializes the serial connection to the Arduino board
        """
        self.conn = serial.Serial(serial_port, baud_rate)
        self.conn.timeout = read_timeout

    def set_pin_mode(self, pin_number, mode):
        """
        Performs a pinMode() operation on pin_number
        Internally sends b'M{mode}{pin_number} where mode could be:
        - I for INPUT
        - O for OUTPUT
        - P for INPUT_PULLUP
        """
        command = ("".join(("M", mode, str(pin_number)))).encode()
        self.conn.write(command)

    def digital_read(self, pin_number):
        """
        Performs a digital read on pin_number and returns the value (1 or 0)
        Internally sends b'RD{pin_number}' over the serial connection
        """
        command = ("".join(("RD", str(pin_number)))).encode()
        self.conn.write(command)
        line_received = self.conn.readline().decode().strip()
        header, value = line_received.split(":")  # e.g. D13:1
        if header == ("D" + str(pin_number)):
            # If header matches
            return int(value)

    def digital_write(self, pin_number, digital_value):
        """
        Writes the digital_value on pin_number
        Internally sends b'WD{pin_number}:{digital_value}' over the serial
        connection
        """
        command = ("".join(("WD", str(pin_number), ":", str(digital_value)))).encode()
        self.conn.write(command)
