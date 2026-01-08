"""Shared helpers for building tabs."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QWidget

from HackAttack.ui.styles import (
    PLACEHOLDER_ICON_STYLE,
    PLACEHOLDER_DESCRIPTION_CARD_STYLE,
    PLACEHOLDER_DESCRIPTION_TEXT_STYLE,
    PLACEHOLDER_MISSING_STYLE,
)


def build_tab(
    title: str,
    description: str,
    icon_name: str,
    content_widget: QWidget | None = None,
    show_description: bool = True,
) -> QWidget:
    """Create a tab page with a header and optional content."""
    page = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(20, 15, 20, 15)
    layout.setSpacing(15)

    header = QWidget()
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(0, 0, 0, 20)

    icon_label = QLabel(icon_name)
    icon_label.setStyleSheet(PLACEHOLDER_ICON_STYLE)
    header_layout.addWidget(icon_label)

    title_label = QLabel(f"<h1 style='margin: 0; color: #cdd6f4;'>{title}</h1>")
    title_label.setStyleSheet("font-size: 24px;")
    header_layout.addWidget(title_label, 1)

    layout.addWidget(header)

    if show_description:
        desc_card = QWidget()
        desc_card.setStyleSheet(PLACEHOLDER_DESCRIPTION_CARD_STYLE)
        desc_layout = QVBoxLayout(desc_card)

        desc_text = QLabel(description)
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet(PLACEHOLDER_DESCRIPTION_TEXT_STYLE)
        desc_layout.addWidget(desc_text)

        layout.addWidget(desc_card)

    if content_widget is not None:
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(content_widget)

    layout.addStretch()

    page.setLayout(layout)
    return page


def build_missing_tab(title: str, description: str, icon_name: str) -> QWidget:
    """Create a tab with a missing-module notice."""
    page = build_tab(title, description, icon_name, show_description=True)
    layout = page.layout()
    missing = QLabel("Module UI not yet implemented. Please check back for updates.")
    missing.setStyleSheet(PLACEHOLDER_MISSING_STYLE)
    missing.setAlignment(Qt.AlignCenter)
    layout.insertWidget(layout.count() - 1, missing)
    return page
