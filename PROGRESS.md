# PROGRESS LOG

## Project Overview
- **Project Name**: PDFForge
- **Current Phase**: v1.0.0 release preparation
- **Status**: PDF tools implemented; source regression suite passes; packaging and publication remain pending
- **Proposed release**: v1.0.0 (not published; no release tag created)

## Current Verification Snapshot (12 October 2026)
- **Automated source tests**: `.venv\Scripts\python.exe -m pytest -q` — 126 passed in 13.21 seconds. In this managed environment, `TEMP` and `TMP` were set to a workspace-local temporary directory so Windows file-install operations could complete.
- **Packaged app manual checks**: The project owner reports launching the packaged app and checking all nine listed PDF operation tools, including each compression preset. This is owner-reported verification, not a new manual run during release preparation.
- **Portable archive**: The owner reports extracting the ZIP into a separate folder and testing it. During this preparation, the archive was inspected without extraction: it contains `PDFForge.exe` and `_internal/` at its root, has 228 entries, and is 74,530,331 bytes. The packaged folder also contains the executable alongside `_internal/`.
- **Installer**: `installer/PDFForge.iss` compiled successfully with Inno Setup 7.1.0 into the x64 setup executable. The project owner reports that manual testing succeeded.
- **Publication**: Pending. No commit, push, tag, GitHub release, or upload was made.

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

## Phase 6 — Full Regression Testing and Reliability (11 October 2026)
- **Status**: Regression review and automated verification completed; no verified PDF-processing or navigation bugs were found.
- **Baseline**: `.venv\Scripts\python.exe -m pytest -q` — 111 passed before this phase's test additions.
- **Review**: Inspected the source tree, README, progress log, all nine PDF core modules, their native GUI pages, shared PDF output validation, thumbnail preview support, and existing core/navigation tests. Existing tests exercise output reopening/content or page order, common invalid/missing/encrypted inputs, source overwrite protection, output collisions, and navigation for the implemented tools.
- **Coverage added**: Added nine fault-injection regressions in `tests/test_operation_cleanup.py`. Eight verify cleanup of temporary PDF files and no partial destination after final installation fails across merge, page removal, reordering, numbering, images-to-PDF, protection, unlocking, and compression. One verifies failed PDF-to-image encoding preserves an existing output and removes its staging directory.
- **Changes**: No production behavior required a fix; updated README and this log with the verified status and remaining manual checks.
- **Verification**: `.venv\Scripts\python.exe -m pytest -q` — 120 passed. `git diff --check` passed. Worktree status is reported with this phase's completion; no commit or push was made.
- **Manual verification still needed**: Launch the desktop app and visit each implemented tool from Home/All Tools and sidebar. Confirm native file dialogs, confirmations, progress/responsiveness, and result/error dialogs. Run representative documents through all nine operations and inspect outputs in a PDF viewer/image viewer. Automated offscreen Qt tests cover page construction and route mapping but do not replace visual Windows GUI review.
- **Known limitations**: Manual GUI testing was not performed. Large-document operations have the progress/cancellation limitations described in their feature sections; this reliability pass did not add progress reporting or redesign threading.

