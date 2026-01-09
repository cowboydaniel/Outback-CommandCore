"""
VANTAGE Animated Splash Screen
Device Intelligence Platform themed with monitoring dashboard visualization.
"""
 
import sys
import math
import random
import time
from PySide6.QtCore import (Qt, QTimer, QRectF, QRect, QPointF,
                          Property, QEasingCurve, QPropertyAnimation)
from PySide6.QtGui import (QPainter, QColor, QLinearGradient, QRadialGradient,
                         QPainterPath, QPen, QFont)
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
 
 
class DeviceIntelligenceBackground(QWidget):
    """Animated device monitoring dashboard visualization."""
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
 
        # VANTAGE colors - blue/teal tech theme
        self.primary = QColor('#00a8ff')    # Vantage blue
        self.accent = QColor('#00d2d3')     # Teal
        self.secondary = QColor('#0097e6')  # Darker blue
        self.success = QColor('#2ecc71')    # Green for healthy
        self.warning = QColor('#f39c12')    # Orange for warnings
        self.bg_color = QColor(20, 28, 35)
 
        self.time = 0.0
        self.devices = []  # Connected devices
        self.metrics = []  # Performance metrics bars
        self.graph_points = []  # Line graph data
        self.scan_rings = []  # Scanning rings
        self.data_streams = []  # Data flowing to/from devices
 
        # Status
        self.status_message = "Initializing device scanner..."
        self.status_font = QFont("Arial", 9)
 
        # Fonts
        self.title_font = QFont("Arial", 48, QFont.Bold)
        self.subtitle_font = QFont("Arial", 16)
        self.version_font = QFont("Arial", 10, QFont.Bold)
        self.metric_font = QFont("Consolas", 8)
 
        self.init_dashboard()
 
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)
 
    def init_dashboard(self):
        """Initialize dashboard elements."""
        # Devices around the edges
        self.devices = []
        device_positions = [
            (0.08, 0.25), (0.08, 0.5), (0.08, 0.75),  # Left side
            (0.92, 0.25), (0.92, 0.5), (0.92, 0.75),  # Right side
        ]
        device_types = ['laptop', 'phone', 'server', 'tablet', 'desktop', 'router']
 
        for i, (x, y) in enumerate(device_positions):
            self.devices.append({
                'x': x, 'y': y,
                'type': device_types[i % len(device_types)],
                'status': random.choice(['healthy', 'healthy', 'healthy', 'warning']),
                'pulse': random.uniform(0, 2 * math.pi),
                'connected': True,
                'metrics': {
                    'cpu': random.uniform(20, 80),
                    'mem': random.uniform(30, 70),
                    'net': random.uniform(10, 90)
                }
            })
 
        # Performance metric bars (center-left area)
        self.metrics = [
            {'name': 'CPU', 'value': 0.45, 'target': 0.45, 'color': self.primary},
            {'name': 'MEM', 'value': 0.62, 'target': 0.62, 'color': self.accent},
            {'name': 'NET', 'value': 0.38, 'target': 0.38, 'color': self.secondary},
            {'name': 'DSK', 'value': 0.71, 'target': 0.71, 'color': self.success},
        ]
 
        # Graph data points
        self.graph_points = []
        for i in range(50):
            self.graph_points.append(0.5 + random.uniform(-0.2, 0.2))
 
    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
 
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            painter.fillPath(path, self.bg_color)
 
            # Draw grid background
            self.draw_grid(painter)
 
            # Draw connection lines from devices to center
            self.draw_connections(painter)
 
            # Draw data streams
            self.draw_data_streams(painter)
 
            # Draw scanning rings in center
            self.draw_scan_rings(painter)
 
            # Draw devices
            self.draw_devices(painter)
 
            # Draw metric bars
            self.draw_metrics(painter)
 
            # Draw mini graph
            self.draw_graph(painter)
 
            # Draw center hub
            self.draw_hub(painter)
 
            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)
 
        finally:
            painter.end()
 
    def draw_grid(self, painter):
        """Draw subtle tech grid."""
        grid_color = QColor(40, 55, 65, 40)
        painter.setPen(QPen(grid_color, 1))
 
        spacing = 25
        for x in range(0, self.width(), spacing):
            alpha = 60 if x % 100 == 0 else 30
            painter.setPen(QPen(QColor(40, 55, 65, alpha), 1))
            painter.drawLine(x, 0, x, self.height())
 
        for y in range(0, self.height(), spacing):
            alpha = 60 if y % 100 == 0 else 30
            painter.setPen(QPen(QColor(40, 55, 65, alpha), 1))
            painter.drawLine(0, y, self.width(), y)
 
    def draw_connections(self, painter):
        """Draw connection lines from devices to center."""
        center_x = self.width() * 0.5
        center_y = self.height() * 0.5
 
        for device in self.devices:
            if not device['connected']:
                continue
 
            dev_x = device['x'] * self.width()
            dev_y = device['y'] * self.height()
 
            # Pulsing connection
            pulse = 0.4 + 0.3 * math.sin(self.time * 2 + device['pulse'])
 
            # Draw dashed line
            color = QColor(self.primary)
            color.setAlpha(int(100 * pulse))
 
            pen = QPen(color, 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(QPointF(dev_x, dev_y), QPointF(center_x, center_y))
 
    def draw_data_streams(self, painter):
        """Draw data flowing along connections."""
        center_x = self.width() * 0.5
        center_y = self.height() * 0.5
 
        for stream in self.data_streams:
            device = self.devices[stream['device_idx']]
            dev_x = device['x'] * self.width()
            dev_y = device['y'] * self.height()
 
            # Interpolate position
            t = stream['progress']
            if stream['direction'] == 'in':
                x = dev_x + (center_x - dev_x) * t
                y = dev_y + (center_y - dev_y) * t
            else:
                x = center_x + (dev_x - center_x) * t
                y = center_y + (dev_y - center_y) * t
 
            # Draw glowing data packet
            glow = QRadialGradient(x, y, 8)
            glow.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 200))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
 
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), 8, 8)
 
    def draw_scan_rings(self, painter):
        """Draw expanding scan rings from center."""
        center_x = self.width() * 0.5
        center_y = self.height() * 0.5
 
        for ring in self.scan_rings:
            radius = ring['radius'] * min(self.width(), self.height()) * 0.4
            alpha = int(150 * (1 - ring['progress']))
 
            color = QColor(self.primary)
            color.setAlpha(alpha)
 
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(center_x, center_y), radius, radius * 0.6)
 
    def draw_devices(self, painter):
        """Draw device icons."""
        for device in self.devices:
            x = device['x'] * self.width()
            y = device['y'] * self.height()
 
            # Pulse effect
            pulse = 0.8 + 0.2 * math.sin(self.time * 3 + device['pulse'])
 
            # Status color
            if device['status'] == 'healthy':
                status_color = self.success
            else:
                status_color = self.warning
 
            # Device background glow
            glow = QRadialGradient(x, y, 30)
            glow.setColorAt(0, QColor(status_color.red(), status_color.green(), status_color.blue(), int(60 * pulse)))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), 30, 30)
 
            # Device icon (simplified shapes)
            painter.setPen(QPen(status_color, 2))
            painter.setBrush(QColor(30, 40, 50, 200))
 
            if device['type'] in ['laptop', 'desktop']:
                # Monitor shape
                painter.drawRoundedRect(QRectF(x - 12, y - 8, 24, 14), 2, 2)
                painter.drawLine(QPointF(x - 6, y + 6), QPointF(x + 6, y + 6))
                painter.drawLine(QPointF(x, y + 6), QPointF(x, y + 10))
                painter.drawLine(QPointF(x - 8, y + 10), QPointF(x + 8, y + 10))
            elif device['type'] == 'phone':
                # Phone shape
                painter.drawRoundedRect(QRectF(x - 6, y - 10, 12, 20), 2, 2)
            elif device['type'] == 'tablet':
                # Tablet shape
                painter.drawRoundedRect(QRectF(x - 10, y - 7, 20, 14), 2, 2)
            elif device['type'] == 'server':
                # Server shape (stacked rectangles)
                for i in range(3):
                    painter.drawRect(QRectF(x - 10, y - 8 + i * 6, 20, 5))
            else:  # router
                # Router shape
                painter.drawRoundedRect(QRectF(x - 12, y - 4, 24, 8), 2, 2)
                # Antennas
                painter.drawLine(QPointF(x - 6, y - 4), QPointF(x - 8, y - 10))
                painter.drawLine(QPointF(x + 6, y - 4), QPointF(x + 8, y - 10))
 
            # Status indicator dot
            painter.setPen(Qt.NoPen)
            painter.setBrush(status_color)
            painter.drawEllipse(QPointF(x + 10, y - 8), 4, 4)
 
    def draw_metrics(self, painter):
        """Draw performance metric bars."""
        bar_x = self.width() * 0.15
        bar_y = self.height() * 0.7
        bar_width = 80
        bar_height = 8
        spacing = 18
 
        painter.setFont(self.metric_font)
 
        for i, metric in enumerate(self.metrics):
            y = bar_y + i * spacing
 
            # Label
            painter.setPen(QColor(180, 200, 220, 180))
            painter.drawText(QPointF(bar_x - 35, y + 6), metric['name'])
 
            # Background bar
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(40, 50, 60))
            painter.drawRoundedRect(QRectF(bar_x, y, bar_width, bar_height), 2, 2)
 
            # Value bar
            value_width = bar_width * metric['value']
            gradient = QLinearGradient(bar_x, 0, bar_x + value_width, 0)
            gradient.setColorAt(0, metric['color'])
            gradient.setColorAt(1, metric['color'].lighter(120))
            painter.setBrush(gradient)
            painter.drawRoundedRect(QRectF(bar_x, y, value_width, bar_height), 2, 2)
 
            # Percentage
            painter.setPen(QColor(200, 220, 240, 200))
            painter.drawText(QPointF(bar_x + bar_width + 8, y + 6), f"{int(metric['value'] * 100)}%")
 
    def draw_graph(self, painter):
        """Draw mini performance graph."""
        graph_x = self.width() * 0.72
        graph_y = self.height() * 0.7
        graph_width = 100
        graph_height = 50
 
        # Graph background
        painter.setPen(QPen(QColor(50, 60, 70), 1))
        painter.setBrush(QColor(25, 35, 45, 150))
        painter.drawRoundedRect(QRectF(graph_x, graph_y, graph_width, graph_height), 4, 4)
 
        # Graph line
        if len(self.graph_points) > 1:
            path = QPainterPath()
            for i, value in enumerate(self.graph_points):
                x = graph_x + 5 + (i / (len(self.graph_points) - 1)) * (graph_width - 10)
                y = graph_y + graph_height - 5 - value * (graph_height - 10)
 
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
 
            # Glow effect
            painter.setPen(QPen(QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 100), 4))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
 
            # Main line
            painter.setPen(QPen(self.accent, 2))
            painter.drawPath(path)
 
    def draw_hub(self, painter):
        """Draw central monitoring hub."""
        center_x = self.width() * 0.5
        center_y = self.height() * 0.5
        radius = 35
 
        # Outer glow
        glow = QRadialGradient(center_x, center_y, radius * 2)
        glow.setColorAt(0, QColor(self.primary.red(), self.primary.green(), self.primary.blue(), 40))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(center_x, center_y), radius * 2, radius * 2)
 
        # Hub circle
        hub_gradient = QRadialGradient(center_x - 10, center_y - 10, radius * 1.5)
        hub_gradient.setColorAt(0, QColor(50, 65, 80))
        hub_gradient.setColorAt(1, QColor(30, 40, 50))
 
        painter.setPen(QPen(self.primary, 2))
        painter.setBrush(hub_gradient)
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
 
        # Inner rings
        painter.setPen(QPen(self.accent, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(center_x, center_y), radius * 0.7, radius * 0.7)
        painter.drawEllipse(QPointF(center_x, center_y), radius * 0.4, radius * 0.4)
 
        # Rotating indicator
        angle = self.time * 2
        indicator_x = center_x + radius * 0.5 * math.cos(angle)
        indicator_y = center_y + radius * 0.5 * math.sin(angle)
 
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.accent)
        painter.drawEllipse(QPointF(indicator_x, indicator_y), 4, 4)
 
    def draw_progress_bar(self, painter):
        progress_height = 4
        margin = 40
        bar_width = self.width() - 2 * margin
        bar_y = self.height() - 80
 
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawRoundedRect(margin, bar_y, bar_width, progress_height, 2, 2)
 
        progress_gradient = QLinearGradient(0, 0, bar_width, 0)
        progress_gradient.setColorAt(0, self.primary)
        progress_gradient.setColorAt(1, self.accent)
 
        painter.setBrush(progress_gradient)
        progress_width = bar_width * self._animation_progress
        painter.drawRoundedRect(margin, bar_y, progress_width, progress_height, 2, 2)
 
    def draw_text(self, painter):
        base_opacity = self._text_opacity
        center_y = self.height() // 2
        title_height = 60
 
        painter.setFont(self.title_font)
        title = "VANTAGE"
 
        title_rect = painter.fontMetrics().boundingRect(title)
        title_x = (self.width() - title_rect.width()) // 2
        title_y = center_y - 40
 
        gradient = QLinearGradient(0, 0, 0, title_height)
        gradient.setColorAt(0, self.primary)
        gradient.setColorAt(1, self.accent)
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
 
        text_path = QPainterPath()
        text_path.addText(0, 0, self.title_font, title)
 
        painter.save()
        painter.translate(title_x, title_y)
        painter.setOpacity(base_opacity)
        painter.drawPath(text_path)
        painter.restore()
 
        painter.setFont(self.subtitle_font)
        subtitle = "Device Intelligence Platform"
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle)
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + title_height + 10
 
        painter.setPen(QColor(180, 220, 255, int(220 * base_opacity)))
        painter.drawText(subtitle_x, subtitle_y, subtitle)
 
        version = "v1.0.0"
        painter.setFont(self.version_font)
        version_rect = painter.fontMetrics().boundingRect(version)
        version_x = self.width() - version_rect.width() - 30
        version_y = self.height() - 30
 
        painter.setPen(QColor(160, 200, 230, int(200 * base_opacity)))
        painter.drawText(version_x, version_y, version)
 
        # Status
        painter.setFont(self.status_font)
        status_rect = painter.fontMetrics().boundingRect(self.status_message)
        status_x = 30
        status_y = self.height() - 30
 
        bg_rect = QRect(status_x - 5, status_y - status_rect.height() - 5,
                       status_rect.width() + 10, status_rect.height() + 10)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 120))
        painter.drawRoundedRect(bg_rect, 4, 4)
 
        painter.setPen(QColor(220, 220, 220, int(180 * base_opacity)))
        painter.drawText(status_x, status_y, self.status_message)
 
    def animate(self):
        current_time = time.time()
        if not hasattr(self, 'last_frame_time'):
            self.last_frame_time = current_time
        delta_time = min(0.1, current_time - self.last_frame_time)
        self.last_frame_time = current_time
        self.time += delta_time
 
        # Update metrics (smooth animation toward target)
        for metric in self.metrics:
            if random.random() < 0.02:
                metric['target'] = random.uniform(0.2, 0.9)
            metric['value'] += (metric['target'] - metric['value']) * 0.1
 
        # Update graph points (shift left and add new)
        if random.random() < 0.3:
            self.graph_points.pop(0)
            last = self.graph_points[-1] if self.graph_points else 0.5
            new_val = last + random.uniform(-0.1, 0.1)
            new_val = max(0.1, min(0.9, new_val))
            self.graph_points.append(new_val)
 
        # Spawn scan rings
        if random.random() < 0.02:
            self.scan_rings.append({
                'radius': 0.1,
                'progress': 0.0,
                'speed': random.uniform(0.01, 0.02)
            })
 
        # Update scan rings
        new_rings = []
        for ring in self.scan_rings:
            ring['progress'] += ring['speed']
            ring['radius'] += ring['speed'] * 0.5
            if ring['progress'] < 1.0:
                new_rings.append(ring)
        self.scan_rings = new_rings
 
        # Spawn data streams
        if random.random() < 0.08 and self.devices:
            device_idx = random.randint(0, len(self.devices) - 1)
            self.data_streams.append({
                'device_idx': device_idx,
                'direction': random.choice(['in', 'out']),
                'progress': 0.0,
                'speed': random.uniform(0.02, 0.04)
            })
 
        # Update data streams
        new_streams = []
        for stream in self.data_streams:
            stream['progress'] += stream['speed']
            if stream['progress'] < 1.0:
                new_streams.append(stream)
        self.data_streams = new_streams
 
        self.update()
 
    def update_status(self, message: str):
        self.status_message = message
        self.update()
 
 
