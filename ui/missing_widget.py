from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QStyle, QStyledItemDelegate,
    QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from database.connection import get_db, get_product_from_xpertpharm, get_lots_by_product_code
from database.models import MissingItem
from datetime import datetime

class BackgroundDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Check if item has a background color set
        bg_brush = index.data(Qt.ItemDataRole.BackgroundRole)
        if bg_brush and not (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(option.rect, bg_brush)
        
        super().paint(painter, option, index)

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
        
        delete_all_btn = QPushButton("Tout Supprimer")
        delete_all_btn.clicked.connect(self.delete_all_items)
        delete_all_btn.setStyleSheet("background-color: #ffcdd2; color: #c62828;") # Light red background, dark red text
        top_layout.addWidget(delete_all_btn)
        
        layout.addLayout(top_layout)
        
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Du:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.dateChanged.connect(self.load_items)
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("Au:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_items)
        filter_layout.addWidget(self.date_to)
        
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self.load_items)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Code", "Désignation", "Date Signalement", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.itemSelectionChanged.connect(self.load_lots_for_selected)
        
        # Set Custom Delegate for Background Coloring
        self.table.setItemDelegate(BackgroundDelegate(self.table))
        
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

        # Try to get designation from XpertPharm if possible to ensure it exists in Nomenclature?
        # Actually, we just add the code. The designation comes from Nomenclature.
        # If it's not in Nomenclature, it will show as "Inconnu" or we should ensure it's in Nomenclature.
        
        # Check if product exists in Nomenclature, if not maybe fetch from XP and add it?
        # For now, just add the MissingItem.
        
        # If input is barcode, resolve to code
        prod_data = get_product_from_xpertpharm(code)
        if prod_data:
            code = prod_data['CODE_PRODUIT']
        
        with get_db() as db:
            if not db: return
            
            new_item = MissingItem(
                product_code=code,
                source="Manquant",
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
        with get_db() as db:
            if not db: return
            
            # Date Filter
            d_from = self.date_from.date().toPyDate()
            d_to = self.date_to.date().addDays(1).toPyDate() # Include end date
            
            # Join with Nomenclature to get designation
            # We use outerjoin in case it's missing from Nomenclature
            from database.models import Nomenclature
            
            # Filter by date range and not deleted
            items = db.query(MissingItem).outerjoin(Nomenclature, MissingItem.product_code == Nomenclature.code)\
                .filter(MissingItem.reported_at >= d_from, MissingItem.reported_at < d_to)\
                .filter(MissingItem.is_deleted == False)\
                .order_by(MissingItem.reported_at.asc()).all()
            
            # Deduplicate: Keep only the latest item for each product_code
            latest_items_map = {}
            for item in items:
                latest_items_map[item.product_code] = item
            
            # Convert back to list and sort by date desc for display
            unique_items = sorted(latest_items_map.values(), key=lambda x: x.reported_at, reverse=True)
            
            self.table.setRowCount(len(unique_items))
            for row, item in enumerate(unique_items):
                designation = item.nomenclature.designation if item.nomenclature else "Inconnu"
                
                self.table.setItem(row, 0, QTableWidgetItem(item.product_code))
                self.table.setItem(row, 1, QTableWidgetItem(designation))
                self.table.setItem(row, 2, QTableWidgetItem(str(item.reported_at)))
                
                # Highlight "Comptoir" items
                if item.source == "Comptoir":
                    color = QColor("#fff9c4") # Light Yellow
                    for col in range(3):
                        self.table.item(row, col).setBackground(color)
                
                btn = QPushButton()
                btn.setObjectName("TableActionBtn")
                btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
                btn.setToolTip("Supprimer")
                # Pass product_code instead of item_id to delete all instances
                btn.clicked.connect(lambda checked, p_code=item.product_code: self.delete_item(p_code))
                
                # Center the button
                widget = QWidget()
                layout = QHBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                layout.addWidget(btn)
                layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                widget.setLayout(layout)
                
                self.table.setCellWidget(row, 3, widget)

    def delete_item(self, product_code):
        # Soft delete all active items with this product code
        with get_db() as db:
            if not db: return
            
            # Find all non-deleted items with this product code
            items = db.query(MissingItem).filter(MissingItem.product_code == product_code, MissingItem.is_deleted == False).all()
            
            if items:
                for item in items:
                    item.is_deleted = True
                
                db.commit()
                self.load_items()

    def delete_all_items(self):
        reply = QMessageBox.question(self, "Confirmer", "Voulez-vous vraiment supprimer TOUS les produits de la liste des manquants ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with get_db() as db:
                if not db: return
                try:
                    # Soft delete all
                    db.query(MissingItem).filter(MissingItem.is_deleted == False).update({MissingItem.is_deleted: True})
                    db.commit()
                    self.load_items()
                    QMessageBox.information(self, "Succès", "La liste des manquants a été vidée.")
                except Exception as e:
                    db.rollback()
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression : {e}")

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

        # Add Total Row
        if lots:
            total_qty = sum(float(lot.get('QUANTITE', 0)) for lot in lots)
            row = self.lots_table.rowCount()
            self.lots_table.insertRow(row)
            
            item_label = QTableWidgetItem("Total")
            item_label.setFont(self.get_bold_font())
            self.lots_table.setItem(row, 0, item_label)
            
            item_qty = QTableWidgetItem(str(total_qty))
            item_qty.setFont(self.get_bold_font())
            self.lots_table.setItem(row, 1, item_qty)

    def get_bold_font(self):
        font = self.font()
        font.setBold(True)
        return font
