"""Shared visual system and safe application-wide font initialization."""

import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication


class Theme:
    """PDFForge's restrained Windows-inspired dark palette and QSS."""

    MAIN_BG = "#10151C"
    SIDEBAR_BG = "#121922"
    PANEL_BG = "#18222D"
    CARD_BG = "#1D2935"
    CARD_HOVER_BG = "#243442"
    INPUT_BG = "#111A23"
    ACCENT_BLUE = "#70B7E5"
    ACCENT_HOVER = "#91CCF0"
    TEXT_PRIMARY = "#F2F6FA"
    TEXT_SECONDARY = "#A8B6C4"
    TEXT_MUTED = "#8493A2"
    BORDER_COLOR = "#2B3A49"
    FOCUS_COLOR = "#92D2F5"
    ERROR_COLOR = "#F28B82"
    SUCCESS_COLOR = "#81C995"

    FONT_FAMILY = "Google Sans"
    PREFERRED_FAMILIES = ("Google Sans", "Inter", "Roboto")
    FALLBACK_FAMILIES = ("Segoe UI", "Arial", "sans-serif")
    _font_family: str | None = None
    _font_id = -1

    @classmethod
    def font_resource_path(cls) -> Path:
        """Optional licensed application font location, including PyInstaller builds."""
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        return bundle_root / "resources" / "fonts" / "GoogleSans-Regular.ttf"

    @classmethod
    def choose_font_family(
        cls,
        available_families: list[str],
        google_sans_loaded: bool = False,
        system_default: str = "",
    ) -> str:
        families = {family.casefold(): family for family in available_families}
        google = families.get(cls.FONT_FAMILY.casefold())
        if google:
            return google
        for family in (*cls.PREFERRED_FAMILIES[1:], *cls.FALLBACK_FAMILIES):
            if family.casefold() == "sans-serif":
                continue
            if family.casefold() in families:
                return families[family.casefold()]
        return system_default or "sans-serif"

    @classmethod
    def initialize_app(cls, app: QApplication) -> str:
        """Apply a single readable font and shared styling without making startup fragile."""
        if cls._font_family is None:
            loaded = False
            try:
                path = cls.font_resource_path()
                if path.is_file():
                    cls._font_id = QFontDatabase.addApplicationFont(str(path))
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
        try:
            app.setStyleSheet(cls.GLOBAL_STYLE)
        except (RuntimeError, ValueError):
            # A visual polish failure must never prevent the native app from opening.
            app.setStyleSheet("")
        return cls._font_family

    @classmethod
    def animations_enabled(cls, app: QApplication | None = None) -> bool:
        """Honor an explicit reduced-motion preference where Qt lacks a portable API."""
        if os.environ.get("PDFFORGE_REDUCED_MOTION", "").casefold() in {"1", "true", "yes"}:
            return False
        app = app or QApplication.instance()
        if app is not None:
            hints = app.styleHints()
            preference = getattr(hints, "reducedMotionEnabled", None)
            if preference is not None:
                try:
                    return not bool(preference() if callable(preference) else preference)
                except RuntimeError:
                    pass
        return True

    GLOBAL_STYLE = f"""
        QMainWindow {{ background: {MAIN_BG}; color: {TEXT_PRIMARY}; }}
        QWidget {{ color: {TEXT_PRIMARY}; font-size: 14px; }}
        QToolTip {{ color: {TEXT_PRIMARY}; background: {PANEL_BG}; border: 1px solid {BORDER_COLOR}; padding: 6px 8px; }}
        QLabel {{ background: transparent; color: {TEXT_PRIMARY}; }}
        QLineEdit, QSpinBox, QComboBox {{
            background: {INPUT_BG}; color: {TEXT_PRIMARY};
            border: 1px solid {BORDER_COLOR}; border-radius: 8px;
            padding: 9px 11px; selection-background-color: {ACCENT_BLUE};
        }}
        QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{ border-color: #43566A; }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QListWidget:focus,
        QToolButton:focus, QPushButton:focus {{ border: 1px solid {FOCUS_COLOR}; }}
        QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ color: {TEXT_MUTED}; background: #17212B; }}
        QPushButton {{
            background: #26394A; color: {TEXT_PRIMARY};
            border: 1px solid #354A5E; border-radius: 9px;
            padding: 9px 15px; font-size: 13px; font-weight: 600;
        }}
        QPushButton:hover {{ background: #30485D; border-color: #52708A; }}
        QPushButton:pressed {{ background: #1C2D3B; }}
        QPushButton:disabled {{ background: #202A34; color: {TEXT_MUTED}; border-color: #2A3540; }}
        QScrollArea {{ border: 1px solid {BORDER_COLOR}; border-radius: 12px; background: transparent; }}
        QListWidget {{ background: {PANEL_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 12px; padding: 8px; }}
        QListWidget::item {{ background: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 9px; padding: 8px; margin: 3px; }}
        QListWidget::item:hover {{ background: {CARD_HOVER_BG}; border-color: #496176; }}
        QListWidget::item:selected {{ background: #263D50; border-color: {ACCENT_BLUE}; color: {TEXT_PRIMARY}; }}
        QProgressBar {{ background: {INPUT_BG}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_COLOR}; border-radius: 7px; text-align: center; min-height: 12px; }}
        QProgressBar::chunk {{ background: {ACCENT_BLUE}; border-radius: 6px; }}
        QSlider::groove:horizontal {{ height: 5px; background: {BORDER_COLOR}; border-radius: 2px; }}
        QSlider::sub-page:horizontal {{ background: {ACCENT_BLUE}; border-radius: 2px; }}
        QSlider::handle:horizontal {{ background: {TEXT_PRIMARY}; border: 2px solid {ACCENT_BLUE}; width: 15px; margin: -7px 0; border-radius: 8px; }}
        QComboBox::drop-down {{ border: none; width: 26px; }}
        QComboBox QAbstractItemView {{ background: {PANEL_BG}; color: {TEXT_PRIMARY}; selection-background-color: #30485D; border: 1px solid {BORDER_COLOR}; }}
        QScrollBar:vertical {{ background: transparent; width: 11px; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: #354657; min-height: 24px; border-radius: 5px; }}
        QScrollBar::handle:vertical:hover {{ background: #50677D; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 2px; }}
        QScrollBar::handle:horizontal {{ background: #354657; min-width: 24px; border-radius: 5px; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QToolButton {{ background: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; padding: 7px; }}
        QToolButton:hover {{ background: {CARD_HOVER_BG}; border-color: {ACCENT_BLUE}; }}
        QToolButton:checked {{ background: #3A2B32; border: 2px solid {ERROR_COLOR}; color: #FFDAD6; }}
        QFrame#Toolbar {{ background: {SIDEBAR_BG}; border-bottom: 1px solid {BORDER_COLOR}; }}
        QFrame#SurfaceCard {{ background: {PANEL_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 14px; }}
        QMessageBox {{ background: {PANEL_BG}; }}
    """

    SIDEBAR_STYLE = f"""
        QWidget#Sidebar {{ background: {SIDEBAR_BG}; border-right: 1px solid {BORDER_COLOR}; }}
        QScrollArea#NavScroll {{ border: none; background: transparent; }}
        QPushButton#NavButton {{
            background: transparent; color: {TEXT_SECONDARY}; text-align: left;
            border: 1px solid transparent; border-radius: 8px; padding: 10px 12px;
            margin: 1px 8px; font-weight: 500;
        }}
        QPushButton#NavButton:hover {{ background: {CARD_BG}; color: {TEXT_PRIMARY}; border-color: {BORDER_COLOR}; }}
        QPushButton#NavButton[active="true"] {{ background: #243443; color: {TEXT_PRIMARY}; border-color: #30495E; }}
        QPushButton#NavButton:focus {{ border: 1px solid {FOCUS_COLOR}; }}
    """

    CARD_STYLE = f"""
        QFrame#ToolCard {{ background: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 14px; }}
        QFrame#ToolCard:hover {{ background: {CARD_HOVER_BG}; border-color: #4A667E; }}
        QLabel#ToolTitle {{ font-size: 16px; font-weight: 650; color: {TEXT_PRIMARY}; }}
        QLabel#ToolDesc {{ font-size: 13px; color: {TEXT_SECONDARY}; }}
        QLabel#ToolStatus {{ font-size: 11px; color: {ACCENT_BLUE}; background: #223646; padding: 3px 8px; border-radius: 7px; }}
    """
