"""Native GUI page for choosing and removing PDF pages with visual previews."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path
from src.core.remove_pages import (
    format_page_numbers, parse_page_selection, remove_pdf_pages,
)
from src.ui.pdf_preview import PdfPreviewWorker, ThumbnailGrid
from src.ui.theme import Theme


class RemovePagesWorker(QThread):
    """Write the page-filtered PDF in the background."""

    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, source: str, output: str, selection: str, overwrite: bool) -> None:
        super().__init__()
        self.source = source
        self.output = output
        self.selection = selection
        self.overwrite = overwrite

    def run(self) -> None:
        try:
            output, _, _ = remove_pdf_pages(
                self.source, self.output, self.selection, overwrite=self.overwrite
            )
            self.succeeded.emit(str(output))
        except PDFOperationError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Could not save the modified PDF: {exc}")


class RemovePagesPage(QWidget):
    """PDF selection, visual page preview, and safe output controls."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        heading = QLabel("Remove PDF Pages")
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        description = QLabel(
            "Click page previews or enter one-based page numbers and ranges, such as 2,4,7-9. "
            "Duplicate selections are ignored. At least one page must remain."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(description)

        input_row = QHBoxLayout()
        self.open_button = QPushButton("Open PDF…")
        self.open_button.clicked.connect(self.choose_input)
        self.file_info = QLabel("No PDF selected")
        self.file_info.setWordWrap(True)
        self.file_info.setAccessibleName("Selected PDF filename and page count")
        input_row.addWidget(self.open_button)
        input_row.addWidget(self.file_info, 1)
        layout.addLayout(input_row)

        workspace = QHBoxLayout()
        workspace.setSpacing(20)
        self.thumbnail_grid = ThumbnailGrid()
        self.thumbnail_grid.page_toggled.connect(self._page_toggled)
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setMinimumWidth(400)
        self.preview_scroll.setMinimumHeight(330)
        self.preview_scroll.setWidget(self.thumbnail_grid)
        workspace.addWidget(self.preview_scroll, 1)

        controls = QVBoxLayout()
        controls.setSpacing(12)
        controls.setContentsMargins(0, 0, 0, 0)
        selection_label = QLabel("Pages to remove")
        controls.addWidget(selection_label)
        self.selection_input = QLineEdit()
        self.selection_input.setPlaceholderText("For example: 2,4,7-9")
        self.selection_input.setAccessibleName("One-based PDF page numbers to remove")
        self.selection_input.textChanged.connect(self.update_preview)
        self.selection_input.setEnabled(False)
        controls.addWidget(self.selection_input)

        self.preview_removed = QLabel("Pages to remove: —")
        self.preview_remaining = QLabel("Pages that will remain: —")
        self.preview_error = QLabel("Open a PDF to see its page previews.")
        for label in (self.preview_removed, self.preview_remaining, self.preview_error):
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            controls.addWidget(label)

        controls.addSpacing(12)
        controls.addWidget(QLabel("Save modified PDF to"))
        self.output_input = QLineEdit()
        self.output_input.setReadOnly(True)
        self.output_input.setPlaceholderText("Choose a new filename and location…")
        self.output_input.setAccessibleName("Modified PDF output path")
        controls.addWidget(self.output_input)
        self.output_button = QPushButton("Choose Output…")
        self.output_button.clicked.connect(self.choose_output)
        self.output_button.setEnabled(False)
        controls.addWidget(self.output_button)

        self.remove_button = QPushButton("Save PDF Without Selected Pages")
        self.remove_button.setMinimumHeight(48)
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self.start_removal)
        controls.addWidget(self.remove_button)
        controls.addStretch()
        workspace.addLayout(controls, 1)
        layout.addLayout(workspace, 1)

        self.input_path: str | None = None
        self.page_count = 0
        self._preview_worker: PdfPreviewWorker | None = None
        self._remove_worker: RemovePagesWorker | None = None
        self._page_buttons = {}

    def choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF documents (*.pdf)"
        )
        if not path:
            return
        self.input_path = None
        self.page_count = 0
        self._page_buttons.clear()
        self.thumbnail_grid.clear_pages()
        self.selection_input.clear()
        self.selection_input.setEnabled(False)
        self.output_input.clear()
        self.output_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.preview_removed.setText("Pages to remove: —")
        self.preview_remaining.setText("Pages that will remain: —")
        self.preview_error.setText("Loading PDF and page previews…")
        self.preview_error.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self.open_button.setEnabled(False)
        self.file_info.setText(f"Loading {Path(path).name}…")
        self._preview_worker = PdfPreviewWorker(str(Path(path).absolute()))
        self._preview_worker.loaded.connect(self._input_loaded)
        self._preview_worker.thumbnail_ready.connect(self._thumbnail_ready)
        self._preview_worker.failed.connect(self._input_failed)
        self._preview_worker.finished.connect(self._preview_worker_finished)
        self._preview_worker.start()

    def _input_loaded(self, path: str, page_count: int) -> None:
        self.input_path = path
        self.page_count = page_count
        self.file_info.setText(f"{Path(path).name} — {page_count} pages")
        self.selection_input.setEnabled(True)
        self.output_button.setEnabled(True)
        self.update_preview()

    def _thumbnail_ready(self, _path: str, page_number: int, image) -> None:
        button = self._page_buttons.get(page_number)
        if button is None:
            button = self.thumbnail_grid.add_page(page_number)
            self._page_buttons[page_number] = button
        button.set_thumbnail(image)
        try:
            selected = set(parse_page_selection(
                self.selection_input.text(), self.page_count, allow_all=True
            ))
        except PDFOperationError:
            selected = set()
        self._sync_thumbnail_selection(selected)

    def _input_failed(self, _path: str, message: str) -> None:
        self.input_path = None
        self.page_count = 0
        self._page_buttons.clear()
        self.thumbnail_grid.clear_pages()
        self.file_info.setText("No valid PDF selected")
        self.preview_error.setText(message)
        self.preview_error.setStyleSheet("color: #F28B82;")
        self.selection_input.setEnabled(False)
        self.output_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        QMessageBox.critical(self, "Could not preview PDF", message)

    def _preview_worker_finished(self) -> None:
        self.open_button.setEnabled(True)
        self._preview_worker = None

    def _page_toggled(self, page_number: int, checked: bool) -> None:
        selected = set()
        try:
            selected.update(parse_page_selection(
                self.selection_input.text(), self.page_count, allow_all=True
            ))
        except PDFOperationError:
            pass
        if checked:
            selected.add(page_number)
        else:
            selected.discard(page_number)
        text = format_page_numbers(sorted(selected)) if selected else ""
        self.selection_input.setText(text)

    def update_preview(self, _text: str = "") -> None:
        if not self.input_path or self.page_count < 1:
            return
        try:
            removed = parse_page_selection(
                self.selection_input.text(), self.page_count, allow_all=True
            )
        except PDFOperationError as exc:
            self.preview_removed.setText("Pages to remove: —")
            self.preview_remaining.setText(f"Pages that will remain: {self.page_count} pages")
            self.preview_error.setText(str(exc))
            self.preview_error.setStyleSheet("color: #F28B82;")
            self._sync_thumbnail_selection(set())
            self.remove_button.setEnabled(False)
            return

        removed_set = set(removed)
        remaining = [page for page in range(1, self.page_count + 1) if page not in removed_set]
        self.preview_removed.setText(
            f"Pages to remove ({len(removed)}): {format_page_numbers(removed)}"
        )
        self.preview_remaining.setText(
            f"Pages that will remain ({len(remaining)}): {format_page_numbers(remaining)}"
        )
        if not remaining:
            self.preview_error.setText("You cannot remove every page. Leave at least one page in the PDF.")
            self.preview_error.setStyleSheet("color: #F28B82;")
        else:
            self.preview_error.setText("Click a page thumbnail to toggle it for removal.")
            self.preview_error.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        self._sync_thumbnail_selection(removed_set)
        self.remove_button.setEnabled(bool(remaining))

    def _sync_thumbnail_selection(self, selected: set[int]) -> None:
        for page_number, button in self._page_buttons.items():
            button.blockSignals(True)
            button.setChecked(page_number in selected)
            button.setText(
                f"Page {page_number} • Remove" if page_number in selected else f"Page {page_number}"
            )
            button.setAccessibleName(
                f"Page {page_number}, selected for removal" if page_number in selected
                else f"Page {page_number}, select to remove"
            )
            button.blockSignals(False)

    def choose_output(self) -> None:
        if not self.input_path:
            return
        source = Path(self.input_path)
        suggestion = str(source.with_name(f"{source.stem}_pages_removed.pdf"))
        output, _ = QFileDialog.getSaveFileName(
            self, "Save modified PDF", suggestion, "PDF documents (*.pdf)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if output:
            if Path(output).suffix.casefold() != ".pdf":
                output += ".pdf"
            self.output_input.setText(str(Path(output).absolute()))

    def start_removal(self) -> None:
        if not self.input_path:
            QMessageBox.warning(self, "Open a PDF", "Choose a PDF file first.")
            return
        selection = self.selection_input.text()
        try:
            parse_page_selection(selection, self.page_count)
        except PDFOperationError as exc:
            self.update_preview()
            QMessageBox.warning(self, "Check page selection", str(exc))
            return
        output_text = self.output_input.text().strip()
        if not output_text:
            QMessageBox.warning(self, "Choose an output", "Choose a new output filename and location first.")
            return
        try:
            output = validate_pdf_output_path(output_text, [self.input_path], overwrite=True)
        except PDFOperationError as exc:
            QMessageBox.warning(self, "Invalid output", str(exc))
            return

        overwrite = False
        if output.exists():
            choice = QMessageBox.question(
                self, "Replace existing PDF?",
                f"The file already exists:\n{output}\n\nReplace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
            overwrite = True

        self._set_controls_enabled(False)
        self.remove_button.setText("Saving…")
        self._remove_worker = RemovePagesWorker(
            self.input_path, str(output), selection, overwrite
        )
        self._remove_worker.succeeded.connect(self._removal_succeeded)
        self._remove_worker.failed.connect(self._removal_failed)
        self._remove_worker.finished.connect(self._removal_worker_finished)
        self._remove_worker.start()

    def _removal_succeeded(self, output: str) -> None:
        QMessageBox.information(
            self, "Pages removed", f"The modified PDF was saved to:\n{output}"
        )

    def _removal_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Could not remove pages", message)

    def _removal_worker_finished(self) -> None:
        self.remove_button.setText("Save PDF Without Selected Pages")
        self._set_controls_enabled(True)
        self.update_preview()
        self._remove_worker = None

    def _set_controls_enabled(self, enabled: bool) -> None:
        for control in (self.open_button, self.selection_input, self.output_button, self.remove_button):
            control.setEnabled(enabled)
