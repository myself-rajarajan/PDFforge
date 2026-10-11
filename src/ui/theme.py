"""Theme and style constants for PDFForge."""

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

    # Stylesheets
    GLOBAL_STYLE = f"""
        QMainWindow {{
            background-color: {MAIN_BG};
            color: {TEXT_PRIMARY};
        }}

        QWidget {{
            color: {TEXT_PRIMARY};
            font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
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
