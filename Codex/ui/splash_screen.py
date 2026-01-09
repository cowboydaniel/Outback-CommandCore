"""
Codex Animated Splash Screen
Matrix-style falling code with syntax highlighting colors.
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


class MatrixCodeBackground(QWidget):
    """Animated matrix-style falling code visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # Codex colors - green/cyan code theme
        self.primary = QColor('#2ecc71')    # Green (strings)
        self.accent = QColor('#3498db')     # Blue (keywords)
        self.secondary = QColor('#e74c3c')  # Red (functions)
        self.comment = QColor('#95a5a6')    # Gray (comments)
        self.number = QColor('#f39c12')     # Orange (numbers)
        self.bg_color = QColor(15, 20, 25)

        self.time = 0.0
        self.columns = []  # Falling code columns
        self.code_snippets = []  # Floating code snippets

        # Status
        self.status_message = "Loading AI models..."
        self.status_font = QFont("Arial", 9)

        # Fonts
        self.title_font = QFont("Arial", 48, QFont.Bold)
        self.subtitle_font = QFont("Arial", 14)
        self.version_font = QFont("Arial", 10, QFont.Bold)
        self.code_font = QFont("Consolas", 11)

        self.init_matrix()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def init_matrix(self):
        """Initialize falling code columns."""
        self.columns = []

        # Characters used in the matrix rain
        self.chars = "abcdefghijklmnopqrstuvwxyz0123456789{}[]();:=<>+-*/"

        # Create columns of falling characters
        num_columns = 40
        for i in range(num_columns):
            col_x = i / num_columns

            # Each column has multiple characters falling
            drops = []
            num_drops = random.randint(3, 8)
            for _ in range(num_drops):
                drops.append({
                    'y': random.uniform(-1, 1),
                    'speed': random.uniform(0.3, 0.8),
                    'chars': [random.choice(self.chars) for _ in range(random.randint(5, 15))],
                    'color_type': random.choice(['green', 'blue', 'white']),
                    'brightness': random.uniform(0.3, 1.0)
                })

            self.columns.append({
                'x': col_x,
                'drops': drops
            })

        # Floating code snippets (like syntax highlighted code)
        self.code_snippets = [
            {'text': 'def generate():', 'color': self.accent, 'x': 0.1, 'y': 0.3},
            {'text': 'return code', 'color': self.secondary, 'x': 0.7, 'y': 0.2},
            {'text': '# AI magic', 'color': self.comment, 'x': 0.5, 'y': 0.7},
            {'text': 'model.predict()', 'color': self.primary, 'x': 0.2, 'y': 0.6},
            {'text': 'for i in range:', 'color': self.accent, 'x': 0.6, 'y': 0.4},
            {'text': '"hello world"', 'color': self.primary, 'x': 0.8, 'y': 0.8},
            {'text': 'import ai', 'color': self.accent, 'x': 0.15, 'y': 0.85},
            {'text': '42', 'color': self.number, 'x': 0.4, 'y': 0.5},
        ]

        for snippet in self.code_snippets:
            snippet['base_x'] = snippet['x']
            snippet['base_y'] = snippet['y']
            snippet['phase'] = random.uniform(0, 2 * math.pi)
            snippet['alpha'] = random.uniform(0.2, 0.5)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            painter.fillPath(path, self.bg_color)

            # Draw matrix rain
            self.draw_matrix_rain(painter)

            # Draw floating code snippets
            self.draw_code_snippets(painter)

            # Draw glow effect in center
            self.draw_center_glow(painter)

            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)

        finally:
            painter.end()

    def draw_matrix_rain(self, painter):
        """Draw falling code characters."""
        painter.setFont(self.code_font)

        for col in self.columns:
            x = col['x'] * self.width()

            for drop in col['drops']:
                # Draw trail of characters
                for i, char in enumerate(drop['chars']):
                    char_y = (drop['y'] - i * 0.03) * self.height()

                    if char_y < 0 or char_y > self.height():
                        continue

                    # Fade based on position in trail (head is brightest)
                    trail_fade = 1.0 - (i / len(drop['chars']))
                    alpha = int(255 * drop['brightness'] * trail_fade * 0.7)

                    if drop['color_type'] == 'green':
                        color = QColor(46, 204, 113, alpha)
                    elif drop['color_type'] == 'blue':
                        color = QColor(52, 152, 219, alpha)
                    else:
                        color = QColor(255, 255, 255, alpha)

                    # Head character is extra bright
                    if i == 0:
                        color = QColor(200, 255, 200, min(255, alpha + 100))

                    painter.setPen(color)
                    painter.drawText(QPointF(x, char_y), char)

    def draw_code_snippets(self, painter):
        """Draw floating syntax-highlighted code snippets."""
        painter.setFont(self.code_font)

        for snippet in self.code_snippets:
            x = snippet['x'] * self.width()
            y = snippet['y'] * self.height()

            # Pulsing alpha
            pulse = 0.7 + 0.3 * math.sin(self.time * 2 + snippet['phase'])
            alpha = int(255 * snippet['alpha'] * pulse)

            # Draw glow behind text
            glow_color = QColor(snippet['color'])
            glow_color.setAlpha(alpha // 3)
            glow = QRadialGradient(x + 40, y, 60)
            glow.setColorAt(0, glow_color)
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(QPointF(x + 40, y), 60, 20)

            # Draw text
            text_color = QColor(snippet['color'])
            text_color.setAlpha(alpha)
            painter.setPen(text_color)
            painter.drawText(QPointF(x, y), snippet['text'])

    def draw_center_glow(self, painter):
        """Draw ambient glow in the center."""
        center_x = self.width() / 2
        center_y = self.height() / 2

        pulse = 0.8 + 0.2 * math.sin(self.time * 1.5)

        glow = QRadialGradient(center_x, center_y, 200 * pulse)
        glow.setColorAt(0, QColor(46, 204, 113, 30))
        glow.setColorAt(0.5, QColor(52, 152, 219, 15))
        glow.setColorAt(1, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(center_x, center_y), 200, 150)

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
        title = "CODEX"

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
        subtitle = "AI-Powered Code Generation"
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

        # Update matrix rain
        for col in self.columns:
            for drop in col['drops']:
                drop['y'] += drop['speed'] * delta_time

                # Reset when off screen
                if drop['y'] > 1.5:
                    drop['y'] = random.uniform(-0.5, -0.1)
                    drop['speed'] = random.uniform(0.3, 0.8)
                    drop['chars'] = [random.choice(self.chars) for _ in range(random.randint(5, 15))]
                    drop['brightness'] = random.uniform(0.3, 1.0)

                # Randomly change characters
                if random.random() < 0.05:
                    idx = random.randint(0, len(drop['chars']) - 1)
                    drop['chars'][idx] = random.choice(self.chars)

        # Float code snippets
        for snippet in self.code_snippets:
            snippet['x'] = snippet['base_x'] + 0.02 * math.sin(self.time * 0.5 + snippet['phase'])
            snippet['y'] = snippet['base_y'] + 0.01 * math.cos(self.time * 0.7 + snippet['phase'])

        self.update()

    def update_status(self, message: str):
        self.status_message = message
        self.update()


class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Codex")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QMainWindow { background: rgb(15, 20, 25); }")

        self.main_widget = MatrixCodeBackground(self)
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
