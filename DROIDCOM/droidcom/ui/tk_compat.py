from PySide6 import QtCore, QtGui, QtWidgets

from droidcom.utils import threading as threading_utils

# Tkinter -> PySide6 mapping for migration reference:
# tk/ttk widgets -> QtWidgets; tk variable classes -> QtCore; tk images -> QtGui
# tk/ttk: Frame/LabelFrame/Label/Button/Entry/Checkbutton/Radiobutton/Combobox/Notebook/PanedWindow/Separator
#   -> QtWidgets.QWidget/QGroupBox/QLabel/QPushButton/QLineEdit/QCheckBox/QRadioButton/QComboBox/QTabWidget/QSplitter/QFrame
# tk: Text/ScrolledText/Listbox/Canvas/Scrollbar/Toplevel -> QtWidgets.QPlainTextEdit/QPlainTextEdit/QListWidget/QGraphicsView/QScrollBar/QDialog
# tk: StringVar/BooleanVar -> QtCore (direct widget setters, or QtCore.Property/Signal if needed)
# tk: PhotoImage -> QtGui.QPixmap/QIcon


class MessageBox:
    @staticmethod
    def showinfo(title, message):
        QtWidgets.QMessageBox.information(None, title, message)

    @staticmethod
    def showerror(title, message):
        QtWidgets.QMessageBox.critical(None, title, message)

    @staticmethod
    def askyesno(title, message):
        return (
            QtWidgets.QMessageBox.question(
                None, title, message, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            == QtWidgets.QMessageBox.Yes
        )


class FileDialog:
    @staticmethod
    def askopenfilename(title=None, filetypes=None):
        filters = FileDialog._to_filter_string(filetypes)
        path, _ = QtWidgets.QFileDialog.getOpenFileName(None, title or "Select File", "", filters)
        return path

    @staticmethod
    def asksaveasfilename(defaultextension=None, filetypes=None, title=None, initialfile=None):
        filters = FileDialog._to_filter_string(filetypes)
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            None, title or "Save File", initialfile or "", filters
        )
        if path and defaultextension and not path.endswith(defaultextension):
            path += defaultextension
        return path

    @staticmethod
    def askdirectory(title=None, initialdir=None):
        return QtWidgets.QFileDialog.getExistingDirectory(
            None, title or "Select Directory", initialdir or ""
        )

    @staticmethod
    def _to_filter_string(filetypes):
        if not filetypes:
            return "All Files (*)"
        return ";;".join([f"{label} ({pattern})" for label, pattern in filetypes])


messagebox = MessageBox
filedialog = FileDialog


class _TkVarBase:
    def __init__(self, value=None):
        self._value = value
        self._callbacks = []

    def set(self, value):
        self._value = value
        for callback in self._callbacks:
            callback(None, None, None)

    def get(self):
        return self._value

    def trace_add(self, _mode, callback):
        self._callbacks.append(callback)


class StringVar(_TkVarBase):
    pass


class BooleanVar(_TkVarBase):
    pass


class _TkWidgetMixin:
    def pack(self, side=None, fill=None, expand=False, padx=0, pady=0, anchor=None, before=None):
        parent = self.parent()
        if parent is None:
            return
        layout = parent.layout()
        if layout is None:
            if side in ("left", "right"):
                layout = QtWidgets.QHBoxLayout(parent)
            else:
                layout = QtWidgets.QVBoxLayout(parent)
            parent.setLayout(layout)
        layout.addWidget(self)
        if expand:
            layout.setStretch(layout.count() - 1, 1)

    def grid(self, row=0, column=0, rowspan=1, columnspan=1, sticky=None, padx=0, pady=0):
        parent = self.parent()
        if parent is None:
            return
        layout = parent.layout()
        if not isinstance(layout, QtWidgets.QGridLayout):
            layout = QtWidgets.QGridLayout(parent)
            parent.setLayout(layout)
        layout.addWidget(self, row, column, rowspan, columnspan)

    def pack_propagate(self, _flag):
        return

    def columnconfigure(self, _index, **_kwargs):
        return

    def rowconfigure(self, _index, **_kwargs):
        return

    def configure(self, **kwargs):
        self._apply_config(**kwargs)

    def config(self, **kwargs):
        self._apply_config(**kwargs)

    def _apply_config(self, **kwargs):
        text = kwargs.get("text")
        if text is not None and hasattr(self, "setText"):
            self.setText(text)
        state = kwargs.get("state")
        if state is not None:
            enabled = state not in ("disabled", QtCore.Qt.Disabled)
            if hasattr(self, "setEnabled"):
                self.setEnabled(enabled)
        width = kwargs.get("width")
        height = kwargs.get("height")
        if width or height:
            current = self.size()
            self.resize(width or current.width(), height or current.height())

    def bind(self, _event, _handler):
        return

    def bind_all(self, _event, _handler):
        return

    def after(self, ms, func):
        QtCore.QTimer.singleShot(ms, func)

    def update_idletasks(self):
        QtWidgets.QApplication.processEvents()

    def winfo_screenwidth(self):
        return QtWidgets.QApplication.primaryScreen().geometry().width()

    def winfo_screenheight(self):
        return QtWidgets.QApplication.primaryScreen().geometry().height()

    def winfo_width(self):
        return self.width()


