from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QEvent
from src.ui.theme import Theme

class ToolCard(QFrame):
    """A clickable card representing a PDF tool."""

    clicked = Signal(str) # Emits the tool key

    def __init__(self, title, description, key, is_implemented=False):
        super().__init__()
        self.setObjectName("ToolCard")
        self.setStyleSheet(Theme.CARD_STYLE)
        self.key = key
        self.title = title
        self.description = description
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Header with title and status
        header_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ToolTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        if not is_implemented:
            status_label = QLabel("COMING SOON")
            status_label.setObjectName("ToolStatus")
            header_layout.addWidget(status_label)

        layout.addLayout(header_layout)

        # Description
        self.desc_label = QLabel(description)
        self.desc_label.setObjectName("ToolDesc")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)
