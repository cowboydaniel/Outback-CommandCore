"""Android tools tab layout for DROIDCOM."""

from PySide6 import QtCore, QtWidgets

from ..ui.styles import COLORS, EMOJI_ICONS


def create_tools_tab(ui):
    """Create the Android Tools tab with all tool categories."""
    ui.tools_frame = QtWidgets.QWidget(ui.notebook)
    tools_layout = QtWidgets.QVBoxLayout(ui.tools_frame)
    tools_layout.setContentsMargins(0, 0, 0, 0)  # Remove outer margins
    tools_layout.setSpacing(0)
    ui.notebook.addTab(ui.tools_frame, "\U0001F6E0 Android Tools")

    # Create scroll area
    scroll_area = QtWidgets.QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
    scroll_area.setStyleSheet("""
        QScrollArea {
            border: none;
            background: transparent;
        }
        QScrollBar:vertical {
            border: none;
            background: #2a2a2a;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #4a4a4a;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """)
    tools_layout.addWidget(scroll_area)

    # Create content widget for scroll area
    content_widget = QtWidgets.QWidget()
    content_widget.setStyleSheet("background: transparent;")

    # Main layout for the content
    main_content_layout = QtWidgets.QVBoxLayout(content_widget)
    main_content_layout.setContentsMargins(12, 12, 12, 12)
    main_content_layout.setSpacing(16)

    # Instruction label
    instruction_label = QtWidgets.QLabel(
        "\U0001F4A1 Tip: Scroll down to discover all available tools",
        content_widget
    )
    instruction_label.setStyleSheet(f"""
        color: {COLORS['text_muted']};
        font-size: 12px;
        font-style: italic;
        padding: 10px 14px;
        background-color: {COLORS['background_light']};
        border-radius: 8px;
        margin-bottom: 8px;
    """)
    main_content_layout.addWidget(instruction_label)

    # Create a scroll area for the categories grid
    categories_container = QtWidgets.QWidget()
    categories_container.setStyleSheet("background: transparent;")

    # Set up the categories grid layout
    categories_grid = QtWidgets.QGridLayout(categories_container)
    categories_grid.setHorizontalSpacing(16)
    categories_grid.setVerticalSpacing(16)
    categories_grid.setContentsMargins(0, 0, 0, 0)

    # Add stretch to push content to the top
    main_content_layout.addWidget(categories_container, 1)  # Add stretch factor
    main_content_layout.addStretch()  # Add stretch to push content up

    # Set the content widget to the scroll area
    scroll_area.setWidget(content_widget)

    # Define categories with their respective icons and minimum heights
    categories = [
        {
            "name": "Device Control",
            "icon": EMOJI_ICONS['Device Control'],
            "min_height": 320  # Increased minimum height for better spacing
        },
        {
            "name": "App Management",
            "icon": EMOJI_ICONS['App Management'],
            "min_height": 320
        },
        {
            "name": "System Tools",
            "icon": EMOJI_ICONS['System Tools'],
            "min_height": 280
        },
        {
            "name": "Debugging",
            "icon": EMOJI_ICONS['Debugging'],
            "min_height": 280
        },
        {
            "name": "File Operations",
            "icon": EMOJI_ICONS['File Operations'],
            "min_height": 280
        },
        {
            "name": "Security & Permissions",
            "icon": EMOJI_ICONS['Security & Permissions'],
            "min_height": 280
        },
        {
            "name": "Automation & Scripting",
            "icon": EMOJI_ICONS['Automation & Scripting'],
            "min_height": 280
        },
        {
            "name": "Advanced Tests",
            "icon": EMOJI_ICONS['Advanced Tests'],
            "min_height": 280
        },
    ]

    # Calculate the number of columns based on available width
    num_columns = 2
    for idx, category in enumerate(categories):
        row = idx // num_columns
        col = idx % num_columns

        # Create category frame with improved styling
        category_frame = QtWidgets.QGroupBox(
            f"{category['icon']} {category['name']}",
            categories_container
        )

        # Apply consistent styling to all category frames
        category_frame.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {COLORS['surface_border']};
                border-radius: 10px;
                margin-top: 16px;
                padding-top: 20px;
                background: {COLORS['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: {COLORS['text_primary']};
                font-weight: 600;
            }}
        """)

        # Set size policy to allow expansion
        category_frame.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )

        # Create layout for the category content
        category_layout = QtWidgets.QVBoxLayout(category_frame)
        category_layout.setContentsMargins(12, 20, 12, 16)
        category_layout.setSpacing(10)

        # Create content widget for the buttons
        content_widget = QtWidgets.QWidget()
        content_widget.setStyleSheet("background: transparent;")

        # Layout for the buttons - using QGridLayout for better organization
        content_layout = QtWidgets.QGridLayout(content_widget)
        content_layout.setHorizontalSpacing(10)
        content_layout.setVerticalSpacing(10)
        content_layout.setContentsMargins(2, 2, 2, 2)
        content_layout.setRowStretch(10, 1)  # Add stretch to the last row

        # Add content widget to the category layout
        category_layout.addWidget(content_widget)

        # Add stretch to push content to the top
        category_layout.addStretch()

        # Add the category frame to the grid
        categories_grid.addWidget(category_frame, row, col, 1, 1, QtCore.Qt.AlignTop)

        # Populate the category with buttons
        ui._populate_category_buttons(category["name"], content_layout)

    # Configure grid layout
    categories_grid.setColumnStretch(0, 1)
    categories_grid.setColumnStretch(1, 1)
    categories_grid.setRowStretch(categories_grid.rowCount(), 1)  # Add stretch to last row
