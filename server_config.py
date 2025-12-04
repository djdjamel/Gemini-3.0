"""
Server Configuration Manager
Handles server/client mode detection and storage
"""
import json
import os
from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

CONFIG_FILE = 'server_config.json'

def is_server_mode():
    """
    Check if this PC is configured as server mode
    Returns:
        bool: True if server mode, False if client mode
        None: If not configured yet (first run)
    """
    if not os.path.exists(CONFIG_FILE):
        return None  # Not configured yet
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('is_server', False)
    except Exception:
        return None

def save_server_mode(is_server):
    """
    Save server mode configuration
    Args:
        is_server (bool): True for server mode, False for client mode
    """
    config = {'is_server': is_server}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

class ServerModeDialog(QDialog):
    """Dialog to ask user if this PC is server or client"""
    
    def __init__(self):
        super().__init__()
        self.is_server = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Configuration Initiale - Gravity Stock Manager")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("⚙️ Configuration du Type de Poste")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Ce PC sera-t-il utilisé comme <b>serveur</b> ou <b>client</b> ?<br><br>"
            "<b>📌 SERVEUR :</b><br>"
            "• Héberge la base de données PostgreSQL<br>"
            "• Crée les tables et importe les emplacements<br>"
            "• Un seul PC serveur par installation<br><br>"
            "<b>💻 CLIENT :</b><br>"
            "• Se connecte à la base de données du serveur<br>"
            "• Ne crée pas de tables<br>"
            "• Plusieurs PC clients peuvent se connecter<br><br>"
            "<i>⚠️ Cette configuration ne peut être changée qu'en supprimant le fichier 'server_config.json'</i>"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 10pt; padding: 15px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(desc)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        server_btn = QPushButton("🖥️ Serveur")
        server_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        server_btn.clicked.connect(self.select_server)
        btn_layout.addWidget(server_btn)
        
        client_btn = QPushButton("💻 Client")
        client_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        client_btn.clicked.connect(self.select_client)
        btn_layout.addWidget(client_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def select_server(self):
        self.is_server = True
        self.accept()
    
    def select_client(self):
        self.is_server = False
        self.accept()

def ask_server_mode():
    """
    Show dialog to ask user if this PC is server or client
    Returns:
        bool: True for server, False for client
    """
    dialog = ServerModeDialog()
    dialog.exec()
    
    if dialog.is_server is None:
        # User closed dialog without selecting, default to client for safety
        return False
    
    # Save the configuration
    save_server_mode(dialog.is_server)
    
    return dialog.is_server
