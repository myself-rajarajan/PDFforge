"""Native GUI page for merging local PDF documents."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from src.core.merge import MergeError, merge_pdfs, validate_output_path
from src.ui.pdf_preview import PdfPreviewWorker
from src.ui.theme import Theme


class MergeWorker(QThread):
    """Run normal PDF merges away from the UI thread."""

    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, inputs: list[str], output: str, overwrite: bool) -> None:
        super().__init__()
        self.inputs = inputs
        self.output = output
        self.overwrite = overwrite

    def run(self) -> None:
        try:
            saved_path = merge_pdfs(self.inputs, self.output, overwrite=self.overwrite)
            self.succeeded.emit(str(saved_path))
        except MergeError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # Keep unexpected worker failures user-visible.
            self.failed.emit(f"The merge could not be completed: {exc}")


class MergePDFPage(QWidget):
    """File ordering, output selection, and asynchronous merge controls."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(16)

        heading = QLabel("Merge PDFs")
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        description = QLabel(
            "Combine local PDF files in the order shown below. Files stay on this computer."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(description)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.setAccessibleName("PDF files in merge order")
        self.file_list.setIconSize(QSize(130, 170))
        self.file_list.setSpacing(8)
        self.file_list.setMinimumHeight(190)
        layout.addWidget(self.file_list, 1)

        file_controls = QHBoxLayout()
        self.add_button = QPushButton("Add PDFs…")
        self.remove_button = QPushButton("Remove Selected")
        self.up_button = QPushButton("Move Up")
        self.down_button = QPushButton("Move Down")
        self.add_button.clicked.connect(self.add_files)
        self.remove_button.clicked.connect(self.remove_selected)
        self.up_button.clicked.connect(self.move_selected_up)
        self.down_button.clicked.connect(self.move_selected_down)
        for button in (self.add_button, self.remove_button, self.up_button, self.down_button):
            file_controls.addWidget(button)
        file_controls.addStretch()
        layout.addLayout(file_controls)

        output_row = QHBoxLayout()
        output_label = QLabel("Save merged PDF to")
        self.output_input = QLineEdit()
        self.output_input.setReadOnly(True)
        self.output_input.setPlaceholderText("Choose an output filename and folder…")
        self.output_input.setAccessibleName("Merged PDF output path")
        self.output_button = QPushButton("Choose Output…")
        self.output_button.clicked.connect(self.choose_output)
        output_row.addWidget(output_label)
        output_row.addWidget(self.output_input, 1)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.merge_button = QPushButton("Merge PDFs")
        self.merge_button.setMinimumWidth(150)
        self.merge_button.clicked.connect(self.start_merge)
        action_row.addWidget(self.merge_button)
        layout.addLayout(action_row)

        self._worker: MergeWorker | None = None
        self._preview_workers: dict[str, PdfPreviewWorker] = {}

    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add PDF files", "", "PDF documents (*.pdf)"
        )
        existing = {self.file_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.file_list.count())}
        for file_path in files:
            normalized = str(Path(file_path).resolve())
            if normalized not in existing:
                item = QListWidgetItem(f"Loading preview…  {Path(normalized).name}")
                item.setData(Qt.ItemDataRole.UserRole, normalized)
                item.setToolTip(normalized)
                item.setSizeHint(QSize(360, 190))
                self.file_list.addItem(item)
                existing.add(normalized)
                preview = PdfPreviewWorker(normalized, page_numbers=[1])
                preview.loaded.connect(self._preview_loaded)
                preview.thumbnail_ready.connect(self._preview_thumbnail_ready)
                preview.failed.connect(self._preview_failed)
                preview.finished.connect(lambda path=normalized: self._preview_finished(path))
                self._preview_workers[normalized] = preview
                preview.start()

    def _find_file_item(self, path: str) -> QListWidgetItem | None:
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                return item
        return None

    def _preview_loaded(self, path: str, page_count: int) -> None:
        item = self._find_file_item(path)
        if item is not None:
            item.setText(f"{Path(path).name}  •  {page_count} pages")

    def _preview_thumbnail_ready(self, path: str, _page_number: int, image) -> None:
        item = self._find_file_item(path)
        if item is not None:
            item.setIcon(QIcon(QPixmap.fromImage(image)))

    def _preview_failed(self, path: str, message: str) -> None:
        item = self._find_file_item(path)
        if item is not None:
            item.setText(f"{Path(path).name}  •  preview unavailable")
            item.setToolTip(f"{path}\n{message}")

    def _preview_finished(self, path: str) -> None:
        self._preview_workers.pop(path, None)

    def remove_selected(self) -> None:
        for row in sorted((self.file_list.row(item) for item in self.file_list.selectedItems()), reverse=True):
            self.file_list.takeItem(row)

    def move_selected_up(self) -> None:
        rows = sorted(self.file_list.row(item) for item in self.file_list.selectedItems())
        for row in rows:
            if row > 0:
                item = self.file_list.takeItem(row)
                self.file_list.insertItem(row - 1, item)
                item.setSelected(True)

    def move_selected_down(self) -> None:
        rows = sorted((self.file_list.row(item) for item in self.file_list.selectedItems()), reverse=True)
        for row in rows:
            if row < self.file_list.count() - 1:
                item = self.file_list.takeItem(row)
                self.file_list.insertItem(row + 1, item)
                item.setSelected(True)

    def choose_output(self) -> None:
        suggested_name = "merged.pdf"
        if self.file_list.count():
            first = Path(self.file_list.item(0).data(Qt.ItemDataRole.UserRole))
            suggested_name = str(first.with_name(f"{first.stem}_merged.pdf"))
        output, _ = QFileDialog.getSaveFileName(
            self, "Save merged PDF", suggested_name, "PDF documents (*.pdf)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if output:
            if Path(output).suffix.casefold() != ".pdf":
                output += ".pdf"
            self.output_input.setText(str(Path(output).absolute()))

    def start_merge(self) -> None:
        inputs = [str(self.file_list.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.file_list.count())]
        if len(inputs) < 2:
            QMessageBox.warning(self, "Select PDFs", "Add at least two PDF files to merge.")
            return
        output_text = self.output_input.text().strip()
        if not output_text:
            QMessageBox.warning(self, "Choose an output", "Choose where to save the merged PDF first.")
            return

        try:
            output = validate_output_path(output_text, inputs, overwrite=True)
        except MergeError as exc:
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
        self.merge_button.setText("Merging…")
        self._worker = MergeWorker(inputs, str(output), overwrite)
        self._worker.succeeded.connect(self._show_success)
        self._worker.failed.connect(self._show_failure)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _show_success(self, output: str) -> None:
        QMessageBox.information(self, "Merge complete", f"The merged PDF was saved to:\n{output}")

    def _show_failure(self, message: str) -> None:
        QMessageBox.critical(self, "Merge failed", message)

    def _worker_finished(self) -> None:
        self.merge_button.setText("Merge PDFs")
        self._set_controls_enabled(True)
        self._worker = None

    def _set_controls_enabled(self, enabled: bool) -> None:
        for button in (
            self.add_button, self.remove_button, self.up_button, self.down_button,
            self.output_button, self.merge_button,
        ):
            button.setEnabled(enabled)
        self.file_list.setEnabled(enabled)
