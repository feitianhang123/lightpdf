"""OCR via Tesseract (pytesseract)."""
from __future__ import annotations

import io
import os
from typing import List, Sequence

import fitz
from PIL import Image

from .document import PdfDocument, PdfError

_EXE = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _pytesseract():
    """Import pytesseract lazily (avoids bundling pandas/numpy when unused)."""
    try:
        import pytesseract
        if os.path.isfile(_EXE):
            pytesseract.pytesseract.tesseract_cmd = _EXE
        return pytesseract
    except Exception:  # noqa: BLE001
        return None


def available_languages() -> List[str]:
    pyt = _pytesseract()
    if pyt is None:
        return []
    try:
        return pyt.get_languages(config="")
    except Exception:  # noqa: BLE001
        return []


def _page_image(doc: PdfDocument, index: int, dpi: int = 300) -> Image.Image:
    pix = doc.render(index, zoom=dpi / 72.0, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def ocr_text(doc: PdfDocument, index: int, lang: str = "eng") -> str:
    pyt = _pytesseract()
    if pyt is None:
        raise PdfError("pytesseract/Tesseract not available.")
    return pyt.image_to_string(_page_image(doc, index), lang=lang)


def make_searchable_pdf(doc: PdfDocument, out_path: str, *, lang: str = "eng",
                        dpi: int = 300, pages: Sequence[int] | None = None) -> str:
    """OCR each page and build a searchable PDF (image + invisible text layer)."""
    pyt = _pytesseract()
    if pyt is None:
        raise PdfError("pytesseract/Tesseract not available.")
    out = fitz.open()
    idxs = list(pages) if pages else range(doc.page_count)
    for i in idxs:
        img = _page_image(doc, i, dpi=dpi)
        pdf_bytes = pyt.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)
        src = fitz.open("pdf", pdf_bytes)
        out.insert_pdf(src)
        src.close()
    out.save(out_path, garbage=3, deflate=True)
    out.close()
    return out_path
