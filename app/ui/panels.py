"""Left dock: thumbnails + outline. Right dock: search/annotations."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QTreeWidget,
                               QTreeWidgetItem, QTabWidget, QWidget, QVBoxLayout)

from ..i18n import tr
from ..core.document import PdfDocument


class ThumbnailPanel(QListWidget):
    pageActivated = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setIconSize(QSize(120, 160))
        self.setSpacing(4)
        self.setUniformItemSizes(True)
        self.itemClicked.connect(lambda it: self.pageActivated.emit(it.data(Qt.UserRole)))

    def set_document(self, doc: Optional[PdfDocument]) -> None:
        self.clear()
        if not doc or not doc.is_open:
            return
        for i in range(doc.page_count):
            it = QListWidgetItem(tr("page.label", n=i + 1))
            it.setData(Qt.UserRole, i)
            it.setTextAlignment(Qt.AlignHCenter)
            self.addItem(it)
        self._render_thumbs(doc)

    def _render_thumbs(self, doc: PdfDocument) -> None:
        for i in range(doc.page_count):
            pix = doc.render(i, zoom=0.22, alpha=False)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                         QImage.Format_RGB888).copy()
            self.item(i).setIcon(QIcon(QPixmap.fromImage(img)))

    def refresh_page(self, doc: PdfDocument, index: int) -> None:
        pix = doc.render(index, zoom=0.22, alpha=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                     QImage.Format_RGB888).copy()
        self.item(index).setIcon(QIcon(QPixmap.fromImage(img)))

    def highlight_page(self, index: int) -> None:
        if 0 <= index < self.count():
            self.blockSignals(True)
            self.setCurrentRow(index)
            self.blockSignals(False)


class OutlinePanel(QTreeWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self._cb = None
        self.itemClicked.connect(self._clicked)

    def set_document(self, doc: Optional[PdfDocument]) -> None:
        self.clear()
        if not doc or not doc.is_open:
            return
        stack: List[QTreeWidgetItem] = []
        for item in doc.get_outline():
            node = QTreeWidgetItem([item.title])
            node.setData(0, Qt.UserRole, item.page)
            while stack and stack[-1].data(0, Qt.UserRole + 1) >= item.level:
                stack.pop()
            if stack:
                stack[-1].addChild(node)
            else:
                self.addTopLevelItem(node)
            node.setData(0, Qt.UserRole + 1, item.level)
            stack.append(node)
        self.expandAll()

    def _clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        page = item.data(0, Qt.UserRole)
        if page is not None and self._cb:
            self._cb(int(page))

    def set_page_callback(self, cb) -> None:
        self._cb = cb


class LeftDock(QTabWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.thumbnails = ThumbnailPanel()
        self.outline = OutlinePanel()
        self.addTab(self.thumbnails, "Thumbnails")
        self.addTab(self.outline, "Outline")


class ResultsPanel(QListWidget):
    """Displays search hits and annotation lists."""
    hitActivated = Signal(int)  # row index

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.itemClicked.connect(lambda it: self.hitActivated.emit(self.row(it)))
