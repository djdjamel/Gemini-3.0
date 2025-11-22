from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QDialog, QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer
from database.connection import get_db
from database.models import Product, Location
from sqlalchemy.orm import joinedload
from ui.dialogs import ChangeLocationDialog
import logging

logger = logging.getLogger(__name__)

class SearchWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.interval = 500 # 500ms debounce
        self.search_timer.timeout.connect(self.perform_search)

    def init_ui(self):
        layout = QVBoxLayout()

        # Search Bar
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Rechercher Produit:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tapez le nom du produit...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        top_layout.addWidget(self.search_input)
        layout.addLayout(top_layout)

        # Results Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Emplacement", "Code", "Désignation", "Code Barre", "Date Exp", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def on_search_text_changed(self):
        self.search_timer.start(500)

    def perform_search(self):
        query_text = self.search_input.text().strip()
        self.table.setRowCount(0)
        
        if not query_text:
            return

        db = next(get_db())
        # ILIKE for case-insensitive search in Postgres, but standard SQL uses LIKE. 
        # SQLAlchemy 'ilike' covers this.
        products = db.query(Product).options(joinedload(Product.location)).filter(Product.designation.ilike(f"%{query_text}%")).all()
        
        self.table.setRowCount(len(products))
        for row, prod in enumerate(products):
            loc_label = prod.location.label if prod.location else "N/A"
            
            self.table.setItem(row, 0, QTableWidgetItem(loc_label))
            self.table.setItem(row, 1, QTableWidgetItem(str(prod.code)))
            self.table.setItem(row, 2, QTableWidgetItem(prod.designation))
            self.table.setItem(row, 3, QTableWidgetItem(prod.barcode))
            self.table.setItem(row, 4, QTableWidgetItem(str(prod.expiry_date)))
            
            # Actions Widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            move_btn = QPushButton("Déplacer")
            move_btn.clicked.connect(lambda checked, p=prod: self.move_product(p))
            actions_layout.addWidget(move_btn)
            
            del_btn = QPushButton("Supprimer")
            del_btn.clicked.connect(lambda checked, p_id=prod.id: self.delete_product(p_id))
            actions_layout.addWidget(del_btn)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 5, actions_widget)

    def delete_product(self, product_id):
        reply = QMessageBox.question(self, "Confirmer", "Voulez-vous vraiment supprimer ce produit ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db = next(get_db())
            prod = db.query(Product).filter(Product.id == product_id).first()
            if prod:
                db.delete(prod)
                db.commit()
                self.perform_search() # Refresh

    def move_product(self, product):
        dialog = ChangeLocationDialog(product.location_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_loc_id = dialog.selected_location_id
            if new_loc_id:
                db = next(get_db())
                prod_db = db.query(Product).filter(Product.id == product.id).first()
                if prod_db:
                    prod_db.location_id = new_loc_id
                    db.commit()
                    self.perform_search() # Refresh
