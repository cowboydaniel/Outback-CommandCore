"""
NIGHTFIRE Animated Splash Screen
Active defense theme with rising flame particles and radar sweep.
"""

import sys
import math
import random
import time
from PySide6.QtCore import (Qt, QTimer, QRectF, QRect, QPointF,
                          Property, QEasingCurve, QPropertyAnimation)
from PySide6.QtGui import (QPainter, QColor, QLinearGradient, QRadialGradient,
                         QPainterPath, QPen, QFont, QConicalGradient)
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget


class FlameRadarBackground(QWidget):
    """Animated flames with radar sweep for active defense visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # NIGHTFIRE colors - fire/ember theme
        self.primary = QColor('#ff6b35')    # Orange fire
        self.accent = QColor('#f7931e')     # Bright orange
        self.secondary = QColor('#c0392b')  # Deep red
        self.ember = QColor('#ff4757')      # Red ember
        self.bg_color = QColor(15, 10, 20)  # Dark purple-black

        self.time = 0.0
        self.flame_particles = []
        self.embers = []
        self.radar_angle = 0.0
        self.threats = []  # Detected threats on radar
        self.shield_pulse = 0.0

        # Status
        self.status_message = "Initializing defense systems..."
        self.status_font = QFont("Arial", 9)

        # Fonts
        self.title_font = QFont("Arial", 48, QFont.Bold)
        self.subtitle_font = QFont("Arial", 14)
        self.version_font = QFont("Arial", 10, QFont.Bold)

        self.init_effects()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def init_effects(self):
        """Initialize flame and radar effects."""
        # Flame particles rising from bottom
        self.flame_particles = []
        for _ in range(80):
            self.spawn_flame_particle()

        # Floating embers
        self.embers = []
        for _ in range(30):
            self.embers.append({
                'x': random.uniform(0, 1),
                'y': random.uniform(0, 1),
                'vx': random.uniform(-0.002, 0.002),
                'vy': random.uniform(-0.005, -0.001),
                'size': random.uniform(1, 3),
                'life': random.uniform(0, 1),
                'flicker': random.uniform(0, 2 * math.pi)
            })

        # Threats on radar
        self.threats = []
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0.3, 0.9)
            self.threats.append({
                'angle': angle,
                'distance': distance,
                'detected': False,
                'pulse': 0.0
            })

    def spawn_flame_particle(self):
        """Create a new flame particle."""
        self.flame_particles.append({
            'x': random.uniform(0.2, 0.8),
            'y': 1.1,
            'vx': random.uniform(-0.003, 0.003),
            'vy': random.uniform(-0.015, -0.008),
            'size': random.uniform(8, 20),
            'life': 1.0,
            'color_phase': random.uniform(0, 1),
            'wobble': random.uniform(0, 2 * math.pi)
        })

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            painter.fillPath(path, self.bg_color)

            # Draw ambient heat glow at bottom
            self.draw_heat_glow(painter)

            # Draw flames
            self.draw_flames(painter)

            # Draw embers
            self.draw_embers(painter)

            # Draw radar
            self.draw_radar(painter)

            # Draw shield effect
            self.draw_shield(painter)

            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)

        finally:
            painter.end()

    def draw_heat_glow(self, painter):
        """Draw ambient heat glow at bottom."""
        glow = QLinearGradient(0, self.height(), 0, self.height() * 0.5)
        glow.setColorAt(0, QColor(255, 100, 50, 60))
        glow.setColorAt(0.3, QColor(200, 50, 30, 30))
        glow.setColorAt(1, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawRect(0, int(self.height() * 0.5), self.width(), int(self.height() * 0.5))

    def draw_flames(self, painter):
        """Draw rising flame particles."""
        for particle in self.flame_particles:
            x = particle['x'] * self.width()
            y = particle['y'] * self.height()
            size = particle['size'] * particle['life']

            # Color based on life (white -> yellow -> orange -> red)
            life = particle['life']
            if life > 0.7:
                color = QColor(255, 255, 200, int(200 * life))  # White/yellow core
            elif life > 0.4:
                t = (life - 0.4) / 0.3
                color = QColor(255, int(150 + 105 * t), int(50 * t), int(180 * life))  # Orange
            else:
                color = QColor(200, 50, 30, int(150 * life))  # Red

            # Draw flame particle with glow
            glow = QRadialGradient(x, y, size * 1.5)
            glow.setColorAt(0, color)
            glow.setColorAt(0.5, QColor(color.red(), color.green() // 2, 0, color.alpha() // 2))
            glow.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), size * 1.5, size * 2)

    def draw_embers(self, painter):
        """Draw floating ember particles."""
        for ember in self.embers:
            x = ember['x'] * self.width()
            y = ember['y'] * self.height()

            # Flickering brightness
            flicker = 0.5 + 0.5 * math.sin(self.time * 10 + ember['flicker'])
            alpha = int(200 * ember['life'] * flicker)

            color = QColor(255, int(150 * flicker), 50, alpha)

            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y), ember['size'], ember['size'])

            # Tiny glow
            glow = QRadialGradient(x, y, ember['size'] * 3)
            glow.setColorAt(0, QColor(255, 100, 50, alpha // 3))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x, y), ember['size'] * 3, ember['size'] * 3)

    def draw_radar(self, painter):
        """Draw radar sweep in corner."""
        # Radar position and size
        radar_x = self.width() - 100
        radar_y = 100
        radar_radius = 70

        # Radar background
        painter.setPen(Qt.NoPen)
        radar_bg = QRadialGradient(radar_x, radar_y, radar_radius)
        radar_bg.setColorAt(0, QColor(20, 30, 25, 200))
        radar_bg.setColorAt(1, QColor(10, 15, 12, 220))
        painter.setBrush(radar_bg)
        painter.drawEllipse(QPointF(radar_x, radar_y), radar_radius, radar_radius)

        # Radar rings
        painter.setBrush(Qt.NoBrush)
        for ring in [0.33, 0.66, 1.0]:
            painter.setPen(QPen(QColor(self.primary.red(), self.primary.green(), self.primary.blue(), 50), 1))
            painter.drawEllipse(QPointF(radar_x, radar_y), radar_radius * ring, radar_radius * ring)

        # Cross lines
        painter.setPen(QPen(QColor(100, 120, 100, 60), 1))
        painter.drawLine(QPointF(radar_x - radar_radius, radar_y), QPointF(radar_x + radar_radius, radar_y))
        painter.drawLine(QPointF(radar_x, radar_y - radar_radius), QPointF(radar_x, radar_y + radar_radius))

        # Radar sweep
        sweep_gradient = QConicalGradient(radar_x, radar_y, -math.degrees(self.radar_angle))
        sweep_gradient.setColorAt(0, QColor(self.primary.red(), self.primary.green(), self.primary.blue(), 150))
        sweep_gradient.setColorAt(0.1, QColor(self.primary.red(), self.primary.green(), self.primary.blue(), 50))
        sweep_gradient.setColorAt(0.2, QColor(0, 0, 0, 0))
        sweep_gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(sweep_gradient)
        painter.drawEllipse(QPointF(radar_x, radar_y), radar_radius - 2, radar_radius - 2)

        # Sweep line
        end_x = radar_x + radar_radius * math.cos(self.radar_angle)
        end_y = radar_y + radar_radius * math.sin(self.radar_angle)
        painter.setPen(QPen(self.primary, 2))
        painter.drawLine(QPointF(radar_x, radar_y), QPointF(end_x, end_y))

        # Draw threats
        for threat in self.threats:
            if threat['detected']:
                tx = radar_x + radar_radius * threat['distance'] * math.cos(threat['angle'])
                ty = radar_y + radar_radius * threat['distance'] * math.sin(threat['angle'])

                # Pulsing threat indicator
                pulse_size = 4 + threat['pulse'] * 3
                alpha = int(200 * (0.5 + threat['pulse'] * 0.5))

                painter.setPen(Qt.NoPen)
                glow = QRadialGradient(tx, ty, pulse_size * 2)
                glow.setColorAt(0, QColor(255, 50, 50, alpha))
                glow.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setBrush(glow)
                painter.drawEllipse(QPointF(tx, ty), pulse_size * 2, pulse_size * 2)

                painter.setBrush(QColor(255, 100, 100, alpha))
                painter.drawEllipse(QPointF(tx, ty), pulse_size, pulse_size)

        # Radar border
        painter.setPen(QPen(self.primary, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(radar_x, radar_y), radar_radius, radar_radius)

    def draw_shield(self, painter):
        """Draw shield pulse effect around center."""
        if self.shield_pulse > 0:
            center_x = self.width() / 2
            center_y = self.height() / 2
            radius = 150 + (1 - self.shield_pulse) * 50

            alpha = int(100 * self.shield_pulse)
            painter.setPen(QPen(QColor(self.primary.red(), self.primary.green(), self.primary.blue(), alpha), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(center_x, center_y), radius, radius * 0.6)

    def draw_progress_bar(self, painter):
        progress_height = 4
        margin = 40
        bar_width = self.width() - 2 * margin
        bar_y = self.height() - 80

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawRoundedRect(margin, bar_y, bar_width, progress_height, 2, 2)

        progress_gradient = QLinearGradient(0, 0, bar_width, 0)
        progress_gradient.setColorAt(0, self.secondary)
        progress_gradient.setColorAt(0.5, self.primary)
        progress_gradient.setColorAt(1, self.accent)

        painter.setBrush(progress_gradient)
        progress_width = bar_width * self._animation_progress
        painter.drawRoundedRect(margin, bar_y, progress_width, progress_height, 2, 2)

    def draw_text(self, painter):
        base_opacity = self._text_opacity
        center_y = self.height() // 2
        title_height = 60

        painter.setFont(self.title_font)
        title = "NIGHTFIRE"

        title_rect = painter.fontMetrics().boundingRect(title)
        title_x = (self.width() - title_rect.width()) // 2
        title_y = center_y - 40

        gradient = QLinearGradient(0, 0, 0, title_height)
        gradient.setColorAt(0, self.accent)
        gradient.setColorAt(0.5, self.primary)
        gradient.setColorAt(1, self.secondary)
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
        subtitle = "Real-Time Active Defense"
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

        painter.setPen(QColor(230, 180, 160, int(200 * base_opacity)))
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

        # Update flame particles
        for particle in self.flame_particles:
            wobble = math.sin(self.time * 5 + particle['wobble']) * 0.002
            particle['x'] += particle['vx'] + wobble
            particle['y'] += particle['vy']
            particle['life'] -= delta_time * 0.5

        # Remove dead particles and spawn new ones
        self.flame_particles = [p for p in self.flame_particles if p['life'] > 0]
        while len(self.flame_particles) < 80:
            self.spawn_flame_particle()

        # Update embers
        for ember in self.embers:
            ember['x'] += ember['vx']
            ember['y'] += ember['vy']
            ember['life'] -= delta_time * 0.2

            if ember['life'] <= 0 or ember['y'] < 0:
                ember['x'] = random.uniform(0.2, 0.8)
                ember['y'] = random.uniform(0.8, 1.0)
                ember['life'] = 1.0

        # Rotate radar
        self.radar_angle += delta_time * 2

        # Check for threat detection
        for threat in self.threats:
            angle_diff = abs(((self.radar_angle - threat['angle'] + math.pi) % (2 * math.pi)) - math.pi)
            if angle_diff < 0.2:
                threat['detected'] = True
                threat['pulse'] = 1.0

            # Decay pulse
            threat['pulse'] *= 0.97

        # Shield pulse
        if random.random() < 0.01:
            self.shield_pulse = 1.0
        self.shield_pulse *= 0.95

        self.update()

    def update_status(self, message: str):
        self.status_message = message
        self.update()


class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NIGHTFIRE")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QMainWindow { background: rgb(15, 10, 20); }")

        self.main_widget = FlameRadarBackground(self)
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
