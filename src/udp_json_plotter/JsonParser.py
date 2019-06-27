import collections
import sys
from collections import defaultdict
import json


class JsonParser:
    _recent_timestamp = None
    _recent_packet_counter = None

    def parse_into_x_y(self, json_string):
        obj_list = json.loads(json_string)
        if not isinstance(obj_list, list):
            print(f'The received message must be a json array! But the message is: "{obj_list}"', file=sys.stderr)
            exit(-1)

        x_values = defaultdict(list)
        y_values = {}

        for obj_dict in obj_list:
            if not isinstance(obj_dict, dict):
                print(f'The top level json array may only contains json objects.'
                      f'The element "{obj_dict}" is not an json object!', file=sys.stderr)
                continue
            keys = obj_dict.keys()

            if 'PacketCounter' in keys:
                if len(keys) > 1:
                    print(f'The json object contains the key "Paketcounter".'
                          f' This object may in principle not contain other keys! But there are also this keys:'
                          f' {keys}', file=sys.stderr)
                new_packet_counter = int(obj_dict['PacketCounter'])
                if not self._recent_packet_counter:
                    self._recent_packet_counter = new_packet_counter
                    continue
                diff_packet_counter = self._recent_packet_counter - new_packet_counter
                if diff_packet_counter > 1:
                    print(str(diff_packet_counter) + " packets lost!")
                self._recent_packet_counter = new_packet_counter
                continue

            if 'Timestamp' in keys:
                if len(keys) > 1:
                    print(f'The json object contains the key "Timestamp".'
                          f' This object may in principle not contain other keys! But there are also this keys:'
                          f' {keys}', file=sys.stderr)
                self._recent_timestamp = int(obj_dict['Timestamp'])
                continue

            if not self._recent_timestamp:
                print(f'No recent timestamp specified and therefore this keys {keys} are skipped!', file=sys.stderr)
                continue

            for key in keys:
                x_values[key].append(self._recent_timestamp)
                value = obj_dict[key]

                # primitive types
                if not isinstance(value, collections.Iterable):
                    if key not in y_values:
                        y_values[key] = list()
                    y_values[key].append(value)
                    continue
                # array type
                if isinstance(value, collections.Sequence):
                    for index, value_value in enumerate(value):
                        if key not in y_values:
                            y_values[key] = defaultdict(list)
                        y_values[key][index].append(value_value)
                    continue
                # mapping types
                if isinstance(value, collections.Mapping):
                    for value_key, value_value in value.items():
                        if key not in y_values:
                            y_values[key] = defaultdict(list)
                        y_values[key][value_key].append(value_value)
                    continue

                print(f'Value "{value}" is not supported!', file=sys.stderr)
                x_values[key].pop()  # undo `x_values[key].append(self._recent_timestamp)`

        return x_values, y_values