class Frame(QtWidgets.QFrame, _TkWidgetMixin):
    def __init__(self, parent=None, padding=None):
        super().__init__(parent)


class LabelFrame(QtWidgets.QGroupBox, _TkWidgetMixin):
    def __init__(self, parent=None, text="", padding=None):
        super().__init__(text, parent)


class Label(QtWidgets.QLabel, _TkWidgetMixin):
    def __init__(self, parent=None, text="", textvariable=None, font=None):
        super().__init__(text, parent)
        self._textvar = textvariable
        if textvariable is not None:
            self.setText(str(textvariable.get()))
            textvariable.trace_add("write", self._sync_textvariable)
        if font:
            self.setFont(QtGui.QFont(*font))

    def _sync_textvariable(self, *_args):
        if self._textvar is not None:
            self.setText(str(self._textvar.get()))


class Button(QtWidgets.QPushButton, _TkWidgetMixin):
    def __init__(self, parent=None, text="", command=None, width=None, state=None):
        super().__init__(text, parent)
        if command:
            self.clicked.connect(command)
        if width:
            self.setFixedWidth(width * 10)
        if state == "disabled":
            self.setEnabled(False)


class Entry(QtWidgets.QLineEdit, _TkWidgetMixin):
    def __init__(self, parent=None, textvariable=None, width=None):
        super().__init__(parent)
        self._textvar = textvariable
        if textvariable is not None:
            self.setText(str(textvariable.get()))
            textvariable.trace_add("write", self._sync_textvariable)
            self.textChanged.connect(lambda value: textvariable.set(value))
        if width:
            self.setFixedWidth(width * 10)

    def _sync_textvariable(self, *_args):
        if self._textvar is not None:
            value = str(self._textvar.get())
            if self.text() != value:
                self.setText(value)


class Checkbutton(QtWidgets.QCheckBox, _TkWidgetMixin):
    def __init__(self, parent=None, text="", variable=None):
        super().__init__(text, parent)
        self._var = variable
        if variable is not None:
            self.setChecked(bool(variable.get()))
            self.stateChanged.connect(lambda value: variable.set(value == QtCore.Qt.Checked))


class Radiobutton(QtWidgets.QRadioButton, _TkWidgetMixin):
    def __init__(self, parent=None, text="", variable=None, value=None):
        super().__init__(text, parent)
        self._var = variable
        self._value = value
        if variable is not None:
            self.setChecked(variable.get() == value)
            self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked):
        if checked and self._var is not None:
            self._var.set(self._value)


class Combobox(QtWidgets.QComboBox, _TkWidgetMixin):
    def __init__(self, parent=None, textvariable=None, values=None, width=None, state=None):
        super().__init__(parent)
        self._textvar = textvariable
        if values:
            self.addItems(values)
        if textvariable is not None:
            self.setCurrentText(str(textvariable.get()))
            self.currentTextChanged.connect(lambda value: textvariable.set(value))
        if width:
            self.setFixedWidth(width * 10)
        if state == "readonly":
            self.setEditable(False)

    def bind(self, event, handler):
        if event == "<<ComboboxSelected>>":
            self.currentIndexChanged.connect(lambda _index: handler(None))

    def __setitem__(self, key, value):
        if key == "values":
            self.clear()
            self.addItems(value)


class Notebook(QtWidgets.QTabWidget, _TkWidgetMixin):
    def add(self, widget, text=""):
        super().addTab(widget, text)


