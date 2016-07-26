import threading
import time

import matplotlib.pylab as plt
import numpy as np
import serial

plt.ion()

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
            plt.xlim([0, 10000])
            plt.ylim([-0.1, 1.1])
            plt.show()
            plt.pause(0.005)


def calculate_cosine(stream1, stream2):
    x = np.array(stream1.to_list())
    y = np.array(stream2.to_list())

    return np.dot(x, y)/(np.linalg.norm(x) * np.linalg.norm(y))


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


def main():
    arduino = serial.Serial(ARDUINO_ADDR, ARDUINO_BAUD_RATE)
    bit_stream = None
    previous_bit_stream = None
    bit_plotter = BitStreamPlotter()

    try:
        while True:
            data = arduino.readline().rstrip('\r\n')

            if data == 'START':
                if bit_stream:
                    previous_bit_stream = bit_stream

                bit_stream = BitStream()
                bit_stream.start_receiving()
            elif data == 'END':
                bit_stream.stop_receiving()
                bit_plotter.plot(bit_stream)
                bits = decode(bit_stream)

                if previous_bit_stream:
                    print calculate_cosine(bit_stream, previous_bit_stream)
            else:
                bit_stream.receive(data)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
