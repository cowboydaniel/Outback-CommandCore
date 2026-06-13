from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTabWidget,
                             QHBoxLayout, QFormLayout, QSplitter)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QSplineSeries, QValueAxis
from PySide6.QtCore import Qt, QTimer, QMargins, QObject, QThread, Signal, Slot
from PySide6.QtGui import QPainter, QColor, QPen
import psutil
import platform
from datetime import datetime

logger = __import__('logging').getLogger(__name__)


# ---------------------------------------------------------------------------
# Background metrics collector
# ---------------------------------------------------------------------------

class PerfMetricsCollector(QObject):
    """All psutil calls for Performance Analytics — runs in a background QThread."""
    metrics_ready = Signal(dict)

    def __init__(self):
        super().__init__()
        self._timer = None
        self._last_disk_io = None
        self._last_net_io  = None
        self._last_io_time = None

    @Slot()
    def start(self):
        try:
            self._last_disk_io = psutil.disk_io_counters()
            self._last_net_io  = psutil.net_io_counters()
        except Exception:
            pass
        self._last_io_time = datetime.now()
        self._timer = QTimer()
        self._timer.timeout.connect(self._collect)
        self._timer.start(1000)
        self._collect()

    def stop(self):
        if self._timer:
            self._timer.stop()

    @Slot()
    def _collect(self):
        try:
            m = {}

            # --- CPU ---
            m['cpu_per_core']      = psutil.cpu_percent(percpu=True)
            m['cpu_freq']          = psutil.cpu_freq()
            m['cpu_count_logical'] = psutil.cpu_count(logical=True)
            m['cpu_count_phys']    = psutil.cpu_count(logical=False)
            try:
                m['load_avg'] = [x * 100 for x in psutil.getloadavg()]
            except Exception:
                m['load_avg'] = [0.0, 0.0, 0.0]

            # --- Memory ---
            vm = psutil.virtual_memory()
            sw = psutil.swap_memory()
            m['mem_percent']   = vm.percent
            m['mem_total']     = vm.total
            m['mem_available'] = vm.available
            m['mem_used']      = vm.used
            m['swap_total']    = sw.total
            m['swap_used']     = sw.used
            m['swap_percent']  = sw.percent

            # --- Disk ---
            disk = psutil.disk_usage('/')
            m['disk_total']   = disk.total
            m['disk_used']    = disk.used
            m['disk_free']    = disk.free
            m['disk_percent'] = disk.percent

            now = datetime.now()
            time_diff = max(0.001, (now - self._last_io_time).total_seconds()) if self._last_io_time else 1.0

            cur_disk = psutil.disk_io_counters()
            if self._last_disk_io and cur_disk:
                m['disk_read_kbps']  = max(0.0, (cur_disk.read_bytes  - self._last_disk_io.read_bytes)  / 1024 / time_diff)
                m['disk_write_kbps'] = max(0.0, (cur_disk.write_bytes - self._last_disk_io.write_bytes) / 1024 / time_diff)
            else:
                m['disk_read_kbps'] = m['disk_write_kbps'] = 0.0
            self._last_disk_io = cur_disk

            # --- Network ---
            cur_net = psutil.net_io_counters()
            if self._last_net_io and cur_net:
                m['net_sent_kbps']  = max(0.0, (cur_net.bytes_sent - self._last_net_io.bytes_sent) / 1024 / time_diff)
                m['net_recv_kbps']  = max(0.0, (cur_net.bytes_recv - self._last_net_io.bytes_recv) / 1024 / time_diff)
                m['net_total_sent'] = cur_net.bytes_sent
                m['net_total_recv'] = cur_net.bytes_recv
            else:
                m['net_sent_kbps'] = m['net_recv_kbps'] = 0.0
                m['net_total_sent'] = m['net_total_recv'] = 0
            self._last_net_io  = cur_net
            self._last_io_time = now

            try:
                conns = psutil.net_connections(kind='inet')
                m['net_connections'] = len([c for c in conns if c.status == 'ESTABLISHED'])
            except Exception:
                m['net_connections'] = None

            self.metrics_ready.emit(m)
        except Exception as exc:
            logger.exception("PerfMetricsCollector error: %s", exc)


