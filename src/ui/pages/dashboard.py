from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QScrollArea, QGridLayout, QPushButton
from PySide6.QtCore import Qt, Signal
from src.ui.theme import Theme
from src.ui.tool_card import ToolCard
from src.utils.constants import TOOLS

class DashboardPage(QWidget):
    """Home dashboard page for PDFForge."""

    tool_clicked = Signal(str)
    explore_clicked = Signal()

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Scroll area for the dashboard content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(40)

        # Featured Panel
        featured_panel = QWidget()
        featured_panel.setStyleSheet(f"background-color: {Theme.PANEL_BG}; border-radius: 12px;")
        featured_panel.setFixedHeight(220)
        featured_layout = QVBoxLayout(featured_panel)
        featured_layout.setContentsMargins(30, 30, 30, 30)

        featured_title = QLabel("Your PDF Workspace")
        featured_title.setStyleSheet("font-size: 32px; font-weight: bold;")

        featured_sub = QLabel("Everything you need to manage PDFs, right on your Windows PC.")
        featured_sub.setStyleSheet(f"font-size: 16px; color: {Theme.TEXT_SECONDARY};")

        explore_btn = QPushButton("Explore Tools")
        explore_btn.setFixedWidth(150)
        explore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        explore_btn.clicked.connect(self.explore_clicked.emit)

        featured_layout.addWidget(featured_title)
        featured_layout.addWidget(featured_sub)
        featured_layout.addStretch()
        featured_layout.addWidget(explore_btn)

        scroll_layout.addWidget(featured_panel)

        # Quick Access Section
        qa_label = QLabel("QUICK ACCESS")
        qa_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        scroll_layout.addWidget(qa_label)

        qa_grid = QGridLayout()
        qa_grid.setSpacing(20)

        quick_tools = [t for t in TOOLS if t["quick_access"]]
        for i, tool in enumerate(quick_tools):
            card = ToolCard(tool["title"], tool["description"], tool["key"], tool["is_implemented"])
            card.clicked.connect(self.tool_clicked.emit)
            qa_grid.addWidget(card, 0, i)

        scroll_layout.addLayout(qa_grid)

        # All Tools Section (Mini Grid)
        all_label = QLabel("ALL TOOLS")
        all_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        scroll_layout.addWidget(all_label)

        tools_grid = QGridLayout()
        tools_grid.setSpacing(20)

        for i, tool in enumerate(TOOLS):
            row = i // 3
            col = i % 3
            card = ToolCard(tool["title"], tool["description"], tool["key"], tool["is_implemented"])
            card.clicked.connect(self.tool_clicked.emit)
            tools_grid.addWidget(card, row, col)

        scroll_layout.addLayout(tools_grid)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
