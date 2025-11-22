import sys
from PyQt6.QtWidgets import QApplication, QDialog, QSplashScreen
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from database.connection import init_db
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Start UI
    app = QApplication(sys.argv)
    
    # Apply a clean style
    app.setStyle("Fusion")

    # Splash Screen
    from PyQt6.QtGui import QFont
    
    # Load splash image
    pixmap = QPixmap("assets/splash_background.png")
    # Resize to a good size (e.g., 800px width, maintaining aspect ratio)
    pixmap = pixmap.scaledToWidth(800, Qt.TransformationMode.SmoothTransformation)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Draw Title
    painter.setPen(QColor("white"))
    font = QFont("Arial", 36, QFont.Weight.Bold)
    painter.setFont(font)
    
    # Draw text with shadow for better visibility
    rect = pixmap.rect()
    # Move text up a bit
    text_rect = rect.adjusted(0, -50, 0, 0)
    
    # Shadow
    painter.setPen(QColor(0, 0, 0, 150))
    painter.drawText(text_rect.translated(2, 2), Qt.AlignmentFlag.AlignCenter, "Gravity Stock Manager")
    
    # Main Text
    painter.setPen(QColor("white"))
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "Gravity Stock Manager")
    
    painter.end()
    
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents() # Force update

    # Initialize Database
    logger.info("Initializing database...")
    init_db()
    
    splash.showMessage("Démarrage de l'interface...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
    app.processEvents()
    
    # Start Main Window directly (Default to Agent)
    window = MainWindow(splash)
    window.show()
    splash.finish(window)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
