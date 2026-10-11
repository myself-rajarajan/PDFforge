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
    assert window._pages["tool_merge"] is window.merge_page
    assert window._pages["tool_reorder"] is window.reorder_pages_page
    assert next(tool for tool in TOOLS if tool["key"] == "tool_reorder")["is_implemented"]
    window.sidebar.merge_btn.click()
    assert window.stack.currentWidget() is window.merge_page
    window.sidebar.remove_btn.click()
    assert window.stack.currentWidget() is window.remove_pages_page

def test_reorder_thumbnail_drop_tracks_displayed_order(qapp):
    from src.ui.pages.reorder_pages import ReorderPagesPage
    page = ReorderPagesPage()
    page.input_path = "document.pdf"
    page.page_count = 3
    page.page_order = [1, 2, 3]
    for number in page.page_order:
        page.thumbnail_grid.add_page(number)
    page._page_moved(3, 1)
    assert page.page_order == [3, 1, 2]
    assert [button.page_number for button in page.thumbnail_grid.buttons] == [3, 1, 2]
    assert [button.text() for button in page.thumbnail_grid.buttons] == [
        "Position 1 • Page 3", "Position 2 • Page 1", "Position 3 • Page 2",
    ]
    page._page_moved(99, 1)
    assert page.page_order == [3, 1, 2]
    page._page_moved(3, 2, True)
    assert page.page_order == [1, 2, 3]
    assert [button.page_number for button in page.thumbnail_grid.buttons] == [1, 2, 3]

def test_merge_page_can_reorder_and_remove_files(qapp):
    from PySide6.QtWidgets import QListWidgetItem
    from src.ui.pages.merge_pdf import MergePDFPage
    page = MergePDFPage()
    for name in ("first.pdf", "second.pdf", "third.pdf"):
        page.file_list.addItem(QListWidgetItem(name))
    page.file_list.item(1).setSelected(True)
    page.move_selected_down()
    assert [page.file_list.item(i).text() for i in range(3)] == [
        "first.pdf", "third.pdf", "second.pdf",
    ]
    page.file_list.item(2).setSelected(True)
    page.move_selected_up()
    assert [page.file_list.item(i).text() for i in range(3)] == [
        "first.pdf", "second.pdf", "third.pdf",
    ]
    page.file_list.item(1).setSelected(True)
    page.remove_selected()
    assert [page.file_list.item(i).text() for i in range(page.file_list.count())] == [
        "first.pdf", "third.pdf",
    ]

def test_remove_pages_preview_updates_and_blocks_empty_result(qapp):
    from src.ui.pages.remove_pages import RemovePagesPage
    page = RemovePagesPage()
    page.input_path = "document.pdf"
    page.page_count = 6
    page.selection_input.setEnabled(True)
    page.selection_input.setText("2,4")
    assert page.remove_button.isEnabled()
    assert page.preview_removed.text() == "Pages to remove (2): 2, 4"
    assert page.preview_remaining.text() == "Pages that will remain (4): 1, 3, 5-6"
    page.selection_input.setText("1-6")
    assert not page.remove_button.isEnabled()
    assert "cannot remove every page" in page.preview_error.text()

def test_page_thumbnail_click_selects_page_for_removal(qapp):
    from src.ui.pages.remove_pages import RemovePagesPage
    page = RemovePagesPage()
    page.input_path = "document.pdf"
    page.page_count = 3
    page.selection_input.setEnabled(True)
    for number in range(1, 4):
        page._page_buttons[number] = page.thumbnail_grid.add_page(number)
    page._page_buttons[2].click()
    assert page.selection_input.text() == "2"
    assert page._page_buttons[2].isChecked()
    assert "Pages to remove (1): 2" == page.preview_removed.text()

def test_pdf_preview_worker_renders_page_images(qapp, tmp_path):
    from PySide6.QtTest import QSignalSpy
    from pypdf import PdfWriter
    from src.ui.pdf_preview import PdfPreviewWorker
    source = tmp_path / "preview.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=160, height=240)
    writer.add_blank_page(width=240, height=160)
    with source.open("wb") as stream:
        writer.write(stream)
    writer.close()

    worker = PdfPreviewWorker(str(source))
    loaded = QSignalSpy(worker.loaded)
    thumbnails = QSignalSpy(worker.thumbnail_ready)
    worker.start()
    assert worker.wait(10000)
    qapp.processEvents()

    assert loaded.count() == 1
    assert loaded.at(0)[1] == 2
    assert thumbnails.count() == 2
    assert all(not thumbnails.at(index)[2].isNull() for index in range(thumbnails.count()))

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
