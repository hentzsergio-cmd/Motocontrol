DARK_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #121212;
    color: #e8eaed;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #1e1e1e;
    border-right: 1px solid #2d2d2d;
}
QFrame#card {
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 10px;
}
QPushButton#navBtn {
    background-color: transparent;
    color: #b0b3b8;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
}
QPushButton#navBtn:hover {
    background-color: #2d2d2d;
    color: #ffffff;
}
QPushButton#navBtn:checked {
    background-color: #1a73e8;
    color: #ffffff;
}
QPushButton {
    background-color: #1a73e8;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover { background-color: #1557b0; }
QPushButton:disabled { background-color: #3c4043; color: #9aa0a6; }
QPushButton#dangerBtn { background-color: #d93025; }
QPushButton#dangerBtn:hover { background-color: #b31412; }
QPushButton#secondaryBtn {
    background-color: #2d2d2d;
    color: #e8eaed;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
    background-color: #2d2d2d;
    color: #e8eaed;
    border: 1px solid #3c4043;
    border-radius: 6px;
    padding: 8px;
}
QComboBox::drop-down { border: none; }
QHeaderView::section {
    background-color: #2d2d2d;
    color: #e8eaed;
    padding: 8px;
    border: none;
}
QTableWidget {
    background-color: #1e1e1e;
    alternate-background-color: #252525;
    gridline-color: #2d2d2d;
    border: 1px solid #2d2d2d;
    border-radius: 8px;
}
QTableWidget::item:selected {
    background-color: #1a73e8;
}
QLabel#title { font-size: 24px; font-weight: 700; color: #ffffff; }
QLabel#subtitle { font-size: 14px; color: #9aa0a6; }
QLabel#statValue { font-size: 22px; font-weight: 700; color: #1a73e8; }
QLabel#statLabel { font-size: 12px; color: #9aa0a6; }
QLabel#chartTitle { font-size: 11px; font-weight: 600; color: #ffffff; }
QLabel#alert { color: #f28b82; font-weight: 600; }
QScrollArea { border: none; }
QGroupBox {
    border: 1px solid #2d2d2d;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QTabWidget::pane { border: 1px solid #2d2d2d; border-radius: 8px; }
QTabBar::tab {
    background: #2d2d2d;
    color: #b0b3b8;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: #1a73e8; color: white; }
QStatusBar { background-color: #1e1e1e; color: #9aa0a6; }
"""

LIGHT_THEME = """
QMainWindow, QDialog, QWidget {
    background-color: #f5f7fa;
    color: #202124;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QFrame#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #dadce0;
}
QFrame#card {
    background-color: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 10px;
}
QPushButton#navBtn {
    background-color: transparent;
    color: #5f6368;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
}
QPushButton#navBtn:hover {
    background-color: #f1f3f4;
    color: #202124;
}
QPushButton#navBtn:checked {
    background-color: #1a73e8;
    color: #ffffff;
}
QPushButton {
    background-color: #1a73e8;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover { background-color: #1557b0; }
QPushButton:disabled { background-color: #dadce0; color: #80868b; }
QPushButton#dangerBtn { background-color: #d93025; }
QPushButton#dangerBtn:hover { background-color: #b31412; }
QPushButton#secondaryBtn {
    background-color: #f1f3f4;
    color: #202124;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
    background-color: #ffffff;
    color: #202124;
    border: 1px solid #dadce0;
    border-radius: 6px;
    padding: 8px;
}
QHeaderView::section {
    background-color: #f1f3f4;
    color: #202124;
    padding: 8px;
    border: none;
}
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f9fa;
    gridline-color: #dadce0;
    border: 1px solid #dadce0;
    border-radius: 8px;
}
QTableWidget::item:selected { background-color: #1a73e8; color: white; }
QLabel#title { font-size: 24px; font-weight: 700; }
QLabel#subtitle { font-size: 14px; color: #5f6368; }
QLabel#statValue { font-size: 22px; font-weight: 700; color: #1a73e8; }
QLabel#statLabel { font-size: 12px; color: #5f6368; }
QLabel#chartTitle { font-size: 11px; font-weight: 600; color: #202124; }
QLabel#alert { color: #d93025; font-weight: 600; }
QScrollArea { border: none; }
QGroupBox {
    border: 1px solid #dadce0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 600;
}
QTabWidget::pane { border: 1px solid #dadce0; border-radius: 8px; }
QTabBar::tab {
    background: #f1f3f4;
    color: #5f6368;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: #1a73e8; color: white; }
QStatusBar { background-color: #ffffff; color: #5f6368; }
"""


def get_stylesheet(theme: str) -> str:
    return DARK_THEME if theme == "dark" else LIGHT_THEME