# ---------------------------------------------------------------------------
# Tab
# ---------------------------------------------------------------------------

class PerformanceAnalyticsTab(QWidget):
    """Performance Analytics tab — CPU, Memory, Disk I/O, Network."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_points = 60
        self.time_range  = 5        # minutes shown
        self.prediction_steps  = 30
        self.prediction_window = 10
        self._latest: dict = {}
        self.setup_ui()
        self._start_collector()

    # ------------------------------------------------------------------
    # Collector
    # ------------------------------------------------------------------

    def _start_collector(self):
        self._thread    = QThread()
        self._collector = PerfMetricsCollector()
        self._collector.moveToThread(self._thread)
        self._thread.started.connect(self._collector.start)
        self._collector.metrics_ready.connect(self._on_metrics)
        self._thread.start()

        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._refresh_charts)
        self._ui_timer.start(1000)

    def start_data_collection(self):
        """Called by main.py after tab creation — collector already running."""
        pass

    @Slot(dict)
    def _on_metrics(self, m: dict):
        self._latest = m

    def closeEvent(self, event):
        self._collector.stop()
        self._thread.quit()
        self._thread.wait(2000)
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.cpu_tab     = QWidget()
        self.memory_tab  = QWidget()
        self.disk_tab    = QWidget()
        self.network_tab = QWidget()

        self.tabs.addTab(self.cpu_tab,     "CPU")
        self.tabs.addTab(self.memory_tab,  "Memory")
        self.tabs.addTab(self.disk_tab,    "Disk I/O")
        self.tabs.addTab(self.network_tab, "Network")

        self.setup_cpu_tab()
        self.setup_memory_tab()
        self.setup_disk_tab()
        self.setup_network_tab()

        layout.addWidget(self.tabs)
        self.setMinimumSize(800, 600)

    # ------------------------------------------------------------------
    # Chart factory
    # ------------------------------------------------------------------

    def _make_chart(self, title, y_title, y_range=(0, 100)):
        """Create a reversed-axis chart (past on right, future/prediction on left)."""
        chart = QChart()
        chart.setTitle(title)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setTheme(QChart.ChartThemeDark)
        chart.setBackgroundBrush(QColor(45, 45, 45))
        chart.setTitleBrush(Qt.white)
        chart.legend().setLabelColor(Qt.white)
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.layout().setContentsMargins(5, 5, 5, 5)

        ax = QValueAxis()
        ax.setTitleText("Time (seconds)")
        ax.setRange(-30, 300)
        ax.setReverse(True)   # newest (0) on left, oldest (300) right, future (-30) far left
        ax.setTickCount(6)
        ax.setTitleBrush(Qt.white)
        ax.setLabelsBrush(Qt.white)
        ax.setGridLineColor(QColor(100, 100, 100))
        ax.setLinePenColor(QColor(180, 180, 180))

        ay = QValueAxis()
        ay.setTitleText(y_title)
        ay.setRange(*y_range)
        ay.setTickCount(6)
        ay.setTitleBrush(Qt.white)
        ay.setLabelsBrush(Qt.white)
        ay.setGridLineColor(QColor(100, 100, 100))
        ay.setLinePenColor(QColor(180, 180, 180))

        chart.addAxis(ax, Qt.AlignBottom)
        chart.addAxis(ay, Qt.AlignLeft)

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(250)
        view.setBackgroundBrush(QColor(30, 30, 30))
        view.setStyleSheet("border: none; background: transparent;")
        view.setContentsMargins(0, 0, 0, 0)
        view.setViewportMargins(0, 0, 0, 0)

        return chart, view, ax, ay

    @staticmethod
    def _divider_pen():
        p = QPen(QColor(255, 255, 255, 150))
        p.setWidth(1)
        p.setStyle(Qt.DotLine)
        return p

    @staticmethod
    def _pred_pen(color):
        p = QPen(color)
        p.setWidth(2)
        p.setStyle(Qt.DashDotLine)
        return p

    def _attach(self, chart, series, ax, ay):
        chart.addSeries(series)
        series.attachAxis(ax)
        series.attachAxis(ay)

    # ------------------------------------------------------------------
    # CPU tab
    # ------------------------------------------------------------------

    def setup_cpu_tab(self):
        layout = QVBoxLayout(self.cpu_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)

        info = QLabel(f"CPU: {platform.processor() or 'Unknown'}")
        info.setStyleSheet("font-weight: bold; font-size: 11px;")
        top_layout.addWidget(info)

        self.cpu_chart, self.cpu_chart_view, self.cpu_ax, self.cpu_ay = self._make_chart(
            "CPU Usage Over Time", "Usage (%)")
        self.cpu_chart.setMargins(QMargins(0, 0, 0, 0))
        self.cpu_chart.layout().setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(self.cpu_chart_view, 1)

        # Divider
        self.cpu_divider = QLineSeries()
        self.cpu_divider.setName("Now")
        self.cpu_divider.setPen(self._divider_pen())
        self.cpu_divider.append(0, 0)
        self.cpu_divider.append(0, 100)
        self._attach(self.cpu_chart, self.cpu_divider, self.cpu_ax, self.cpu_ay)

        # Prediction series
        self.cpu_pred_series = QSplineSeries()
        self.cpu_pred_series.setName("Predicted")
        self.cpu_pred_series.setPen(self._pred_pen(QColor(255, 100, 100)))
        self._attach(self.cpu_chart, self.cpu_pred_series, self.cpu_ax, self.cpu_ay)

        # Avg series (created once — per-core series added on first update)
        self.avg_series = QSplineSeries()
        self.avg_series.setName("Avg")
        avg_pen = QPen(Qt.white)
        avg_pen.setWidth(2)
        avg_pen.setStyle(Qt.DashLine)
        self.avg_series.setPen(avg_pen)
        self._attach(self.cpu_chart, self.avg_series, self.cpu_ax, self.cpu_ay)

        # Stats labels
        metrics = QWidget()
        form = QFormLayout(metrics)
        form.setContentsMargins(10, 5, 10, 5)
        self.cpu_usage_label = QLabel()
        self.cpu_cores_label = QLabel()
        self.cpu_freq_label  = QLabel()
        self.cpu_load_label  = QLabel()
        form.addRow("<b>CPU Usage:</b>",      self.cpu_usage_label)
        form.addRow("<b>CPU Cores:</b>",      self.cpu_cores_label)
        form.addRow("<b>CPU Frequency:</b>",  self.cpu_freq_label)
        form.addRow("<b>Load Average:</b>",   self.cpu_load_label)

        layout.addWidget(top, 1)
        layout.addWidget(metrics, 1)

        # Data buffers — index 0 = newest
        self._cpu_count = psutil.cpu_count() or 1
        self.cpu_data     = [[0.0] * self.data_points for _ in range(self._cpu_count)]
        self.avg_cpu_data = [0.0] * self.data_points
        self.cpu_series   = []  # per-core series, created on first update

        # Color palette (golden-ratio hue spread)
        gr = 0.618033988749895
        hue = 0.3
        self._core_colors = []
        for _ in range(max(128, self._cpu_count)):
            hue = (hue + gr) % 1.0
            self._core_colors.append(QColor.fromHsvF(hue, 0.9, 0.9))

    def _ensure_cpu_series(self, cpu_count: int):
        """Create per-core series the first time (or if core count changed)."""
        if len(self.cpu_series) == cpu_count:
            return
        for s in self.cpu_series:
            self.cpu_chart.removeSeries(s)
        self.cpu_series = []
        # Expand data buffers if needed
        while len(self.cpu_data) < cpu_count:
            self.cpu_data.append([0.0] * self.data_points)
        for core in range(cpu_count):
            s = QSplineSeries()
            s.setName(f"Core {core + 1}")
            pen = QPen(self._core_colors[core % len(self._core_colors)])
            pen.setWidthF(1.5)
            s.setPen(pen)
            self._attach(self.cpu_chart, s, self.cpu_ax, self.cpu_ay)
            self.cpu_series.append(s)

    def _update_cpu(self, m: dict):
        cpu_percent = m.get('cpu_per_core', [])
        if not cpu_percent:
            return
        cpu_count = len(cpu_percent)
        self._ensure_cpu_series(cpu_count)

        avg = sum(cpu_percent) / cpu_count
        freq = m.get('cpu_freq')
        load = m.get('load_avg', [0, 0, 0])

        self.cpu_usage_label.setText(f"{avg:.1f}%")
        self.cpu_cores_label.setText(f"{cpu_count} (Physical: {m.get('cpu_count_phys', '?')})")
        if freq:
            self.cpu_freq_label.setText(f"{freq.current/1000:.2f} GHz  (max {freq.max/1000:.2f} GHz)")
        self.cpu_load_label.setText(f"{load[0]:.1f}% / {load[1]:.1f}% / {load[2]:.1f}%")

        ti = (self.time_range * 60) / (self.data_points - 1)

        # Shift and insert newest at 0
        self.avg_cpu_data.pop()
        self.avg_cpu_data.insert(0, avg)

        self.avg_series.clear()
        for i, v in enumerate(self.avg_cpu_data):
            self.avg_series.append(i * ti, v)

        for core in range(cpu_count):
            self.cpu_data[core].pop()
            self.cpu_data[core].insert(0, cpu_percent[core])
            self.cpu_series[core].clear()
            for i, v in enumerate(self.cpu_data[core]):
                self.cpu_series[core].append(i * ti, v)

        if self.prediction_window <= len(self.avg_cpu_data):
            self._update_prediction(
                self.avg_cpu_data, self.cpu_pred_series,
                alpha=0.4, beta=0.2, phi=0.85, max_step_range=(1.5, 8.0), clamp=(0, 100))

    # ------------------------------------------------------------------
    # Memory tab
    # ------------------------------------------------------------------

    def setup_memory_tab(self):
        layout = QVBoxLayout(self.memory_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(QLabel("Memory Usage"))

        self.mem_chart, self.mem_chart_view, self.mem_ax, self.mem_ay = self._make_chart(
            "Memory Usage Over Time", "Usage (%)")
        self.mem_chart.setMargins(QMargins(0, 0, 0, 0))
        self.mem_chart.layout().setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(self.mem_chart_view, 1)

        # Divider
        self.mem_divider = QLineSeries()
        self.mem_divider.setName("Now")
        self.mem_divider.setPen(self._divider_pen())
        self.mem_divider.append(0, 0)
        self.mem_divider.append(0, 100)
        self._attach(self.mem_chart, self.mem_divider, self.mem_ax, self.mem_ay)

        def _mseries(name, color):
            s = QSplineSeries()
            s.setName(name)
            s.setPen(QPen(QColor(color), 2))
            self._attach(self.mem_chart, s, self.mem_ax, self.mem_ay)
            return s

        self.mem_series          = _mseries("Memory (%)",        "#32cd32")
        self.mem_available_series = _mseries("Available (%)",    "#4682b4")
        self.mem_used_series      = _mseries("Used (%)",         "#ff8c00")
        self.swap_used_series     = _mseries("Swap Used (%)",    "#dc143c")
        self.swap_percent_series  = _mseries("Swap Usage (%)",   "#ffd700")
        self.mem_pred_series      = QSplineSeries()
        self.mem_pred_series.setName("Predicted")
        self.mem_pred_series.setPen(self._pred_pen(QColor(255, 100, 100)))
        self._attach(self.mem_chart, self.mem_pred_series, self.mem_ax, self.mem_ay)

        metrics = QWidget()
        form = QFormLayout(metrics)
        form.setContentsMargins(10, 5, 10, 5)
        self.total_mem_label     = QLabel()
        self.available_mem_label = QLabel()
        self.used_mem_label      = QLabel()
        self.mem_percent_label   = QLabel()
        self.swap_total_label    = QLabel()
        self.swap_used_label     = QLabel()
        self.swap_percent_label  = QLabel()
        form.addRow("<b>Memory Total:</b>",     self.total_mem_label)
        form.addRow("<b>Memory Available:</b>", self.available_mem_label)
        form.addRow("<b>Memory Used:</b>",      self.used_mem_label)
        form.addRow("<b>Memory Usage %:</b>",   self.mem_percent_label)
        form.addRow("<b>Swap Total:</b>",        self.swap_total_label)
        form.addRow("<b>Swap Used:</b>",         self.swap_used_label)
        form.addRow("<b>Swap Usage %:</b>",      self.swap_percent_label)

        layout.addWidget(top, 1)
        layout.addWidget(metrics, 1)

        # Data buffers — index 0 = newest
        self.mem_data            = [0.0] * self.data_points
        self.mem_available_data  = [0.0] * self.data_points
        self.mem_used_data       = [0.0] * self.data_points
        self.swap_used_data      = [0.0] * self.data_points
        self.swap_percent_data   = [0.0] * self.data_points

    def _update_memory(self, m: dict):
        mem_pct  = m.get('mem_percent',   0)
        mem_tot  = m.get('mem_total',     1)
        mem_avail= m.get('mem_available', 0)
        mem_used = m.get('mem_used',      0)
        sw_tot   = m.get('swap_total',    0)
        sw_used  = m.get('swap_used',     0)
        sw_pct   = m.get('swap_percent',  0)

        def _fmt(b):
            for u in ['B','KB','MB','GB','TB']:
                if b < 1024: return f"{b:.1f} {u}"
                b /= 1024
            return f"{b:.1f} PB"

        self.total_mem_label.setText(_fmt(mem_tot))
        self.available_mem_label.setText(_fmt(mem_avail))
        self.used_mem_label.setText(_fmt(mem_used))
        self.mem_percent_label.setText(f"{mem_pct:.1f}%")
        self.swap_total_label.setText(_fmt(sw_tot))
        self.swap_used_label.setText(_fmt(sw_used))
        self.swap_percent_label.setText(f"{sw_pct:.1f}%")

        avail_pct = mem_avail * 100 / mem_tot if mem_tot else 0
        used_pct  = mem_used  * 100 / mem_tot if mem_tot else 0
        swap_used_pct = sw_used * 100 / sw_tot if sw_tot else 0

        for buf, val in [
            (self.mem_data,           mem_pct),
            (self.mem_available_data, avail_pct),
            (self.mem_used_data,      used_pct),
            (self.swap_used_data,     swap_used_pct),
            (self.swap_percent_data,  sw_pct),
        ]:
            buf.pop(); buf.insert(0, val)

        ti = (self.time_range * 60) / (self.data_points - 1)
        for series, buf in [
            (self.mem_series,           self.mem_data),
            (self.mem_available_series, self.mem_available_data),
            (self.mem_used_series,      self.mem_used_data),
            (self.swap_used_series,     self.swap_used_data),
            (self.swap_percent_series,  self.swap_percent_data),
        ]:
            series.clear()
            for i, v in enumerate(buf):
                series.append(i * ti, v)

        if self.prediction_window <= len(self.mem_data):
            self._update_prediction(
                self.mem_data, self.mem_pred_series,
                alpha=0.3, beta=0.1, phi=0.7, max_step_range=(0.5, 4.0), clamp=(0, 100))

    # ------------------------------------------------------------------
    # Disk I/O tab
    # ------------------------------------------------------------------

    def setup_disk_tab(self):
        splitter = QSplitter(Qt.Vertical)

        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.addWidget(QLabel("Disk I/O"))

        self.disk_chart, self.disk_chart_view, self.disk_ax, self.disk_ay = self._make_chart(
            "Disk I/O Over Time", "KB/s", (0, 1024))
        chart_layout.addWidget(self.disk_chart_view, 1)

        def _dseries(name, color):
            s = QSplineSeries()
            s.setName(name)
            s.setPen(QPen(QColor(color), 2))
            self._attach(self.disk_chart, s, self.disk_ax, self.disk_ay)
            return s

        self.disk_read_series  = _dseries("Read (KB/s)",  "#ff8c00")
        self.disk_write_series = _dseries("Write (KB/s)", "#ff4500")
        self.disk_read_pred    = QSplineSeries()
        self.disk_read_pred.setName("Read (Predicted)")
        self.disk_read_pred.setPen(self._pred_pen(QColor(255, 200, 120)))
        self._attach(self.disk_chart, self.disk_read_pred, self.disk_ax, self.disk_ay)
        self.disk_write_pred = QSplineSeries()
        self.disk_write_pred.setName("Write (Predicted)")
        self.disk_write_pred.setPen(self._pred_pen(QColor(255, 140, 120)))
        self._attach(self.disk_chart, self.disk_write_pred, self.disk_ax, self.disk_ay)
        self.disk_divider = QLineSeries()
        self.disk_divider.setName("Now")
        self.disk_divider.setPen(self._divider_pen())
        self.disk_divider.append(0, 0)
        self.disk_divider.append(0, 1024)
        self._attach(self.disk_chart, self.disk_divider, self.disk_ax, self.disk_ay)

        metrics = QWidget()
        form = QFormLayout(metrics)
        form.setContentsMargins(10, 5, 10, 5)
        self.disk_total_label  = QLabel()
        self.disk_used_label   = QLabel()
        self.disk_free_label   = QLabel()
        self.disk_pct_label    = QLabel()
        self.disk_read_label   = QLabel()
        self.disk_write_label  = QLabel()
        form.addRow("<b>Total Space:</b>",  self.disk_total_label)
        form.addRow("<b>Used Space:</b>",   self.disk_used_label)
        form.addRow("<b>Free Space:</b>",   self.disk_free_label)
        form.addRow("<b>Usage %:</b>",      self.disk_pct_label)
        form.addRow("<b>Read Speed:</b>",   self.disk_read_label)
        form.addRow("<b>Write Speed:</b>",  self.disk_write_label)

        splitter.addWidget(chart_widget)
        splitter.addWidget(metrics)
        splitter.setSizes([400, 200])

        tab_layout = QVBoxLayout(self.disk_tab)
        tab_layout.setContentsMargins(5, 5, 5, 5)
        tab_layout.addWidget(splitter)

        # Data buffers — index 0 = newest
        self.disk_read_data  = [0.0] * self.data_points
        self.disk_write_data = [0.0] * self.data_points

    def _update_disk(self, m: dict):
        def _fmt(b):
            for u in ['B','KB','MB','GB','TB']:
                if b < 1024: return f"{b:.1f} {u}"
                b /= 1024
            return f"{b:.1f} PB"

        self.disk_total_label.setText(_fmt(m.get('disk_total', 0)))
        self.disk_used_label.setText(_fmt(m.get('disk_used',  0)))
        self.disk_free_label.setText(_fmt(m.get('disk_free',  0)))
        self.disk_pct_label.setText(f"{m.get('disk_percent', 0):.1f}%")

        r = m.get('disk_read_kbps',  0.0)
        w = m.get('disk_write_kbps', 0.0)
        self.disk_read_label.setText(f"{r:.1f} KB/s")
        self.disk_write_label.setText(f"{w:.1f} KB/s")

        self.disk_read_data.pop();  self.disk_read_data.insert(0, r)
        self.disk_write_data.pop(); self.disk_write_data.insert(0, w)

        max_io = max(max(self.disk_read_data + self.disk_write_data) * 1.1, 10)
        self.disk_ay.setRange(0, max_io)
        self.disk_divider.clear()
        self.disk_divider.append(0, 0)
        self.disk_divider.append(0, max_io)

        ti = (self.time_range * 60) / (self.data_points - 1)
        self.disk_read_series.clear()
        self.disk_write_series.clear()
        for i in range(self.data_points):
            self.disk_read_series.append(i * ti, self.disk_read_data[i])
            self.disk_write_series.append(i * ti, self.disk_write_data[i])

        if len(self.disk_read_data) >= 2:
            self._update_prediction(self.disk_read_data, self.disk_read_pred,
                alpha=0.35, beta=0.15, phi=0.8, max_step_range=(5.0, 200.0))
            self._update_prediction(self.disk_write_data, self.disk_write_pred,
                alpha=0.35, beta=0.15, phi=0.8, max_step_range=(5.0, 200.0))

    # ------------------------------------------------------------------
    # Network tab
    # ------------------------------------------------------------------

    def setup_network_tab(self):
        splitter = QSplitter(Qt.Vertical)

        self.net_chart, self.net_chart_view, self.net_ax, self.net_ay = self._make_chart(
            "Network I/O (KB/s)", "KB/s", (0, 1024))

        def _nseries(name, color):
            s = QSplineSeries()
            s.setName(name)
            s.setPen(QPen(QColor(color), 2))
            self._attach(self.net_chart, s, self.net_ax, self.net_ay)
            return s

        self.net_sent_series = _nseries("Sent",     "#ff6347")
        self.net_recv_series = _nseries("Received", "#6495ed")
        self.net_sent_pred   = QSplineSeries()
        self.net_sent_pred.setName("Sent (Predicted)")
        self.net_sent_pred.setPen(self._pred_pen(QColor(255, 160, 140)))
        self._attach(self.net_chart, self.net_sent_pred, self.net_ax, self.net_ay)
        self.net_recv_pred = QSplineSeries()
        self.net_recv_pred.setName("Received (Predicted)")
        self.net_recv_pred.setPen(self._pred_pen(QColor(140, 180, 255)))
        self._attach(self.net_chart, self.net_recv_pred, self.net_ax, self.net_ay)
        self.net_divider = QLineSeries()
        self.net_divider.setName("Now")
        self.net_divider.setPen(self._divider_pen())
        self.net_divider.append(0, 0)
        self.net_divider.append(0, 1024)
        self._attach(self.net_chart, self.net_divider, self.net_ax, self.net_ay)

        stats = QWidget()
        form = QFormLayout(stats)
        form.setContentsMargins(10, 5, 10, 5)
        self.net_sent_label      = QLabel("0 B")
        self.net_recv_label      = QLabel("0 B")
        self.net_sent_rate_label = QLabel("0 KB/s")
        self.net_recv_rate_label = QLabel("0 KB/s")
        self.net_connections_label = QLabel("—")
        form.addRow("Data Sent:",          self.net_sent_label)
        form.addRow("Data Received:",      self.net_recv_label)
        form.addRow("Send Rate:",          self.net_sent_rate_label)
        form.addRow("Receive Rate:",       self.net_recv_rate_label)
        form.addRow("Active Connections:", self.net_connections_label)

        splitter.addWidget(self.net_chart_view)
        splitter.addWidget(stats)
        splitter.setSizes([400, 200])

        tab_layout = QVBoxLayout(self.network_tab)
        tab_layout.setContentsMargins(5, 5, 5, 5)
        tab_layout.addWidget(splitter)

        # Data buffers — index 0 = newest
        self.net_sent_data = [0.0] * self.data_points
        self.net_recv_data = [0.0] * self.data_points

    def _update_network(self, m: dict):
        def _fmt(b):
            for u in ['B','KB','MB','GB','TB']:
                if b < 1024: return f"{b:.1f} {u}"
                b /= 1024
            return f"{b:.1f} PB"

        self.net_sent_label.setText(_fmt(m.get('net_total_sent', 0)))
        self.net_recv_label.setText(_fmt(m.get('net_total_recv', 0)))

        s = m.get('net_sent_kbps', 0.0)
        r = m.get('net_recv_kbps', 0.0)
        self.net_sent_rate_label.setText(f"{s:.1f} KB/s")
        self.net_recv_rate_label.setText(f"{r:.1f} KB/s")

        conns = m.get('net_connections')
        self.net_connections_label.setText(f"{conns} established" if conns is not None else "N/A")

        self.net_sent_data.pop(); self.net_sent_data.insert(0, s)
        self.net_recv_data.pop(); self.net_recv_data.insert(0, r)

        max_net = max(max(self.net_sent_data + self.net_recv_data) * 1.1, 10)
        self.net_ay.setRange(0, max_net)
        self.net_divider.clear()
        self.net_divider.append(0, 0)
        self.net_divider.append(0, max_net)

        ti = (self.time_range * 60) / (self.data_points - 1)
        self.net_sent_series.clear()
        self.net_recv_series.clear()
        for i in range(self.data_points):
            self.net_sent_series.append(i * ti, self.net_sent_data[i])
            self.net_recv_series.append(i * ti, self.net_recv_data[i])

        if len(self.net_sent_data) >= 2:
            self._update_prediction(self.net_sent_data, self.net_sent_pred,
                alpha=0.35, beta=0.15, phi=0.8, max_step_range=(5.0, 200.0))
            self._update_prediction(self.net_recv_data, self.net_recv_pred,
                alpha=0.35, beta=0.15, phi=0.8, max_step_range=(5.0, 200.0))

    # ------------------------------------------------------------------
    # Shared prediction engine (Holt's damped linear trend)
    # ------------------------------------------------------------------

    def _update_prediction(self, data: list, series: QSplineSeries, *,
                            alpha: float, beta: float, phi: float,
                            max_step_range: tuple,
                            clamp: tuple | None = None):
        window = data[:self.prediction_window]
        if len(window) < 2:
            return

        chronological = list(reversed(window))
        level = chronological[0]
        trend = chronological[1] - chronological[0]
        for v in chronological[1:]:
            prev = level
            level = alpha * v + (1 - alpha) * (level + trend)
            trend = beta * (level - prev) + (1 - beta) * trend

        deltas = [abs(b - a) for a, b in zip(chronological[:-1], chronological[1:])]
        avg_d = sum(deltas) / len(deltas) if deltas else 0
        max_step = max(max_step_range[0], min(max_step_range[1], avg_d * 1.5))

        series.clear()
        series.append(0, data[0])  # connect to "now"

        last_y = data[0]
        for i in range(1, self.prediction_steps + 1):
            if phi == 1:
                forecast = level + trend * i
            else:
                forecast = level + trend * (1 - phi ** i) / (1 - phi)

            delta = forecast - last_y
            if abs(delta) > max_step:
                forecast = last_y + max_step * (1 if delta > 0 else -1)

            if clamp:
                forecast = max(clamp[0], min(clamp[1], forecast))
            else:
                forecast = max(0, forecast)

            time_point = -i * (30.0 / self.prediction_steps)
            series.append(time_point, forecast)
            last_y = forecast

    # ------------------------------------------------------------------
    # Main refresh (called by UI timer every second)
    # ------------------------------------------------------------------

    def _refresh_charts(self):
        m = self._latest
        if not m:
            return
        self._update_cpu(m)
        self._update_memory(m)
        self._update_disk(m)
        self._update_network(m)
