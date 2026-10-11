# ARCHITECTURE

## Overview
PDFForge is a native desktop application built with Python and PySide6. It follows a modular architecture to separate the graphical user interface (GUI) from the core PDF processing logic.

## Responsibilities

### `main.py`
The entry point of the application. It handles high-level startup logic and initializes the PySide6 event loop.

### `src/app.py`
Initializes the main application instance and the primary window.

### `src/ui/`
Contains native PySide6 UI components and the centralized `Theme` stylesheet.
- `sidebar.py`: Navigation buttons and selected-page state.
- `tool_card.py`: Reusable clickable tool card.
- `pages/dashboard.py`: Home feature panel and quick access cards.
- `pages/all_tools.py`: Tool directory and immediate name/description filter.
- `src/app.py`: Main window, toolbar, stacked pages, and navigation wiring.

`PDFForgeApp` owns a `QStackedWidget` and routes sidebar and card selections by stable page keys. Planned operations open explicit Coming Soon pages; the Recent Files page remains empty until real processing exists. The toolbar search filters the All Tools page without network access.

### `src/core/`
Contains the business logic for PDF and image processing.
- This module remains offline and works strictly with local files.
- Uses `PyMuPDF`, `pypdf`, and `Pillow`.

### `src/utils/`
Shared utility functions, such as file path helpers, logging, and error handling.

### `tests/`
Automated test suite using `pytest`. Tests are designed to verify core logic without requiring a GUI when possible.

## Offline-First Design
All processing is performed locally on the user's machine. No data is transmitted to external servers.
