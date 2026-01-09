"""
PC-X Animated Splash Screen
System tools theme with rotating gears and circuit board patterns.
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


class GearCircuitBackground(QWidget):
    """Animated gears and circuit board visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # PC-X colors - industrial/mechanical theme
        self.primary = QColor('#3498db')    # Steel blue
        self.accent = QColor('#2ecc71')     # Green (success/active)
        self.secondary = QColor('#95a5a6')  # Gray (metal)
        self.copper = QColor('#e67e22')     # Copper traces
        self.bg_color = QColor(20, 25, 30)

        self.time = 0.0
        self.gears = []
        self.circuit_nodes = []
        self.circuit_traces = []
        self.data_pulses = []  # Pulses traveling along traces

        # Status
        self.status_message = "Loading system tools..."
        self.status_font = QFont("Arial", 9)

        # Fonts
        self.title_font = QFont("Arial", 48, QFont.Bold)
        self.subtitle_font = QFont("Arial", 14)
        self.version_font = QFont("Arial", 10, QFont.Bold)

        self.init_elements()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def init_elements(self):
        """Initialize gears and circuit elements."""
        # Create gears
        self.gears = [
            {'x': 0.15, 'y': 0.3, 'radius': 0.08, 'teeth': 12, 'angle': 0, 'speed': 1.0, 'direction': 1},
            {'x': 0.22, 'y': 0.45, 'radius': 0.05, 'teeth': 8, 'angle': 0, 'speed': 1.6, 'direction': -1},
            {'x': 0.85, 'y': 0.25, 'radius': 0.07, 'teeth': 10, 'angle': 0, 'speed': 1.2, 'direction': 1},
            {'x': 0.78, 'y': 0.4, 'radius': 0.04, 'teeth': 6, 'angle': 0, 'speed': 2.0, 'direction': -1},
            {'x': 0.12, 'y': 0.7, 'radius': 0.06, 'teeth': 9, 'angle': 0, 'speed': 1.3, 'direction': 1},
            {'x': 0.88, 'y': 0.65, 'radius': 0.055, 'teeth': 8, 'angle': 0, 'speed': 1.5, 'direction': -1},
        ]

        # Create circuit nodes (chips/components)
        self.circuit_nodes = []
        for _ in range(15):
            self.circuit_nodes.append({
                'x': random.uniform(0.25, 0.75),
                'y': random.uniform(0.2, 0.8),
                'size': random.uniform(0.015, 0.025),
                'type': random.choice(['chip', 'capacitor', 'resistor']),
                'active': False,
                'pulse': 0.0
            })

        # Create circuit traces connecting nodes
        self.circuit_traces = []
        for i, node in enumerate(self.circuit_nodes):
            # Connect to 1-2 nearby nodes
            connections = random.randint(1, 2)
            for _ in range(connections):
                target_idx = random.randint(0, len(self.circuit_nodes) - 1)
                if target_idx != i:
                    target = self.circuit_nodes[target_idx]
                    # Create orthogonal trace (like PCB)
                    mid_x = node['x'] if random.random() < 0.5 else target['x']
                    mid_y = target['y'] if mid_x == node['x'] else node['y']

                    self.circuit_traces.append({
                        'points': [(node['x'], node['y']), (mid_x, mid_y), (target['x'], target['y'])],
                        'from_node': i,
                        'to_node': target_idx
                    })

    def create_gear_path(self, cx, cy, radius, teeth, angle):
        """Create a gear shape path."""
        path = QPainterPath()

        inner_radius = radius * 0.7
        tooth_height = radius * 0.15

        points_per_tooth = 4
        total_points = teeth * points_per_tooth

        for i in range(total_points):
            tooth_idx = i // points_per_tooth
            point_in_tooth = i % points_per_tooth

            base_angle = angle + (2 * math.pi * tooth_idx / teeth)

            if point_in_tooth == 0:
                r = inner_radius
                a = base_angle - (math.pi / teeth) * 0.4
            elif point_in_tooth == 1:
                r = radius + tooth_height
                a = base_angle - (math.pi / teeth) * 0.2
            elif point_in_tooth == 2:
                r = radius + tooth_height
                a = base_angle + (math.pi / teeth) * 0.2
            else:
                r = inner_radius
                a = base_angle + (math.pi / teeth) * 0.4

            px = cx + r * math.cos(a)
            py = cy + r * math.sin(a)

            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)

        path.closeSubpath()

        # Add center hole
        hole_path = QPainterPath()
        hole_path.addEllipse(QPointF(cx, cy), radius * 0.2, radius * 0.2)
        path = path.subtracted(hole_path)

        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            painter.fillPath(path, self.bg_color)

            # Draw circuit board background pattern
            self.draw_circuit_background(painter)

            # Draw circuit traces
            self.draw_traces(painter)

            # Draw data pulses
            self.draw_pulses(painter)

            # Draw circuit nodes
            self.draw_nodes(painter)

            # Draw gears
            self.draw_gears(painter)

            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)

        finally:
            painter.end()

    def draw_circuit_background(self, painter):
        """Draw subtle circuit board grid pattern."""
        grid_color = QColor(40, 50, 45, 30)
        painter.setPen(QPen(grid_color, 1))

        # Vertical lines
        spacing = 20
        for x in range(0, self.width(), spacing):
            if x % 60 == 0:
                painter.setPen(QPen(QColor(50, 60, 55, 50), 1))
            else:
                painter.setPen(QPen(grid_color, 1))
            painter.drawLine(x, 0, x, self.height())

        # Horizontal lines
        for y in range(0, self.height(), spacing):
            if y % 60 == 0:
                painter.setPen(QPen(QColor(50, 60, 55, 50), 1))
            else:
                painter.setPen(QPen(grid_color, 1))
            painter.drawLine(0, y, self.width(), y)

    def draw_traces(self, painter):
        """Draw circuit board traces."""
        for trace in self.circuit_traces:
            points = trace['points']

            # Draw copper trace
            trace_color = QColor(self.copper)
            trace_color.setAlpha(100)

            for i in range(len(points) - 1):
                x1, y1 = points[i][0] * self.width(), points[i][1] * self.height()
                x2, y2 = points[i+1][0] * self.width(), points[i+1][1] * self.height()

                # Draw trace with slight glow
                for width, alpha in [(4, 30), (2, 100)]:
                    color = QColor(self.copper)
                    color.setAlpha(alpha)
                    painter.setPen(QPen(color, width))
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def draw_pulses(self, painter):
        """Draw data pulses traveling along traces."""
        for pulse in self.data_pulses:
            trace = self.circuit_traces[pulse['trace_idx']]
            points = trace['points']

            # Calculate position along trace
            total_length = 0
            segments = []
            for i in range(len(points) - 1):
                dx = points[i+1][0] - points[i][0]
                dy = points[i+1][1] - points[i][1]
                length = math.sqrt(dx*dx + dy*dy)
                segments.append((length, i))
                total_length += length

            target_dist = pulse['progress'] * total_length
            current_dist = 0

            px, py = points[0]
            for length, seg_idx in segments:
                if current_dist + length >= target_dist:
                    t = (target_dist - current_dist) / length if length > 0 else 0
                    px = points[seg_idx][0] + t * (points[seg_idx+1][0] - points[seg_idx][0])
                    py = points[seg_idx][1] + t * (points[seg_idx+1][1] - points[seg_idx][1])
                    break
                current_dist += length

            x = px * self.width()
            y = py * self.height()

            # Draw glowing pulse
            glow = QRadialGradient(x, y, 10)
            glow.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 200))
            glow.setColorAt(0.5, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), 100))
            glow.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), 10, 10)

    def draw_nodes(self, painter):
        """Draw circuit components."""
        for node in self.circuit_nodes:
            x = node['x'] * self.width()
            y = node['y'] * self.height()
            size = node['size'] * min(self.width(), self.height())

            # Pulse effect
            pulse_scale = 1.0 + node['pulse'] * 0.3
            size *= pulse_scale

            # Glow when active
            if node['active'] or node['pulse'] > 0:
                glow_alpha = int(100 * max(0.3, node['pulse']))
                glow = QRadialGradient(x, y, size * 2)
                glow.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), glow_alpha))
                glow.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(glow)
                painter.drawEllipse(QPointF(x, y), size * 2, size * 2)

            if node['type'] == 'chip':
                # Draw IC chip
                painter.setPen(QPen(self.secondary, 1))
                painter.setBrush(QColor(30, 35, 40))
                painter.drawRect(QRectF(x - size, y - size * 0.6, size * 2, size * 1.2))

                # Pins
                pin_color = QColor(self.copper)
                pin_color.setAlpha(180)
                painter.setPen(QPen(pin_color, 2))
                for i in range(4):
                    px = x - size * 0.6 + i * size * 0.4
                    painter.drawLine(QPointF(px, y - size * 0.6), QPointF(px, y - size * 0.9))
                    painter.drawLine(QPointF(px, y + size * 0.6), QPointF(px, y + size * 0.9))

            elif node['type'] == 'capacitor':
                # Draw capacitor
                painter.setPen(QPen(self.secondary, 2))
                painter.setBrush(QColor(40, 45, 50))
                painter.drawEllipse(QPointF(x, y), size * 0.5, size * 0.5)
                painter.drawLine(QPointF(x, y - size * 0.5), QPointF(x, y - size))
                painter.drawLine(QPointF(x, y + size * 0.5), QPointF(x, y + size))

            else:  # resistor
                # Draw resistor
                painter.setPen(QPen(self.secondary, 2))
                painter.setBrush(QColor(60, 50, 40))
                painter.drawRoundedRect(QRectF(x - size, y - size * 0.3, size * 2, size * 0.6), 2, 2)

    def draw_gears(self, painter):
        """Draw rotating gears."""
        for gear in self.gears:
            cx = gear['x'] * self.width()
            cy = gear['y'] * self.height()
            radius = gear['radius'] * min(self.width(), self.height())

            # Create gear path
            gear_path = self.create_gear_path(cx, cy, radius, gear['teeth'], gear['angle'])

            # Gear gradient
            gear_gradient = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 1.5)
            gear_gradient.setColorAt(0, QColor(80, 90, 100))
            gear_gradient.setColorAt(0.5, QColor(50, 60, 70))
            gear_gradient.setColorAt(1, QColor(35, 40, 50))

            painter.setPen(QPen(QColor(100, 110, 120), 2))
            painter.setBrush(gear_gradient)
            painter.drawPath(gear_path)

            # Highlight
            highlight = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 0.8)
            highlight.setColorAt(0, QColor(255, 255, 255, 30))
            highlight.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(highlight)
            painter.drawEllipse(QPointF(cx, cy), radius * 0.6, radius * 0.6)

            # Center bolt
            painter.setPen(QPen(QColor(60, 70, 80), 1))
            painter.setBrush(QColor(40, 45, 55))
            painter.drawEllipse(QPointF(cx, cy), radius * 0.15, radius * 0.15)

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
        title = "PC-X"

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
        subtitle = "Linux System Management"
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle)
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + title_height + 10

        painter.setPen(QColor(180, 200, 220, int(220 * base_opacity)))
        painter.drawText(subtitle_x, subtitle_y, subtitle)

        version = "v1.0.0"
        painter.setFont(self.version_font)
        version_rect = painter.fontMetrics().boundingRect(version)
        version_x = self.width() - version_rect.width() - 30
        version_y = self.height() - 30

        painter.setPen(QColor(160, 180, 200, int(200 * base_opacity)))
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

        # Rotate gears
        for gear in self.gears:
            gear['angle'] += gear['speed'] * gear['direction'] * delta_time

        # Decay node pulses
        for node in self.circuit_nodes:
            node['pulse'] *= 0.95

        # Spawn data pulses
        if random.random() < 0.05 and self.circuit_traces:
            trace_idx = random.randint(0, len(self.circuit_traces) - 1)
            self.data_pulses.append({
                'trace_idx': trace_idx,
                'progress': 0.0,
                'speed': random.uniform(0.02, 0.04)
            })

        # Update pulses
        new_pulses = []
        for pulse in self.data_pulses:
            pulse['progress'] += pulse['speed']
            if pulse['progress'] < 1.0:
                new_pulses.append(pulse)
            else:
                # Pulse reached destination - light up target node
                trace = self.circuit_traces[pulse['trace_idx']]
                target_node = self.circuit_nodes[trace['to_node']]
                target_node['pulse'] = 1.0
                target_node['active'] = True
        self.data_pulses = new_pulses

        self.update()

    def update_status(self, message: str):
        self.status_message = message
        self.update()


class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC-X")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QMainWindow { background: rgb(20, 25, 30); }")

        self.main_widget = GearCircuitBackground(self)
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
