"""Annotation authoring helpers on top of PyMuPDF."""
from __future__ import annotations

import struct
import uuid
import zlib
from typing import List, Optional, Sequence

import fitz

from .document import PdfDocument, PdfError

Color = tuple  # (r, g, b) floats 0..1 or ints 0..255

# 骑缝章分组标记：写在每个切片图片对象的字典里，随 PDF 一起持久化。
# 同一枚章的所有切片共享一个 group id；这样重开文件后仍能识别"哪些切片属于
# 同一枚章"，拖动其中一页时把垂直位移同步给整组，水平位置则锁定。
RIDING_GROUP_KEY = "LightpdfRidingGroup"
RIDING_SLOT_KEY = "LightpdfRidingSlot"


def _group_key_value(doc: PdfDocument, xref: int, key: str) -> Optional[int]:
    if not doc or not doc.doc or xref <= 0:
        return None
    try:
        kind, value = doc.doc.xref_get_key(int(xref), key)
    except Exception:  # noqa: BLE001
        return None
    if kind not in ("int", "xnumber", "number"):
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def riding_group_at(doc: PdfDocument, xref: int) -> Optional[int]:
    """Return the riding-stamp group id of an image xref, or ``None``."""
    return _group_key_value(doc, xref, RIDING_GROUP_KEY)


def riding_slot_at(doc: PdfDocument, xref: int) -> int:
    return _group_key_value(doc, xref, RIDING_SLOT_KEY) or 0


def tag_riding_slice(doc: PdfDocument, xref: int, group_id: int, slot: int) -> None:
    """Tag an inserted slice image so it can be found as part of a seal group."""
    if not doc.doc or xref <= 0:
        return
    try:
        doc.doc.xref_set_key(int(xref), RIDING_GROUP_KEY, str(int(group_id)))
        doc.doc.xref_set_key(int(xref), RIDING_SLOT_KEY, str(int(slot)))
    except Exception:  # noqa: BLE001
        pass


def unique_png_bytes(png: bytes, group_id: int = 0, slot: int = 0) -> bytes:
    """Give an image stream a unique digest without changing its pixels.

    PyMuPDF de-duplicates identical image streams by content digest.  Two
    riding-stamp slices that happen to be pixel-identical would otherwise share
    one PDF xref, and the second ``tag_riding_slice`` would overwrite the first
    slice's group/slot — breaking the "all slices of one seal move together"
    rule.  Adding a private PNG text chunk changes only the stream digest.
    """
    sig = b"\x89PNG\r\n\x1a\n"
    if not png or not png.startswith(sig):
        return png
    marker = ("LightpdfRiding-%d-%d-%s" %
              (int(group_id), int(slot), uuid.uuid4().hex)).encode("ascii")
    text = b"LightpdfStamp\0" + marker
    chunk = (struct.pack(">I", len(text)) + b"tEXt" + text +
             struct.pack(">I", zlib.crc32(b"tEXt" + text) & 0xFFFFFFFF))
    out = bytearray(sig)
    pos = len(sig)
    while pos + 8 <= len(png):
        length = struct.unpack(">I", png[pos:pos + 4])[0]
        ctype = png[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(png):
            return png                      # malformed: do not touch it
        if ctype == b"IEND":
            out.extend(chunk)
        out.extend(png[pos:end])
        pos = end
        if ctype == b"IEND":
            out.extend(png[pos:])           # keep any trailing bytes verbatim
            break
    return bytes(out)


def next_riding_group_base(doc: PdfDocument) -> int:
    """Group id for the next stamp: one above the largest id already in the PDF."""
    biggest = 0
    if not doc or not doc.doc:
        return 1
    for page_index in range(doc.page_count):
        try:
            infos = doc.page(page_index).get_image_info(xrefs=True)
        except Exception:  # noqa: BLE001
            continue
        for info in infos:
            gid = riding_group_at(doc, int(info.get("xref") or 0))
            if gid is not None and gid > biggest:
                biggest = gid
    return biggest + 1


def _transform_rotation(transform) -> int:
    if not transform or len(transform) < 6:
        return 0
    a, b = float(transform[0]), float(transform[1])
    if abs(a) >= abs(b):
        return 0 if a >= 0 else 180
    return 270 if b > 0 else 90


def find_riding_group(doc: PdfDocument, group_id: int) -> List[dict]:
    """All slices of one seal across the document.

    Each entry: ``{page, xref, bbox, rotate, slot}``.  ``bbox`` is in the
    page's unrotated coordinate space; callers map it back to display space.
    """
    out: List[dict] = []
    if not doc or not doc.doc:
        return out
    for page_index in range(doc.page_count):
        try:
            page = doc.page(page_index)
            infos = page.get_image_info(xrefs=True)
        except Exception:  # noqa: BLE001
            continue
        for info in infos:
            xref = int(info.get("xref") or 0)
            if riding_group_at(doc, xref) != int(group_id):
                continue
            out.append({"page": page_index, "xref": xref,
                        "bbox": fitz.Rect(info["bbox"]),
                        "rotate": _transform_rotation(info.get("transform")),
                        "slot": riding_slot_at(doc, xref)})
    out.sort(key=lambda s: (s["page"], s["slot"]))
    return out


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
                        top_mm: Optional[float] = None,
                        side: str = "alternate",
                        group_base: Optional[int] = None) -> int:
    """Return the first group id used (assignments may contain several seals)."""
    """Place one vertical slice of a seal on the edge of each page (骑缝章).

    ``assignments`` items are ``(page_index, png_bytes, width_pt, height_pt,
    slot_index, seal_seq)``.  ``slot_index`` is the slice's order inside one
    seal group; ``seal_seq`` distinguishes several seals laid out in one job.
    Legacy 5-tuples are still accepted as a single seal.

    ``side`` is the binding/placement convention, using standard print-shop
    terminology:

    * ``"right"``        - every slice on the right edge (simplex);
    * ``"left"``         - every slice on the left edge (simplex);
    * ``"alternate"``    - odd pages right / even pages left (standard duplex):
                           stacking the sheets rebuilds one complete seal;
    * ``"alternate_rev"`` - odd pages left / even pages right (reverse duplex).

    The odd/even test uses the **1-based page number**, so the convention holds
    even when the user stamps a non-1-based page range.  Edge distance and
    vertical position are in millimetres.  All pages share one ``top_mm``
    (seal top measured from the page top), so a single vertical value moves
    every stamped page in sync.  ``None`` centres the seal vertically.
    """
    pt_per_mm = 72.0 / 25.4
    margin_pt = float(margin_mm) * pt_per_mm
    if group_base is None:
        group_base = next_riding_group_base(doc)
    first_group = None
    # Each item is (page, png, w, h, slot, seal_seq).  Old 5-tuples are still
    # accepted and treated as a single seal.
    for item in assignments:
        if len(item) >= 6:
            page_index, data, sw, sh, slot, seal_seq = item
        else:
            page_index, data, sw, sh, slot = item
            seal_seq = 0
        group_id = int(group_base) + int(seal_seq)
        if first_group is None:
            first_group = group_id
        page = doc.page(page_index)
        pr = page.rect
        odd_page = (int(page_index) + 1) % 2 == 1
        if side == "right":
            right = True
        elif side == "left":
            right = False
        elif side == "alternate_rev":
            right = not odd_page
        else:  # "alternate" (default) — standard duplex binding
            right = odd_page
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
        # Force a distinct image object even when two slices are pixel-identical.
        # Otherwise PyMuPDF reuses one xref and the group tag of the first seal
        # is silently overwritten by the second.
        data = unique_png_bytes(bytes(data), group_id, slot)
        xref = page.insert_image(rect, stream=data, keep_proportion=False,
                                 overlay=True, rotate=rot)
        tag_riding_slice(doc, xref, group_id, slot)
    doc.mark_dirty()
    return first_group if first_group is not None else int(group_base)


