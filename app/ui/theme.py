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
* {{ font-family: "Microsoft YaHei UI", "Segoe UI", "Noto Sans CJK SC", "Noto Sans SC",
     "WenQuanYi Micro Hei", "Source Han Sans SC", "PingFang SC", sans-serif;
     font-size: 13px; color: {TEXT}; }}
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
/* --- 输入框：白底细边，保持"可打字"的观感 --- */
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {{
    background: #FFFFFF; border: 1px solid {BORDER}; border-radius: 4px;
    padding: 3px 6px; selection-background-color: {BUTTON};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QPlainTextEdit:focus, QTextEdit:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background: #EDF2ED; color: #8AA98C; border-color: #C5E1A5;
}}

/* --- 下拉菜单：淡绿底 + 粗绿边 + 右侧独立的箭头按钮区 ---
   与输入框拉开明显差距，一眼就能认出"点这里会展开选项" --- */
QComboBox {{
    background: {BG_ALT};
    border: 2px solid {ACCENT};
    border-radius: 5px;
    padding: 4px 34px 4px 10px;
    min-height: 22px;
    color: {ACCENT_DARK};
    font-weight: 600;
    selection-background-color: {BUTTON};
}}
QComboBox:hover {{ background: {BUTTON_HOVER}; border-color: {ACCENT_DARK}; }}
QComboBox:focus, QComboBox:on {{ background: #FFFFFF; border-color: {ACCENT_DARK}; }}
QComboBox:disabled {{ background: #EDF2ED; color: #8AA98C; border-color: #C5E1A5; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 2px solid {ACCENT};
    background: {BUTTON};
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}}
QComboBox::drop-down:hover {{ background: {BUTTON_HOVER}; }}
QComboBox:on::drop-down {{ background: {BUTTON_HOVER}; border-left-color: {ACCENT_DARK}; }}
QComboBox:disabled::drop-down {{ background: #DCEDC8; border-left-color: #C5E1A5; }}

/* 展开后的选项列表也要统一成同一套绿色视觉 */
QComboBox QAbstractItemView {{
    background: #FFFFFF; border: 2px solid {ACCENT}; border-radius: 4px;
    padding: 3px; outline: 0;
}}
QComboBox QAbstractItemView::item {{
    min-height: 24px; padding: 3px 8px; color: {TEXT};
}}
QComboBox QAbstractItemView::item:hover {{ background: {BG_ALT}; }}
QComboBox QAbstractItemView::item:selected {{ background: {ACCENT}; color: #FFFFFF; }}

/* 拆分方式是重点控件：更大更高，箭头区更宽 */
QComboBox#splitMode {{ min-height: 30px; font-size: 14px; }}
QComboBox#splitMode::drop-down {{ width: 34px; }}
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


def _combo_arrow_rules() -> str:
    """Draw real triangle arrows at runtime and return their QSS rules.

    Qt style sheets cannot build a triangle out of CSS borders (it renders a
    solid square), so we paint a tiny PNG into the temp dir and point the
    ``::down-arrow`` sub-control at it. Works both from source and from a
    PyInstaller bundle — no external asset needs to be shipped.
    """
    import os
    import tempfile

    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtGui import QImage, QPainter, QPolygon

    def draw(filename: str, color: str) -> str:
        img = QImage(14, 14, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(color))
        painter.drawPolygon(QPolygon([QPoint(2, 5), QPoint(12, 5), QPoint(7, 10)]))
        painter.end()
        path = os.path.join(tempfile.gettempdir(), filename)
        if not img.save(path, "PNG"):
            return ""                     # temp dir not writable -> skip the rule
        return path.replace("\\", "/")

    # Two Qt quirks worth knowing:
    #  * without an explicit size Qt also paints its native grey arrow in the
    #    middle of the combo, so two arrows show up;
    #  * adding state-scoped rules (:on / :disabled) makes Qt paint *those*
    #    images in the middle too, even when the state does not match.
    # So: exactly one plain rule, with a fixed size. Hover / open / disabled
    # feedback is carried by the ::drop-down background instead.
    normal = draw("lightpdf_combo_arrow.png", ACCENT_DARK)
    if not normal:
        return ""                         # still fine: the green arrow button remains
    return 'QComboBox::down-arrow { image: url("%s"); width: 14px; height: 14px; }\n' % normal


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
    app.setStyleSheet(QSS + "\n" + _combo_arrow_rules())
