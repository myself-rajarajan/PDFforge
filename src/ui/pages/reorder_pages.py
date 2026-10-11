"""Native GUI page for previewing and reordering local PDF pages."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path
from src.core.reorder_pages import reorder_pdf_pages
from src.ui.pdf_preview import PdfPreviewWorker, ThumbnailGrid
from src.ui.theme import Theme


class ReorderPagesWorker(QThread):
    """Write the reordered document away from the GUI thread."""

    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, source: str, output: str, page_order: list[int], overwrite: bool) -> None:
        super().__init__()
        self.source = source
        self.output = output
        self.page_order = page_order
        self.overwrite = overwrite

    def run(self) -> None:
        try:
            saved = reorder_pdf_pages(
                self.source, self.output, self.page_order, overwrite=self.overwrite
            )
            self.succeeded.emit(str(saved))
        except PDFOperationError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Could not save the reordered PDF: {exc}")


class ReorderPagesPage(QWidget):
    """PDF page thumbnails with drag ordering and safe output controls."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        heading = QLabel("Reorder PDF Pages")
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        description = QLabel(
            "Drag a page preview onto another page: drop in its upper half to place it before, or lower half to place it after. The position and original page number are shown on each preview."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(description)

        file_row = QHBoxLayout()
        self.open_button = QPushButton("Open PDF…")
        self.open_button.clicked.connect(self.choose_input)
        self.file_info = QLabel("No PDF selected")
        self.file_info.setWordWrap(True)
        self.file_info.setAccessibleName("Selected PDF filename and page count")
        file_row.addWidget(self.open_button)
        file_row.addWidget(self.file_info, 1)
        layout.addLayout(file_row)

        self.thumbnail_grid = ThumbnailGrid(draggable=True)
        self.thumbnail_grid.page_dropped.connect(self._page_moved)
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setMinimumHeight(350)
        self.preview_scroll.setWidget(self.thumbnail_grid)
        layout.addWidget(self.preview_scroll, 1)

        self.order_label = QLabel("Current order: —")
        self.order_label.setWordWrap(True)
        self.order_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.order_label)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Save reordered PDF to"))
        self.output_label = QLabel("Choose a new filename and location…")
        self.output_label.setWordWrap(True)
        self.output_label.setAccessibleName("Reordered PDF output path")
        output_row.addWidget(self.output_label, 1)
        self.output_button = QPushButton("Choose Output…")
        self.output_button.clicked.connect(self.choose_output)
        self.output_button.setEnabled(False)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row)

        self.save_button = QPushButton("Save Reordered PDF")
        self.save_button.setMinimumHeight(48)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.start_reorder)
        layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.input_path: str | None = None
        self.page_count = 0
        self.output_path: str | None = None
        self.page_order: list[int] = []
        self._preview_worker: PdfPreviewWorker | None = None
        self._worker: ReorderPagesWorker | None = None

    def choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF documents (*.pdf)")
        if not path:
            return
        self.input_path = None
        self.page_count = 0
        self.page_order = []
        self.output_path = None
        self.thumbnail_grid.clear_pages()
        self.order_label.setText("Current order: Loading page previews…")
        self.file_info.setText(f"Loading {Path(path).name}…")
        self.output_label.setText("Choose a new filename and location…")
        self.output_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self._preview_worker = PdfPreviewWorker(str(Path(path).absolute()))
        self._preview_worker.loaded.connect(self._input_loaded)
        self._preview_worker.thumbnail_ready.connect(self._thumbnail_ready)
        self._preview_worker.failed.connect(self._input_failed)
        self._preview_worker.finished.connect(self._preview_finished)
        self._preview_worker.start()

    def _input_loaded(self, path: str, page_count: int) -> None:
        self.input_path = path
        self.page_count = page_count
        self.page_order = list(range(1, page_count + 1))
        self.file_info.setText(f"{Path(path).name} — {page_count} pages")
        self.output_button.setEnabled(True)
        self.save_button.setEnabled(self.output_path is not None)
        self._update_order_label()

    def _thumbnail_ready(self, _path: str, page_number: int, image) -> None:
        button = self.thumbnail_grid.add_page(page_number)
        button.set_thumbnail(image)
        self._sync_grid_order()

    def _input_failed(self, _path: str, message: str) -> None:
        self.input_path = None
        self.page_count = 0
        self.page_order = []
        self.thumbnail_grid.clear_pages()
        self.file_info.setText("No valid PDF selected")
        self.order_label.setText(message)
        self.order_label.setStyleSheet("color: #F28B82;")
        self.output_button.setEnabled(False)
        self.save_button.setEnabled(False)
        QMessageBox.critical(self, "Could not open PDF", message)

    def _preview_finished(self) -> None:
        self.open_button.setEnabled(True)
        self._preview_worker = None

    def _page_moved(self, source_page: int, target_page: int, insert_after: bool = False) -> None:
        if source_page not in self.page_order or target_page not in self.page_order:
            return
        if source_page == target_page:
            return
        self.thumbnail_grid.move_page(source_page, target_page, insert_after)
        self.page_order.remove(source_page)
        destination = self.page_order.index(target_page) + int(insert_after)
        self.page_order.insert(destination, source_page)
        self._sync_grid_order()
        self._update_order_label()

    def _sync_grid_order(self) -> None:
        self.thumbnail_grid.set_page_order(self.page_order)

    def _update_order_label(self) -> None:
        self.order_label.setStyleSheet("")
        self.order_label.setText(
            "Current order (original page numbers): " +
            (" → ".join(map(str, self.page_order)) if self.page_order else "—")
        )

    def choose_output(self) -> None:
        if not self.input_path:
            return
        source = Path(self.input_path)
        suggested = str(source.with_name(f"{source.stem}_reordered.pdf"))
        output, _ = QFileDialog.getSaveFileName(
            self, "Save reordered PDF", suggested, "PDF documents (*.pdf)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if output:
            if Path(output).suffix.casefold() != ".pdf":
                output += ".pdf"
            self.output_path = str(Path(output).absolute())
            self.output_label.setText(self.output_path)
            self.save_button.setEnabled(True)

    def start_reorder(self) -> None:
        if not self.input_path or not self.output_path:
            QMessageBox.warning(self, "Choose input and output", "Open a PDF and choose an output location first.")
            return
        try:
            output = validate_pdf_output_path(self.output_path, [self.input_path], overwrite=True)
        except PDFOperationError as exc:
            QMessageBox.warning(self, "Invalid output", str(exc))
            return
        overwrite = False
        if output.exists():
            choice = QMessageBox.question(
                self, "Replace existing PDF?", f"The file already exists:\n{output}\n\nReplace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
            overwrite = True
        self._set_controls_enabled(False)
        self.save_button.setText("Saving…")
        self._worker = ReorderPagesWorker(
            self.input_path, str(output), list(self.page_order), overwrite
        )
        self._worker.succeeded.connect(self._reorder_succeeded)
        self._worker.failed.connect(self._reorder_failed)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _reorder_succeeded(self, output: str) -> None:
        QMessageBox.information(self, "Reorder complete", f"The reordered PDF was saved to:\n{output}")

    def _reorder_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Reorder failed", message)

    def _worker_finished(self) -> None:
        self.save_button.setText("Save Reordered PDF")
        self._set_controls_enabled(True)
        self._worker = None

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.open_button.setEnabled(enabled)
        self.output_button.setEnabled(enabled and self.input_path is not None)
        self.save_button.setEnabled(enabled and self.output_path is not None and self.input_path is not None)
        self.preview_scroll.setEnabled(enabled)
