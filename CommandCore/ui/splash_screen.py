"""
CommandCore Splash Screen with particle animation.
"""
import sys
import os
import math
import random
import time
from PySide6.QtCore import (Qt, QTimer, QPointF, QRectF, QRect, QSize, 
                          Property, QLineF, QEasingCurve, QPropertyAnimation)
from PySide6.QtGui import QIcon
from PySide6.QtGui import (QPainter, QColor, QLinearGradient, QRadialGradient, 
                         QPainterPath, QBrush, QPen, QFont, QFontMetrics)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QFrame, QLabel, QSizePolicy, QDialog)


class AnimatedBackground(QWidget):
    """A widget that displays an animated background with particles."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        
        # CommandCore color scheme
        self.primary = QColor('#00a8ff')  # CommandCore blue
        self.accent = QColor('#00d2d3')   # CommandCore teal
        self.bg_color = QColor(30, 39, 46)  # Dark background
        self.secondary = QColor(0, 151, 230)  # Slightly darker blue
        
        # Animation properties
        self.time = 0.0
        self.pulse_phase = 0.0
        self.particles = []
        
        # Fonts
        self.title_font = QFont("Segoe UI", 48, QFont.Bold)
        self.subtitle_font = QFont("Segoe UI", 16)
        self.version_font = QFont("Segoe UI", 10, QFont.Bold)
        
        # Initialize particle system
        self.init_particles(200)  # Start with 200 particles
        
        # Animation timer (60fps for smoother animation)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)  # ~60fps
    
    def init_particles(self, count):
        """Initialize wireframe elements with random positions and colors."""
        self.particles = []
        
        for _ in range(count):
            # Random position within the visible area with some margin
            margin = 0.1
            x = random.uniform(-1 + margin, 1 - margin)
            y = random.uniform(-1 + margin, 1 - margin)
            
            # Subtle random movement
            vx = random.uniform(-0.002, 0.002)
            vy = random.uniform(-0.002, 0.002)
            
            # Randomly choose between primary and accent colors
            use_primary = random.random() > 0.3  # 70% primary, 30% accent
            base_color = self.primary if use_primary else self.accent
            
            # Subtle color variation
            color = QColor(base_color)
            h, s, l, _ = color.getHslF()
            color.setHslF(
                (h + random.uniform(-0.02, 0.02)) % 1.0,
                min(0.8, s * random.uniform(0.9, 1.1)),
                min(0.7, l * random.uniform(0.9, 1.1)),
                0.15  # More transparent for subtlety
            )
            
            self.particles.append({
                'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'color': color,
                'size': random.uniform(0.006, 0.01),
                'rotation': random.uniform(0, 2 * math.pi),
                'rotation_speed': random.uniform(-0.05, 0.05),
                'phase': random.uniform(0, 2 * math.pi)
            })
    
    def animate(self):
        """Update animation state."""
        self.time += 0.02
        self.pulse_phase = (self.pulse_phase + 0.005) % (2 * math.pi)
        
        # Update particle positions
        for p in self.particles:
            # Update position with boundary checking
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['rotation'] += p['rotation_speed']
            
            # Bounce off edges
            if abs(p['x']) > 1.0:
                p['x'] = 1.0 if p['x'] > 0 else -1.0
                p['vx'] *= -1
            if abs(p['y']) > 1.0:
                p['y'] = 1.0 if p['y'] > 0 else -1.0
                p['vy'] *= -1
        
        self.update()  # Trigger a repaint
    
    def paintEvent(self, event):
        """Handle paint events."""
        painter = QPainter(self)
        try:
            painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
            
            # Create a path for the rounded corners
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)
            painter.setClipPath(path)
            
            # Draw solid background
            painter.fillPath(path, self.bg_color)
            
            # Draw particles
            for p in self.particles:
                self.draw_particle(painter, p)
            
            # Draw progress bar and text if we have the animation properties
            if hasattr(self, '_animation_progress') and hasattr(self, '_text_opacity'):
                self.draw_progress_bar(painter)
                self.draw_text(painter)
            
        except Exception as e:
            print(f"Error in paintEvent: {e}")
        finally:
            painter.end()
    
    def draw_particle(self, painter, p):
        """Draw a single particle."""
        painter.save()
        
        # Calculate position
        x = (p['x'] + 1) * 0.5 * self.width()
        y = (p['y'] + 1) * 0.5 * self.height()
        size = p['size'] * min(self.width(), self.height())
        
        # Set up painter
        painter.setPen(Qt.NoPen)
        painter.setBrush(p['color'])
        
        # Draw particle
        painter.save()
        painter.translate(x, y)
        painter.rotate(p['rotation'] * 180 / math.pi)
        painter.drawEllipse(QRectF(-size/2, -size/2, size, size))
        painter.restore()
        
        painter.restore()
    
    def draw_progress_bar(self, painter):
        """Draw animated progress bar."""
        progress_height = 4
        margin = 40
        bar_width = self.width() - 2 * margin
        bar_y = self.height() - 80
        
        # Background bar
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 20))
        painter.drawRoundedRect(margin, bar_y, bar_width, progress_height, 2, 2)
        
        # Progress bar
        progress_gradient = QLinearGradient(0, 0, bar_width, 0)
        progress_gradient.setColorAt(0, self.primary)
        progress_gradient.setColorAt(1, self.accent)
        
        painter.setBrush(progress_gradient)
        progress_width = bar_width * self._animation_progress
        painter.drawRoundedRect(margin, bar_y, progress_width, progress_height, 2, 2)
    
    def draw_text(self, painter):
        """Draw text elements with animation."""
        base_opacity = self._text_opacity
        
        # Calculate vertical positions
        center_y = self.height() // 2
        title_height = 60
        
        # Draw title
        painter.setFont(self.title_font)
        title = "CommandCore"
        
        # Calculate title position (centered)
        title_rect = painter.fontMetrics().boundingRect(title)
        title_x = (self.width() - title_rect.width()) // 2
        title_y = center_y - 40  # Move up from center
        
        # Draw title with gradient
        gradient = QLinearGradient(0, 0, 0, title_height)
        gradient.setColorAt(0, self.primary)
        gradient.setColorAt(1, self.accent)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        
        # Create a path for the text to apply gradient
        path = QPainterPath()
        path.addText(title_x, title_y, self.title_font, title)
        
        # Draw the text with gradient fill
        painter.save()
        painter.setClipPath(path)
        painter.drawPath(path)
        painter.restore()
        
        # Draw version text below title
        version_text = "v1.0.0"
        painter.setFont(self.version_font)
        painter.setPen(QColor(255, 255, 255, int(200 * base_opacity)))
        
        version_rect = painter.fontMetrics().boundingRect(version_text)
        version_x = (self.width() - version_rect.width()) // 2
        version_y = title_y + title_rect.height() + 10
        
        painter.drawText(version_x, version_y, version_text)


class SplashScreen(QMainWindow):
    """Custom splash screen for the CommandCore Launcher with animated background."""
    
    def __init__(self):
        """Initialize the splash screen."""
        super().__init__()
        
        # Set window properties
        self.setFixedSize(800, 500)
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'icons', 'commandcore.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            print(f"Splash screen icon loaded from: {icon_path}")
        else:
            print(f"Warning: Icon not found at {icon_path}")
        
        # Set up main widget with animated background
        self.background = AnimatedBackground(self)
        self.setCentralWidget(self.background)
        
        # Animation properties
        self._animation_progress = 0.0
        self._text_opacity = 0.0
        
        # Center the window on screen
        self.center_on_screen()
        
        # Set up animations
        self.setup_animations()
        
        # Set up mouse tracking for window dragging
        self.dragging = False
        self.offset = None
    
    def center_on_screen(self):
        """Center the window on the screen."""
        frame_geometry = self.frameGeometry()
        screen = QApplication.primaryScreen().availableGeometry()
        frame_geometry.moveCenter(screen.center())
        self.move(frame_geometry.topLeft())
    
    # Animation properties
    def get_animation_progress(self):
        return self._animation_progress
    
    def set_animation_progress(self, value):
        self._animation_progress = value
        self.background._animation_progress = value
        self.background.update()
    
    def get_text_opacity(self):
        return self._text_opacity
    
    def set_text_opacity(self, value):
        self._text_opacity = value
        self.background._text_opacity = value
        self.background.update()
    
    animation_progress = Property(float, get_animation_progress, set_animation_progress)
    text_opacity = Property(float, get_text_opacity, set_text_opacity)
    
    def setup_animations(self):
        """Set up the splash screen animations."""
        # Start progress animation (5.9 seconds total)
        self.progress_anim = QPropertyAnimation(self, b"animation_progress")
        self.progress_anim.setDuration(5900)  # 5.9 seconds
        self.progress_anim.setStartValue(0.0)
        self.progress_anim.setEndValue(1.0)
        self.progress_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.progress_anim.start()
        
        # Text fade in animation
        self.text_fade_in = QPropertyAnimation(self, b"text_opacity")
        self.text_fade_in.setDuration(1000)  # 1 second
        self.text_fade_in.setStartValue(0.0)
        self.text_fade_in.setEndValue(1.0)
        self.text_fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self.text_fade_in.start()
    
    def finish(self, main_window):
        """Finish the splash screen animation and show the main window."""
        # Create fade out animation
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.finished.connect(lambda: self.close_splash(main_window))
        self.fade_out.start()
    
    def close_splash(self, main_window):
        """Close the splash screen and show the main window."""
        self.close()
        if main_window:
            main_window.show()
    
    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging."""
        if event.button() == Qt.LeftButton and event.y() < 32:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.pos()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging."""
        if self.dragging and hasattr(self, 'offset') and self.offset is not None:
            self.move(event.globalPosition().toPoint() - self.offset)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            if hasattr(self, 'offset'):
                self.offset = None


def show_splash_screen():
    """Show the splash screen and return the window instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = SplashScreen()
    window.show()
    
    # Ensure the window is properly centered and visible
    window.raise_()
    window.activateWindow()
    
    # Process events to make sure the window is shown
    if app:
        app.processEvents()
    
    return window


if __name__ == "__main__":
    # For testing the splash screen
    app = QApplication(sys.argv)
    
    # Create and show splash screen
    splash = show_splash_screen()
    
    # Simulate loading process
    QTimer.singleShot(3000, lambda: splash.finish(None))
    
    sys.exit(app.exec())
