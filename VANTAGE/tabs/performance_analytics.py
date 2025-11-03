from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTabWidget, 
                             QHBoxLayout, QFormLayout, QSizePolicy, QSplitter, QFrame,
                             QGraphicsView)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QSplineSeries, QValueAxis, QBarSet, QBarSeries, QBarCategoryAxis
from PySide6.QtCore import Qt, QPointF, QTimer, QMargins
from PySide6.QtGui import QPainter, QColor, QFont, QPen
import psutil
import platform
import math
from datetime import datetime, timedelta

class PerformanceAnalyticsTab(QWidget):
    """Performance Analytics tab that displays system performance metrics with multiple subtabs."""
    
    def __init__(self, parent=None):
        """Initialize the performance analytics tab with multiple subtabs."""
        super().__init__(parent)
        self.data_points = 60  # Number of data points to display
        self.time_range = 5  # Minutes to display
        self.setup_ui()
        self.setup_timers()
    
    def setup_ui(self):
        """Set up the user interface with tabs for different metrics."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        
        # Add tabs
        self.cpu_tab = QWidget()
        self.memory_tab = QWidget()
        self.disk_tab = QWidget()
        self.network_tab = QWidget()
        
        self.tabs.addTab(self.cpu_tab, "CPU")
        self.tabs.addTab(self.memory_tab, "Memory")
        self.tabs.addTab(self.disk_tab, "Disk I/O")
        self.tabs.addTab(self.network_tab, "Network")
        
        # Setup each tab
        self.setup_cpu_tab()
        self.setup_memory_tab()
        self.setup_disk_tab()
        self.setup_network_tab()
        
        # Add tabs to layout
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        # Set minimum sizes for better layout
        self.setMinimumSize(800, 600)
    
    def setup_timers(self):
        """Setup timers for updating the charts."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_charts)
        self.update_timer.start(1000)  # Update every second
    
    def update_charts(self):
        """Update all charts with fresh data."""
        self.update_cpu_chart()
        self.update_memory_chart()
        self.update_disk_chart()
        self.update_network_chart()
    
    def create_chart(self, title, y_title, y_range=(0, 100)):
        """Create a base chart with common settings."""
        chart = QChart()
        chart.setTitle(title)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # Apply dark theme
        chart.setTheme(QChart.ChartThemeDark)
        chart.setBackgroundBrush(QColor(45, 45, 45))
        chart.setTitleBrush(Qt.white)
        chart.legend().setLabelColor(Qt.white)
        
        # Create axes with improved styling
        axis_x = QValueAxis()
        axis_x.setTitleText("Time (seconds)")
        # Set range to show past (positive) and future (negative) times
        # -30s to 300s to show 30 seconds into future and 300s (5min) into past
        axis_x.setRange(-30, 300)
        axis_x.setReverse(True)  # Show past on right, future on left
        axis_x.setTickCount(6)
        axis_x.setTitleBrush(Qt.white)
        axis_x.setLabelsBrush(Qt.white)
        axis_x.setGridLineColor(QColor(100, 100, 100))
        axis_x.setLinePenColor(QColor(180, 180, 180))
        
        axis_y = QValueAxis()
        axis_y.setTitleText(y_title)
        axis_y.setRange(*y_range)
        axis_y.setTickCount(6)
        axis_y.setTitleBrush(Qt.white)
        axis_y.setLabelsBrush(Qt.white)
        axis_y.setGridLineColor(QColor(100, 100, 100))
        axis_y.setLinePenColor(QColor(180, 180, 180))
        
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(250)
        
        # Set margins to make room for labels
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.layout().setContentsMargins(5, 5, 5, 5)
        
        return chart, chart_view, axis_x, axis_y
    
    def setup_cpu_tab(self):
        """Setup CPU tab with CPU usage chart and stats."""
        # Main vertical layout
        main_layout = QVBoxLayout(self.cpu_tab)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create a container for the top half (charts)
        top_half = QWidget()
        top_layout = QHBoxLayout(top_half)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)  # Remove spacing between graphs
        
        # CPU chart container
        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # CPU info
        cpu_info = f"CPU: {platform.processor() or 'Unknown'}"
        cpu_info_label = QLabel(cpu_info)
        cpu_info_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        chart_layout.addWidget(cpu_info_label)
        
        # Create CPU chart - full width
        self.cpu_chart, self.cpu_chart_view, self.cpu_axis_x, self.cpu_axis_y = self.create_chart(
            "CPU Usage Over Time", "Usage (%)")
        
        # Remove margins for clean look
        self.cpu_chart.setMargins(QMargins(0, 0, 0, 0))
        self.cpu_chart.layout().setContentsMargins(0, 0, 0, 0)
        self.cpu_chart_view.setContentsMargins(0, 0, 0, 0)
        self.cpu_chart_view.setViewportMargins(0, 0, 0, 0)
        self.cpu_chart_view.setBackgroundBrush(QColor(30, 30, 30))
        self.cpu_chart_view.setStyleSheet("border: none; background: transparent;")
        
        # Add chart to layout with stretch
        chart_layout.addWidget(self.cpu_chart_view, 1)
        
        # Add chart container to top layout with full width
        top_layout.addWidget(chart_container)
        
        # Ensure no spacing or margins between the charts
        top_layout.setSpacing(-1)  # Negative spacing to overlap borders
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create metrics container for bottom half (full width)
        metrics_container = QWidget()
        metrics_layout = QVBoxLayout(metrics_container)
        metrics_layout.setContentsMargins(10, 5, 10, 5)
        
        # CPU stats
        self.cpu_usage_label = QLabel()
        self.cpu_cores_label = QLabel()
        self.cpu_freq_label = QLabel()
        self.cpu_load_label = QLabel()
        
        # Create form layout for metrics
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addRow("<b>CPU Usage:</b>", self.cpu_usage_label)
        form_layout.addRow("<b>CPU Cores:</b>", self.cpu_cores_label)
        form_layout.addRow("<b>CPU Frequency:</b>", self.cpu_freq_label)
        form_layout.addRow("<b>Load Average:</b>", self.cpu_load_label)
        
        # Add form layout to metrics container
        metrics_layout.addLayout(form_layout)
        
        # Add both halves to main layout with equal stretch
        main_layout.addWidget(top_half, 1)  # Top half (chart) - 1/2 height
        main_layout.addWidget(metrics_container, 1)  # Bottom half (metrics) - 1/2 height
        
        # Set stretch factors for the main layout
        main_layout.setStretch(0, 1)  # Top half (chart) - 1/2 height
        main_layout.setStretch(1, 1)  # Bottom half (metrics) - 1/2 height
        
        # Initialize with zero values for each core and average
        self.cpu_count = psutil.cpu_count()
        self.cpu_data = [[0] * self.data_points for _ in range(self.cpu_count)]
        self.avg_cpu_data = [0] * self.data_points
        self.cpu_series = []  # Will store series for each core
        self.avg_series = None  # Will store the average series
        
        # Create prediction series
        self.prediction_series = QSplineSeries()
        self.prediction_series.setName("Predicted")
        pred_pen = QPen(QColor(255, 100, 100))  # Light red
        pred_pen.setWidth(2)
        pred_pen.setStyle(Qt.DashDotLine)
        self.prediction_series.setPen(pred_pen)
        
        # Add to chart
        self.cpu_chart.addSeries(self.prediction_series)
        self.prediction_series.attachAxis(self.cpu_axis_x)
        self.prediction_series.attachAxis(self.cpu_axis_y)
        
        # Add a vertical line at 0 to separate real data from predictions
        self.divider_line = QLineSeries()
        self.divider_line.setName("Now")
        divider_pen = QPen(QColor(255, 255, 255, 150))  # Semi-transparent white
        divider_pen.setWidth(1)
        divider_pen.setStyle(Qt.DotLine)
        self.divider_line.setPen(divider_pen)
        
        # Add points for the line (from bottom to top of chart)
        self.divider_line.append(0, 0)
        self.divider_line.append(0, 100)  # Will be clipped by axis range
        
        # Add to chart
        self.cpu_chart.addSeries(self.divider_line)
        self.divider_line.attachAxis(self.cpu_axis_x)
        self.divider_line.attachAxis(self.cpu_axis_y)
        
        # Prediction settings
        self.prediction_enabled = True
        self.prediction_steps = 30  # 30 points into future (one per second)
        self.prediction_window = 10  # Use last 10 points for calculation
        
        def generate_distinct_colors(n):
            """Generate n visually distinct colors using the golden ratio for hue distribution."""
            colors = []
            # Golden ratio conjugate
            golden_ratio_conjugate = 0.618033988749895
            # Start with a random hue between 0 and 1
            hue = 0.3  # Start with a nice blue-ish color
            
            for i in range(n):
                # Use golden ratio to get a well-distributed hue
                hue = (hue + golden_ratio_conjugate) % 1.0
                # Convert HSV to RGB (saturation and value both at 0.9 for bright but not neon colors)
                color = QColor.fromHsvF(hue, 0.9, 0.9)
                colors.append(color)
            
            return colors
            
        # Generate distinct colors for up to 128 cores (can handle more if needed)
        self.core_colors = generate_distinct_colors(128)
        
        # Ensure we have enough colors by cycling if needed
        if self.cpu_count > len(self.core_colors):
            self.core_colors = (self.core_colors * ((self.cpu_count // len(self.core_colors)) + 1))[:self.cpu_count]
        
        self.update_cpu_chart()
    
    def update_cpu_chart(self):
        """Update CPU chart with current CPU usage for all cores."""
        # Get per-CPU stats
        cpu_percent = psutil.cpu_percent(percpu=True)
        cpu_count = len(cpu_percent)
        cpu_freq = psutil.cpu_freq()
        load_avg = [x * 100 for x in psutil.getloadavg()]  # Convert to percentage of all cores
        
        # Calculate average CPU usage
        avg_cpu = sum(cpu_percent) / cpu_count
        
        # Update labels
        self.cpu_usage_label.setText(f"<b>CPU Usage:</b> {avg_cpu:.1f}%")
        self.cpu_cores_label.setText(f"<b>Cores:</b> {cpu_count} (Physical: {psutil.cpu_count(logical=False)})")
        
        if cpu_freq is not None:
            self.cpu_freq_label.setText(f"<b>Frequency:</b> {cpu_freq.current/1000:.2f} GHz (Max: {cpu_freq.max/1000:.2f} GHz)")
        
        self.cpu_load_label.setText(
            f"<b>Load Average (1/5/15 min):</b> {load_avg[0]:.1f}% / {load_avg[1]:.1f}% / {load_avg[2]:.1f}%"
        )
        
        # Update data for each core and calculate average
        time_interval = (self.time_range * 60) / (self.data_points - 1)
        
        # Initialize series if not done yet
        if not self.cpu_series:
            # Clear any existing series
            for series in self.cpu_series:
                self.cpu_chart.removeSeries(series)
            if hasattr(self, 'avg_series') and self.avg_series:
                self.cpu_chart.removeSeries(self.avg_series)
            
            self.cpu_series = []
            
            # Create the average series (white dashed line)
            self.avg_series = QSplineSeries()
            self.avg_series.setName("Avg")
            avg_pen = QPen(Qt.white)
            avg_pen.setWidth(2)
            avg_pen.setStyle(Qt.DashLine)
            self.avg_series.setPen(avg_pen)
            
            # Add average series to chart
            self.cpu_chart.addSeries(self.avg_series)
            self.avg_series.attachAxis(self.cpu_axis_x)
            self.avg_series.attachAxis(self.cpu_axis_y)
            
            # Create a new series for each core
            for core in range(len(psutil.cpu_percent(percpu=True))):
                series = QSplineSeries()
                series.setName(f"Core {core + 1}")
                
                # Assign color from our palette
                color = self.core_colors[core % len(self.core_colors)]
                pen = QPen(color)
                pen.setWidth(1.5)  # Slightly thinner lines for better visibility
                series.setPen(pen)
                
                self.cpu_chart.addSeries(series)
                series.attachAxis(self.cpu_axis_x)
                series.attachAxis(self.cpu_axis_y)
                self.cpu_series.append(series)
        
        # Update average data
        for i in range(self.data_points - 1, 0, -1):
            self.avg_cpu_data[i] = self.avg_cpu_data[i-1]
        
        # Calculate and store new average
        current_avg = sum(cpu_percent) / cpu_count
        self.avg_cpu_data[0] = current_avg
        
        # Update average series (from 0 to 300 seconds in the past)
        self.avg_series.clear()
        for i, value in enumerate(self.avg_cpu_data):
            # Calculate time point (0 to 300 seconds in the past)
            time_point = i * (300.0 / (self.data_points - 1))
            self.avg_series.append(time_point, value)
            
        # Update prediction if enabled
        if self.prediction_enabled and len(self.avg_cpu_data) >= self.prediction_window:
            self.update_cpu_prediction()
        
        # Update data for each core
        for core in range(cpu_count):
            # Update data - add new point to the beginning
            self.cpu_data[core].pop()  # Remove the oldest point from the end
            self.cpu_data[core].insert(0, cpu_percent[core])  # Add new point to the beginning
            
            # Update series data
            self.cpu_series[core].clear()
            for i, value in enumerate(self.cpu_data[core]):
                time_point = i * time_interval
                self.cpu_series[core].append(time_point, value)
    
    def update_cpu_prediction(self):
        """
        Calculate and update CPU usage prediction with natural-looking fluctuations.
        Uses a combination of linear regression and noise to simulate realistic patterns.
        """
        # Get recent data points for prediction
        recent_data = self.avg_cpu_data[:self.prediction_window]
        
        if len(recent_data) < 2:  # Need at least 2 points for prediction
            return
            
        # Calculate the standard deviation of recent data for natural fluctuation
        mean = sum(recent_data) / len(recent_data)
        std_dev = (sum((x - mean) ** 2 for x in recent_data) / len(recent_data)) ** 0.5
        
        # Add some randomness but keep it within reasonable bounds
        noise_scale = min(5.0, std_dev * 0.8) if std_dev > 0 else 2.0
        
        # Calculate linear regression (y = mx + b)
        x_vals = list(range(len(recent_data)))
        y_vals = recent_data
        n = len(x_vals)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_x2 = sum(x * x for x in x_vals)
        
        # Calculate slope (m) and intercept (b)
        if n * sum_x2 - sum_x * sum_x != 0:  # Avoid division by zero
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
            
            # Clear previous prediction
            self.prediction_series.clear()
            
            # Add connection point at current time (0)
            if self.avg_cpu_data:
                self.prediction_series.append(0, self.avg_cpu_data[0])
            
            # Add predicted points (from 0 to -30 seconds)
            last_y = self.avg_cpu_data[0] if self.avg_cpu_data else 0
            
            for i in range(1, self.prediction_steps + 1):
                # Calculate base prediction using linear regression
                future_x = len(recent_data) + i
                base_prediction = slope * future_x + intercept
                
                # Add some natural-looking fluctuations
                # 1. Add some noise based on recent volatility
                noise = (hash(str(i)) % 200 - 100) / 100.0 * noise_scale
                
                # 2. Add some momentum from recent trend (weighted average of last few points)
                momentum = 0
                if len(recent_data) > 3:
                    recent_trend = sum(recent_data[0:3])/3 - sum(recent_data[3:6])/3 if len(recent_data) >= 6 else 0
                    momentum = recent_trend * 0.7  # Dampen the momentum effect
                
                # 3. Add some inertia (tendency to stay near recent values)
                inertia = (last_y - base_prediction) * 0.3
                
                # Combine all factors
                predicted_y = base_prediction + noise + momentum + inertia
                
                # Clamp values between 0 and 100
                predicted_y = max(0, min(100, predicted_y))
                last_y = predicted_y
                
                # Add some sinusoidal variation for more natural movement
                if i > 1:  # Skip first point to avoid sharp angles
                    cycle = (i / 5.0) % (2 * 3.14159)  # Cycle every ~6 seconds
                    predicted_y += math.sin(cycle) * (noise_scale * 0.5)
                    predicted_y = max(0, min(100, predicted_y))
                
                # Calculate time point (negative because we're going into future)
                time_point = -i * (30.0 / self.prediction_steps)
                self.prediction_series.append(time_point, predicted_y)
    
    def classify_trend(self, deltas):
        if deltas[0] > 10 and all(abs(d) < 3 for d in deltas[1:]):
            return "Spike then Flatten"
        elif all(d > 0 for d in deltas) and deltas[-1] > deltas[0]:
            return "Accelerating Uptrend"
        elif all(abs(d) < 2 for d in deltas):
            return "Flat"
        elif deltas[0] < -10 and all(abs(d) < 3 for d in deltas[1:]):
            return "Decline then Stable"
        elif deltas[0] < -5 and deltas[1] > 5:
            return "Drop then Rebound"
        elif max(deltas) - min(deltas) > 10:
            return "Volatile / Noisy"
        else:
            return "Unclassified"

    def setup_memory_tab(self):
        """Setup Memory tab with memory usage chart and stats."""
        # Main vertical layout
        main_layout = QVBoxLayout(self.memory_tab)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create a container for the top half (charts)
        top_half = QWidget()
        top_layout = QHBoxLayout(top_half)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)  # Remove spacing between graphs
        
        # Memory chart container
        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)  # No margins
        
        # Memory info
        mem_info = "Memory Usage"
        mem_info_label = QLabel(mem_info)
        mem_info_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        chart_layout.addWidget(mem_info_label)
        
        # Create memory chart - full width
        self.mem_chart, self.mem_chart_view, self.mem_axis_x, self.mem_axis_y = self.create_chart(
            "Memory Usage Over Time", "Usage (%)")
        
        # Remove margins for clean look
        self.mem_chart.setMargins(QMargins(0, 0, 0, 0))
        self.mem_chart.layout().setContentsMargins(0, 0, 0, 0)
        self.mem_chart_view.setContentsMargins(0, 0, 0, 0)
        self.mem_chart_view.setViewportMargins(0, 0, 0, 0)
        self.mem_chart_view.setBackgroundBrush(QColor(30, 30, 30))
        self.mem_chart_view.setStyleSheet("border: none; background: transparent;")
        
        # Add chart to layout with stretch
        chart_layout.addWidget(self.mem_chart_view, 1)
        
        # Add chart container to top layout with full width
        top_layout.addWidget(chart_container)
        
        # Ensure no spacing or margins between the charts
        top_layout.setSpacing(-1)  # Negative spacing to overlap borders
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create metrics container for bottom half (full width)
        metrics_container = QWidget()
        metrics_layout = QVBoxLayout(metrics_container)
        metrics_layout.setContentsMargins(10, 5, 10, 5)
        
        # Memory stats
        self.total_mem_label = QLabel()
        self.available_mem_label = QLabel()
        self.used_mem_label = QLabel()
        self.mem_percent_label = QLabel()
        self.swap_total_label = QLabel()
        self.swap_used_label = QLabel()
        self.swap_percent_label = QLabel()
        
        # Create form layout for metrics
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addRow("\u003cb\u003eMemory Total:\u003c/b\u003e", self.total_mem_label)
        form_layout.addRow("\u003cb\u003eMemory Available:\u003c/b\u003e", self.available_mem_label)
        form_layout.addRow("\u003cb\u003eMemory Used:\u003c/b\u003e", self.used_mem_label)
        form_layout.addRow("\u003cb\u003eMemory Usage %:\u003c/b\u003e", self.mem_percent_label)
        form_layout.addRow("\u003cb\u003eSwap Total:\u003c/b\u003e", self.swap_total_label)
        form_layout.addRow("\u003cb\u003eSwap Used:\u003c/b\u003e", self.swap_used_label)
        form_layout.addRow("\u003cb\u003eSwap Usage %:\u003c/b\u003e", self.swap_percent_label)
        
        # Add form layout to metrics container
        metrics_layout.addLayout(form_layout)
        
        # Add both halves to main layout with equal stretch
        main_layout.addWidget(top_half, 1)  # Top half (chart) - 1/2 height
        main_layout.addWidget(metrics_container, 1)  # Bottom half (metrics) - 1/2 height
        
        # Set stretch factors for the main layout
        main_layout.setStretch(0, 1)  # Top half (chart) - 1/2 height
        main_layout.setStretch(1, 1)  # Bottom half (metrics) - 1/2 height
        
        # Initialize with zero values
        self.mem_data = [0] * self.data_points
        self.avg_mem_data = [0] * self.data_points
        self.mem_available_data = [0] * self.data_points
        self.mem_used_data = [0] * self.data_points
        self.swap_total_data = [0] * self.data_points
        self.swap_used_data = [0] * self.data_points
        self.swap_percent_data = [0] * self.data_points
        
        # Create memory usage series
        self.mem_series = QSplineSeries()
        self.mem_series.setName("Memory (%)")
        pen = QPen(QColor(50, 205, 50))  # LimeGreen
        pen.setWidth(2)
        self.mem_series.setPen(pen)
        self.mem_chart.addSeries(self.mem_series)
        self.mem_series.attachAxis(self.mem_axis_x)
        self.mem_series.attachAxis(self.mem_axis_y)
        
        # Create prediction series
        self.mem_prediction_series = QSplineSeries()
        self.mem_prediction_series.setName("Predicted")
        pred_pen = QPen(QColor(255, 100, 100))  # Light red
        pred_pen.setWidth(2)
        pred_pen.setStyle(Qt.DashDotLine)
        self.mem_prediction_series.setPen(pred_pen)
        self.mem_chart.addSeries(self.mem_prediction_series)
        self.mem_prediction_series.attachAxis(self.mem_axis_x)
        self.mem_prediction_series.attachAxis(self.mem_axis_y)
        
        # Add a vertical line at 0 to separate real data from predictions
        self.mem_divider_line = QLineSeries()
        self.mem_divider_line.setName("Now")
        divider_pen = QPen(QColor(255, 255, 255, 150))  # Semi-transparent white
        divider_pen.setWidth(1)
        divider_pen.setStyle(Qt.DotLine)
        self.mem_divider_line.setPen(divider_pen)
        
        # Add points for the line (from bottom to top of chart)
        self.mem_divider_line.append(0, 0)
        self.mem_divider_line.append(0, 100)  # Will be clipped by axis range
        
        # Add to chart
        self.mem_chart.addSeries(self.mem_divider_line)
        self.mem_divider_line.attachAxis(self.mem_axis_x)
        self.mem_divider_line.attachAxis(self.mem_axis_y)

        # Prediction settings
        self.mem_prediction_enabled = True
        self.prediction_steps = 30  # 30 points into future (one per second)

    def update_memory_chart(self):
        """Update memory chart with current memory usage."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Update data
        self.mem_data.pop()
        self.mem_data.insert(0, mem.percent)
        self.mem_available_data.pop()
        self.mem_available_data.insert(0, mem.available * 100 / mem.total if mem.total else 0)
        self.mem_used_data.pop()
        self.mem_used_data.insert(0, mem.used * 100 / mem.total if mem.total else 0)
        self.swap_total_data.pop()
        self.swap_total_data.insert(0, swap.total * 100 / mem.total if mem.total else 0)
        self.swap_used_data.pop()
        self.swap_used_data.insert(0, swap.used * 100 / mem.total if mem.total else 0)
        self.swap_percent_data.pop()
        self.swap_percent_data.insert(0, swap.percent)
        
        # Update Y-axis range
        self.mem_axis_y.setRange(0, 100)
        
        # Update series
        self.mem_series.clear()
        time_interval = (self.time_range * 60) / (self.data_points - 1)
        
        for i, value in enumerate(self.mem_data):
            time_point = i * time_interval
            self.mem_series.append(time_point, value)

        # Add other memory percentages as separate series
        if not hasattr(self, 'mem_available_series'):
            self.mem_available_series = QSplineSeries()
            self.mem_available_series.setName("Available Memory (%)")
            pen = QPen(QColor(70, 130, 180))  # SteelBlue
            pen.setWidth(2)
            self.mem_available_series.setPen(pen)
            self.mem_chart.addSeries(self.mem_available_series)
            self.mem_available_series.attachAxis(self.mem_axis_x)
            self.mem_available_series.attachAxis(self.mem_axis_y)

        if not hasattr(self, 'mem_used_series'):
            self.mem_used_series = QSplineSeries()
            self.mem_used_series.setName("Used Memory (%)")
            pen = QPen(QColor(255, 140, 0))  # DarkOrange
            pen.setWidth(2)
            self.mem_used_series.setPen(pen)
            self.mem_chart.addSeries(self.mem_used_series)
            self.mem_used_series.attachAxis(self.mem_axis_x)
            self.mem_used_series.attachAxis(self.mem_axis_y)

        if not hasattr(self, 'swap_total_series'):
            self.swap_total_series = QSplineSeries()
            self.swap_total_series.setName("Swap Total (%)")
            pen = QPen(QColor(138, 43, 226))  # BlueViolet
            pen.setWidth(2)
            self.swap_total_series.setPen(pen)
            self.mem_chart.addSeries(self.swap_total_series)
            self.swap_total_series.attachAxis(self.mem_axis_x)
            self.swap_total_series.attachAxis(self.mem_axis_y)

        if not hasattr(self, 'swap_used_series'):
            self.swap_used_series = QSplineSeries()
            self.swap_used_series.setName("Swap Used (%)")
            pen = QPen(QColor(220, 20, 60))  # Crimson
            pen.setWidth(2)
            self.swap_used_series.setPen(pen)
            self.mem_chart.addSeries(self.swap_used_series)
            self.swap_used_series.attachAxis(self.mem_axis_x)
            self.swap_used_series.attachAxis(self.mem_axis_y)

        if not hasattr(self, 'swap_percent_series'):
            self.swap_percent_series = QSplineSeries()
            self.swap_percent_series.setName("Swap Usage (%)")
            pen = QPen(QColor(255, 215, 0))  # Gold
            pen.setWidth(2)
            self.swap_percent_series.setPen(pen)
            self.mem_chart.addSeries(self.swap_percent_series)
            self.swap_percent_series.attachAxis(self.mem_axis_x)
            self.swap_percent_series.attachAxis(self.mem_axis_y)

        # Clear and update these new series
        self.mem_available_series.clear()
        self.mem_used_series.clear()
        self.swap_total_series.clear()
        self.swap_used_series.clear()
        self.swap_percent_series.clear()

        for i, value in enumerate(self.mem_available_data):
            time_point = i * time_interval
            self.mem_available_series.append(time_point, value)

        for i, value in enumerate(self.mem_used_data):
            time_point = i * time_interval
            self.mem_used_series.append(time_point, value)

        for i, value in enumerate(self.swap_total_data):
            time_point = i * time_interval
            self.swap_total_series.append(time_point, value)

        for i, value in enumerate(self.swap_used_data):
            time_point = i * time_interval
            self.swap_used_series.append(time_point, value)

        for i, value in enumerate(self.swap_percent_data):
            time_point = i * time_interval
            self.swap_percent_series.append(time_point, value)

        # Update prediction if enabled
        if hasattr(self, 'mem_prediction_enabled') and self.mem_prediction_enabled and len(self.mem_data) >= self.prediction_window:
            self.update_memory_prediction()
    
    def update_memory_prediction(self):
        """
        Simple and predictable memory usage prediction.
        Uses recent trend but dampens it over time.
        """
        recent_data = self.mem_data[:min(3, len(self.mem_data))]  # Use last 3 points only
        
        if len(recent_data) < 2:
            return
        
        # Calculate deltas between adjacent points
        deltas = [b - a for a, b in zip(recent_data[:-1], recent_data[1:])]
        avg_delta = - sum(deltas) / len(deltas)
        slope_changes = [j - i for i, j in zip(deltas[:-1], deltas[1:])]
        
        # Classify trend
        trend_label = self.classify_trend(deltas)
        
        current_value = recent_data[0]
        
        self.mem_prediction_series.clear()
        self.mem_prediction_series.append(0, current_value)
        
        # Add predicted points
        for i in range(1, self.prediction_steps + 1):
            damping = max(0.05, 1.0 - (i / self.prediction_steps) * 0.8)
            
            # Modify prediction based on trend label
            if trend_label == "Spike then Flatten":
                # Prediction flattens after initial spike
                factor = 0.3 + 0.7 * (i / self.prediction_steps)
                predicted_y = current_value + (avg_delta * i * damping * factor)
            elif trend_label == "Accelerating Uptrend":
                # Accelerate the trend
                factor = 1.0 + 0.5 * (i / self.prediction_steps)
                predicted_y = current_value + (avg_delta * i * damping * factor)
            elif trend_label == "Flat":
                # Minimal change
                predicted_y = current_value + (hash(str(i)) % 10 - 5) / 1000.0  # ±0.005%
            elif trend_label == "Decline then Stable":
                # Prediction stabilizes after initial decline
                factor = 0.3 + 0.7 * (i / self.prediction_steps)
                predicted_y = current_value + (avg_delta * i * damping * factor)
            elif trend_label == "Drop then Rebound":
                # Prediction rebounds after initial drop
                factor = 1.0 + 0.5 * (i / self.prediction_steps)
                predicted_y = current_value + (avg_delta * i * damping * factor)
            elif trend_label == "Volatile / Noisy":
                # Prediction is highly variable
                predicted_y = current_value + (hash(str(i)) % 10 - 5) / 100.0  # ±0.5%
            else:
                # Default behavior
                predicted_y = current_value + (avg_delta * i * damping)
            
            predicted_y += (hash(str(i)) % 10 - 5) / 1000.0  # ±0.005%
            predicted_y = max(0, min(100, predicted_y))
            time_point = -i * (30.0 / self.prediction_steps)
            self.mem_prediction_series.append(time_point, predicted_y)
        
        # Optionally: store or display trend_label for UI
        self.mem_trend_label = trend_label

    def setup_disk_tab(self):
        """Setup Disk I/O tab with disk usage and I/O charts."""
        # Main layout with splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Top part - Chart
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # Disk info
        disk_info = "Disk I/O"
        disk_info_label = QLabel(disk_info)
        disk_info_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        chart_layout.addWidget(disk_info_label)
        
        # Create disk I/O chart
        self.disk_chart, self.disk_chart_view, self.disk_axis_x, self.disk_axis_y = self.create_chart(
            "Disk I/O Over Time", "KB/s", (0, 1024))  # 0-1MB/s range by default
        
        # Create series for read/write
        self.disk_read_series = QSplineSeries()
        self.disk_read_series.setName("Read (KB/s)")
        pen = QPen(QColor(255, 140, 0))  # DarkOrange
        pen.setWidth(2)
        self.disk_read_series.setPen(pen)
        
        self.disk_write_series = QSplineSeries()
        self.disk_write_series.setName("Write (KB/s)")
        pen = QPen(QColor(255, 69, 0))  # OrangeRed
        pen.setWidth(2)
        self.disk_write_series.setPen(pen)
        
        self.disk_chart.addSeries(self.disk_read_series)
        self.disk_chart.addSeries(self.disk_write_series)
        
        for series in [self.disk_read_series, self.disk_write_series]:
            series.attachAxis(self.disk_axis_x)
            series.attachAxis(self.disk_axis_y)
        
        # Set background color for the chart view
        self.disk_chart_view.setBackgroundBrush(QColor(30, 30, 30))
        
        # Add chart to layout
        chart_layout.addWidget(self.disk_chart_view)
        
        # Bottom part - Detailed metrics
        metrics_widget = QWidget()
        metrics_layout = QFormLayout(metrics_widget)
        metrics_layout.setContentsMargins(10, 5, 10, 5)
        
        # Disk stats
        disk_usage = psutil.disk_usage('/')
        
        self.disk_total_label = QLabel()
        self.disk_used_label = QLabel()
        self.disk_free_label = QLabel()
        self.disk_percent_label = QLabel()
        self.disk_read_speed = QLabel()
        self.disk_write_speed = QLabel()
        
        # Format disk size
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        
        metrics_layout.addRow("<b>Total Space:</b>", self.disk_total_label)
        metrics_layout.addRow("<b>Used Space:</b>", self.disk_used_label)
        metrics_layout.addRow("<b>Free Space:</b>", self.disk_free_label)
        metrics_layout.addRow("<b>Usage %:</b>", self.disk_percent_label)
        metrics_layout.addRow("<b>Read Speed:</b>", self.disk_read_speed)
        metrics_layout.addRow("<b>Write Speed:</b>", self.disk_write_speed)
        
        # Add widgets to splitter
        splitter.addWidget(chart_widget)
        splitter.addWidget(metrics_widget)
        
        # Set initial sizes (chart takes 60%, metrics take 40%)
        splitter.setSizes([int(self.height() * 0.6), int(self.height() * 0.4)])
        
        # Set layout
        layout = QVBoxLayout(self.disk_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(splitter)
        
        # Initialize with zero values
        self.disk_read_data = [0] * self.data_points
        self.disk_write_data = [0] * self.data_points
        self.last_disk_io = psutil.disk_io_counters()
        self.last_disk_update = datetime.now()
        
        # Initial update
        self.update_disk_chart()
    
    def update_disk_chart(self):
        """Update disk I/O chart with current disk activity."""
        # Get disk usage
        disk_usage = psutil.disk_usage('/')
        
        # Format function for bytes
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        
        # Update labels
        self.disk_total_label.setText(format_bytes(disk_usage.total))
        self.disk_used_label.setText(format_bytes(disk_usage.used))
        self.disk_free_label.setText(format_bytes(disk_usage.free))
        self.disk_percent_label.setText(f"{disk_usage.percent}%")
        
        # Calculate disk I/O rates
        current_io = psutil.disk_io_counters()
        current_time = datetime.now()
        time_diff = (current_time - self.last_disk_update).total_seconds() or 1  # Avoid division by zero
        
        # Calculate KB/s for read and write
        read_kb = (current_io.read_bytes - self.last_disk_io.read_bytes) / 1024
        write_kb = (current_io.write_bytes - self.last_disk_io.write_bytes) / 1024
        
        read_kbps = read_kb / time_diff
        write_kbps = write_kb / time_diff
        
        # Update speed labels
        self.disk_read_speed.setText(f"{read_kbps:.1f} KB/s")
        self.disk_write_speed.setText(f"{write_kbps:.1f} KB/s")
        
        # Update data
        self.disk_read_data.pop(0)
        self.disk_write_data.pop(0)
        
        self.disk_read_data.append(read_kbps)
        self.disk_write_data.append(write_kbps)
        
        # Update Y-axis range
        max_io = max(max(self.disk_read_data + self.disk_write_data) * 1.1, 10)  # At least 10 KB/s range
        self.disk_axis_y.setRange(0, max_io)
        
        # Update series
        self.disk_read_series.clear()
        self.disk_write_series.clear()
        
        time_interval = (self.time_range * 60) / (self.data_points - 1)
        
        for i in range(self.data_points):
            self.disk_read_series.append(i * time_interval, self.disk_read_data[i])
            self.disk_write_series.append(i * time_interval, self.disk_write_data[i])
        
        # Update last values
        self.last_disk_io = current_io
        self.last_disk_update = current_time
    
    def setup_network_tab(self):
        """Setup Network tab with network I/O chart and stats."""
        # Create layout
        layout = QVBoxLayout(self.network_tab)
        
        # Create chart
        self.net_chart, self.net_chart_view, self.net_axis_x, self.net_axis_y = self.create_chart(
            "Network I/O (KB/s)", "KB/s", y_range=(0, 1024)  # Start with 1 MB/s range
        )
        
        # Create series for sent and received data
        self.net_sent_series = QSplineSeries()
        self.net_sent_series.setName("Sent")
        self.net_sent_series.setColor(QColor(255, 99, 71))  # Tomato
        
        self.net_recv_series = QSplineSeries()
        self.net_recv_series.setName("Received")
        self.net_recv_series.setColor(QColor(100, 149, 237))  # Cornflower Blue
        
        # Add series to chart
        self.net_chart.addSeries(self.net_sent_series)
        self.net_chart.addSeries(self.net_recv_series)
        
        # Attach axes
        self.net_sent_series.attachAxis(self.net_axis_x)
        self.net_sent_series.attachAxis(self.net_axis_y)
        self.net_recv_series.attachAxis(self.net_axis_x)
        self.net_recv_series.attachAxis(self.net_axis_y)
        
        # Create stats labels
        stats_widget = QWidget()
        stats_layout = QFormLayout()
        
        # Network stats
        self.net_sent_label = QLabel("0 B")
        self.net_recv_label = QLabel("0 B")
        self.net_sent_rate_label = QLabel("0 KB/s")
        self.net_recv_rate_label = QLabel("0 KB/s")
        self.net_connections_label = QLabel("0")
        
        # Format labels
        for label in [self.net_sent_label, self.net_recv_label, 
                     self.net_sent_rate_label, self.net_recv_rate_label]:
            label.setStyleSheet("font-weight: bold;")
        
        # Add to layout
        stats_layout.addRow("Data Sent:", self.net_sent_label)
        stats_layout.addRow("Data Received:", self.net_recv_label)
        stats_layout.addRow("Send Rate:", self.net_sent_rate_label)
        stats_layout.addRow("Receive Rate:", self.net_recv_rate_label)
        stats_layout.addRow("Active Connections:", self.net_connections_label)
        
        stats_widget.setLayout(stats_layout)
        
        # Add widgets to main layout
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.net_chart_view)
        splitter.addWidget(stats_widget)
        splitter.setSizes([int(self.height() * 0.6), int(self.height() * 0.4)])
        
        layout.addWidget(splitter)
        self.network_tab.setLayout(layout)
        
        # Initialize network data
        self.net_sent_data = [0] * self.data_points
        self.net_recv_data = [0] * self.data_points
        self.last_net_io = psutil.net_io_counters()
        self.last_net_update = datetime.now()
    
    def update_network_chart(self):
        """Update network I/O chart with current network activity."""
        current_io = psutil.net_io_counters()
        current_time = datetime.now()
        time_diff = (current_time - self.last_net_update).total_seconds() or 1  # Avoid division by zero
        
        # Format function for bytes
        def format_bytes(bytes_value):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        
        # Update total labels
        self.net_sent_label.setText(format_bytes(current_io.bytes_sent))
        self.net_recv_label.setText(format_bytes(current_io.bytes_recv))
        
        # Calculate KB/s for sent and received
        sent_kb = (current_io.bytes_sent - self.last_net_io.bytes_sent) / 1024
        recv_kb = (current_io.bytes_recv - self.last_net_io.bytes_recv) / 1024
        
        sent_kbps = sent_kb / time_diff
        recv_kbps = recv_kb / time_diff
        
        # Update rate labels
        self.net_sent_rate_label.setText(f"{sent_kbps:.1f} KB/s")
        self.net_recv_rate_label.setText(f"{recv_kbps:.1f} KB/s")
        
        # Get active connections
        try:
            connections = psutil.net_connections(kind='inet')
            active_connections = len([conn for conn in connections if conn.status == 'ESTABLISHED'])
            self.net_connections_label.setText(f"{active_connections} established")
        except:
            self.net_connections_label.setText("N/A")
        
        # Update data
        self.net_sent_data.pop(0)
        self.net_recv_data.pop(0)
        
        self.net_sent_data.append(sent_kbps)
        self.net_recv_data.append(recv_kbps)
        
        # Update Y-axis range
        max_net = max(max(self.net_sent_data + self.net_recv_data) * 1.1, 10)  # At least 10 KB/s range
        self.net_axis_y.setRange(0, max_net)
        
        # Update series
        self.net_sent_series.clear()
        self.net_recv_series.clear()
        
        time_interval = (self.time_range * 60) / (self.data_points - 1)
        
        for i in range(self.data_points):
            self.net_sent_series.append(i * time_interval, self.net_sent_data[i])
            self.net_recv_series.append(i * time_interval, self.net_recv_data[i])
        
        # Update last values
        self.last_net_io = current_io
        self.last_net_update = current_time