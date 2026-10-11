"""Background PDF thumbnail rendering and native page preview cards."""

from pathlib import Path

from PySide6.QtCore import QThread, Signal, QSize, Qt, QPoint
from PySide6.QtGui import QImage, QIcon, QPixmap, QDrag, QMouseEvent
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
            page_numbers = (
                list(range(1, page_count + 1))
                if self.page_numbers is None else self.page_numbers
            )
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
    page_dropped = Signal(int, int, bool)

    def __init__(
        self,
        page_number: int,
        *,
        draggable: bool = False,
        selectable: bool = True,
        icon_size: QSize | None = None,
        button_size: QSize | None = None,
    ) -> None:
        super().__init__()
        self.page_number = page_number
        self.draggable = draggable
        self.selectable = selectable
        self._drag_start: QPoint | None = None
        self.setAcceptDrops(draggable)
        self.setCheckable(selectable)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setIconSize(icon_size or QSize(150, 190))
        self.setFixedSize(button_size or QSize(190, 245))
        self.setText(f"Page {page_number}")
        self.setAccessibleName(
            f"Page {page_number}, select to remove" if selectable else f"Page {page_number} preview"
        )
        self.setToolTip(
            f"Page {page_number}" if draggable or not selectable else
            f"Click to toggle page {page_number} for removal"
        )
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

    def set_position_label(self, position: int) -> None:
        self.setText(f"Position {position} • Page {self.page_number}")
        self.setAccessibleName(f"Position {position}, original page {self.page_number}")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.draggable and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (self.draggable and self._drag_start is not None and
                event.buttons() & Qt.MouseButton.LeftButton and
                (event.position().toPoint() - self._drag_start).manhattanLength() >= 8):
            drag = QDrag(self)
            from PySide6.QtCore import QMimeData
            mime = QMimeData()
            mime.setText(str(self.page_number))
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)
            self._drag_start = None
            return
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event) -> None:
        if self.draggable and event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        if not self.draggable or not event.mimeData().hasText():
            event.ignore()
            return
        try:
            source_page = int(event.mimeData().text())
        except ValueError:
            event.ignore()
            return
        insert_after = event.position().toPoint().y() >= self.height() // 2
        self.page_dropped.emit(source_page, self.page_number, insert_after)
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()


class ThumbnailGrid(QWidget):
    """Responsive grid of clickable PDF page thumbnail buttons."""

    page_toggled = Signal(int, bool)
    page_dropped = Signal(int, int, bool)

    def __init__(
        self,
        *,
        draggable: bool = False,
        selectable: bool = True,
        icon_size: QSize | None = None,
        button_size: QSize | None = None,
    ) -> None:
        super().__init__()
        self.draggable = draggable
        self.selectable = selectable
        self.icon_size = icon_size or QSize(150, 190)
        self.button_size = button_size or QSize(190, 245)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(14)
        self._buttons: list[PageThumbnailButton] = []
        self._columns = 0

    @property
    def buttons(self) -> list[PageThumbnailButton]:
        return self._buttons

    def add_page(self, page_number: int) -> PageThumbnailButton:
        button = PageThumbnailButton(
            page_number,
            draggable=self.draggable,
            selectable=self.selectable,
            icon_size=self.icon_size,
            button_size=self.button_size,
        )
        button.page_toggled.connect(self.page_toggled.emit)
        button.page_dropped.connect(self.page_dropped.emit)
        index = len(self._buttons)
        self._buttons.append(button)
        columns = max(1, (self.width() - 16) // (self.button_size.width() + self._layout.spacing()))
        if columns != self._columns:
            self._reflow()
        else:
            self._layout.addWidget(button, index // columns, index % columns)
        return button

    def move_page(self, source_page: int, target_page: int, insert_after: bool = False) -> None:
        """Insert a source thumbnail before or after the target thumbnail."""
        source_index = next((i for i, button in enumerate(self._buttons)
                             if button.page_number == source_page), None)
        target_index = next((i for i, button in enumerate(self._buttons)
                             if button.page_number == target_page), None)
        if source_index is None or target_index is None or source_index == target_index:
            return
        button = self._buttons.pop(source_index)
        # Recompute after popping, since the source may have been before target.
        target_index = next(i for i, item in enumerate(self._buttons)
                            if item.page_number == target_page)
        destination = target_index + int(insert_after)
        self._buttons.insert(destination, button)
        for position, page_button in enumerate(self._buttons, 1):
            page_button.set_position_label(position)
        self._reflow(force=True)

    def set_page_order(self, page_order: list[int]) -> None:
        """Arrange currently loaded thumbnails according to original page numbers."""
        by_page = {button.page_number: button for button in self._buttons}
        self._buttons = [by_page[number] for number in page_order if number in by_page]
        for button in self._buttons:
            button.set_position_label(page_order.index(button.page_number) + 1)
        self._reflow(force=True)

    def clear_pages(self) -> None:
        for button in self._buttons:
            self._layout.removeWidget(button)
            button.deleteLater()
        self._buttons.clear()
        self._reflow()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reflow()

    def _reflow(self, *, force: bool = False) -> None:
        columns = max(1, (self.width() - 16) // (self.button_size.width() + self._layout.spacing()))
        if not force and columns == self._columns and self._layout.count() == len(self._buttons):
            return
        while self._layout.count():
            self._layout.takeAt(0)
        self._columns = columns
        for index, button in enumerate(self._buttons):
            self._layout.addWidget(button, index // columns, index % columns)
