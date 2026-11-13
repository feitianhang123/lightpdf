"""Core PDF document wrapper built on PyMuPDF (MuPDF).

This module is deliberately Qt-free so it can be unit-tested and reused.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Tuple

import fitz  # PyMuPDF


@dataclass
class OutlineItem:
    level: int
    title: str
    page: int  # 0-based page index, -1 if unresolved


class PdfError(Exception):
    """Raised for user-facing PDF errors."""


class PdfDocument:
    """Thin, safe wrapper around a MuPDF document."""

    def __init__(self) -> None:
        self.doc: Optional[fitz.Document] = None
        self.path: Optional[str] = None
        self.password: Optional[str] = None
        self._dirty: bool = False

    # ------------------------------------------------------------------ state
    @property
    def is_open(self) -> bool:
        return self.doc is not None

    @property
    def page_count(self) -> int:
        return self.doc.page_count if self.doc else 0

    @property
    def dirty(self) -> bool:
        return self._dirty

    def mark_dirty(self, value: bool = True) -> None:
        self._dirty = value

    # ------------------------------------------------------------------ open
    def open(self, path: str, password: Optional[str] = None) -> None:
        if not os.path.isfile(path):
            raise PdfError(f"File not found: {path}")
        try:
            doc = fitz.open(path)
        except Exception as exc:  # noqa: BLE001
            raise PdfError(f"Cannot open PDF: {exc}") from exc

        if doc.needs_pass:
            if not password or not doc.authenticate(password):
                doc.close()
                raise PdfError("Password required or incorrect.")
        self.doc = doc
        self.path = path
        self.password = password
        self._dirty = False

    def create_blank(self, width: float = 595.0, height: float = 842.0) -> None:
        """Create a new single blank page document (A4 default)."""
        self.close()
        doc = fitz.open()
        doc.new_page(width=width, height=height)
        self.doc = doc
        self.path = None
        self._dirty = True

    def close(self) -> None:
        if self.doc is not None:
            self.doc.close()
        self.doc = None
        self.path = None
        self._dirty = False

    # ------------------------------------------------------------------ save
    def save(self, path: Optional[str] = None, *, incremental: bool = False) -> str:
        """Save the document, including the common "save back to the opened
        file" case.

        MuPDF refuses a full rewrite onto the file a document is opened from
        ("save to original must be incremental").  A plain incremental save is
        not a universal answer either: after undo/redo the document is an
        in-memory copy, which cannot be saved incrementally.  So in-place saves
        serialize to bytes, write a sibling temporary file, close the old
        handle (mandatory on Windows), atomically replace the target and reopen
        it, keeping the session bound to the saved file.
        """
        if self.doc is None:
            raise PdfError("No document open.")
        target = path or self.path
        if not target:
            raise PdfError("No output path given.")
        try:
            if self._is_current_file(target):
                if incremental and self._can_save_incrementally(target):
                    self.doc.save(target, incremental=True,
                                  encryption=fitz.PDF_ENCRYPT_KEEP)
                else:
                    self._rewrite_current_file(target)
            else:
                self.doc.save(target, garbage=3, deflate=True)
        except Exception as exc:  # noqa: BLE001
            raise PdfError(f"Save failed: {exc}") from exc
        self.path = target
        self._dirty = False
        return target

    @staticmethod
    def _norm(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    def _is_current_file(self, target: str) -> bool:
        return bool(self.path) and self._norm(target) == self._norm(self.path)

    def _can_save_incrementally(self, target: str) -> bool:
        """Incremental saves only work while MuPDF still owns the real file."""
        name = getattr(self.doc, "name", "") or ""
        if not name or not os.path.isfile(name):
            return False
        if self._norm(name) != self._norm(target):
            return False
        try:
            return bool(self.doc.can_save_incrementally())
        except Exception:  # noqa: BLE001
            return False

    def _rewrite_current_file(self, target: str) -> None:
        data = self.doc.tobytes(garbage=3, deflate=True,
                                encryption=fitz.PDF_ENCRYPT_KEEP)
        directory = os.path.dirname(os.path.abspath(target))
        tmp: Optional[str] = None
        try:
            fd, tmp = tempfile.mkstemp(prefix=".lightpdf-", suffix=".pdf",
                                       dir=directory)
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
        except OSError:
            tmp = None  # fall back to overwriting the target directly

        old = self.doc
        self.doc = None
        try:
            old.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            if tmp:
                try:
                    os.replace(tmp, target)
                    tmp = None
                except OSError:
                    # e.g. read-only attribute: keep the original file node
                    shutil.copyfile(tmp, target)
            else:
                with open(target, "wb") as fh:
                    fh.write(data)
            reopened = fitz.open(target)
            if reopened.needs_pass and self.password:
                reopened.authenticate(self.password)
            self.doc = reopened
        except Exception:  # noqa: BLE001
            # Never leave the editing session without a usable document.
            if self.doc is None:
                for factory in (lambda: fitz.open("pdf", data),
                                lambda: fitz.open(target)):
                    try:
                        self.doc = factory()
                        break
                    except Exception:  # noqa: BLE001
                        continue
            raise
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    # ------------------------------------------------------------ snapshots
    def tobytes(self) -> bytes:
        """Serialize the current in-memory document (including edits)."""
        if self.doc is None:
            raise PdfError("No document open.")
        return self.doc.tobytes(garbage=0, deflate=True)

    def restore_bytes(self, data: bytes) -> None:
        """Replace the in-memory document with a previously taken snapshot."""
        old_path = self.path
        try:
            newdoc = fitz.open("pdf", data)
        except Exception as exc:  # noqa: BLE001
            raise PdfError(f"Undo failed: {exc}") from exc
        if self.doc is not None:
            self.doc.close()
        self.doc = newdoc
        self.path = old_path
        self._dirty = True

    # -------------------------------------------------------------- page data
    def page(self, index: int) -> fitz.Page:
        if self.doc is None:
            raise PdfError("No document open.")
        if not (0 <= index < self.doc.page_count):
            raise PdfError(f"Page index out of range: {index}")
        return self.doc.load_page(index)

    def page_size(self, index: int) -> Tuple[float, float]:
        r = self.page(index).rect
        return r.width, r.height

    def render(self, index: int, zoom: float = 1.0, rotation: int = 0,
               alpha: bool = False, annots: bool = True) -> fitz.Pixmap:
        page = self.page(index)
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        return page.get_pixmap(matrix=mat, alpha=alpha, annots=annots)

    # ------------------------------------------------------------------ meta
    def metadata(self) -> dict:
        return dict(self.doc.metadata) if self.doc else {}

    def set_metadata(self, values: dict) -> None:
        if self.doc is None:
            raise PdfError("No document open.")
        meta = self.doc.metadata or {}
        meta.update(values)
        self.doc.set_metadata(meta)
        self.mark_dirty()

    # --------------------------------------------------------------- outline
    def get_outline(self) -> List[OutlineItem]:
        if self.doc is None:
            return []
        items: List[OutlineItem] = []
        try:
            toc = self.doc.get_toc(simple=True)
        except Exception:  # noqa: BLE001
            return []
        for level, title, page in toc:
            items.append(OutlineItem(int(level), str(title), int(page) - 1))
        return items

    # ---------------------------------------------------------------- search
    def search(self, needle: str, *, ignore_case: bool = True) -> List[Tuple[int, fitz.Rect]]:
        """Return (page_index, rect) matches with per-page rects merged."""
        results: List[Tuple[int, fitz.Rect]] = []
        if self.doc is None or not needle:
            return results
        for pno in range(self.doc.page_count):
            page = self.doc.load_page(pno)
            hits = page.search_for(needle, quads=False)
            for r in hits:
                results.append((pno, r))
        return results

    def page_text(self, index: int) -> str:
        return self.page(index).get_text("text")
