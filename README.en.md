# Light PDF Editor (轻PDF编辑器)

> Language / 语言: [简体中文](README.md) | **English**

A compact, **clean-room** PDF editor, independently written from scratch based on the feature set of mainstream PDF editors. Built on the open-source **PyMuPDF (MuPDF)** + **PySide6 (Qt)** stack. The application UI can be switched between Chinese and English at runtime.

> ⚠️ This is an unofficial, independent project intended for learning and exchange only. It is a reduced-scope PDF editor with no affiliation to, or partnership with, any commercial PDF software vendor. If you believe it infringes your rights, please contact the author for removal (QQ: 10780329).

## Download & Install

Get the installers from [**Releases**](https://github.com/feitianhang123/lightpdf/releases/latest):

| OS | File |
|---|---|
| Windows (64-bit) | `setup.exe` (v1.0.12) |
| Kylin V10 SP1 / Linux (ARM64, Phytium / Kunpeng) | `lightpdf_1.0.12_arm64.deb` (v1.0.12) |

> Both the Windows installer and the Kylin `.deb` are now **v1.0.12**: they fix "saving changes back to the original file fails", add **Page → Replace Pages...**, and support **any combination of target and source page counts** (many → one, one → many, many → many).
> The Kylin package was built with `packaging/linux/build-kylin.sh` on an aarch64 machine and is published in the
> [v1.0.12 Release](https://github.com/feitianhang123/lightpdf/releases/tag/v1.0.12). The `lightpdf_1.0.9_arm64.deb` in the
> [v1.0.9 Release](https://github.com/feitianhang123/lightpdf/releases/tag/v1.0.9) is kept as a historical build.

**Windows**: double-click `setup.exe` and follow the wizard (default location `C:\Program Files\轻PDF编辑器`). A "轻PDF编辑器" entry appears in the Start menu.

**Kylin / Debian-family (aarch64)**:
```bash
sudo dpkg -i lightpdf_1.0.12_arm64.deb
sudo apt-get -f install     # only if dependencies are missing
```
Then launch it from the Start menu, or run `lightpdf file.pdf` in a terminal. Uninstall with `sudo apt-get remove lightpdf`.

## Features

- **View & navigate**: continuous scroll / facing pages, zoom (slider / mouse wheel / fit width & height / actual size), thumbnails, bookmarks & outline, text search, printing
- **Annotate & mark up**: highlight, underline, strikethrough, sticky notes (with editable content), text boxes, rectangles, ellipses, lines, arrows, custom **stamps** (text / image, configurable shape and color), and **riding stamps** (a single seal split into N slices and placed along the edges of N pages, so stacking the sheets reconstructs the full seal)
- **Page management**: insert (at a chosen position), **delete (current page, or many pages at once with `1-3,5,8-10`)**, **replace pages (target and source page counts can differ freely)**, move, rotate (current / all / specified pages), extract, split (by page count or custom ranges), merge (drag to reorder), watermark, header & footer, page numbers / Bates numbering
- **Content editing**: edit existing text (wording, font, size), insert / edit auto-sizing text boxes, **insert images / stamps (drag to move, 8 resize handles, precise size & position fields, still selectable and adjustable after saving)**
- **Document compare**: pixel-level visual diff plus line-level text diff
- **Convert**: PDF to images, images to PDF (reorder multiple images, choose A4 / A3 / A5 / Letter and "fit / original size")
- **Print**: a full multi-column print dialog — preview (zoom / page size / paper / page slider), print range (current view / current page / all pages / custom page numbers / odd-even subsets / reverse order), page handling (scaling "None · Fit · Shrink · Custom %", tile large pages, multiple pages per sheet, booklet), duplex (long / short edge flip), auto-rotate / center, orientation, print content, output, grayscale / print as image / bleed marks, copies / collate, print to file, advanced / print hints
- **Other**: multiple tabs, **single instance (opening another PDF adds a tab to the running window)**, undo / redo, light-green theme, Chinese / English UI switch

## Run from Source

```bash
python -m pip install -r requirements.txt
python -m app.main            # or: python -m app.main document.pdf
```

## Packaging

### Windows (single-file exe + Inno Setup installer)

```powershell
python -m PyInstaller --noconfirm --windowed --onefile --name "轻PDF编辑器" ^
  --icon icon.ico --version-file version_info.txt --paths . ^
  --add-data "icon.ico;." --add-data "resources;resources" run_app.py
ISCC.exe installer.iss                    # produces 安装包\setup.exe
```

### Kylin / Linux (aarch64, `.deb`)

> PyInstaller cannot cross-compile, so this must run on the target machine with the same architecture.

```bash
git clone https://github.com/feitianhang123/lightpdf.git && cd lightpdf
bash packaging/linux/build-kylin.sh       # one command: install system deps if needed, then build
# output: dist/lightpdf_1.0.12_arm64.deb
```

For an offline transfer, **source only (~0.6 MB)** is needed: `app/`, `run_app.py`, `requirements.txt`, `icon.ico`,
`resources/`, `packaging/linux/`. **Do not** copy `.venv-build/`, `build/`, `dist/` or other caches.
See [`packaging/linux/README.md`](packaging/linux/README.md) (in Chinese) for the full file list.

You can also run the steps separately: `packaging/linux/install_deps.sh` (system deps) → `packaging/linux/build_deb.sh` (build).
The version number is read automatically from `app/version.py`; there is no need to edit the scripts.
See [`packaging/linux/README.md`](packaging/linux/README.md) (in Chinese).

## Changelog

Detailed release notes are written in Chinese; links below point to those documents.

### 1.0.12

- **Page → Replace Pages... now accepts any combination of page counts**: you may select one or many pages in the current document, and one or many pages in the source PDF. They no longer have to be equal.
  - **Many → one**: original pages `3-5` ← source page `2`: total pages −2, everything after the original page 5 follows the new page.
  - **One → many**: original page `3` ← source pages `1-3`: total pages +2, the new pages become pages 3/4/5.
  - **Many → many**: e.g. original pages `3-5` (3 pages) ← source pages `1-5` (5 pages): total pages +2; source pages may be out of order or repeated.
  - Rule: when both sides have the **same** count, pages still pair up one-to-one (identical to v1.0.11). When the counts **differ**, all target pages are removed and the chosen source pages are inserted as one ordered block at the first target's position; later pages follow. Total pages = original − targets + sources.
  - The dialog shows a live summary such as "pages 3-5 (3 pages) ← source pages 1, 2, 3, 4, 5 (5 pages); total pages 12 → 14". A missing / encrypted source file or an out-of-range page number still disables Replace and explains why.
  - Screenshots: [`16_替换页面_3页换5页.png`](docs/preview/16_替换页面_3页换5页.png),
    [`17_替换页面_3页换1页.png`](docs/preview/17_替换页面_3页换1页.png).
    59 new regression assertions plus the 44 save-fix assertions from v1.0.10 all pass;
    see [`docs/release-notes-v1.0.12.md`](docs/release-notes-v1.0.12.md) (Chinese).
  - No visual changes were made to the rest of the UI.

### 1.0.11

- **New: Page → Replace Pages...** — replace pages in the current document with pages from another PDF.
  - Replace the **current page**, or specify **multiple non-contiguous pages** with `1-3,5,8-10`. Source page numbers support ranges too, default to `1-N`, are no longer overwritten after you edit them manually, and the same source page may be reused for several targets.
  - The dialog validates live and disables Replace when counts differ, a page number is out of range, or the source file is encrypted / missing.
  - The **total page count stays the same**; untouched pages, their rotation and annotations are preserved. Replaced pages and their annotations are removed, and Undo / Redo can restore them.
  - Screenshot: [`15_替换页面.png`](docs/preview/15_替换页面.png); 48 regression assertions pass;
    see [`docs/release-notes-v1.0.11.md`](docs/release-notes-v1.0.11.md) (Chinese).
  - No visual changes were made to the rest of the UI.

### 1.0.10

- **Fixed: saving after editing showed `Save failed: save to original must be incremental`.**
  - Root cause: PyMuPDF (MuPDF) does not allow a full rewrite of the currently open file back onto its own path — exactly what "open PDF → edit → Ctrl+S" did. After undo / redo the document becomes an in-memory copy, so even incremental saving is unavailable.
  - Saving to the original file now serializes to memory → writes a temporary file in the same folder → releases the old file handle → atomically replaces the file → reopens it. `garbage=3` object cleanup and deflate compression are retained, so repeated saves do not bloat the file. The editing session stays bound to the saved file, and already-written images / stamps can still be selected and adjusted.
  - Also covers "save as, then keep saving", encrypted PDFs, Chinese / spaced paths, page deletion, and protecting the original file when a save fails. 44 regression assertions pass.
    See [`docs/release-notes-v1.0.10.md`](docs/release-notes-v1.0.10.md) (Chinese).

### 1.0.9

- **New: resize images after inserting them**.
  - A newly inserted image is selected automatically, with a blue dashed frame, **8 white handles** and a live size label. Drag the body to move, drag a corner to scale proportionally, drag an edge to stretch in one direction, or hold `Shift` for free scaling.
  - **Edit / Annotate → Adjust Image / Stamp...** or **double-click** the object to open a numeric dialog with exact X / Y / width / height, a "lock aspect ratio" switch and a "delete this object" button.
  - `Delete` removes the selected object; arrow keys nudge by 1 pt (`Shift` + arrow = 10 pt). Resizing, moving and deleting are all undoable / redoable.
  - Screenshots: [`12_图片缩放控制点.png`](docs/preview/12_图片缩放控制点.png),
    [`13_调整大小与位置.png`](docs/preview/13_调整大小与位置.png).
- **New: reposition stamps after inserting them**.
  - A single stamp is no longer burned into the PDF the moment you click. It uses the same **editable floating-object** system as images: after placement the tool switches to Select, so you can drag it, resize it, set exact coordinates or delete it. It is written into the PDF only when saving / printing / exporting.
  - Images and stamps **already baked into a PDF** (older files, or files reopened after saving) can be selected and adjusted again. Selecting does not modify the document; the actual drag / numeric edit lifts that image out of the page content stream and re-inserts it. Other placements of a reused image are preserved, and the alpha channel of transparent stamps is restored in full.
  - Display ↔ PDF coordinate conversion for rotated pages (`/Rotate 90/180/270`) was corrected; handles follow the page when zooming.
  - Screenshot: [`14_图章位置调整.png`](docs/preview/14_图章位置调整.png).
- Riding stamps are still generated once as a set of per-page slices (each slice is an image object and can be re-selected for fine tuning).
- Both the Windows `setup.exe` and the Kylin aarch64 `lightpdf_1.0.9_arm64.deb` were rebuilt and published in the
  [v1.0.9 Release](https://github.com/feitianhang123/lightpdf/releases/tag/v1.0.9);
  see [`docs/release-notes-v1.0.9.md`](docs/release-notes-v1.0.9.md) (Chinese).

### 1.0.8

- **Changed: drop-down menus and input fields now share exactly the same border and height**.
  - Removed the `2px` bold green frame and bold text from drop-downs; they now use the same `1px` thin border, rounded corners and padding as input fields, including the expanded item list.
  - All single-line inputs (`QLineEdit` / `QComboBox` / `QSpinBox` / `QDoubleSpinBox`) are **33 px** tall. Spin boxes compensate for the 3 px added by their up/down buttons and draw clear triangles so they are not squashed into lines.
  - Drop-downs remain easy to spot: pale green background, a separate arrow button area on the right and a dark green down triangle. "Split by" is no longer enlarged and matches every other drop-down.
  - Updated screenshots: [`07_拆分方式下拉菜单.png`](docs/preview/07_拆分方式下拉菜单.png),
    [`08_输入框与下拉菜单对比.png`](docs/preview/08_输入框与下拉菜单对比.png).
- v1.0.5 / v1.0.6 / v1.0.7 were not released separately; their changes accumulated into this version. Installers for both platforms (including `lightpdf_1.0.8_arm64.deb` for Kylin aarch64) were published in the
  [v1.0.8 Release](https://github.com/feitianhang123/lightpdf/releases/tag/v1.0.8).

### 1.0.7

- **Fixed: choosing a PNG image stamp had no effect**.
  - Root cause: when the "Type" drop-down was still set to "Text stamp", clicking "Choose image..." only filled in the path without switching the type, so preview and insertion kept using the text stamp. Also, a failing image did not clear the previous preview, which looked like "nothing happened".
  - Fix: picking an image **switches the type to "Image stamp" automatically** (pasting a valid path does the same), image controls stay available in both modes, the image is copied into the app's settings folder so moving / deleting the original is safe, and a load failure shows the reason and disables OK.
  - Also fixed: font / shape settings not showing saved values on reopen, and reading Chinese paths / more image formats.
- **New: Annotate → Insert Riding Stamp** (for multi-page documents).
  - A complete seal is **split vertically into N slices** placed along the edges of N pages. "Alternate left/right" supports duplex printing (odd pages on the right, even pages on the left): stack the sheets and the full seal reappears. All-right / all-left placement is also available.
  - Configurable page range (all / current page to end / `1-3,5,8-10`), pages per seal (repeat in groups for long documents), total seal width, distance from the edge, vertical position, slice overlap compensation and reversed slice order.
  - The dialog shows a live **reassembled seal preview + per-page placement diagram**. One insertion can be undone as a whole from Edit → Undo. Rotated landscape pages are handled correctly too.
  - Screenshots: [`09_骑缝章设置.png`](docs/preview/09_骑缝章设置.png),
    [`10_骑缝章落位效果.png`](docs/preview/10_骑缝章落位效果.png),
    [`11_图片图章设置.png`](docs/preview/11_图片图章设置.png).
- The Kylin / Linux package has to be rebuilt on a Kylin (aarch64) machine; this version was not published separately. Changes from v1.0.5 ~ v1.0.7 shipped together in the [v1.0.8 Release](https://github.com/feitianhang123/lightpdf/releases/tag/v1.0.8) as `lightpdf_1.0.8_arm64.deb`.

### 1.0.6

- **UI**: all **20 drop-down menus** were restyled so they are instantly distinguishable from input fields.
  - Inputs stay **white with a thin border**; drop-downs use a **pale green background + 2 px green frame + bold text + a separate green arrow area** on the right, with a clear down triangle inside. Hover / expanded / disabled states each have distinct feedback.
  - The expanded **item list** also uses the green frame with a white background, a highlighted selection and taller rows.
  - "Split by" in **Page → Split Document** was emphasized (taller, larger font, wider arrow area) with a tooltip saying "click the arrow on the right to open the list".
  - Comparison screenshots: [`08_输入框与下拉菜单对比.png`](docs/preview/08_输入框与下拉菜单对比.png),
    [`07_拆分方式下拉菜单.png`](docs/preview/07_拆分方式下拉菜单.png).
- Note: the multi-page deletion from v1.0.5 is included in this installer too. The Kylin / Linux package also needs rebuilding on a Kylin (aarch64) machine, producing `lightpdf_1.0.6_arm64.deb`.

### 1.0.5

- **Page management**: "Page → Delete Current Page" became "**Delete Pages...**", able to delete the current page **or any set of pages** in one action.
  - Choose "Current page" (one click, same as before) or "Selected pages"; page numbers support `1-3,5,8-10`, single pages, arbitrary order and Chinese commas. Duplicates are removed, entries are sorted and out-of-range numbers are ignored.
  - The dialog shows a live summary ("Will delete N pages: 1-3, 5") and refuses to delete every page (a PDF must keep at least one).
  - Deletion is undoable from Edit → Undo, and the view automatically lands on a valid page.
- The Kylin / Linux package needs rebuilding on a Kylin (aarch64) machine as described above, producing `lightpdf_1.0.5_arm64.deb`; the already published `lightpdf_1.0.4_arm64.deb` does not include these changes.

### 1.0.4

- **Printing**: fixed **red seals / electronic signatures not appearing in printed output**.
  - Root cause: a red seal in a PDF is the appearance stream of a **Signature Widget annotation**, and the print pipeline rendered with `annots=False`, dropping that layer entirely — so neither the preview nor the printout showed it.
  - Fix: printing now **includes annotations** by default, and a new **"Print stamps and electronic signatures"** checkbox toggles it (unchecking prints only the page content, with no seal in preview or output).
  - Also fixed an old bug where "multiple pages per sheet / booklet" ignored the switch (previously hard-coded to include annotations). **Preview == output == switch state** in every mode now.
- "Print content" now defaults to **"Document and markings"** (so signed documents show the red seal as soon as they are opened); the drop-down and the seal checkbox stay in sync in both directions.

### 1.0.3

- **Printing**: three real-world issues fixed
  - "Multiple pages per sheet" preview orientation did not match the output — the preview sheet no longer deforms with the content, so **preview == output**;
  - The preview was not a full page when the dialog opened — the base image is decoupled from zoom and recomputed after layout;
  - Some network MFPs (e.g. Canon iR C3020) produced nothing — added a fallback retry and clear troubleshooting hints.
- **Packaging**: added the one-command Kylin script `packaging/linux/build-kylin.sh`; the version number is now read automatically from `app/version.py`.

### 1.0.2

- **Printing**: the print dialog was rebuilt as a **three-column layout**, adding zoom, multiple pages per sheet, tile large pages, booklet, duplex, orientation, print content, output, grayscale, print as image, bleed marks, copies and print to file.

## Requirements

- Python 3.8+ (3.10 recommended on Windows)
- Runtime: PySide6, PyMuPDF, Pillow, numpy (see `requirements.txt`; opencv / pytesseract / pdf2docx are optional)
- Packaging: PyInstaller; Inno Setup 7 is also required on Windows

## License

[MIT](LICENSE)
