"""Page-management operations: rotate, delete, reorder, extract, split, merge,
watermark, header/footer and Bates numbering."""
from __future__ import annotations

import os
from typing import Iterable, List, Sequence

import fitz

from .document import PdfDocument, PdfError


# ---------------------------------------------------------------- rotation
def rotate_page(doc: PdfDocument, index: int, degrees: int) -> None:
    page = doc.page(index)
    page.set_rotation((page.rotation + degrees) % 360)
    doc.mark_dirty()


def rotate_all(doc: PdfDocument, degrees: int) -> None:
    for i in range(doc.page_count):
        page = doc.page(i)
        page.set_rotation((page.rotation + degrees) % 360)
    doc.mark_dirty()


def rotate_pages(doc: PdfDocument, indices: Iterable[int], degrees: int) -> None:
    for i in indices:
        if 0 <= i < doc.page_count:
            page = doc.page(i)
            page.set_rotation((page.rotation + degrees) % 360)
    doc.mark_dirty()


# ------------------------------------------------------------ delete/reorder
def delete_pages(doc: PdfDocument, indices: Iterable[int]) -> None:
    idxs = sorted(set(int(i) for i in indices), reverse=True)
    if len(idxs) >= doc.page_count:
        raise PdfError("Cannot delete every page.")
    for i in idxs:
        doc.doc.delete_page(i)
    doc.mark_dirty()


def move_page(doc: PdfDocument, src: int, dst: int) -> None:
    if src == dst:
        return
    doc.doc.move_page(src, dst)
    doc.mark_dirty()


def reorder(doc: PdfDocument, new_order: Sequence[int]) -> None:
    if sorted(new_order) != list(range(doc.page_count)):
        raise PdfError("Order must be a permutation of all pages.")
    doc.doc.select(list(new_order))
    doc.mark_dirty()


def reverse(doc: PdfDocument) -> None:
    doc.doc.select(list(reversed(range(doc.page_count))))
    doc.mark_dirty()


# --------------------------------------------------------------- extract/split
def extract_pages(doc: PdfDocument, indices: Sequence[int], out_path: str) -> str:
    out = fitz.open()
    for i in indices:
        out.insert_pdf(doc.doc, from_page=i, to_page=i)
    out.save(out_path, garbage=3, deflate=True)
    out.close()
    return out_path


def split(doc: PdfDocument, out_dir: str, *, every_n: int = 1,
          ranges: Sequence[tuple] | None = None) -> List[str]:
    """Split into files. Either every N pages or explicit (from,to) 0-based pairs."""
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(doc.path or "document"))[0]
    groups: List[Sequence[int]] = []
    if ranges:
        for a, b in ranges:
            groups.append(list(range(a, b + 1)))
    else:
        n = doc.page_count
        for start in range(0, n, max(1, every_n)):
            groups.append(list(range(start, min(start + every_n, n))))
    outputs: List[str] = []
    for k, group in enumerate(groups, start=1):
        out = fitz.open()
        for i in group:
            out.insert_pdf(doc.doc, from_page=i, to_page=i)
        path = os.path.join(out_dir, f"{base}_part{k:03d}.pdf")
        out.save(path, garbage=3, deflate=True)
        out.close()
        outputs.append(path)
    return outputs


def merge(paths: Sequence[str], out_path: str) -> str:
    out = fitz.open()
    try:
        for p in paths:
            src = fitz.open(p)
            out.insert_pdf(src)
            src.close()
    except Exception as exc:  # noqa: BLE001
        out.close()
        raise PdfError(f"Merge failed: {exc}") from exc
    out.save(out_path, garbage=3, deflate=True)
    out.close()
    return out_path


def insert_pages_from(doc: PdfDocument, src_path: str, at_index: int,
                      pages: Sequence[int] | None = None) -> None:
    src = fitz.open(src_path)
    try:
        if pages:
            for i in pages:
                doc.doc.insert_pdf(src, from_page=i, to_page=i, start_at=at_index)
                at_index += 1
        else:
            doc.doc.insert_pdf(src, start_at=at_index)
    finally:
        src.close()
    doc.mark_dirty()


