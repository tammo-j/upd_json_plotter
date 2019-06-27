import tkinter as tk
from udp_json_plotter.CheckboxFrame import CheckboxFrame
from udp_json_plotter.PlotterFrame import PlotterFrame


class TkGUI(tk.Tk):
    def __init__(self, data_queue, timespan_seconds=30):
        super().__init__()
        self.title('Json Plotter')

        checkbox_frame = CheckboxFrame(self)
        PlotterFrame(self, checkbox_frame, data_queue, timespan_seconds=timespan_seconds)
