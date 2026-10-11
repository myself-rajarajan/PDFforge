"""Background PDF thumbnail rendering and native page preview cards."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, QSize, Qt
from PySide6.QtGui import QImage, QIcon, QPixmap
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QGridLayout, QToolButton, QWidget

from src.core.pdf_output import PDFOperationError
from src.ui.theme import Theme


class PdfPreviewWorker(QThread):
    """Read PDF metadata and render small page images off the GUI thread."""

    loaded = Signal(str, int)
    thumbnail_ready = Signal(str, int, QImage)
    failed = Signal(str, str)

    def __init__(self, path: str, page_numbers: list[int] | None = None) -> None:
        super().__init__()
        self.path = path
        self.page_numbers = page_numbers

    def run(self) -> None:
        document = QPdfDocument()
        try:
            document.load(self.path)
            if document.status() != QPdfDocument.Status.Ready:
                if document.error() == QPdfDocument.Error.IncorrectPassword:
                    raise PDFOperationError(
                        f"'{Path(self.path).name}' is password-protected. PDFForge will not bypass its password."
                    )
                raise PDFOperationError(
                    f"Could not open '{self.path}': {document.error()}"
                )
            page_count = document.pageCount()
            if page_count < 1:
                raise PDFOperationError("The selected PDF does not contain any pages.")
            self.loaded.emit(self.path, page_count)
            page_numbers = self.page_numbers or list(range(1, page_count + 1))
            for page_number in page_numbers:
                if page_number < 1 or page_number > page_count:
                    continue
                page_size = document.pagePointSize(page_number - 1)
                scale = min(180 / max(page_size.width(), 1), 230 / max(page_size.height(), 1))
                image_size = QSize(
                    max(1, round(page_size.width() * scale)),
                    max(1, round(page_size.height() * scale)),
                )
                image = document.render(page_number - 1, image_size)
                if image.isNull():
                    raise PDFOperationError(f"Could not render page {page_number} of '{Path(self.path).name}'.")
                self.thumbnail_ready.emit(self.path, page_number, image)
        except PDFOperationError as exc:
            self.failed.emit(self.path, str(exc))
        except Exception as exc:
            self.failed.emit(self.path, f"Could not preview '{Path(self.path).name}': {exc}")
        finally:
            document.close()


class PageThumbnailButton(QToolButton):
    """A clickable thumbnail showing whether a page is selected for removal."""

    page_toggled = Signal(int, bool)

    def __init__(self, page_number: int) -> None:
        super().__init__()
        self.page_number = page_number
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(150, 190))
        self.setFixedSize(190, 245)
        self.setText(f"Page {page_number}")
        self.setAccessibleName(f"Page {page_number}, select to remove")
        self.setToolTip(f"Click to toggle page {page_number} for removal")
        self.setStyleSheet(f"""
            QToolButton {{
                background-color: {Theme.CARD_BG};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid {Theme.BORDER_COLOR};
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }}
            QToolButton:hover {{ border: 1px solid {Theme.ACCENT_BLUE}; }}
            QToolButton:checked {{
                background-color: #3B2A31;
                border: 2px solid #F28B82;
                color: #F6C7C2;
            }}
        """)
        self.toggled.connect(lambda checked: self.page_toggled.emit(self.page_number, checked))

    def set_thumbnail(self, image: QImage) -> None:
        self.setIcon(QIcon(QPixmap.fromImage(image)))


class ThumbnailGrid(QWidget):
    """Responsive grid of clickable PDF page thumbnail buttons."""

    page_toggled = Signal(int, bool)

    def __init__(self) -> None:
        super().__init__()
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(14)
        self._buttons: list[PageThumbnailButton] = []
        self._columns = 0

    @property
    def buttons(self) -> list[PageThumbnailButton]:
        return self._buttons

    def add_page(self, page_number: int) -> PageThumbnailButton:
        button = PageThumbnailButton(page_number)
        button.page_toggled.connect(self.page_toggled.emit)
        index = len(self._buttons)
        self._buttons.append(button)
        columns = max(1, self.width() // 208)
        if columns != self._columns:
            self._reflow()
        else:
            self._layout.addWidget(button, index // columns, index % columns)
        return button

    def clear_pages(self) -> None:
        for button in self._buttons:
            self._layout.removeWidget(button)
            button.deleteLater()
        self._buttons.clear()
        self._reflow()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reflow()

    def _reflow(self) -> None:
        columns = max(1, self.width() // 208)
        if columns == self._columns and self._layout.count() == len(self._buttons):
            return
        while self._layout.count():
            self._layout.takeAt(0)
        self._columns = columns
        for index, button in enumerate(self._buttons):
            self._layout.addWidget(button, index // columns, index % columns)
