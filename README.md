# PDFForge

PDFForge is a native Windows desktop application for common PDF tasks. It is built with Python and PySide6 and processes documents locally on the computer where it runs. PDFForge is not a web application.

Version **1.0.0 is proposed and not published**. The application and portable archive described below exist locally; release downloads will only be available after publication on GitHub.

## Features

- **Merge PDFs** — Select multiple PDF files, inspect first-page previews and page counts, arrange their order, and combine them into a new PDF.
- **Remove PDF pages** — Preview and select pages or enter one-based page numbers and ranges. The remaining pages keep their original order.
- **Reorder PDF pages** — Drag numbered page thumbnails into the desired order and save a new PDF.
- **Add page numbers** — Add sequential page numbers at any of six top/bottom and left/center/right positions, with configurable starting number and font size.
- **Images to PDF** — Preview, reorder, and remove selected images before converting them into one PDF. The Pillow-supported image formats include JPEG, PNG, BMP, GIF, TIFF, and WebP. Image proportions and EXIF orientation are retained; transparency is flattened onto white.
- **PDF to images** — Preview a PDF and export its pages as PNG, JPEG, TIFF, or WebP, in page order, at a selected resolution.
- **Compress PDF** — Apply best-effort cleanup, deflation, and selective recompression of already-lossy raster images. Presets and a quality slider trade image quality for size reduction. The app reports actual sizes and avoids keeping a larger rewritten result when it can preserve the original bytes instead.
- **Protect PDF** — Encrypt a new PDF with AES-256 when the installed backend supports it. Existing encrypted inputs are rejected instead of silently re-encrypted.
- **Unlock PDF** — Decrypt a PDF only with the password supplied by the user. This is not password recovery or password bypass.

All tools use native file dialogs and keep source files safe from accidental replacement. Existing output files require confirmation before replacement. Processing is local; source PDFs and images are not uploaded to a service.

## Screenshots

Screenshots are not currently included in this repository.

## Technology

- Python 3.12+
- PySide6 for the native desktop interface
- PyMuPDF and pypdf for PDF operations
- Pillow for image handling
- pytest for automated tests

The interface prefers Google Sans when an authorized local font resource is available, with system-font fallbacks. No Google Sans file is bundled because its redistribution license has not been verified.

## Project structure

```text
PDFforge/
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── installer/
│   └── PDFForge.iss
├── src/
│   ├── app.py
│   ├── core/                 # PDF operations and output validation
│   ├── ui/
│   │   ├── pages/            # Dashboard and native tool pages
│   │   ├── pdf_preview.py
│   │   ├── sidebar.py
│   │   └── theme.py
│   └── utils/constants.py
├── tests/                    # Core, reliability, and offscreen GUI tests
├── main.py                   # Desktop application entry point
├── requirements.txt
├── README.md
├── PROGRESS.md
└── RELEASE_NOTES_v1.0.0.md
```

PyInstaller's one-folder release contains `PDFForge.exe` and the adjacent `_internal/` runtime directory. Build output folders and `.venv` are excluded from Git.

## Requirements

- Windows 10 or later is recommended for the current native Windows release.
- Python 3.12 or later to run from source.

## Install and run from source

In PowerShell, from the project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

If the project already has a `.venv`, activate and reuse it instead of recreating it. To start the app in the existing environment:

```powershell
Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'
.\.venv\Scripts\python.exe main.py
```

## Run automated tests

```powershell
python -m pytest -q
```

The latest source-tree run recorded for this preparation passed **126 tests**. See [PROGRESS.md](PROGRESS.md) for the verification conditions and the distinction between automated checks and user-reported manual checks.

## Windows release

The proposed GitHub release version is **v1.0.0**. It has not been published, so there is no release download URL yet. The local tested portable archive is `%USERPROFILE%\PDFForge-Windows-x64.zip` (about 74.5 MB). The packaged app is `%USERPROFILE%\PDFForge_Release\PDFForge\PDFForge.exe` with runtime files in the adjacent `_internal` directory. A setup installer has now been built locally at `%USERPROFILE%\PDFForge_Release\PDFForge-Setup-v1.0.0.exe`; it still needs install, launch, and uninstall testing before distribution.

Project source: [github.com/myself-rajarajan/PDFforge](https://github.com/myself-rajarajan/PDFforge). Check the [GitHub Releases page](https://github.com/myself-rajarajan/PDFforge/releases) for downloads after the release is published.

When the portable ZIP is made available, download and extract it, then run `PDFForge.exe`. Keep `_internal` beside the executable; moving or copying the executable alone will not work. The archive was extracted and manually tested according to the project owner's supplied status. The installer is built locally but is not yet verified by installation/uninstallation and is not ready to list as a download.

## Privacy and local processing

PDF and image operations run on the local computer using the installed PDF and image libraries. PDFForge does not require a web account or send selected documents to an online conversion service. Protect and Unlock operate on local files; Unlock requires a password the user is authorized to use.

## Limitations

- Compression is best effort. The resulting file size depends on document contents; no specific reduction or target size is guaranteed. Lossless image assets are not converted to JPEG, and text/vector content is retained.
- Unlocking requires a valid supplied password and a supported encryption method. PDFForge does not crack or bypass passwords.
- Some operations may not provide progress or cancellation for very large files; see the feature notes in [PROGRESS.md](PROGRESS.md).
- Google Sans is not bundled. Actual rendering depends on local availability; the app falls back to system fonts.
- The conventional installer compiles, but its installation, application launch, desktop shortcut, and uninstallation have not yet been manually verified.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Progress and verification log](PROGRESS.md)
- [Proposed v1.0.0 release notes](RELEASE_NOTES_v1.0.0.md)

## Progress summary and development log

- **Phases 1–5:** Implemented; the nine listed PDF operation tools are covered by automated tests.
- **Phase 6:** Reliability regression coverage added. The latest source suite passed 126 tests; manual review details are in [PROGRESS.md](PROGRESS.md).
- **Proposed release:** v1.0.0 documentation is prepared. The portable ZIP is reported manually tested by the project owner. The installer is built locally, but install testing and GitHub publication remain pending.

See [PROGRESS.md](PROGRESS.md) for the chronological development log.
