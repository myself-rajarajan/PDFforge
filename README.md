# PDFForge

PDFForge is a professional, offline-first native desktop PDF utility inspired by the convenience and organization of iLovePDF. It provides a suite of tools for processing PDF files locally on your computer, ensuring privacy and security.

## Phase 2 — Native Desktop GUI

The current build provides a native PySide6 dashboard, local tool search, navigation, and clear placeholders for tools that are still planned. Phase 3, Step 1 adds PDF merging and Step 2 adds page removal; the other PDF processing features remain planned.

### Typography

The application configures its font centrally through `QApplication.setFont()`. It prefers Google Sans when that font is installed or a licensed `resources/fonts/GoogleSans-Regular.ttf` is supplied; otherwise it falls back to Segoe UI, Arial, or the system default. Google Sans was not found in the local project or Windows font directories during this update, so no font file is bundled and Google Sans rendering is not confirmed. The source and PyInstaller resource lookup both resolve the optional font from `resources/fonts/` (PyInstaller builds must include that directory as data).

## Implemented PDF Operations
- **Merge PDFs**: Combine multiple local PDF files in a user-selected order. Each file shows a first-page thumbnail and page count. The tool validates inputs, protects source files from being overwritten, and asks before replacing an existing destination.
- **Remove PDF Pages**: Browse rendered page thumbnails and click pages to select them, or enter one-based page numbers/ranges. The tool previews which pages will be removed and retained, preserves remaining-page order, ignores duplicates, protects the original, and rejects removing every page.

## Features (Planned)
- **Compress PDF**: Reduce PDF file size while preserving quality.
- **Image Conversion**: Convert images to PDF and PDF pages to images.
- **Unlock PDF**: Open password-protected PDFs (credentials required).
- **Protect PDF**: Secure PDFs with passwords and encryption.
- **Reorder Pages**: Rearrange the pages in a PDF.
- **Add Page Numbers**: Customize and add page numbers to documents.

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
