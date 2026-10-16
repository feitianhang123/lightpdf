"""Load Qt's own translations so built-in context menus (Cut/Copy/Paste/
Select All, etc.) follow the selected UI language."""
from __future__ import annotations

from PySide6.QtCore import QLibraryInfo, QTranslator

_translator = None


def _translations_path() -> str:
    try:
        return QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    except AttributeError:
        return QLibraryInfo.path(QLibraryInfo.TranslationsPath)


def apply_qt_translations(app, lang: str) -> None:
    global _translator
    if _translator is not None:
        app.removeTranslator(_translator)
        _translator = None
    if lang != "zh":
        return
    path = _translations_path()
    trans = QTranslator(app)
    for name in ("qtbase_zh_CN", "qt_zh_CN"):
        if trans.load(name, path):
            app.installTranslator(trans)
            _translator = trans
            break
