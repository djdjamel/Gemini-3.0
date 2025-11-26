from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QDialogButtonBox
from PyQt6.QtCore import Qt

class QuantityDialog(QDialog):
    def __init__(self, product_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quantité")
        self.setFixedWidth(300)
        self.init_ui(product_name)

    def init_ui(self, product_name):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(f"Produit: <b>{product_name}</b>"))
        layout.addWidget(QLabel("Saisir la quantité:"))
        
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(-9999, 9999)
        self.qty_spin.setValue(1)
        self.qty_spin.selectAll() # Select all so user can type immediately
        layout.addWidget(self.qty_spin)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)

    def get_quantity(self):
        return self.qty_spin.value()
