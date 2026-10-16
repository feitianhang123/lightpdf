"""Annotation authoring helpers on top of PyMuPDF."""
from __future__ import annotations

from typing import List, Sequence

import fitz

from .document import PdfDocument, PdfError

Color = tuple  # (r, g, b) floats 0..1 or ints 0..255


def _as_fitz_color(color: Color) -> tuple:
    """Accept 0..1 floats or 0..255 ints and return 0..1 floats.

    Values are treated as 0..255 only when some component exceeds 1, so the
    common 0..1 convention (e.g. (1, 1, 0) = yellow) is preserved.
    """
    vals = list(color)
    if any(float(v) > 1.0 for v in vals):
        return tuple(max(0.0, min(1.0, float(v) / 255.0)) for v in vals)
    return tuple(max(0.0, min(1.0, float(v))) for v in vals)


MARKUP_KINDS = {
    "highlight": "add_highlight_annot",
    "underline": "add_underline_annot",
    "strikeout": "add_strikeout_annot",
    "squiggly": "add_squiggly_annot",
}


def add_markup(doc: PdfDocument, page_index: int, kind: str, rects: Sequence[fitz.Rect],
               color: Color = (1, 1, 0), opacity: float = 0.3) -> None:
    if kind not in MARKUP_KINDS:
        raise PdfError(f"Unknown markup kind: {kind}")
    if not rects:
        raise PdfError("No text selected.")
    page = doc.page(page_index)
    quads = [r if isinstance(r, fitz.Rect) else fitz.Rect(r) for r in rects]
    annot = getattr(page, MARKUP_KINDS[kind])(quads)
    annot.set_colors(stroke=_as_fitz_color(color))
    try:
        annot.set_opacity(max(0.05, min(1.0, float(opacity))))
    except Exception:  # noqa: BLE001
        pass
    annot.update()
    doc.mark_dirty()


def add_note(doc: PdfDocument, page_index: int, point: fitz.Point, text: str,
             color: Color = (1, 0.8, 0)) -> None:
    page = doc.page(page_index)
    annot = page.add_text_annot(point, text or "")
    annot.set_colors(stroke=_as_fitz_color(color))
    annot.set_info(content=text or "")
    annot.update()
    doc.mark_dirty()


def add_freetext(doc: PdfDocument, page_index: int, rect: fitz.Rect, text: str,
                 fontsize: float = 12, color: Color = (0, 0, 0),
                 fill: Color | None = None, fontname: str = "helv",
                 fontfile: str | None = None) -> None:
    page = doc.page(page_index)
    if fontfile:
        try:
            page.insert_font(fontname="FXbox", fontfile=fontfile)
            fontname = "FXbox"
        except Exception:  # noqa: BLE001
            fontname = "helv"
    annot = page.add_freetext_annot(rect, text, fontsize=fontsize, fontname=fontname,
                                    text_color=_as_fitz_color(color),
                                    fill_color=_as_fitz_color(fill) if fill is not None else None)
    try:
        annot.set_border(width=0)   # no visible frame
    except Exception:  # noqa: BLE001
        pass
    annot.update()
    doc.mark_dirty()


def add_ink(doc: PdfDocument, page_index: int, strokes: Sequence[Sequence[fitz.Point]],
            color: Color = (1, 0, 0), width: float = 1.5) -> None:
    if not strokes:
        raise PdfError("Empty ink stroke.")
    page = doc.page(page_index)
    pairs = [[(float(p.x), float(p.y)) for p in s] for s in strokes]
    annot = page.add_ink_annot(pairs)
    annot.set_colors(stroke=_as_fitz_color(color))
    annot.set_border(width=width)
    annot.update()
    doc.mark_dirty()


def add_shape(doc: PdfDocument, page_index: int, kind: str, rect: fitz.Rect,
              color: Color = (1, 0, 0), width: float = 1.5,
              fill: Color | None = None) -> None:
    page = doc.page(page_index)
    if kind == "rect":
        annot = page.add_rect_annot(rect)
    elif kind == "ellipse":
        annot = page.add_circle_annot(rect)
    else:
        raise PdfError(f"Unknown shape: {kind}")
    annot.set_colors(stroke=_as_fitz_color(color),
                     fill=_as_fitz_color(fill) if fill else None)
    annot.set_border(width=width)
    annot.update()
    doc.mark_dirty()


