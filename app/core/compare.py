"""Document comparison: page-aligned visual pixel diff + text line diff."""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import fitz
import numpy as np
from PIL import Image


@dataclass
class Region:
    x: int
    y: int
    w: int
    h: int


@dataclass
class PageDiff:
    page: int
    changed_ratio: float
    regions: List[Region] = field(default_factory=list)
    overlay_png: Optional[bytes] = None  # RGB diff overlay as PNG bytes
    text_changes: List[Tuple[str, str]] = field(default_factory=list)  # (kind, text)


@dataclass
class CompareResult:
    pages: List[PageDiff] = field(default_factory=list)
    a_pages: int = 0
    b_pages: int = 0
    note: str = ""

    @property
    def changed_pages(self) -> List[int]:
        return [p.page for p in self.pages if p.changed_ratio > 0.0005]


def _load_image(path: str) -> List[np.ndarray]:
    doc = fitz.open(path)
    imgs = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        imgs.append(arr.copy())
    doc.close()
    return imgs


def _pad_to(a: np.ndarray, shape: Tuple[int, int]) -> np.ndarray:
    h, w = shape
    out = np.full((h, w, 3), 255, dtype=np.uint8)
    out[:a.shape[0], :a.shape[1]] = a[:h, :w]
    return out


def _regions_from_mask(mask: np.ndarray, min_area: int = 30) -> List[Region]:
    try:
        import cv2
    except Exception:  # noqa: BLE001
        ys, xs = np.where(mask)
        if len(xs) == 0:
            return []
        return [Region(int(xs.min()), int(ys.min()),
                       int(xs.max() - xs.min()), int(ys.max() - ys.min()))]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h >= min_area:
            regions.append(Region(x, y, w, h))
    return regions


def compare_pdfs(path_a: str, path_b: str, *, render_scale: int = 2) -> CompareResult:
    imgs_a = _load_image(path_a)
    imgs_b = _load_image(path_b)
    result = CompareResult(a_pages=len(imgs_a), b_pages=len(imgs_b))
    if len(imgs_a) != len(imgs_b):
        result.note = f"Page counts differ ({len(imgs_a)} vs {len(imgs_b)}); compared the first {min(len(imgs_a), len(imgs_b))}."

    doc_a = fitz.open(path_a)
    doc_b = fitz.open(path_b)
    n = min(len(imgs_a), len(imgs_b))
    for i in range(n):
        a, b = imgs_a[i], imgs_b[i]
        h = max(a.shape[0], b.shape[0])
        w = max(a.shape[1], b.shape[1])
        a2, b2 = _pad_to(a, (h, w)), _pad_to(b, (h, w))
        diff = np.abs(a2.astype(np.int16) - b2.astype(np.int16)).sum(axis=2)
        mask = (diff > 40).astype(np.uint8) * 255
        changed = float((mask > 0).mean())
        regions = _regions_from_mask(mask)

        overlay = a2.copy()
        overlay[mask > 0] = [255, 0, 0]
        overlay_img = Image.fromarray(overlay)
        import io
        buf = io.BytesIO()
        overlay_img.save(buf, format="PNG")

        pd = PageDiff(page=i, changed_ratio=changed, regions=regions,
                      overlay_png=buf.getvalue())
        pd.text_changes = _text_diff(doc_a.load_page(i).get_text("text"),
                                     doc_b.load_page(i).get_text("text"))
        result.pages.append(pd)

    doc_a.close()
    doc_b.close()
    return result


def _text_diff(text_a: str, text_b: str) -> List[Tuple[str, str]]:
    la = [l for l in text_a.splitlines() if l.strip()]
    lb = [l for l in text_b.splitlines() if l.strip()]
    sm = difflib.SequenceMatcher(a=la, b=lb)
    changes: List[Tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for line in la[i1:i2]:
            changes.append(("-", line.strip()))
        for line in lb[j1:j2]:
            changes.append(("+", line.strip()))
    return changes
