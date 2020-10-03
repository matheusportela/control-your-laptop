import collections
import glob
import logging
import math
import os
import pickle
import sys

import serial


ARDUINO_PATH = '/dev/cu.usbserial*'
ARDUINO_BAUD_RATE = 115200


logging.basicConfig(format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UnknownCommand(Exception):
    pass


class NoArduinoFound(Exception):
    pass


class BitStream:
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
            logger.debug(int(data))
            self.bits.append(int(data))

    def to_list(self):
        return self.bits

    def calculate_differences(self):
        differences = []
        previous_time = 0

        for bit_time in self.to_list():
            differences.append(bit_time - previous_time)
            previous_time = bit_time

        logger.debug(f'differences: {differences}')
        return differences


def decode(bit_stream):
    differences = bit_stream.calculate_differences()
    bits = []

    for difference in differences:
        if math.isclose(difference, 120, abs_tol=10):
            bits.append(0)
        elif math.isclose(difference, 400, abs_tol=10):
            bits.append(1)

    return bits


class CommandContainer:
    def __init__(self):
        self.commands = {}

    def make_key(self, bits):
        return ''.join([str(b) for b in bits])

    def set_command(self, bits, name):
        key = self.make_key(bits)
        self.commands[key] = name

    def get_command(self, bits):
        key = self.make_key(bits)

        try:
            return self.commands[key]
        except KeyError:
            raise UnknownCommand


class BitReceiver:
    def __init__(self):
        self.bit_stream = BitStream()
        self.arduino = self.get_arduino()

    def get_arduino(self):
        for arduino_addr in glob.glob(ARDUINO_PATH):
            try:
                return serial.Serial(arduino_addr, ARDUINO_BAUD_RATE)
            except serial.SerialException:
                pass

        raise NoArduinoFound

    def receive_bits(self):
        while True:
            data = self.arduino.readline().rstrip(b'\r\n')

            logger.debug(f'Received: {data}')

            if data == b'START':
                self.bit_stream.start_receiving()
            elif data == b'END':
                self.bit_stream.stop_receiving()
                break
            else:
                self.bit_stream.receive(data)

        return decode(self.bit_stream)


class CLI:
    def __init__(self):
        self.bit_receiver = BitReceiver()
        self.cli_commands = {
            'r': self.receive_commands,
            'c': self.configure_commands,
            'h': self.help,
            'q': self.quit,
        }
        self.control_commands = collections.OrderedDict()
        self.control_commands['play'] = self.play
        self.control_commands['stop'] = self.stop
        self.control_commands['pause'] = self.pause
        self.control_commands['backward'] = self.backward
        self.control_commands['forward'] = self.forward

        self.config_file = '.control_your_laptop'
        self.load_commands()

    def save_commands(self):
        with open(self.config_file, 'wb') as f:
            pickle.dump(self.command_container, f)
        print('Saved commands to "{}"'.format(self.config_file))

    def load_commands(self):
        try:
            with open(self.config_file, 'rb') as f:
                self.command_container = pickle.load(f)
            print('Loaded commands from "{}"'.format(self.config_file))
        except IOError:
            self.command_container = CommandContainer()

    def run(self):
        self.help()

        try:
            while True:
                command = input('~> ').lower()

                try:
                    method = self.cli_commands[command]
                except KeyError:
                    print('Unknown command "{}"'.format(command))
                    method = self.help

                method()
        except KeyboardInterrupt:
            print('\nBye!')

    def help(self):
        print
        print('Control Your Computer')
        print
        print('===== Commands =====')
        print('r: Receive commands')
        print('c: Configure commands')
        print('h: Help')
        print('q: Quit')

    def quit(self):
        sys.exit()

    def configure_commands(self):
        print('Configuring commands')
        print('Press any button 2 times to start')

        # Ignore first 2 streams received as they usually are garbage
        for _ in range(2):
            self.bit_receiver.receive_bits()

        for command in self.control_commands.keys():
            self.set_command(command)

        self.save_commands()

        print('Successfully configured commands')

    def set_command(self, command):
        print('Configuring command:', command)
        print('Press the button 2 times to configure')

        # Set 2 signals to include the bit flip
        for _ in range(2):
            bits = self.bit_receiver.receive_bits()
            print(bits)

            self.command_container.set_command(bits, command)

    def receive_commands(self):
        print('Receiving commands')

        try:
            while True:
                bits = self.bit_receiver.receive_bits()
                print(bits)

                try:
                    command = self.command_container.get_command(bits)
                    command_method = self.control_commands[command]
                    command_method()
                except UnknownCommand:
                    print('Unknown command')
        except KeyboardInterrupt:
            print('Stop receiving commands')

    def play(self):
        print('Play')
        cmd = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            tell process frontAppName to keystroke space
        end tell
        '''
        os.system('osascript -e \'' + cmd + '\'')

    def stop(self):
        print('Stop')
        cmd = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            tell process frontAppName to key code 47 using command down
        end tell
        '''
        os.system('osascript -e \'' + cmd + '\'')

    def pause(self):
        print('Pause')
        cmd = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            tell process frontAppName to keystroke space
        end tell
        '''
        os.system('osascript -e \'' + cmd + '\'')

    def backward(self):
        print('Backward')
        cmd = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            tell process frontAppName to keystroke "v"
        end tell
        '''
        os.system('osascript -e \'' + cmd + '\'')

    def forward(self):
        print('Forward')
        cmd = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set frontAppName to name of frontApp
            tell process frontAppName to keystroke "b"
        end tell
        '''
        os.system('osascript -e \'' + cmd + '\'')


def main():
    cli = CLI()
    cli.run()


if __name__ == '__main__':
    main()