## UI/UX Polish Pass (11 October 2026)
- **Status**: Implemented; automated layout and navigation checks pass. Manual visual review remains outstanding.
- **Visual system**: Reworked the shared PySide6 theme with layered charcoal surfaces, restrained accent blue, consistent rounded panels and controls, low-contrast borders, readable text hierarchy, keyboard focus outlines, and selected/hover/disabled states. The styles remain QSS/native widgets; no web view or dependencies were added.
- **Navigation motion**: The active sidebar selection marker slides to the selected tool. Page fades and card drop shadows were removed after the Windows startup log showed repeated inactive-painter warnings; ordinary native widget rendering is retained.
- **Responsive behavior**: The minimum window size is now 860×580. Sidebar width adapts to the window and its navigation list scrolls independently. Page margins tighten when compact, dashboard and All Tools cards reflow between columns, and PDF preview tiles scale within bounded limits. Existing Qt layouts and thumbnail wrapping remain in use.
- **Typography and licensing**: Google Sans remains preferred if locally available, then Inter and Roboto, then Segoe UI/Arial/system fallback. Google Sans, Inter, and Roboto font files were not found in the project or Windows font folders; Segoe UI font files are present. No font was bundled because redistribution licensing was not verified. No automatic font download was introduced.
- **Warning fix**: Changed PyMuPDF imports to the supported `import pymupdf` module in runtime modules and tests. Removed page opacity effects and card drop-shadow effects after the Windows startup log reported repeated inactive-painter warnings. Native styling, hover states, and the sidebar marker remain.
- **Tests**: Added responsive layout and navigation repaint checks; the new repaint check captures Qt messages and confirms page/card graphics effects are absent. Full `.venv\Scripts\python.exe -m pytest -q` — 123 passed.
- **Manual checks**: The app process was started, but screenshot/window control was unavailable: the session's native UI bridge returned an empty app inventory and did not expose its documented `listApps` method. Therefore, visual appearance, resize recovery, native file dialogs, sidebar marker animation, long-path rendering, PDF preview, drag/drop, and operation-state dialogs still need review on Windows. Run `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py` and follow the manual checklist in README.
- **Files**: Updated `src/ui/theme.py`, `src/ui/sidebar.py`, `src/ui/tool_card.py`, `src/ui/pdf_preview.py`, `src/ui/pages/dashboard.py`, `src/ui/pages/all_tools.py`, `src/ui/pages/remove_pages.py`, `src/app.py`, `src/core/add_page_numbers.py`, `src/core/images_to_pdf.py`, `src/core/pdf_to_images.py`, their tests, `tests/test_basic.py`, README, and this log. PDF processing algorithms and business logic were not changed.

## Home Page and Compression Improvements (12 October 2026)
- **Dashboard**: Added a PDFForge introduction with the requested headline, plain-language local-processing explanation, a concise overview of implemented capabilities, a four-step workflow, and the existing Explore Tools action. Per the follow-up request, removed the Quick Access and All Tools sections from Home; the dedicated All Tools page and sidebar navigation remain available.
- **Compression findings**: PDFForge already used PyMuPDF `Document.rewrite_images` for raster images over 200 DPI, with slider-controlled JPEG quality/target DPI, plus garbage collection, cleanup, and deflation. It did not validate rewritten page/text properties or guard against output growth.
- **Compression**: Added Recommended (75 quality / 150 DPI), Strong (50 / 133 DPI), and Maximum (25 / 116 DPI) presets while retaining fine slider control. Only already-lossy images are recompressed; lossless images and bitonal assets are excluded to avoid damaging graphics and transparency. Stream deflation, image/font deflation, cleanup, and garbage collection remain enabled. PDF metadata is retained rather than discarded.
- **Validation and safety**: The temporary result is reopened and checked for non-empty output, encryption status, page count, page dimensions, rotation, and searchable text. If optimization grows the PDF, the original bytes are copied into the staged output. The destination is installed only after validation and the source/output conflict checks remain in force.
- **Size reporting**: Compression reports original and resulting sizes, the selected preset, percentage change, and actual bytes saved when smaller. Estimates continue to be produced by a temporary compression pass; final reporting reads the output size from disk.
- **Windows output compatibility**: Baseline testing found output-install failures because the managed Windows test environment denies hard-link creation in its default temporary directory. Added a shared installer that uses same-volume `os.rename` on Windows (which refuses to replace an existing file) and retains create-if-absent hard links on POSIX. Reused it across PDF outputs and staged image exports, preserving explicit replacement behavior.
- **Tests**: Added coverage for preset values and settings, image rewrite parameters, larger-result fallback, and dashboard content. Existing cross-feature install-failure injection now covers the shared installer. Full `.venv\Scripts\python.exe -m pytest -q` — 126 passed (with `TEMP`/`TMP` directed to a workspace-local test folder because this sandbox blocks rename/link operations under its system temp directory).
- **Limitations**: Compression does not guarantee a particular percentage or target size. Lossless images are intentionally not converted to JPEG; PDFs dominated by lossless scans, text, vectors, already-compressed content, or fonts may show little reduction. Removing document metadata is not attempted.
- **Manual verification**: Not performed. Launch with `Set-Location 'C:\Users\rajar\OneDrive\Desktop\PDFforge'; .\.venv\Scripts\python.exe main.py`. Check the home introduction at narrow and wide window sizes. In Compress PDF, try all three presets and a custom slider value with an image-heavy PDF and a text/vector PDF; compare actual output sizes and inspect text, page order, and image quality.

