from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QScrollArea, QLineEdit
from PySide6.QtCore import Qt, Signal
from src.ui.theme import Theme
from src.ui.tool_card import ToolCard
from src.utils.constants import TOOLS

class AllToolsPage(QWidget):
    """Page displaying all available PDF tools with filtering."""

    tool_clicked = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header_label = QLabel("All PDF Tools")
        header_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(header_label)

        desc_label = QLabel("Browse and select the tool you need for your PDF tasks.")
        desc_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 14px;")
        layout.addWidget(desc_label)

        # Search field (local to this page as well)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search PDF tools...")
        self.search_input.setFixedWidth(400)
        self.search_input.textChanged.connect(self._filter_tools)
        layout.addWidget(self.search_input)

        # Scroll area for the grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setContentsMargins(0, 20, 0, 0)
        self.grid_layout.setSpacing(20)

        self.cards = []
        self._populate_grid(TOOLS)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # No results message
        self.no_results_label = QLabel("No tools match your search.")
        self.no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_results_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 16px; margin-top: 50px;")
        self.no_results_label.hide()
        layout.addWidget(self.no_results_label)

    def _populate_grid(self, tools_list):
        # Clear existing
        for card in self.cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

        for i, tool in enumerate(tools_list):
            row = i // 3
            col = i % 3
            card = ToolCard(tool["title"], tool["description"], tool["key"], tool["is_implemented"])
            card.clicked.connect(self.tool_clicked.emit)
            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)

    def _filter_tools(self, query):
        query = query.lower()
        filtered_tools = [
            t for t in TOOLS
            if query in t["title"].lower() or query in t["description"].lower()
        ]

        # Show/hide cards
        for card in self.cards:
            match = query in card.title.lower() or query in card.description.lower()
            card.setVisible(match)

        self.no_results_label.setVisible(len(filtered_tools) == 0)

    def set_search_query(self, query):
        """External entry point for search from the toolbar."""
        self.search_input.setText(query)
        self._filter_tools(query)