def replace_pages(doc: PdfDocument, target_indices: Sequence[int], src_path: str,
                  src_indices: Sequence[int]) -> None:
    """Replace pages of *doc* with pages copied from another PDF.

    ``target_indices`` and ``src_indices`` are 0-based and positionally paired:
    the k-th target page receives the k-th source page.  Each copy is inserted
    immediately behind its target and the original is then deleted; processing
    back-to-front keeps the remaining indices valid.  Page count and the order
    of untouched pages are unchanged, and annotations / rotation survive.
    A source page may be reused for several targets.
    """
    targets = [int(i) for i in target_indices]
    sources = [int(i) for i in src_indices]
    if not targets or not sources:
        raise PdfError("No pages selected.")
    if len(targets) != len(sources):
        raise PdfError("Source and target page counts must match.")
    if len(set(targets)) != len(targets):
        raise PdfError("Target pages must be unique.")
    if not os.path.isfile(src_path):
        raise PdfError(f"Source PDF not found: {src_path}")
    n = doc.page_count
    if any(i < 0 or i >= n for i in targets):
        raise PdfError("Target page out of range.")
    try:
        src = fitz.open(src_path)
    except Exception as exc:  # noqa: BLE001
        raise PdfError(f"Cannot open source PDF: {exc}") from exc
    try:
        if src.needs_pass:
            raise PdfError("Source PDF is password protected.")
        if any(i < 0 or i >= src.page_count for i in sources):
            raise PdfError("Source page out of range.")
        pairs = sorted(zip(targets, sources), key=lambda p: p[0])
        for t, s in reversed(pairs):
            doc.doc.insert_pdf(src, from_page=s, to_page=s,
                               start_at=t + 1, annots=True)
            doc.doc.delete_page(t)
    except PdfError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PdfError(f"Replace pages failed: {exc}") from exc
    finally:
        src.close()
    doc.mark_dirty()


# ------------------------------------------------------------------ watermark
def add_watermark(doc: PdfDocument, text: str, *, fontsize: float = 48,
                  color: tuple = (0.6, 0.6, 0.6), opacity: float = 0.3,
                  angle: float = 45, fontname: str = "helv") -> None:
    if not text:
        raise PdfError("Watermark text is empty.")
    for i in range(doc.page_count):
        page = doc.page(i)
        r = page.rect
        pivot = fitz.Point(r.width / 2, r.height / 2)
        morph = (pivot, fitz.Matrix(angle))
        # centre-ish placement
        tw = fitz.get_text_length(text, fontname=fontname, fontsize=fontsize)
        point = fitz.Point(r.width / 2 - tw / 2, r.height / 2)
        page.insert_text(point, text, fontsize=fontsize, color=color,
                         fontname=fontname, fill_opacity=opacity,
                         morph=morph, render_mode=0)
    doc.mark_dirty()


# -------------------------------------------------------------- header/footer
def _apply_text(page: fitz.Page, text: str, position: str, fontsize: float,
                color: tuple, margin: float, fontname: str, align: int) -> None:
    r = page.rect
    if position == "top":
        y = margin
    else:
        y = r.height - margin
    rect = fitz.Rect(margin, y - fontsize, r.width - margin, y + fontsize)
    page.insert_textbox(rect, text, fontsize=fontsize, color=color,
                        fontname=fontname, align=align)


def add_header_footer(doc: PdfDocument, header: str = "", footer: str = "",
                      *, fontsize: float = 10, color: tuple = (0, 0, 0),
                      margin: float = 24, fontname: str = "helv",
                      align: int = 1) -> None:
    for i in range(doc.page_count):
        page = doc.page(i)
        if header:
            _apply_text(page, header, "top", fontsize, color, margin, fontname, align)
        if footer:
            _apply_text(page, footer, "bottom", fontsize, color, margin, fontname, align)
    doc.mark_dirty()


# ----------------------------------------------------------------- Bates/pages
def add_page_numbers(doc: PdfDocument, *, template: str = "{n}",
                     start: int = 1, prefix: str = "", fontsize: float = 10,
                     color: tuple = (0, 0, 0), margin: float = 24,
                     position: str = "bottom", fontname: str = "helv") -> None:
    for i in range(doc.page_count):
        page = doc.page(i)
        label = prefix + template.format(n=start + i, total=doc.page_count)
        _apply_text(page, label, position, fontsize, color, margin, fontname, 1)
    doc.mark_dirty()
