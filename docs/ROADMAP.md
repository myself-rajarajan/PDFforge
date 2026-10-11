# ROADMAP

## Phase 1 — Project Foundation and Git Setup [COMPLETED]
- [x] Inspect the repository and existing environment.
- [x] Set up or verify Git.
- [x] Establish the project structure.
- [x] Configure dependencies and `.gitignore`.
- [ ] Create the minimum native desktop application entry point.
- [ ] Add basic automated tests.
- [ ] Create documentation and progress tracking.
- [ ] Run verification.
- [ ] Make an initial local commit if verification succeeds.

## Phase 2 — Native Desktop GUI [IMPLEMENTED]
- [x] Build the main PDFForge application window using PySide6.
- [x] Create a dark dashboard with featured and quick access sections.
- [x] Add navigation and placeholder pages for all eight planned tools.
- [x] Add local search, recent files empty state, About page, and shared theme.
- [x] Establish reusable UI components.
- [x] Test navigation, search, page construction, and startup.
- [ ] Manually inspect the window and resize behavior.

## Phase 3 — Core PDF Operations
- [ ] Implement merging PDFs.
- [ ] Implement removing pages.
- [ ] Implement reordering pages.
- [ ] Implement adding page numbers.
- [ ] Add tests and user-facing error handling.

## Phase 4 — Image Conversion
- [ ] Implement image-to-PDF conversion.
- [ ] Implement PDF-to-image conversion.
- [ ] Add format validation and tests.

## Phase 5 — PDF Security and Compression
- [ ] Implement password protection.
- [ ] Implement authorized password-based unlocking.
- [ ] Implement best-effort PDF compression.
- [ ] Test common errors and document limitations.

## Phase 6 — Quality and Reliability
- [ ] Expand automated tests.
- [ ] Validate edge cases and malformed files.
- [ ] Improve error messages and user experience.
- [ ] Check that core operations work offline.
- [ ] Review file handling, temporary files, and overwrite behavior.
- [ ] Fix bugs before packaging.

## Phase 7 — Desktop Packaging and Release
- [ ] Configure PyInstaller or an appropriate packaging method.
- [ ] Build and test a Windows desktop executable.
- [ ] Document Linux and macOS packaging considerations.
- [ ] Update installation instructions.
- [ ] Prepare a release checklist.
