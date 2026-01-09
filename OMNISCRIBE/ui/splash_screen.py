"""
OMNISCRIBE Animated Splash Screen
Transcription theme with sound waveforms and speech-to-text visualization.
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


class WaveformBackground(QWidget):
    """Animated sound waveforms and transcription visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # OMNISCRIBE colors - voice/audio theme (purple/pink)
        self.primary = QColor('#9b59b6')    # Purple
        self.accent = QColor('#e91e63')     # Pink
        self.secondary = QColor('#3498db')  # Blue
        self.text_color = QColor('#00bcd4')  # Cyan for text
        self.bg_color = QColor(18, 18, 28)

        self.time = 0.0
        self.waveform_data = []  # Main waveform
        self.mini_waveforms = []  # Small floating waveforms
        self.text_particles = []  # Text appearing from speech
        self.frequency_bars = []  # Frequency spectrum bars

        # Status
        self.status_message = "Loading speech recognition models..."
        self.status_font = QFont("Arial", 9)

        # Fonts
        self.title_font = QFont("Arial", 44, QFont.Bold)
        self.subtitle_font = QFont("Arial", 14)
        self.version_font = QFont("Arial", 10, QFont.Bold)
        self.transcript_font = QFont("Georgia", 11, QFont.Normal, True)

        self.init_waveforms()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)

    def init_waveforms(self):
        """Initialize waveform data."""
        # Main waveform - multiple frequencies combined
        self.waveform_data = []
        for i in range(200):
            self.waveform_data.append({
                'base': i / 200,
                'amplitude': random.uniform(0.3, 1.0),
                'frequency': random.uniform(0.5, 2.0),
                'phase': random.uniform(0, 2 * math.pi)
            })

        # Floating mini waveforms
        self.mini_waveforms = []
        for _ in range(5):
            self.mini_waveforms.append({
                'x': random.uniform(0.1, 0.9),
                'y': random.uniform(0.15, 0.35),
                'width': random.uniform(0.1, 0.2),
                'amplitude': random.uniform(0.02, 0.04),
                'speed': random.uniform(0.5, 1.5),
                'phase': random.uniform(0, 2 * math.pi),
                'alpha': random.uniform(0.3, 0.6)
            })

        # Frequency spectrum bars
        self.frequency_bars = []
        num_bars = 32
        for i in range(num_bars):
            self.frequency_bars.append({
                'x': i / num_bars,
                'height': random.uniform(0.1, 0.5),
                'target_height': random.uniform(0.1, 0.5),
                'phase': random.uniform(0, 2 * math.pi)
            })

        # Text particles (words appearing)
        self.transcript_words = ["transcribing", "audio", "speech", "voice", "text", "words"]
        self.text_particles = []

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            painter.fillPath(path, self.bg_color)

            # Draw frequency bars at bottom
            self.draw_frequency_bars(painter)

            # Draw mini floating waveforms
            self.draw_mini_waveforms(painter)

            # Draw main waveform
            self.draw_main_waveform(painter)

            # Draw text particles
            self.draw_text_particles(painter)

            # Draw microphone icon
            self.draw_microphone(painter)

            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                self.draw_progress_bar(painter)
                self.draw_text(painter)

        finally:
            painter.end()

    def draw_frequency_bars(self, painter):
        """Draw frequency spectrum bars."""
        bar_area_height = self.height() * 0.15
        bar_area_y = self.height() - bar_area_height - 100

        num_bars = len(self.frequency_bars)
        bar_width = self.width() / num_bars * 0.7
        spacing = self.width() / num_bars

        for i, bar in enumerate(self.frequency_bars):
            x = i * spacing + spacing * 0.15
            height = bar['height'] * bar_area_height

            # Gradient from primary to accent
            t = i / num_bars
            color = QColor(
                int(self.primary.red() * (1-t) + self.accent.red() * t),
                int(self.primary.green() * (1-t) + self.accent.green() * t),
                int(self.primary.blue() * (1-t) + self.accent.blue() * t),
                150
            )

            # Bar gradient
            bar_gradient = QLinearGradient(0, bar_area_y, 0, bar_area_y + bar_area_height)
            bar_gradient.setColorAt(0, color)
            bar_gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 50))

            painter.setPen(Qt.NoPen)
            painter.setBrush(bar_gradient)
            painter.drawRoundedRect(QRectF(x, bar_area_y + bar_area_height - height,
                                          bar_width, height), 2, 2)

    def draw_mini_waveforms(self, painter):
        """Draw floating mini waveforms."""
        for wave in self.mini_waveforms:
            start_x = wave['x'] * self.width()
            y = wave['y'] * self.height()
            width = wave['width'] * self.width()

            path = QPainterPath()
            first = True

            for i in range(50):
                t = i / 49
                x = start_x + t * width
                wave_y = y + math.sin(t * 10 + self.time * wave['speed'] + wave['phase']) * wave['amplitude'] * self.height()

                if first:
                    path.moveTo(x, wave_y)
                    first = False
                else:
                    path.lineTo(x, wave_y)

            color = QColor(self.secondary)
            color.setAlphaF(wave['alpha'] * 0.5)
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

    def draw_main_waveform(self, painter):
        """Draw the main animated waveform."""
        center_y = self.height() * 0.5
        amplitude = self.height() * 0.08

        # Draw multiple overlapping waveforms for richness
        for layer in range(3):
            path = QPainterPath()
            first = True

            layer_offset = layer * 0.5
            layer_alpha = 0.8 - layer * 0.25

            for i, point in enumerate(self.waveform_data):
                x = point['base'] * self.width()

                # Combine multiple sine waves for organic movement
                y_offset = 0
                y_offset += math.sin(self.time * 2 + point['phase'] + layer_offset) * point['amplitude']
                y_offset += math.sin(self.time * 3.7 + point['phase'] * 2) * point['amplitude'] * 0.5
                y_offset += math.sin(self.time * 1.3 + point['base'] * 10) * 0.3

                y = center_y + y_offset * amplitude

                if first:
                    path.moveTo(x, y)
                    first = False
                else:
                    path.lineTo(x, y)

            # Color based on layer
            if layer == 0:
                color = QColor(self.primary)
            elif layer == 1:
                color = QColor(self.accent)
            else:
                color = QColor(self.secondary)

            color.setAlphaF(layer_alpha)
            painter.setPen(QPen(color, 3 - layer))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        # Draw glow under waveform
        glow = QRadialGradient(self.width() / 2, center_y, self.width() * 0.4)
        glow.setColorAt(0, QColor(self.primary.red(), self.primary.green(), self.primary.blue(), 30))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(self.width() / 2, center_y), self.width() * 0.4, amplitude * 2)

    def draw_text_particles(self, painter):
        """Draw text appearing from transcription."""
        painter.setFont(self.transcript_font)

        for particle in self.text_particles:
            x = particle['x'] * self.width()
            y = particle['y'] * self.height()

            alpha = int(255 * particle['alpha'])
            color = QColor(self.text_color)
            color.setAlpha(alpha)

            painter.setPen(color)
            painter.drawText(QPointF(x, y), particle['text'])

    def draw_microphone(self, painter):
        """Draw animated microphone icon."""
        mic_x = 50
        mic_y = self.height() // 2
        mic_height = 30
        mic_width = 15

        # Pulsing glow
        pulse = 0.7 + 0.3 * math.sin(self.time * 3)
        glow = QRadialGradient(mic_x, mic_y, 40 * pulse)
        glow.setColorAt(0, QColor(self.accent.red(), self.accent.green(), self.accent.blue(), int(60 * pulse)))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(mic_x, mic_y), 40, 40)

        # Microphone body
        painter.setPen(QPen(self.accent, 2))
        painter.setBrush(QColor(30, 30, 40))

        # Mic head (rounded rectangle)
        mic_rect = QRectF(mic_x - mic_width/2, mic_y - mic_height/2, mic_width, mic_height)
        painter.drawRoundedRect(mic_rect, mic_width/2, mic_width/2)

        # Mic stand
        painter.drawLine(QPointF(mic_x, mic_y + mic_height/2),
                        QPointF(mic_x, mic_y + mic_height/2 + 15))
        painter.drawLine(QPointF(mic_x - 10, mic_y + mic_height/2 + 15),
                        QPointF(mic_x + 10, mic_y + mic_height/2 + 15))

        # Sound waves emanating
        for i in range(3):
            wave_alpha = int(150 * (1 - i/3) * pulse)
            wave_color = QColor(self.accent)
            wave_color.setAlpha(wave_alpha)
            painter.setPen(QPen(wave_color, 1))
            painter.setBrush(Qt.NoBrush)

            arc_rect = QRectF(mic_x + 10 + i * 8, mic_y - 15 - i * 5,
                             20 + i * 10, 30 + i * 10)
            painter.drawArc(arc_rect, -60 * 16, 120 * 16)

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
        title = "OMNISCRIBE"

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
        subtitle = "Transcription & Analysis"
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle)
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + title_height + 10

        painter.setPen(QColor(220, 180, 255, int(220 * base_opacity)))
        painter.drawText(subtitle_x, subtitle_y, subtitle)

        version = "v1.0.0"
        painter.setFont(self.version_font)
        version_rect = painter.fontMetrics().boundingRect(version)
        version_x = self.width() - version_rect.width() - 30
        version_y = self.height() - 30

        painter.setPen(QColor(200, 160, 230, int(200 * base_opacity)))
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

        # Update waveform amplitudes
        for point in self.waveform_data:
            point['amplitude'] += (random.uniform(0.3, 1.0) - point['amplitude']) * 0.1

        # Update frequency bars
        for bar in self.frequency_bars:
            # Randomly change target
            if random.random() < 0.1:
                bar['target_height'] = random.uniform(0.1, 0.8)
            # Smoothly animate to target
            bar['height'] += (bar['target_height'] - bar['height']) * 0.15

        # Update mini waveforms
        for wave in self.mini_waveforms:
            wave['phase'] += delta_time * wave['speed']

        # Spawn text particles occasionally
        if random.random() < 0.03:
            self.text_particles.append({
                'text': random.choice(self.transcript_words),
                'x': random.uniform(0.3, 0.8),
                'y': 0.6,
                'vy': -0.02,
                'alpha': 1.0
            })

        # Update text particles
        new_particles = []
        for particle in self.text_particles:
            particle['y'] += particle['vy'] * delta_time * 10
            particle['alpha'] -= delta_time * 0.3
            if particle['alpha'] > 0:
                new_particles.append(particle)
        self.text_particles = new_particles

        self.update()

    def update_status(self, message: str):
        self.status_message = message
        self.update()


class SplashScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OMNISCRIBE")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QMainWindow { background: rgb(18, 18, 28); }")

        self.main_widget = WaveformBackground(self)
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
