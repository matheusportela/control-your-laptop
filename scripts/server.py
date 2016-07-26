import sys

import serial


ARDUINO_ADDR = '/dev/cu.usbmodem1411'
ARDUINO_BAUD_RATE = 115200


class BitStream(object):
    IDLE = 0
    RECEIVING = 1

    def __init__(self):
        self.bits = []
        self.stop_receiving()

    def __iter__(self):
        for bit in self.bits:
            yield bit

    def start_receiving(self):
        self.state = BitStream.RECEIVING
        self.bits = []

    def stop_receiving(self):
        self.state = BitStream.IDLE

    def is_receiving(self):
        return self.state == BitStream.RECEIVING

    def receive(self, data):
        if self.is_receiving():
            self.bits.append(int(data))

    def to_list(self):
        return self.bits

    def calculate_differences(self):
        differences = []
        previous_time = 0

        for bit_time in self.to_list():
            differences.append(bit_time - previous_time)
            previous_time = bit_time

        return differences


def decode(bit_stream):
    differences = bit_stream.calculate_differences()[1:]
    period = differences[0]/2.0

    bits = []
    bit = 1

    for difference in differences[1:]:
        num_periods = int(round(difference/period))

        if num_periods >= 3:
            break

        bits.extend([bit] * num_periods)
        bit = 0 if bit == 1 else 1

    return bits


class CommandContainer(object):
    def __init__(self):
        self.commands = {}

    def make_key(self, bits):
        return ''.join([str(b) for b in bits])

    def set_command(self, bits, name):
        key = self.make_key(bits)
        self.commands[key] = name

    def get_command(self, bits):
        key = self.make_key(bits)

        if key in self.commands:
            return self.commands[key]
        return 'Unknown'


def receive_bits():
    arduino = serial.Serial(ARDUINO_ADDR, ARDUINO_BAUD_RATE)
    bit_stream = BitStream()

    while True:
        data = arduino.readline().rstrip('\r\n')

        if data == 'START':
            bit_stream.start_receiving()
        elif data == 'END':
            bit_stream.stop_receiving()
            break
        else:
            bit_stream.receive(data)

    return decode(bit_stream)


class CLI(object):
    def __init__(self):
        self.command_container = CommandContainer()
        self.cli_commands = {
            'r': self.receive_commands,
            'c': self.configure_commands,
            'h': self.help,
            'q': self.quit,
        }
        self.control_commands = {
            'play': None,
            'stop': None,
            'pause': None,
        }

    def run(self):
        self.help()

        while True:
            command = str(raw_input('~> ')).lower()

            if command in self.cli_commands:
                method = self.cli_commands[command]
            else:
                print 'Unknown command "{}"'.format(command)
                method = self.help

            method()

    def help(self):
        print
        print 'Control Your Computer'
        print
        print '===== Commands ====='
        print 'r: Receive commands'
        print 'c: Configure commands'
        print 'h: Help'
        print 'q: Quit'

    def quit(self):
        sys.exit()

    def configure_commands(self):
        print 'Configuring commands'

        # Ignore first 2 streams received as they usually are garbage
        for _ in range(2):
            receive_bits()

        for command in self.control_commands.keys():
            self.set_command(command)

        print 'Successfully configured commands'

    def set_command(self, command):
        print 'Configuring command:', command

        # Set 2 signals to include the bit flip
        for _ in range(2):
            bits = receive_bits()
            print bits
            self.command_container.set_command(bits, command)

    def receive_commands(self):
        try:
            while True:
                bits = receive_bits()
                print 'Received command:', self.command_container.get_command(bits), bits
        except KeyboardInterrupt:
            print 'Exiting'


def main():
    cli = CLI()
    cli.run()


if __name__ == '__main__':
    main()