class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VANTAGE")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
 
        self.setStyleSheet("QMainWindow { background: rgb(20, 28, 35); }")
 
        self.main_widget = DeviceIntelligenceBackground(self)
        self.setCentralWidget(self.main_widget)
 
        self._animation_progress = 0.0
        self._text_opacity = 0.0
 
        self.progress_anim = QPropertyAnimation(self, b"animation_progress")
        self.progress_anim.setDuration(5900)
        self.progress_anim.setStartValue(0.0)
        self.progress_anim.setEndValue(1.0)
        self.progress_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.progress_anim.start()
 
        self.text_fade_in = QPropertyAnimation(self, b"text_opacity")
        self.text_fade_in.setDuration(1000)
        self.text_fade_in.setStartValue(0.0)
        self.text_fade_in.setEndValue(1.0)
        self.text_fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self.text_fade_in.start()
 
        self.dragging = False
        self.offset = None
 
    def get_animation_progress(self):
        return self._animation_progress
 
    def set_animation_progress(self, value):
        self._animation_progress = value
        self.update()
 
    def get_text_opacity(self):
        return self._text_opacity
 
    def set_text_opacity(self, value):
        self._text_opacity = value
        self.update()
 
    animation_progress = Property(float, get_animation_progress, set_animation_progress)
    text_opacity = Property(float, get_text_opacity, set_text_opacity)
 
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.pos()
 
    def mouseMoveEvent(self, event):
        if self.dragging and self.offset:
            self.move(event.globalPosition().toPoint() - self.offset)
 
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
 
    def update_status(self, message: str):
        if hasattr(self, 'main_widget'):
            self.main_widget.update_status(message)
 
 
def show_splash_screen():
    window = SplashScreen()
    frame_geometry = window.frameGeometry()
    screen = QApplication.primaryScreen().availableGeometry()
    frame_geometry.moveCenter(screen.center())
    window.move(frame_geometry.topLeft())
    window.show()
    return window
 
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SplashScreen()
    window.show()
    sys.exit(app.exec())