class PanedWindow(QtWidgets.QSplitter, _TkWidgetMixin):
    def __init__(self, parent=None, orient="horizontal"):
        orientation = QtCore.Qt.Horizontal if orient == "horizontal" else QtCore.Qt.Vertical
        super().__init__(orientation, parent)

    def add(self, widget, weight=1):
        self.addWidget(widget)
        self.setStretchFactor(self.indexOf(widget), weight)


class Separator(QtWidgets.QFrame, _TkWidgetMixin):
    def __init__(self, parent=None, orient="horizontal"):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.HLine if orient == "horizontal" else QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class Progressbar(QtWidgets.QProgressBar, _TkWidgetMixin):
    def __init__(self, parent=None, orient=None, length=None, mode=None):
        super().__init__(parent)
        if mode == "indeterminate":
            self.setRange(0, 0)
        if length:
            self.setFixedWidth(length)

    def start(self):
        self.setRange(0, 0)

    def stop(self):
        self.setRange(0, 100)


class Scrollbar(QtWidgets.QScrollBar, _TkWidgetMixin):
    def __init__(self, parent=None, orient="vertical", command=None):
        orientation = QtCore.Qt.Vertical if orient == "vertical" else QtCore.Qt.Horizontal
        super().__init__(orientation, parent)
        if command:
            self.valueChanged.connect(lambda value: command("moveto", value))

    def set(self, _first, _last=None):
        return


class Listbox(QtWidgets.QListWidget, _TkWidgetMixin):
    def curselection(self):
        return [self.row(item) for item in self.selectedItems()]

    def get(self, index):
        item = self.item(index)
        return item.text() if item else ""

    def insert(self, _index, text):
        self.addItem(text)

    def delete(self, start, end=None):
        if end is None:
            end = start
        if end == tk.END:
            end = self.count() - 1
        if start == tk.END:
            start = self.count() - 1
        for row in range(end, start - 1, -1):
            item = self.takeItem(row)
            del item

    def size(self):
        return self.count()

    def selection_set(self, index):
        self.setCurrentRow(index)

    def selection_clear(self, _start, _end=None):
        self.clearSelection()

    def see(self, index):
        item = self.item(index)
        if item:
            self.scrollToItem(item)

    def bind(self, event, handler):
        if event == "<Double-1>":
            self.itemDoubleClicked.connect(lambda _item: handler(None))


class Text(QtWidgets.QPlainTextEdit, _TkWidgetMixin):
    def __init__(self, parent=None, height=None, width=None, wrap=None, font=None):
        super().__init__(parent)
        if height:
            self.setFixedHeight(height * 18)
        if width:
            self.setFixedWidth(width * 10)
        if font:
            self.setFont(QtGui.QFont(*font))
        if wrap == "word":
            self.setWordWrapMode(QtGui.QTextOption.WordWrap)
        elif wrap == "none":
            self.setWordWrapMode(QtGui.QTextOption.NoWrap)

    def insert(self, _index, text, _tag=None):
        self.appendPlainText(text.rstrip("\n"))

    def delete(self, _start, _end=None):
        self.setPlainText("")

    def get(self, _start, _end=None):
        return self.toPlainText()

    def see(self, _index):
        self.moveCursor(QtGui.QTextCursor.End)

    def config(self, **kwargs):
        state = kwargs.get("state")
        if state == "disabled":
            self.setReadOnly(True)
        elif state == "normal":
            self.setReadOnly(False)

    def yview(self, action, value=None):
        bar = self.verticalScrollBar()
        if action == "moveto" and value is not None:
            bar.setValue(int(value))
        elif action == "scroll" and value is not None:
            bar.setValue(bar.value() + int(value))

    def tag_configure(self, _tag, **_kwargs):
        return


class ScrolledText(Text):
    pass


class scrolledtext:
    ScrolledText = ScrolledText


