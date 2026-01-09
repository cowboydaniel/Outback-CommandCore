"""
ARES-i Animated Splash Screen
Neural network themed animation with pulsing nodes and connections.
"""

import sys
import math
import random
import time
from PySide6.QtCore import (Qt, QTimer, QRectF, QRect, QPointF,
                          Property, QLineF, QEasingCurve, QPropertyAnimation)
from PySide6.QtGui import (QPainter, QColor, QLinearGradient, QRadialGradient,
                         QPainterPath, QPen, QFont)
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget


class NeuralNetworkBackground(QWidget):
    """Animated neural network visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # ARES-i colors - warm orange/red for AI research
        self.primary = QColor('#ff6b35')  # Orange
        self.accent = QColor('#f7c59f')   # Light peach
        self.secondary = QColor('#e63946')  # Red
        self.bg_color = QColor(25, 25, 35)

        self.time = 0.0
        self.nodes = []
        self.connections = []
        self.pulses = []  # Traveling pulses along connections

        # Status
        self.status_message = "Initializing neural networks..."
        self.status_font = QFont("Arial", 9)

        # Fonts
        self.title_font = QFont("Arial", 48, QFont.Bold)
        self.subtitle_font = QFont("Arial", 14)
        self.version_font = QFont("Arial", 10, QFont.Bold)

        self.init_network()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def init_network(self):
        """Create neural network nodes in layers."""
        self.nodes = []
        self.connections = []

        # Create layered structure (like a neural network)
        layers = [4, 6, 8, 6, 4]  # Nodes per layer
        layer_spacing = 1.6 / (len(layers) + 1)

        node_id = 0
        layer_nodes = []

        for layer_idx, node_count in enumerate(layers):
            layer_x = -0.8 + (layer_idx + 1) * layer_spacing
            current_layer = []

            for i in range(node_count):
                # Distribute nodes vertically
                y_spacing = 1.4 / (node_count + 1)
                y = -0.7 + (i + 1) * y_spacing

                # Add some randomness
                x = layer_x + random.uniform(-0.05, 0.05)
                y += random.uniform(-0.03, 0.03)

                node = {
                    'id': node_id,
                    'x': x, 'y': y,
                    'base_x': x, 'base_y': y,
                    'size': random.uniform(0.015, 0.025),
                    'phase': random.uniform(0, 2 * math.pi),
                    'pulse_intensity': 0.0,
                    'layer': layer_idx
                }
                self.nodes.append(node)
                current_layer.append(node_id)
                node_id += 1

            # Connect to previous layer
            if layer_nodes:
                prev_layer = layer_nodes[-1]
                for prev_id in prev_layer:
                    for curr_id in current_layer:
                        if random.random() < 0.6:  # 60% connection chance
                            self.connections.append({
                                'from': prev_id,
                                'to': curr_id,
                                'strength': random.uniform(0.3, 1.0)
                            })

            layer_nodes.append(current_layer)

        # Add some scattered background nodes
        for _ in range(30):
            self.nodes.append({
                'id': node_id,
                'x': random.uniform(-1, 1),
                'y': random.uniform(-1, 1),
                'base_x': random.uniform(-1, 1),
                'base_y': random.uniform(-1, 1),
                'size': random.uniform(0.005, 0.01),
                'phase': random.uniform(0, 2 * math.pi),
                'pulse_intensity': 0.0,
                'layer': -1  # Background node
            })
            node_id += 1

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            painter.fillPath(path, self.bg_color)

            # Draw connections first (behind nodes)
            self.draw_connections(painter)

            # Draw pulses traveling along connections
            self.draw_pulses(painter)

            # Draw nodes
            self.draw_nodes(painter)

            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)

        finally:
            painter.end()

    def draw_connections(self, painter):
        """Draw neural network connections."""
        for conn in self.connections:
            from_node = self.nodes[conn['from']]
            to_node = self.nodes[conn['to']]

            x1 = (from_node['x'] * 0.4 + 0.5) * self.width()
            y1 = (from_node['y'] * 0.4 + 0.5) * self.height()
            x2 = (to_node['x'] * 0.4 + 0.5) * self.width()
            y2 = (to_node['y'] * 0.4 + 0.5) * self.height()

            # Pulsing opacity based on time
            pulse = 0.3 + 0.2 * math.sin(self.time * 2 + from_node['phase'])
            alpha = int(255 * conn['strength'] * pulse * 0.3)

            color = QColor(self.primary)
            color.setAlpha(alpha)

            pen = QPen(color, 1.0)
            painter.setPen(pen)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def draw_pulses(self, painter):
        """Draw traveling pulses along connections."""
        for pulse in self.pulses:
            conn = self.connections[pulse['conn_idx']]
            from_node = self.nodes[conn['from']]
            to_node = self.nodes[conn['to']]

            x1 = (from_node['x'] * 0.4 + 0.5) * self.width()
            y1 = (from_node['y'] * 0.4 + 0.5) * self.height()
            x2 = (to_node['x'] * 0.4 + 0.5) * self.width()
            y2 = (to_node['y'] * 0.4 + 0.5) * self.height()

            # Interpolate position
            t = pulse['progress']
            px = x1 + (x2 - x1) * t
            py = y1 + (y2 - y1) * t

            # Draw glowing pulse
            glow = QRadialGradient(px, py, 8)
            glow.setColorAt(0, QColor(255, 200, 100, 200))
            glow.setColorAt(0.5, QColor(255, 150, 50, 100))
            glow.setColorAt(1, QColor(255, 100, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(px, py), 8, 8)

    def draw_nodes(self, painter):
        """Draw neural network nodes."""
        for node in self.nodes:
            x = (node['x'] * 0.4 + 0.5) * self.width()
            y = (node['y'] * 0.4 + 0.5) * self.height()

            # Pulsing size
            pulse = 1.0 + 0.3 * math.sin(self.time * 3 + node['phase'])
            size = node['size'] * min(self.width(), self.height()) * pulse

            # Intensity affects color
            intensity = node['pulse_intensity']

            if node['layer'] >= 0:
                # Network nodes - brighter
                glow = QRadialGradient(x, y, size * 2)
                core_color = QColor(self.primary).lighter(120 + int(80 * intensity))
                glow.setColorAt(0, core_color)
                glow.setColorAt(0.4, self.primary)
                glow.setColorAt(1, QColor(0, 0, 0, 0))
            else:
                # Background nodes - dimmer
                glow = QRadialGradient(x, y, size * 1.5)
                glow.setColorAt(0, QColor(100, 100, 120, 60))
                glow.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), size * 2, size * 2)

            # Core dot for main nodes
            if node['layer'] >= 0:
                painter.setBrush(QColor(255, 255, 255, 200))
                painter.drawEllipse(QPointF(x, y), size * 0.3, size * 0.3)

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
        title = "ARES-i"

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
        subtitle = "AI-Powered Research & Analysis"
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle)
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + title_height + 10

        painter.setPen(QColor(255, 200, 180, int(220 * base_opacity)))
        painter.drawText(subtitle_x, subtitle_y, subtitle)

        version = "v1.0.0"
        painter.setFont(self.version_font)
        version_rect = painter.fontMetrics().boundingRect(version)
        version_x = self.width() - version_rect.width() - 30
        version_y = self.height() - 30

        painter.setPen(QColor(200, 180, 160, int(200 * base_opacity)))
        painter.drawText(version_x, version_y, version)

        # Status message
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

        # Animate nodes with subtle floating motion
        for node in self.nodes:
            if node['layer'] >= 0:
                node['x'] = node['base_x'] + 0.02 * math.sin(self.time * 0.5 + node['phase'])
                node['y'] = node['base_y'] + 0.02 * math.cos(self.time * 0.7 + node['phase'])

            # Decay pulse intensity
            node['pulse_intensity'] *= 0.95

        # Spawn new pulses occasionally
        if random.random() < 0.1 and self.connections:
            conn_idx = random.randint(0, len(self.connections) - 1)
            self.pulses.append({
                'conn_idx': conn_idx,
                'progress': 0.0,
                'speed': random.uniform(0.02, 0.04)
            })

        # Update pulses
        new_pulses = []
        for pulse in self.pulses:
            pulse['progress'] += pulse['speed']
            if pulse['progress'] < 1.0:
                new_pulses.append(pulse)
            else:
                # Pulse reached destination - light up the node
                conn = self.connections[pulse['conn_idx']]
                self.nodes[conn['to']]['pulse_intensity'] = 1.0
        self.pulses = new_pulses

        self.update()

    def update_status(self, message: str):
        self.status_message = message
        self.update()


class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARES-i")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QMainWindow { background: rgb(25, 25, 35); }")

        self.main_widget = NeuralNetworkBackground(self)
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
