from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QHBoxLayout, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPalette
import pyttsx3

class NotificationOverlay(QWidget):
    responded = pyqtSignal(int, str) # notification_id, action (confirmed/rejected)

    def __init__(self, notification_data, parent=None):
        super().__init__(parent)
        self.notification_data = notification_data
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Style based on urgency
        self.is_urgent = notification_data.get('is_urgent', False)
        self.bg_color = "#ffebee" if self.is_urgent else "#e3f2fd" # Red or Blue
        self.border_color = "#d32f2f" if self.is_urgent else "#1976d2"
        
        self.init_ui()
        self.speak()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Main Container
        container = QWidget()
        container.setStyleSheet(f"""
            background-color: {self.bg_color};
            border: 2px solid {self.border_color};
            border-radius: 10px;
            padding: 10px;
        """)
        layout.addWidget(container)
        
        c_layout = QVBoxLayout(container)
        
        # Header
        header = QLabel("URGENT - DEMANDE PRODUIT" if self.is_urgent else "DEMANDE PRODUIT")
        header.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {self.border_color};")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(header)
        
        # Content
        prod_label = QLabel(f"Produit: {self.notification_data.get('product_name')}")
        prod_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        prod_label.setWordWrap(True)
        c_layout.addWidget(prod_label)
        
        qty_label = QLabel(f"Quantité: {self.notification_data.get('quantity')}")
        c_layout.addWidget(qty_label)
        
        msg_label = QLabel(f"Message: {self.notification_data.get('message')}")
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("font-style: italic;")
        c_layout.addWidget(msg_label)
        
        sender_label = QLabel(f"De: {self.notification_data.get('sender_station')}")
        sender_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        c_layout.addWidget(sender_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        confirm_btn = QPushButton("Confirmer")
        confirm_btn.setStyleSheet("background-color: #4caf50; color: white; padding: 5px;")
        confirm_btn.clicked.connect(self.confirm)
        btn_layout.addWidget(confirm_btn)
        
        reject_btn = QPushButton("Rejeter")
        reject_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        reject_btn.clicked.connect(self.reject)
        btn_layout.addWidget(reject_btn)
        
        c_layout.addLayout(btn_layout)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)

    def speak(self):
        try:
            engine = pyttsx3.init()
            text = f"Demande {'urgente' if self.is_urgent else ''} de {self.notification_data.get('sender_station')}. Produit: {self.notification_data.get('product_name')}. Quantité: {self.notification_data.get('quantity')}."
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

    def confirm(self):
        self.responded.emit(self.notification_data['id'], 'confirmed')
        self.close()

    def reject(self):
        self.responded.emit(self.notification_data['id'], 'rejected')
        self.close()
