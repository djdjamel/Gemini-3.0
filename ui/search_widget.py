from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QDialog, QComboBox, QDialogButtonBox, QStyle
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
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Designation
        for i in [0, 1, 3, 4, 5]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def on_search_text_changed(self):
        self.search_timer.start(500)

    def perform_search(self):
        query_text = self.search_input.text().strip()
        self.table.setRowCount(0)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QDialog, QComboBox, QDialogButtonBox, QStyle
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor # Added QColor import
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
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Designation
        for i in [0, 1, 3, 4, 5]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(48)
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
        # 1. Local Search (Inventory - Stock Lines)
        stock_lines = db.query(Product).options(joinedload(Product.location)).filter(Product.designation.ilike(f"%{query_text}%")).all()
        
        # 2. Local Search (Distinct Products - Catalog View)
        # We want to find unique products matching the description to allow adding to "Missing"
        # distinct() on code/designation
        distinct_products = db.query(Product.code, Product.designation, Product.barcode).filter(Product.designation.ilike(f"%{query_text}%")).distinct(Product.code).all()
        
        total_rows = len(stock_lines) + len(distinct_products)
        self.table.setRowCount(total_rows)
        
        # Display Stock Lines
        for row, prod in enumerate(stock_lines):
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
            actions_layout.setSpacing(4)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            move_btn = QPushButton()
            move_btn.setObjectName("TableActionBtn")
            move_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
            move_btn.setToolTip("Déplacer")
            move_btn.clicked.connect(lambda checked, p=prod: self.move_product(p))
            actions_layout.addWidget(move_btn)
            
            del_btn = QPushButton()
            del_btn.setObjectName("TableActionBtn")
            del_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            del_btn.setToolTip("Supprimer")
            del_btn.clicked.connect(lambda checked, p_id=prod.id: self.delete_product(p_id))
            actions_layout.addWidget(del_btn)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 5, actions_widget)

        # Display Distinct Products (Catalog View)
        start_distinct = len(stock_lines)
        for i, d_prod in enumerate(distinct_products):
            row = start_distinct + i
            
            # Helper to set item with background color
            def create_colored_item(text):
                item = QTableWidgetItem(str(text or ""))
                item.setBackground(QColor("#ffebee")) # Light Red / Soft
                # Mark as catalog item
                # d_prod is a Row/Tuple (code, designation, barcode)
                data = {
                    "CODE_PRODUIT": d_prod.code,
                    "designation": d_prod.designation,
                    "barcode": d_prod.barcode
                }
                item.setData(Qt.ItemDataRole.UserRole, {"type": "catalog", "data": data})
                return item

            self.table.setItem(row, 0, create_colored_item("CATALOGUE"))
            self.table.setItem(row, 1, create_colored_item(d_prod.code))
            self.table.setItem(row, 2, create_colored_item(d_prod.designation))
            self.table.setItem(row, 3, create_colored_item(d_prod.barcode))
            self.table.setItem(row, 4, create_colored_item("")) # No expiry for generic view
            
            # Actions Widget for Catalog items
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(4)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            add_missing_btn = QPushButton()
            add_missing_btn.setObjectName("TableActionBtn")
            add_missing_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)) # Example icon
            add_missing_btn.setToolTip("Ajouter au Manquant")
            # Pass the distinct product data to the handler
            add_missing_btn.clicked.connect(lambda checked, p_data=d_prod: self.add_to_missing(p_data))
            actions_layout.addWidget(add_missing_btn)

            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 5, actions_widget)


    def add_to_missing(self, product_data):
        # product_data can be a Row (from distinct query) or Dict (from double click)
        # Handle both
        if hasattr(product_data, 'code'):
            code = product_data.code
            designation = product_data.designation
        else:
            code = product_data.get('CODE_PRODUIT')
            designation = product_data.get('designation')
        
        if not code:
            return

        db = next(get_db())
        try:
            existing = db.query(MissingItem).filter(MissingItem.product_code == code).first()
            if existing:
                existing.reported_at = datetime.now()
                msg = f"Le produit '{designation}' était déjà dans la liste des manquants. Date mise à jour."
            else:
                new_missing = MissingItem(
                    product_code=code,
                    designation=designation,
                    reported_at=datetime.now()
                )
                db.add(new_missing)
                msg = f"Le produit '{designation}' a été ajouté aux manquants."
            
            db.commit()
            QMessageBox.information(self, "Succès", msg)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout aux manquants: {e}")


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
