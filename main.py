import sys
from PySide6.QtWidgets import QApplication
from src.app import PDFForgeApp

def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("PDFForge")
    
    window = PDFForgeApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
