"""
Vantage Animated Background
A smooth animated background with particles and progress animation.
"""

import sys
import math
import random
import time
from PySide6.QtCore import (Qt, QTimer, QPointF, QRectF, QRect, QSize, 
                          Property, QLineF, QEasingCurve, QPropertyAnimation)
from PySide6.QtGui import (QPainter, QColor, QLinearGradient, QRadialGradient, 
                         QPainterPath, QBrush, QPen, QFont, QFontMetrics)
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout

class AnimatedBackground(QWidget):
    """A widget that displays an animated background with particles."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        
        # Vantage color scheme
        self.primary = QColor('#00a8ff')  # Vantage blue
        self.accent = QColor('#00d2d3')   # Vantage teal
        self.bg_color = QColor(30, 39, 46)  # Exact Vantage background color
        self.secondary = QColor(0, 151, 230)  # Slightly darker blue
        
        # Animation properties
        self.time = 0.0
        self.pulse_phase = 0.0
        self.particles = []
        
        # Status message
        self.status_message = "Initializing..."
        self.status_font = QFont("Arial", 9)
        self.status_opacity = 0.8
        
        # Fonts
        self.title_font = QFont("Arial", 48, QFont.Bold)
        self.subtitle_font = QFont("Arial", 16)
        self.version_font = QFont("Arial", 10, QFont.Bold)
        
        # Initialize particle system
        self.init_particles(200)  # Start with 200 particles
        
        # Animation timer (60fps for smoother animation)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)  # ~60fps
    
    def init_particles(self, count):
        """Initialize wireframe elements with random positions and Vantage colors."""
        self.particles = []
        
        for _ in range(count):
            # Random position within the visible area with some margin
            margin = 0.1
            x = random.uniform(-1 + margin, 1 - margin)
            y = random.uniform(-1 + margin, 1 - margin)
            
            # Subtle random movement (increased speed)
            vx = random.uniform(-0.002, 0.002)  # Increased from 0.001 to 0.002
            vy = random.uniform(-0.002, 0.002)  # Increased from 0.001 to 0.002
            
            # Randomly choose between primary and accent colors
            use_primary = random.random() > 0.3  # 70% primary, 30% accent
            base_color = self.primary if use_primary else self.accent
            
            # Subtle color variation
            color = QColor(base_color)
            h, s, l, _ = color.getHslF()
            color.setHslF(
                (h + random.uniform(-0.02, 0.02)) % 1.0,  # Small hue variation
                min(0.8, s * random.uniform(0.9, 1.1)),  # Slight saturation variation
                min(0.7, l * random.uniform(0.9, 1.1)),  # Slight lightness variation
                0.15  # More transparent for subtlety
            )
            
            self.particles.append({
                'x': x, 'y': y,
                'vx': vx, 'vy': vy,
                'color': color,
                'size': random.uniform(0.006, 0.01),  # Smaller size for more subtlety
                'rotation': random.uniform(0, 2 * math.pi),
                'rotation_speed': random.uniform(-0.05, 0.05),  # Very slow rotation
                'phase': random.uniform(0, 2 * math.pi)
            })
    
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
            
            # Get parent window for animation properties
            parent = self.parent()
            if hasattr(parent, '_animation_progress') and hasattr(parent, '_text_opacity'):
                self._animation_progress = parent._animation_progress
                self._text_opacity = parent._text_opacity
                
                # Draw progress bar and text if we have the animation properties
                self.draw_progress_bar(painter)
                self.draw_text(painter)
            
        except Exception as e:
            print(f"Error in paintEvent: {e}")
        finally:
            painter.end()
    
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
        title = "VANTAGE"
        
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
        
        # Create and draw text path for gradient fill
        path = QPainterPath()
        path.addText(0, 0, self.title_font, title)
        
        # Position and draw the title
        painter.save()
        painter.translate(title_x, title_y)
        painter.setOpacity(base_opacity)
        painter.drawPath(path)
        painter.restore()
        
        # Draw subtitle
        painter.setFont(self.subtitle_font)
        subtitle = "Device Intelligence Platform"
        subtitle_rect = painter.fontMetrics().boundingRect(subtitle)
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + title_height + 10
        
        painter.setPen(QColor(200, 200, 255, int(220 * base_opacity)))
        painter.drawText(subtitle_x, subtitle_y, subtitle)
        
        # Draw version in bottom right
        version = "v1.0.0"
        painter.setFont(self.version_font)
        version_rect = painter.fontMetrics().boundingRect(version)
        version_x = self.width() - version_rect.width() - 30
        version_y = self.height() - 30
        
        painter.setPen(QColor(180, 220, 255, int(200 * base_opacity)))
        painter.drawText(version_x, version_y, version)
        
        # Draw status message in bottom left
        if hasattr(self, 'status_message'):
            painter.setFont(self.status_font)
            status_rect = painter.fontMetrics().boundingRect(self.status_message)
            status_x = 30
            status_y = self.height() - 30
            
            # Draw semi-transparent background for better readability
            bg_rect = QRect(
                status_x - 5, 
                status_y - status_rect.height() - 5, 
                status_rect.width() + 10, 
                status_rect.height() + 10
            )
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 120))  # Semi-transparent black
            painter.drawRoundedRect(bg_rect, 4, 4)
            
            # Draw status text
            painter.setPen(QColor(220, 220, 220, int(220 * base_opacity * self.status_opacity)))
            painter.drawText(status_x, status_y, self.status_message)
    
    def update_status(self, message: str):
        """Update the status message in the splash screen.
        
        Args:
            message: The status message to display
        """
        self.status_message = message
        self.update()  # Trigger a repaint
    
    def animate(self):
        """Update animation state."""
        current_time = time.time()
        if not hasattr(self, 'last_frame_time'):
            self.last_frame_time = current_time
        delta_time = min(0.1, current_time - self.last_frame_time)
        self.last_frame_time = current_time
        self.time += delta_time
        
        # Update particles
        for p in self.particles:
            # Add subtle noise-based movement (increased speed)
            noise = math.sin(self.time * 0.3 + p['phase'] * 2) * 0.0008  # Increased frequency and amplitude
            p['x'] += (p['vx'] * 1.5 + noise) * delta_time * 15  # Increased speed
            p['y'] += (p['vy'] * 1.5 + noise) * delta_time * 15  # Increased speed
            
            # Very slow rotation
            p['rotation'] += p['rotation_speed'] * delta_time * 5
            
            # Gentle boundary wrapping
            if abs(p['x']) > 1.2:
                p['x'] = -p['x'] * 0.9
            if abs(p['y']) > 1.2:
                p['y'] = -p['y'] * 0.9
        
        self.update()
    
    def draw_particle(self, painter, p):
        """Draw a wireframe element with subtle glow."""
        # Convert normalized coordinates to screen coordinates
        x = (p['x'] * 0.5 + 0.5) * self.width()
        y = (p['y'] * 0.5 + 0.5) * self.height()
        size = p['size'] * min(self.width(), self.height())
        
        # Get base color with very subtle pulsing alpha
        base_alpha = 20 + 5 * math.sin(self.time * 0.2 + p['phase'] * 2)
        color = QColor(p['color'])
        color.setAlphaF(color.alphaF() * (base_alpha / 255.0))
        
        painter.save()
        painter.translate(x, y)
        painter.rotate(p['rotation'] * 180 / math.pi)
        
        # Draw a subtle glow behind the point
        glow = QRadialGradient(0, 0, size * 3)
        glow.setColorAt(0, color.lighter(150))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        
        # Draw the point
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QRectF(-size*1.5, -size*1.5, size*3, size*3))
        
        # Draw connecting lines to nearby points
        line_color = QColor(color)
        line_color.setAlphaF(color.alphaF() * 0.7)  # Slightly more transparent lines
        
        # Only draw lines for points that are close to each other
        for other in self.particles:
            if p == other:
                continue
                
            dx = p['x'] - other['x']
            dy = p['y'] - other['y']
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Only connect very close points
            if distance < 0.15:  # Reduced connection distance for cleaner look
                # Calculate target position
                tx = (other['x'] * 0.5 + 0.5) * self.width()
                ty = (other['y'] * 0.5 + 0.5) * self.height()
                
                # Calculate line properties based on distance
                line_width = 0.2 + (1 - distance/0.15) * 0.3  # Very thin lines
                line_alpha = 0.1 + (1 - distance/0.15) * 0.3  # Very subtle alpha
                
                # Draw a subtle line with glow
                line = QLineF(0, 0, tx - x, ty - y)
                pen = QPen(line_color, line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                pen.setColor(QColor(line_color.red(), line_color.green(), line_color.blue(), int(255 * line_alpha * color.alphaF())))
                painter.setPen(pen)
                painter.drawLine(line)
        
        # Draw a small point in the center
        painter.setPen(Qt.NoPen)
        painter.setBrush(color.lighter(120))
        painter.drawEllipse(QRectF(-size*0.7, -size*0.7, size*1.4, size*1.4))
        
        painter.restore()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vantage Background")
        self.setGeometry(100, 100, 800, 500)  # Match splash screen size
        
        # Set window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Set a solid background color
        self.setStyleSheet("""
            QMainWindow {
                background: rgb(30, 39, 46);
                border: none;
                border-radius: 20px;
            }
        """)
        
        # Set up main widget
        self.main_widget = AnimatedBackground(self)
        self.setCentralWidget(self.main_widget)
        
        # Animation properties
        self._animation_progress = 0.0
        self._text_opacity = 0.0
        
        # Start progress animation
        self.progress_anim = QPropertyAnimation(self, b"animation_progress")
        self.progress_anim.setDuration(5900)  # 5.9 seconds to match splash screen display time
        self.progress_anim.setStartValue(0.0)
        self.progress_anim.setEndValue(1.0)
        self.progress_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.progress_anim.start()
        
        # Text fade in animation
        self.text_fade_in = QPropertyAnimation(self, b"text_opacity")
        self.text_fade_in.setDuration(1000)
        self.text_fade_in.setStartValue(0.0)
        self.text_fade_in.setEndValue(1.0)
        self.text_fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self.text_fade_in.start()
        
        # Set up mouse tracking for window dragging
        self.dragging = False
        self.offset = None
    
    # Animation properties
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
    
    # Animation properties
    animation_progress = Property(float, get_animation_progress, set_animation_progress)
    text_opacity = Property(float, get_text_opacity, set_text_opacity)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() < 32:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging and hasattr(self, 'offset') and self.offset is not None:
            self.move(event.globalPosition().toPoint() - self.offset)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            if hasattr(self, 'offset'):
                self.offset = None
    
    def update_status(self, message: str):
        """Update the status message in the splash screen.
        
        Args:
            message: The status message to display
        """
        if hasattr(self, 'main_widget') and hasattr(self.main_widget, 'update_status'):
            self.main_widget.update_status(message)


def show_splash_screen():
    """Create and show the splash screen.
    
    Returns:
        MainWindow: The splash screen window instance
    """
    window = MainWindow()
    
    # Center the window on the screen
    frame_geometry = window.frameGeometry()
    screen = QApplication.primaryScreen().availableGeometry()
    frame_geometry.moveCenter(screen.center())
    window.move(frame_geometry.topLeft())
    
    window.show()
    return window

if __name__ == "__main__":
    # Set up the application
    app = QApplication(sys.argv)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Run the application
    sys.exit(app.exec())
