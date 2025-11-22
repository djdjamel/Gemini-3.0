from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Gravity Stock")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        self.setLayout(layout)
        
    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        # TODO: Implement actual authentication against DB
        if username == "admin" and password == "admin":
            self.accept()
        elif username == "agent" and password == "agent":
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials")