## v1.0.0 Release Preparation (12 October 2026)
- **Release state**: v1.0.0 is proposed only. No tag, commit, push, publication, or upload was made.
- **Documentation**: Reorganized README around the native application, supported operations, source setup, local processing, limitations, actual project structure, and release state. Added `RELEASE_NOTES_v1.0.0.md`; it does not claim an invented date, download URL, signature, or publication.
- **Source verification**: Re-ran `.venv\Scripts\python.exe -m pytest -q` against the current worktree — 126 passed in 13.21 seconds. `TEMP` and `TMP` pointed to a workspace-local temporary directory due file-operation restrictions in the managed environment's system temp location.
- **Owner-reported manual status**: The project owner reports that the packaged application was launched and all nine listed PDF operation tools were checked, including all compression presets. The owner also reports extracting the portable archive in a separate folder and testing it. These checks were not repeated during this documentation task.
- **Artifact inspection**: Confirmed `%USERPROFILE%\PDFForge_Release\PDFForge` contains `PDFForge.exe` and `_internal/`. Inspected `%USERPROFILE%\PDFForge-Windows-x64.zip` without extracting it: root contains `PDFForge.exe` and `_internal/`, with 228 entries and a size of 74,530,331 bytes. No existing build or ZIP was modified.
- **Installer preparation**: Added `installer/PDFForge.iss` for a per-user install under LocalAppData, with `_internal` copied recursively, Start Menu and optional desktop shortcuts, uninstaller support, and a post-install launch option. Source folder is configured by `PDFFORGE_DIST_DIR`; output is written beside the one-folder build. Inno Setup was unavailable, so the script was not compiled and the installer was not installed/uninstalled or tested. This asset is pending and is not downloadable.
- **Pending release tasks**: Install Inno Setup, compile the script against the existing one-folder build, inspect the installer file, install and launch it, verify a PDF operation and optional desktop shortcut, uninstall and confirm removal, then review final source changes and assets before separately authorizing any commit, push, tag, or GitHub publication.
- **Verification**: `git diff --check` passed before this release-preparation edit; rerun after the documentation changes. `.venv`, the packaged build, and the portable ZIP were preserved.

## Installer Build Follow-up (12 October 2026)
- **Compiler discovery**: Inno Setup 7.1.0 was installed per-user at `%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe`. The initial lookup failed because this managed execution shell maps `LOCALAPPDATA` to a sandbox location; the compiler was then located under the user's actual profile path.
- **Build**: Compiled `installer/PDFForge.iss` against the existing `%USERPROFILE%\PDFForge_Release\PDFForge` one-folder app. The first compile warned that the old `x64` architecture identifier is deprecated, so the script was updated to `SetupArchitecture=x64` and rebuilt. Final Inno Setup 7.1.0 compile succeeded without that warning and produced `%USERPROFILE%\PDFForge_Release\PDFForge-Setup-v1.0.0.exe` (53,418,283 bytes).
- **Safety**: The portable ZIP and PyInstaller folder were not modified. The setup output was written as a separate file beside the existing release folder.
- **At the time of this build entry**: Manual verification had not yet been reported. The owner later confirmed successful manual installer testing; see the release status below.

## Installer Manual Verification and Release (12 October 2026)
- **Manual verification**: The project owner confirmed the installer was manually tested successfully. This is owner-reported verification; the exact steps were not independently observed in this session.
- **Release assets**: `PDFForge-Windows-x64.zip` (74,530,331 bytes) and `PDFForge-Setup-v1.0.0.exe` (53,418,283 bytes) are published. The installer uses Inno Setup 7.1.0 and includes the application executable and `_internal` runtime.
- **Publication**: Published as GitHub Release [v1.0.0](https://github.com/myself-rajarajan/PDFforge/releases/tag/v1.0.0). Verified the release is public and includes both assets at their expected sizes.
