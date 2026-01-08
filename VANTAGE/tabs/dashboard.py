import sys
import random
import time
import logging
import psutil
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSizePolicy, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QComboBox)
from PySide6 import QtCore
from PySide6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QPointF, 
                          QTimer, QDateTime, Signal, QPoint, QRectF, QMargins)
from PySide6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QLinearGradient, QGradient, QPainterPath, QPixmap, QBrush
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QValueAxis, 
                            QPieSeries, QPieSlice, QBarSet, QBarSeries, 
                            QBarCategoryAxis, QBarLegendMarker, QSplineSeries)

logger = logging.getLogger(__name__)

class MetricCard(QFrame):
    """Custom widget for displaying metric cards with gradient styling"""
    def __init__(self, title, value, unit="", trend=None, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 140)  # Increased height to prevent text cutoff
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        # Set up styles for text elements
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                padding: 10px 15px;
            }
            QFrame > QLabel {
                background-color: transparent;
            }
            QLabel#title {
                color: #b0b0b0;
                font-size: 14px;
                font-weight: 500;
                padding: 0;
                margin: 0;
            }
            QLabel#value {
                color: #ffffff;
                font-size: 36px;
                font-weight: 600;
                padding: 0;
                margin: 0;
                line-height: 1.0;
            }
            QLabel#unit {
                color: #b0b0b0;
                font-size: 18px;
                padding: 0;
                margin: 0 0 0 5px;
                line-height: 1.0;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("title")
        
        # Value and unit
        value_layout = QHBoxLayout()
        self.value_label = QLabel(value)
        self.value_label.setObjectName("value")
        self.unit_label = QLabel(unit)
        self.unit_label.setObjectName("unit")
        
        value_layout.addWidget(self.value_label)
        value_layout.addWidget(self.unit_label)
        value_layout.addStretch()
        
        # Add trend indicator if provided
        if trend is not None:
            self.trend_label = QLabel("↗" if trend > 0 else "↘")
            self.trend_label.setStyleSheet(
                f"color: {'#00d4aa' if trend > 0 else '#ff6b6b'};"
                "font-size: 16px; font-weight: bold;"
            )
            value_layout.addWidget(self.trend_label)
        
        layout.addWidget(title_label)
        layout.addLayout(value_layout)
        layout.addStretch()
        
    def paintEvent(self, event):
        """Custom paint event to draw the card with gradient background"""
        with QPainter(self) as painter:
            # Set up rendering hints for best quality
            painter.setRenderHints(
                QPainter.Antialiasing |
                QPainter.SmoothPixmapTransform |
                QPainter.TextAntialiasing
            )
            
            # Define the card's rounded rectangle area
            rect = self.rect().adjusted(1, 1, -1, -1)
            radius = 12
            
            # Create gradient with user-specified colors
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0.0, QColor("#3a3a3a"))  # Top color
            gradient.setColorAt(0.5, QColor("#2a2a2a"))  # Middle color
            gradient.setColorAt(1.0, QColor("#1a1a1a"))  # Bottom color
            
            # Create a subtle dithering effect using a texture brush
            dither_brush = QBrush(Qt.DiagCrossPattern)
            dither_brush.setColor(QColor(0, 0, 0, 10))  # Very subtle dithering
            
            # Draw the background with rounded corners
            path = QPainterPath()
            path.addRoundedRect(rect, radius, radius)
            
            # Create a clip path for the rounded corners
            painter.setClipPath(path)
            
            # Draw the gradient
            painter.fillPath(path, gradient)
            
            # Apply subtle dithering
            painter.setOpacity(0.05)  # Very subtle dithering
            painter.fillPath(path, dither_brush)
            painter.setOpacity(1.0)
            
            # Draw border with anti-aliasing
            painter.setRenderHint(QPainter.Antialiasing, True)
            pen = QPen(QColor("#3d3d3d"), 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawRoundedRect(rect, radius, radius)

class AnimatedGaugeWidget(QWidget):
    """Enhanced gauge widget with smooth animations and gradients"""
    def __init__(self, title, min_val=0, max_val=100, parent=None):
        super().__init__(parent)
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self.current_value = min_val
        self.target_value = min_val
        self.setMinimumSize(220, 220)
        
        # Animation for smooth value transitions - faster animation
        self.animation = QPropertyAnimation(self, b"animatedValue")
        self.animation.setDuration(200)  # Faster animation (200ms instead of 500ms)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
    def set_value(self, value):
        new_value = max(self.min_val, min(self.max_val, value))
        if abs(new_value - self.target_value) > 0.5:  # Only animate if significant change
            self.target_value = new_value
            self.animation.setStartValue(self.current_value)
            self.animation.setEndValue(self.target_value)
            self.animation.start()
    
    def getAnimatedValue(self):
        return self.current_value
    
    def setAnimatedValue(self, value):
        self.current_value = value
        self.update()
    
    animatedValue = QtCore.Property(float, getAnimatedValue, setAnimatedValue)
    
    def apply_dither_overlay(self, painter, rect, strength=8, opacity=0.03):
        """Helper method to apply dithering overlay"""
        dither = QBrush(Qt.Dense5Pattern)
        color = QColor(0, 0, 0, strength)
        painter.save()
        painter.setOpacity(opacity)
        painter.setBrush(dither)
        painter.setPen(Qt.NoPen)
        painter.fillRect(rect, color)
        painter.restore()

    def paintEvent(self, event):
        """Custom paint event to draw the gauge with animations"""
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.TextAntialiasing
        )
        
        # Draw background with stronger contrast gradient
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0, QColor("#3a3a3a"))
        bg_gradient.setColorAt(0.5, QColor("#2a2a2a"))
        bg_gradient.setColorAt(1, QColor("#1a1a1a"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_gradient)
        painter.drawRoundedRect(self.rect(), 12, 12)
        
        # Apply subtle dithering overlay
        self.apply_dither_overlay(painter, self.rect())
        
        # Draw gauge arc
        size = min(self.width(), self.height()) - 60
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2 + 10
        
        # Background arc with gradient - 280 degree arc with centered alignment
        bg_pen = QPen(QColor("#3d3d3d"), 8, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(x, y, size, size, 230 * 16, -280 * 16)  # 280 degree arc, centered
        
        # Value arc with animated gradient - smoother transitions
        if self.current_value > self.min_val:
            # Create gradient from left to right of the gauge
            gradient = QLinearGradient(x, 0, x + size, 0)
            
            # Color based on value percentage with smoother transitions
            ratio = (self.current_value - self.min_val) / (self.max_val - self.min_val)
            if ratio < 0.5:
                # Blue gradient
                gradient.setColorAt(0.0, QColor("#00a8ff"))
                gradient.setColorAt(0.3, QColor("#0099ee"))
                gradient.setColorAt(0.7, QColor("#0088dd"))
                gradient.setColorAt(1.0, QColor("#0077cc"))
            elif ratio < 0.8:
                # Teal to blue gradient
                gradient.setColorAt(0.0, QColor("#00d4aa"))
                gradient.setColorAt(0.3, QColor("#00c0c0"))
                gradient.setColorAt(0.7, QColor("#00a0e0"))
                gradient.setColorAt(1.0, QColor("#0088ff"))
            else:
                # Red gradient
                gradient.setColorAt(0.0, QColor("#ff7b7b"))
                gradient.setColorAt(0.3, QColor("#ff6b6b"))
                gradient.setColorAt(0.7, QColor("#ff5555"))
                gradient.setColorAt(1.0, QColor("#ff3b3b"))
            
            value_pen = QPen(gradient, 8, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(value_pen)
            
            angle = int(280 * ratio)  # 280 degree range
            painter.drawArc(x, y, size, size, 230 * 16, -angle * 16)  # Negative angle for counter-clockwise drawing
        
        # Draw center circle
        center_x = self.width() // 2
        center_y = (self.height() // 2) + 5
        
        center_gradient = QLinearGradient(center_x - 30, center_y - 30, center_x + 30, center_y + 30)
        center_gradient.setColorAt(0, QColor("#404040"))
        center_gradient.setColorAt(1, QColor("#2d2d2d"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(center_gradient)
        painter.drawEllipse(center_x - 25, center_y - 25, 50, 50)
        
        # Draw value text
        font = QFont("Segoe UI", 18, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        
        value_text = f"{self.current_value:.0f}"
        text_rect = painter.boundingRect(self.rect(), Qt.AlignCenter, value_text)
        text_rect.moveCenter(QPoint(int(center_x), int(center_y - 5)))
        painter.drawText(text_rect, Qt.AlignCenter, value_text)
        
        # Draw unit
        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.setPen(QColor("#00a8ff"))
        unit_text = "%"
        unit_rect = painter.boundingRect(self.rect(), Qt.AlignCenter, unit_text)
        unit_rect.moveCenter(QPoint(int(center_x), int(center_y + 15)))
        painter.drawText(unit_rect, Qt.AlignCenter, unit_text)
        
        # Draw title
        font = QFont("Segoe UI", 11, QFont.Medium)
        painter.setFont(font)
        painter.setPen(QColor("#b0b0b0"))
        
        title_rect = self.rect().adjusted(10, 0, -10, -15)
        painter.drawText(title_rect, Qt.AlignHCenter | Qt.AlignBottom, self.title)

class DashboardTab(QWidget):
    """Modern dashboard tab with smooth animated visualizations"""
    
    def __init__(self, parent=None, main_window=None, tab_widget=None):
        """Initialize the dashboard tab with enhanced UI."""
        super().__init__(parent)
        self.main_window = main_window
        self.tab_widget = tab_widget
        self.chart_data_points = []  # Store time-series data
        self.max_data_points = 120   # 2 minutes of data at 1Hz
        self.health_history = []     # Store health scores for trend calculation
        self.max_health_history = 6  # Keep last 6 scores for trend (30s history at 5s updates)
        self.health_window_seconds = 15  # Time window for health score calculation (seconds)
        
        # Performance score tracking
        self.performance_history = []  # Store (timestamp, score) tuples
        self.performance_window_seconds = 3  # 3-second window for performance average
        self.setup_ui()
        self.setup_data_refresh()
    
    def setup_ui(self):
        """Set up the modern dashboard UI with enhanced styling."""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        # Container widget for scroll area
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)
        
        # Header
        header = self.create_header()
        layout.addLayout(header)

        initial_metrics = self.collect_initial_metrics()
        
        # Metrics row 1
        metrics_row1 = QHBoxLayout()
        metrics_row1.setSpacing(20)
        
        # Initialize with real data from system collectors
        self.health_card = MetricCard(
            "System Health",
            initial_metrics["health_value"],
            "%",
            initial_metrics["health_trend"]
        )
        self.device_card = MetricCard(
            "Active Devices",
            initial_metrics["device_count"],
            "",
            initial_metrics["device_trend"]
        )
        self.alerts_card = MetricCard(
            "Security Alerts",
            initial_metrics["alerts_value"],
            ""
        )
        self.performance_card = MetricCard(
            "Performance",
            initial_metrics["performance_value"],
            "%",
            initial_metrics["performance_trend"]
        )
        
        metrics_row1.addWidget(self.health_card)
        metrics_row1.addWidget(self.device_card)
        metrics_row1.addWidget(self.alerts_card)
        metrics_row1.addWidget(self.performance_card)
        
        layout.addLayout(metrics_row1)
        
        # Charts row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(20)
        
        # Left side - Enhanced Gauges
        gauges_layout = QVBoxLayout()
        gauges_layout.setSpacing(15)
        self.cpu_gauge = AnimatedGaugeWidget("CPU Usage")
        self.memory_gauge = AnimatedGaugeWidget("Memory Usage")
        
        gauges_layout.addWidget(self.cpu_gauge)
        gauges_layout.addWidget(self.memory_gauge)
        
        # Right side - Enhanced Line chart
        self.line_chart = self.create_enhanced_line_chart()
        
        charts_row.addLayout(gauges_layout, 2)
        charts_row.addWidget(self.line_chart, 5)
        
        layout.addLayout(charts_row)
        
        # Bottom row - Additional metrics
        metrics_row2 = QHBoxLayout()
        metrics_row2.setSpacing(20)
        
        self.network_card = MetricCard("Network I/O", initial_metrics["network_value"], "MB/s")
        self.storage_card = MetricCard("Storage Used", initial_metrics["storage_value"], initial_metrics["storage_unit"])
        self.temp_card = MetricCard("Avg. Temp", initial_metrics["temp_value"], "°C")
        self.uptime_card = MetricCard("Uptime", initial_metrics["uptime_value"], "")
        
        metrics_row2.addWidget(self.network_card)
        metrics_row2.addWidget(self.storage_card)
        metrics_row2.addWidget(self.temp_card)
        metrics_row2.addWidget(self.uptime_card)
        
        layout.addLayout(metrics_row2)
        layout.addStretch()
        
        # Set up scroll area
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # Apply enhanced dark theme
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1a, stop:1 #0f0f0f);
                color: #ffffff;
                font-family: 'Segoe UI', 'San Francisco', Arial, sans-serif;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(45, 45, 45, 0.3);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                height: 0px;
            }
        """)
    
    def create_header(self):
        """Create the dashboard header with device selection."""
        header = QHBoxLayout()
        
        # Left side - Container for device selection
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        
        # Device selection dropdown
        self.device_dropdown = QComboBox()
        self.device_dropdown.setFixedWidth(300)
        self.device_dropdown.setStyleSheet("""
            QComboBox {
                background-color: rgba(30, 39, 46, 0.8);
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 200px;
                font-size: 14px;
                selection-background-color: #00a8ff;
            }
            QComboBox:hover {
                border: 1px solid #5d5d5d;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(icons/down-arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2d2e;
                color: #ffffff;
                selection-background-color: #00a8ff;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        
        # Add current device as default
        import socket
        current_device = socket.gethostname()
        self.device_dropdown.addItem(f"{current_device} (This Device)", "local")
        
        # Connect to device change signal
        self.device_dropdown.currentIndexChanged.connect(self.on_device_changed)
        
        # Store current device ID
        self.current_device_id = "local"  # Default to local device
        
        # Add device dropdown to layout
        title_layout.addWidget(self.device_dropdown)
        
        # Add title container to header
        header.addWidget(title_container)
        
        # Enhanced timestamp
        self.timestamp = QLabel()
        self.update_timestamp()
        
        # Status indicator
        status_label = QLabel("● ONLINE")
        status_label.setStyleSheet("""
            color: #00d4aa;
            font-size: 12px;
            font-weight: 600;
            padding: 5px 10px;
            background-color: rgba(0, 212, 170, 0.1);
            border-radius: 15px;
            border: 1px solid rgba(0, 212, 170, 0.3);
        """)
        
        # Add widgets to header
        header.addStretch()
        header.addWidget(status_label)
        header.addWidget(self.timestamp)
        
        return header
    
    def create_enhanced_line_chart(self):
        """Create an enhanced line chart with smooth splines and animations."""
        # Create chart with enhanced styling
        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.legend().setVisible(True)
        chart.legend().setLabelColor(QColor("#e0e0e0"))
        chart.legend().setFont(QFont("Segoe UI", 10))
        chart.setMargins(QMargins(10, 10, 10, 10))
        chart.setTitle("Real-time System Performance")
        chart.setTitleBrush(QColor("#ffffff"))
        chart.setTitleFont(QFont("Segoe UI", 14, QFont.Medium))
        
        # Create smooth spline series instead of line series
        self.cpu_series = QSplineSeries()
        self.cpu_series.setName("CPU Usage")
        self.cpu_series.setColor(QColor("#00a8ff"))
        self.cpu_series.setPen(QPen(QColor("#00a8ff"), 3))
        
        self.memory_series = QSplineSeries()
        self.memory_series.setName("Memory Usage")
        self.memory_series.setColor(QColor("#00d4aa"))
        self.memory_series.setPen(QPen(QColor("#00d4aa"), 3))
        
        # Add glow effect with additional series
        self.cpu_glow = QSplineSeries()
        self.cpu_glow.setColor(QColor(0, 168, 255, 60))
        self.cpu_glow.setPen(QPen(QColor(0, 168, 255, 60), 8))
        
        self.memory_glow = QSplineSeries()
        self.memory_glow.setColor(QColor(0, 212, 170, 60))
        self.memory_glow.setPen(QPen(QColor(0, 212, 170, 60), 8))
        
        # Start with empty series - they will fill from right to left
        chart.addSeries(self.cpu_glow)
        chart.addSeries(self.memory_glow)
        chart.addSeries(self.cpu_series)
        chart.addSeries(self.memory_series)
        
        # Create enhanced axes
        axis_x = QValueAxis()
        axis_x.setLabelsColor(QColor("#b0b0b0"))
        axis_x.setGridLineColor(QColor("#2d2d2d"))
        axis_x.setLabelsFont(QFont("Segoe UI", 9))
        axis_x.setRange(0, self.max_data_points)
        axis_x.setTitleText("Time (Latest →)")
        axis_x.setTitleBrush(QColor("#e0e0e0"))
        axis_x.setTitleFont(QFont("Segoe UI", 10))
        axis_x.setLabelsVisible(False)
        
        axis_y = QValueAxis()
        axis_y.setLabelsColor(QColor("#b0b0b0"))
        axis_y.setGridLineColor(QColor("#2d2d2d"))
        axis_y.setLabelsFont(QFont("Segoe UI", 9))
        axis_y.setRange(0, 100)
        axis_y.setTitleText("Usage %")
        axis_y.setTitleBrush(QColor("#e0e0e0"))
        axis_y.setTitleFont(QFont("Segoe UI", 10))
        
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        
        # Attach axes to all series
        for series in [self.cpu_series, self.memory_series, self.cpu_glow, self.memory_glow]:
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        
        # Create enhanced chart view with dithering
        class DitherChartView(QChartView):
            def paintEvent(self, event):
                # First draw the chart
                super().paintEvent(event)
                
                # Then apply dithering overlay
                painter = QPainter(self.viewport())
                painter.setRenderHints(
                    QPainter.Antialiasing |
                    QPainter.SmoothPixmapTransform |
                    QPainter.TextAntialiasing
                )
                
                # Create dither brush
                dither_brush = QBrush(Qt.DiagCrossPattern)
                dither_brush.setColor(QColor(0, 0, 0, 10))  # Very subtle dithering
                
                # Apply dithering to the chart area
                painter.setOpacity(0.05)
                painter.fillRect(self.rect(), dither_brush)
                painter.end()
        
        chart_view = DitherChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setStyleSheet("""
            QChartView {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3a, stop:0.5 #2a2a2a, stop:1 #1a1a1a);
                border-radius: 12px;
                border: 1px solid #3d3d3d;
            }
        """)
        chart_view.setMinimumHeight(350)
        
        return chart_view
        
    def setup_data_refresh(self):
        """Set up timers for data refresh and smooth animations."""
        # Update dashboard every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)  # 1 FPS for data updates
        
        # Animation timer for smooth chart updates - increased to 60 FPS
        self.chart_animation_timer = QTimer(self)
        self.chart_animation_timer.timeout.connect(self.animate_chart_update)
        self.chart_animation_timer.start(16)  # ~60 FPS for smooth animation

    def collect_initial_metrics(self):
        """Collect initial metric values for card initialization."""
        metrics = {
            "health_value": "Data unavailable",
            "health_trend": 0,
            "device_count": "Data unavailable",
            "device_trend": 0,
            "alerts_value": "Data unavailable",
            "performance_value": "Data unavailable",
            "performance_trend": 0,
            "network_value": "Data unavailable",
            "storage_value": "Data unavailable",
            "storage_unit": "",
            "temp_value": "Data unavailable",
            "uptime_value": "Data unavailable"
        }

        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/')

            health_score = self.calculate_system_health()
            if health_score is not None:
                metrics["health_value"] = f"{int(health_score)}"

            performance_score = self.calculate_performance_score(cpu_usage, memory_usage)
            if performance_score is not None:
                metrics["performance_value"] = f"{int(performance_score)}"

            metrics["alerts_value"] = str(
                self.calculate_alert_count(cpu_usage, memory_usage, disk_usage.percent)
            )

            metrics["device_count"] = "1"

            net_io = psutil.net_io_counters()
            self._prev_net_io = net_io
            self._prev_net_time = time.time()
            metrics["network_value"] = "0.0/0.0"

            storage_value, storage_unit = self.format_storage_usage(disk_usage)
            metrics["storage_value"] = storage_value
            metrics["storage_unit"] = storage_unit

            avg_temp = self.get_average_cpu_temp()
            if avg_temp is not None:
                metrics["temp_value"] = f"{avg_temp:.0f}"

            metrics["uptime_value"] = self.format_uptime(time.time() - psutil.boot_time())
        except Exception as e:
            logger.exception("Error collecting initial metrics: %s", e)

        return metrics

    def set_metric_unavailable(self, card, unit_text=""):
        """Show a clear unavailable state on a metric card."""
        card.value_label.setText("Data unavailable")
        card.unit_label.setText(unit_text)
        if hasattr(card, 'trend_label'):
            card.trend_label.setText("!")
            card.trend_label.setStyleSheet("color: #b0b0b0; font-size: 16px; font-weight: bold;")

    def get_average_cpu_temp(self):
        """Return average CPU temperature, or None if unavailable."""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None

            cpu_temps = []
            for name, entries in temps.items():
                if 'core' in name.lower() or 'cpu' in name.lower() or 'k10temp' in name.lower() or 'coretemp' in name.lower():
                    for entry in entries:
                        if entry.current and entry.current > 0:
                            cpu_temps.append(entry.current)

            if cpu_temps:
                return sum(cpu_temps) / len(cpu_temps)
            return None
        except Exception as e:
            logger.exception("Error reading CPU temperature: %s", e)
            return None

    def format_storage_usage(self, disk_usage):
        """Format storage usage display values."""
        def format_bytes(size):
            power = 2**10  # 2**10 = 1024
            n = 0
            power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
            while size > power and n < len(power_labels) - 1:
                size /= power
                n += 1
            return size, power_labels[n]

        used, used_unit = format_bytes(disk_usage.used)
        total, total_unit = format_bytes(disk_usage.total)
        percent_used = disk_usage.percent

        storage_value = (
            f"{used:.1f}<span style='font-size: 18px; color: #b0b0b0;'>"
            f" {used_unit} / {total:.1f} {total_unit}</span>"
        )
        storage_unit = f"({percent_used:.0f}% used)"
        return storage_value, storage_unit

    def calculate_alert_count(self, cpu_usage, memory_usage, disk_percent):
        """Calculate a basic alert count based on system thresholds."""
        alerts = 0

        if cpu_usage >= 90:
            alerts += 1
        if memory_usage >= 90:
            alerts += 1
        if disk_percent >= 90:
            alerts += 1

        avg_temp = self.get_average_cpu_temp()
        if avg_temp is not None and avg_temp >= 85:
            alerts += 1

        return alerts

    def calculate_performance_score(self, cpu_usage, memory_usage):
        """Calculate a performance score for the current system state."""
        try:
            cpu_score = max(0, 100 - (cpu_usage * 1.2))

            if memory_usage < 60:
                memory_score = 100 - (memory_usage * 0.5)
            elif memory_usage < 85:
                memory_score = 100 - (60 * 0.5) - ((memory_usage - 60) * 1.5)
            else:
                memory_score = max(0, 100 - (60 * 0.5) - (25 * 1.5) - ((memory_usage - 85) * 4))

            try:
                io_wait = psutil.cpu_times_percent().iowait
                disk_io_score = max(0, 100 - (io_wait * 2))
            except Exception as e:
                logger.exception("Error reading I/O wait time: %s", e)
                disk_io_score = 90

            weights = {
                'cpu': 0.5,
                'memory': 0.3,
                'disk_io': 0.2
            }

            return (
                (cpu_score * weights['cpu']) +
                (memory_score * weights['memory']) +
                (disk_io_score * weights['disk_io'])
            )
        except Exception as e:
            logger.exception("Error calculating performance score: %s", e)
            return None

    def update_timestamp(self):
        """Update the timestamp with enhanced styling."""
        now = datetime.now()
        self.timestamp.setText(now.strftime("%a, %b %d %Y • %H:%M:%S"))
        self.timestamp.setStyleSheet("""
            color: #b0b0b0; 
            font-size: 11px; 
            font-weight: 500;
            padding: 5px 10px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        """)
    
    def calculate_system_health(self):
        """Calculate system health score based on various metrics with 15-second moving average."""
        try:
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate individual scores (0-100 scale)
            cpu_score = max(0, 100 - (cpu_usage * 1.2))  # Slight penalty for high CPU
            
            # More forgiving memory scoring
            memory_usage = memory.percent
            if memory_usage < 40:
                # 0-40% usage: 100-95% score (very forgiving)
                memory_score = 100 - (memory_usage * 0.125)
            elif memory_usage < 70:
                # 40-70% usage: 95-85% score (gentle slope)
                memory_score = 95 - ((memory_usage - 40) * 0.333)
            elif memory_usage < 90:
                # 70-90% usage: 85-50% score (steeper drop)
                memory_score = 85 - ((memory_usage - 70) * 1.75)
            else:
                # 90%+ usage: 50-0% score (very steep drop)
                memory_score = max(0, 50 - ((memory_usage - 90) * 5))
            
            # Disk score - 100% until 95% full, then drops sharply
            disk_used_percent = (disk.used / disk.total * 100) if disk.total > 0 else 0
            if disk_used_percent < 95:
                disk_free_score = 100  # Full score until 95% full
            else:
                # Drop sharply from 100 to 0 in the last 5%
                disk_free_score = max(0, 100 - ((disk_used_percent - 95) * 20))
                
            try:
                disk_io_wait = psutil.cpu_times_percent().iowait
                disk_io_score = max(0, 100 - (disk_io_wait * 2))  # Less aggressive I/O penalty
            except Exception as e:
                logger.exception("Error reading disk I/O wait: %s", e)
                disk_io_score = 100
                
            disk_score = (disk_free_score * 0.8) + (disk_io_score * 0.2)  # Favor free space more
            
            # More granular temperature scoring
            try:
                temp = self.get_average_cpu_temp()
                if temp is None:
                    temp_score = 100
                elif temp < 60:
                    temp_score = 100
                elif temp < 70:
                    temp_score = 95
                elif temp < 75:
                    temp_score = 90
                elif temp < 80:
                    temp_score = 80
                elif temp < 85:
                    temp_score = 70
                else:
                    temp_score = 50
            except Exception as e:
                logger.exception("Error reading temperature: %s", e)
                temp_score = 100  # If temp can't be read, assume it's fine
                
            # Network score - check if there's any network activity
            try:
                net_io = psutil.net_io_counters()
                bytes_sent = getattr(net_io, 'bytes_sent', 0)
                bytes_recv = getattr(net_io, 'bytes_recv', 0)
                if bytes_sent > 0 or bytes_recv > 0:
                    net_score = 100  # Network is active
                else:
                    net_score = 90  # No network activity but interface is up
            except Exception as e:
                logger.exception("Error reading network counters: %s", e)
                net_score = 90  # Default if can't check
            
            # Get system uptime in hours
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_hours = uptime_seconds / 3600
            
            # Uptime score (100% if < 12 hours, decreasing to 0% at 5 days)
            if uptime_hours <= 12:
                uptime_score = 100
            else:
                # Linear decrease from 100% at 12h to 0% at 120h (5 days)
                uptime_score = max(0, 100 - ((uptime_hours - 12) * (100 / 108)))
            
            # Weighted average with updated weights (sums to 100%)
            weights = {
                'cpu': 0.30,      # 30% weight
                'memory': 0.25,    # 25% weight
                'disk': 0.15,      # 15% weight
                'temp': 0.25,      # 25% weight
                'network': 0.01,   # 1% weight
                'uptime': 0.04     # 4% weight
            }
            
            # Calculate weighted components for debugging
            weighted_scores = {
                'cpu': cpu_score * weights['cpu'],
                'memory': memory_score * weights['memory'],
                'disk': disk_score * weights['disk'],
                'temp': temp_score * weights['temp'],
                'network': net_score * weights['network'],
                'uptime': uptime_score * weights['uptime']
            }
            
            # Calculate current health score
            current_health_score = sum(weighted_scores.values())
            current_health_score = min(100, max(0, current_health_score))
            
            # Get current timestamp
            current_time = time.time()
            
            # Add current score to history with timestamp
            self.health_history.append((current_time, current_health_score))
            
            # Remove entries older than 15 seconds
            cutoff_time = current_time - self.health_window_seconds
            self.health_history = [(t, s) for t, s in self.health_history if t >= cutoff_time]
            
            # Calculate moving average
            if self.health_history:
                avg_health = sum(s for _, s in self.health_history) / len(self.health_history)
                
                # Calculate trend based on first and last values in the window
                if len(self.health_history) > 1:
                    first_time, first_score = self.health_history[0]
                    last_time, last_score = self.health_history[-1]
                    time_diff = last_time - first_time
                    if time_diff > 0:  # Avoid division by zero
                        trend = (last_score - first_score) / time_diff
                        print(f"Trend: {trend:+.4f}% per second (over {time_diff:.1f}s window)")
                
                # Debug output
                print("\n=== System Health Debug ===")
                print(f"Current Health Score: {current_health_score:.2f}%")
                print(f"15s Moving Average: {avg_health:.2f}% (based on {len(self.health_history)} samples)")
                print(f"Raw Scores (weighted):")
                for metric, score in weighted_scores.items():
                    print(f"  {metric:8}: {score:6.2f} (weight: {weights[metric]:.2f})")
                print(f"\nRaw Scores (unweighted):")
                print(f"  {'CPU:':8} {cpu_score:6.2f}% (usage: {cpu_usage}%)")
                print(f"  {'Memory:':8} {memory_score:6.2f}% (usage: {memory_usage}%)")
                print(f"  {'Disk:':8} {disk_score:6.2f}% (used: {disk_used_percent:.1f}%, io_wait: {disk_io_wait if 'disk_io_wait' in locals() else 'N/A'})")
                print(f"  {'Temp:':8} {temp_score:6.2f}% ({temp if 'temp' in locals() else 'N/A'}°C)")
                print(f"  {'Network:':8} {net_score:6.2f}%")
                print(f"  {'Uptime:':8} {uptime_score:6.2f}% ({uptime_hours:.1f} hours)")
                
                return avg_health  # Return the moving average instead of current score
            
            return current_health_score  # Fallback if no history yet
            
        except Exception as e:
            logger.exception("Error calculating system health: %s", e)
            return None
    
    def update_dashboard(self):
        """Update all dashboard metrics with real data."""
        # Update timestamp
        self.update_timestamp()
        
        # Get real system data
        cpu_usage = psutil.cpu_percent(interval=None)
        memory_usage = psutil.virtual_memory().percent
        
        # Update gauges with smooth animation
        self.cpu_gauge.set_value(cpu_usage)
        self.memory_gauge.set_value(memory_usage)
        
        # Calculate and update system health
        health_score = self.calculate_system_health()
        
        # Store new data point for chart
        self.chart_data_points.append({
            'timestamp': time.time(),
            'cpu': cpu_usage,
            'memory': memory_usage
        })
        
        # Calculate trend based on the 15s moving average window
        if len(self.health_history) >= 2:
            # Get oldest and newest scores in the window
            oldest_time, oldest_score = self.health_history[0]
            newest_time, newest_score = self.health_history[-1]
            
            # Calculate trend (1.5 if improving, -0.5 if declining, 0.5 if stable)
            time_diff = newest_time - oldest_time
            if time_diff > 0:  # Avoid division by zero
                trend_rate = (newest_score - oldest_score) / time_diff
                if trend_rate > 0.1:  # More than 0.1% per second improvement
                    trend = 1.5
                elif trend_rate < -0.1:  # More than 0.1% per second decline
                    trend = -0.5
                else:
                    trend = 0.5  # Stable
            else:
                trend = 0.5  # Default neutral trend if we can't calculate
        else:
            trend = 0.5  # Default neutral trend if not enough data
        
        if health_score is None:
            self.set_metric_unavailable(self.health_card, "%")
        else:
            # Update health card with moving average if we have data
            if self.health_history:
                avg_health = sum(s for _, s in self.health_history) / len(self.health_history)
                self.health_card.value_label.setText(f"{int(avg_health)}")
                
                # Update trend indicator if it exists
                if hasattr(self.health_card, 'trend_label'):
                    color = "#00d4aa" if trend > 1 else ("#ff6b6b" if trend < 0 else "#b0b0b0")
                    self.health_card.trend_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
            else:
                # Fallback to current health score if no history yet
                self.health_card.value_label.setText(f"{int(health_score)}")
        
        # Keep only recent data points
        if len(self.chart_data_points) > self.max_data_points:
            self.chart_data_points = self.chart_data_points[-self.max_data_points:]
        
        # Update other metrics
        self.update_system_metrics()
        self.update_uptime()
        self.update_device_count()
        self.update_alerts(cpu_usage, memory_usage)
        
        # Calculate and update performance score with 3-second moving average
        try:
            current_time = time.time()
            
            # Get current metrics
            current_score = self.calculate_performance_score(cpu_usage, memory_usage)
            if current_score is None:
                raise ValueError("Performance score unavailable")
            
            # Add current score to history with timestamp
            self.performance_history.append((current_time, current_score))
            
            # Remove scores older than our window
            cutoff_time = current_time - self.performance_window_seconds
            self.performance_history = [score for score in self.performance_history 
                                     if score[0] >= cutoff_time]
            
            # Calculate moving average if we have data
            if self.performance_history:
                avg_score = sum(score[1] for score in self.performance_history) / len(self.performance_history)
                # Ensure score is within 0-100 range
                avg_score = max(0, min(100, avg_score))
                
                # Update performance card with the averaged score
                self.performance_card.value_label.setText(f"{int(avg_score)}")
                
                # Update trend indicator if it exists
                if hasattr(self.performance_card, 'trend_label'):
                    # Simple trend based on previous value if available
                    if not hasattr(self, '_last_performance_score'):
                        self._last_performance_score = avg_score
                    
                    trend = avg_score - self._last_performance_score
                    color = "#00d4aa" if trend > 1 else ("#ff6b6b" if trend < -1 else "#b0b0b0")
                    trend_icon = "↗" if trend > 1 else ("↘" if trend < -1 else "→")
                    
                    self.performance_card.trend_label.setText(trend_icon)
                    self.performance_card.trend_label.setStyleSheet(
                        f"color: {color}; font-size: 16px; font-weight: bold;"
                    )
                    
                    self._last_performance_score = avg_score
            
        except Exception as e:
            logger.exception("Error updating performance score: %s", e)
            self.set_metric_unavailable(self.performance_card, "%")
    
    def animate_chart_update(self):
        """Smoothly animate chart updates with data flowing right to left."""
        if not self.chart_data_points:
            return
            
        try:
            # Clear existing points
            self.cpu_series.clear()
            self.memory_series.clear()
            self.cpu_glow.clear()
            self.memory_glow.clear()
            
            # Add points from right to left (newest to oldest)
            num_points = len(self.chart_data_points)
            for i, data_point in enumerate(self.chart_data_points):
                # Calculate x position from right to left
                x_pos = self.max_data_points - (num_points - i)
                
                # Add main series points
                self.cpu_series.append(x_pos, data_point['cpu'])
                self.memory_series.append(x_pos, data_point['memory'])
                
                # Add glow effect points (slightly offset)
                self.cpu_glow.append(x_pos, data_point['cpu'])
                self.memory_glow.append(x_pos, data_point['memory'])
            
            # Update x-axis range to show data flowing from right to left
            if hasattr(self, 'line_chart'):
                chart = self.line_chart.chart()
                if chart:
                    axes = chart.axes(Qt.Horizontal)
                    if axes:
                        axis_x = axes[0]
                        # Set range to show data flowing from right to left
                        axis_x.setRange(0, self.max_data_points)
                        
        except Exception as e:
            print(f"Error updating chart animation: {e}")
    
    def update_system_metrics(self):
        """Update additional system metrics."""
        try:
            # Network I/O
            net_io = psutil.net_io_counters()
            if hasattr(self, '_prev_net_io') and hasattr(self, '_prev_net_time'):
                time_delta = time.time() - self._prev_net_time
                if time_delta > 0:
                    bytes_sent_per_sec = (net_io.bytes_sent - self._prev_net_io.bytes_sent) / time_delta
                    bytes_recv_per_sec = (net_io.bytes_recv - self._prev_net_io.bytes_recv) / time_delta
                    
                    # Convert to MB/s
                    mb_sent = bytes_sent_per_sec / (1024 * 1024)
                    mb_recv = bytes_recv_per_sec / (1024 * 1024)
                    
                    self.network_card.value_label.setText(f"{mb_recv:.1f}/{mb_sent:.1f}")
                else:
                    self.set_metric_unavailable(self.network_card, "MB/s")
            else:
                self.set_metric_unavailable(self.network_card, "MB/s")
            
            self._prev_net_io = net_io
            self._prev_net_time = time.time()
            
            # Storage usage for boot drive
            boot_drive = psutil.disk_usage('/')

            # Update the storage card with formatted values
            storage_value, storage_unit = self.format_storage_usage(boot_drive)
            self.storage_card.value_label.setText(storage_value)
            self.storage_card.unit_label.setText(storage_unit)
            
            # Update the card title to be more specific
            for i in range(self.storage_card.layout().count()):
                widget = self.storage_card.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.objectName() == "title":
                    widget.setText("Boot Drive Used")
                    break
            
            # CPU temperature (if available)
            avg_temp = self.get_average_cpu_temp()
            if avg_temp is not None:
                self.temp_card.value_label.setText(f"{avg_temp:.0f}")
                # Update the card title to be more specific by finding the title label
                for i in range(self.temp_card.layout().count()):
                    widget = self.temp_card.layout().itemAt(i).widget()
                    if isinstance(widget, QLabel) and widget.objectName() == "title":
                        widget.setText("CPU Temp")
                        break
            else:
                self.set_metric_unavailable(self.temp_card, "°C")
                
        except Exception as e:
            logger.exception("Error updating system metrics: %s", e)
            self.set_metric_unavailable(self.network_card, "MB/s")
            self.set_metric_unavailable(self.storage_card)
            self.set_metric_unavailable(self.temp_card, "°C")
    
    def format_uptime(self, seconds):
        """Format uptime into a human-readable string with seconds."""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds = int(remainder % 60)
        
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m {seconds}s"
        elif hours > 0:
            return f"{int(hours)}h {int(minutes)}m {seconds}s"
        elif minutes > 0:
            return f"{int(minutes)}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def update_uptime(self):
        """Update the uptime display with real system uptime."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = (datetime.now() - boot_time).total_seconds()
            self.uptime_card.value_label.setText(self.format_uptime(uptime_seconds))
        except Exception as e:
            logger.exception("Error updating uptime: %s", e)
            self.set_metric_unavailable(self.uptime_card)

    def update_alerts(self, cpu_usage=None, memory_usage=None):
        """Update the alert count based on current system thresholds."""
        try:
            if cpu_usage is None:
                cpu_usage = psutil.cpu_percent(interval=None)
            if memory_usage is None:
                memory_usage = psutil.virtual_memory().percent

            disk_percent = psutil.disk_usage('/').percent
            alert_count = self.calculate_alert_count(cpu_usage, memory_usage, disk_percent)
            self.alerts_card.value_label.setText(str(alert_count))
        except Exception as e:
            logger.exception("Error updating alert count: %s", e)
            self.set_metric_unavailable(self.alerts_card)
            
    def on_device_changed(self, index):
        """Handle device selection change."""
        if index >= 0:  # Check if the index is valid
            device_data = self.device_dropdown.itemData(index)
            if device_data:
                self.current_device_id = device_data
                print(f"Selected device: {self.device_dropdown.itemText(index)}")
                # Here you would typically update the dashboard to show data for the selected device
                # For now, we'll just store the device ID
            else:
                print("No device data available")
    
    def update_device_count(self):
        """Update the active devices count based on the DevicesTab.
        
        Counts the number of devices listed in the DevicesTab plus the local device.
        """
        try:
            tab_widget = self.tab_widget
            if tab_widget is None and self.main_window is not None:
                tab_widget = self.main_window.tab_widget
            if tab_widget is None:
                logger.warning("DashboardTab has no tab widget reference for device count")
                self.set_metric_unavailable(self.device_card)
                return
                
            # Initialize device count to 1 for local device
            device_count = 1
            
            # Try to find the DevicesTab
            for i in range(tab_widget.count()):
                widget = tab_widget.widget(i)
                if widget and widget.objectName() == "DevicesTab":
                    # Found the DevicesTab, now count the rows in its table
                    if hasattr(widget, 'devices_table'):
                        # Count non-empty rows in the devices table
                        table = widget.devices_table
                        for row in range(table.rowCount()):
                            # Check if the first column has text (device ID)
                            if table.item(row, 0) and table.item(row, 0).text().strip():
                                device_count += 1
                    break
            
            # Update the display
            self.device_card.value_label.setText(str(device_count))
            
            # Update trend indicator
            if hasattr(self, 'last_device_count'):
                trend = 1 if device_count > self.last_device_count else (-1 if device_count < self.last_device_count else 0)
                if hasattr(self.device_card, 'trend_label'):
                    self.device_card.trend_label.setText("↗" if trend > 0 else ("↘" if trend < 0 else "→"))
                    color = "#00d4aa" if trend > 0 else ("#ff6b6b" if trend < 0 else "#b0b0b0")
                    self.device_card.trend_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
            
            self.last_device_count = device_count
            
        except Exception as e:
            logger.exception("Error updating device count: %s", e)
            self.set_metric_unavailable(self.device_card)
