"""Main window and page navigation for PDFForge."""

from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QStackedWidget,
    QVBoxLayout, QWidget,
)

from src.ui.pages.all_tools import AllToolsPage
from src.ui.pages.dashboard import DashboardPage
from src.ui.sidebar import Sidebar
from src.ui.theme import Theme
from src.utils.constants import TOOLS


class InfoPage(QWidget):
    """Simple native page for recent files, about, and planned tools."""

    def __init__(self, title: str, description: str, status: str = "") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.setSpacing(16)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(heading)
        body = QLabel(description)
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size: 15px; color: {Theme.TEXT_SECONDARY};")
        layout.addWidget(body)
        if status:
            badge = QLabel(status)
            badge.setStyleSheet(f"color: {Theme.ACCENT_BLUE}; font-weight: 700; padding-top: 12px;")
            layout.addWidget(badge)
        layout.addStretch()


class PDFForgeApp(QMainWindow):
    """Native PDFForge desktop application window."""

    TITLES = {
        "home": "Home", "all_tools": "All Tools", "recent": "Recent Files",
        "about": "About PDFForge",
    }

    def __init__(self) -> None:
        app = QApplication.instance()
        if app is not None:
            Theme.initialize_app(app)
        super().__init__()
        self.setWindowTitle("PDFForge")
        self.setMinimumSize(1000, 650)
        self.resize(1400, 850)
        self._pages: dict[str, QWidget] = {}

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.sidebar = Sidebar()
        root_layout.addWidget(self.sidebar)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        toolbar = QFrame()
        toolbar.setObjectName("Toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(28, 14, 28, 14)
        self.page_title = QLabel("Home")
        self.page_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        toolbar_layout.addWidget(self.page_title)
        toolbar_layout.addStretch()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search PDF tools...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMaximumWidth(360)
        toolbar_layout.addWidget(self.search_input)
        online = QLabel("●  LOCAL & OFFLINE")
        online.setStyleSheet(f"color: {Theme.ACCENT_BLUE}; font-size: 11px; font-weight: 700; margin-left: 20px;")
        toolbar_layout.addWidget(online)
        body_layout.addWidget(toolbar)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack, 1)
        root_layout.addWidget(body, 1)
        self.setCentralWidget(root)

        self.dashboard = DashboardPage()
        self.all_tools = AllToolsPage()
        self._register_page("home", self.dashboard)
        self._register_page("all_tools", self.all_tools)
        self._register_page("recent", InfoPage(
            "Recent Files",
            "Recently processed documents will appear here once PDF processing features are implemented. No file history is stored yet.",
        ))
        self._register_page("about", InfoPage(
            "About PDFForge",
            "PDFForge is a Windows desktop PDF utility designed for local, offline PDF operations. The project is under development; some planned tools are not yet available.",
            "VERSION 0.1.0 • UNDER DEVELOPMENT",
        ))
        for tool in TOOLS:
            self._register_page(tool["key"], InfoPage(
                tool["title"], tool["description"], "COMING SOON",
            ))

        self.sidebar.nav_clicked.connect(self.navigate)
        self.dashboard.tool_clicked.connect(self.navigate)
        self.dashboard.explore_clicked.connect(lambda: self.navigate("all_tools"))
        self.all_tools.tool_clicked.connect(self.navigate)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.navigate("home")

    def _register_page(self, key: str, page: QWidget) -> None:
        self._pages[key] = page
        self.stack.addWidget(page)

    def navigate(self, key: str) -> None:
        """Show the requested page and synchronize navigation state."""
        page = self._pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(key)
        self.page_title.setText(self.TITLES.get(key, next(
            (tool["title"] for tool in TOOLS if tool["key"] == key), "PDFForge"
        )))
        self.search_input.setVisible(key in ("home", "all_tools"))
        if key != "all_tools" and self.search_input.text():
            self.search_input.clear()

    def _on_search_changed(self, query: str) -> None:
        self.all_tools.set_search_query(query)
        if query and self.stack.currentWidget() is not self.all_tools:
            self.navigate("all_tools")
