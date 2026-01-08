"""ListBox component used in DROIDCOM widgets."""

from PySide6 import QtWidgets


class ListBox(QtWidgets.QListWidget):
    """QListWidget adapter with Tkinter-like listbox methods."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)

    def curselection(self):
        return [self.row(item) for item in self.selectedItems()]

    def get(self, index):
        index = self._normalize_index(index)
        if index is None:
            return ""
        item = self.item(index)
        return item.text() if item else ""

    def delete(self, first, last=None):
        if last is None:
            last = first
        first_index = self._normalize_index(first)
        last_index = self._normalize_index(last)
        if first_index is None:
            return
        if last_index is None:
            last_index = first_index
        for index in range(last_index, first_index - 1, -1):
            self.takeItem(index)

    def insert(self, index, text):
        text = str(text)
        if isinstance(index, str) and index.lower() == "end":
            self.addItem(text)
            return
        normalized = self._normalize_index(index)
        if normalized is None:
            self.addItem(text)
            return
        self.insertItem(normalized, text)

    def size(self):
        return self.count()

    def selection_set(self, first, last=None):
        first_index = self._normalize_index(first)
        last_index = self._normalize_index(last) if last is not None else first_index
        if first_index is None:
            return
        if last_index is None:
            last_index = first_index
        for index in range(first_index, last_index + 1):
            item = self.item(index)
            if item:
                item.setSelected(True)
        self.setCurrentRow(first_index)

    def selection_clear(self, first=None, last=None):
        self.clearSelection()

    def see(self, index):
        normalized = self._normalize_index(index)
        if normalized is None:
            return
        item = self.item(normalized)
        if item:
            self.scrollToItem(item)

    def _normalize_index(self, index):
        if isinstance(index, (list, tuple)):
            if not index:
                return None
            index = index[0]
        if isinstance(index, str):
            if index.lower() == "end":
                return max(self.count() - 1, 0)
            try:
                return int(index)
            except ValueError:
                return None
        try:
            return int(index)
        except (TypeError, ValueError):
            return None
