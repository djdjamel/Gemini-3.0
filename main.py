import sys
from PyQt6.QtWidgets import QApplication, QDialog, QSplashScreen
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from database.connection import init_db
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('comtypes').setLevel(logging.WARNING) # Suppress comtypes INFO logs
logger = logging.getLogger(__name__)

def main():
    # Start UI
    app = QApplication(sys.argv)
    
    # Single Instance Check
    from PyQt6.QtCore import QLockFile, QDir
    from PyQt6.QtWidgets import QMessageBox
    
    lock_file = QLockFile("gravity.lock")
    if not lock_file.tryLock(100):
        print("Lock failed! Another instance is running.")
        QMessageBox.critical(None, "Erreur", "L'application est déjà en cours d'exécution.")
        sys.exit(1)
    print(f"Lock acquired on {lock_file.fileName()}")
    
    # Apply Modern Stylesheet
    from ui.styles import get_stylesheet
    app.setStyleSheet(get_stylesheet())

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

    # Check Server Mode Configuration (First Run)
    from server_config import is_server_mode, ask_server_mode
    if is_server_mode() is None:
        # First run - ask user to configure server/client mode
        splash.showMessage("Configuration initiale...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
        app.processEvents()
        
        # Show configuration dialog
        is_server = ask_server_mode()
        
        if is_server:
            splash.showMessage("Mode SERVEUR configuré. Initialisation de la base de données...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
        else:
            splash.showMessage("Mode CLIENT configuré. Connexion à la base de données...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
        
        app.processEvents()

    # Initialize Database
    logger.info("Initializing database...")
    init_db()

    # Start Product Cache Loader
    from database.cache import ProductCache
    ProductCache.instance().load_cache()
    
    splash.showMessage("Démarrage de l'interface...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
    app.processEvents()
    
    # Start Main Window directly (Default to Agent)
    window = MainWindow(splash)
    window.show()
    splash.finish(window)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
