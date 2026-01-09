"""
HackAttack Animated Splash Screen
Network topology with scanning effects and terminal aesthetic.
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


class NetworkScanBackground(QWidget):
    """Animated network topology with scanning effects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # HackAttack colors - cyberpunk red/cyan theme
        self.primary = QColor('#e74c3c')    # Red (danger/attack)
        self.accent = QColor('#00ff88')     # Neon green (terminal)
        self.secondary = QColor('#3498db')  # Blue (network)
        self.warning = QColor('#f39c12')    # Orange (warnings)
        self.bg_color = QColor(10, 12, 18)  # Very dark blue-black

        self.time = 0.0
        self.nodes = []  # Network nodes
        self.scan_line = 0.0  # Horizontal scan line
        self.terminal_lines = []  # Scrolling terminal output
        self.packets = []  # Network packets
        self.scan_targets = []  # Nodes being scanned

        # Status
        self.status_message = "Initializing penetration testing modules..."
        self.status_font = QFont("Arial", 9)

        # Fonts
        self.title_font = QFont("Arial", 48, QFont.Bold)
        self.subtitle_font = QFont("Arial", 14)
        self.version_font = QFont("Arial", 10, QFont.Bold)
        self.terminal_font = QFont("Consolas", 8)

        self.init_network()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def init_network(self):
        """Initialize network topology."""
        self.nodes = []

        # Create random network topology
        for _ in range(20):
            node = {
                'x': random.uniform(0.1, 0.9),
                'y': random.uniform(0.1, 0.9),
                'size': random.uniform(0.01, 0.02),
                'connections': [],
                'scanned': False,
                'vulnerable': random.random() < 0.3,
                'pulse': 0.0,
                'type': random.choice(['server', 'router', 'client'])
            }
            self.nodes.append(node)

        # Create connections (nearby nodes)
        for i, node in enumerate(self.nodes):
            for j, other in enumerate(self.nodes):
                if i != j:
                    dx = node['x'] - other['x']
                    dy = node['y'] - other['y']
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < 0.25 and random.random() < 0.5:
                        node['connections'].append(j)

        # Terminal output lines
        self.terminal_lines = [
            "$ nmap -sV -sC target",
            "Starting scan...",
            "Discovered host: 192.168.1.1",
            "PORT    STATE  SERVICE",
            "22/tcp  open   ssh",
            "80/tcp  open   http",
            "443/tcp open   https",
            "Scanning vulnerabilities...",
        ]

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            painter.fillPath(path, self.bg_color)

            # Draw hex grid background
            self.draw_hex_grid(painter)

            # Draw network connections
            self.draw_connections(painter)

            # Draw scan line
            self.draw_scan_line(painter)

            # Draw network nodes
            self.draw_nodes(painter)

            # Draw packets
            self.draw_packets(painter)

            # Draw terminal overlay
            self.draw_terminal(painter)

            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)

        finally:
            painter.end()

    def draw_hex_grid(self, painter):
        """Draw subtle hexagonal grid."""
        hex_color = QColor(30, 40, 50, 40)
        painter.setPen(QPen(hex_color, 1))

        hex_size = 25
        for row in range(-1, int(self.height() / (hex_size * 1.5)) + 2):
            for col in range(-1, int(self.width() / (hex_size * 1.73)) + 2):
                offset = (hex_size * 0.866) if row % 2 else 0
                cx = col * hex_size * 1.73 + offset
                cy = row * hex_size * 1.5

                # Draw hexagon
                hex_path = QPainterPath()
                for i in range(6):
                    angle = math.pi / 3 * i + math.pi / 6
                    px = cx + hex_size * 0.8 * math.cos(angle)
                    py = cy + hex_size * 0.8 * math.sin(angle)
                    if i == 0:
                        hex_path.moveTo(px, py)
                    else:
                        hex_path.lineTo(px, py)
                hex_path.closeSubpath()
                painter.drawPath(hex_path)

    def draw_connections(self, painter):
        """Draw network connections."""
        for i, node in enumerate(self.nodes):
            for j in node['connections']:
                other = self.nodes[j]

                x1 = node['x'] * self.width()
                y1 = node['y'] * self.height()
                x2 = other['x'] * self.width()
                y2 = other['y'] * self.height()

                # Color based on scan state
                if node['scanned'] and other['scanned']:
                    color = QColor(self.accent)
                    color.setAlpha(80)
                else:
                    color = QColor(self.secondary)
                    color.setAlpha(40)

                painter.setPen(QPen(color, 1))
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def draw_scan_line(self, painter):
        """Draw horizontal scanning line."""
        y = self.scan_line * self.height()

        # Scan line glow
        for offset, alpha in [(0, 150), (2, 80), (4, 40), (6, 20)]:
            color = QColor(self.accent)
            color.setAlpha(alpha)
            painter.setPen(QPen(color, 2))
            painter.drawLine(QPointF(0, y - offset), QPointF(self.width(), y - offset))
            painter.drawLine(QPointF(0, y + offset), QPointF(self.width(), y + offset))

        # Main line
        painter.setPen(QPen(self.accent, 2))
        painter.drawLine(QPointF(0, y), QPointF(self.width(), y))

    def draw_nodes(self, painter):
        """Draw network nodes."""
        for node in self.nodes:
            x = node['x'] * self.width()
            y = node['y'] * self.height()
            size = node['size'] * min(self.width(), self.height())

            # Pulse effect
            pulse_scale = 1.0 + node['pulse'] * 0.5
            size *= pulse_scale

            # Color based on state
            if node['vulnerable'] and node['scanned']:
                base_color = self.primary  # Red for vulnerable
            elif node['scanned']:
                base_color = self.accent  # Green for scanned
            else:
                base_color = self.secondary  # Blue for unscanned

            # Glow
            glow_alpha = 60 + int(node['pulse'] * 100)
            glow = QRadialGradient(x, y, size * 3)
            glow.setColorAt(0, QColor(base_color.red(), base_color.green(), base_color.blue(), glow_alpha))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), size * 3, size * 3)

            # Node shape based on type
            painter.setPen(QPen(base_color, 2))
            painter.setBrush(QColor(20, 25, 35, 200))

            if node['type'] == 'server':
                # Square for server
                painter.drawRect(QRectF(x - size, y - size, size * 2, size * 2))
            elif node['type'] == 'router':
                # Diamond for router
                diamond = QPainterPath()
                diamond.moveTo(x, y - size)
                diamond.lineTo(x + size, y)
                diamond.lineTo(x, y + size)
                diamond.lineTo(x - size, y)
                diamond.closeSubpath()
                painter.drawPath(diamond)
            else:
                # Circle for client
                painter.drawEllipse(QPointF(x, y), size, size)

            # Vulnerability indicator
            if node['vulnerable'] and node['scanned']:
                painter.setPen(QPen(self.primary, 1))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(x, y), size * 1.5, size * 1.5)

    def draw_packets(self, painter):
        """Draw network packets."""
        for packet in self.packets:
            x = packet['x'] * self.width()
            y = packet['y'] * self.height()

            # Glowing packet
            glow = QRadialGradient(x, y, 8)
            glow.setColorAt(0, QColor(self.warning.red(), self.warning.green(), self.warning.blue(), 200))
            glow.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), 8, 8)

    def draw_terminal(self, painter):
        """Draw terminal output overlay."""
        # Terminal background
        terminal_rect = QRect(10, 10, 200, 120)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.drawRoundedRect(terminal_rect, 4, 4)

        # Terminal border
        painter.setPen(QPen(self.accent, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(terminal_rect, 4, 4)

        # Terminal text
        painter.setFont(self.terminal_font)
        y_offset = 22

        visible_lines = self.terminal_lines[-8:]  # Show last 8 lines
        for i, line in enumerate(visible_lines):
            alpha = 150 + int(50 * (i / len(visible_lines)))
            if line.startswith('$'):
                color = self.accent
            elif 'open' in line or 'Discovered' in line:
                color = self.warning
            elif 'vulnerab' in line.lower():
                color = self.primary
            else:
                color = QColor(180, 180, 180)

            color.setAlpha(alpha)
            painter.setPen(color)
            painter.drawText(18, y_offset + i * 12, line[:30])

        # Blinking cursor
        if int(self.time * 2) % 2:
            painter.setPen(self.accent)
            cursor_y = y_offset + len(visible_lines) * 12
            painter.drawText(18, cursor_y, "_")

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
        title = "HackAttack"

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
        subtitle = "Penetration Testing Framework"
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle)
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + title_height + 10

        painter.setPen(QColor(200, 180, 180, int(220 * base_opacity)))
        painter.drawText(subtitle_x, subtitle_y, subtitle)

        version = "v1.0.0"
        painter.setFont(self.version_font)
        version_rect = painter.fontMetrics().boundingRect(version)
        version_x = self.width() - version_rect.width() - 30
        version_y = self.height() - 30

        painter.setPen(QColor(180, 160, 160, int(200 * base_opacity)))
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

        # Move scan line
        self.scan_line += delta_time * 0.15
        if self.scan_line > 1.0:
            self.scan_line = 0.0
            # Reset scanned states for new pass
            for node in self.nodes:
                node['scanned'] = False

        # Mark nodes as scanned when scan line passes
        for node in self.nodes:
            if node['y'] < self.scan_line and not node['scanned']:
                node['scanned'] = True
                node['pulse'] = 1.0

        # Decay pulses
        for node in self.nodes:
            node['pulse'] *= 0.95

        # Spawn packets along connections
        if random.random() < 0.05:
            node = random.choice(self.nodes)
            if node['connections']:
                target_idx = random.choice(node['connections'])
                target = self.nodes[target_idx]
                self.packets.append({
                    'x': node['x'], 'y': node['y'],
                    'target_x': target['x'], 'target_y': target['y'],
                    'progress': 0.0,
                    'speed': random.uniform(0.03, 0.06)
                })

        # Update packets
        new_packets = []
        for packet in self.packets:
            packet['progress'] += packet['speed']
            t = packet['progress']
            packet['x'] = packet['x'] + (packet['target_x'] - packet['x']) * packet['speed'] * 2
            packet['y'] = packet['y'] + (packet['target_y'] - packet['y']) * packet['speed'] * 2
            if packet['progress'] < 1.0:
                new_packets.append(packet)
        self.packets = new_packets

        # Add terminal output occasionally
        if random.random() < 0.02:
            new_lines = [
                f"Scanning port {random.randint(1, 65535)}...",
                f"Host {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)} up",
                "Service detected: " + random.choice(['ssh', 'http', 'ftp', 'mysql', 'smtp']),
                f"CVE-{random.randint(2020,2024)}-{random.randint(1000,9999)} found",
            ]
            self.terminal_lines.append(random.choice(new_lines))
            if len(self.terminal_lines) > 50:
                self.terminal_lines = self.terminal_lines[-50:]

        self.update()

    def update_status(self, message: str):
        self.status_message = message
        self.update()


class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HackAttack")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QMainWindow { background: rgb(10, 12, 18); }")

        self.main_widget = NetworkScanBackground(self)
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
