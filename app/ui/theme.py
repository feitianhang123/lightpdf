"""Light-green application theme (QSS)."""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# palette
BG = "#E8F5E9"          # window background
BG_ALT = "#F1F8E9"      # panels
TOOLBAR = "#C8E6C9"     # toolbar / headers
BUTTON = "#A5D6A7"      # buttons
BUTTON_HOVER = "#B9E0BB"
BORDER = "#66BB6A"
ACCENT = "#43A047"
ACCENT_DARK = "#2E7D32"
TEXT = "#1B3A1E"
PAGE_AREA = "#9EC9A1"   # document scroll area

QSS = f"""
* {{ font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; font-size: 13px; color: {TEXT}; }}
QMainWindow, QDialog {{ background: {BG}; }}
QMenuBar {{ background: {TOOLBAR}; }}
QMenuBar::item {{ padding: 4px 10px; background: transparent; border-radius: 4px; }}
QMenuBar::item:selected {{ background: {BUTTON}; }}
QMenu {{ background: {BG_ALT}; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 5px 24px 5px 12px; border-radius: 4px; }}
QMenu::item:selected {{ background: {BUTTON}; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
QToolBar {{ background: {TOOLBAR}; border: 0; spacing: 2px; padding: 3px; }}
QToolBar::separator {{ width: 1px; background: {BORDER}; margin: 4px 4px; }}
QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 5px; padding: 3px; }}
QToolButton:hover {{ background: {BUTTON}; border-color: {BORDER}; }}
QToolButton:checked {{ background: {ACCENT}; }}
QToolButton:checked:hover {{ background: {ACCENT_DARK}; }}
QPushButton {{ background: {BUTTON}; border: 1px solid {BORDER}; border-radius: 5px; padding: 5px 12px; }}
QPushButton:hover {{ background: {BUTTON_HOVER}; }}
QPushButton:pressed {{ background: {ACCENT}; color: white; }}
QPushButton:disabled {{ background: #DCEDC8; color: #8AA98C; border-color: #C5E1A5; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {{
    background: white; border: 1px solid {BORDER}; border-radius: 4px; padding: 3px 6px;
    selection-background-color: {BUTTON};
}}
QComboBox::drop-down {{ border: 0; width: 18px; }}
QListWidget, QTreeWidget, QListWidget#ResultsPanel {{
    background: {BG_ALT}; border: 1px solid {BORDER}; border-radius: 4px;
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background: {ACCENT}; color: white;
}}
QListWidget::item:hover, QTreeWidget::item:hover {{ background: {BUTTON}; }}
QDockWidget::title {{ background: {TOOLBAR}; padding: 5px; border-bottom: 1px solid {BORDER}; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; top: -1px; }}
QTabBar::tab {{ background: {BUTTON}; padding: 5px 12px; border: 1px solid {BORDER}; border-bottom: 0;
                border-top-left-radius: 5px; border-top-right-radius: 5px; }}
QTabBar::tab:selected {{ background: {BG_ALT}; }}
QStatusBar {{ background: {TOOLBAR}; }}
QScrollBar:vertical {{ background: {BG_ALT}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {BUTTON}; border-radius: 6px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar:horizontal {{ background: {BG_ALT}; height: 12px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {BUTTON}; border-radius: 6px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QSplitter::handle {{ background: {BORDER}; }}
QLabel {{ background: transparent; }}
QCheckBox {{ spacing: 6px; }}
"""


def apply_theme(app: QApplication) -> None:
    pal = app.palette()
    pal.setColor(QPalette.Window, QColor(BG))
    pal.setColor(QPalette.Base, QColor("#FFFFFF"))
    pal.setColor(QPalette.AlternateBase, QColor(BG_ALT))
    pal.setColor(QPalette.Button, QColor(BUTTON))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(pal)
    app.setStyleSheet(QSS)
