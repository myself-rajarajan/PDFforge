# PROGRESS LOG

## Project Overview
- **Project Name**: PDFForge
- **Current Phase**: Phase 5 — PDF Security and Compression
- **Status**: Steps 1–3 implemented; manual review pending

## Phase 1 Checklist
- [x] Inspect the repository and existing environment.
- [x] Set up or verify Git.
- [x] Establish the project structure.
- [x] Configure dependencies and `.gitignore`.
- [x] Create the minimum native desktop application entry point.
- [x] Add basic automated tests.
- [x] Create documentation and progress tracking.
- [x] Run verification.
- [x] Make an initial local commit.

## Work Completed (11 October 2026)
- Initialized project directory structure (`src/`, `tests/`, `docs/`).
- Configured `.gitignore` and `.gitattributes`.
- Added `requirements.txt` with core dependencies (PySide6, PyMuPDF, pypdf, Pillow, pytest).
- Created `main.py` as the application entry point.
- Implemented a minimal `src/app.py` with a PySide6 `QMainWindow`.
- Added basic import and initialization tests in `tests/test_basic.py`.
- Created comprehensive documentation: `README.md`, `PROGRESS.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`.
- Verified Git remote configuration and `.venv` exclusion.

## Dependencies Verified
- PySide6: 6.12.0
- PyMuPDF: 1.28.2
- pypdf: 6.20.0
- Pillow: 12.3.0
- pytest: 9.1.1

## Verification Results
- **Imports**: Success
- **PySide6 Initialization**: Success (Tested via pytest)
- **Git Status**: Clean (pre-commit)

## Next Steps
- Begin Phase 2: Native Desktop GUI.
- Design the dashboard layout and navigation.

## History
- **2026-10-11**: Phase 1 initialized and completed.

## Phase 2 — Native Desktop GUI (11 October 2026)
- **Status**: Implemented; manual visual inspection remains outstanding.
- **GUI**: Added a dark native PySide6 dashboard, shared theme, sidebar, featured panel, quick access and all-tool cards, toolbar, local/offline indicator, recent-files empty state, About page, and Coming Soon pages for all eight planned tools.
- **Behavior**: Sidebar and cards navigate through a stacked page layout; selection follows the current page; toolbar search opens the tool directory and filters by tool name or description; Explore Tools opens All Tools.
- **Files**: Updated `src/app.py`, UI modules under `src/ui/`, `src/utils/constants.py`, `tests/test_basic.py`, README, roadmap, and architecture notes.
- **Dependencies**: No new dependencies.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 6 passed. `git diff --check` checked; `.venv` is ignored.
- **Visual verification**: Not manually launched or inspected in this run. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py` in Windows PowerShell.
- **Known issues**: PDF operations are intentionally placeholders. UI layout has not yet received manual visual review.
- **Git**: Branch `main`; Phase 2 completed in commit `d438d6d`.
- **Next**: Phase 3, Step 1 — Merge PDFs (completed below).

## Typography Update (11 October 2026)
- **Status**: Implemented and covered by automated tests.
- **Font setup**: Centralized `QApplication.setFont()` initialization in `src/ui/theme.py`, called before app widgets are created. Google Sans is preferred if installed or available at `resources/fonts/GoogleSans-Regular.ttf`; fallback order is Segoe UI, Arial, then the system default.
- **Availability and licensing**: No Google Sans font file was found in the project or Windows system/user font directories. No font was copied, downloaded, or bundled because a redistribution license was not verified. Google Sans rendering is not claimed.
- **Packaging**: Font lookup supports the PyInstaller `_MEIPASS` extraction directory. A future bundled font must be included as PyInstaller data under `resources/fonts/`.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 9 passed. Font preference, fallback selection, missing-resource initialization, and existing navigation/search behavior pass. `git diff --check` passed.

## Phase 3, Step 1 — Merge PDFs (11 October 2026)
- **Status**: Implemented and automated tests pass; manual GUI inspection remains outstanding.
- **GUI**: Replaced the Merge PDF placeholder with a native page for adding local PDFs, previewing each file's first page and total page count, viewing/changing merge order, removing selected files, choosing an output path, and starting the merge. Processing runs in a `QThread`; success and failure are reported with dialogs.
- **Merge behavior**: Reused the existing `pypdf` dependency. Inputs are read in order and merged locally. Invalid, missing, unreadable, and encrypted inputs fail with an explanatory error. Temporary output is written beside the destination and atomically installed. Existing destinations require explicit UI confirmation; input paths and aliases are protected from overwrite.
- **Files**: Added `src/core/merge.py`, `src/ui/pages/merge_pdf.py`, and `tests/test_merge.py`; updated app routing, tool metadata, GUI tests, README, and this progress log.
- **Dependencies**: No dependencies added.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 16 passed. `git diff --check` passed.
- **Manual visual verification**: Not performed. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py` in Windows PowerShell and open Merge PDF from the sidebar or dashboard.
- **Known limitations**: Large merges run in the background but have no progress percentage or cancellation control. Other PDF tools remain Coming Soon.
- **Git**: Completed in commit `8a5411a`; no push.
- **Next**: Stop for review before implementing another feature.

