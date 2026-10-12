"""Home dashboard introducing PDFForge and guiding users into its tools."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, QPushButton,
)

from src.ui.theme import Theme


class DashboardPage(QWidget):
    """Home dashboard page for PDFForge."""

    tool_clicked = Signal(str)
    explore_clicked = Signal()

    def __init__(self):
        super().__init__()
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
        featured_panel.setMinimumHeight(244)
        featured_layout = QVBoxLayout(featured_panel)
        featured_layout.setContentsMargins(26, 24, 26, 22)
        featured_layout.setSpacing(8)
        project_name = QLabel("PDFForge")
        project_name.setStyleSheet(
            f"color: {Theme.ACCENT_BLUE}; font-size: 13px; font-weight: 700;"
        )
        featured_title = QLabel("Everything You Need to Manage PDFs")
        featured_title.setWordWrap(True)
        featured_title.setStyleSheet("font-size: 28px; font-weight: 700;")
        featured_sub = QLabel(
            "A desktop utility to merge documents, organize pages, convert files, protect PDFs "
            "with passwords, and reduce file sizes. Your files are processed locally on this "
            "computer; no online PDF service is required."
        )
        featured_sub.setWordWrap(True)
        featured_sub.setStyleSheet(f"font-size: 15px; color: {Theme.TEXT_SECONDARY};")
        capabilities = QLabel(
            "Merge PDFs  •  Remove and reorder pages  •  Add page numbers  •  Images to PDF "
            "and PDF pages to images  •  Protect and unlock PDFs  •  Compress PDFs"
        )
        capabilities.setObjectName("DashboardCapabilities")
        capabilities.setWordWrap(True)
        capabilities.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        explore_btn = QPushButton("Explore Tools")
        explore_btn.setMaximumWidth(170)
        explore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        explore_btn.clicked.connect(self.explore_clicked.emit)
        featured_layout.addWidget(project_name)
        featured_layout.addWidget(featured_title)
        featured_layout.addWidget(featured_sub)
        featured_layout.addWidget(capabilities)
        featured_layout.addStretch()
        featured_layout.addWidget(explore_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        scroll_layout.addWidget(featured_panel)

        workflow_panel = QWidget()
        workflow_panel.setObjectName("SurfaceCard")
        workflow_layout = QVBoxLayout(workflow_panel)
        workflow_layout.setContentsMargins(20, 16, 20, 16)
        workflow_layout.setSpacing(10)
        workflow_heading = QLabel("How it works")
        workflow_heading.setStyleSheet("font-size: 17px; font-weight: 650;")
        workflow_layout.addWidget(workflow_heading)
        workflow_steps = QHBoxLayout()
        workflow_steps.setSpacing(12)
        for number, step in enumerate((
            "Select a PDF or image", "Choose an operation", "Set available options", "Save your file",
        ), start=1):
            step_label = QLabel(f"{number}.  {step}")
            step_label.setWordWrap(True)
            step_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 13px;")
            workflow_steps.addWidget(step_label, 1)
        workflow_layout.addLayout(workflow_steps)
        scroll_layout.addWidget(workflow_panel)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