class Treeview(QtWidgets.QTreeWidget, _TkWidgetMixin):
    def __init__(self, parent=None, columns=None, yscrollcommand=None):
        super().__init__(parent)
        self._columns = columns or []
        self.setColumnCount(len(self._columns) + 1)
        self.setHeaderLabels(["Name", *self._columns])
        if yscrollcommand:
            self.verticalScrollBar().valueChanged.connect(lambda _: yscrollcommand())

    def column(self, column, width=None, minwidth=None, anchor=None):
        column_index = 0 if column == "#0" else self._columns.index(column) + 1
        if width:
            self.setColumnWidth(column_index, width)

    def heading(self, column, text=""):
        column_index = 0 if column == "#0" else self._columns.index(column) + 1
        self.headerItem().setText(column_index, text)

    def insert(self, _parent, _index, text="", values=(), image=None, tags=()):
        item = QtWidgets.QTreeWidgetItem([text, *[str(v) for v in values]])
        item.setData(0, QtCore.Qt.UserRole, tags)
        self.addTopLevelItem(item)
        return item

    def get_children(self):
        return [self.topLevelItem(i) for i in range(self.topLevelItemCount())]

    def delete(self, item):
        if isinstance(item, list):
            for it in item:
                self._delete_item(it)
        else:
            self._delete_item(item)

    def _delete_item(self, item):
        index = self.indexOfTopLevelItem(item)
        if index >= 0:
            self.takeTopLevelItem(index)

    def item(self, item_id, option=None):
        if option == "text":
            return item_id.text(0)
        if option == "tags":
            return item_id.data(0, QtCore.Qt.UserRole) or ()
        return {"text": item_id.text(0)}

    def selection(self):
        return self.selectedItems()

    def selection_set(self, item_id):
        self.setCurrentItem(item_id)

    def bind(self, event, handler):
        if event == "<Double-1>":
            self.itemDoubleClicked.connect(lambda _item, _column: handler(None))

    def yview(self, action, value=None):
        bar = self.verticalScrollBar()
        if action == "moveto" and value is not None:
            bar.setValue(int(value))
        elif action == "scroll" and value is not None:
            bar.setValue(bar.value() + int(value))


class Canvas(QtWidgets.QScrollArea, _TkWidgetMixin):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._content_widget = None

    def create_window(self, _position, window=None, anchor=None):
        if window:
            self._content_widget = window
            self.setWidget(window)
        return window

    def configure(self, **kwargs):
        return

    def bbox(self, _tag):
        if self._content_widget:
            rect = self._content_widget.geometry()
            return (rect.x(), rect.y(), rect.width(), rect.height())
        return (0, 0, 0, 0)

    def yview_scroll(self, amount, _units):
        bar = self.verticalScrollBar()
        bar.setValue(bar.value() + amount * 10)

    def itemconfig(self, _item, **kwargs):
        width = kwargs.get("width")
        if width and self._content_widget:
            self._content_widget.setFixedWidth(width)

    def yview(self, action, value=None):
        bar = self.verticalScrollBar()
        if action == "moveto" and value is not None:
            bar.setValue(int(value))
        elif action == "scroll" and value is not None:
            bar.setValue(bar.value() + int(value))


class Toplevel(QtWidgets.QDialog, _TkWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)

    def title(self, text):
        self.setWindowTitle(text)

    def geometry(self, geometry):
        parts = geometry.split("x")
        if len(parts) == 2 and "+" not in parts[1]:
            width, height = parts
            self.resize(int(width), int(height))

    def resizable(self, _width, _height):
        return

    def transient(self, _parent):
        return

    def grab_set(self):
        self.setModal(True)

    def wait_window(self, _window=None):
        self.exec()

    def protocol(self, _event, _handler):
        return


class TkApp(QtWidgets.QApplication):
    pass


class tk:
    END = "end"
    WORD = "word"
    BOTH = "both"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    X = "x"
    Y = "y"
    W = "w"
    E = "e"
    N = "n"
    S = "s"
    NONE = "none"

    Tk = TkApp
    Toplevel = Toplevel
    Frame = Frame
    LabelFrame = LabelFrame
    Label = Label
    Button = Button
    Entry = Entry
    Checkbutton = Checkbutton
    Radiobutton = Radiobutton
    Combobox = Combobox
    Notebook = Notebook
    PanedWindow = PanedWindow
    Separator = Separator
    Progressbar = Progressbar
    Scrollbar = Scrollbar
    Listbox = Listbox
    Text = Text
    Canvas = Canvas
    StringVar = StringVar
    BooleanVar = BooleanVar


class ttk:
    Frame = Frame
    LabelFrame = LabelFrame
    Label = Label
    Button = Button
    Entry = Entry
    Checkbutton = Checkbutton
    Radiobutton = Radiobutton
    Combobox = Combobox
    Notebook = Notebook
    PanedWindow = PanedWindow
    Separator = Separator
    Progressbar = Progressbar
    Scrollbar = Scrollbar
    Treeview = Treeview
