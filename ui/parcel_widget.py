from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QListWidget, QPushButton, QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate
from database.connection import get_product_from_xpertpharm
from utils.printer_utils import generate_parcel_pdf, print_pdf
import tempfile
import os

class ParcelWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.items_to_print = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Scan Input
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Scan Produit:"))
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Scan Code Barre...")
        self.scan_input.returnPressed.connect(self.handle_scan)
        top_layout.addWidget(self.scan_input)
        layout.addLayout(top_layout)

        # List of items to print
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Vider la liste")
        clear_btn.clicked.connect(self.clear_list)
        btn_layout.addWidget(clear_btn)
        
        print_btn = QPushButton("Imprimer")
        print_btn.clicked.connect(self.print_labels)
        btn_layout.addWidget(print_btn)
        
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def handle_scan(self):
        barcode = self.scan_input.text().strip()
        if not barcode:
            return

        # Fetch product details (from XpertPharm as per requirement "récupérer les données du produits")
        # "la saisie d'un code à barre... permet d'ajouter le produit à la liste d'impression"
        product_data = get_product_from_xpertpharm(barcode)
        
        if not product_data:
            QMessageBox.warning(self, "Erreur", "Produit non trouvé.")
            return

        item = {
            'designation': product_data['designation'],
            'expiry_date': str(product_data['expiry_date']),
            'barcode': barcode,
            'print_date': QDate.currentDate().toString("yyyy-MM-dd")
        }
        
        self.items_to_print.append(item)
        
        # Add to UI List
        display_text = f"{item['designation']} - {item['expiry_date']} - {item['barcode']}"
        self.list_widget.addItem(display_text)
        
        self.scan_input.clear()

    def clear_list(self):
        self.items_to_print = []
        self.list_widget.clear()

    def print_labels(self):
        if not self.items_to_print:
            return

        try:
            # Create temp file
            fd, path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            
            generate_parcel_pdf(self.items_to_print, path)
            
            # Print
            print_pdf(path)
            
            # Optional: Clear list after print?
            # self.clear_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'impression: {e}")
