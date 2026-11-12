"""Continuous, lazily-rendered PDF view with interaction tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import fitz
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView)

from ..core import annotations as annot
from ..core import editor as ed
from ..core.document import PdfDocument
from ..core.editor import TextSpan, iter_spans
from ..i18n import tr
from .theme import PAGE_AREA

# visual style of the editable-object selection frame
SEL_COLOR = QColor(0, 120, 215)
HANDLE_SIZE = 8.0
MIN_OBJECT_SIZE = 12.0
HANDLES = ("nw", "n", "ne", "e", "se", "s", "sw", "w")

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
    objectEditRequested = Signal(int)   # overlay index (double click)
    overlayChanged = Signal()           # overlays added / moved / removed

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setBackgroundBrush(QColor(PAGE_AREA))
        self.setFocusPolicy(Qt.StrongFocus)

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
        self.pending_images: List[dict] = []
        self._pending_owner = None
        self._img_drag = None
        self._selected: Optional[int] = None
        self._frame_items: List[object] = []
        self._img_snapshot: bool = False
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
        if doc is not self._pending_owner:
            self.pending_images.clear()
            self._img_drag = None
            self._selected = None
            self._frame_items = []
            self._pending_owner = doc
        self.doc = doc
        self.spans_cache.clear()
        self._rendered.clear()
        self._frame_items = []
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
        self._frame_items = []
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
        self._rebuild_pending_items()

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
            hit = self.scene_to_page(self.mapToScene(event.position().toPoint()))
            if hit and self.tool == "select":
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
            # Clicking an existing object always selects it first -- even while
            # the stamp / insert-image tool is active, so stamps stay movable.
            if hit and self.tool in ("select", "stamp", "insertimage"):
                index, dp = hit
                obj = self._overlay_hit(index, dp)
                if obj is None and self.tool == "select":
                    obj = self._select_baked_image(index, dp)
                if obj is not None:
                    idx, handle = obj
                    self._selected = idx
                    self._img_snapshot = False
                    self._img_drag = {"index": idx, "handle": handle, "page": index,
                                      "start": QPointF(dp),
                                      "rect": fitz.Rect(self.pending_images[idx]["rect"])}
                    self._rebuild_pending_items()
                    self.viewport().setCursor(self._cursor_for(handle))
                    event.accept()
                    return
                if self.tool == "select":
                    self._clear_baked_selections()
                    self._selected = None
                    self._rebuild_pending_items()
            if self.tool != "select":
                self._handle_tool_press(event)
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.doc and self.tool in ("select", "stamp", "insertimage"):
            hit = self.scene_to_page(self.mapToScene(event.position().toPoint()))
            if hit:
                index, dp = hit
                obj = self._overlay_hit(index, dp)
                if obj is not None:
                    self._selected = obj[0]
                    self._rebuild_pending_items()
                    self.objectEditRequested.emit(obj[0])
                    event.accept()
                    return
                xref = (annot.annot_xref_at(self.doc, index,
                                            self.page_to_pdf_point(index, dp))
                        if self.tool == "select" else None)
                if xref is not None:
                    self.annotEditRequested.emit(index, xref)
                    return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self._img_drag is not None:
            hit = self.scene_to_page(self.mapToScene(event.position().toPoint()))
            if hit:
                d = self._img_drag
                idx = d["index"]
                if idx >= len(self.pending_images):
                    self._img_drag = None
                    event.accept()
                    return
                if not self._img_snapshot:
                    self.aboutToModify.emit()      # one undo step per interaction
                    self._img_snapshot = True
                    self.materialize_overlay(idx, push=False)
                dp = hit[1]
                r0 = d["rect"]
                if d["handle"] is None:
                    dx = dp.x() - d["start"].x()
                    dy = dp.y() - d["start"].y()
                    new = fitz.Rect(r0.x0 + dx, r0.y0 + dy, r0.x1 + dx, r0.y1 + dy)
                else:
                    keep = not bool(event.modifiers() & Qt.ShiftModifier)
                    new = self._resized_rect(r0, d["handle"],
                                             fitz.Point(dp.x(), dp.y()), keep)
                self.pending_images[idx]["rect"] = self._clamp_display_rect(d["page"], new)
                self._rebuild_pending_items()
            event.accept()
            return
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
        if self.tool == "select" and self.doc:
            hit = self.scene_to_page(self.mapToScene(event.position().toPoint()))
            obj = self._overlay_hit(hit[0], hit[1]) if hit else None
            self.viewport().setCursor(self._cursor_for(obj[1]) if obj else Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._img_drag is not None:
            self._img_drag = None
            self._img_snapshot = False
            self.apply_cursor()
            self.doc.mark_dirty()
            self.overlayChanged.emit()
            event.accept()
            return
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

    # ------------------------------------------------------- editable overlays
    def add_pending_image(self, page: int, rect, source, *, kind: str = "image",
                          rotate: int = 0, baked: Optional[dict] = None,
                          select: bool = True) -> int:
        """Add an image/stamp as a movable, resizable overlay.

        ``rect`` is in *display* page coordinates (what the user sees); it is
        converted back to unrotated PDF coordinates when the overlay is baked.
        A ``baked`` entry means the picture is still drawn by the page itself
        and will only be detached when the user actually edits it.
        """
        self.pending_images.append({
            "page": int(page), "rect": fitz.Rect(rect), "source": source,
            "item": None, "kind": kind, "rotate": int(rotate or 0),
            "baked": baked,
        })
        idx = len(self.pending_images) - 1
        if select:
            self._selected = idx
        self._rebuild_pending_items()
        self.overlayChanged.emit()
        return idx

    def overlay_snapshot(self) -> List[dict]:
        """Plain-data copy of the overlay state (used by undo / redo)."""
        out = []
        for im in self.pending_images:
            baked = im.get("baked")
            copy = None
            if baked:
                copy = {"xref": baked["xref"], "bbox": fitz.Rect(baked["bbox"]),
                        "rotate": baked.get("rotate", 0),
                        "objects": [dict(o, bbox=fitz.Rect(o["bbox"]))
                                    for o in baked.get("objects", [])]}
            out.append({"page": im["page"], "rect": fitz.Rect(im["rect"]),
                        "source": im["source"], "item": None,
                        "kind": im.get("kind", "image"),
                        "rotate": im.get("rotate", 0), "baked": copy})
        return out

    def set_overlays(self, items: List[dict]) -> None:
        self._detach_items()
        self.pending_images = [dict(im) for im in items]
        self._selected = None
        self._img_drag = None
        self._img_snapshot = False
        self._rebuild_pending_items()

    def selected_object(self) -> Optional[dict]:
        if self._selected is None or not (0 <= self._selected < len(self.pending_images)):
            return None
        im = self.pending_images[self._selected]
        return {"index": self._selected, "page": im["page"],
                "rect": fitz.Rect(im["rect"]), "kind": im.get("kind", "image"),
                "baked": im.get("baked") is not None}

    def _pixmap_for(self, source) -> QPixmap:
        pm = QPixmap()
        if isinstance(source, (bytes, bytearray)):
            pm.loadFromData(bytes(source))
        else:
            pm.load(str(source))
        return pm

    # ---------------------------------------------------------- frame/handles
    def _clear_frame_items(self) -> None:
        for it in self._frame_items:
            try:
                self._scene.removeItem(it)
            except Exception:  # noqa: BLE001
                pass
        self._frame_items = []

    def _detach_items(self, indices=None) -> None:
        """Remove the scene graphics owned by overlays before changing the list."""
        targets = range(len(self.pending_images)) if indices is None else indices
        for i in targets:
            if 0 <= i < len(self.pending_images):
                im = self.pending_images[i]
                if im.get("item") is not None:
                    try:
                        self._scene.removeItem(im["item"])
                    except Exception:  # noqa: BLE001
                        pass
                    im["item"] = None
        self._clear_frame_items()

    @staticmethod
    def _handle_points(r: fitz.Rect) -> Dict[str, Tuple[float, float]]:
        mx, my = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
        return {"nw": (r.x0, r.y0), "n": (mx, r.y0), "ne": (r.x1, r.y0),
                "e": (r.x1, my), "se": (r.x1, r.y1), "s": (mx, r.y1),
                "sw": (r.x0, r.y1), "w": (r.x0, my)}

    def _draw_selection(self) -> None:
        self._clear_frame_items()
        if self._selected is None or not (0 <= self._selected < len(self.pending_images)):
            return
        if not self._geoms or not self.doc or not self.doc.is_open:
            return
        im = self.pending_images[self._selected]
        pg = im["page"]
        if pg < 0 or pg >= len(self._geoms):
            return
        g = self._geoms[pg]
        r = im["rect"]
        x, y = g.x + r.x0 * self.zoom, g.y + r.y0 * self.zoom
        w, h = r.width * self.zoom, r.height * self.zoom
        pen = QPen(SEL_COLOR); pen.setWidth(1); pen.setStyle(Qt.DashLine)
        frame = QGraphicsRectItem(QRectF(x, y, w, h))
        frame.setPen(pen); frame.setZValue(9)
        self._scene.addItem(frame); self._frame_items.append(frame)
        for _name, (px, py) in self._handle_points(r).items():
            sx, sy = g.x + px * self.zoom, g.y + py * self.zoom
            hp = QPen(SEL_COLOR); hp.setWidth(1)
            handle = QGraphicsRectItem(QRectF(sx - HANDLE_SIZE / 2,
                                              sy - HANDLE_SIZE / 2,
                                              HANDLE_SIZE, HANDLE_SIZE))
            handle.setPen(hp)
            handle.setBrush(QBrush(QColor(255, 255, 255)))
            handle.setZValue(10)
            self._scene.addItem(handle); self._frame_items.append(handle)
        label = QGraphicsSimpleTextItem(f"{r.width:.0f} x {r.height:.0f} pt")
        label.setBrush(QBrush(SEL_COLOR))
        br = label.boundingRect()
        plate = QGraphicsRectItem(QRectF(x, max(0.0, y - 20), br.width() + 8,
                                         br.height() + 2))
        plate.setPen(QPen(Qt.NoPen))
        plate.setBrush(QBrush(QColor(255, 255, 255)))
        plate.setZValue(9)
        label.setPos(x + 4, max(0.0, y - 20))
        label.setZValue(10)
        self._scene.addItem(plate); self._frame_items.append(plate)
        self._scene.addItem(label); self._frame_items.append(label)

    def _rebuild_pending_items(self) -> None:
        self._detach_items()
        if not self.doc or not self.doc.is_open or not self._geoms:
            return
        for im in self.pending_images:
            pg = im["page"]
            if pg < 0 or pg >= len(self._geoms):
                continue
            if im.get("baked") is not None:
                continue            # still rendered as part of the page bitmap
            g = self._geoms[pg]
            r = im["rect"]
            x = g.x + r.x0 * self.zoom
            y = g.y + r.y0 * self.zoom
            w = max(1, int(r.width * self.zoom))
            h = max(1, int(r.height * self.zoom))
            pm = self._pixmap_for(im["source"])
            if pm.isNull():
                continue
            item = QGraphicsPixmapItem(pm.scaled(w, h, Qt.IgnoreAspectRatio,
                                                 Qt.SmoothTransformation))
            item.setPos(x, y)
            item.setZValue(5)
            item.setTransformationMode(Qt.SmoothTransformation)
            self._scene.addItem(item)
            im["item"] = item
        self._draw_selection()

    def has_pending_images(self) -> bool:
        return any(im.get("baked") is None for im in self.pending_images)

    def bake_images(self) -> bool:
        """Write all loose overlays into the PDF (display -> PDF coordinates)."""
        if not self.doc:
            return False
        todo = [im for im in self.pending_images if im.get("baked") is None]
        if not todo:
            return False
        for im in todo:
            try:
                page = self.doc.page(im["page"])
                pdf_rect = fitz.Rect(im["rect"]) * page.derotation_matrix
                ed.insert_image_bytes(self.doc, im["page"], pdf_rect, im["source"],
                                      rotate=im.get("rotate") or 0)
            except Exception:  # noqa: BLE001
                pass
        self.doc.mark_dirty()
        self._detach_items()
        self.pending_images.clear()
        self._selected = None
        self._img_drag = None
        return True

    # ------------------------------------------------------------ hit testing
    @staticmethod
    def _cursor_for(handle: Optional[str]):
        if handle is None:
            return Qt.SizeAllCursor
        if handle in ("nw", "se"):
            return Qt.SizeFDiagCursor
        if handle in ("ne", "sw"):
            return Qt.SizeBDiagCursor
        if handle in ("n", "s"):
            return Qt.SizeVerCursor
        return Qt.SizeHorCursor

    def _overlay_hit(self, page: int, dp: QPointF):
        """Return (index, handle) for an overlay at a display-space point."""
        tol = 10.0 / max(0.1, self.zoom)
        p = fitz.Point(dp.x(), dp.y())
        for i in range(len(self.pending_images) - 1, -1, -1):
            im = self.pending_images[i]
            if im["page"] != page:
                continue
            r = im["rect"]
            outer = fitz.Rect(r.x0 - tol, r.y0 - tol, r.x1 + tol, r.y1 + tol)
            if not outer.contains(p):
                continue
            if i == self._selected:
                for name, (cx, cy) in self._handle_points(r).items():
                    if abs(p.x - cx) <= tol and abs(p.y - cy) <= tol:
                        return i, name
            return i, None
        return None

    def _select_baked_image(self, page: int, dp: QPointF):
        """Pick an image/stamp already baked into the PDF, without touching it."""
        if not self.doc or not self.doc.is_open:
            return None
        pg = self.doc.page(page)
        try:
            objects = ed.list_image_objects(self.doc, page)
        except Exception:  # noqa: BLE001
            return None
        if not objects:
            return None
        tol = 4.0 / max(0.1, self.zoom)
        pdf_pt = fitz.Point(dp.x(), dp.y()) * pg.derotation_matrix
        best, best_key = None, None
        for n, o in enumerate(objects):
            b = o["bbox"]
            if not fitz.Rect(b.x0 - tol, b.y0 - tol, b.x1 + tol, b.y1 + tol).contains(pdf_pt):
                continue
            key = (b.get_area(), -n)       # prefer the smallest / topmost object
            if best_key is None or key < best_key:
                best, best_key = o, key
        if best is None:
            return None
        try:
            data = ed.image_object_bytes(self.doc, best["xref"])
        except Exception:  # noqa: BLE001
            return None
        display_rect = fitz.Rect(best["bbox"]) * pg.rotation_matrix
        baked = {"xref": best["xref"], "bbox": fitz.Rect(best["bbox"]),
                 "rotate": best["rotate"], "objects": objects}
        idx = self.add_pending_image(page, display_rect, data, kind="image",
                                     rotate=best["rotate"], baked=baked, select=True)
        self.statusMessage.emit(tr("msg.object_selected"))
        return idx, None

    def _clear_baked_selections(self) -> None:
        doomed = [i for i, im in enumerate(self.pending_images)
                  if im.get("baked") is not None]
        if not doomed:
            return
        self._detach_items(doomed)
        self.pending_images = [im for i, im in enumerate(self.pending_images)
                               if i not in set(doomed)]
        self._selected = None
        self._rebuild_pending_items()

    # --------------------------------------------------------- object editing
    def materialize_overlay(self, idx: int, push: bool = True) -> bool:
        """Detach a baked image so further edits happen on a movable overlay."""
        if not (0 <= idx < len(self.pending_images)):
            return False
        im = self.pending_images[idx]
        baked = im.get("baked")
        if baked is None:
            return False
        if push:
            self.aboutToModify.emit()
        try:
            data = ed.lift_image_object(self.doc, im["page"], baked,
                                        baked.get("objects"))
        except Exception as exc:  # noqa: BLE001
            self.statusMessage.emit(str(exc))
            return False
        im["source"] = data
        im["baked"] = None
        self.doc.mark_dirty()
        self.invalidate_page(im["page"])
        self._rebuild_pending_items()
        self.overlayChanged.emit()
        return True

    def set_object_rect(self, idx: int, rect, push: bool = True) -> None:
        if not (0 <= idx < len(self.pending_images)):
            return
        if push:
            self.aboutToModify.emit()
        self.materialize_overlay(idx, push=False)
        im = self.pending_images[idx]
        im["rect"] = self._clamp_display_rect(im["page"], fitz.Rect(rect))
        self._rebuild_pending_items()
        self.doc.mark_dirty()
        self.overlayChanged.emit()

    def remove_selected(self) -> bool:
        idx = self._selected
        if idx is None or not (0 <= idx < len(self.pending_images)):
            return False
        self.aboutToModify.emit()
        self.materialize_overlay(idx, push=False)
        self._detach_items([idx])
        del self.pending_images[idx]
        self._selected = None
        self._img_drag = None
        self._rebuild_pending_items()
        self.doc.mark_dirty()
        self.overlayChanged.emit()
        return True

    def _clamp_display_rect(self, page_index: int, r: fitz.Rect) -> fitz.Rect:
        try:
            pr = self.doc.page(page_index).rect
        except Exception:  # noqa: BLE001
            return r
        dx = dy = 0.0
        if r.x0 < 0:
            dx = -r.x0
        elif r.x1 > pr.width:
            dx = pr.width - r.x1
        if r.y0 < 0:
            dy = -r.y0
        elif r.y1 > pr.height:
            dy = pr.height - r.y1
        return fitz.Rect(r.x0 + dx, r.y0 + dy, r.x1 + dx, r.y1 + dy)

    @staticmethod
    def _resized_rect(r: fitz.Rect, handle: str, pt,
                      keep_aspect: bool = True) -> fitz.Rect:
        """Resize around the opposite corner/edge; ``Shift`` unlocks the ratio."""
        x0, y0, x1, y1 = r.x0, r.y0, r.x1, r.y1
        if r.width <= 0 or r.height <= 0:
            return r
        m = MIN_OBJECT_SIZE
        has_w, has_e = "w" in handle, "e" in handle
        has_n, has_s = "n" in handle, "s" in handle
        nx0, ny0, nx1, ny1 = x0, y0, x1, y1
        if has_w:
            nx0 = min(pt.x, x1 - m)
        if has_e:
            nx1 = max(pt.x, x0 + m)
        if has_n:
            ny0 = min(pt.y, y1 - m)
        if has_s:
            ny1 = max(pt.y, y0 + m)
        if not keep_aspect:
            return fitz.Rect(nx0, ny0, max(nx0 + m, nx1), max(ny0 + m, ny1))
        ar = r.width / r.height
        if has_w or has_e:
            nw = max(m, nx1 - nx0)
            nh = nw / ar
        else:
            nh = max(m, ny1 - ny0)
            nw = nh * ar
        nw, nh = max(m, nw), max(m, nh)
        if has_w:
            ax = x1 - nw
        elif has_e:
            ax = x0
        else:
            ax = (x0 + x1) / 2 - nw / 2
        if has_n:
            ay = y1 - nh
        elif has_s:
            ay = y0
        else:
            ay = (y0 + y1) / 2 - nh / 2
        return fitz.Rect(ax, ay, ax + nw, ay + nh)

    def keyPressEvent(self, event) -> None:
        if self.tool in ("select", "stamp", "insertimage") and self._selected is not None:
            key = event.key()
            if key in (Qt.Key_Delete, Qt.Key_Backspace):
                self.remove_selected()
                event.accept()
                return
            step = 10.0 if event.modifiers() & Qt.ShiftModifier else 1.0
            moves = {Qt.Key_Left: (-step, 0.0), Qt.Key_Right: (step, 0.0),
                     Qt.Key_Up: (0.0, -step), Qt.Key_Down: (0.0, step)}
            if key in moves and 0 <= self._selected < len(self.pending_images):
                dx, dy = moves[key]
                r = self.pending_images[self._selected]["rect"]
                self.set_object_rect(self._selected,
                                     fitz.Rect(r.x0 + dx, r.y0 + dy,
                                               r.x1 + dx, r.y1 + dy))
                event.accept()
                return
        super().keyPressEvent(event)

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
