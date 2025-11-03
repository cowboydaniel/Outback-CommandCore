"""
Dashboard tab for the CommandCore Launcher.
"""
from PySide6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QPushButton, 
                             QHBoxLayout, QFrame, QSizePolicy, QTabWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QColor, QLinearGradient, QPainter


class DashboardCard(QFrame):
    """A card widget for the dashboard."""
    
    def __init__(self, title, description, parent=None):
        """Initialize the dashboard card."""
        super().__init__(parent)
        self.setObjectName("dashboardCard")
        
        # Set up the card
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(120)
        
        # Style
        self.setStyleSheet("""
            #dashboardCard {
                background-color: #3A3A3A;
                border: 1px solid #4A4A4A;
                border-radius: 8px;
                padding: 16px;
            }
            
            #dashboardCard:hover {
                border-color: #00a8ff;
            }
            
            .card-title {
                color: #ECF0F1;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 8px;
            }
            
            .card-description {
                color: #B0B0B0;
                font-size: 13px;
            }
            
            .card-button {
                background-color: #00a8ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                margin-top: 12px;
                font-weight: 500;
            }
            
            .card-button:hover {
                background-color: #0095e0;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setProperty("class", "card-title")
        
        # Description
        self.desc_label = QLabel(description)
        self.desc_label.setWordWrap(True)
        self.desc_label.setProperty("class", "card-description")
        
        # Button
        self.button = QPushButton("Open")
        self.button.setProperty("class", "card-button")
        
        # Add widgets to layout
        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
        layout.addWidget(self.button, 0, Qt.AlignRight)


class DashboardTab(QWidget):
    """Dashboard tab implementation for the CommandCore Launcher."""
    
    # Signal to request tab change
    request_tab_change = Signal(str)
    
    def __init__(self, parent=None):
        """Initialize the tab."""
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(24)
        
        # Welcome section
        welcome_layout = QVBoxLayout()
        welcome_layout.setSpacing(8)
        
        welcome_title = QLabel("Welcome to CommandCore")
        welcome_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #ECF0F1;
        """)
        
        welcome_subtitle = QLabel("Your central hub for system management and control")
        welcome_subtitle.setStyleSheet("""
            font-size: 14px;
            color: #B0B0B0;
        """)
        
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_subtitle)
        main_layout.addLayout(welcome_layout)
        
        # Cards section
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        # Card 1 - System Status
        self.card1 = DashboardCard(
            "System Status",
            "View and manage system resources, performance metrics, and hardware information.",
            self
        )
        
        # Card 2 - Application Manager
        self.card2 = DashboardCard(
            "Application Manager",
            "Launch, monitor, and manage your installed applications and services.",
            self
        )
        self.card2.button.clicked.connect(lambda: self.request_tab_change.emit("Application Manager"))
        
        # Card 3 - Settings
        self.card3 = DashboardCard(
            "Settings",
            "Configure application preferences, themes, and system settings.",
            self
        )
        
        cards_layout.addWidget(self.card1)
        cards_layout.addWidget(self.card2)
        cards_layout.addWidget(self.card3)
        
        main_layout.addLayout(cards_layout)
        main_layout.addStretch()
        
        # Status bar
        status_bar = QFrame()
        status_bar.setFrameShape(QFrame.StyledPanel)
        status_bar.setStyleSheet("""
            background-color: #2A2D2E;
            border: 1px solid #3E3E3E;
            border-radius: 4px;
            padding: 8px 16px;
        """)
        
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        status_label = QLabel("Ready")
        status_label.setStyleSheet("color: #B0B0B0; font-size: 12px;")
        
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #808080; font-size: 12px;")
        status_layout.addWidget(version_label)
        
        main_layout.addWidget(status_bar)
