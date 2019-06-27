import unittest
from udp_json_plotter.JsonParser import JsonParser


class TestJsonParser(unittest.TestCase):
    def setUp(self):
        self.json_parser = JsonParser()

    def test_msg(self):
        msg = '[' \
            '{"PacketCounter" : 0},' \
            '{"Timestamp" : 1000},' \
            '{"sig1" : {"X" : 1.1, "Y" : 2.2, "Z" : 3.3}},' \
            '{"sig2" : {"A" : 1.1, "B" : 2.2, "C" : 3.3}},' \
            '{"sig3" : [1, 2, 3, 4]},' \
            '{"sig3" : [4, 5, 6, 7]},' \
            '{"sig4" : true},' \
            '{"Timestamp" : 1001},' \
            '{"sig2" : {"A" : 7, "B" : 8, "C" : 9}},' \
            '{"sig3" : [4, 3, 2, 1]}' \
            ']'

        self.json_parser.parse_into_x_y(msg)
        keys = self.json_parser.get_signal_names()

        for key in keys:
            xy = self.json_parser.get_timestamps_and_values(key)
            print(f'{key}: {xy}')


if __name__ == '__main__':
    unittest.main()
