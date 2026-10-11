"""Native GUI page for adding sequential page numbers to a local PDF."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from src.core.add_page_numbers import (
    MAX_FONT_SIZE, MAX_STARTING_NUMBER, MIN_FONT_SIZE, PAGE_NUMBER_POSITIONS,
    add_page_numbers,
)
from src.core.pdf_output import PDFOperationError, validate_pdf_output_path
from src.ui.pdf_preview import PdfPreviewWorker
from src.ui.theme import Theme


class AddPageNumbersWorker(QThread):
    """Run PDF page-number insertion away from the UI thread."""

    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(
        self, source: str, output: str, position: str,
        starting_number: int, font_size: int, overwrite: bool,
    ) -> None:
        super().__init__()
        self.source = source
        self.output = output
        self.position = position
        self.starting_number = starting_number
        self.font_size = font_size
        self.overwrite = overwrite

    def run(self) -> None:
        try:
            saved = add_page_numbers(
                self.source,
                self.output,
                position=self.position,
                starting_number=self.starting_number,
                font_size=self.font_size,
                overwrite=self.overwrite,
            )
            self.succeeded.emit(str(saved))
        except PDFOperationError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Could not add page numbers: {exc}")


class AddPageNumbersPage(QWidget):
    """Input selection, numbering options, and output controls."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(18)

        heading = QLabel("Add Page Numbers")
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        description = QLabel(
            "Add sequential page numbers to a local PDF. The original file is preserved."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(description)

        input_row = QHBoxLayout()
        self.open_button = QPushButton("Open PDF…")
        self.open_button.clicked.connect(self.choose_input)
        self.file_info = QLabel("No PDF selected")
        self.file_info.setWordWrap(True)
        self.file_info.setAccessibleName("Selected PDF filename")
        input_row.addWidget(self.open_button)
        input_row.addWidget(self.file_info, 1)
        layout.addLayout(input_row)

        form = QFormLayout()
        self.position_combo = QComboBox()
        self.position_combo.setAccessibleName("Page number position")
        for label, value in PAGE_NUMBER_POSITIONS.items():
            self.position_combo.addItem(label, value)
        self.position_combo.setCurrentIndex(self.position_combo.findData("bottom-center"))
        form.addRow("Position", self.position_combo)

        self.starting_number = QSpinBox()
        self.starting_number.setRange(1, MAX_STARTING_NUMBER)
        self.starting_number.setValue(1)
        self.starting_number.setAccessibleName("Starting page number")
        form.addRow("Starting number", self.starting_number)

        self.font_size = QSpinBox()
        self.font_size.setRange(MIN_FONT_SIZE, MAX_FONT_SIZE)
        self.font_size.setValue(12)
        self.font_size.setSuffix(" pt")
        self.font_size.setAccessibleName("Page number font size in points")
        form.addRow("Font size", self.font_size)
        layout.addLayout(form)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Save numbered PDF to"))
        self.output_label = QLabel("Choose a new filename and location…")
        self.output_label.setWordWrap(True)
        self.output_label.setAccessibleName("Numbered PDF output path")
        output_row.addWidget(self.output_label, 1)
        self.output_button = QPushButton("Choose Output…")
        self.output_button.setEnabled(False)
        self.output_button.clicked.connect(self.choose_output)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.apply_button = QPushButton("Add Page Numbers")
        self.apply_button.setMinimumHeight(48)
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self.start_numbering)
        action_row.addWidget(self.apply_button)
        layout.addLayout(action_row)
        layout.addStretch()

        self.input_path: str | None = None
        self.output_path: str | None = None
        self.page_count: int | None = None
        self._worker: AddPageNumbersWorker | None = None
        self._preview_worker: PdfPreviewWorker | None = None

    def choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF documents (*.pdf)")
        if not path:
            return
        self.input_path = None
        self.output_path = None
        self.page_count = None
        self.file_info.setText(f"Checking {Path(path).name}…")
        self.output_label.setText("Choose a new filename and location…")
        self.output_button.setEnabled(False)
        self.apply_button.setEnabled(False)
        self.open_button.setEnabled(False)
        # The shared renderer validates readability/encryption and reports page count.
        self._preview_worker = PdfPreviewWorker(str(Path(path).absolute()), page_numbers=[])
        self._preview_worker.loaded.connect(self._input_loaded)
        self._preview_worker.failed.connect(self._input_failed)
        self._preview_worker.finished.connect(self._preview_finished)
        self._preview_worker.start()

    def _input_loaded(self, path: str, page_count: int) -> None:
        self.input_path = path
        self.page_count = page_count
        self.file_info.setText(f"{Path(path).name} — {page_count} pages")
        self.output_button.setEnabled(True)
        self.apply_button.setEnabled(self.output_path is not None)

    def _input_failed(self, _path: str, message: str) -> None:
        self.input_path = None
        self.page_count = None
        self.file_info.setText("No valid PDF selected")
        self.output_button.setEnabled(False)
        self.apply_button.setEnabled(False)
        QMessageBox.critical(self, "Could not open PDF", message)

    def _preview_finished(self) -> None:
        self.open_button.setEnabled(True)
        self._preview_worker = None

    def choose_output(self) -> None:
        if not self.input_path:
            return
        source = Path(self.input_path)
        suggestion = str(source.with_name(f"{source.stem}_numbered.pdf"))
        output, _ = QFileDialog.getSaveFileName(
            self, "Save numbered PDF", suggestion, "PDF documents (*.pdf)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if output:
            if Path(output).suffix.casefold() != ".pdf":
                output += ".pdf"
            self.output_path = str(Path(output).absolute())
            self.output_label.setText(self.output_path)
            self.apply_button.setEnabled(self.input_path is not None)

    def start_numbering(self) -> None:
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
        self.apply_button.setText("Adding page numbers…")
        self._worker = AddPageNumbersWorker(
            self.input_path,
            str(output),
            str(self.position_combo.currentData()),
            self.starting_number.value(),
            self.font_size.value(),
            overwrite,
        )
        self._worker.succeeded.connect(self._numbering_succeeded)
        self._worker.failed.connect(self._numbering_failed)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _numbering_succeeded(self, output: str) -> None:
        QMessageBox.information(self, "Page numbers added", f"The numbered PDF was saved to:\n{output}")

    def _numbering_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Could not add page numbers", message)

    def _worker_finished(self) -> None:
        self.apply_button.setText("Add Page Numbers")
        self._set_controls_enabled(True)
        self._worker = None

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.open_button.setEnabled(enabled)
        self.position_combo.setEnabled(enabled)
        self.starting_number.setEnabled(enabled)
        self.font_size.setEnabled(enabled)
        self.output_button.setEnabled(enabled and self.input_path is not None)
        self.apply_button.setEnabled(enabled and self.output_path is not None and self.input_path is not None)
