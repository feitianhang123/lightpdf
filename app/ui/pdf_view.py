"""Continuous, lazily-rendered PDF view with interaction tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import fitz
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsView)

from ..core import annotations as annot
from ..core.document import PdfDocument
from ..core.editor import TextSpan, iter_spans
from .theme import PAGE_AREA

TOOLS = ["select", "highlight", "underline", "strikeout", "note", "freetext",
         "ink", "rect", "ellipse", "line", "arrow", "stamp", "edittext",
         "whiteout", "insertimage"]


@dataclass
class PageGeom:
    index: int
    x: float
    y: float
    w: float          # displayed width (points)
    h: float          # displayed height (points)
    rot_w: float      # unscaled rotated width
    rot_h: float


class PdfView(QGraphicsView):
    pageChanged = Signal(int)
    zoomChanged = Signal(float)
    aboutToModify = Signal()        # emitted just before a document mutation
    annotEditRequested = Signal(int, int)      # page index, annotation xref
    annotActivated = Signal(int, int)          # page index, annotation xref (clicked)
    spanPicked = Signal(object)     # TextSpan for edit-text tool
    pointPicked = Signal(int, QPointF)  # page index, displayed point (for note/stamp/freetext)
    rectPicked = Signal(int, QRectF, str)  # page index, displayed rect, tool
    noteRequested = Signal(int, QPointF)   # page index, displayed point
    stampRequested = Signal(int, QPointF)  # page index, displayed point
    inkFinished = Signal(int, list)
    statusMessage = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setBackgroundBrush(QColor(PAGE_AREA))

        self.doc: Optional[PdfDocument] = None
        self.zoom: float = 1.0
        self.tool: str = "select"
        self.span_color = (1.0, 1.0, 0.0)   # yellow, 0..1 floats
        self.pen_color = (1.0, 0.0, 0.0)    # red
        self.markup_opacity = 0.3           # highlight/markup transparency
        self.pen_width = 1.5
        self.freetext_size = 12
        self.spans_cache: Dict[int, List[TextSpan]] = {}

        self._geoms: List[PageGeom] = []
        self._items: Dict[int, QGraphicsPixmapItem] = {}
        self._rendered: Dict[int, float] = {}
        self._columns = 1
        self._in_relayout = False
        self._page_gap = 12
        self._margin = 12

        self._drag_start: Optional[QPointF] = None
        self._drag_index: Optional[int] = None
        self._drag_dp0: Optional[QPointF] = None
        self._panning: bool = False
        self._pan_start = None
        self._move_xref = None
        self._move_index: Optional[int] = None
        self._move_last_pdf = None
        self._move_snapshot: bool = False
        self._drag_rect_item: Optional[QGraphicsRectItem] = None
        self._ink_points: List[QPointF] = []
        self._current_page = 0

        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(40)
        self._render_timer.timeout.connect(self._render_visible)

        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    # ------------------------------------------------------------------ setup
    def set_document(self, doc: Optional[PdfDocument]) -> None:
        self.doc = doc
        self.spans_cache.clear()
        self._rendered.clear()
        self._scene.clear()
        self._items.clear()
        self._geoms.clear()
        if doc and doc.is_open:
            self._layout_pages()
            self.goto_page(0)
        self._render_timer.start()
        self.zoomChanged.emit(self.zoom)

    def invalidate_page(self, index: int) -> None:
        self._rendered.pop(index, None)
        self._render_timer.start()

    # ----------------------------------------------------------------- layout
    def _compute_columns(self) -> int:
        if not self.doc or self.doc.page_count == 0:
            return 1
        avail = max(200, self.viewport().width() - 2 * self._margin)
        colw = max(self.doc.page(i).rect.width for i in range(self.doc.page_count)) * self.zoom
        gap = self._page_gap
        if colw <= 0:
            return 1
        return max(1, int((avail + gap) // (colw + gap)))

    def _layout_pages(self) -> None:
        assert self.doc is not None
        self._geoms.clear()
        self._items.clear()
        self._scene.clear()
        n = self.doc.page_count
        if n == 0:
            self._scene.setSceneRect(0, 0, 1, 1)
            return
        rects = [self.doc.page(i).rect for i in range(n)]
        columns = self._compute_columns()
        self._columns = columns
        gap = self._page_gap
        avail = max(200, self.viewport().width() - 2 * self._margin)
        y = self._margin
        i = 0
        while i < n:
            row = list(range(i, min(i + columns, n)))
            row_h = max(rects[k].height for k in row) * self.zoom
            row_w = sum(rects[k].width * self.zoom for k in row) + gap * (len(row) - 1)
            x = self._margin + max(0.0, (avail - row_w) / 2)
            for k in row:
                r = rects[k]
                w = r.width * self.zoom
                h = r.height * self.zoom
                geom = PageGeom(k, x, y, w, h, r.width, r.height)
                self._geoms.append(geom)
                placeholder = self._scene.addRect(QRectF(x, y, w, h),
                                                  QPen(QColor(150, 150, 150)), QColor(255, 255, 255))
                placeholder.setZValue(0)
                item = QGraphicsPixmapItem()
                item.setPos(x, y)
                item.setTransformationMode(Qt.SmoothTransformation)
                item.setZValue(1)
                self._scene.addItem(item)
                self._items[k] = item
                x += w + gap
            y += row_h + gap
            i += len(row)
        self._geoms.sort(key=lambda g: g.index)
        right = max((g.x + g.w) for g in self._geoms) + self._margin
        self._scene.setSceneRect(0, 0, right, y)

    def _render_visible(self) -> None:
        if not self.doc or not self.doc.is_open:
            return
        if not self._in_relayout and self._compute_columns() != self._columns:
            keep = self.current_page()
            ratio = self._page_center_ratio(keep)
            self._in_relayout = True
            try:
                self._rendered.clear()
                self._layout_pages()
                self._scroll_to_ratio(keep, ratio)
            finally:
                self._in_relayout = False
        view_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        for geom in self._geoms:
            if self._rendered.get(geom.index) == self.zoom:
                continue
            page_rect = QRectF(geom.x, geom.y, geom.w, geom.h)
            if not page_rect.intersects(view_rect.adjusted(-400, -400, 400, 400)):
                continue
            self._render_page(geom)

    def _render_page(self, geom: PageGeom) -> None:
        assert self.doc is not None
        pix = self.doc.render(geom.index, zoom=self.zoom, alpha=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride,
                     QImage.Format_RGB888).copy()
        qpix = QPixmap.fromImage(img)
        item = self._items[geom.index]
        item.setPixmap(qpix)
        item.setPos(geom.x, geom.y)
        self._rendered[geom.index] = self.zoom

    # ------------------------------------------------------------------ zoom
    def set_zoom(self, zoom: float, anchor_page: Optional[int] = None) -> None:
        zoom = max(0.1, min(8.0, zoom))
        if abs(zoom - self.zoom) < 1e-6:
            return
        keep = anchor_page if anchor_page is not None else self.current_page()
        self.zoom = zoom
        pos_ratio = self._page_center_ratio(keep)
        self._rendered.clear()
        self._layout_pages()
        self._scroll_to_ratio(keep, pos_ratio)
        self.zoomChanged.emit(self.zoom)
        self._render_visible()

    def zoom_in(self) -> None:
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self) -> None:
        self.set_zoom(self.zoom / 1.25)

    def fit_width(self) -> None:
        if not self._geoms:
            return
        g = self._geoms[self.current_page()]
        avail = self.viewport().width() - 2 * self._margin - 20
        self.set_zoom(max(0.1, avail / g.rot_w))

    def fit_page(self) -> None:
        if not self._geoms:
            return
        g = self._geoms[self.current_page()]
        aw = self.viewport().width() - 2 * self._margin - 20
        ah = self.viewport().height() - 2 * self._margin - 20
        self.set_zoom(max(0.1, min(aw / g.rot_w, ah / g.rot_h)))

    def actual_size(self) -> None:
        self.set_zoom(1.0)

    # ------------------------------------------------------------- navigation
    def current_page(self) -> int:
        if not self._geoms:
            return 0
        center = self.mapToScene(self.viewport().rect().center())
        best, best_d = 0, 1e18
        for g in self._geoms:
            cy = g.y + g.h / 2
            d = abs(cy - center.y())
            if d < best_d:
                best_d, best = d, g.index
        return best

    def goto_page(self, index: int) -> None:
        if not self._geoms:
            return
        index = max(0, min(index, len(self._geoms) - 1))
        g = self._geoms[index]
        self.verticalScrollBar().setValue(int(g.y))
        self._render_timer.start()
        self.pageChanged.emit(index)

    def _page_center_ratio(self, index: int) -> float:
        if not self._geoms:
            return 0.0
        g = self._geoms[min(index, len(self._geoms) - 1)]
        cy = self.mapToScene(self.viewport().rect().center()).y()
        return (cy - g.y) / max(1.0, g.h)

    def _scroll_to_ratio(self, index: int, ratio: float) -> None:
        if not self._geoms:
            return
        g = self._geoms[min(index, len(self._geoms) - 1)]
        target = g.y + ratio * g.h - self.viewport().height() / 2
        self.verticalScrollBar().setValue(int(max(0, target)))

    # ------------------------------------------------------------- hit testing
    def _geom_at_scene(self, pos: QPointF) -> Optional[PageGeom]:
        for g in self._geoms:
            if QRectF(g.x, g.y, g.w, g.h).contains(pos):
                return g
        return None

    def scene_to_page(self, pos: QPointF) -> Optional[Tuple[int, QPointF]]:
        g = self._geom_at_scene(pos)
        if not g:
            return None
        px = (pos.x() - g.x) / self.zoom
        py = (pos.y() - g.y) / self.zoom
        return g.index, QPointF(px, py)

    def page_to_pdf_point(self, index: int, dp: QPointF) -> fitz.Point:
        page = self.doc.page(index)
        return fitz.Point(dp.x(), dp.y()) * page.derotation_matrix

    def page_to_pdf_rect(self, index: int, r: QRectF) -> fitz.Rect:
        page = self.doc.page(index)
        rect = fitz.Rect(r.left(), r.top(), r.right(), r.bottom())
        return rect * page.derotation_matrix

    def spans(self, index: int) -> List[TextSpan]:
        if index not in self.spans_cache:
            self.spans_cache[index] = iter_spans(self.doc, index)
        return self.spans_cache[index]

    def span_at_display(self, index: int, dp: QPointF) -> Optional[TextSpan]:
        for s in self.spans(index):
            # convert pdf bbox to display coords
            page = self.doc.page(index)
            disp = s.bbox * page.rotation_matrix
            if (disp.x0 - 2 <= dp.x() <= disp.x1 + 2 and
                    disp.y0 - 2 <= dp.y() <= disp.y1 + 2):
                return s
        return None

    # ------------------------------------------------------------- mouse tools
    def _on_scroll(self) -> None:
        self._render_timer.start()
        page = self.current_page()
        if page != self._current_page:
            self._current_page = page
            self.pageChanged.emit(page)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.doc:
            if self.tool == "hand":
                self._panning = True
                self._pan_start = event.position().toPoint()
                self.viewport().setCursor(Qt.ClosedHandCursor)
                event.accept()
                return
            if self.tool == "select":
                hit = self.scene_to_page(self.mapToScene(event.position().toPoint()))
                if hit:
                    xref = annot.annot_xref_at(self.doc, hit[0],
                                               self.page_to_pdf_point(hit[0], hit[1]))
                    if xref is not None:
                        info = annot.annot_info(self.doc, hit[0], xref)
                        if info.get("type") == "Text":
                            self.annotActivated.emit(hit[0], xref)
                        self._move_xref = xref
                        self._move_index = hit[0]
                        self._move_last_pdf = self.page_to_pdf_point(hit[0], hit[1])
                        self._move_snapshot = False
                        self.viewport().setCursor(Qt.SizeAllCursor)
                        event.accept()
                        return
            if self.tool != "select":
                self._handle_tool_press(event)
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.doc and self.tool == "select":
            hit = self.scene_to_page(self.mapToScene(event.position().toPoint()))
            if hit:
                xref = annot.annot_xref_at(self.doc, hit[0],
                                           self.page_to_pdf_point(hit[0], hit[1]))
                if xref is not None:
                    self.annotEditRequested.emit(hit[0], xref)
                    return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_start is not None:
            pos = event.position().toPoint()
            delta = pos - self._pan_start
            self._pan_start = pos
            hb = self.horizontalScrollBar()
            vb = self.verticalScrollBar()
            hb.setValue(hb.value() - delta.x())
            vb.setValue(vb.value() - delta.y())
            event.accept()
            return
        if self._move_xref is not None:
            hit = self.scene_to_page(self.mapToScene(event.position().toPoint()))
            if hit and hit[0] == self._move_index:
                pdf = self.page_to_pdf_point(self._move_index, hit[1])
                dx = pdf.x - self._move_last_pdf.x
                dy = pdf.y - self._move_last_pdf.y
                if abs(dx) > 0.01 or abs(dy) > 0.01:
                    if not self._move_snapshot:
                        self.aboutToModify.emit()
                        self._move_snapshot = True
                    annot.move_annot(self.doc, self._move_index, self._move_xref, dx, dy)
                    self._move_last_pdf = pdf
                    self.invalidate_page(self._move_index)
            event.accept()
            return
        if self._drag_start is not None and self.tool in ("highlight", "underline",
                                                          "strikeout", "rect",
                                                          "ellipse", "line",
                                                          "arrow") and self.doc:
            self._update_drag_rect(event.position())
            return
        if self._ink_points and self.tool == "ink":
            self._ink_points.append(event.position())
            self.viewport().update()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._move_xref is not None:
            self._move_xref = None
            self._move_snapshot = False
            self.apply_cursor()
            event.accept()
            return
        if self._panning:
            self._panning = False
            self.apply_cursor()
            event.accept()
            return
        if event.button() == Qt.LeftButton and self.doc and self.tool != "select":
            self._handle_tool_release(event)
            return
        super().mouseReleaseEvent(event)

    def markup_style(self, tool: str):
        """Highlight uses the chosen color/opacity; underline & strikeout are
        solid black lines."""
        if tool == "highlight":
            return self.span_color, self.markup_opacity
        return (0.0, 0.0, 0.0), 1.0

    def apply_cursor(self) -> None:
        if self.tool == "hand":
            self.viewport().setCursor(Qt.OpenHandCursor)
        else:
            self.viewport().setCursor(Qt.ArrowCursor)

    def _handle_tool_press(self, event) -> None:
        scene_pos = self.mapToScene(event.position().toPoint())
        hit = self.scene_to_page(scene_pos)
        if not hit:
            return
        index, dp = hit
        t = self.tool
        if t == "note":
            self.noteRequested.emit(index, dp)
            return
        if t == "stamp":
            self.stampRequested.emit(index, dp)
            return
        if t == "insertimage":
            self.pointPicked.emit(index, dp)
            return
        if t == "edittext":
            span = self.span_at_display(index, dp)
            if span:
                self.spanPicked.emit(span)
            else:
                self.statusMessage.emit("No text found at that point.")
            return
        if t == "freetext":
            self.rectPicked.emit(index, QRectF(dp.x(), dp.y(), 1, 1), "freetext")
            return
        if t == "whiteout":
            self._drag_start = scene_pos
            return
        if t == "ink":
            self._ink_points = [dp]
            return
        # drag tools
        self._drag_start = scene_pos
        self._drag_index = index
        self._drag_dp0 = dp
        item = QGraphicsRectItem(QRectF(scene_pos, scene_pos))
        pen = QPen(QColor(0, 120, 215)); pen.setStyle(Qt.DashLine)
        item.setPen(pen)
        self._scene.addItem(item)
        self._drag_rect_item = item

    def _update_drag_rect(self, viewport_pos) -> None:
        scene_pos = self.mapToScene(viewport_pos.toPoint())
        if self._drag_rect_item:
            self._drag_rect_item.setRect(QRectF(self._drag_start, scene_pos).normalized())

    def _handle_tool_release(self, event) -> None:
        t = self.tool
        index = getattr(self, "_drag_index", None)
        if t == "ink":
            if len(self._ink_points) > 1 and index is not None:
                stroke = [self.page_to_pdf_point(index, p) for p in self._ink_points]
                self.aboutToModify.emit()
                annot.add_ink(self.doc, index, [stroke], self.pen_color, self.pen_width)
                self.invalidate_page(index)
            self._ink_points = []
            self.viewport().update()
            return
        if self._drag_start is None or index is None:
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        dp_end = None
        hit = self.scene_to_page(scene_pos)
        if hit and hit[0] == index:
            dp_end = hit[1]
        if dp_end is None:
            self._cleanup_drag()
            return
        dp0 = self._drag_dp0
        if t == "whiteout":
            r = QRectF(dp0, dp_end).normalized()
            if r.width() > 1 and r.height() > 1:
                from ..core.editor import white_out
                self.aboutToModify.emit()
                white_out(self.doc, index, self.page_to_pdf_rect(index, r), remove_content=True)
                self.invalidate_page(index)
        elif t in ("highlight", "underline", "strikeout"):
            r = QRectF(dp0, dp_end).normalized()
            if r.width() > 2 and r.height() > 2:
                words = self.doc.page(index).get_text("words", clip=self.page_to_pdf_rect(index, r))
                rects = [fitz.Rect(w[:4]) for w in words]
                if rects:
                    color, opacity = self.markup_style(t)
                    self.aboutToModify.emit()
                    annot.add_markup(self.doc, index, t, rects, color, opacity)
                    self.invalidate_page(index)
        elif t in ("rect", "ellipse"):
            r = QRectF(dp0, dp_end).normalized()
            self.aboutToModify.emit()
            annot.add_shape(self.doc, index, t, self.page_to_pdf_rect(index, r),
                            self.pen_color, self.pen_width)
            self.invalidate_page(index)
        elif t in ("line", "arrow"):
            p1 = self.page_to_pdf_point(index, dp0)
            p2 = self.page_to_pdf_point(index, dp_end)
            self.aboutToModify.emit()
            annot.add_line(self.doc, index, p1, p2, self.pen_color,
                           self.pen_width, arrow=(t == "arrow"))
            self.invalidate_page(index)
        self._cleanup_drag()

    def _cleanup_drag(self) -> None:
        if self._drag_rect_item:
            self._scene.removeItem(self._drag_rect_item)
            self._drag_rect_item = None
        self._drag_start = None
        self._drag_index = None

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render_timer.start()
