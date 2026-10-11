from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

class PDFForgeApp(QMainWindow):
    """Main application window for PDFForge."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PDFForge")
        self.setMinimumSize(800, 600)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Welcome message
        welcome_label = QLabel("Welcome to PDFForge")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        subtitle_label = QLabel("Your offline-first PDF utility.")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 14px; color: gray;")
        
        layout.addStretch()
        layout.addWidget(welcome_label)
        layout.addWidget(subtitle_label)
        layout.addStretch()
