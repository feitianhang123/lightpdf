"""Entry point for the Light PDF Editor."""
from __future__ import annotations

import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import i18n
from .paths import icon_path
from .ui.main_window import MainWindow
from .ui.theme import apply_theme
from .ui.translations import apply_qt_translations


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("轻PDF编辑器")
    app.setOrganizationName("MiniPDF")

    ic = icon_path()
    if ic:
        app.setWindowIcon(QIcon(ic))

    i18n.load_language()
    apply_qt_translations(app, i18n.language())
    apply_theme(app)

    win = MainWindow()
    if ic:
        win.setWindowIcon(QIcon(ic))
    win.show()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        win._load(sys.argv[1])
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
