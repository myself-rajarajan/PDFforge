import pytest
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
import sys

# Ensure a QApplication exists for widget testing if needed
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

def test_imports():
    """Test that core modules can be imported."""
    try:
        import src.app
        import src.core
        import src.ui
        import src.utils
    except ImportError as e:
        pytest.fail(f"Module import failed: {e}")

def test_app_initialization(qapp):
    """Test that the main application window can be initialized."""
    from PySide6.QtWidgets import QApplication
    from src.app import PDFForgeApp
    from src.ui.theme import Theme
    window = PDFForgeApp()
    assert window.windowTitle() == "PDFForge"
    assert window.minimumSize().width() == 1000
    assert window.minimumSize().height() == 650
    assert QApplication.font().family() == Theme._font_family

def test_font_selection_falls_back_without_google_sans():
    from src.ui.theme import Theme
    assert Theme.choose_font_family(["Arial"], google_sans_loaded=False) == "Arial"
    assert Theme.choose_font_family([], google_sans_loaded=False, system_default="System UI") == "System UI"

def test_font_selection_prefers_google_sans_when_available():
    from src.ui.theme import Theme
    assert Theme.choose_font_family(["Google Sans", "Segoe UI"]) == "Google Sans"

def test_font_initialization_survives_missing_resource(qapp, monkeypatch, tmp_path):
    from PySide6.QtGui import QFontDatabase
    from src.ui.theme import Theme
    previous_family = Theme._font_family
    previous_font = qapp.font()
    monkeypatch.setattr(Theme, "_font_family", None)
    monkeypatch.setattr(Theme, "font_resource_path", classmethod(lambda cls: tmp_path / "missing.ttf"))
    monkeypatch.setattr(QFontDatabase, "families", staticmethod(lambda: ["Arial"]))
    try:
        assert Theme.initialize_app(qapp) == "Arial"
        assert qapp.font().family() == "Arial"
    finally:
        Theme._font_family = previous_family
        qapp.setFont(previous_font)

def test_navigation_and_tool_pages(qapp):
    from src.app import PDFForgeApp
    from src.utils.constants import TOOLS
    window = PDFForgeApp()
    assert len(TOOLS) == 8
    for key in ("all_tools", "recent", "about", *(tool["key"] for tool in TOOLS)):
        window.navigate(key)
        assert window.sidebar.buttons[[b.property("key") for b in window.sidebar.buttons].index(key)].property("active")
    assert window.stack.count() == 12

def test_search_filters_tool_cards(qapp):
    from src.ui.pages.all_tools import AllToolsPage
    page = AllToolsPage()
    page.search_input.setText("compress")
    assert sum(not card.isHidden() for card in page.cards) == 1
    assert page.no_results_label.isHidden()
    page.search_input.setText("not a tool")
    assert all(card.isHidden() for card in page.cards)
    assert not page.no_results_label.isHidden()

def test_recent_and_about_pages(qapp):
    from src.app import PDFForgeApp
    window = PDFForgeApp()
    from PySide6.QtWidgets import QLabel
    recent = window._pages["recent"]
    assert any("No file history is stored yet" in label.text() for label in recent.findChildren(QLabel))
    assert window._pages["about"] is not None

def test_toolbar_search_opens_filtered_tool_directory(qapp):
    from src.app import PDFForgeApp
    window = PDFForgeApp()
    window.search_input.setText("compress")
    assert window.stack.currentWidget() is window.all_tools
    assert sum(not card.isHidden() for card in window.all_tools.cards) == 1
