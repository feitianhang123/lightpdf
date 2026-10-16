"""Content editing: text (touchup-style), text boxes, images and white-out.

True vector-object editing is intentionally out of scope; this module provides
the practical subset: edit existing text runs, add new text/images, and erase
regions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import fitz

from .document import PdfDocument, PdfError

# base-14 heuristic map from common embedded font names
_BASE14 = {
    "arial": "helv", "helvetica": "helv", "liberationsans": "helv",
    "timesnewroman": "tiro", "times": "tiro", "liberationserif": "tiro",
    "couriernew": "cour", "courier": "cour", "liberationmono": "cour",
}


@dataclass
class TextSpan:
    page: int
    bbox: fitz.Rect
    origin: fitz.Point
    text: str
    font: str
    size: float
    color: int  # sRGB int
    flags: int

    @property
    def color_rgb(self) -> tuple:
        return ((self.color >> 16) & 255, (self.color >> 8) & 255, self.color & 255)


def iter_spans(doc: PdfDocument, page_index: int) -> List[TextSpan]:
    page = doc.page(page_index)
    spans: List[TextSpan] = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if not span.get("text", "").strip():
                    continue
                spans.append(TextSpan(
                    page=page_index,
                    bbox=fitz.Rect(span["bbox"]),
                    origin=fitz.Point(span["origin"]),
                    text=span["text"],
                    font=span.get("font", ""),
                    size=float(span.get("size", 12)),
                    color=int(span.get("color", 0)),
                    flags=int(span.get("flags", 0)),
                ))
    return spans


def _pick_base14(font_name: str) -> str:
    key = "".join(ch for ch in font_name.lower() if ch.isalnum())
    for token, base in _BASE14.items():
        if token in key:
            return base
    return "helv"


def text_size(text: str, fontname: str = "helv", fontsize: float = 12.0,
              fontfile: Optional[str] = None) -> tuple:
    """Approximate rendered (width, height) of a text block, for auto-sizing."""
    lines = text.split("\n") or [""]
    try:
        font = fitz.Font(fontfile=fontfile) if fontfile else fitz.Font(fontname=fontname)
        widths = [font.text_length(ln, fontsize) for ln in lines]
        width = max(widths) if widths else 0.0
    except Exception:  # noqa: BLE001
        # crude fallback (CJK chars are about one em wide)
        width = 0.0
        for ln in lines:
            w = 0.0
            for ch in ln:
                w += fontsize * (1.0 if ord(ch) > 0x2E7F else 0.55)
            width = max(width, w)
    height = len(lines) * fontsize * 1.4
    return width, height


def _cjk_font_for(text: str) -> Optional[str]:
    """Return a built-in CJK font name when the text contains CJK glyphs."""
    for ch in text:
        o = ord(ch)
        if (0x2E80 <= o <= 0x9FFF or 0x3040 <= o <= 0x30FF
                or 0xAC00 <= o <= 0xD7A3 or 0xF900 <= o <= 0xFAFF):
            return "china-s"
    return None


def _font_buffer(doc: PdfDocument, page: fitz.Page, basefont: str) -> Optional[bytes]:
    """Try to fetch the original embedded font program so re-typed text keeps
    the same glyphs (critical for CJK and non-Latin content)."""
    if not basefont:
        return None
    try:
        fonts = page.get_fonts(full=True)
    except Exception:  # noqa: BLE001
        return None
    target = basefont.split("+")[-1].lower()
    for f in fonts:
        name = (f[3] or "")
        if target and target in name.lower():
            try:
                _b, _e, _s, buf = doc.doc.extract_font(f[0])
                if buf:
                    return buf
            except Exception:  # noqa: BLE001
                continue
    return None


def replace_span(doc: PdfDocument, span: TextSpan, new_text: str,
                 *, fontname: Optional[str] = None, fontsize: Optional[float] = None,
                 color: Optional[tuple] = None, fontfile: Optional[str] = None) -> None:
    """Erase a text run and rewrite it (touchup-style edit).

    If the text, font and size are all unchanged the document is left untouched."""
    size_same = fontsize is None or abs(float(fontsize) - float(span.size)) < 0.01
    if new_text == span.text and fontname is None and fontfile is None and size_same:
        return
    page = doc.page(span.page)
    fs = fontsize or span.size
    rgb = color or span.color_rgb
    col = tuple(c / 255.0 for c in rgb)
    buf = None if (fontname or fontfile) else _font_buffer(doc, page, span.font)

    # remove original glyphs but keep images/graphics underneath
    page.add_redact_annot(span.bbox)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    if fontfile:
        try:
            page.insert_text(span.origin, new_text, fontsize=fs, color=col,
                             render_mode=0, fontfile=fontfile, fontname="F0")
            doc.mark_dirty()
            return
        except Exception:  # noqa: BLE001
            pass

    if buf:
        try:
            page.insert_text(span.origin, new_text, fontsize=fs, color=col,
                             render_mode=0, fontbuffer=buf, fontname="origfont")
            doc.mark_dirty()
            return
        except Exception:  # noqa: BLE001
            pass
    fn = fontname or _cjk_font_for(new_text) or _pick_base14(span.font)
    page.insert_text(span.origin, new_text, fontsize=fs, fontname=fn,
                     color=col, render_mode=0)
    doc.mark_dirty()


def white_out(doc: PdfDocument, page_index: int, rect: fitz.Rect,
              *, remove_content: bool = True) -> None:
    page = doc.page(page_index)
    if remove_content:
        page.add_redact_annot(rect)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)
    else:
        page.draw_rect(rect, color=None, fill=(1, 1, 1), fill_opacity=1)
    doc.mark_dirty()


def insert_text_box(doc: PdfDocument, page_index: int, rect: fitz.Rect, text: str,
                    *, fontsize: float = 12, color: tuple = (0, 0, 0),
                    fontname: str = "helv") -> None:
    page = doc.page(page_index)
    rc = page.insert_textbox(rect, text, fontsize=fontsize, color=color,
                             fontname=fontname, align=0)
    if rc < 0:
        raise PdfError("Text does not fit in the box; enlarge it or reduce font size.")
    doc.mark_dirty()


def insert_image(doc: PdfDocument, page_index: int, rect: fitz.Rect,
                 image_path: str) -> None:
    page = doc.page(page_index)
    try:
        page.insert_image(rect, filename=image_path, keep_proportion=True)
    except Exception as exc:  # noqa: BLE001
        raise PdfError(f"Image insert failed: {exc}") from exc
    doc.mark_dirty()


def replace_image(doc: PdfDocument, page_index: int, image_xref: int,
                  image_path: str) -> None:
    """Replace an embedded image in place."""
    page = doc.page(page_index)
    try:
        page.replace_image(image_xref, filename=image_path)
    except Exception as exc:  # noqa: BLE001
        raise PdfError(f"Image replace failed: {exc}") from exc
    doc.mark_dirty()


def list_images(doc: PdfDocument, page_index: int) -> List[dict]:
    page = doc.page(page_index)
    out = []
    for img in page.get_images(full=True):
        xref = img[0]
        rects = page.get_image_rects(xref)
        out.append({"xref": xref, "rects": rects,
                    "width": img[2], "height": img[3]})
    return out