## Phase 5, Step 2 — Unlock PDFs (11 October 2026)
- **Status**: Implemented and covered by automated tests; manual GUI verification remains outstanding.
- **GUI**: Added a native Unlock PDF page with local PDF selection, a masked password field, output selection, explicit confirmation before replacing an existing destination, and a background worker. The existing sidebar route is now active and the tool is marked implemented.
- **Behavior**: Uses pypdf's `decrypt()` to verify the supplied password and write the decrypted pages when supported. If the installed pypdf AES handler is unavailable, it verifies the same supplied password through installed PyMuPDF and writes an unencrypted output. Incorrect passwords, unencrypted/missing/corrupt PDFs, unsupported encryption, invalid paths, and source overwrite attempts fail safely. Page order and content are retained as supported by the PDF libraries.
- **Files**: Added `src/core/unlock_pdf.py`, `src/ui/pages/unlock_pdf.py`, and `tests/test_unlock_pdf.py`; updated app routing, tool metadata, GUI tests, README, and this progress log.
- **Dependencies**: No dependencies added; reused pypdf 6.20.0, PyMuPDF, PySide6, and shared output validation.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 99 passed. `git diff --check` passed (Git may report line-ending normalization notices).
- **Manual verification**: Not performed. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py`, open Unlock PDF, select a password-protected document, enter its authorized password, choose a different output filename, and verify the output opens without a password and has the same page count/order/content. Also try a wrong password, an unencrypted PDF, and confirming/rejecting replacement of an existing output.
- **Known limitations**: pypdf AES processing requires its optional cryptography backend; this environment uses PyMuPDF for AES-protected files. Unknown passwords are never guessed or bypassed.
- **Git**: Changes remain uncommitted and have not been pushed, pending review.

## Phase 5, Step 3 — PDF Compression (11 October 2026)
- **Status**: Implemented and covered by automated tests; manual GUI verification remains outstanding.
- **GUI**: Added a native Compress PDF page for selecting the input/output and setting image quality with a slider. Changing the slider measures a temporary compression pass in a background worker and shows the estimated output size below it. Final compression reports both file sizes, actual percent saved (or no reduction/growth), and the output path.
- **Behavior**: Uses PyMuPDF cleanup, garbage collection, stream/font/image deflation, and `rewrite_images` on images above 200 DPI. The 20–95 quality slider controls JPEG quality and target resolution (approximately 113–163 DPI); lower settings trade image detail for potential size reduction. The page explains output size is content-dependent. Missing, invalid, corrupt, password-protected PDFs and input/output collisions are rejected; existing destinations require confirmation.
- **Files**: Added `src/core/compress_pdf.py`, `src/ui/pages/compress_pdf.py`, and `tests/test_compress_pdf.py`; updated app routing, tool metadata, GUI routing tests, README, and this progress log.
- **Dependencies**: No dependencies added; reused PyMuPDF 1.28.2, PySide6, and shared output validation.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 111 passed. `git diff --check` passed (Git may report line-ending normalization notices).
- **Manual verification**: Not performed. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py`, open Compress PDF, choose a PDF with high-resolution images and a new output destination, then compare original and output file sizes and inspect the output visually. Also try a text-only PDF, a password-protected PDF, and an existing output path.
- **Known limitations**: Image optimization uses lossy JPEG recompression for eligible image assets and can reduce image detail. PDFs without eligible images may show little/no reduction or grow slightly due to file structure and compression overhead.
- **Git**: Changes remain uncommitted and have not been pushed, pending review.

