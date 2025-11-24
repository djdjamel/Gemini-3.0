from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QStyle
)
from PyQt6.QtCore import Qt
from database.connection import get_db, get_product_from_xpertpharm, get_lots_by_product_code
from database.models import MissingItem
from datetime import datetime

class MissingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_items()

    def init_ui(self):
        layout = QVBoxLayout()

        # Input
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Code Produit:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Code Produit ou Scan...")
        self.code_input.returnPressed.connect(self.add_item)
        top_layout.addWidget(self.code_input)
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(self.add_item)
        top_layout.addWidget(add_btn)
        
        layout.addLayout(top_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Code", "Désignation", "Date Signalement", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.itemSelectionChanged.connect(self.load_lots_for_selected)
        layout.addWidget(self.table)
        
        # Lots Table
        layout.addWidget(QLabel("Lots disponibles (XpertPharm):"))
        self.lots_table = QTableWidget()
        self.lots_table.setColumnCount(4)
        self.lots_table.setHorizontalHeaderLabels(["Code Barre", "Quantité", "Date Péremption", "Date Achat"])
        self.lots_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lots_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.lots_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.lots_table)

        self.setLayout(layout)

    def add_item(self):
        code = self.code_input.text().strip()
        if not code:
            return

        # Try to get designation from XpertPharm if possible, otherwise just use code
        # Requirement says "quand un produit est épuisé... mentionné... par son code et date"
        # It doesn't explicitly say we need to fetch name, but it's better UX.
        # However, we might not have a barcode, just a product code?
        # Let's assume input is barcode or code.
        
        # If it's a barcode, we can fetch details.
        designation = "Inconnu"
        # Try fetching by barcode first
        prod_data = get_product_from_xpertpharm(code)
        if prod_data:
            designation = prod_data['designation']
            code = prod_data['CODE_PRODUIT'] # Use actual product code
        
        db = next(get_db())
        new_item = MissingItem(
            product_code=code,
            designation=designation,
            reported_at=datetime.now()
        )
        
        try:
            db.add(new_item)
            db.commit()
            self.load_items()
            self.code_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur: {e}")

    def load_items(self):
        self.table.setRowCount(0)
        db = next(get_db())
        items = db.query(MissingItem).order_by(MissingItem.reported_at.desc()).all()
        
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item.product_code))
            self.table.setItem(row, 1, QTableWidgetItem(item.designation))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.reported_at)))
            
            btn = QPushButton()
            btn.setObjectName("TableActionBtn")
            btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            btn.setToolTip("Supprimer")
            btn.clicked.connect(lambda checked, i_id=item.id: self.delete_item(i_id))
            
            # Center the button
            widget = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(0,0,0,0)
            layout.addWidget(btn)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            widget.setLayout(layout)
            
            self.table.setCellWidget(row, 3, widget)

    def delete_item(self, item_id):
        db = next(get_db())
        item = db.query(MissingItem).filter(MissingItem.id == item_id).first()
        if item:
            db.delete(item)
            db.commit()
            self.load_items()

    def load_lots_for_selected(self):
        self.lots_table.setRowCount(0)
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
            
        # Assuming single row selection, get the first item (row)
        row = selected_items[0].row()
        code_item = self.table.item(row, 0)
        if not code_item:
            return
            
        product_code = code_item.text()
        lots = get_lots_by_product_code(product_code)
        
        self.lots_table.setRowCount(len(lots))
        for r, lot in enumerate(lots):
            self.lots_table.setItem(r, 0, QTableWidgetItem(str(lot.get('CODE_BARRE_LOT', ''))))
            self.lots_table.setItem(r, 1, QTableWidgetItem(str(lot.get('QUANTITE', ''))))
            
            # Format Date as MM/YY
            date_exp = lot.get('DATE_PEREMPTION')
            date_str = ""
            if date_exp:
                try:
                    # Assuming date_exp is a datetime object or string
                    if isinstance(date_exp, str):
                         # Try parsing if string
                         pass 
                    else:
                         date_str = date_exp.strftime('%m/%y')
                except:
                    date_str = str(date_exp)
            
            self.lots_table.setItem(r, 2, QTableWidgetItem(date_str))
            self.lots_table.setItem(r, 3, QTableWidgetItem(str(lot.get('DATE_ACHAT', ''))))
