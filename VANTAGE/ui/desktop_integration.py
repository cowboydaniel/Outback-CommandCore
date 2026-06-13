"""Linux desktop integration: system-tray applet and desktop background widget.

Each consumer (tray, desktop widget) has its own independently chosen source
(local machine or any SSH server).  The controller maintains a per-source
metrics cache and fetches remote metrics in background threads.
"""
import logging
import os
import subprocess
import threading
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal, Slot, QObject
from PySide6.QtGui import (QIcon, QFont, QColor, QPainter, QPen,
                            QPixmap, QPainterPath, QGuiApplication, QAction)
from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget,
                                QVBoxLayout, QLabel, QDialog, QFormLayout,
                                QPushButton, QDialogButtonBox, QSlider,
                                QCheckBox, QGroupBox, QComboBox)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_bytes(b: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB'):
        if b < 1024:
            return f"{b:.0f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"


def _status_color(cpu: float, mem: float) -> str:
    if cpu > 85 or mem > 85:
        return "#E53935"
    if cpu > 60 or mem > 60:
        return "#FB8C00"
    return "#43A047"


def _dot_icon(color: str) -> QIcon:
    px = QPixmap(16, 16)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, 12, 12)
    p.end()
    return QIcon(px)


def _metric_lines(data: dict) -> list[str]:
    cpu  = data.get('cpu_percent', 0)
    mem  = data.get('memory_percent', 0)
    temp = data.get('cpu_temp')
    disk = data.get('disk_percent', 0)
    sent = data.get('net_bytes_sent', 0)
    recv = data.get('net_bytes_recv', 0)
    up   = data.get('uptime_seconds', 0)
    h, m = int(up // 3600), int((up % 3600) // 60)
    temp_str = f"  {temp:.0f}°C" if temp is not None else ""
    return [
        f"CPU:    {cpu:5.1f}%{temp_str}",
        f"Memory: {mem:5.1f}%",
        f"Disk:   {disk:5.1f}%",
        f"Net ↑:  {_fmt_bytes(int(sent))}",
        f"Net ↓:  {_fmt_bytes(int(recv))}",
        f"Uptime: {h}h {m}m",
    ]


# ---------------------------------------------------------------------------
# Source selector — reusable QMenu section
# ---------------------------------------------------------------------------

class SourceMenu(QObject):
    """Adds a 'Monitor source' sub-menu and emits source_changed(source_id)."""

    source_changed = Signal(str)

    def __init__(self, registry, current_source: str = "local", parent=None):
        super().__init__(parent)
        self._registry = registry
        self._current = current_source
        self._actions: list[QAction] = []
        self._menu = QMenu("Monitor source")
        self._rebuild()
        if registry:
            registry.servers_changed.connect(self._rebuild)

    @property
    def menu(self) -> QMenu:
        return self._menu

    @property
    def current(self) -> str:
        return self._current

    def set_current(self, source_id: str):
        self._current = source_id
        self._sync_checks()

    def _rebuild(self):
        self._menu.clear()
        self._actions.clear()
        self._add_action("local", "Local machine")
        if self._registry:
            for srv in self._registry.all_servers():
                self._add_action(srv.server_id, srv.display_name)
        self._sync_checks()

    def _add_action(self, source_id: str, label: str):
        act = QAction(label, self._menu, checkable=True)
        act.setData(source_id)
        sid = source_id
        act.triggered.connect(lambda _=False, s=sid: self._select(s))
        self._menu.addAction(act)
        self._actions.append(act)

    def _select(self, source_id: str):
        self._current = source_id
        self._sync_checks()
        self.source_changed.emit(source_id)

    def _sync_checks(self):
        for act in self._actions:
            act.setChecked(act.data() == self._current)


# ---------------------------------------------------------------------------
# System Tray Applet
# ---------------------------------------------------------------------------

class TrayApplet(QObject):
    show_window_requested = Signal()
    quit_requested = Signal()
    # source_changed carries the source_id chosen *for the tray*
    source_changed = Signal(str)

    def __init__(self, registry, initial_source: str = "local", parent=None):
        super().__init__(parent)
        self._registry = registry

        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(_dot_icon("#43A047"))
        self._tray.setToolTip("VANTAGE")
        self._tray.activated.connect(self._on_activated)

        self._src_menu = SourceMenu(registry, initial_source, parent=self)
        self._src_menu.source_changed.connect(self._on_source_changed)

        self._build_context_menu()
        self._tray.show()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_icon)
        self._timer.start(1000)

        self._data: dict = {}
        self._label: str = "Local"

    def _build_context_menu(self):
        menu = QMenu()
        menu.addMenu(self._src_menu.menu)
        menu.addSeparator()
        show_act = QAction("Open VANTAGE", self)
        show_act.triggered.connect(self.show_window_requested)
        menu.addAction(show_act)
        settings_act = QAction("Desktop integration settings…", self)
        settings_act.triggered.connect(self._open_settings)
        menu.addAction(settings_act)
        menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self.quit_requested)
        menu.addAction(quit_act)
        self._tray.setContextMenu(menu)

    def _open_settings(self):
        # Controller will connect this signal to show the settings dialog
        pass  # overridden by controller

    def _on_source_changed(self, source_id: str):
        self.source_changed.emit(source_id)

    def push(self, data: dict, label: str):
        self._data = data
        self._label = label

    def _refresh_icon(self):
        cpu = self._data.get('cpu_percent', 0)
        mem = self._data.get('memory_percent', 0)
        temp = self._data.get('cpu_temp')
        temp_str = f" {temp:.0f}°C" if temp is not None else ""
        disk = self._data.get('disk_percent', 0)
        mem_pct = self._data.get('memory_percent', 0)
        self._tray.setIcon(_dot_icon(_status_color(cpu, mem_pct)))
        lines = "\n".join(_metric_lines(self._data))
        self._tray.setToolTip(f"VANTAGE — {self._label}\n{lines}")

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window_requested.emit()

    @property
    def current_source(self) -> str:
        return self._src_menu.current

    def destroy(self):
        self._tray.hide()


