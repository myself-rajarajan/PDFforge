# PDFForge

PDFForge is a professional, offline-first native desktop PDF utility inspired by the convenience and organization of iLovePDF. It provides a suite of tools for processing PDF files locally on your computer, ensuring privacy and security.

## Phase 2 — Native Desktop GUI

The current build provides a native PySide6 dashboard, local tool search, and navigation. Phase 3 adds PDF merging, page removal, page reordering, and page numbering. Phase 4 adds local image-to-PDF and PDF-to-image conversion. Phase 5 adds local PDF password protection and authorized unlocking.

### Typography

The application configures its font centrally through `QApplication.setFont()`. It prefers an available Google Sans, then Inter or Roboto, followed by Segoe UI, Arial, and the system default. Google Sans, Inter, and Roboto font files were not found in the project or Windows font folders during the UI polish pass; Windows Segoe UI files are present. No font is bundled because a redistribution license was not verified. The optional Google Sans resource lookup supports source and PyInstaller builds under `resources/fonts/` (a future packaged font must include its license and be added as build data).

## Implemented PDF Operations
- **Merge PDFs**: Combine multiple local PDF files in a user-selected order. Each file shows a first-page thumbnail and page count. The tool validates inputs, protects source files from being overwritten, and asks before replacing an existing destination.
- **Remove PDF Pages**: Browse rendered page thumbnails and click pages to select them, or enter one-based page numbers/ranges. The tool previews which pages will be removed and retained, preserves remaining-page order, ignores duplicates, protects the original, and rejects removing every page.
- **Reorder PDF Pages**: Browse rendered, numbered page thumbnails and drag them into a new order. Drop on the upper or lower half of a thumbnail to insert before or after it. The displayed order is saved to a new local PDF; source files are protected and existing destinations require confirmation.
- **Add Page Numbers**: Add sequential numbers to every page in one of six top/bottom and left/center/right positions. Configure the starting number and font size; the tool preserves the source, validates page fit, and requires confirmation before replacing an existing destination.
- **Images to PDF**: See thumbnail previews of selected JPG/JPEG, PNG, BMP, GIF, TIFF, or WebP files, then reorder or remove them before converting into one PDF. Pages preserve image proportions and EXIF orientation; transparency is flattened onto white.
- **PDF to Images**: Preview the selected PDF's pages as thumbnails, then export them in order as PNG, JPEG, TIFF, or WebP at a selected DPI. Filenames are predictable (`page_001.png` etc.); progress is shown and replacing collisions requires confirmation.
- **Compress PDF**: Apply best-effort cleanup, deflation, and image optimization for images over 200 DPI. A quality slider (20–95%) controls JPEG quality and target resolution; lower quality can reduce image detail to seek smaller output. Changing the slider measures an estimated result with a temporary compression pass. Not every PDF will become smaller; the original and final sizes plus actual savings/no-change/growth are shown.
- **Protect PDF**: Encrypt a local PDF with AES-256 after the user enters and confirms a non-empty password. It uses pypdf's AES-256 writer when its optional crypto backend is available and the already-installed PyMuPDF AES-256 writer otherwise. The input remains unchanged, already-encrypted documents are rejected, and the output runs in a background worker. Existing destinations require confirmation.
- **Unlock PDF**: Remove encryption from a local PDF after verifying a password supplied by the user. It uses pypdf password verification and writing where supported, and the already-installed PyMuPDF backend for AES PDFs when pypdf's optional crypto backend is unavailable. The source is preserved and existing output destinations require confirmation.

## Reliability Status

The automated regression suite currently passes **123 tests**. It includes cross-feature failure-injection checks confirming that temporary PDF outputs are removed when the final destination install fails, and that a failed PDF-to-image encoding preserves existing output files and removes its staging directory. GUI routing, repainting, and page initialization are covered by offscreen Qt tests; manual visual verification remains outstanding. See [PROGRESS.md](PROGRESS.md) for the baseline and detailed verification record.

## UI/UX Polish

The native PySide6 interface uses a layered charcoal palette, low-contrast borders, rounded cards and fields, and keyboard focus outlines. It avoids QWidget graphics effects to keep native repainting reliable. Tool directories reflow between one and several columns as the window changes size; the sidebar adjusts its width and scrolls when vertical space is limited; PDF page previews scale within a bounded range. The active sidebar marker slides to the selected tool. The interface remains local and offline; no web view or dependency was added. Automated resizing and navigation checks pass, but a manual visual review is still needed.

### Manual UI review

Run `.\.venv\Scripts\python.exe main.py` from the project folder. Navigate to all nine PDF tools using both the dashboard/All Tools cards and sidebar; check the active marker and page rendering. Resize repeatedly through 860×580, 1100×720, and 1500×900; check that tool cards reflow, the sidebar scrolls, paths wrap or remain accessible, and page previews resize. For each tool, test native input/output pickers, an ordinary success, a validation/error state, and an existing-output confirmation. Also check image thumbnails, PDF page previews, page drag/drop in Reorder Pages, page selection in Remove Pages, and progress feedback in PDF-to-Images and Compress PDF.

## Features (Planned)

## Technology Stack
- **Python 3.12**
- **PySide6**: Native desktop GUI framework.
- **PyMuPDF & pypdf**: Core PDF processing engines.
- **Pillow**: Image processing library.
- **pytest**: Automated testing framework.

## Getting Started

### Prerequisites
- Python 3.12 or later.

### Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/myself-rajarajan/PDFforge.git
   cd PDFforge
   ```

2. **Activate the virtual environment**:
   - Windows: `.venv\Scripts\activate`
   - Linux/macOS: `source .venv/bin/activate`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
```bash
python main.py
```

### Running Tests
```powershell
python -m pytest -q
```

## Architecture
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details on the project structure and design decisions.

## Roadmap
See [docs/ROADMAP.md](docs/ROADMAP.md) for the detailed development plan and current progress.

---

### Progress Summary
- **Phase 1 (Foundation)**: Complete.
- **Phase 2 (Native Desktop GUI)**: Implemented; automated tests are documented in [PROGRESS.md](PROGRESS.md). Manual visual review is still required.
- **Phase 3, Step 1 (Merge PDFs)**: Implemented and covered by automated tests; manual GUI review is still required.
- **Phase 3, Step 2 (Remove PDF Pages)**: Implemented and covered by automated tests; manual GUI review is still required.
- **Phase 3, Step 3 (Reorder PDF Pages)**: Implemented and covered by automated tests; manual GUI review is still required.
- **Phase 3, Step 4 (Add Page Numbers)**: Implemented and covered by automated tests; manual GUI review is still required.
- **Phase 4 (Image Conversion)**: Images to PDF and PDF to Images are implemented and covered by automated tests; manual GUI review is still required.
- **Phase 5, Step 1 (Protect PDFs)**: Implemented and covered by automated tests; manual GUI review is still required.
- **Phase 5, Step 2 (Unlock PDFs)**: Implemented and covered by automated tests; manual GUI review is still required.
- **Phase 5, Step 3 (PDF Compression)**: Implemented and covered by automated tests; manual GUI review is still required.
- **Phase 6 (Regression Testing and Reliability)**: Regression and repaint checks pass in the current 123-test suite, including temporary-output cleanup and failed-export safety; manual GUI review is still required.
- **UI/UX Polish**: Shared dark styling, responsive grids/sidebar/previews, keyboard focus states, and native sidebar marker motion are implemented without QWidget graphics effects; manual visual review is still required.
