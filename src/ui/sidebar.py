from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt, Signal
from src.ui.theme import Theme

class Sidebar(QWidget):
    """Left navigation sidebar for PDFForge."""

    nav_clicked = Signal(str) # Emits the page key

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setStyleSheet(Theme.SIDEBAR_STYLE)
        self.setFixedWidth(240)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 20, 0, 20)
        self.layout.setSpacing(0)

        # Logo section
        self.logo_label = QLabel("PDFFORGE")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.ACCENT_BLUE}; padding-bottom: 20px;")
        self.layout.addWidget(self.logo_label)

        # Navigation groups
        self._add_nav_group("MAIN NAVIGATION")
        self.home_btn = self._add_nav_item("Home", "home")
        self.all_tools_btn = self._add_nav_item("All Tools", "all_tools")
        self.recent_btn = self._add_nav_item("Recent Files", "recent")

        self.layout.addSpacing(20)

        self._add_nav_group("PDF TOOLS")
        self.merge_btn = self._add_nav_item("Merge PDF", "tool_merge")
        self.compress_btn = self._add_nav_item("Compress PDF", "tool_compress")
        self.convert_btn = self._add_nav_item("Images to PDF", "tool_convert")
        self.pdf_images_btn = self._add_nav_item("PDF to Images", "tool_pdf_to_images")
        self.unlock_btn = self._add_nav_item("Unlock PDF", "tool_unlock")
        self.protect_btn = self._add_nav_item("Protect PDF", "tool_protect")
        self.remove_btn = self._add_nav_item("Remove Pages", "tool_remove")
        self.reorder_btn = self._add_nav_item("Reorder Pages", "tool_reorder")
        self.number_btn = self._add_nav_item("Add Page Numbers", "tool_numbers")

        self.layout.addStretch()

        # Footer
        self.about_btn = self._add_nav_item("About PDFForge", "about")
        self.version_label = QLabel("v0.1.0-alpha")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; margin-top: 5px;")
        self.layout.addWidget(self.version_label)

        self.buttons = [
            self.home_btn, self.all_tools_btn, self.recent_btn,
            self.merge_btn, self.compress_btn, self.convert_btn, self.pdf_images_btn,
            self.unlock_btn, self.protect_btn, self.remove_btn,
            self.reorder_btn, self.number_btn, self.about_btn
        ]

        # Default active
        self.set_active("home")

    def _add_nav_group(self, title):
        label = QLabel(title)
        label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 10px; font-weight: bold; margin-left: 20px; margin-bottom: 5px;")
        self.layout.addWidget(label)

    def _add_nav_item(self, text, key):
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setProperty("key", key)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_btn_clicked(btn))
        self.layout.addWidget(btn)
        return btn

    def _on_btn_clicked(self, btn):
        key = btn.property("key")
        self.set_active(key)
        self.nav_clicked.emit(key)

    def set_active(self, key):
        """Update the active button visually."""
        for btn in self.buttons:
            is_active = btn.property("key") == key
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
