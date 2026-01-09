"""
BLACKSTORM Animated Splash Screen
Storm themed animation with lightning bolts and data particles disintegrating.
"""

import sys
import math
import random
import time
from PySide6.QtCore import (Qt, QTimer, QRectF, QRect, QPointF,
                          Property, QEasingCurve, QPropertyAnimation)
from PySide6.QtGui import (QPainter, QColor, QLinearGradient, QRadialGradient,
                         QPainterPath, QPen, QFont, QPolygonF)
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget


class StormBackground(QWidget):
    """Animated storm with lightning and disintegrating data particles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # BLACKSTORM colors - dark purple/electric blue storm theme
        self.primary = QColor('#8e44ad')  # Purple
        self.accent = QColor('#3498db')   # Electric blue
        self.lightning = QColor('#f39c12')  # Lightning yellow
        self.bg_color = QColor(15, 15, 25)  # Very dark

        self.time = 0.0
        self.particles = []  # Data fragments
        self.lightning_bolts = []  # Active lightning
        self.rain_drops = []  # Background rain effect

        # Status
        self.status_message = "Initializing secure wipe protocols..."
        self.status_font = QFont("Arial", 9)

        # Fonts
        self.title_font = QFont("Arial", 44, QFont.Bold)
        self.subtitle_font = QFont("Arial", 14)
        self.version_font = QFont("Arial", 10, QFont.Bold)

        self.init_storm()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def init_storm(self):
        """Initialize storm elements."""
        # Data particles that will disintegrate
        self.particles = []
        for _ in range(60):
            self.particles.append({
                'x': random.uniform(-1, 1),
                'y': random.uniform(-1, 1),
                'vx': random.uniform(-0.01, 0.01),
                'vy': random.uniform(0.005, 0.02),  # Falling down
                'size': random.uniform(2, 6),
                'char': random.choice('01'),  # Binary data
                'alpha': random.uniform(0.3, 0.8),
                'disintegrating': False,
                'disintegrate_progress': 0.0
            })

        # Rain drops for atmosphere
        self.rain_drops = []
        for _ in range(100):
            self.rain_drops.append({
                'x': random.uniform(0, 1),
                'y': random.uniform(0, 1),
                'speed': random.uniform(0.02, 0.05),
                'length': random.uniform(5, 15)
            })

    def create_lightning(self, start_x=None, start_y=None):
        """Generate a lightning bolt path."""
        if start_x is None:
            start_x = random.uniform(0.2, 0.8)
        if start_y is None:
            start_y = 0.0

        points = [(start_x, start_y)]
        current_x, current_y = start_x, start_y

        while current_y < 1.0:
            # Jagged movement
            current_x += random.uniform(-0.1, 0.1)
            current_y += random.uniform(0.05, 0.15)
            current_x = max(0.1, min(0.9, current_x))
            points.append((current_x, current_y))

            # Chance to branch
            if random.random() < 0.2 and len(points) > 2:
                branch_points = [(current_x, current_y)]
                bx, by = current_x, current_y
                for _ in range(random.randint(2, 4)):
                    bx += random.uniform(-0.15, 0.15)
                    by += random.uniform(0.05, 0.1)
                    branch_points.append((bx, by))

        return {
            'points': points,
            'branches': [],
            'lifetime': 0.3,
            'age': 0.0,
            'intensity': 1.0
        }

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)

            # Draw gradient storm background
            bg_gradient = QLinearGradient(0, 0, 0, self.height())
            bg_gradient.setColorAt(0, QColor(20, 15, 35))
            bg_gradient.setColorAt(0.5, QColor(15, 15, 25))
            bg_gradient.setColorAt(1, QColor(10, 10, 20))
            painter.fillPath(path, bg_gradient)

            # Draw storm clouds at top
            self.draw_clouds(painter)

            # Draw rain
            self.draw_rain(painter)

            # Draw data particles
            self.draw_particles(painter)

            # Draw lightning
            self.draw_lightning(painter)

            # Draw flash effect when lightning strikes
            self.draw_flash(painter)

            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)

        finally:
            painter.end()

    def draw_clouds(self, painter):
        """Draw animated storm clouds."""
        cloud_y = self.height() * 0.1

        for i in range(5):
            offset = math.sin(self.time * 0.3 + i) * 20
            cx = self.width() * (0.1 + i * 0.2) + offset
            cy = cloud_y + math.sin(self.time * 0.5 + i * 0.5) * 10

            cloud_gradient = QRadialGradient(cx, cy, 80)
            cloud_gradient.setColorAt(0, QColor(60, 50, 80, 100))
            cloud_gradient.setColorAt(0.5, QColor(40, 35, 60, 60))
            cloud_gradient.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(cloud_gradient)
            painter.drawEllipse(QPointF(cx, cy), 100, 40)

    def draw_rain(self, painter):
        """Draw falling rain."""
        rain_color = QColor(100, 120, 180, 40)
        painter.setPen(QPen(rain_color, 1))

        for drop in self.rain_drops:
            x = drop['x'] * self.width()
            y = drop['y'] * self.height()
            length = drop['length']

            painter.drawLine(QPointF(x, y), QPointF(x - 2, y + length))

    def draw_particles(self, painter):
        """Draw data particles/fragments."""
        data_font = QFont("Consolas", 10)
        painter.setFont(data_font)

        for p in self.particles:
            x = (p['x'] * 0.5 + 0.5) * self.width()
            y = (p['y'] * 0.5 + 0.5) * self.height()

            if p['disintegrating']:
                # Disintegration effect - scatter into smaller pieces
                progress = p['disintegrate_progress']
                alpha = int(255 * p['alpha'] * (1 - progress))

                # Draw fragmenting character
                for j in range(3):
                    offset_x = math.sin(progress * 10 + j) * progress * 30
                    offset_y = math.cos(progress * 10 + j) * progress * 20 + progress * 50

                    frag_color = QColor(self.accent)
                    frag_color.setAlpha(max(0, alpha - j * 30))
                    painter.setPen(frag_color)
                    painter.drawText(QPointF(x + offset_x, y + offset_y), p['char'])
            else:
                # Normal particle
                alpha = int(255 * p['alpha'])
                glow = QRadialGradient(x, y, p['size'] * 3)
                glow.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), alpha))
                glow.setColorAt(1, QColor(0, 0, 0, 0))

                painter.setPen(Qt.NoPen)
                painter.setBrush(glow)
                painter.drawEllipse(QPointF(x, y), p['size'] * 2, p['size'] * 2)

                # Draw binary character
                char_color = QColor(180, 200, 255, alpha)
                painter.setPen(char_color)
                painter.drawText(QPointF(x - 4, y + 4), p['char'])

    def draw_lightning(self, painter):
        """Draw lightning bolts."""
        for bolt in self.lightning_bolts:
            progress = bolt['age'] / bolt['lifetime']
            alpha = int(255 * (1 - progress) * bolt['intensity'])

            if alpha <= 0:
                continue

            # Main bolt
            points = bolt['points']
            for i in range(len(points) - 1):
                x1 = points[i][0] * self.width()
                y1 = points[i][1] * self.height()
                x2 = points[i + 1][0] * self.width()
                y2 = points[i + 1][1] * self.height()

                # Glow effect
                for width, a_mult in [(8, 0.2), (4, 0.5), (2, 1.0)]:
                    color = QColor(self.lightning)
                    color.setAlpha(int(alpha * a_mult))
                    painter.setPen(QPen(color, width))
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def draw_flash(self, painter):
        """Draw screen flash effect during lightning."""
        total_flash = 0
        for bolt in self.lightning_bolts:
            if bolt['age'] < 0.1:
                total_flash += (0.1 - bolt['age']) / 0.1 * 0.3

        if total_flash > 0:
            flash_color = QColor(255, 255, 255, int(min(100, 255 * total_flash)))
            painter.fillRect(0, 0, self.width(), self.height(), flash_color)

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
        title = "BLACKSTORM"

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
        subtitle = "Forensic & Secure Wipe Utility"
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle)
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + title_height + 10

        painter.setPen(QColor(180, 180, 220, int(220 * base_opacity)))
        painter.drawText(subtitle_x, subtitle_y, subtitle)

        version = "v1.0.0"
        painter.setFont(self.version_font)
        version_rect = painter.fontMetrics().boundingRect(version)
        version_x = self.width() - version_rect.width() - 30
        version_y = self.height() - 30

        painter.setPen(QColor(160, 160, 200, int(200 * base_opacity)))
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

        # Update rain
        for drop in self.rain_drops:
            drop['y'] += drop['speed']
            if drop['y'] > 1:
                drop['y'] = 0
                drop['x'] = random.uniform(0, 1)

        # Update particles
        for p in self.particles:
            if p['disintegrating']:
                p['disintegrate_progress'] += delta_time * 2
                if p['disintegrate_progress'] >= 1.0:
                    # Reset particle
                    p['x'] = random.uniform(-1, 1)
                    p['y'] = random.uniform(-1, -0.5)
                    p['disintegrating'] = False
                    p['disintegrate_progress'] = 0.0
                    p['alpha'] = random.uniform(0.3, 0.8)
            else:
                p['x'] += p['vx']
                p['y'] += p['vy']

                # Trigger disintegration randomly or at bottom
                if p['y'] > 0.8 or (random.random() < 0.002):
                    p['disintegrating'] = True

                # Wrap around
                if p['y'] > 1.2:
                    p['y'] = -1
                    p['x'] = random.uniform(-1, 1)

        # Spawn lightning occasionally
        if random.random() < 0.02:
            self.lightning_bolts.append(self.create_lightning())

        # Update lightning
        new_bolts = []
        for bolt in self.lightning_bolts:
            bolt['age'] += delta_time
            if bolt['age'] < bolt['lifetime']:
                new_bolts.append(bolt)
        self.lightning_bolts = new_bolts

        self.update()

    def update_status(self, message: str):
        self.status_message = message
        self.update()


class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLACKSTORM")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QMainWindow { background: rgb(15, 15, 25); }")

        self.main_widget = StormBackground(self)
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