# ---------------------------------------------------------------------------
# Desktop background widget
# ---------------------------------------------------------------------------

class DesktopWidget(QWidget):
    # Emitted when user picks a new source from the widget's own context menu
    source_changed = Signal(str)

    def __init__(self, registry, initial_source: str = "local", parent=None):
        # No Qt.Tool — it causes the window to float above normal windows on
        # many WMs regardless of WindowStaysOnBottomHint.
        super().__init__(None,
                         Qt.Window |
                         Qt.FramelessWindowHint |
                         Qt.WindowStaysOnBottomHint |
                         Qt.NoDropShadowWindowHint)
        self._registry = registry
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_X11DoNotAcceptFocus, True)
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)
        self.setWindowFlag(Qt.X11BypassWindowManagerHint, False)  # keep WM hints active
        self._hints_set = False

        self._data: dict = {}
        self._label: str = "Local"
        self._opacity: float = 0.82
        self._font_size: int = 13

        self._src_menu = SourceMenu(registry, initial_source, parent=self)
        self._src_menu.source_changed.connect(self.source_changed)

        self._build_ui()
        self._load_geometry()
        self.show()

    def showEvent(self, event):
        super().showEvent(event)
        # Set X11 hints after the window is mapped so winId() is valid.
        # Do this only once; repeated calls on re-show are harmless but wasteful.
        if not self._hints_set:
            self._hints_set = True
            QTimer.singleShot(0, self._set_x11_hints)

    def _set_x11_hints(self):
        """Set X11 window type + state hints after the window is mapped."""
        wid = str(int(self.winId()))
        # Desktop window type: most WMs will keep it below everything
        try:
            subprocess.Popen(
                ['xprop', '-id', wid,
                 '-f', '_NET_WM_WINDOW_TYPE', '32a',
                 '-set', '_NET_WM_WINDOW_TYPE', '_NET_WM_WINDOW_TYPE_DESKTOP'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        # State: below + skip taskbar + skip pager
        state = ('_NET_WM_STATE_BELOW, '
                 '_NET_WM_STATE_SKIP_TASKBAR, '
                 '_NET_WM_STATE_SKIP_PAGER')
        try:
            subprocess.Popen(
                ['xprop', '-id', wid,
                 '-f', '_NET_WM_STATE', '32a',
                 '-set', '_NET_WM_STATE', state],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)
        self._title_lbl = QLabel("VANTAGE")
        self._title_lbl.setAlignment(Qt.AlignCenter)
        self._title_lbl.setSizePolicy(
            self._title_lbl.sizePolicy().horizontalPolicy(),
            self._title_lbl.sizePolicy().verticalPolicy())
        layout.addWidget(self._title_lbl)
        self._lines: list[QLabel] = []
        for _ in range(6):
            lbl = QLabel("—")
            lbl.setAlignment(Qt.AlignLeft)
            lbl.setWordWrap(False)
            layout.addWidget(lbl)
            self._lines.append(lbl)
        self._apply_fonts()
        # Wide enough for longest expected line; will grow if needed
        self.setMinimumWidth(260)

    def _apply_fonts(self):
        alpha = int(self._opacity * 255)
        self._title_lbl.setFont(QFont("Monospace", self._font_size + 1, QFont.Bold))
        self._title_lbl.setStyleSheet(f"color: rgba(144,202,249,{alpha});")
        body_style = f"color: rgba(224,224,224,{alpha});"
        body_font = QFont("Monospace", self._font_size)
        for lbl in self._lines:
            lbl.setFont(body_font)
            lbl.setStyleSheet(body_style)

    def push(self, data: dict, label: str):
        self._data = data
        self._label = label
        self._title_lbl.setText(f"VANTAGE — {label}")
        for lbl, val in zip(self._lines, _metric_lines(data)):
            lbl.setText(val)
        self.adjustSize()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        p.fillPath(path, QColor(10, 12, 20, int(self._opacity * 160)))
        p.setPen(QPen(QColor(60, 80, 120, 180), 1))
        p.drawPath(path)

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        menu.addMenu(self._src_menu.menu)
        menu.addSeparator()
        hide_act = QAction("Hide widget", self)
        hide_act.triggered.connect(self.hide)
        menu.addAction(hide_act)
        menu.exec(e.globalPos())

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _):
        self._save_geometry()

    def set_opacity(self, value: float):
        self._opacity = max(0.2, min(1.0, value))
        self._apply_fonts()
        self.update()

    def set_font_size(self, size: int):
        self._font_size = size
        self._apply_fonts()
        self.adjustSize()

    @property
    def current_source(self) -> str:
        return self._src_menu.current

    def _cfg_path(self):
        return os.path.expanduser("~/.vantage/desktop_widget.conf")

    def _save_geometry(self):
        try:
            os.makedirs(os.path.dirname(self._cfg_path()), exist_ok=True)
            with open(self._cfg_path(), 'w') as f:
                f.write(f"{self.x()},{self.y()},{self.width()},{self.height()}\n")
        except Exception:
            pass

    def _load_geometry(self):
        try:
            with open(self._cfg_path()) as f:
                x, y, w, h = map(int, f.read().strip().split(','))
            self.setGeometry(x, y, w, h)
        except Exception:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            self.adjustSize()
            self.move(screen.right() - self.width() - 20, screen.top() + 40)


# ---------------------------------------------------------------------------
# Settings dialog
# ---------------------------------------------------------------------------

class DesktopIntegrationSettings(QDialog):
    def __init__(self, controller: 'DesktopIntegrationController', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Desktop Integration Settings")
        self._ctrl = controller
        layout = QVBoxLayout(self)

        # --- Tray applet ---
        tray_box = QGroupBox("System Tray Applet")
        tray_layout = QFormLayout(tray_box)
        self._tray_cb = QCheckBox("Enable tray applet")
        self._tray_cb.setChecked(controller.tray_enabled)
        self._tray_cb.toggled.connect(controller.set_tray_enabled)
        tray_layout.addRow(self._tray_cb)
        layout.addWidget(tray_box)

        # --- Desktop widget ---
        widget_box = QGroupBox("Desktop Background Widget")
        widget_layout = QFormLayout(widget_box)
        self._widget_cb = QCheckBox("Enable desktop widget")
        self._widget_cb.setChecked(controller.widget_enabled)
        self._widget_cb.toggled.connect(controller.set_widget_enabled)
        widget_layout.addRow(self._widget_cb)

        w = controller.desktop_widget
        if w:
            self._opacity = QSlider(Qt.Horizontal)
            self._opacity.setRange(20, 100)
            self._opacity.setValue(int(w._opacity * 100))
            self._opacity.valueChanged.connect(lambda v: w.set_opacity(v / 100))
            widget_layout.addRow("Opacity:", self._opacity)

            self._font_sz = QSlider(Qt.Horizontal)
            self._font_sz.setRange(9, 20)
            self._font_sz.setValue(w._font_size)
            self._font_sz.valueChanged.connect(w.set_font_size)
            widget_layout.addRow("Font size:", self._font_sz)

        layout.addWidget(widget_box)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class DesktopIntegrationController(QObject):
    """
    Owns the tray applet and desktop widget.  Maintains a per-source metrics
    cache; local metrics arrive via on_local_metrics(); remote metrics are
    fetched in background threads on a timer.
    """

    # Signal used to marshal remote fetch results back to the main thread.
    # Qt signals are thread-safe; QTimer.singleShot is not when called from
    # a plain threading.Thread.
    _remote_ready = Signal(str, object)   # source_id, metrics dict

    def __init__(self, registry=None, parent=None):
        super().__init__(parent)
        self._registry = registry
        self._tray: Optional[TrayApplet] = None
        self._widget: Optional[DesktopWidget] = None
        self._tray_enabled = False
        self._widget_enabled = False

        # source_id → latest metrics dict
        self._cache: dict[str, dict] = {"local": {}}
        # source_id → RemoteClient (lazy)
        self._clients: dict = {}
        self._client_lock = threading.Lock()

        self._remote_timer = QTimer(self)
        self._remote_timer.timeout.connect(self._fetch_remotes)
        self._remote_timer.start(3000)

        # Thread-safe bridge: background thread emits this, main thread updates cache
        self._remote_ready.connect(self._on_remote_ready)

    # ------------------------------------------------------------------
    # Enable / disable
    # ------------------------------------------------------------------

    def start(self, enable_tray: bool = True, enable_desktop_widget: bool = False):
        self.set_tray_enabled(enable_tray)
        self.set_widget_enabled(enable_desktop_widget)

    def set_tray_enabled(self, enabled: bool):
        if enabled and not self._tray:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self._tray = TrayApplet(self._registry, parent=self)
                # show_window_requested and quit_requested are wired in main.py
                # after start() returns, so the main_window reference is available.
                self._tray.source_changed.connect(self._on_tray_source_changed)
                self._tray._open_settings = self.show_settings
                self._tray_enabled = True
                self._push_to_consumers()
            else:
                logger.warning("System tray not available")
        elif not enabled and self._tray:
            self._tray.destroy()
            self._tray = None
            self._tray_enabled = False

    def set_widget_enabled(self, enabled: bool):
        if enabled and not self._widget:
            self._widget = DesktopWidget(self._registry, parent=self)
            self._widget.source_changed.connect(self._on_widget_source_changed)
            self._widget_enabled = True
            self._push_to_consumers()
        elif not enabled and self._widget:
            self._widget.hide()
            self._widget.deleteLater()
            self._widget = None
            self._widget_enabled = False

    @property
    def tray_enabled(self) -> bool:
        return self._tray is not None

    @property
    def widget_enabled(self) -> bool:
        return self._widget is not None and self._widget.isVisible()

    @property
    def tray(self) -> Optional[TrayApplet]:
        return self._tray

    @property
    def desktop_widget(self) -> Optional[DesktopWidget]:
        return self._widget

    # ------------------------------------------------------------------
    # Metrics ingestion
    # ------------------------------------------------------------------

    @Slot(dict)
    def on_local_metrics(self, data: dict):
        self._cache["local"] = data
        self._push_to_consumers()

    def _push_to_consumers(self):
        if self._tray:
            src = self._tray.current_source
            data = self._cache.get(src, {})
            label = self._label_for(src)
            self._tray.push(data, label)
        if self._widget and self._widget.isVisible():
            src = self._widget.current_source
            data = self._cache.get(src, {})
            label = self._label_for(src)
            self._widget.push(data, label)

    def _label_for(self, source_id: str) -> str:
        if source_id == "local":
            return "Local"
        if self._registry:
            srv = self._registry.get(source_id)
            if srv:
                return srv.display_name
        return source_id

    # ------------------------------------------------------------------
    # Remote fetching
    # ------------------------------------------------------------------

    def _needed_sources(self) -> set[str]:
        sources: set[str] = set()
        if self._tray and self._tray.current_source != "local":
            sources.add(self._tray.current_source)
        if self._widget and self._widget.isVisible() and self._widget.current_source != "local":
            sources.add(self._widget.current_source)
        return sources

    @Slot()
    def _fetch_remotes(self):
        for source_id in self._needed_sources():
            threading.Thread(target=self._fetch_one, args=(source_id,),
                             daemon=True).start()

    def _fetch_one(self, source_id: str):
        client = self._get_client(source_id)
        if not client:
            return
        result = client.fetch_metrics()
        if result:
            import dataclasses
            # Emit signal instead of QTimer.singleShot — signals are thread-safe,
            # QTimer is not when called from a plain threading.Thread.
            self._remote_ready.emit(source_id, dataclasses.asdict(result))

    @Slot(str, object)
    def _on_remote_ready(self, source_id: str, data: dict):
        self._cache[source_id] = data
        self._push_to_consumers()

    def _get_client(self, source_id: str):
        with self._client_lock:
            if source_id in self._clients:
                return self._clients[source_id]
            if not self._registry:
                return None
            srv = self._registry.get(source_id)
            if not srv:
                return None
            from core.remote_client import RemoteClient
            client = RemoteClient(
                host=srv.host, port=srv.port, username=srv.username,
                password=srv.password, key_path=srv.key_path,
            )
            self._clients[source_id] = client
            return client

    # ------------------------------------------------------------------
    # Source change callbacks
    # ------------------------------------------------------------------

    def _on_tray_source_changed(self, source_id: str):
        # Immediately push whatever is in cache (may be empty until next fetch)
        self._push_to_consumers()

    def _on_widget_source_changed(self, source_id: str):
        self._push_to_consumers()

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    _show_window_cb = None  # set by main.py

    def _on_show_window(self):
        if self._show_window_cb:
            self._show_window_cb()

    def show_settings(self, parent=None):
        dlg = DesktopIntegrationSettings(self, parent)
        dlg.exec()
