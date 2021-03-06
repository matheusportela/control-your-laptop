import glob
import math
import threading
import time

import matplotlib.pylab as plt
import numpy as np
import serial

plt.ion()

ARDUINO_PATH = '/dev/cu.usbserial*'
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


class BitStreamPlotter(object):
    def __init__(self):
        self.previous_bit_stream = None

    def plot(self, bit_stream):
        if self.previous_bit_stream != bit_stream.to_list():
            self.previous_bit_stream = bit_stream

            x = []
            y = []
            bit = None

            for bit_time in bit_stream.to_list():
                if bit is None:
                    x.append(bit_time)
                    y.append(0)
                    bit = 0
                elif bit == 0:
                    x.extend([bit_time, bit_time])
                    y.extend([0, 1])
                    bit = 1
                elif bit == 1:
                    x.extend([bit_time, bit_time])
                    y.extend([1, 0])
                    bit = 0

            plt.clf()
            plt.plot(x, y)
            plt.ylim([-0.1, 1.1])
            plt.show()
            plt.pause(0.005)


def decode(bit_stream):
    differences = bit_stream.calculate_differences()
    bits = []

    for difference in differences:
        if math.isclose(difference, 120, abs_tol=10):
            bits.append(0)
        elif math.isclose(difference, 400, abs_tol=10):
            bits.append(1)

    return bits

def get_arduino():
    for arduino_addr in glob.glob(ARDUINO_PATH):
        try:
            return serial.Serial(arduino_addr, ARDUINO_BAUD_RATE)
        except serial.SerialException:
            pass

    raise IOError

def main():
    arduino = get_arduino()
    bit_stream = None
    bit_plotter = BitStreamPlotter()

    try:
        while True:
            data = arduino.readline().rstrip(b'\r\n')

            if data == b'START':
                bit_stream = BitStream()
                bit_stream.start_receiving()
            elif data == b'END':
                bit_stream.stop_receiving()
                bits = decode(bit_stream)
                print(bits)
                bit_plotter.plot(bit_stream)
            else:
                bit_stream.receive(data)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
