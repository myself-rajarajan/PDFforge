from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal
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
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(f"{title}. {description}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumSize(0, 132)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(17, 16, 17, 16)
        layout.setSpacing(8)

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

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit(self.key)
            event.accept()
            return
        super().keyPressEvent(event)