def add_line(doc: PdfDocument, page_index: int, p1: fitz.Point, p2: fitz.Point,
             color: Color = (1, 0, 0), width: float = 1.5, arrow: bool = False) -> None:
    page = doc.page(page_index)
    annot = page.add_line_annot(p1, p2)
    annot.set_colors(stroke=_as_fitz_color(color))
    annot.set_border(width=width)
    if arrow:
        annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_OPEN_ARROW)
    annot.update()
    doc.mark_dirty()


STAMPS = ["Approved", "Not Approved", "Draft", "Confidential", "Final",
          "For Comment", "Void", "Reviewed"]


def add_stamp(doc: PdfDocument, page_index: int, rect: fitz.Rect, text: str,
              color: Color = (0.8, 0, 0)) -> None:
    page = doc.page(page_index)
    annot = page.add_stamp_annot(rect, stamp=max(0, min(21, len(text) % 22)))
    annot.set_info(content=text)
    annot.set_colors(stroke=_as_fitz_color(color))
    annot.update()
    doc.mark_dirty()


def insert_stamp_image(doc: PdfDocument, page_index: int, rect: fitz.Rect,
                       png_bytes: bytes) -> None:
    """Insert a rendered (custom) stamp as an image on the page."""
    page = doc.page(page_index)
    page.insert_image(rect, stream=bytes(png_bytes), keep_proportion=True)
    doc.mark_dirty()


# ------------------------------------------------------------------ inspect
def list_annotations(doc: PdfDocument, page_index: int) -> List[dict]:
    page = doc.page(page_index)
    out = []
    for a in page.annots() or []:
        out.append({
            "type": a.type[1],
            "rect": a.rect,
            "content": a.info.get("content", ""),
            "xref": a.xref,
        })
    return out


def annot_xref_at(doc: PdfDocument, page_index: int, point) -> "int | None":
    """Return the xref of the topmost annotation containing `point` (page coords).

    Only the xref is returned so callers never hold an Annot across events."""
    page = doc.page(page_index)
    for a in page.annots() or []:
        try:
            if a.rect.contains(point):
                return a.xref
        except Exception:  # noqa: BLE001
            continue
    return None


def annot_info(doc: PdfDocument, page_index: int, xref: int) -> dict:
    page = doc.page(page_index)
    for a in page.annots() or []:
        if a.xref == xref:
            return {"type": a.type[1], "content": a.info.get("content", "")}
    return {}


def move_annot(doc: PdfDocument, page_index: int, xref: int, dx: float, dy: float) -> bool:
    """Translate one annotation; the page object stays alive for the whole call."""
    page = doc.page(page_index)
    for a in page.annots() or []:
        if a.xref == xref:
            r = a.rect
            a.set_rect(fitz.Rect(r.x0 + dx, r.y0 + dy, r.x1 + dx, r.y1 + dy))
            a.update()
            doc.mark_dirty()
            return True
    return False


def set_annot_content(doc: PdfDocument, page_index: int, xref: int, text: str) -> bool:
    page = doc.page(page_index)
    for a in page.annots() or []:
        if a.xref == xref:
            a.set_info(content=text)
            a.update()
            doc.mark_dirty()
            return True
    return False


def annot_rect_content(doc: PdfDocument, page_index: int, xref: int):
    """Return (rect, content) for one annotation xref, or None."""
    page = doc.page(page_index)
    for a in page.annots() or []:
        if a.xref == xref:
            return a.rect, a.info.get("content", "")
    return None


def delete_annot(doc: PdfDocument, page_index: int, xref: int) -> bool:
    page = doc.page(page_index)
    for a in page.annots() or []:
        if a.xref == xref:
            page.delete_annot(a)
            doc.mark_dirty()
            return True
    return False


def delete_annotation(doc: PdfDocument, page_index: int, annot) -> None:
    page = doc.page(page_index)
    page.delete_annot(annot)
    doc.mark_dirty()
