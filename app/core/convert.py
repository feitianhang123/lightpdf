"""Format conversion helpers."""
from __future__ import annotations

import os
from typing import List, Sequence

import fitz
from PIL import Image

from .document import PdfDocument, PdfError


def pdf_to_images(doc: PdfDocument, out_dir: str, *, fmt: str = "png",
                  dpi: int = 150, pages: Sequence[int] | None = None) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(doc.path or "page"))[0]
    zoom = dpi / 72.0
    idxs = list(pages) if pages else range(doc.page_count)
    outputs: List[str] = []
    fmt = fmt.lower()
    for i in idxs:
        pix = doc.render(i, zoom=zoom, alpha=False)
        path = os.path.join(out_dir, f"{base}_{i + 1:04d}.{fmt}")
        if fmt in ("jpg", "jpeg"):
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img.save(path, quality=90)
        elif fmt == "tiff":
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img.save(path, compression="tiff_deflate")
        else:
            pix.save(path)
        outputs.append(path)
    return outputs


def images_to_pdf(paths: Sequence[str], out_path: str, *, page_size=None,
                  fit: str = "fit") -> str:
    """Create a PDF from images.

    page_size: None -> page matches each image; else (width_pt, height_pt).
    fit:       "fit" scales the image to the page; "original" keeps 1:1 points.
    """
    doc = fitz.open()
    for p in paths:
        img = Image.open(p)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        w, h = float(img.size[0]), float(img.size[1])
        if page_size is None:
            page = doc.new_page(width=w, height=h)
            rect = page.rect
        else:
            pw, ph = float(page_size[0]), float(page_size[1])
            page = doc.new_page(width=pw, height=ph)
            if fit == "fit":
                m = 18.0
                scale = min((pw - 2 * m) / w, (ph - 2 * m) / h)
                dw, dh = w * scale, h * scale
            else:
                dw, dh = w, h
            x, y = (pw - dw) / 2, (ph - dh) / 2
            rect = fitz.Rect(x, y, x + dw, y + dh)
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        page.insert_image(rect, stream=buf.getvalue(), keep_proportion=True)
    doc.save(out_path, garbage=3, deflate=True)
    doc.close()
    return out_path


def pdf_to_text(doc: PdfDocument, out_path: str) -> str:
    parts = []
    for i in range(doc.page_count):
        parts.append(f"----- Page {i + 1} -----")
        parts.append(doc.page_text(i))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return out_path


def pdf_to_html(doc: PdfDocument, out_path: str) -> str:
    parts = ["<html><head><meta charset='utf-8'></head><body>"]
    for i in range(doc.page_count):
        parts.append(f"<h3>Page {i + 1}</h3>")
        html = doc.page(i).get_text("html")
        parts.append(html)
    parts.append("</body></html>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return out_path


def pdf_to_docx(doc: PdfDocument, out_path: str) -> str:
    try:
        from pdf2docx import Converter  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise PdfError(
            "PDF->Word needs the optional 'pdf2docx' package (pip install pdf2docx)."
        ) from exc
    if not doc.path:
        raise PdfError("Save the document before converting to Word.")
    cv = Converter(doc.path)
    try:
        cv.convert(out_path)
    finally:
        cv.close()
    return out_path


def pdf_to_pdfa(doc: PdfDocument, out_path: str) -> str:
    """Best-effort PDF/A via Ghostscript if available."""
    import shutil
    import subprocess
    gs = shutil.which("gswin64c") or shutil.which("gswin32c") or shutil.which("gs")
    if not gs:
        raise PdfError("PDF/A requires Ghostscript on PATH.")
    if not doc.path:
        raise PdfError("Save the document first.")
    subprocess.run([gs, "-dPDFA", "-dBATCH", "-dNOPAUSE", "-sDEVICE=pdfwrite",
                    f"-sOutputFile={out_path}", doc.path], check=True)
    return out_path
