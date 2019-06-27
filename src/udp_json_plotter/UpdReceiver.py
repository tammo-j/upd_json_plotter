import os
import threading
import socket
import time
from threading import Thread
from udp_json_plotter.JsonParser import JsonParser


class UDPReceiver(Thread):
    _buffer_size = 1024 * 256
    _output_file = None

    def __init__(self, msg_queue, udp_port, file_name=''):
        """ Use `file_name=None` to omit a logfile. """
        super().__init__()
        self.shutdown_event = threading.Event()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(("", udp_port))
        self._socket.settimeout(0.5)
        self._msg_queue = msg_queue
        self._json_parser = JsonParser()
        self._file = None
        if file_name is not None:
            output_dir_name = '../out'
            if not os.path.exists(output_dir_name):
                os.makedirs(output_dir_name)
            if file_name == '':
                file_name = f'json_{time.strftime("%Y-%m-%d_%H-%M-%S")}.txt'
            file = f'{output_dir_name}/{file_name}'
            self._file = open(file, 'w')
            print(f'Received data will be recorded within {file}...')

    def run(self):
        while not self.shutdown_event.is_set():
            try:
                packet, _ = self._socket.recvfrom(1024 * 256)
            except socket.timeout:
                continue
            new_msg = packet.decode('utf-8')
            self._write_to_file(new_msg)
            self._msg_queue.put(new_msg)

    def _write_to_file(self, msg):
        if not self._file:
            return
        self._file.write(msg)
        self._file.write("\n")
