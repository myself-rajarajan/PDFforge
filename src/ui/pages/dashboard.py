"""Responsive home dashboard with keyboard-accessible tool cards."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, QPushButton,
)

from src.ui.theme import Theme
from src.ui.tool_card import ToolCard
from src.utils.constants import TOOLS


class DashboardPage(QWidget):
    """Home dashboard page for PDFForge."""

    tool_clicked = Signal(str)
    explore_clicked = Signal()

    def __init__(self):
        super().__init__()
        self._quick_cards: list[ToolCard] = []
        self._all_cards: list[ToolCard] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(22)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(2, 3, 6, 6)
        scroll_layout.setSpacing(24)

        featured_panel = QWidget()
        featured_panel.setObjectName("SurfaceCard")
        featured_panel.setMinimumHeight(198)
        featured_layout = QVBoxLayout(featured_panel)
        featured_layout.setContentsMargins(26, 24, 26, 22)
        featured_layout.setSpacing(10)
        featured_title = QLabel("Your PDF Workspace")
        featured_title.setStyleSheet("font-size: 30px; font-weight: 700;")
        featured_sub = QLabel("Everything you need to manage PDFs, right on your Windows PC.")
        featured_sub.setWordWrap(True)
        featured_sub.setStyleSheet(f"font-size: 15px; color: {Theme.TEXT_SECONDARY};")
        explore_btn = QPushButton("Explore Tools")
        explore_btn.setMaximumWidth(170)
        explore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        explore_btn.clicked.connect(self.explore_clicked.emit)
        featured_layout.addWidget(featured_title)
        featured_layout.addWidget(featured_sub)
        featured_layout.addStretch()
        featured_layout.addWidget(explore_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        scroll_layout.addWidget(featured_panel)

        scroll_layout.addWidget(self._section_label("QUICK ACCESS"))
        self.quick_grid = QGridLayout()
        self.quick_grid.setSpacing(14)
        for tool in (item for item in TOOLS if item["quick_access"]):
            card = self._create_card(tool)
            self._quick_cards.append(card)
        scroll_layout.addLayout(self.quick_grid)

        scroll_layout.addWidget(self._section_label("ALL TOOLS"))
        self.all_grid = QGridLayout()
        self.all_grid.setSpacing(14)
        for tool in TOOLS:
            self._all_cards.append(self._create_card(tool))
        scroll_layout.addLayout(self.all_grid)
        scroll_layout.addStretch()
        self._reflow_cards()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )
        return label

    def _create_card(self, tool: dict) -> ToolCard:
        card = ToolCard(tool["title"], tool["description"], tool["key"], tool["is_implemented"])
        card.clicked.connect(self.tool_clicked.emit)
        return card

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reflow_cards()

    def _reflow_cards(self) -> None:
        """Reflow cards between compact and wide layouts as the page is resized."""
        if not hasattr(self, "quick_grid"):
            return
        available = max(300, self.width() - 62)
        for cards, grid, max_columns in (
            (self._quick_cards, self.quick_grid, 4),
            (self._all_cards, self.all_grid, 3),
        ):
            columns = max(1, min(max_columns, (available + 14) // 250))
            while grid.count():
                grid.takeAt(0)
            for index, card in enumerate(cards):
                grid.addWidget(card, index // columns, index % columns)
            for column in range(max_columns):
                grid.setColumnStretch(column, int(column < columns))
