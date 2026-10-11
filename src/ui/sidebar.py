"""Compact native navigation with a restrained animated active marker."""

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QLabel, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from src.ui.theme import Theme


class Sidebar(QWidget):
    """Scrollable tool navigation that adapts to the available window width."""

    nav_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self.setStyleSheet(Theme.SIDEBAR_STYLE)
        self.setMinimumWidth(170)
        self.setMaximumWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 14, 8, 14)
        self.layout.setSpacing(8)

        self.logo_label = QLabel("PDFFORGE")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {Theme.ACCENT_BLUE}; padding: 8px 0 12px;"
        )
        self.layout.addWidget(self.logo_label)

        self.nav_scroll = QScrollArea()
        self.nav_scroll.setObjectName("NavScroll")
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.nav_content = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_content)
        self.nav_layout.setContentsMargins(0, 2, 0, 6)
        self.nav_layout.setSpacing(2)
        self.nav_scroll.setWidget(self.nav_content)
        self.layout.addWidget(self.nav_scroll, 1)

        self._add_nav_group("MAIN NAVIGATION")
        self.home_btn = self._add_nav_item("Home", "home")
        self.all_tools_btn = self._add_nav_item("All Tools", "all_tools")
        self.recent_btn = self._add_nav_item("Recent Files", "recent")
        self.nav_layout.addSpacing(12)
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
        self.nav_layout.addStretch(1)

        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(0, 4, 0, 0)
        footer_layout.setSpacing(4)
        self.about_btn = self._make_nav_item("About PDFForge", "about")
        self.about_btn.clicked.connect(lambda: self._on_btn_clicked(self.about_btn))
        footer_layout.addWidget(self.about_btn)
        self.version_label = QLabel("v0.1.0-alpha")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 10px;")
        footer_layout.addWidget(self.version_label)
        self.layout.addWidget(footer)

        self.buttons = [
            self.home_btn, self.all_tools_btn, self.recent_btn, self.merge_btn,
            self.compress_btn, self.convert_btn, self.pdf_images_btn, self.unlock_btn,
            self.protect_btn, self.remove_btn, self.reorder_btn, self.number_btn,
            self.about_btn,
        ]
        self._indicator = QFrame(self.nav_content)
        self._indicator.setObjectName("ActiveNavIndicator")
        self._indicator.setStyleSheet(
            f"QFrame#ActiveNavIndicator {{ background: {Theme.ACCENT_BLUE}; border-radius: 2px; }}"
        )
        self._indicator.setFixedWidth(3)
        self._indicator.hide()
        self._indicator_animation: QPropertyAnimation | None = None
        self._active_key = "home"
        self.set_active("home", animate=False)

    def _add_nav_group(self, title: str) -> None:
        label = QLabel(title)
        label.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            "letter-spacing: 0.8px; margin: 7px 10px 3px;"
        )
        self.nav_layout.addWidget(label)

    def _make_nav_item(self, text: str, key: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("NavButton")
        button.setProperty("key", key)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(38)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.clicked.connect(lambda: self._on_btn_clicked(button))
        return button

    def _add_nav_item(self, text: str, key: str) -> QPushButton:
        button = self._make_nav_item(text, key)
        self.nav_layout.addWidget(button)
        return button

    def set_adaptive_width(self, window_width: int) -> None:
        self.setFixedWidth(max(170, min(240, round(window_width * 0.19))))

    def _on_btn_clicked(self, button: QPushButton) -> None:
        key = str(button.property("key"))
        self.set_active(key)
        self.nav_clicked.emit(key)

    def set_active(self, key: str, *, animate: bool = True) -> None:
        """Update selection and move the slim indicator to the active tool."""
        button = next((item for item in self.buttons if item.property("key") == key), None)
        if button is None:
            return
        for item in self.buttons:
            active = item is button
            item.setProperty("active", active)
            item.style().unpolish(item)
            item.style().polish(item)
        self._active_key = key
        if self._indicator_animation is not None:
            self._indicator_animation.stop()
            self._indicator_animation.deleteLater()
            self._indicator_animation = None
        if button.parentWidget() is not self.nav_content:
            self._indicator.hide()
            return
        target = button.geometry().adjusted(0, 1, 0, -1)
        target.moveLeft(0)
        self._indicator.show()
        self._indicator.raise_()
        if (animate and Theme.animations_enabled() and self._indicator.isVisible()
                and self._indicator.geometry().isValid()):
            animation = QPropertyAnimation(self._indicator, b"geometry", self)
            animation.setDuration(145)
            animation.setStartValue(self._indicator.geometry())
            animation.setEndValue(target)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._indicator_animation = animation
            animation.start()
        else:
            self._indicator.setGeometry(target)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._active_key:
            button = next((item for item in self.buttons if item.property("key") == self._active_key), None)
            if (button is not None and button.parentWidget() is self.nav_content
                    and (self._indicator_animation is None or not self._indicator_animation.state())):
                self._indicator.setGeometry(button.geometry().adjusted(0, 1, 0, -1))
                self._indicator.setGeometry(0, self._indicator.y(), 3, button.height() - 2)

    def closeEvent(self, event) -> None:
        if self._indicator_animation is not None:
            self._indicator_animation.stop()
        super().closeEvent(event)
