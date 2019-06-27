import tkinter as tk
from tkinter import ttk, font
import ttkwidgets


class CheckboxFrame(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(master=parent, bg='white', *args, **kwargs)
        self.pack(side=tk.RIGHT, fill=tk.Y)

        # buttons
        self.button_toggle_check_automatically = tk.Button(master=self, text='Check new automatically.',
                                                           command=self.toggle_check_new_automatically,
                                                           relief='flat', overrelief='solid', bd=1,
                                                           bg='white', activebackground='white',
                                                           fg='black', activeforeground='black')
        self.button_toggle_check_automatically.pack()
        self._is_toggle_set_to_check_new_automatically = True

        self.button_toggle_checkbuttons = tk.Button(master=self, text='Disable all. (toggle)',
                                                    command=self.toggle_all_checkbuttons,
                                                    relief='flat', overrelief='solid', bd=1,
                                                    bg='white', activebackground='white',
                                                    fg='black', activeforeground='black')
        self.button_toggle_checkbuttons.pack()
        self._is_toggle_set_to_disabled = True

        self.button_toggle_collapse = tk.Button(master=self, text='Collapse all. (toggle)',
                                                command=self.toggle_all_collapse,
                                                relief='flat', overrelief='solid', bd=1,
                                                bg='white', activebackground='white',
                                                fg='black', activeforeground='black')
        self.button_toggle_collapse.pack()
        self._is_toggle_set_to_collapsed = True

        # checkbutton tree
        # https://github.com/RedFantom/ttkwidgets/blob/master/ttkwidgets/checkboxtreeview.py
        # https://docs.python.org/3.6/library/tkinter.ttk.html#ttk-treeview
        self._checkbutton_tree = ttkwidgets.CheckboxTreeview(master=self, show='tree')  # only 'tree ' no 'headings'
        self._checkbutton_tree.pack(side=tk.LEFT, fill=tk.Y)
        # workaround for Windows/Microsoft to remove border --> https://stackoverflow.com/a/23690759/3108856
        ttk.Style().layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])

        self._checkbutton_tree.bind('<Button-1>', self._row_click, add=True)  # add=True to trigger also
        # internal event handling

        # scrollbar
        scrollbar = ttk.Scrollbar(master=self, orient="vertical", command=self._checkbutton_tree.yview)
        self._checkbutton_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self._checkbutton_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _row_click(self, event):
        # auto collapse/expand if all unchecked/checked
        element = event.widget.identify_element(event.x, event.y)
        if element != 'image':  # i.e. checkbuttons which are realised as images
            return
        item_id = self._checkbutton_tree.identify_row(event.y)
        signal_checkbutton = self._checkbutton_tree.parent(item_id)  # '' if no parent
        if signal_checkbutton:
            # item_id is component checkbox
            if self.is_checked(signal_checkbutton):
                self._checkbutton_tree.item(signal_checkbutton, open=True)
            else:
                self._checkbutton_tree.item(signal_checkbutton, open=False)
        else:
            # item_id is signal checkbox
            if self.is_checked(item_id):
                self._checkbutton_tree.item(item_id, open=True)
            else:
                self._checkbutton_tree.item(item_id, open=False)

        # TODO: make text clickable as well
        # x, y, widget = event.x, event.y, event.widget
        # elem = widget.identify_element(x, y)
        # if elem in ['text', 'padding']:
        #     print(item_id)
        #     # self._checkbutton_tree.change_state(item_id, 'unchecked')
        #
        #     # self._checkbutton_tree.event_generate('<Button-1>', x=45, y=y)
        #
        #     # if self._checkbutton_tree.tag_has("unchecked", item_id) or
        #     #         self._checkbutton_tree.tag_has("tristate", item_id):
        #     #     self._checkbutton_tree._check_ancestor(item_id)
        #     #     self._checkbutton_tree._check_descendant(item_id)
        #     # else:
        #     #     self._checkbutton_tree._uncheck_descendant(item_id)
        #     #     self._checkbutton_tree._uncheck_ancestor(item_id)

    def add_signal_checkbutton(self, signal_name, background_color=None):
        tags = []
        if self._is_toggle_set_to_check_new_automatically:
            tags.append('checked')  # all ancestors get checked as well
        if background_color:
            color_name = f'color_{signal_name}'
            tags.append(color_name)
            self._checkbutton_tree.tag_configure(tagname=color_name, foreground=background_color)

        self._checkbutton_tree.insert(parent='', index='end', iid=signal_name, text=signal_name, open=True,
                                      tags=tuple(tags))

    def add_component_checkbutton(self, signal_name, component_name, background_color=None):
        tags = []
        if self._is_toggle_set_to_check_new_automatically:
            tags.append('checked')
        if background_color:
            color_name = f'color_{signal_name}_{component_name}'
            tags.append(color_name)
            self._checkbutton_tree.tag_configure(tagname=color_name,
                                                 foreground=background_color)

        self._checkbutton_tree.insert(parent=signal_name, index='end', iid=f'{signal_name}_{component_name}',
                                      text=component_name, tags=tuple(tags))

    def is_known(self, signal_name, component_name=None):
        if component_name is None:
            return self._checkbutton_tree.exists(signal_name)
        return self._checkbutton_tree.exists(f'{signal_name}_{component_name}')

    def is_checked(self, signal_name, component_name=None):
        if component_name is None:
            item = signal_name
        else:
            item = f'{signal_name}_{component_name}'

        is_checked = self._checkbutton_tree.tag_has('checked', item=item)
        is_tristate = self._checkbutton_tree.tag_has('tristate', item=item)
        return is_checked or is_tristate

    def toggle_all_checkbuttons(self):
        if self._is_toggle_set_to_disabled:
            self.disable_all_checkbuttons()
            self.button_toggle_checkbuttons.config(text='Enable all. (toggle)')
        else:
            self.enable_all_checkbuttons()
            self.button_toggle_checkbuttons.config(text='Disable all. (toggle)')

        self._is_toggle_set_to_disabled = not self._is_toggle_set_to_disabled

    def disable_all_checkbuttons(self):
        for signal_checkbutton in self._checkbutton_tree.get_children():  # all root children
            self._checkbutton_tree.change_state(signal_checkbutton, 'unchecked')
            for component_checkbutton in self._checkbutton_tree.get_children(item=signal_checkbutton):
                self._checkbutton_tree.change_state(component_checkbutton, 'unchecked')
        self._checkbutton_tree.collapse_all()

    def enable_all_checkbuttons(self):
        for signal_checkbutton in self._checkbutton_tree.get_children():
            self._checkbutton_tree.change_state(signal_checkbutton, 'checked')
            for component_checkbutton in self._checkbutton_tree.get_children(item=signal_checkbutton):
                self._checkbutton_tree.change_state(component_checkbutton, 'checked')
        self._checkbutton_tree.expand_all()

    def toggle_all_collapse(self):
        if self._is_toggle_set_to_collapsed:
            self._checkbutton_tree.collapse_all()
            self.button_toggle_collapse.config(text='Expand all. (toggle)')
        else:
            self._checkbutton_tree.expand_all()
            self.button_toggle_collapse.config(text='Collapse all. (toggle)')
        self._is_toggle_set_to_collapsed = not self._is_toggle_set_to_collapsed

    def toggle_check_new_automatically(self):
        current_font_name = self.button_toggle_check_automatically.cget('font')
        current_font = font.Font(font=current_font_name).copy()
        if current_font['overstrike'] == 0:
            current_font['overstrike'] = 1
            self._is_toggle_set_to_check_new_automatically = False
        else:
            current_font['overstrike'] = 0
            self._is_toggle_set_to_check_new_automatically = True
        self.button_toggle_check_automatically.configure(font=current_font)
