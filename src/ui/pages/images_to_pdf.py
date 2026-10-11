"""Native GUI for assembling selected images into a PDF."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt, QSize
from PySide6.QtGui import QImage, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QProgressBar, QLineEdit, QVBoxLayout, QWidget,
)

from src.core.images_to_pdf import DEFAULT_DPI, images_to_pdf
from src.core.pdf_output import PDFOperationError, validate_pdf_output_path
from src.ui.theme import Theme


class ImageThumbnailWorker(QThread):
    """Decode an image preview away from the GUI thread."""

    loaded = Signal(str, QImage)
    failed = Signal(str, str)

    def __init__(self, path: str) -> None:
        super().__init__()
        self.path = path

    def run(self) -> None:
        try:
            from PIL import Image, ImageOps

            with Image.open(self.path) as source:
                preview = ImageOps.exif_transpose(source)
                preview.thumbnail((320, 240), Image.Resampling.LANCZOS)
                rgba = preview.convert("RGBA")
                width, height = rgba.size
                image = QImage(
                    rgba.tobytes(), width, height, width * 4,
                    QImage.Format.Format_RGBA8888,
                ).copy()
                rgba.close()
            self.loaded.emit(self.path, image)
        except Exception as exc:
            self.failed.emit(self.path, str(exc))


class ImagesToPdfWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, inputs: list[str], output: str, overwrite: bool) -> None:
        super().__init__()
        self.inputs = inputs
        self.output = output
        self.overwrite = overwrite

    def run(self) -> None:
        try:
            saved = images_to_pdf(self.inputs, self.output, dpi=DEFAULT_DPI, overwrite=self.overwrite)
            self.succeeded.emit(str(saved))
        except PDFOperationError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Could not convert the images to PDF: {exc}")


class ImagesToPdfPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(16)

        heading = QLabel("Images to PDF")
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        description = QLabel(
            "Select images, arrange their order, and combine them into one PDF. Each image becomes a page without cropping."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(description)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.setAccessibleName("Images in PDF page order")
        self.file_list.setMinimumHeight(220)
        self.file_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.file_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.file_list.setMovement(QListWidget.Movement.Static)
        self.file_list.setWrapping(True)
        self.file_list.setIconSize(QSize(160, 120))
        self.file_list.setGridSize(QSize(190, 170))
        layout.addWidget(self.file_list, 1)

        controls = QHBoxLayout()
        self.add_button = QPushButton("Add Images…")
        self.remove_button = QPushButton("Remove Selected")
        self.up_button = QPushButton("Move Up")
        self.down_button = QPushButton("Move Down")
        self.add_button.clicked.connect(self.add_images)
        self.remove_button.clicked.connect(self.remove_selected)
        self.up_button.clicked.connect(self.move_selected_up)
        self.down_button.clicked.connect(self.move_selected_down)
        for button in (self.add_button, self.remove_button, self.up_button, self.down_button):
            controls.addWidget(button)
        controls.addStretch()
        layout.addLayout(controls)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Save PDF to"))
        self.output_input = QLineEdit()
        self.output_input.setReadOnly(True)
        self.output_input.setPlaceholderText("Choose an output PDF filename and folder…")
        self.output_input.setAccessibleName("Images-to-PDF output path")
        output_row.addWidget(self.output_input, 1)
        self.output_button = QPushButton("Choose Output…")
        self.output_button.clicked.connect(self.choose_output)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.convert_button = QPushButton("Convert Images to PDF")
        self.convert_button.setMinimumHeight(48)
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button, alignment=Qt.AlignmentFlag.AlignRight)

        self._worker: ImagesToPdfWorker | None = None
        self._thumbnail_workers: dict[str, ImageThumbnailWorker] = {}

    def add_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select images", "",
            "Images (*.jpg *.jpeg *.jfif *.png *.bmp *.gif *.tif *.tiff *.webp);;All files (*.*)",
        )
        existing = {
            str(Path(self.file_list.item(i).data(Qt.ItemDataRole.UserRole)).resolve())
            for i in range(self.file_list.count())
        }
        self.add_image_paths(files, existing)

    def add_image_paths(self, files: list[str], existing: set[str] | None = None) -> None:
        """Add image tiles immediately, then fill each tile with its preview."""
        if existing is None:
            existing = {
                str(Path(self.file_list.item(i).data(Qt.ItemDataRole.UserRole)).resolve())
                for i in range(self.file_list.count())
            }
        for file_path in files:
            normalized = str(Path(file_path).resolve())
            if normalized not in existing:
                item = QListWidgetItem(Path(normalized).name)
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
                item.setData(Qt.ItemDataRole.UserRole, normalized)
                item.setToolTip(normalized)
                self.file_list.addItem(item)
                existing.add(normalized)
                worker = ImageThumbnailWorker(normalized)
                worker.loaded.connect(self._thumbnail_loaded)
                worker.failed.connect(self._thumbnail_failed)
                worker.finished.connect(lambda path=normalized: self._thumbnail_finished(path))
                self._thumbnail_workers[normalized] = worker
                worker.start()

    def _find_item(self, path: str) -> QListWidgetItem | None:
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == path:
                return item
        return None

    def _thumbnail_loaded(self, path: str, image: QImage) -> None:
        item = self._find_item(path)
        if item is not None:
            item.setIcon(QIcon(QPixmap.fromImage(image)))

    def _thumbnail_failed(self, path: str, error: str) -> None:
        item = self._find_item(path)
        if item is not None:
            item.setToolTip(f"{path}\nPreview unavailable: {error}")

    def _thumbnail_finished(self, path: str) -> None:
        self._thumbnail_workers.pop(path, None)

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
        suggestion = "images.pdf"
        if self.file_list.count():
            source = Path(self.file_list.item(0).data(Qt.ItemDataRole.UserRole))
            suggestion = str(source.with_name(f"{source.stem}.pdf"))
        output, _ = QFileDialog.getSaveFileName(
            self, "Save images as PDF", suggestion, "PDF documents (*.pdf)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if output:
            if Path(output).suffix.casefold() != ".pdf":
                output += ".pdf"
            self.output_input.setText(str(Path(output).absolute()))

    def start_conversion(self) -> None:
        inputs = [str(self.file_list.item(i).data(Qt.ItemDataRole.UserRole))
                  for i in range(self.file_list.count())]
        if not inputs:
            QMessageBox.warning(self, "Select images", "Add at least one image first.")
            return
        if not self.output_input.text().strip():
            QMessageBox.warning(self, "Choose output", "Choose where to save the PDF first.")
            return
        try:
            output = validate_pdf_output_path(self.output_input.text(), inputs, overwrite=True)
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
        self._set_busy(True)
        self._worker = ImagesToPdfWorker(inputs, str(output), overwrite)
        self._worker.succeeded.connect(self._success)
        self._worker.failed.connect(self._failure)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _success(self, output: str) -> None:
        QMessageBox.information(self, "Conversion complete", f"The PDF was saved to:\n{output}")

    def _failure(self, message: str) -> None:
        QMessageBox.critical(self, "Image conversion failed", message)

    def _set_busy(self, busy: bool) -> None:
        for button in (self.add_button, self.remove_button, self.up_button, self.down_button,
                       self.output_button, self.convert_button):
            button.setEnabled(not busy)
        self.file_list.setEnabled(not busy)
        self.progress.setVisible(busy)
        if not busy:
            self._worker = None
