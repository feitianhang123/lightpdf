"""Annotation authoring helpers on top of PyMuPDF."""
from __future__ import annotations

from typing import List, Optional, Sequence

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


def words_for_markup(page, rect, *, pad_x: float = 0.5,
                     pad_y: float = 1.5) -> List[fitz.Rect]:
    """Return text rectangles for highlight / underline / strikeout.

    Selection is deliberately forgiving in one direction and precise in the
    other:

    * **Vertical (forgiving)**: text is grouped into lines, and a line is hit
      when its vertical span overlaps the dragged box (padded by ``pad_y``).
      A shallow horizontal swipe is enough -- the box does not have to cover
      the line's full height.
    * **Horizontal (precise)**: only the characters actually swept over are
      marked, i.e. the highlight spans exactly as far as the drag.  Character
      granularity matters for CJK text, where a whole sentence is a single
      ``word`` to PyMuPDF -- word-level selection would mark the entire line.
      ``pad_x`` adds a tiny tolerance so the edges need not be pixel-perfect.

    Selected characters that touch each other are merged into one rectangle,
    so the result is a continuous highlight instead of one block per glyph.
    Nothing outside the dragged span is touched: other lines, other columns
    and blank margins are never marked.  ``rect`` and the returned rectangles
    are in unrotated PDF page coordinates (the space ``page.get_text`` uses).
    """
    box = fitz.Rect(rect)
    hit = fitz.Rect(box.x0 - pad_x, box.y0 - pad_y,
                    box.x1 + pad_x, box.y1 + pad_y)
    raw = page.get_text("rawdict")
    out: List[fitz.Rect] = []
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            lb = fitz.Rect(line["bbox"])
            if lb.y1 < hit.y0 or lb.y0 > hit.y1:   # vertical: line snapping
                continue
            chosen = []
            for span in line.get("spans", []):
                for ch in span.get("chars", []):
                    cb = fitz.Rect(ch["bbox"])
                    if cb.x1 >= hit.x0 and cb.x0 <= hit.x1:   # horizontal: swept span
                        chosen.append(cb)
            # merge touching characters into continuous runs
            for r in sorted(chosen, key=lambda q: q.x0):
                if out:
                    prev = out[-1]
                    if (abs(prev.y0 - r.y0) < 2 and abs(prev.y1 - r.y1) < 2
                            and r.x0 <= prev.x1 + 2.0):
                        out[-1] = fitz.Rect(prev.x0, min(prev.y0, r.y0),
                                            max(prev.x1, r.x1), max(prev.y1, r.y1))
                        continue
                out.append(fitz.Rect(r))
    return out


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


def insert_riding_stamp(doc: PdfDocument, assignments: list, *,
                        margin_mm: float = 4.23,
                        top_mm: Optional[float] = None) -> None:
    """Place one vertical slice of a seal on the edge of each page (骑缝章).

    ``assignments`` items are ``(page_index, png_bytes, width_pt, height_pt,
    slot_index)``.  ``slot_index`` is the position within one seal group and
    drives odd/even edges for double-sided printing: slice 0 goes to the right
    edge of page 1, slice 1 to the left edge of page 2, etc.  Stacking the
    sheets then reassembles the seal.

    Edge distance and vertical position are given in millimetres.  All pages
    share the same ``top_mm`` (top edge of the seal, measured from the page
    top), so a single vertical value moves every stamped page in sync.  When
    ``top_mm`` is omitted the seal is vertically centred on each page.
    """
    pt_per_mm = 72.0 / 25.4
    margin_pt = float(margin_mm) * pt_per_mm
    for page_index, data, sw, sh, slot in assignments:
        page = doc.page(page_index)
        pr = page.rect
        right = (slot % 2 == 0)
        x0 = (pr.width - margin_pt - sw) if right else margin_pt
        avail = max(0.0, pr.height - sh)
        if top_mm is None:
            y0 = avail / 2.0
        else:
            y0 = max(0.0, min(avail, float(top_mm) * pt_per_mm))
        rect = fitz.Rect(x0, y0, x0 + sw, y0 + sh)
        # PyMuPDF places images in *unrotated* page coordinates while
        # ``page.rect`` is the visible (rotated) rectangle.  For landscape
        # pages (/Rotate 90/180/270) map the visible rect back and pre-rotate
        # the slice by the same angle, otherwise it lands outside the sheet.
        rot = page.rotation or 0
        if rot:
            rect = rect * page.derotation_matrix
        page.insert_image(rect, stream=bytes(data), keep_proportion=False,
                          overlay=True, rotate=rot)
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
