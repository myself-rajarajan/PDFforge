"""Native GUI for unlocking a PDF with a supplied password."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path
from src.core.unlock_pdf import unlock_pdf
from src.ui.theme import Theme


class UnlockPdfWorker(QThread):
    """Run password verification and PDF writing off the GUI thread."""

    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, source: str, output: str, password: str, overwrite: bool) -> None:
        super().__init__()
        self.source = source
        self.output = output
        self.password = password
        self.overwrite = overwrite

    def run(self) -> None:
        try:
            saved = unlock_pdf(self.source, self.output, self.password, overwrite=self.overwrite)
            self.succeeded.emit(str(saved))
        except PDFOperationError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("An unexpected error occurred while unlocking the PDF.")


class UnlockPdfPage(QWidget):
    """Input, password, and output controls for PDF unlocking."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(18)

        heading = QLabel("Unlock PDF")
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        description = QLabel(
            "Remove password protection from a PDF when you know its password. The original file is preserved."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(description)

        input_row = QHBoxLayout()
        self.open_button = QPushButton("Open PDF…")
        self.open_button.clicked.connect(self.choose_input)
        input_row.addWidget(self.open_button)
        self.file_info = QLabel("No PDF selected")
        self.file_info.setWordWrap(True)
        self.file_info.setAccessibleName("Selected PDF filename")
        input_row.addWidget(self.file_info, 1)
        layout.addLayout(input_row)

        form = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter the authorized PDF password")
        self.password_input.setAccessibleName("PDF password")
        form.addRow("Password", self.password_input)
        layout.addLayout(form)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Save unlocked PDF to"))
        self.output_label = QLabel("Choose a new filename and location…")
        self.output_label.setWordWrap(True)
        self.output_label.setAccessibleName("Unlocked PDF output path")
        output_row.addWidget(self.output_label, 1)
        self.output_button = QPushButton("Choose Output…")
        self.output_button.setEnabled(False)
        self.output_button.clicked.connect(self.choose_output)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.unlock_button = QPushButton("Unlock PDF")
        self.unlock_button.setMinimumHeight(48)
        self.unlock_button.setEnabled(False)
        self.unlock_button.clicked.connect(self.start_unlock)
        action_row.addWidget(self.unlock_button)
        layout.addLayout(action_row)
        layout.addStretch()

        self.input_path: str | None = None
        self.output_path: str | None = None
        self._worker: UnlockPdfWorker | None = None
        self.password_input.textChanged.connect(self._update_enabled)

    def choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF documents (*.pdf)")
        if not path:
            return
        self.input_path = str(Path(path).absolute())
        self.output_path = None
        self.file_info.setText(Path(path).name)
        self.output_label.setText("Choose a new filename and location…")
        self.output_button.setEnabled(True)
        self._update_enabled()

    def choose_output(self) -> None:
        if not self.input_path:
            return
        source = Path(self.input_path)
        suggestion = str(source.with_name(f"{source.stem}_unlocked.pdf"))
        output, _ = QFileDialog.getSaveFileName(
            self, "Save unlocked PDF", suggestion, "PDF documents (*.pdf)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if output:
            if Path(output).suffix.casefold() != ".pdf":
                output += ".pdf"
            self.output_path = str(Path(output).absolute())
            self.output_label.setText(self.output_path)
            self._update_enabled()

    def _update_enabled(self) -> None:
        self.unlock_button.setEnabled(bool(
            self.input_path and self.output_path and self.password_input.text()
        ))

    def start_unlock(self) -> None:
        if not self.input_path or not self.output_path:
            QMessageBox.warning(self, "Choose input and output", "Open a PDF and choose an output location first.")
            return
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Enter password", "Enter the PDF password to continue.")
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
        self.unlock_button.setText("Unlocking PDF…")
        self._worker = UnlockPdfWorker(self.input_path, str(output), password, overwrite)
        self._worker.succeeded.connect(self._unlock_succeeded)
        self._worker.failed.connect(self._unlock_failed)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _unlock_succeeded(self, output: str) -> None:
        QMessageBox.information(self, "PDF unlocked", f"The unlocked PDF was saved to:\n{output}")

    def _unlock_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Could not unlock PDF", message)

    def _worker_finished(self) -> None:
        self.password_input.clear()
        self.unlock_button.setText("Unlock PDF")
        self._set_controls_enabled(True)
        self._worker = None

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.open_button.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.output_button.setEnabled(enabled and self.input_path is not None)
        self.unlock_button.setEnabled(enabled and bool(
            self.input_path and self.output_path and self.password_input.text()
        ))
