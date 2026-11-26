"""Compact dialog for selecting a capture target, not a list of every system task."""
from pc_monitor.locales.i18n import tr
import os
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import psutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox,
                               QTableWidgetItem)
from pc_monitor.ui.qt_pages import table
from pc_monitor.ui.qt_theme import label, button, SPACE


@dataclass(frozen=True)
class Target:
    name: str
    pid: int
    created: float
    title: str = ""


def visible_windows():
    """Return one visible titled top-level window per PID; no game detection claim."""
    if os.name != "nt":
        return {}
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = (callback_type, wintypes.LPARAM)
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = (wintypes.HWND,)
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    windows = {}

    @callback_type
    def visit(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                text = ctypes.create_unicode_buffer(min(length + 1, 1024))
                user32.GetWindowTextW(hwnd, text, len(text))
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value and text.value.strip():
                    windows.setdefault(pid.value, text.value.strip())
        return True

    user32.EnumWindows(visit, 0)
    return windows


def collect_targets():
    try:
        windows = visible_windows()
    except OSError:
        windows = {}
    rows = []
    for proc in psutil.process_iter(["pid", "name", "create_time"], ad_value=None):
        info = proc.info
        pid = info["pid"]
        if pid and pid != os.getpid() and info["name"] and info["create_time"] is not None:
            rows.append(Target(info["name"], pid, info["create_time"], windows.get(pid, "")))
    return rows


def filter_targets(rows, query="", show_all=False):
    q = query.strip().casefold()
    return sorted(
        (r for r in rows if (show_all or r.title)
         and (not q or q in r.name.casefold() or q in r.title.casefold() or q in str(r.pid))),
        key=lambda r: (not bool(r.title), r.name.casefold(), r.pid),
    )


class ProcessPicker(QDialog):
    def __init__(self, parent=None, previous=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Výběr hry nebo aplikace"))
        self.resize(720, 490)
        self.setMinimumSize(480, 330)
        self.selected = None
        self.previous = previous
        self.rows = []
        self.filtered = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3 * SPACE, 3 * SPACE, 3 * SPACE, 3 * SPACE)
        layout.setSpacing(SPACE * 2)
        layout.addWidget(label(tr("Vyber proces pro měření FPS"), "section"))
        layout.addWidget(label(tr("Spusť hru a vyhledej její název, okno nebo PID."), "muted"))
        row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("Hledat hru, aplikaci nebo PID…"))
        self.search.setClearButtonEnabled(True)
        row.addWidget(self.search, 1)
        reload_button = button(tr("Obnovit"))
        reload_button.clicked.connect(self.reload)
        row.addWidget(reload_button)
        layout.addLayout(row)
        self.all = QCheckBox(tr("Zobrazit také procesy bez viditelného okna"))
        layout.addWidget(self.all)
        self.table = table([tr("Aplikace / proces"), tr("Název okna"), "PID"])
        from PySide6.QtWidgets import QHeaderView, QAbstractItemView
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 85)
        layout.addWidget(self.table, 1)
        self.count = label("", "muted")
        layout.addWidget(self.count)
        row = QHBoxLayout()
        row.addStretch()
        cancel = button(tr("Zrušit"))
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        self.confirm = button(tr("Vybrat proces"), True)
        self.confirm.clicked.connect(self.accept_selection)
        self.confirm.setEnabled(False)
        row.addWidget(self.confirm)
        layout.addLayout(row)
        self.search.textChanged.connect(self.render)
        self.all.toggled.connect(self.render)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        self.table.cellDoubleClicked.connect(lambda *_: self.accept_selection())
        self.reload()
        self.search.setFocus()

    def reload(self):
        self.rows = collect_targets()
        self.render()

    def render(self, *_):
        self.filtered = filter_targets(self.rows, self.search.text(), self.all.isChecked())
        self.table.clearSelection()
        self.table.setRowCount(len(self.filtered))
        self.table.setUpdatesEnabled(False)
        try:
            for i, target in enumerate(self.filtered):
                for j, value in enumerate((target.name, target.title or "—", str(target.pid))):
                    item = QTableWidgetItem(value)
                    item.setToolTip(value)
                    if j == 2:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(i, j, item)
                if self.previous == (target.pid, target.created):
                    self.table.selectRow(i)
        finally:
            self.table.setUpdatesEnabled(True)
        self.count.setText(tr(f"{len(self.filtered)} z {len(self.rows)} procesů") if self.filtered else
                           tr("Nic nenalezeno. Změň hledání nebo zobraz procesy bez okna."))
        self.selection_changed()

    def selection_changed(self):
        self.confirm.setEnabled(bool(self.table.selectedItems()))

    def accept_selection(self):
        row = self.table.currentRow()
        if self.table.selectedItems() and 0 <= row < len(self.filtered):
            self.selected = self.filtered[row]
            self.accept()
