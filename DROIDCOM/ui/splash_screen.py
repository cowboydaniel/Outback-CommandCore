"""
DROIDCOM Animated Splash Screen
Android device management with device outlines and connection wave animations.
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


class DeviceConnectionBackground(QWidget):
    """Animated device connections and signal waves."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # DROIDCOM colors - Android green theme
        self.primary = QColor('#3DDC84')    # Android green
        self.accent = QColor('#4285F4')     # Google blue
        self.secondary = QColor('#EA4335')  # Google red
        self.dark_green = QColor('#0F9D58')  # Darker green
        self.bg_color = QColor(20, 25, 30)

        self.time = 0.0
        self.devices = []  # Device outlines
        self.connection_waves = []  # Radiating connection signals
        self.data_packets = []  # Data flowing between devices

        # Status
        self.status_message = "Scanning for devices..."
        self.status_font = QFont("Arial", 9)

        # Fonts
        self.title_font = QFont("Arial", 48, QFont.Bold)
        self.subtitle_font = QFont("Arial", 14)
        self.version_font = QFont("Arial", 10, QFont.Bold)

        self.init_devices()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def init_devices(self):
        """Initialize device representations."""
        # Central hub (computer/server)
        self.hub = {'x': 0.5, 'y': 0.5, 'size': 0.08}

        # Surrounding devices (phones/tablets)
        self.devices = []
        device_count = 6
        for i in range(device_count):
            angle = (2 * math.pi * i / device_count) - math.pi / 2
            radius = 0.3
            self.devices.append({
                'x': 0.5 + radius * math.cos(angle),
                'y': 0.5 + radius * math.sin(angle),
                'base_x': 0.5 + radius * math.cos(angle),
                'base_y': 0.5 + radius * math.sin(angle),
                'size': 0.04,
                'angle': angle,
                'phase': random.uniform(0, 2 * math.pi),
                'connected': True,
                'pulse': 0.0
            })

        # Initialize some connection waves
        self.connection_waves = []

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            painter.fillPath(path, self.bg_color)

            # Draw grid pattern in background
            self.draw_grid(painter)

            # Draw connection lines
            self.draw_connections(painter)

            # Draw connection waves
            self.draw_waves(painter)

            # Draw data packets
            self.draw_data_packets(painter)

            # Draw hub
            self.draw_hub(painter)

            # Draw devices
            self.draw_devices(painter)

            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)

        finally:
            painter.end()

    def draw_grid(self, painter):
        """Draw subtle background grid."""
        grid_color = QColor(60, 80, 70, 30)
        painter.setPen(QPen(grid_color, 1))

        spacing = 30
        for x in range(0, self.width(), spacing):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), spacing):
            painter.drawLine(0, y, self.width(), y)

    def draw_connections(self, painter):
        """Draw connection lines between hub and devices."""
        hub_x = self.hub['x'] * self.width()
        hub_y = self.hub['y'] * self.height()

        for device in self.devices:
            if not device['connected']:
                continue

            dev_x = device['x'] * self.width()
            dev_y = device['y'] * self.height()

            # Pulsing connection line
            pulse = 0.4 + 0.3 * math.sin(self.time * 3 + device['phase'])
            alpha = int(255 * pulse)

            # Draw glowing line
            for width, a_mult in [(6, 0.2), (3, 0.5), (1, 1.0)]:
                color = QColor(self.primary)
                color.setAlpha(int(alpha * a_mult))
                painter.setPen(QPen(color, width))
                painter.drawLine(QPointF(hub_x, hub_y), QPointF(dev_x, dev_y))

    def draw_waves(self, painter):
        """Draw radiating connection waves."""
        for wave in self.connection_waves:
            x = wave['x'] * self.width()
            y = wave['y'] * self.height()
            radius = wave['radius'] * min(self.width(), self.height())

            alpha = int(255 * (1 - wave['progress']) * 0.5)
            color = QColor(self.primary)
            color.setAlpha(alpha)

            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(x, y), radius, radius)

    def draw_data_packets(self, painter):
        """Draw data packets traveling between devices."""
        for packet in self.data_packets:
            # Interpolate position
            start_x = packet['from_x'] * self.width()
            start_y = packet['from_y'] * self.height()
            end_x = packet['to_x'] * self.width()
            end_y = packet['to_y'] * self.height()

            t = packet['progress']
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t

            # Draw glowing packet
            glow = QRadialGradient(x, y, 12)
            glow.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 200))
            glow.setColorAt(0.5, QColor(self.primary.red(), self.primary.green(), self.primary.blue(), 100))
            glow.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), 12, 12)

            # Core
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.drawEllipse(QPointF(x, y), 3, 3)

    def draw_hub(self, painter):
        """Draw central hub (computer icon)."""
        x = self.hub['x'] * self.width()
        y = self.hub['y'] * self.height()
        size = self.hub['size'] * min(self.width(), self.height())

        # Glow effect
        glow = QRadialGradient(x, y, size * 2)
        glow.setColorAt(0, QColor(self.primary.red(), self.primary.green(), self.primary.blue(), 60))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(x, y), size * 2, size * 2)

        # Computer/monitor shape
        monitor_width = size * 1.5
        monitor_height = size * 1.0

        # Monitor body
        monitor_rect = QRectF(x - monitor_width/2, y - monitor_height/2 - 5,
                             monitor_width, monitor_height)
        painter.setPen(QPen(self.primary, 2))
        painter.setBrush(QColor(30, 40, 35, 200))
        painter.drawRoundedRect(monitor_rect, 4, 4)

        # Screen
        screen_rect = QRectF(x - monitor_width/2 + 4, y - monitor_height/2 - 1,
                            monitor_width - 8, monitor_height - 8)
        screen_gradient = QLinearGradient(0, screen_rect.top(), 0, screen_rect.bottom())
        screen_gradient.setColorAt(0, QColor(40, 60, 50))
        screen_gradient.setColorAt(1, QColor(30, 45, 40))
        painter.setBrush(screen_gradient)
        painter.drawRoundedRect(screen_rect, 2, 2)

        # Stand
        painter.setPen(QPen(self.primary, 2))
        painter.drawLine(QPointF(x, y + monitor_height/2 - 5),
                        QPointF(x, y + monitor_height/2 + 8))
        painter.drawLine(QPointF(x - 10, y + monitor_height/2 + 8),
                        QPointF(x + 10, y + monitor_height/2 + 8))

    def draw_devices(self, painter):
        """Draw device icons (phones/tablets)."""
        for device in self.devices:
            x = device['x'] * self.width()
            y = device['y'] * self.height()
            size = device['size'] * min(self.width(), self.height())

            # Pulse effect when receiving data
            pulse_scale = 1.0 + device['pulse'] * 0.3
            size *= pulse_scale

            # Glow
            glow_alpha = 40 + int(device['pulse'] * 100)
            glow = QRadialGradient(x, y, size * 2)
            glow.setColorAt(0, QColor(self.primary.red(), self.primary.green(), self.primary.blue(), glow_alpha))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), size * 2, size * 2)

            # Phone shape
            phone_width = size * 0.7
            phone_height = size * 1.4

            phone_rect = QRectF(x - phone_width/2, y - phone_height/2,
                               phone_width, phone_height)

            # Phone body
            painter.setPen(QPen(self.primary, 2))
            painter.setBrush(QColor(25, 35, 30, 220))
            painter.drawRoundedRect(phone_rect, 4, 4)

            # Screen
            screen_rect = QRectF(x - phone_width/2 + 3, y - phone_height/2 + 6,
                                phone_width - 6, phone_height - 12)
            painter.setBrush(QColor(40, 55, 45))
            painter.drawRoundedRect(screen_rect, 2, 2)

            # Status indicator
            status_color = self.primary if device['connected'] else self.secondary
            painter.setBrush(status_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y - phone_height/2 + 3), 2, 2)

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
        title = "DROIDCOM"

        title_rect = painter.fontMetrics().boundingRect(title)
        title_x = (self.width() - title_rect.width()) // 2
        title_y = center_y - 40

        gradient = QLinearGradient(0, 0, 0, title_height)
        gradient.setColorAt(0, self.primary)
        gradient.setColorAt(1, self.dark_green)
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
        subtitle = "Android Device Management"
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle)
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + title_height + 10

        painter.setPen(QColor(180, 255, 200, int(220 * base_opacity)))
        painter.drawText(subtitle_x, subtitle_y, subtitle)

        version = "v1.0.0"
        painter.setFont(self.version_font)
        version_rect = painter.fontMetrics().boundingRect(version)
        version_x = self.width() - version_rect.width() - 30
        version_y = self.height() - 30

        painter.setPen(QColor(160, 230, 180, int(200 * base_opacity)))
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

        # Animate devices with subtle floating
        for device in self.devices:
            device['x'] = device['base_x'] + 0.01 * math.sin(self.time * 0.8 + device['phase'])
            device['y'] = device['base_y'] + 0.01 * math.cos(self.time * 0.6 + device['phase'])

            # Decay pulse
            device['pulse'] *= 0.95

        # Spawn connection waves from hub
        if random.random() < 0.03:
            self.connection_waves.append({
                'x': self.hub['x'],
                'y': self.hub['y'],
                'radius': 0.02,
                'progress': 0.0,
                'speed': random.uniform(0.01, 0.02)
            })

        # Update waves
        new_waves = []
        for wave in self.connection_waves:
            wave['progress'] += wave['speed']
            wave['radius'] += wave['speed'] * 0.5
            if wave['progress'] < 1.0:
                new_waves.append(wave)
        self.connection_waves = new_waves

        # Spawn data packets
        if random.random() < 0.05 and self.devices:
            device = random.choice(self.devices)
            # Randomly to or from hub
            if random.random() < 0.5:
                self.data_packets.append({
                    'from_x': self.hub['x'], 'from_y': self.hub['y'],
                    'to_x': device['x'], 'to_y': device['y'],
                    'progress': 0.0,
                    'speed': random.uniform(0.02, 0.04),
                    'target_device': device
                })
            else:
                self.data_packets.append({
                    'from_x': device['x'], 'from_y': device['y'],
                    'to_x': self.hub['x'], 'to_y': self.hub['y'],
                    'progress': 0.0,
                    'speed': random.uniform(0.02, 0.04),
                    'target_device': None
                })

        # Update packets
        new_packets = []
        for packet in self.data_packets:
            packet['progress'] += packet['speed']
            if packet['progress'] < 1.0:
                new_packets.append(packet)
            elif packet['target_device']:
                packet['target_device']['pulse'] = 1.0
        self.data_packets = new_packets

        self.update()

    def update_status(self, message: str):
        self.status_message = message
        self.update()


class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DROIDCOM")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QMainWindow { background: rgb(20, 25, 30); }")

        self.main_widget = DeviceConnectionBackground(self)
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