def shift_riding_group_y(doc: PdfDocument, group_id: int, dy: float,
                         skip_xref: int = 0) -> dict:
    """Move every baked slice of a seal vertically by ``dy`` display points.

    Horizontal coordinates and slice sizes are untouched: a riding seal only
    slides up/down as one piece.  ``skip_xref`` is the slice currently being
    edited as a live overlay (already detached from the PDF).

    Returns ``{old_xref: (new_xref, new_bbox_unrotated)}`` so the caller can
    keep its own overlay state in sync (re-inserting creates a new xref).
    """
    moved: dict = {}
    if not doc or not doc.doc or abs(float(dy)) < 1e-6:
        return moved
    slices = [s for s in find_riding_group(doc, group_id) if s["xref"] != skip_xref]
    # Extract bytes before any delete (delete_image invalidates the xref).
    payload = {}
    for s in slices:
        try:
            payload[s["xref"]] = image_object_bytes_for(doc, s["xref"])
        except Exception:  # noqa: BLE001
            pass
    for s in slices:
        xref = s["xref"]
        if xref not in payload:
            continue
        page = doc.page(s["page"])
        # bbox from get_image_info is in unrotated page coordinates; the drag
        # delta is in visible/display points, so round-trip through the page
        # rotation matrices.  For unrotated pages both matrices are identity.
        shown = s["bbox"] * page.rotation_matrix
        new_shown = fitz.Rect(shown.x0, shown.y0 + float(dy),
                              shown.x1, shown.y1 + float(dy))
        new_unrot = new_shown * page.derotation_matrix
        try:
            page.delete_image(xref)
            stream = unique_png_bytes(payload[xref], group_id, s["slot"])
            new_xref = page.insert_image(new_unrot, stream=stream,
                                         keep_proportion=False,
                                         rotate=s["rotate"])
        except Exception:  # noqa: BLE001
            continue
        new_xref = int(new_xref or 0)
        tag_riding_slice(doc, new_xref, group_id, s["slot"])
        moved[xref] = (new_xref, fitz.Rect(new_unrot))
    if moved:
        doc.mark_dirty()
    return moved


def image_object_bytes_for(doc: PdfDocument, xref: int) -> bytes:
    """Extract an embedded image as PNG (shared helper, avoids import cycle)."""
    owner = doc.doc
    try:
        pix = fitz.Pixmap(owner, int(xref))
        if pix.colorspace is None or pix.colorspace.n > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        key = owner.xref_get_key(int(xref), "SMask")
        if key and key[0] == "xref":
            smask_xref = int(str(key[1]).split()[0])
            smask = fitz.Pixmap(owner, smask_xref)
            if smask.width == pix.width and smask.height == pix.height:
                pix = fitz.Pixmap(pix, smask)
        return pix.tobytes("png")
    except Exception:  # noqa: BLE001
        raw = owner.extract_image(int(xref))
        return bytes(raw["image"])


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