## Phase 5, Step 1 — Password-protect PDFs (11 October 2026)
- **Status**: Implemented and covered by automated tests; manual GUI verification remains outstanding.
- **GUI**: Added a native Protect PDF page with PDF selection, masked password and confirmation fields, output selection, existing-output confirmation, and background processing. Protect PDF is now registered in the existing navigation and marked implemented.
- **Behavior**: Uses pypdf AES-256 encryption when its optional crypto backend is available, with the already-installed PyMuPDF AES-256 support as fallback. The service rejects empty passwords, missing/invalid/already-encrypted inputs, invalid destinations, and attempts to alias the source. It writes through a same-directory temporary file and preserves page order/content. Existing outputs are replaced only after explicit confirmation. Passwords are not logged or written to project documentation.
- **Files**: Added `src/core/protect_pdf.py`, `src/ui/pages/protect_pdf.py`, and `tests/test_protect_pdf.py`; updated app routing, tool metadata, GUI routing tests, README, and this progress log.
- **Dependencies**: No dependencies added; reused pypdf 6.20.0, PyMuPDF, and PySide6.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 92 passed. `git diff --check` passed (Git displayed only line-ending normalization notices).
- **Manual verification**: Not performed. Run `.\.venv\Scripts\python.exe main.py`, open Protect PDF, select an unencrypted PDF, enter matching passwords, choose a new output path, then confirm the result opens with the correct password and rejects a wrong password. Also try mismatched/empty values and an already-encrypted input.
- **Known limitations**: pypdf alone requires its optional cryptography backend for AES-256; this environment falls back to the installed PyMuPDF implementation. No password-recovery or decryption workflow is included.
- **Git**: Changes remain uncommitted and have not been pushed, pending review.

## Phase 3, Step 3 — Reorder PDF Pages (11 October 2026)
- **Status**: Implemented and automated tests pass; manual GUI inspection remains outstanding.
- **GUI**: Replaced the Reorder Pages placeholder with a native page that opens a local PDF, renders numbered page thumbnails, supports drop-before/drop-after drag ordering, shows the current original-page sequence, and saves to a user-selected destination. Page processing runs in a background worker.
- **Behavior**: Reuses `pypdf` to preserve page content and rotation while writing pages in the exact displayed order. Invalid permutations, missing/invalid/encrypted PDFs, source overwrite attempts, invalid output paths, and unconfirmed existing destinations are rejected. Original files remain unchanged.
- **Files**: Added `src/core/reorder_pages.py`, `src/ui/pages/reorder_pages.py`, and `tests/test_reorder_pages.py`; updated shared thumbnail drag support, app routing, tool metadata, GUI tests, README, and this progress log.
- **Dependencies**: No dependencies added; reused `pypdf`, Qt PDF rendering, and existing output validation.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 52 passed. `git diff --check` passed (Git reported only expected CRLF normalization notices).
- **Manual visual verification**: Not performed. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py` in Windows PowerShell, then open Reorder Pages from the dashboard or All Tools, open a multi-page PDF, drag thumbnails, and save to a new destination.
- **Known limitations**: Large PDFs have no progress percentage or cancellation control. Password-protected PDFs are rejected; PDFForge does not request or bypass passwords.
- **Git**: Changes remain uncommitted and have not been pushed, pending review.
- **Next**: Stop for review before implementing another feature.

## Phase 3, Step 2 — Remove PDF Pages (11 October 2026)
- **Status**: Implemented and automated tests pass; manual GUI inspection remains outstanding.
- **GUI**: Added a native Remove PDF Pages page with a scrollable, responsive grid of rendered page thumbnails. Clicking a thumbnail toggles it for removal; the one-based number/range field stays synchronized and previews both removed and retained page numbers. The page also shows the filename/page count and output save picker. Loading, thumbnail rendering, and removal use background workers.
- **Behavior**: Removes selected pages locally while preserving remaining page order. Duplicate page numbers/ranges are deduplicated. Malformed syntax, invalid bounds, encrypted/invalid PDFs, missing inputs, removal of every page, and output/input path conflicts are rejected with clear messages. Existing destinations require confirmation.
- **Files**: Added `src/core/remove_pages.py`, `src/core/pdf_output.py`, `src/ui/pages/remove_pages.py`, `src/ui/pdf_preview.py`, and `tests/test_remove_pages.py`; updated app routing, tool metadata, merge thumbnails, GUI tests, README, and this progress log. The shared output validation was extracted while preserving the merge module's prior public aliases.
- **Dependencies**: No dependencies added; reused `pypdf`.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 39 passed, including background PDF thumbnail rendering and click-to-select preview behavior. `git diff --check` passed.
- **Manual visual verification**: Not performed. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py` in Windows PowerShell and open Remove Pages from the sidebar or dashboard.
- **Known limitations**: Large PDFs have no progress percentage or cancellation control. Password-protected PDFs are rejected; PDFForge does not request or bypass passwords.
- **Git**: Changes remain uncommitted and have not been pushed, pending review.
- **Next**: Stop for review before implementing another feature.

