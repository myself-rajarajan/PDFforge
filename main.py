import sys
from PySide6.QtWidgets import QApplication
from src.app import PDFForgeApp
from src.ui.theme import Theme

def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("PDFForge")
    Theme.initialize_app(app)
    
    window = PDFForgeApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
