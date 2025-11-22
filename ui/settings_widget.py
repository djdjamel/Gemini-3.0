from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QGroupBox, QFormLayout
)
import os

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()

        # SQL Server Settings
        sql_group = QGroupBox("XpertPharm (SQL Server)")
        sql_layout = QFormLayout()
        
        self.sql_server = QLineEdit()
        sql_layout.addRow("Server:", self.sql_server)
        
        self.sql_db = QLineEdit()
        sql_layout.addRow("Database:", self.sql_db)
        
        self.sql_user = QLineEdit()
        sql_layout.addRow("User:", self.sql_user)
        
        self.sql_pass = QLineEdit()
        self.sql_pass.setEchoMode(QLineEdit.EchoMode.Password)
        sql_layout.addRow("Password:", self.sql_pass)
        
        sql_group.setLayout(sql_layout)
        layout.addWidget(sql_group)

        # PostgreSQL Settings
        pg_group = QGroupBox("Local Database (PostgreSQL)")
        pg_layout = QFormLayout()
        
        self.pg_host = QLineEdit()
        pg_layout.addRow("Host:", self.pg_host)
        
        self.pg_port = QLineEdit()
        pg_layout.addRow("Port:", self.pg_port)
        
        self.pg_db = QLineEdit()
        pg_layout.addRow("Database:", self.pg_db)
        
        self.pg_user = QLineEdit()
        pg_layout.addRow("User:", self.pg_user)
        
        self.pg_pass = QLineEdit()
        self.pg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        pg_layout.addRow("Password:", self.pg_pass)
        
        pg_group.setLayout(pg_layout)
        layout.addWidget(pg_group)

        # Save Button
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()
        self.setLayout(layout)

    def load_settings(self):
        # Load from env vars or config file?
        # Since we are using .env, we should read it.
        # But .env is static.
        # Ideally, we should have a persistent config file (ini/json) in user profile.
        # For now, let's just populate with what's in os.environ (loaded by dotenv)
        
        self.sql_server.setText(os.getenv("SQL_SERVER", ""))
        self.sql_db.setText(os.getenv("SQL_DB", ""))
        self.sql_user.setText(os.getenv("SQL_USER", ""))
        self.sql_pass.setText(os.getenv("SQL_PASSWORD", ""))
        
        self.pg_host.setText(os.getenv("PG_HOST", "localhost"))
        self.pg_port.setText(os.getenv("PG_PORT", "5432"))
        self.pg_db.setText(os.getenv("PG_DB", "gravity_stock"))
        self.pg_user.setText(os.getenv("PG_USER", "postgres"))
        self.pg_pass.setText(os.getenv("PG_PASSWORD", ""))

    def save_settings(self):
        # Write to .env file
        env_content = f"""
PG_HOST={self.pg_host.text()}
PG_PORT={self.pg_port.text()}
PG_DB={self.pg_db.text()}
PG_USER={self.pg_user.text()}
PG_PASSWORD={self.pg_pass.text()}

SQL_SERVER={self.sql_server.text()}
SQL_DB={self.sql_db.text()}
SQL_USER={self.sql_user.text()}
SQL_PASSWORD={self.sql_pass.text()}
"""
        try:
            with open(".env", "w") as f:
                f.write(env_content.strip())
            
            QMessageBox.information(self, "Succès", "Paramètres enregistrés. Veuillez redémarrer l'application.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {e}")
