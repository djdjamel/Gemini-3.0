import sys
from PyQt6.QtWidgets import QApplication, QDialog
from ui.main_window import MainWindow
from database.connection import init_db
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Initialize Database
    logger.info("Initializing database...")
    init_db()
    
    # Start UI
    app = QApplication(sys.argv)
    
    # Apply a clean style
    app.setStyle("Fusion")
    
    # Show Login
    from ui.login_dialog import LoginDialog
    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
