"""Native GUI for best-effort local PDF compression."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QSlider,
    QVBoxLayout, QWidget,
)

from src.core.compress_pdf import (
    COMPRESSION_PRESETS, DEFAULT_IMAGE_QUALITY, IMAGE_DPI_THRESHOLD,
    MAX_IMAGE_QUALITY, MIN_IMAGE_QUALITY, compress_pdf,
    compression_preset_for_quality, compression_result_text,
    estimate_compressed_size, format_file_size, target_dpi_for_quality,
)
from src.core.pdf_output import PDFOperationError, validate_pdf_output_path
from src.ui.theme import Theme


class CompressPdfWorker(QThread):
    """Compress a PDF away from the GUI thread and report actual file sizes."""

    succeeded = Signal(str, int, int, str)
    failed = Signal(str)

    def __init__(
        self, source: str, output: str, quality: int, preset: str, overwrite: bool,
    ) -> None:
        super().__init__()
        self.source = source
        self.output = output
        self.quality = quality
        self.preset = preset
        self.overwrite = overwrite

    def run(self) -> None:
        try:
            original_size = Path(self.source).stat().st_size
            saved = compress_pdf(
                self.source, self.output, quality=self.quality,
                preset=self.preset if self.preset in COMPRESSION_PRESETS else None,
                overwrite=self.overwrite,
            )
            output_size = saved.stat().st_size
            summary = (
                f"Preset: {self.preset}\n"
                f"{compression_result_text(original_size, output_size)}"
            )
            self.succeeded.emit(str(saved), original_size, output_size, summary)
        except PDFOperationError as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("An unexpected error occurred while compressing the PDF.")


class CompressionEstimateWorker(QThread):
    """Measure the selected compression setting off the GUI thread."""

    estimated = Signal(str, int, int)
    failed = Signal(str, int, str)

    def __init__(self, source: str, quality: int) -> None:
        super().__init__()
        self.source = source
        self.quality = quality

    def run(self) -> None:
        try:
            size = estimate_compressed_size(self.source, quality=self.quality)
            self.estimated.emit(self.source, self.quality, size)
        except PDFOperationError as exc:
            self.failed.emit(self.source, self.quality, str(exc))
        except Exception:
            self.failed.emit(self.source, self.quality, "Could not estimate this PDF's output size.")


class CompressPdfPage(QWidget):
    """Select a source and destination and show actual compression results."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(18)

        heading = QLabel("Compress PDF")
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        description = QLabel(
            "Reduce PDF file size where practical. High-resolution images may be downsampled and recompressed; "
            "this can reduce image detail, and some PDFs may stay the same size or become larger."
        )
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(description)

        self.quality_value_label = QLabel()
        self.quality_value_label.setAccessibleName("Selected image compression quality")
        layout.addWidget(self.quality_value_label)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems((*COMPRESSION_PRESETS, "Custom"))
        self.preset_combo.setAccessibleName("PDF compression preset")
        layout.addWidget(self.preset_combo)
        self.preset_description = QLabel()
        self.preset_description.setWordWrap(True)
        self.preset_description.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(self.preset_description)
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(MIN_IMAGE_QUALITY, MAX_IMAGE_QUALITY)
        self.quality_slider.setValue(DEFAULT_IMAGE_QUALITY)
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(15)
        self.quality_slider.setAccessibleName("Image compression quality")
        self.quality_slider.valueChanged.connect(self._quality_changed)
        self.quality_slider.valueChanged.connect(self._schedule_size_estimate)
        self.preset_combo.currentIndexChanged.connect(self._preset_changed)
        layout.addWidget(self.quality_slider)
        quality_legend = QHBoxLayout()
        quality_legend.addWidget(QLabel("Smaller size • lower image quality"))
        quality_legend.addStretch()
        quality_legend.addWidget(QLabel("Higher image quality • larger size"))
        layout.addLayout(quality_legend)
        self.estimate_label = QLabel("Choose a PDF to estimate its compressed size.")
        self.estimate_label.setWordWrap(True)
        self.estimate_label.setAccessibleName("Estimated compressed PDF file size")
        layout.addWidget(self.estimate_label)

        input_row = QHBoxLayout()
        self.open_button = QPushButton("Open PDF…")
        self.open_button.clicked.connect(self.choose_input)
        input_row.addWidget(self.open_button)
        self.file_info = QLabel("No PDF selected")
        self.file_info.setWordWrap(True)
        self.file_info.setAccessibleName("Selected PDF filename and original file size")
        input_row.addWidget(self.file_info, 1)
        layout.addLayout(input_row)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Save compressed PDF to"))
        self.output_label = QLabel("Choose a new filename and location…")
        self.output_label.setWordWrap(True)
        self.output_label.setAccessibleName("Compressed PDF output path")
        output_row.addWidget(self.output_label, 1)
        self.output_button = QPushButton("Choose Output…")
        self.output_button.setEnabled(False)
        self.output_button.clicked.connect(self.choose_output)
        output_row.addWidget(self.output_button)
        layout.addLayout(output_row)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setAccessibleName("PDF compression size report")
        layout.addWidget(self.result_label)

        action_row = QHBoxLayout()
        action_row.addStretch()
        self.compress_button = QPushButton("Compress PDF")
        self.compress_button.setMinimumHeight(48)
        self.compress_button.setEnabled(False)
        self.compress_button.clicked.connect(self.start_compression)
        action_row.addWidget(self.compress_button)
        layout.addLayout(action_row)
        layout.addStretch()

        self.input_path: str | None = None
        self.output_path: str | None = None
        self._worker: CompressPdfWorker | None = None
        self._estimate_worker: CompressionEstimateWorker | None = None
        self._estimate_pending = False
        self._estimate_timer = QTimer(self)
        self._estimate_timer.setSingleShot(True)
        self._estimate_timer.setInterval(450)
        self._estimate_timer.timeout.connect(self._start_size_estimate)
        self._quality_changed(self.quality_slider.value())

    def _quality_changed(self, quality: int) -> None:
        target_dpi = target_dpi_for_quality(quality)
        profile = compression_preset_for_quality(quality)
        preset_name = profile if profile in COMPRESSION_PRESETS else "Custom"
        if self.preset_combo.currentText() != preset_name:
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText(preset_name)
            self.preset_combo.blockSignals(False)
        self.preset_description.setText(
            COMPRESSION_PRESETS[preset_name].description if preset_name in COMPRESSION_PRESETS
            else "Custom quality. High-resolution raster images may be recompressed; searchable text and vector content are retained."
        )
        self.quality_value_label.setText(
            f"Image quality: {quality}% • images above {IMAGE_DPI_THRESHOLD} DPI target {target_dpi} DPI"
        )

    def _preset_changed(self, _index: int) -> None:
        preset = self.preset_combo.currentText()
        settings = COMPRESSION_PRESETS.get(preset)
        if settings is not None:
            self.quality_slider.setValue(settings.quality)
            self._quality_changed(settings.quality)

    def _schedule_size_estimate(self, _quality: int) -> None:
        if self.input_path is None:
            self.estimate_label.setText("Choose a PDF to estimate its compressed size.")
            return
        self.estimate_label.setText("Updating estimated output size…")
        self._estimate_timer.start()

    def _start_size_estimate(self) -> None:
        if not self.input_path:
            return
        if self._estimate_worker is not None:
            self._estimate_pending = True
            return
        source = self.input_path
        quality = self.quality_slider.value()
        self.compress_button.setEnabled(False)
        preset = compression_preset_for_quality(quality)
        self.estimate_label.setText(f"Estimating {preset} output size at {quality}% quality…")
        self._estimate_worker = CompressionEstimateWorker(source, quality)
        self._estimate_worker.estimated.connect(self._size_estimated)
        self._estimate_worker.failed.connect(self._size_estimate_failed)
        self._estimate_worker.finished.connect(self._estimate_finished)
        self._estimate_worker.start()

    def _size_estimated(self, source: str, quality: int, size: int) -> None:
        if source != self.input_path or quality != self.quality_slider.value():
            return
        try:
            original_size = Path(source).stat().st_size
        except OSError:
            original_size = 0
        preset = compression_preset_for_quality(quality)
        summary = compression_result_text(original_size, size)
        self.estimate_label.setText(
            f"Estimated {preset} output at {quality}% quality: {format_file_size(size)} — {summary} "
            "(measured using a temporary compression pass)."
        )

    def _size_estimate_failed(self, source: str, quality: int, message: str) -> None:
        if source == self.input_path and quality == self.quality_slider.value():
            self.estimate_label.setText(f"Size estimate unavailable: {message}")

    def _estimate_finished(self) -> None:
        self._estimate_worker = None
        if self._estimate_pending:
            self._estimate_pending = False
            self._start_size_estimate()
        else:
            self.compress_button.setEnabled(bool(self.input_path and self.output_path))

    def choose_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF documents (*.pdf)")
        if not path:
            return
        self.input_path = str(Path(path).absolute())
        self.output_path = None
        try:
            size = Path(path).stat().st_size
            self.file_info.setText(f"{Path(path).name} — {format_file_size(size)}")
        except OSError:
            self.file_info.setText(Path(path).name)
        self.output_label.setText("Choose a new filename and location…")
        self.result_label.clear()
        self.output_button.setEnabled(True)
        self._update_enabled()
        self._estimate_timer.start(0)

    def choose_output(self) -> None:
        if not self.input_path:
            return
        source = Path(self.input_path)
        suggestion = str(source.with_name(f"{source.stem}_compressed.pdf"))
        output, _ = QFileDialog.getSaveFileName(
            self, "Save compressed PDF", suggestion, "PDF documents (*.pdf)",
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if output:
            if Path(output).suffix.casefold() != ".pdf":
                output += ".pdf"
            self.output_path = str(Path(output).absolute())
            self.output_label.setText(self.output_path)
            self._update_enabled()

    def _update_enabled(self) -> None:
        self.compress_button.setEnabled(bool(self.input_path and self.output_path))

    def start_compression(self) -> None:
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
        self._estimate_timer.stop()
        quality = self.quality_slider.value()
        preset = compression_preset_for_quality(quality)
        self.compress_button.setText("Compressing PDF…")
        self.result_label.setText("Optimizing the PDF locally…")
        self._worker = CompressPdfWorker(self.input_path, str(output), quality, preset, overwrite)
        self._worker.succeeded.connect(self._compression_succeeded)
        self._worker.failed.connect(self._compression_failed)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _compression_succeeded(self, output: str, original_size: int, output_size: int, summary: str) -> None:
        details = (
            f"Original size: {format_file_size(original_size)}\n"
            f"Compressed size: {format_file_size(output_size)}\n{summary}"
        )
        self.result_label.setText(details)
        QMessageBox.information(
            self, "Compression complete", f"{details}\n\nSaved to:\n{output}"
        )

    def _compression_failed(self, message: str) -> None:
        self.result_label.clear()
        QMessageBox.critical(self, "Could not compress PDF", message)

    def _worker_finished(self) -> None:
        self.compress_button.setText("Compress PDF")
        self._set_controls_enabled(True)
        self._worker = None

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.open_button.setEnabled(enabled)
        self.output_button.setEnabled(enabled and self.input_path is not None)
        self.quality_slider.setEnabled(enabled)
        self.compress_button.setEnabled(enabled and self.input_path is not None and self.output_path is not None)
