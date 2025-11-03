# CommandCore Suite UI/UX Style Guide

This document outlines the design system and coding standards for all applications in the CommandCore Suite to ensure consistency across the platform.

## Table of Contents
1. [Color Scheme](#color-scheme)
2. [Typography](#typography)
3. [Layout & Spacing](#layout--spacing)
4. [UI Components](#ui-components)
5. [Animation & Transitions](#animation--transitions)
6. [Code Structure](#code-structure)
7. [Documentation Standards](#documentation-standards)

## Color Scheme

### Primary Colors
- **CommandCore Blue**: `#00a8ff` (Primary action buttons, highlights)
- **CommandCore Teal**: `#00d2d3` (Secondary actions, accents)
- **Background Dark**: `#2A2D2E` (Main background)
- **Background Light**: `#3A3A3A` (Cards, panels)
- **Text Primary**: `#ECF0F1` (Main text)
- **Text Secondary**: `#B0B0B0` (Secondary text, labels)
- **Success**: `#00d4aa` (Positive actions, success states)
- **Warning**: `#ffbe0b` (Warnings, non-critical alerts)
- **Error**: `#ff6b6b` (Errors, destructive actions)

## Typography

### Font Family
- **Primary**: 'Segoe UI', Arial, sans-serif
- **Monospace**: 'Consolas', 'Monaco', 'Courier New', monospace

### Font Weights
- **Light**: 300
- **Regular**: 400
- **Medium**: 500
- **Bold**: 700

### Font Sizes
- **H1**: 28px (Main titles)
- **H2**: 22px (Section headers)
- **H3**: 18px (Subsection headers)
- **Body**: 14px (Main content)
- **Small**: 12px (Labels, captions)
- **Tiny**: 10px (Status text, timestamps)

## Layout & Spacing

### Grid System
- **Base Unit**: 8px
- **Container Padding**: 24px
- **Section Spacing**: 40px
- **Element Spacing**: 16px
- **Dense Spacing**: 8px
- **Border Radius**: 4px (standard), 8px (panels), 12px (cards)

### Shadows
- **Small**: `0 1px 3px rgba(0, 0, 0, 0.12)`
- **Medium**: `0 4px 6px rgba(0, 0, 0, 0.1)`
- **Large**: `0 10px 25px rgba(0, 0, 0, 0.15)`

## UI Components

### Buttons
```python
# Primary Button
QPushButton {
    background-color: #1E88E5;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 100px;
    font-weight: 500;
}

# Secondary Button
QPushButton {
    background-color: #2C3E50;
    color: #ECF0F1;
    border: 1px solid #3E3E3E;
    /* Rest same as primary */
}
```

### Input Fields
```python
QLineEdit, QComboBox, QSpinBox {
    background-color: #3A3A3A;
    color: #ECF0F1;
    border: 1px solid #4A4A4A;
    border-radius: 4px;
    padding: 8px 12px;
    min-height: 36px;
}
```

### Cards
- **Background**: `#2A2D2E`
- **Border**: `1px solid #3E3E3E`
- **Border Radius**: `12px`
- **Padding**: `16px`
- **Shadow**: `0 2px 8px rgba(0, 0, 0, 0.1)`

## Animation & Transitions

### Timing
- **Fast**: 100ms (micro-interactions)
- **Normal**: 200ms (standard transitions)
- **Slow**: 300ms (complex animations)

### Easing Curves
- **Standard**: `cubic-bezier(0.4, 0, 0.2, 1)`
- **Entering**: `cubic-bezier(0, 0, 0.2, 1)`
- **Exiting**: `cubic-bezier(0.4, 0, 1, 1)`

## Code Structure

## Project Structure

### Directory Layout
```
ApplicationRoot/
├── app/                  # Main application package
│   ├── __init__.py       # Package initialization
│   ├── main.py           # Application entry point
│   └── config.py         # Configuration settings
│
├── tabs/                # Tab implementations
│   ├── __init__.py       # Tabs package
│   ├── tab1.py           # First tab implementation
│   ├── tab2.py           # Second tab implementation
│   └── tab3.py           # Third tab implementation
│
├── core/                # Core functionality
│   ├── __init__.py       # Core package
│   ├── base.py           # Base classes and utilities
│   └── utils.py          # Common utility functions
│
├── ui/                  # UI components and themes
│   ├── components/       # Reusable UI widgets
│   ├── themes/           # Theme definitions
│   ├── styles/           # Style sheets
│   └── splash_screen.py  # Splash screen implementation
│
├── tests/              # Test suite
│   ├── __init__.py
│   ├── test_*.py        # Test files
│
├── docs/               # Documentation
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

### Key Directories

- **app/**: Core application initialization and configuration
- **tabs/**: Individual tab implementations
- **core/**: Shared functionality and base classes
- **ui/**: All UI-related code and assets
- **tests/**: Unit and integration tests
- **docs/**: Project documentation

### Naming Conventions
- Tab files: `tab1.py`, `tab2.py`, etc.
- Test files: `test_*.py`
- Package names: lowercase with underscores
- Class names: `PascalCase`
- Function/method names: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Splash Screen Implementation

Location: `ui/splash_screen.py`

1. **Animation**
   - Smooth particle animation with CommandCore color scheme
   - Progress bar with gradient effect
   - Text fade-in animation

2. **Statistics Display**
   Include the following metrics in the splash screen:
   - Application version
   - Loading progress percentage
   - System status indicators (if applicable)
   - Any relevant initialization metrics

3. **Timing**
   - Total display time: 5.9 seconds
   - Progress animation duration: 5.9s (matches display time)
   - Text fade-in duration: 1s

4. **Styling**
   - Background: `rgb(30, 39, 46)`
   - Primary accent: `#00a8ff` (CommandCore blue)
   - Secondary accent: `#00d2d3` (CommandCore teal)
   - Text: White with opacity for fade effects

5. **Responsive Design**
   - Center content on screen
   - Scale elements proportionally
   - Maintain aspect ratio for visual elements

### Tab Implementation

Each tab in the CommandCore Suite should follow these guidelines:

1. **File Naming**
   - Use `tab1.py`, `tab2.py`, etc. for tab implementations
   - Place all tab files in the `tabs/` directory

2. **Class Naming**
   - Use `[Feature]Tab` format (e.g., `DashboardTab`, `DevicesTab`)
   - Inherit from `QWidget`

3. **Required Methods**
   - `__init__`: Initialize the tab and call setup methods
   - `setup_ui`: Create and layout all UI components
   - `setup_connections`: Connect signals to slots
   - `update_data` (optional): Method to refresh tab data

4. **UI Organization**
   - Use a main layout (QVBoxLayout or QHBoxLayout)
   - Group related controls in QGroupBox widgets
   - Use consistent spacing (8px base unit)
   - Follow the CommandCore color scheme

5. **Performance**
   - Load data asynchronously when possible
   - Use QTimer for periodic updates
   - Clean up resources in `closeEvent` if needed

### Class Structure

```python
class FeatureTab(QWidget):
    """
    Brief description of the tab's purpose and functionality.
    
    This tab provides [describe main functionality] and displays [key features] 
    as part of the CommandCore Suite.
    """
    
    # Signals (if any)
    data_updated = Signal(dict)  # Example signal
    
    def __init__(self, parent=None):
        """
        Initialize the tab.
        
        Args:
            parent: Parent widget, typically the main window
        """
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
        # Initialize data structures
        self.data = {}
        
        # Load initial data
        self.update_data()
    
    def setup_ui(self):
        """Initialize and layout UI components."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        self.title_label = QLabel("Tab Title")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        header.addWidget(self.title_label)
        
        # Add header to main layout
        self.layout.addLayout(header)
        
        # Add content widgets here
        content = QGroupBox("Content")
        content_layout = QVBoxLayout()
        
        # Example widget
        self.example_widget = QLabel("Example content")
        content_layout.addWidget(self.example_widget)
        
        content.setLayout(content_layout)
        self.layout.addWidget(content)
        
        # Add stretch to push content to top
        self.layout.addStretch()
    
    def setup_connections(self):
        """Connect signals to slots."""
        # Example: self.button.clicked.connect(self.on_button_clicked)
        pass
    
    def update_data(self):
        """Update the tab's data and refresh the display."""
        try:
            # Fetch and process data here
            # Update UI components
            pass
        except Exception as e:
            logger.error(f"Error updating tab data: {e}")
    
    def closeEvent(self, event):
        """Clean up resources when the tab is closed."""
        # Stop timers, disconnect signals, etc.
        event.accept()
        self.layout = QVBoxLayout(self)
        # UI setup code here
    
    def setup_connections(self):
        """Connect signals to slots."""
        # Signal connections here
```

## Documentation Standards

### Module Docstring
```python
"""
Module description.

This module provides functionality for [purpose].

Example:
    Example code usage
"""
```

### Function/Method Docstring
```python
def my_function(param1, param2):
    """
    Brief description.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something goes wrong
    """
```

## Best Practices

1. **Separation of Concerns**: Keep UI, business logic, and data access separate.
2. **Responsive Design**: Ensure UI works across different window sizes.
3. **Accessibility**: 
   - Use proper contrast ratios (min 4.5:1 for normal text)
   - Support keyboard navigation
   - Provide text alternatives for icons
4. **Performance**: 
   - Use lazy loading for heavy components
   - Avoid unnecessary re-renders
   - Use QThread for long-running tasks
5. **Testing**:
   - Unit tests for business logic
   - UI tests for critical user flows

## Implementation Example

### Theme Application
```python
def apply_dark_theme(app):
    """Apply CommandCore dark theme to the application."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    # ... rest of the palette setup
    app.setPalette(palette)
    
    # Apply stylesheet
    with open("themes/dark.qss", "r") as f:
        app.setStyleSheet(f.read())
```

## Versioning
- Follow Semantic Versioning (MAJOR.MINOR.PATCH)
- Document all breaking changes in CHANGELOG.md

## Linting & Formatting
- Use `black` for code formatting
- Use `pylint` for static code analysis
- Use `mypy` for type checking

## Code Review Checklist
- [ ] Follows style guide
- [ ] Includes tests
- [ ] Documentation updated
- [ ] No commented-out code
- [ ] No debug statements
- [ ] Error handling in place

## Resources
- [VANTAGE Design System (Internal)]()
- [Qt Documentation](https://doc.qt.io/)
- [Material Design Guidelines](https://material.io/design)

---
*Last Updated: 2025-06-10*
