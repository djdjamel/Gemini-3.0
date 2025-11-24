from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton, QSplitter,
    QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database.connection import get_latest_invoices, get_invoice_details, get_db
from database.models import Product, Location
import logging

logger = logging.getLogger(__name__)

class BackgroundDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Check if item has a background color set
        bg_brush = index.data(Qt.ItemDataRole.BackgroundRole)
        if bg_brush and not (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(option.rect, bg_brush)
        
        super().paint(painter, option, index)

class InvoiceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_invoices()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top Bar: Refresh Button
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Dernières Factures (20)"))
        refresh_btn = QPushButton("Rafraîchir")
        refresh_btn.clicked.connect(self.load_invoices)
        top_layout.addWidget(refresh_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Splitter for Invoices and Details
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Invoices Table
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(3)
        self.invoices_table.setHorizontalHeaderLabels(["Date Saisie", "Fournisseur", "Total TTC"])
        self.invoices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.invoices_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.invoices_table.itemSelectionChanged.connect(self.on_invoice_selected)
        splitter.addWidget(self.invoices_table)

        # Details Table
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        details_layout.addWidget(QLabel("Détails de la facture:"))
        
        self.details_table = QTableWidget()
        self.details_table.setColumnCount(3)
        self.details_table.setHorizontalHeaderLabels(["Produit", "Quantité", "Exp (MM/YY)"])
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.details_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.details_table.setItemDelegate(BackgroundDelegate(self.details_table))
        details_layout.addWidget(self.details_table)
        
        details_widget.setLayout(details_layout)
        splitter.addWidget(details_widget)

        layout.addWidget(splitter)
        self.setLayout(layout)

    def load_invoices(self):
        self.invoices_table.setRowCount(0)
        self.details_table.setRowCount(0)
        
        invoices = get_latest_invoices()
        self.invoices_table.setRowCount(len(invoices))
        
        for row, inv in enumerate(invoices):
            # Date Saisie (CREATED_ON)
            date_str = str(inv.get('CREATED_ON', ''))
            self.invoices_table.setItem(row, 0, QTableWidgetItem(date_str))
            
            # Fournisseur (NOM_TIERS)
            self.invoices_table.setItem(row, 1, QTableWidgetItem(str(inv.get('NOM_TIERS', ''))))
            
            # Total (TOTAL_TTC)
            total = inv.get('TOTAL_TTC', 0)
            self.invoices_table.setItem(row, 2, QTableWidgetItem(f"{total:.2f}"))
            
            # Store CODE_DOC for details
            self.invoices_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, inv.get('CODE_DOC'))

    def on_invoice_selected(self):
        selected_items = self.invoices_table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        code_doc = self.invoices_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        if code_doc:
            self.load_details(code_doc)

    def load_details(self, code_doc):
        self.details_table.setRowCount(0)
        details = get_invoice_details(code_doc)
        
        self.details_table.setRowCount(len(details))
        
        # Pre-fetch local products to check existence
        # We need to check by barcode (CODE_BARRE_LOT)
        barcodes = [d.get('CODE_BARRE_LOT') for d in details if d.get('CODE_BARRE_LOT')]
        existing_barcodes = set()
        
        if barcodes:
            # Clean barcodes (strip whitespace)
            barcodes = [str(b).strip() for b in barcodes]
            
            db = next(get_db())
            if db:
                # Query Product table where barcode is in the list
                products = db.query(Product.barcode).filter(Product.barcode.in_(barcodes)).all()
                existing_barcodes = {p.barcode for p in products}
        
        for row, item in enumerate(details):
            # Produit (DESIGNATION_PRODUIT)
            designation = str(item.get('DESIGNATION_PRODUIT', ''))
            self.details_table.setItem(row, 0, QTableWidgetItem(designation))
            
            # Quantité (QUANTITE)
            qty = str(item.get('QUANTITE', ''))
            self.details_table.setItem(row, 1, QTableWidgetItem(qty))
            
            # Exp (MM/YY)
            date_exp = item.get('DATE_PEREMPTION')
            date_str = ""
            if date_exp:
                try:
                    if not isinstance(date_exp, str):
                         date_str = date_exp.strftime('%m/%y')
                    else:
                         date_str = str(date_exp)
                except:
                    date_str = str(date_exp)
            self.details_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Check if product exists locally
            barcode = str(item.get('CODE_BARRE_LOT', '')).strip()
            if barcode and barcode not in existing_barcodes:
                # Highlight row in red
                for col in range(3):
                    cell = self.details_table.item(row, col)
                    cell.setBackground(QColor("#ffebee")) # Light Red
                    cell.setToolTip("Produit non trouvé dans l'emplacement local")
