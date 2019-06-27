import os
import time
import tkinter as tk
import sys
import queue
import collections
import numpy as np
import matplotlib; matplotlib.use("TkAgg")  # call this immediately after 'import matplotlib'
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import FuncFormatter
from udp_json_plotter.JsonParser import JsonParser
from collections import defaultdict, deque
from datetime import datetime
from itertools import islice
from udp_json_plotter.utils.static_functions import first_index, last_index
from udp_json_plotter.utils.HistoryStack import HistoryStack


# noinspection PyUnusedLocal
def _blit_draw(self, artists, bg_cache):
    # Handles blitted drawing, which renders only the artists given instead of the entire figure.
    updated_ax = []
    for a in artists:
        # If we haven't cached the background for this axes object, do so now.
        if a.axes not in bg_cache:
            bg_cache[a.axes] = a.figure.canvas.copy_from_bbox(a.axes.figure.bbox)
        a.axes.draw_artist(a)
        updated_ax.append(a.axes)

    # After rendering all the needed artists, blit each axes individually.
    for ax in set(updated_ax):
        ax.figure.canvas.blit(ax.figure.bbox)


# MONKEY PATCH to animate axes as well
matplotlib.animation.Animation._blit_draw = _blit_draw


class _NavigationToolbarCustomized(NavigationToolbar2Tk):
    def __init__(self, canvas, window):
        self.plotter_frame = window
        super().__init__(canvas, window)

    # only display the buttons needed  --> ('Name', 'Hint', 'Icon', 'Callback')
    toolitems = [('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
                 ('Home', 'Reset zoom', 'home', 'home'),
                 ('Back', 'Back to previous zoom', 'back', 'back'),
                 ('Forward', 'Forward to next zoom', 'forward', 'forward'),
                 (None, None, None, None),  # divider line
                 ('Save', 'Quick-Save', 'filesave', 'save_figure_quick'),
                 ('SaveSnapshot', 'Adjustable Snapshot.', 'filesave', 'save_figure')]

    def home(self):
        self.plotter_frame.trigger_zoom_reset()

    def back(self):
        self.plotter_frame.trigger_zoom_back()

    def forward(self):
        self.plotter_frame.trigger_zoom_forward()

    def save_figure_quick(self):
        self.save_figure(quick_save=True)

    def save_figure(self, quick_save=False):
        title_name = f'snapshot_{time.strftime("%Y-%m-%d_%H-%M-%S")}'  # used as file name as well
        fig = plt.figure(title_name)
        ax = fig.add_subplot(111)
        ax.xaxis.grid()
        ax.yaxis.grid()
        pf = self.plotter_frame
        # copy axes
        ax.set_xlim(pf.ax.get_xlim())
        ax.set_ylim(pf.ax.get_ylim())
        ax.set_xlabel(pf.ax.get_xlabel())
        ax.set_ylabel(pf.ax.get_ylabel())
        labels = pf.ax.get_xticklabels()
        label_names = []
        for label in labels:
            label_names.append(label.get_text())
        ax.set_xticklabels(label_names)

        for pf_line_name, pf_line in pf.lines.items():
            lines = ax.plot(pf_line.get_xdata(), pf_line.get_ydata())
            lines[0].set_color(pf_line.get_color())

        # Shrink current axis by 20% to give place to the legend
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(pf.lines.keys(), loc='upper left', bbox_to_anchor=(1, 1), frameon=False)
        size = self.plotter_frame.fig.get_size_inches()
        fig.set_size_inches(size[0] / 0.8, size[1], forward=True)

        output_dir_name = 'out'
        if not os.path.exists(output_dir_name):
            os.makedirs(output_dir_name)

        if quick_save:
            file_name = f'{output_dir_name}/{title_name}.svg'
            fig.savefig(file_name, dpi=400, format='svg')
            print(f'Saved {file_name}.')
        else:
            matplotlib.rcParams['savefig.directory'] = 'out'
            matplotlib.rcParams['savefig.format'] = 'svg'
            fig.show()  # opens a new matplotlib windows with toolbar (which again owns a save button)


class PlotterFrame(tk.Frame):
    def __init__(self, parent, checkbox_frame, data_queue, timespan_seconds, *args, **kwargs):
        super().__init__(master=parent, *args, **kwargs)
        self.pack(fill='both', expand=True)

        self._checkbox_frame = checkbox_frame
        self._data_queue = data_queue
        self._timespan_milliseconds = int(timespan_seconds * 1000)
        self.fig = plt.Figure(linewidth=0.1)
        self.fig.set_dpi(150)
        self.ax = self.fig.add_subplot(111)
        self.ax.xaxis.grid()
        self.ax.yaxis.grid()
        self.ax.xaxis.set_animated(True)
        self.ax.yaxis.set_animated(True)
        self.ax.set_ylabel('Measured Value')
        self.ax.set_xlabel('Timestamp [min:sec]')

        self.ax.spines['right'].set_visible(False)
        self.ax.spines['top'].set_visible(False)
        self.ax.yaxis.set_ticks_position('left')
        self.ax.xaxis.set_ticks_position('bottom')

        self.lines = defaultdict(lambda: self.ax.plot([], [])[0])
        self._is_paused = False
        self._insert_gab_after_pause = False
        self._x_average_dt = {}
        self._json_parser = JsonParser()
        self._x_signals = defaultdict(deque)
        self._y_signals = {}
        self._signal_component_colors = {}

        # tkinter canvas
        canvas = FigureCanvasTkAgg(figure=self.fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        canvas.mpl_connect('button_press_event', self.toggle_is_paused)
        # keep reference of the animation to avoid to become garbage-collected
        self._ani = animation.FuncAnimation(self.fig, func=self.animate_func, interval=50, blit=True)
        self._toolbar = _NavigationToolbarCustomized(canvas, self)
        self._toolbar.config(bg='white')
        self._toolbar.update()

        # zoom
        self._y_min = 0
        self._y_max = 1
        self._x_min = np.inf
        self._x_max = - np.inf
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(self._y_min, self._y_max)
        self._x_max_proportion_init = 1  # %
        self._x_min_proportion_init = 1  # %
        self._x_max_proportion = self._x_max_proportion_init
        self._x_min_proportion = self._x_min_proportion_init
        self._is_zoom_reset_pending = False
        self._is_zoom_back_pending = False
        self._is_zoom_forward_pending = False
        self._x_min_proportion_history_stack = HistoryStack()
        self._x_max_proportion_history_stack = HistoryStack()
        self._y_min_history_stack = HistoryStack()
        self._y_max_history_stack = HistoryStack()

    # matplotlib calls this function as a loop which may be used to drive the program's update
    def animate_func(self, _):
        if self._is_paused:
            self.ax.set_title('Double click to continue.', fontdict={'fontsize': 8, 'fontweight': 'medium'})
        else:
            self.ax.set_title('Double click to pause.', fontdict={'fontsize': 8, 'fontweight': 'light'})

        self._update_xy_signals(self._is_paused)
        if self._x_signals:
            self._update_checkbuttons()
            self._update_zoom()
            self._update_x_labels()
            self._update_lines()
        # return artists that needs updating
        return tuple(list(self.lines.values()) + [self.ax.xaxis, self.ax.yaxis, self.ax.title])

    def _update_xy_signals(self, is_paused):
        """ new received data will be discarded while is_paused is set """
        while True:
            # break after all new data got received
            try:
                json_string = self._data_queue.get_nowait()
            except queue.Empty:
                break
            if is_paused:
                self._insert_gab_after_pause = True  # always draw a gab after a manually pause (i.e. break)
                continue  # discard new received data

            if self._insert_gab_after_pause:
                self._insert_gab_after_pause = False
                # insert gab for all signals and theirs components
                for signal_name, timestamps in self._x_signals.items():
                    y_value = self._y_signals[signal_name]
                    if isinstance(y_value, collections.Sequence):  # primitive types
                        self._y_signals[signal_name].append(np.nan)
                    elif isinstance(y_value, collections.Mapping):  # mapping type
                        for component_name, component_value in y_value.items():
                            self._y_signals[signal_name][component_name].append(np.nan)
                    else:
                        print(f'The y_value "{y_value}" is not supported and skipped!', file=sys.stderr)
                        continue  # skip x-value for unsupported y-value to avoid mismatches between length of x and y
                    timestamps.append(np.nan)  # add gab in x-signal as well

            x_values, y_values = self._json_parser.parse_into_x_y(json_string)
            for signal_name, timestamps in x_values.items():
                insert_gap_after_absence = False
                if signal_name in self._x_signals and signal_name in self._x_average_dt:
                        last_timestamp = self._x_signals[signal_name][-1]
                        next_timestamp = timestamps[0]
                        dt = next_timestamp - last_timestamp
                        dt_average = self._x_average_dt[signal_name]
                        if dt > 2 * dt_average:  # insert gab if dt grows over twice its average
                            insert_gap_after_absence = True

                # add y-value
                y_value = y_values[signal_name]
                if isinstance(y_value, collections.Sequence):  # primitive types
                    if signal_name not in self._y_signals:
                        self._y_signals[signal_name] = deque()
                    if insert_gap_after_absence:
                        self._y_signals[signal_name].append(np.nan)
                    self._y_signals[signal_name].extend(y_value)
                elif isinstance(y_value, collections.Mapping):
                    if signal_name not in self._y_signals:
                        self._y_signals[signal_name] = defaultdict(deque)
                    for component_name, component_value in y_value.items():
                        if insert_gap_after_absence:
                            self._y_signals[signal_name][component_name].append(np.nan)
                        self._y_signals[signal_name][component_name].extend(component_value)
                else:
                    print(f'The y_value "{y_value}" is not supported and skipped!', file=sys.stderr)
                    continue  # skip x-value for unsupported y-value to avoid mismatches between the length of x and y

                # add x-value
                x_signal_timestamps = self._x_signals[signal_name]
                if insert_gap_after_absence:
                    x_signal_timestamps.append(np.nan)
                x_signal_timestamps.extend(timestamps)
                if insert_gap_after_absence:
                    del self._x_average_dt[signal_name]  # reset frequency
                else:
                    start_index = last_index(x_signal_timestamps, condition=lambda x: np.isnan(x))
                    if start_index is not None:
                        end_index = len(x_signal_timestamps)
                        x_signal_timestamps_slice = list(islice(x_signal_timestamps, start_index + 1, end_index))
                    else:
                        x_signal_timestamps_slice = x_signal_timestamps
                    if len(x_signal_timestamps_slice) > 3:  # calculate frequency starting from at least three elements
                        self._x_average_dt[signal_name] = np.mean(np.diff(x_signal_timestamps_slice))

        if not is_paused:
            self._trim_timespan()

    def _trim_timespan(self):
        now = int(time.time() * 1000)  # milliseconds
        threshold = now - self._timespan_milliseconds
        for signal_name, timestamps in self._x_signals.items():
            first_index_over_threshold = first_index(iterable=timestamps, condition=lambda x: x >= threshold)
            if not first_index_over_threshold:
                continue
            y = self._y_signals[signal_name]
            for _ in range(first_index_over_threshold):
                timestamps.popleft()
                if isinstance(y, collections.Mapping):
                    for component in y.values():
                        component.popleft()
                else:
                    y.popleft()

    def _update_checkbuttons(self):
        for signal_name, signal_value in self._y_signals.items():
            # signals
            if not self._checkbox_frame.is_known(signal_name):
                if isinstance(signal_value, collections.Mapping):
                    # mapping types
                    self._checkbox_frame.add_signal_checkbutton(signal_name)
                else:
                    # primitive types
                    line = self.lines[signal_name]
                    self._checkbox_frame.add_signal_checkbutton(signal_name, background_color=line.get_color())
                    continue

            # components
            if isinstance(signal_value, collections.Mapping):
                for component_name in signal_value.keys():
                    if not self._checkbox_frame.is_known(signal_name, component_name):
                        signal_component_name = f'{signal_name}_{component_name}'
                        line = self.lines[signal_component_name]
                        self._checkbox_frame.add_component_checkbutton(signal_name, component_name,
                                                                       background_color=line.get_color())

    def _update_zoom(self):
        x_min_new = np.inf
        x_max_new = -np.inf
        y_min_new = np.inf
        y_max_new = -np.inf
        for signal_name, signal_timestamps in self._x_signals.items():
            x_min_new = min(x_min_new, *signal_timestamps)
            x_max_new = max(x_max_new, *signal_timestamps)
            signal_values = self._y_signals[signal_name]
            if isinstance(signal_values, collections.Mapping):
                for component_name, component_values in self._y_signals[signal_name].items():
                    is_component_checked = self._checkbox_frame.is_checked(signal_name, component_name)
                    if not is_component_checked:
                        continue
                    y_min_new = min(y_min_new, *component_values)
                    y_max_new = max(y_max_new, *component_values)
            else:  # primitive types
                is_signal_checked = self._checkbox_frame.is_checked(signal_name)
                if not is_signal_checked:
                    continue
                y_min_new = min(y_min_new, *signal_values)
                y_max_new = max(y_max_new, *signal_values)

        if np.isinf(x_min_new) or np.isinf(x_max_new) or np.isinf(y_min_new) or np.isinf(y_max_new):
            return

        if self._is_zoom_reset_pending:
            self._is_zoom_reset_pending = False
            self._x_min_proportion = self._x_min_proportion_init
            self._x_max_proportion = self._x_max_proportion_init
            # reset also history
            self._x_min_proportion_history_stack.clear()
            self._x_max_proportion_history_stack.clear()
            self._y_min_history_stack.clear()
            self._y_max_history_stack.clear()

        elif self._is_zoom_back_pending:
            self._zoom_back()

        elif self._is_zoom_forward_pending:
            self._zoom_forward()

        elif self._toolbar.mode:
            # check if current x/y limits are smaller or greater as previous ones --> if so the canvas got zoomed

            # check if x-axis got zoomed
            x_min_current, x_max_current = self.ax.get_xlim()
            x_difference = self._x_max - self._x_min
            if x_min_current > self._x_min:
                x_min_proportion = abs(x_min_current - self._x_max) / x_difference
                if abs(x_min_proportion - self._x_min_proportion) > 0.0001:  # zoomed x_min
                    # print(f'x min zoomed: {self._x_min} --> {x_min_current}')
                    self._x_min_proportion_history_stack.append(self._x_min_proportion)
                    self._x_min_proportion = x_min_proportion

            if x_max_current < self._x_max:
                x_max_proportion = abs(x_max_current - self._x_min) / x_difference
                if abs(x_max_proportion - self._x_max_proportion) > 0.0001:  # zoomed x_max
                    # print(f'x max zoomed: {self._x_max} --> {x_max_current}')
                    self._x_max_proportion_history_stack.append(self._x_max_proportion)
                    self._x_max_proportion = x_max_proportion

            # check if y-axis got zoomed
            y_min_current, y_max_current = self.ax.get_ylim()
            if y_min_current > self._y_min:  # zoomed y_min
                # print(f'y min zoomed: {self._y_min} --> {y_min_current}')
                self._y_min_history_stack.append(self._y_min)
                self._y_min = y_min_new = y_min_current
            if y_max_current < self._y_max:  # zoomed y_max
                # print(f'y max zoomed: {self._y_max} --> {y_max_current}')
                self._y_max_history_stack.append(self._y_max)
                self._y_max = y_max_new = y_max_current

        x_difference_new = x_max_new - x_min_new
        x_min_scaled = x_max_new - x_difference_new * self._x_min_proportion
        x_max_scaled = x_min_new + x_difference_new * self._x_max_proportion
        self.ax.set_xlim(x_min_scaled, x_max_scaled)
        self._x_min = x_min_new
        self._x_max = x_max_new

        # only applies if y is not zoomed (i.e. no backward zoom available)
        y_offset_new = 0.01 * (y_max_new - y_min_new)  # plus 1% of y range on top and bottom
        if not self._y_min_history_stack.is_back_feasible():
            self._y_min = y_min_new - y_offset_new
        if not self._y_max_history_stack.is_back_feasible():
            self._y_max = y_max_new + y_offset_new

        self.ax.set_ylim(self._y_min, self._y_max)

    def _zoom_back(self):
        self._is_zoom_back_pending = False
        # x-axes
        if self._x_min_proportion_history_stack.is_back_feasible():
            self._x_min_proportion = self._x_min_proportion_history_stack.back(self._x_min_proportion)
        if self._x_max_proportion_history_stack.is_back_feasible():
            self._x_max_proportion = self._x_max_proportion_history_stack.back(self._x_max_proportion)
        # y-axes
        if self._y_min_history_stack.is_back_feasible():
            self._y_min = self._y_min_history_stack.back(self._y_min)
        if self._y_max_history_stack.is_back_feasible():
            self._y_max = self._y_max_history_stack.back(self._y_max)

    def _zoom_forward(self):
        self._is_zoom_forward_pending = False
        # x-axes
        if self._x_min_proportion_history_stack.is_forward_feasible():
            self._x_min_proportion = self._x_min_proportion_history_stack.forward(self._x_min_proportion)
        if self._x_max_proportion_history_stack.is_forward_feasible():
            self._x_max_proportion = self._x_max_proportion_history_stack.forward(self._x_max_proportion)
        # y-axes
        if self._y_min_history_stack.is_forward_feasible():
            self._y_min = self._y_min_history_stack.forward(self._y_min)
        if self._y_max_history_stack.is_forward_feasible():
            self._y_max = self._y_max_history_stack.forward(self._y_max)

    def _update_x_labels(self):
        # change x labels as 'min:sec' of timestamps
        self.ax.xaxis.set_major_formatter(FuncFormatter(self.x_label_formatter))

    def _update_lines(self):
        for signal_name, signal_timestamps in self._x_signals.items():  # signal's components share the same timestamp
            signal_values = self._y_signals[signal_name]

            is_signal_checked = self._checkbox_frame.is_checked(signal_name)
            if isinstance(signal_values, collections.Mapping):  # mapping types
                for component_name, component_values in self._y_signals[signal_name].items():
                    signal_component_name = f'{signal_name}_{component_name}'
                    # check is visible
                    is_component_checked = self._checkbox_frame.is_checked(signal_name, component_name)
                    if not is_signal_checked or not is_component_checked:
                        if signal_component_name in self.lines:
                            del self.lines[signal_component_name]
                        continue
                    # update line
                    line = self.lines[signal_component_name]
                    line.set_data(signal_timestamps, component_values)
                    if signal_component_name not in self._signal_component_colors:
                        self._signal_component_colors[signal_component_name] = line.get_color()
                    line.set_color(self._signal_component_colors[signal_component_name])
            else:  # primitive types
                # check is visible
                if not is_signal_checked:
                    if signal_name in self.lines:
                        del self.lines[signal_name]
                    continue
                # update line
                line = self.lines[signal_name]
                line.set_data(signal_timestamps, signal_values)
                if signal_name not in self._signal_component_colors:
                    self._signal_component_colors[signal_name] = line.get_color()
                line.set_color(self._signal_component_colors[signal_name])

    @staticmethod
    def x_label_formatter(tick_val, _):
        timestamp_as_seconds = tick_val / 1000  # ticks of x-axis is a timestamp as milliseconds
        try:
            label = datetime.fromtimestamp(timestamp_as_seconds).strftime('%M:%S')
        except OSError:
            label = ''
        return label

    def trigger_zoom_reset(self):
        self._is_zoom_reset_pending = True

    def trigger_zoom_back(self):
        self._is_zoom_back_pending = True

    def trigger_zoom_forward(self):
        self._is_zoom_forward_pending = True

    def toggle_is_paused(self, event):
        if event.dblclick:
            self._is_paused = not self._is_paused
