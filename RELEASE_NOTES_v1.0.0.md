# PDFForge v1.0.0

PDFForge is a native Windows desktop application for processing PDFs locally. Version 1.0.0 is the proposed initial release; it has not been published.

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

The project owner reports that the portable archive was extracted and tested. When made available, download `PDFForge-Windows-x64.zip`, extract it, and run `PDFForge.exe`. Keep the `_internal` folder next to the executable; the executable depends on those runtime files.

### Setup installer

Expected asset: `PDFForge-Setup-v1.0.0.exe`. It has been built locally, but installation, launch, and uninstallation are not yet verified. Do not describe this asset as downloadable until those checks pass.

## Limitations

- Compression is best effort and cannot guarantee a target size or percentage reduction. A PDF may not become smaller.
- Unlock requires a correct password and a supported encryption method.
- Google Sans is not bundled because redistribution permission has not been verified; system font fallbacks are used when unavailable.
- Some long-running operations do not expose cancellation or detailed progress.

## Expected release assets

| Asset | Status |
| --- | --- |
| `PDFForge-Windows-x64.zip` | Existing local archive, reported extracted and tested by the project owner; not uploaded or published. |
| `PDFForge-Setup-v1.0.0.exe` | Built locally; pending install/uninstall testing; not uploaded or published. |

No release date, download URL, signature, or publication status is claimed here.