## Phase 3, Step 4 — Add Page Numbers (11 October 2026)
- **Status**: Implemented and automated tests pass; manual GUI verification remains outstanding.
- **GUI**: Replaced the Add Page Numbers placeholder with a native page for selecting a local PDF, choosing one of six positions, setting the starting number and font size, selecting an output path, and starting the operation. Input validation and document processing run in background workers.
- **Behavior**: Uses existing PyMuPDF to add sequential numbers while retaining original page content/order. Placement adapts to each page's dimensions and rotation, with safe margins and an error for pages too small for the configured font. Encrypted/invalid/missing PDFs, invalid settings, source overwrite, and unsafe output paths are handled with clear errors. Existing destinations require confirmation.
- **Files**: Added `src/core/add_page_numbers.py`, `src/ui/pages/add_page_numbers.py`, and `tests/test_add_page_numbers.py`; updated app routing, tool metadata, shared preview worker's metadata-only mode, GUI tests, README, and this progress log.
- **Dependencies**: No dependencies added; reused PyMuPDF, PySide6, and shared output validation.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 70 passed. `git diff --check` passed (Git reported only expected CRLF normalization notices).
- **Manual verification**: Not performed. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py` in Windows PowerShell. Open Add Page Numbers, choose a multi-page PDF, verify each of the six positions, try a custom starting number/font size, and save as a new file.
- **Known limitations**: The page number is a standard Helvetica text overlay and is not configurable by font family/color. Very small pages reject font/margin settings that do not fit.
- **Git**: Changes remain uncommitted and have not been pushed, pending review.
- **Next**: Stop for review before implementing another feature.

## Phase 4 — Image Conversion (11 October 2026)
- **Status**: Images to PDF and PDF to Images implemented and covered by automated tests; manual GUI review remains outstanding.
- **Images to PDF**: Select multiple local images and see their thumbnails with filenames/order, move items up or down, remove items, select an output PDF, and convert. Thumbnail decoding runs in background workers. PyMuPDF and Pillow create one uncropped proportional page per image; EXIF orientation is applied and transparency is flattened onto white. Conversion runs in a background worker.
- **PDF to Images**: Select a local PDF and inspect its rendered page thumbnails, then choose PNG/JPEG/TIFF/WebP and 36–600 DPI, choose an output folder, and export predictable `page_001` names in page order. Thumbnail rendering runs in the background; a progress bar tracks page export. Existing output images require explicit confirmation; the export stages files and rolls back partial installs on errors.
- **Safety**: Invalid or missing files, encrypted PDFs, invalid formats/resolutions, source/output aliases, output conflicts, and conversion errors are reported locally. No network services or new dependencies are used.
- **Files**: Added `src/core/images_to_pdf.py`, `src/core/pdf_to_images.py`, `src/ui/pages/images_to_pdf.py`, `src/ui/pages/pdf_to_images.py`, and `tests/test_image_conversion.py`; updated app routing, sidebar, tool metadata, GUI tests, README, and this progress log.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 85 passed, including selected-image and PDF-page thumbnail tests. `git diff --check` passed (Git reported only expected CRLF normalization notices).
- **Manual verification**: Not performed. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py`. Verify both conversion directions using multiple differently sized images/pages, reorder and remove image entries, compare the output page/image order, try PNG/JPEG and TIFF/WebP, change DPI, and confirm an existing output set before replacement.
- **Known limitations**: Animated image formats use their first frame. Images to PDF currently uses a fixed 150 DPI output density. PDF output rendering exports every page; there is no page-range selection or cancellation control.
- **Git**: Changes remain uncommitted and have not been pushed, pending review.
- **Next**: Stop for review before implementing another feature.
