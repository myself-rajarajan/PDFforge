"""Shared visual theme and application-wide font initialization."""

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

class Theme:
    # Color palette (Steam-inspired)
    MAIN_BG = "#171A21"
    SIDEBAR_BG = "#11151B"
    PANEL_BG = "#202833"
    CARD_BG = "#252F3B"
    CARD_HOVER_BG = "#303B47"
    ACCENT_BLUE = "#66C0F4"
    TEXT_PRIMARY = "#F1F5F9"
    TEXT_SECONDARY = "#A7B0BC"
    BORDER_COLOR = "#303B47"
    FONT_FAMILY = "Google Sans"
    FALLBACK_FAMILIES = ("Segoe UI", "Arial", "sans-serif")
    _font_family: str | None = None
    _font_id = -1

    @classmethod
    def font_resource_path(cls) -> Path:
        """Return the optional bundled font path in source and PyInstaller builds."""
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        return bundle_root / "resources" / "fonts" / "GoogleSans-Regular.ttf"

    @classmethod
    def choose_font_family(
        cls, available_families: list[str], google_sans_loaded: bool = False,
        system_default: str = "",
    ) -> str:
        """Prefer Google Sans when available, otherwise select a safe local fallback."""
        families = {family.casefold(): family for family in available_families}
        google = families.get(cls.FONT_FAMILY.casefold())
        if google_sans_loaded and google:
            return google
        if google:
            return google
        for fallback in cls.FALLBACK_FAMILIES:
            if fallback.casefold() == "sans-serif":
                continue
            if fallback.casefold() in families:
                return families[fallback.casefold()]
        if system_default:
            return system_default
        return "sans-serif"

    @classmethod
    def initialize_app(cls, app: QApplication) -> str:
        """Set one application font before widgets are constructed, with safe fallback."""
        if cls._font_family is None:
            loaded = False
            try:
                font_path = cls.font_resource_path()
                if font_path.is_file():
                    cls._font_id = QFontDatabase.addApplicationFont(str(font_path))
                    loaded = cls._font_id >= 0
            except (OSError, RuntimeError):
                loaded = False

            try:
                families = QFontDatabase.families()
            except RuntimeError:
                families = []
            cls._font_family = cls.choose_font_family(
                list(families), google_sans_loaded=loaded,
                system_default=app.font().family(),
            )
        app.setFont(QFont(cls._font_family, 10))
        app.setStyleSheet(cls.GLOBAL_STYLE)
        return cls._font_family

    # Stylesheets
    GLOBAL_STYLE = f"""
        QMainWindow {{
            background-color: {MAIN_BG};
            color: {TEXT_PRIMARY};
        }}

        QWidget {{
            color: {TEXT_PRIMARY};
            font-size: 14px;
        }}

        QLabel {{
            color: {TEXT_PRIMARY};
        }}

        QLineEdit {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER_COLOR};
            border-radius: 4px;
            padding: 8px;
            color: {TEXT_PRIMARY};
        }}

        QLineEdit:focus {{
            border: 1px solid {ACCENT_BLUE};
        }}

        QPushButton {{
            background-color: {ACCENT_BLUE};
            color: {MAIN_BG};
            border-radius: 4px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 14px;
        }}

        QPushButton:hover {{
            background-color: #77D0FF;
        }}

        QScrollArea {{
            border: none;
            background-color: transparent;
        }}

        QScrollBar:vertical {{
            border: none;
            background: {SIDEBAR_BG};
            width: 10px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {CARD_BG};
            min-height: 20px;
            border-radius: 5px;
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}
    """

    SIDEBAR_STYLE = f"""
        QWidget#Sidebar {{
            background-color: {SIDEBAR_BG};
            border-right: 1px solid {BORDER_COLOR};
        }}

        QPushButton#NavButton {{
            background-color: transparent;
            color: {TEXT_SECONDARY};
            text-align: left;
            padding: 12px 20px;
            border-radius: 0px;
            border-left: 3px solid transparent;
            font-weight: normal;
        }}

        QPushButton#NavButton:hover {{
            background-color: {PANEL_BG};
            color: {TEXT_PRIMARY};
        }}

        QPushButton#NavButton[active="true"] {{
            background-color: {PANEL_BG};
            color: {TEXT_PRIMARY};
            border-left: 3px solid {ACCENT_BLUE};
        }}
    """

    CARD_STYLE = f"""
        QFrame#ToolCard {{
            background-color: {CARD_BG};
            border-radius: 8px;
            border: 1px solid transparent;
        }}

        QFrame#ToolCard:hover {{
            background-color: {CARD_HOVER_BG};
            border: 1px solid {ACCENT_BLUE};
        }}

        QLabel#ToolTitle {{
            font-size: 16px;
            font-weight: bold;
            color: {TEXT_PRIMARY};
        }}

        QLabel#ToolDesc {{
            font-size: 13px;
            color: {TEXT_SECONDARY};
        }}

        QLabel#ToolStatus {{
            font-size: 11px;
            color: {ACCENT_BLUE};
            background-color: rgba(102, 192, 244, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
        }}
    """
