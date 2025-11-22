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
    
    # Create a simple splash pixmap
    pixmap = QPixmap(400, 200)
    pixmap.fill(QColor("white"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("black"))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Gravity Stock Manager\n\nInitialisation de la base de données...")
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
    window = MainWindow()
    window.show()
    splash.finish(window)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
