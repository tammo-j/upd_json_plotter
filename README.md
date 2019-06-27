# UPD JSON Plotter

## Table of Contents
- [1. About](#1-about)
- [2. Dependencies](#2-dependencies)
- [3. Start](#3-start)
- [4. Config](#4-config)
- [5. Output](#5-output)
    + [5.1 Logfile](#51-logfile)
    + [5.2 Snapshot](#52-snapshot)
- [6. Functionality](#6-functionality)
    + [6.1 Plot](#61-plot)
    + [6.2 Checkbutton-Tree](#62-checkbutton-tree)
    + [6.3 Toolbar](#63-toolbar)
        * [6.3.1 Zooming](#631-zooming)
        * [6.3.2 Pause](#632-pause)
        * [6.3.3 Snapshot](#633-snapshot)
- [7. JSON Format](#7-json-format)
    + [7.1 Primitive Signals](#71-primitive-signals)
    + [7.2 Composite Signals](#72-composite-signals)
        * [7.2.1 Array Type](#721-array-type)
        * [7.2.2 Mapping Type](#722-mapping-type)
    + [7.3 Squashing](#733-squashing)


# 1. About
The *upd_json_plotter* (called *plotter* furthermore) is a tool to visual/plot the most recent received data over the time.
The data must be send over UDP and encoded as JSON.
The data contains *x/y* pairs for different signals, where *x* represents the time and *y* the corresponding value
of a signal. To distinguish the data and associate them to the different signals each signal must be assigned to a name.
\[[7. JSON Format](#7-json-format)\]

The plotter may be started before are afterwards the upd stream is accomplished. To not miss any data
start the plotter always beforehand \[[3. Start](#3-start)\].
Also the udp stream may stopped or reappear while the plotter is running. A visual gab indicated this
break. A visual gab means that the two most recent points around the break are not connected \[Functionality/Toolbar/[6.3.2 Pause](#632-pause)\].
The plotter also records the received data within a file \[Output/[5.1 Logfile](#51-logfile)\]. Also snapshots can be stored as image files \[Output/[5.2 Snapshot](#52-snapshot)\].

This screenshot might help to get an overall overview of the plotter.

![Screenshot](https://niob.werk5.dyndns.org/git/werk5/iiwa/raw/json-logger/wiki_images/UPD+JSON+Plotter/upd_json_plotter.png)

# 2. Dependencies
- python 3.6
- matplotlib 3.0.2
- numpy 1.14
- ttkwidgets 0.9

use: `>pip install <dependency>`


# 3. Start
To start the plotter the `__main__.py` may be called.
Either by using the cli
```
  >cd scr_python
  >python -m udp_json_plotter
```
or by using a IDE and selecting `Run __main__`.


# 4. Config
All configurable options are set through static variables and are given at the top of the file `__main__.py`.
The UPD port can be configure through `UPD_PORT`. \[[7. JSON Format](#7-json-format)\]
Also the timespan of the plot view is adjustable as `TIMESPAN_SECONDS`. \[Functionality/[6.1 Plot](#61-plot)\]
The boolean `CREATED_LOGFILE` toggle if a logfile should be written or not. \[Output/[5.1 Logfile](#51-logfile)\]


# 5. Output
The plot view is only a temporary output of the received data. It also shows just the most recent received
data as a section of the whole received data set.
Therefore a logfile records the whole data set \[Output/[5.1 Logfile](#51-logfile)\]. Also the current view of the plot can be saved
as snapshots which are svg image files \[Output/[5.2 Snapshot](#52-snapshot)\].
All files get stored within the directory `out/` next to the file `__main__.py`. This directory will be created
automatically if not already present.

## 5.1 Logfile
The plotter records all received data automatically (if `CREATE_LOGFILE` is set \[[4. Config](#4-config)\]) within
a text file called `json_<YYYY-MM-DD_HH-MM-SS>.txt` with the timestamp of file's creation.
All received data will be recorded regardless if they are shown within the plotter or not \[Functionality/[6.2 Checkbutton-Tree](#62-checkbutton-tree)\].
Once record within the text file they will never be deleted to offer the opportunity of recovery later on.

## 5.2 Snapshot
During the evaluation of the plot it is necessary to save the current view of the plot. This can be performed with a
snapshot as svg image through the toolbar. To read more about the functionality of the snapshot tool refer
to \[Functionality/Toolbar/[6.3.3 Snapshot](#633-snapshot)\].
The image is saved as `snapshot__<YYYY-MM-DD_HH-MM-SS>.svg` with the timestamp of file's creation.


# 6. Functionality
The plotter provides many accessories to evaluate the received data.
The GUI is divided into three segments. On the left side there is the first and primary segment which shows the plot of
the signals \[Functionality/[6.1 Plot](#61-plot)\]. On top of it a toolbar is located to manipulate the current view of the plot and
to save snapshot of it \[Functionality/[6.3 Toolbar](#63-toolbar)\]. To the right side of the  first and second segment is the
third segment located which holds a tree-like list of all signals to hide/show signals on the
plot \[Functionality/[6.2 Checkbutton-Tree](#62-checkbutton-tree)\].
All data points from one signal/component are connected as line which a unique color. This color decorates also the
name of the signal/component within the checkbutton-tree.
This lines might have gabs to indicate noticeable absences. Therefore the average time delta (aka frequency) of each
signal/component are measured individual to detect automatically deviations.

In summary the plot owns some nice accessories amd can be manipulated through the toolbar and the checkbutton-tree.
Also snapshots can be saved.

## 6.1 Plot
The plot represents a temporary view of the received data. The view includes the most recent
received data within the last 30 seconds, which is adjustable with `TIMESPAN_SECONDS` \[[4. Config](#4-config)\].
The plot consists of a x- and a y-axes. The x-axes is time based and represents the timestamps of each data point.
Each data-point is map on the y-axes as a number value onto the corresponding timestamp from the x-axes.
The timestamp represents the record timestamp as minute and second `<MM:SS>`.
New received data will be inserted on the left and hold for the next 30 seconds
while floating to the right side of the plot.
If data-points reached the most right side of the plot they will be deleted from the plot because there are received 30
seconds ago.
This means that the x-axes is floating as well because it holds the timestamps of the recent 30 seconds.

The y-axes is mostly fixed. It only change to automatically adopt the biggest and smallest values of all visible signals.
This happens as well if signals get shown/hidden from the plot \[Functionality/[6.2 Checkbutton-Tree](#62-checkbutton-tree)\] and if no zoom level is applied \[Functionality/Toolbar/[6.3.1 Zooming](#631-zooming)\].

## 6.2 Checkbutton-Tree
The checkbutton-tree is a manipulator of the plot view. It handles which signals should be shown (i.e. visible) and which
should be hidden from the plot.
The checkbutton-tree is located on the right side and contains all received signals. Each signal may contain components
which are indented to the theirs top level signal to indicate the hierarchy.
Each signal - and all component of each signal - owns a checkbutton which can be selected/deselected to show/hide the
corresponding signal/component from the plot. If a signal or component is hidden its data get still received and recorded.
This means if late one the signal/component gets shown again all data points within the recent 30 seconds are shown as well.

If a signal's checkbutton gets unchecked also all signal's components get unchecked. Unchecked signals/components are hidden form the
plot until they get checked again. As soon as a signal get unchecked its subtree of components gets collapsed. Visa
versa if the signal gets checked its subtree gets expanded und all of its component gets checked as well automatically.
The checkbutton of a signal which owns components gets updated automatically responding to its components. If all
components get checked/unchecked the signal get checked/unchecked as well. If some of its components are checked and some
are unchecked the signal's checkbutton will go in a special state (called tri-state) which is in between checked and
unchecked.

Initially the tree is empty and grows with the number of received signals. If a new, unknown signal is received for the first
time an entry is appended to the end of this tree. New signals are marked as visible (i.e. checked) automatically. If this
is not desired this behaviour can be changed by clicking the above button **Check new automatically.**, which become strike out.

Above the tree there are in total three buttons. The first button is labeled **Check new automatically.**, which is explained above.
The second button **Disable all. (toggle)** acts as toggle and either disables or enables all signals, which implies that
the tree gets collapsed/expanded automatically.


## 6.3 Toolbar
The toolbar is located topmost above the plot view. It performance especially two function: zooming the axis and saving
the current view of the plot as image.

### 6.3.1 Zooming
The zoom tool is a manipulator of the plot view. It handles the scale of the x- and y-axes.
To enter the zoom mode press the **magnifier button** top left. The hint 'zoom rect' will be disabled at the top right side.
If the zoom mode is active the cursor icon will chang into a crosshair cursor as soon as the cursor hovers over the plot.
To zoom just draw a rectangle within the plot. The limits of x and y of this rectangle will be set to the plot.
The x- and y-axis handles the zoom level differently.

For the y-axis the range, i.e. the maximum and minimum value, will be set fixed to the upper and lower edge of the
rectangle. This range will not be changed even if the biggest or smallest y-value of any signal or signal's component
changed.

For the x-axis the range is handled as a proportion factor because the x-axis is floating/changing all the time. This
means the x-axis is floating and changing even if plot is zoomed. But the proportion of the visible x-axis can be
changed through the zoom.

Usually the zoom effect all four edges (i.e. minimum and maximum of x- and y-axis) because the rectangle lies completely
within the plot view. But if the rectangle can be dragged over the plot so that only two edges lies within the plot.
This can be used to effect either only minimum or the maximum of both axis. The other edges stay unaffected and still
adopt the axis range of the initial behaviour.

The zoom level can be nested which means a zoomed view can be zoomed again. To navigate through the history of zoom level
use the **arrow buttons** for- and backwards within the toolbar.

To reset all zoom level and restore the initial plot view press the **home button**. The home button clears also the zoom history.

### 6.3.2 Pause
Another accessory is that the plot can be pause. This is done by double clicking the plot itself.
While the plot is paused all new received data get discarded (but still recorded within the logfile \[Output/[5.1 Logfile](#51-logfile)\])
and will not be plotted even if the plot gets continued. At the moment when the plot continued new received data will
inserted into to plot again. A visual gab in front of this new data will indicate the break if there are still data points
before the break occurs which are not older than 30 seconds.

### 6.3.3 Snapshot
The last two icons are **save buttons**. The first performs a quick save and the second adjustable snapshot. This two buttons
can be distinguish with the mouse hover hint (`Quick-Save` and `Adjustable Snapshot`).
The **quick save button** takes a snapshot of the current view plot without disruptions. The surrounding toolbar and
checkbutton-tree are not part of the snapshot. In place of the checkbutton-tree a legend of the current visible signals
and components is inserted.
The **adjustable snapshot button** opens a new instance of the plot view which own the same signals/components as the currently
visible plot view. There mainly the zoom can be adjusted before saving.
All snapshots are stored with the directory `out/` \[[5. Output](#5-output)\].


# 7. JSON Format
To send data points to the plotter the data must be delivered as JSON string the the UDP port 30000, which is declared within the variable `UPD_PORT` \[[4. Config](#4-config)\].
The format of the JSON string is an array of objects `[{ojb},{obj},{obj},...]`, where the first object `{obj}` must contain
the meta information `{"PacketCounter":Number}` as continuously increasing number.
The second object must contain the timestamp as `{"Timestamp":Number}` which acts as x-value for all following signals
as long as a new timestamp object occurs.
All following objects contains the y-values for the different signals while sharing the most recent received timestamp.
A signal object looks like `{"SignalName":y-value}` and contains the name and the y-value for one specific signal.

## 7.1 Primitive Signals
If a signal has no components its called a primitive signal and its y-value is just a primitive value.
A primitive value is either an instance of a number type or instance of a boolean type, whereat a boolean is
map to 0 and 1 as `false` and `true` respectively. Hence a primitive signal looks like `{"SignalName":primitive-value}`.

## 7.2 Composite Signals
If a signal consists of components its y-value represents not a primitive value but a composite object instead.
A composite object can be either an array type or a mapping type.

### 7.2.1 Array Type
An array type as y-value is just an sequence of multiple primitive values so that the signal looks like
`{"SignalName":[primitive-value, primitive-value, ...]}`. The components get labeled with the enumerated array index within
the plotter's checkbutton-tree \[Functionality/[6.2 Checkbutton-Tree](#62-checkbutton-tree)\].
### 7.2.2 Mapping Type
An mapping type as y-value also holds multiple primitive values but with the difference that each component owns a separated
label. This label is used for the plotter's checkbutton-tree instead of the enumerated array index. Hence a mapping type
signal looks like `{"SignalName":{"ComponentName":primitive-value, "ComponentName":primitive-value, ...}}`.

## 7.3 Squashing
There is one more optimization to squash the JSON string. All signal objects (i.e. not the 'PacketCounter' and 'Timestamp'
object) may not be encapsulated as an separated JSON object - e.g. `{"SignalName":y-value}{"SignalName":y-value}...`.

Instead they may be squashed to '{"SignalName":y-value, "SignalName":y-value, ...}'. It does not matter if all
or only some of the signal objects are squashed together. So the followings are all the same:
```
{"SignalName":y-value}{"SignalName":y-value}{"SignalName":y-value}
{"SignalName":y-value, "SignalName":y-value}{"SignalName":y-value}
{"SignalName":y-value}{"SignalName":y-value, "SignalName":y-value}
{"SignalName":y-value, "SignalName":y-value, "SignalName":y-value}
```
