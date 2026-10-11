# PDFForge

PDFForge is a professional, offline-first native desktop PDF utility inspired by the convenience and organization of iLovePDF. It provides a suite of tools for processing PDF files locally on your computer, ensuring privacy and security.

## Phase 2 — Native Desktop GUI

The current build provides a native PySide6 dashboard, local tool search, navigation, and clear placeholders for planned operations. PDF processing features are not implemented yet; no files are processed by this phase.

## Features (Planned)
- **Merge PDFs**: Combine multiple PDF files into one.
- **Compress PDF**: Reduce PDF file size while preserving quality.
- **Image Conversion**: Convert images to PDF and PDF pages to images.
- **Unlock PDF**: Open password-protected PDFs (credentials required).
- **Protect PDF**: Secure PDFs with passwords and encryption.
- **Remove/Reorder Pages**: Manipulate page structure within a PDF.
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
