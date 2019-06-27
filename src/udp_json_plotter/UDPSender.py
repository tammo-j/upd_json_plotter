import signal
import socket
import sys
import time
import numpy as np
from threading import Thread, Event


class UDPSender(Thread):
    """ This Sender is not part of the plotter itself and needed for testing only. """

    _udp_ip = "127.0.0.1"
    _udp_port = 30000

    def __init__(self, ip, port):
        super().__init__()
        self._udp_ip = ip
        self._udp_port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.shutdown_event = Event()

    def run(self) -> None:
        packet_counter = 0
        last_timestamp = None
        is_sig1_included = True
        while not self.shutdown_event.is_set():
            timestamp = int(time.time() * 1000)
            if not last_timestamp:
                last_timestamp = timestamp
            if timestamp - last_timestamp > 3000:
                last_timestamp = timestamp
                is_sig1_included = not is_sig1_included
            if is_sig1_included:
                x = np.sin(packet_counter/100) + np.random.rand()*0.4
                y = np.sin(packet_counter/50) + np.random.rand()
                z = -1 * np.random.rand()*0.4
                sig_temp = (
                    f',{{"Timestamp" : {int(time.time() * 1000)}}}'
                    f',{{"sig_temp" : {{"X" : {x}, "Y" : {y}, "Z" : {z}}}}}'
                )
            else:
                sig_temp = ''
            time.sleep(.01)
            msg = (
                f'['
                f'{{"PacketCounter" : {packet_counter}}}'
                f'{sig_temp}'
                f',{{"Timestamp" : {int(time.time() * 1000)}}}'
                f',{{"sig_dict" : {{"A" : {float(1+0.2*np.random.rand())}, "B":0}}}}'
                f',{{"sig_list" : [0.11, 0.22, 0.33]}}'
                f',{{"sig_prim" : {2*np.sin(packet_counter/50)}}}'
                f',{{"sig_prim" : 1}}'
                f',{{"sig_m1" : 1, "sig_m2" : 2, "sig_m3_list": [0, 1, 2], "sig_m4_dict": {{"J1": 1, "J2": 2}}}}'
                f',{{"sig_bool" : {str(time.time() % 10 + np.random.rand() > 8).lower()}}}'
                f']')

            self._sock.sendto(str.encode(msg, encoding="utf-8"), (self._udp_ip, self._udp_port))
            time_to_sleep = np.random.rand() * 0.03 + 0.01
            time.sleep(time_to_sleep)
            packet_counter += 1


def _sigterm_handler(*_):
    if stop_receiver():
        sys.exit(0)
    sys.exit(-1)


def stop_receiver():
    if sender and sender.is_alive():
        sender.shutdown_event.set()
        sender.join(timeout=1)
        if sender.is_alive():
            print(f'TIMEOUT! "{__file__}" could not be stopped!')
            return False
    return True


if __name__ == '__main__':
    UDP_IP = "127.0.0.1"
    UDP_PORT = 30000

    # shutdown handling from cli (e.g. ctrl+c)
    # catch SIGTERM|SIGINT to finally shutdown all threads nicely
    signal.signal(signal.SIGTERM, _sigterm_handler)
    signal.signal(signal.SIGINT, _sigterm_handler)

    sender = UDPSender(UDP_IP, UDP_PORT)
    sender.start()
    while sender.is_alive():
        time.sleep(1)
