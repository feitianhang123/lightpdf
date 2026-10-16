"""One open document shown inside a tab, with its own undo/redo history."""
from __future__ import annotations

import os
from typing import List

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..core.document import PdfDocument
from .pdf_view import PdfView

MAX_HISTORY = 30


class DocumentTab(QWidget):
    def __init__(self, doc: PdfDocument, parent=None) -> None:
        super().__init__(parent)
        self.doc = doc
        self.view = PdfView(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.view.set_document(doc)

        self.undo_stack: List[bytes] = []
        self.redo_stack: List[bytes] = []
        self.view.aboutToModify.connect(self.push_undo)

    def title(self) -> str:
        if self.doc.path:
            return os.path.basename(self.doc.path)
        return "Untitled"

    # ------------------------------------------------------- undo / redo
    def push_undo(self) -> None:
        if not self.doc.is_open:
            return
        try:
            data = self.doc.tobytes()
        except Exception:  # noqa: BLE001
            return
        self.undo_stack.append(data)
        if len(self.undo_stack) > MAX_HISTORY:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def can_undo(self) -> bool:
        return bool(self.undo_stack)

    def can_redo(self) -> bool:
        return bool(self.redo_stack)

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        try:
            current = self.doc.tobytes()
        except Exception:  # noqa: BLE001
            current = None
        data = self.undo_stack.pop()
        if current is not None:
            self.redo_stack.append(current)
        self.doc.restore_bytes(data)
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        current = self.doc.tobytes()
        data = self.redo_stack.pop()
        self.undo_stack.append(current)
        self.doc.restore_bytes(data)
        return True
