"""Dark theme styles for HackAttack."""

APP_STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QListWidget {
    background-color: #181825;
    border: none;
    font-size: 13px;
    padding: 10px 5px;
    min-width: 280px;
    max-width: 300px;
}
QListWidget::item {
    padding: 10px 8px;
    border-radius: 5px;
    margin: 2px 0;
    min-height: 50px;
}
QListWidget::item:selected {
    background-color: #89b4fa;
    color: #1e1e2e;
}
QLabel {
    font-size: 18px;
    padding: 20px;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
}
"""
