from fractions import Fraction
import struct
import pickle
from collections import OrderedDict


class FileHandler(object):
    def __init__(self, name):
        self.__name = name

    def read_file(self):
        code = ''
        with open(self.__name, "rb") as f:
            binary = f.read(4)
            while binary:
                i = struct.unpack('i', binary)
                code += str(bin(i[0]))[2:].zfill(31)
                binary = f.read(4)
        return code

    def write_file(self, binary_string):
        with open(self.__name, "wb") as f:
            while len(binary_string) > 0:
                window = binary_string[:31]
                if len(window) < 31:
                    window += '0' * (31 - len(window))
                i = int(window, 2)
                f.write(struct.pack('i', i))
                binary_string = binary_string[31:]


class Coder(object):
    """Encodes and decodes text using arithmetic coding"""
    __statistics = {}

    def train_encode(self, text):
        """
        Train coder on given text and encode this text.

        Args:
            text: a piece of text that you want to encode
        Returns:
            arithmetic code of given text
        """
        self.train(text)
        return self.encode(text)

    def train(self, text):
        """
        Train text statistics from given text string.

        Calculated statistics will be stored in Coder object attributes, and will be used later during encoding or
        decoding process.

        Args:
            text: a piece of text from which you want to get the statistics
        """
        text += str(0)
        counts = OrderedDict()
        for letter in text:
            counts[letter] = counts.get(letter, 0) + 1

        self.__statistics = {}
        start = Fraction(0)
        for letter in counts.keys():
            end = start + Fraction(counts[letter], len(text))
            self.__statistics[letter] = (start, end)
            start = end

    def encode(self, text):
        """
        Encode text using trained statistics.

        Args:
            text: unicode text you want to compress
        Returns:
            arithmetic code of given text
        """
        text += str(0)
        code = ''
        follow = 0
        interval = (Fraction(0), Fraction(1))
        for letter in text:
            length = interval[1] - interval[0]
            prob_interval = self.__statistics[letter]
            interval = (interval[0] + prob_interval[0] * length, interval[0] + prob_interval[1] * length)
            while True:
                if interval[1] < Fraction(1, 2):
                    code += '0' + follow * '1'
                    interval = (interval[0] * 2, interval[1] * 2)
                    follow = 0
                elif interval[0] >= Fraction(1, 2):
                    code += '1' + follow * '0'
                    interval = (interval[0] * 2 - 1, interval[1] * 2 - 1)
                    follow = 0
                elif interval[0] >= Fraction(1, 4) and interval[1] < Fraction(3, 4):
                    follow += 1
                    interval = (interval[0] * 2 - Fraction(1, 2), interval[1] * 2 - Fraction(1, 2))
                else:
                    break
        follow += 1
        if interval[0] < Fraction(1, 4):
            code += '0' + follow * '1'
        else:
            code += '1' + follow * '0'
        return code

    def decode(self, code):
        """
        Decode binary string using trained statistics.

        Args:
            code: binary code you want to decode
        Returns:
            decoded string
        """
        value = Fraction(0)
        inc = Fraction(1)
        for i in range(len(code)):
            inc /= 2
            value += int(code[i]) * inc

        text = ''
        interval = (Fraction(0), Fraction(1))
        while True:
            length = interval[1] - interval[0]
            letter, prob_interval = self.get_letter((value - interval[0]) / length)
            text += letter
            if letter == str(0):
                break
            interval = (interval[0] + prob_interval[0] * length, interval[0] + prob_interval[1] * length)
            while True:
                if interval[1] < Fraction(1, 2):
                    interval = (interval[0] * 2, interval[1] * 2)
                    value *= 2
                elif interval[0] >= Fraction(1, 2):
                    interval = (interval[0] * 2 - 1, interval[1] * 2 - 1)
                    value = value * 2 - 1
                elif interval[0] >= Fraction(1, 4) and interval[1] < Fraction(3, 4):
                    value = value * 2 - Fraction(1, 2)
                    interval = (interval[0] * 2 - Fraction(1, 2), interval[1] * 2 - Fraction(1, 2))
                else:
                    break
        return text[0:-1]

    def get_letter(self, value):
        """
        Get letter and cumulative probability from trained statistics.

        Args:
            value: value in range [0,1) you want to find in statistics
        Returns:
            tuple (a,b) where:
            a: letter
            b: probability interval (tuple)
        """
        for key, i in self.__statistics.items():
            if value >= i[0] and value < i[1]:
                return key, i
        raise 'Value not found'

    def save_statistics(self, filename):
        """
        Save trained statistics to the file.

        Args:
            filename: name of the file you want to write to
        """
        pickle.dump(self.__statistics, open(filename + ".txt", "wb"))

    def load_statistics(self, filename):
        """
        Load saved statistics from the file.

        Args:
            filename: name of the file you want to read from
        """
        self.__statistics = pickle.load(open(filename + ".txt", "rb"))


def main():
    coder = Coder()
    handler = FileHandler("file.txt")
    code = coder.train_encode("b")
    # coder.save_statistics("stat")
    handler.write_file(code)
    print(code)

    # coder.load_statistics("stat")
    print("Code from encoding:", coder.decode(code))
    code = handler.read_file()
    print("Code read from file:", coder.decode(code))


if __name__ == "__main__":
    main()
