# PDFForge v1.0.0

PDFForge v1.0.0 is the initial release of a native Windows desktop application for processing PDFs locally.

## Features

- Merge PDF files in a chosen order.
- Preview and remove selected PDF pages.
- Reorder PDF pages by dragging page previews.
- Add page numbers in six positions with a configurable starting number and font size.
- Convert common image formats to a multi-page PDF, with image previews and ordering controls.
- Export PDF pages as PNG, JPEG, TIFF, or WebP images at a selected resolution.
- Compress PDFs with best-effort presets or a quality slider.
- Protect a PDF with a password using AES-256 where supported by the available PDF backend.
- Unlock a PDF only after the user supplies a valid authorized password.

## Privacy

PDFForge is a native desktop application. PDF and image processing happens locally; selected documents are not uploaded to a conversion service. Unlocking does not guess, crack, or bypass passwords.

## Windows use

### Portable archive

The project owner reports that the portable archive was extracted and tested. Download the [PDFForge-Windows-x64.zip portable archive](https://github.com/myself-rajarajan/PDFforge/releases/download/v1.0.0/PDFForge-Windows-x64.zip), extract it, and run `PDFForge.exe`. Keep the `_internal` folder next to the executable; the executable depends on those runtime files.

### Setup installer

Download the [PDFForge-Setup-v1.0.0.exe installer](https://github.com/myself-rajarajan/PDFforge/releases/download/v1.0.0/PDFForge-Setup-v1.0.0.exe) to install PDFForge per-user. The project owner reports that the installer was manually tested successfully.

## Limitations

- Compression is best effort and cannot guarantee a target size or percentage reduction. A PDF may not become smaller.
- Unlock requires a correct password and a supported encryption method.
- Google Sans is not bundled because redistribution permission has not been verified; system font fallbacks are used when unavailable.
- Some long-running operations do not expose cancellation or detailed progress.

## Published release assets

| Asset | Status |
| --- | --- |
| [PDFForge-Windows-x64.zip](https://github.com/myself-rajarajan/PDFforge/releases/download/v1.0.0/PDFForge-Windows-x64.zip) | Portable Windows x64 application archive. |
| [PDFForge-Setup-v1.0.0.exe](https://github.com/myself-rajarajan/PDFforge/releases/download/v1.0.0/PDFForge-Setup-v1.0.0.exe) | Per-user Windows x64 installer, reported manually tested by the project owner. |

No release date or code-signing status is claimed here.
