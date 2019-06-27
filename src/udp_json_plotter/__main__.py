import queue
import signal
import sys
from udp_json_plotter.UpdReceiver import UDPReceiver
from udp_json_plotter.TkGUI import TkGUI


# noinspection SpellCheckingInspection
"""
dependencies:
> pip install ttkwidgets   --> https://github.com/RedFantom/ttkwidgets
> pip install matplotlib
"""


UDP_PORT = 30000
TIMESPAN_SECONDS = 30
CREATE_LOGFILE = True


def _sigterm_handler():
    if stop_receiver():
        sys.exit(0)
    sys.exit(-1)


def stop_receiver():
    if receiver and receiver.is_alive():
        receiver.shutdown_event.set()
        receiver.join(timeout=1)
        if receiver.is_alive():
            print('TIMEOUT! UDPReceiver could not be stopped!')
            return False
    return True


if __name__ == '__main__':
    # shutdown handling from cli (e.g. ctrl+c)
    # catch SIGTERM|SIGINT to finally shutdown all threads nicely
    signal.signal(signal.SIGTERM, _sigterm_handler)
    signal.signal(signal.SIGINT, _sigterm_handler)

    msg_queue = queue.Queue()

    if CREATE_LOGFILE:
        logfile = ''  # `file_name=''` to enable a logfile with default naming
    else:
        logfile = None  # `file_name=None` to omit a logfile
    receiver = UDPReceiver(msg_queue, UDP_PORT, logfile)
    receiver.start()

    app = TkGUI(msg_queue, TIMESPAN_SECONDS)
    app.mainloop()  # is blocking and must be called within __main__
    if not stop_receiver():
        sys.exit(-1)
