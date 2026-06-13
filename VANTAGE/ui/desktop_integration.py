"""Linux desktop integration: system-tray applet and desktop background widget."""
import logging
import os
import subprocess
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QPoint, QRect, Signal, Slot, QObject, QThread
from PySide6.QtGui import (QIcon, QFont, QColor, QPainter, QPen, QBrush,
                            QFontMetrics, QPixmap, QPainterPath, QGuiApplication)
from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget,
                                QVBoxLayout, QHBoxLayout, QLabel, QAction,
                                QCheckBox, QComboBox, QDialog, QFormLayout,
                                QPushButton, QDialogButtonBox, QSlider, QSizePolicy)

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


def _icon_from_color(color: str) -> QIcon:
    """Create a tiny coloured circle icon (used for tray)."""
    px = QPixmap(16, 16)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, 12, 12)
    p.end()
    return QIcon(px)


def _status_color(cpu: float, mem: float) -> str:
    if cpu > 85 or mem > 85:
        return "#E53935"   # red
    if cpu > 60 or mem > 60:
        return "#FB8C00"   # orange
    return "#43A047"       # green


# ---------------------------------------------------------------------------
# Tray tooltip popup
# ---------------------------------------------------------------------------

class _TrayPopup(QWidget):
    """Frameless floating panel shown on tray-icon hover/click."""

    def __init__(self):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self._title = QLabel("VANTAGE — Local")
        self._title.setStyleSheet("color:#90CAF9;font-weight:600;font-size:12px;")
        layout.addWidget(self._title)

        self._lines: list[QLabel] = []
        for _ in range(6):
            lbl = QLabel("—")
            lbl.setStyleSheet("color:#E0E0E0;font-size:11px;font-family:monospace;")
            layout.addWidget(lbl)
            self._lines.append(lbl)

        self.setMinimumWidth(220)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)
        p.fillPath(path, QColor(30, 30, 40, 220))
        p.setPen(QPen(QColor(80, 80, 100), 1))
        p.drawPath(path)

    def update_metrics(self, data: dict, source_label: str):
        self._title.setText(f"VANTAGE — {source_label}")
        cpu   = data.get('cpu_percent', 0)
        mem   = data.get('memory_percent', 0)
        temp  = data.get('cpu_temp')
        disk  = data.get('disk_percent', 0)
        sent  = data.get('net_bytes_sent', 0)
        recv  = data.get('net_bytes_recv', 0)
        up    = data.get('uptime_seconds', 0)

        h = int(up // 3600)
        m = int((up % 3600) // 60)
        temp_str = f"{temp:.0f}°C" if temp is not None else "N/A"

        values = [
            f"CPU:    {cpu:5.1f}%  {temp_str}",
            f"Memory: {mem:5.1f}%",
            f"Disk:   {disk:5.1f}%",
            f"Net ↑:  {_fmt_bytes(int(sent))}",
            f"Net ↓:  {_fmt_bytes(int(recv))}",
            f"Uptime: {h}h {m}m",
        ]
        for lbl, val in zip(self._lines, values):
            lbl.setText(val)
        self.adjustSize()

    def show_near_tray(self, tray_geometry: QRect):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        w, h = self.width(), self.height()
        x = min(tray_geometry.x(), screen.right() - w - 4)
        y = tray_geometry.top() - h - 4
        if y < screen.top():
            y = tray_geometry.bottom() + 4
        self.move(x, y)
        self.show()


# ---------------------------------------------------------------------------
# System Tray Applet
# ---------------------------------------------------------------------------

class TrayApplet(QObject):
    """System tray icon that shows live metrics in its tooltip and a popup."""

    # Emitted when the user selects a different source from the tray menu
    source_changed = Signal(str)   # "local" or server_id
    show_window_requested = Signal()
    quit_requested = Signal()

    def __init__(self, registry=None, parent=None):
        super().__init__(parent)
        self._registry = registry
        self._current_source = "local"
        self._latest: dict = {}
        self._popup = _TrayPopup()

        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(_icon_from_color("#43A047"))
        self._tray.setToolTip("VANTAGE")
        self._tray.activated.connect(self._on_activated)

        self._build_menu()
        self._tray.show()

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._refresh_icon)
        self._tick_timer.start(1000)

    # ------------------------------------------------------------------

    def _build_menu(self):
        menu = QMenu()

        # Source submenu
        self._source_menu = menu.addMenu("Monitor source")
        self._source_group: list[QAction] = []
        local_act = QAction("Local machine", self, checkable=True, checked=True)
        local_act.setData("local")
        local_act.triggered.connect(lambda: self._select_source("local"))
        self._source_menu.addAction(local_act)
        self._source_group.append(local_act)

        if self._registry:
            for srv in self._registry.all_servers():
                self._add_server_action(srv)
            self._registry.servers_changed.connect(self._rebuild_source_menu)

        menu.addSeparator()

        show_act = QAction("Open VANTAGE", self)
        show_act.triggered.connect(self.show_window_requested)
        menu.addAction(show_act)

        menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(self.quit_requested)
        menu.addAction(quit_act)

        self._tray.setContextMenu(menu)

    def _add_server_action(self, srv):
        act = QAction(srv.display_name, self, checkable=True)
        act.setData(srv.server_id)
        sid = srv.server_id
        act.triggered.connect(lambda: self._select_source(sid))
        self._source_menu.addAction(act)
        self._source_group.append(act)

    def _rebuild_source_menu(self):
        self._source_menu.clear()
        self._source_group.clear()
        local_act = QAction("Local machine", self, checkable=True,
                            checked=(self._current_source == "local"))
        local_act.setData("local")
        local_act.triggered.connect(lambda: self._select_source("local"))
        self._source_menu.addAction(local_act)
        self._source_group.append(local_act)
        if self._registry:
            for srv in self._registry.all_servers():
                self._add_server_action(srv)
        self._sync_check_marks()

    def _select_source(self, source_id: str):
        self._current_source = source_id
        self._sync_check_marks()
        self.source_changed.emit(source_id)

    def _sync_check_marks(self):
        for act in self._source_group:
            act.setChecked(act.data() == self._current_source)

    # ------------------------------------------------------------------

    def push_metrics(self, data: dict, source_label: str = "Local"):
        self._latest = data
        self._source_label = source_label

    def _refresh_icon(self):
        cpu = self._latest.get('cpu_percent', 0)
        mem = self._latest.get('memory_percent', 0)
        temp = self._latest.get('cpu_temp')
        temp_str = f" {temp:.0f}°C" if temp is not None else ""
        tooltip = f"CPU: {cpu:.0f}%{temp_str}  Mem: {mem:.0f}%"
        self._tray.setIcon(_icon_from_color(_status_color(cpu, mem)))
        self._tray.setToolTip(tooltip)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self._popup.isVisible():
                self._popup.hide()
            else:
                label = getattr(self, '_source_label', 'Local')
                self._popup.update_metrics(self._latest, label)
                geo = self._tray.geometry()
                self._popup.show_near_tray(geo)

    def hide_popup(self):
        self._popup.hide()

    def destroy(self):
        self._tray.hide()


# ---------------------------------------------------------------------------
# Desktop background widget (Linux / X11)
# ---------------------------------------------------------------------------

class DesktopWidget(QWidget):
    """Semi-transparent always-below widget painted onto the desktop wallpaper layer."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_X11NetWmWindowTypeDesktop, True)
        self.setWindowFlag(Qt.WindowDoesNotAcceptFocus, True)

        # Try to set _NET_WM_WINDOW_TYPE_DESKTOP hint so WMs keep it behind
        # everything (works on GNOME/KDE/XFCE/Openbox with X11).
        self._set_desktop_hint()

        self._data: dict = {}
        self._label = "Local"
        self._opacity: float = 0.82
        self._font_size: int = 13

        self._build_ui()

        # Restore saved position/size
        self._load_geometry()

        self.show()

    # ------------------------------------------------------------------

    def _set_desktop_hint(self):
        """Use xprop to set _NET_WM_WINDOW_TYPE=_NET_WM_WINDOW_TYPE_DESKTOP."""
        try:
            wid = int(self.winId())
            subprocess.Popen(
                ['xprop', '-id', str(wid),
                 '-f', '_NET_WM_WINDOW_TYPE', '32a',
                 '-set', '_NET_WM_WINDOW_TYPE', '_NET_WM_WINDOW_TYPE_DESKTOP'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass  # xprop not available or Wayland — still works, just at normal z-order

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        self._title_lbl = QLabel("VANTAGE")
        self._title_lbl.setAlignment(Qt.AlignCenter)

        self._lines: list[QLabel] = []
        for _ in range(7):
            lbl = QLabel("—")
            lbl.setAlignment(Qt.AlignLeft)
            self._lines.append(lbl)
            layout.addWidget(lbl)

        layout.insertWidget(0, self._title_lbl)
        self._apply_fonts()
        self.setMinimumSize(200, 160)
        self.adjustSize()

    def _apply_fonts(self):
        title_font = QFont("Monospace", self._font_size + 1, QFont.Bold)
        body_font  = QFont("Monospace", self._font_size)
        self._title_lbl.setFont(title_font)
        self._title_lbl.setStyleSheet(f"color: rgba(144,202,249,{int(self._opacity*255)});")
        style = f"color: rgba(224,224,224,{int(self._opacity*255)});"
        for lbl in self._lines:
            lbl.setFont(body_font)
            lbl.setStyleSheet(style)

    # ------------------------------------------------------------------

    def update_metrics(self, data: dict, source_label: str):
        self._data = data
        self._label = source_label
        self._refresh_labels()

    def _refresh_labels(self):
        d = self._data
        cpu   = d.get('cpu_percent', 0)
        mem   = d.get('memory_percent', 0)
        temp  = d.get('cpu_temp')
        disk  = d.get('disk_percent', 0)
        sent  = d.get('net_bytes_sent', 0)
        recv  = d.get('net_bytes_recv', 0)
        up    = d.get('uptime_seconds', 0)

        h = int(up // 3600)
        m = int((up % 3600) // 60)
        temp_str = f"  {temp:.0f}°C" if temp is not None else ""

        self._title_lbl.setText(f"VANTAGE — {self._label}")
        values = [
            f"CPU:    {cpu:5.1f}%{temp_str}",
            f"Memory: {mem:5.1f}%",
            f"Disk:   {disk:5.1f}%",
            f"Net ↑:  {_fmt_bytes(int(sent))}",
            f"Net ↓:  {_fmt_bytes(int(recv))}",
            f"Uptime: {h}h {m}m",
            "",  # spacer
        ]
        for lbl, val in zip(self._lines, values):
            lbl.setText(val)

    # ------------------------------------------------------------------

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        alpha = int(self._opacity * 160)
        p.fillPath(path, QColor(10, 12, 20, alpha))
        p.setPen(QPen(QColor(60, 80, 120, 180), 1))
        p.drawPath(path)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton and hasattr(self, '_drag_pos'):
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            e.accept()

    def mouseReleaseEvent(self, _):
        self._save_geometry()

    # ------------------------------------------------------------------

    def _cfg_path(self) -> str:
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
            # Default: top-right corner
            screen = QGuiApplication.primaryScreen().availableGeometry()
            self.adjustSize()
            self.move(screen.right() - self.width() - 20, screen.top() + 40)

    def set_opacity(self, value: float):
        self._opacity = max(0.2, min(1.0, value))
        self._apply_fonts()
        self.update()

    def set_font_size(self, size: int):
        self._font_size = size
        self._apply_fonts()
        self.adjustSize()


# ---------------------------------------------------------------------------
# Settings dialog (launched from tray right-click or main window)
# ---------------------------------------------------------------------------

class DesktopIntegrationSettings(QDialog):
    def __init__(self, tray: 'TrayApplet', widget: Optional['DesktopWidget'], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Desktop Integration Settings")
        self._tray = tray
        self._widget = widget

        layout = QFormLayout(self)

        self._widget_cb = QCheckBox("Show desktop background widget")
        self._widget_cb.setChecked(widget is not None and widget.isVisible())
        self._widget_cb.toggled.connect(self._toggle_widget)
        layout.addRow(self._widget_cb)

        if widget:
            self._opacity_slider = QSlider(Qt.Horizontal)
            self._opacity_slider.setRange(20, 100)
            self._opacity_slider.setValue(int(widget._opacity * 100))
            self._opacity_slider.valueChanged.connect(
                lambda v: widget.set_opacity(v / 100))
            layout.addRow("Widget opacity:", self._opacity_slider)

            self._font_slider = QSlider(Qt.Horizontal)
            self._font_slider.setRange(9, 20)
            self._font_slider.setValue(widget._font_size)
            self._font_slider.valueChanged.connect(widget.set_font_size)
            layout.addRow("Font size:", self._font_slider)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.accept)
        layout.addRow(btns)

    def _toggle_widget(self, checked: bool):
        if self._widget:
            if checked:
                self._widget.show()
            else:
                self._widget.hide()


# ---------------------------------------------------------------------------
# Controller — owns both tray and desktop widget, receives metrics pushes
# ---------------------------------------------------------------------------

class DesktopIntegrationController(QObject):
    """Thin orchestrator; wire into main.py after tabs are created."""

    def __init__(self, registry=None, parent=None):
        super().__init__(parent)
        self._registry = registry
        self._tray: Optional[TrayApplet] = None
        self._desktop_widget: Optional[DesktopWidget] = None
        self._source_label = "Local"

    def start(self, enable_tray: bool = True, enable_desktop_widget: bool = False):
        if enable_tray and QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = TrayApplet(registry=self._registry, parent=self)
            self._tray.quit_requested.connect(QApplication.quit)
        else:
            logger.info("System tray not available — skipping tray applet")

        if enable_desktop_widget:
            self._desktop_widget = DesktopWidget()

    @Slot(dict)
    def on_metrics(self, data: dict):
        """Call this from DashboardTab's metrics_ready signal (or a bridge timer)."""
        if self._tray:
            self._tray.push_metrics(data, self._source_label)
        if self._desktop_widget and self._desktop_widget.isVisible():
            self._desktop_widget.update_metrics(data, self._source_label)

    def set_source_label(self, label: str):
        self._source_label = label

    def show_settings(self, parent=None):
        if self._tray:
            dlg = DesktopIntegrationSettings(self._tray, self._desktop_widget, parent)
            dlg.exec()

    @property
    def tray(self) -> Optional[TrayApplet]:
        return self._tray

    @property
    def desktop_widget(self) -> Optional[DesktopWidget]:
        return self._desktop_widget
