from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QTextEdit, QCheckBox, QDialogButtonBox, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt

class RequestDialog(QDialog):
    def __init__(self, product_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Demande de Produit")
        self.setFixedWidth(400)
        self.product_name = product_name
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Product Name (Static)
        layout.addWidget(QLabel(f"Produit: <b>{self.product_name}</b>"))

        # Quantity
        layout.addWidget(QLabel("Quantité:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setValue(1)
        layout.addWidget(self.qty_spin)

        # Message
        layout.addWidget(QLabel("Message:"))
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Message pour le serveur...")
        self.message_edit.setFixedHeight(80)
        layout.addWidget(self.message_edit)

        # Urgent
        self.urgent_check = QCheckBox("Urgent")
        self.urgent_check.setChecked(True)
        layout.addWidget(self.urgent_check)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Envoyer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self):
        return {
            "quantity": self.qty_spin.value(),
            "message": self.message_edit.toPlainText(),
            "is_urgent": self.urgent_check.isChecked()
        }
