"""Native GUI for exporting PDF pages as individual images."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt, QSize
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox,
    QProgressBar, QPushButton, QSpinBox, QVBoxLayout, QWidget, QScrollArea,
)

from src.core.pdf_output import PDFOperationError
from src.core.pdf_to_images import (
    DEFAULT_DPI, MAX_DPI, MIN_DPI, SUPPORTED_FORMATS, expected_image_paths,
    pdf_to_images,
)
from src.ui.pdf_preview import PdfPreviewWorker, ThumbnailGrid
from src.ui.theme import Theme


class PdfToImagesWorker(QThread):
    progress = Signal(int, int)
    succeeded = Signal(str, int)
    failed = Signal(str)

    def __init__(self, source: str, folder: str, image_format: str, dpi: int, overwrite: bool) -> None:
        super().__init__()
        self.source = source
        self.folder = folder
        self.image_format = image_format
        self.dpi = dpi
        self.overwrite = overwrite

    def run(self) -> None:
        try:
            outputs = pdf_to_images(
                self.source, self.folder, image_format=self.image_format, dpi=self.dpi,
                overwrite=self.overwrite, progress_callback=self.progress.emit,
            )
            self.succeeded.emit(self.folder, len(outputs))
        except PDFOperationError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Could not export PDF pages: {exc}")


class PdfToImagesPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(16)

        heading = QLabel("PDF to Images")
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        description = QLabel(
            "Export every page as a separate image in page order. All conversion stays on this computer."
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

        self.thumbnail_grid = ThumbnailGrid(
            selectable=False,
            icon_size=QSize(100, 128),
            button_size=QSize(132, 172),
        )
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setMinimumHeight(185)
        self.preview_scroll.setAccessibleName("Selected PDF page previews")
        self.preview_scroll.setWidget(self.thumbnail_grid)
        layout.addWidget(self.preview_scroll, 1)

        form = QFormLayout()
        self.format_combo = QComboBox()
        self.format_combo.setAccessibleName("Export image format")
        self.format_combo.addItems(list(SUPPORTED_FORMATS))
        self.format_combo.setCurrentText("PNG")
        form.addRow("Image format", self.format_combo)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(MIN_DPI, MAX_DPI)
        self.dpi_spin.setValue(DEFAULT_DPI)
        self.dpi_spin.setSuffix(" DPI")
        self.dpi_spin.setAccessibleName("Image resolution in DPI")
        form.addRow("Resolution", self.dpi_spin)
        layout.addLayout(form)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Output folder"))
        self.folder_label = QLabel("Choose an existing folder…")
        self.folder_label.setWordWrap(True)
        self.folder_label.setAccessibleName("Image export output folder")
        folder_row.addWidget(self.folder_label, 1)
        self.folder_button = QPushButton("Choose Folder…")
        self.folder_button.clicked.connect(self.choose_folder)
        self.folder_button.setEnabled(False)
        folder_row.addWidget(self.folder_button)
        layout.addLayout(folder_row)

        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.export_button = QPushButton("Export PDF Pages")
        self.export_button.setMinimumHeight(48)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.start_export)
        layout.addWidget(self.export_button, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addStretch()

        self.input_path: str | None = None
        self.page_count: int | None = None
        self.output_folder: str | None = None
        self._preview_path: str | None = None
        self._preview_worker: PdfPreviewWorker | None = None
        self._worker: PdfToImagesWorker | None = None

    def choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF documents (*.pdf)")
        if not path:
            return
        self._load_preview(str(Path(path).absolute()))

    def _load_preview(self, path: str) -> None:
        self.input_path = None
        self.page_count = None
        self._preview_path = path
        self.thumbnail_grid.clear_pages()
        self.file_info.setText(f"Loading preview for {Path(path).name}…")
        self.folder_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self._preview_worker = PdfPreviewWorker(path)
        self._preview_worker.loaded.connect(self._input_loaded)
        self._preview_worker.thumbnail_ready.connect(self._thumbnail_ready)
        self._preview_worker.failed.connect(self._input_failed)
        self._preview_worker.finished.connect(self._preview_finished)
        self._preview_worker.start()

    def _input_loaded(self, path: str, page_count: int) -> None:
        self.input_path = path
        self.page_count = page_count
        self.file_info.setText(f"{Path(path).name} — {page_count} pages")
        self.progress_label.setText(f"Loading page previews for {page_count} pages…")
        self.folder_button.setEnabled(True)
        self._update_export_enabled()

    def _input_failed(self, _path: str, message: str) -> None:
        self.input_path = None
        self.page_count = None
        self._preview_path = None
        self.thumbnail_grid.clear_pages()
        self.file_info.setText("No valid PDF selected")
        self.folder_button.setEnabled(False)
        self.export_button.setEnabled(False)
        QMessageBox.critical(self, "Could not open PDF", message)

    def _thumbnail_ready(self, path: str, page_number: int, image) -> None:
        if path != self._preview_path:
            return
        button = self.thumbnail_grid.add_page(page_number)
        button.set_thumbnail(image)

    def _preview_finished(self) -> None:
        if self.page_count is not None:
            self.progress_label.setText(
                f"Preview loaded: {self.page_count} pages. Choose an output folder to export."
            )
        self.open_button.setEnabled(True)
        self._preview_worker = None

    def choose_folder(self) -> None:
        if not self.input_path:
            return
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_folder or "")
        if folder:
            self.output_folder = str(Path(folder).absolute())
            self.folder_label.setText(self.output_folder)
            self._update_export_enabled()

    def _update_export_enabled(self) -> None:
        self.export_button.setEnabled(
            self.input_path is not None and self.page_count is not None and self.output_folder is not None
        )

    def start_export(self) -> None:
        if not self.input_path or self.page_count is None or not self.output_folder:
            QMessageBox.warning(self, "Choose input and output", "Open a PDF and choose an output folder first.")
            return
        image_format = self.format_combo.currentText()
        try:
            outputs = expected_image_paths(self.output_folder, self.page_count, image_format)
        except PDFOperationError as exc:
            QMessageBox.warning(self, "Invalid export settings", str(exc))
            return
        existing = [path for path in outputs if path.exists()]
        overwrite = False
        if existing:
            choice = QMessageBox.question(
                self,
                "Replace existing images?",
                f"{len(existing)} page image(s) already exist in this folder. Replace them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
            overwrite = True

        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Preparing page export…")
        self._worker = PdfToImagesWorker(
            self.input_path, self.output_folder, image_format, self.dpi_spin.value(), overwrite
        )
        self._worker.progress.connect(self._update_progress)
        self._worker.succeeded.connect(self._export_succeeded)
        self._worker.failed.connect(self._export_failed)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _update_progress(self, current: int, total: int) -> None:
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"Exporting page {current} of {total}…")

    def _export_succeeded(self, folder: str, count: int) -> None:
        self.progress_label.setText(f"Exported {count} images to {folder}")
        QMessageBox.information(
            self, "Export complete", f"Exported {count} page images to:\n{folder}"
        )

    def _export_failed(self, message: str) -> None:
        self.progress_label.setText(message)
        QMessageBox.critical(self, "PDF export failed", message)

    def _set_busy(self, busy: bool) -> None:
        for widget in (self.open_button, self.format_combo, self.dpi_spin,
                       self.folder_button, self.export_button):
            widget.setEnabled(not busy)
        if not busy:
            self.folder_button.setEnabled(self.input_path is not None)
            self.open_button.setEnabled(True)
            self._update_export_enabled()
            self._worker = None
        self.progress_bar.setVisible(busy)
