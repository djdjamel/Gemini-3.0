from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QAbstractItemView, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QStyle
from database.connection import get_db, get_product_from_xpertpharm
from database.models import Location, Product
from utils.barcode_utils import is_location_barcode, parse_location_barcode
from ui.dialogs import ChangeLocationDialog
from sqlalchemy.orm import Session
import logging
import pyttsx3

logger = logging.getLogger(__name__)

class TTSThread(QThread):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        try:
            engine = pyttsx3.init()
            engine.say(self.text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS Error: {e}")

class InventoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_location = None
        self.init_ui()
        self.load_locations()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top Bar: Location Selection and Scanning
        top_layout = QHBoxLayout()
        
        top_layout.addWidget(QLabel("Emplacement:"))
        self.location_combo = QComboBox()
        self.location_combo.setEditable(False)
        self.location_combo.currentIndexChanged.connect(self.on_location_changed)
        top_layout.addWidget(self.location_combo)
        
        top_layout.addWidget(QLabel("Scan:"))
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Scan Location or Product Barcode")
        self.scan_input.returnPressed.connect(self.handle_scan)
        top_layout.addWidget(self.scan_input)
        
        layout.addLayout(top_layout)

        # Product Table
        self.table = QTableWidget()
        # Removed 'Code' column, now 4 columns
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Désignation", "Date Exp", "Code Barre", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        # Make table read-only
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)

        self.setLayout(layout)

    def speak(self, text):
        self.tts_thread = TTSThread(text)
        self.tts_thread.start()

    def show_error(self, title, message):
        self.speak(message)
        QMessageBox.warning(self, title, message)

    def load_locations(self):
        self.location_combo.blockSignals(True)
        self.location_combo.clear()
        db = next(get_db())
        if db:
            locations = db.query(Location).order_by(Location.label).all()
            for loc in locations:
                self.location_combo.addItem(loc.label, loc.id)
        self.location_combo.blockSignals(False)
        
        # Select first item by default
        if self.location_combo.count() > 0:
            self.location_combo.setCurrentIndex(0)
            self.on_location_changed()

    def on_location_changed(self):
        location_id = self.location_combo.currentData()
        if location_id:
            db = next(get_db())
            self.current_location = db.query(Location).filter(Location.id == location_id).first()
            self.load_products()
            self.scan_input.setFocus()

    def handle_scan(self):
        barcode = self.scan_input.text().strip()
        if not barcode:
            return

        if is_location_barcode(barcode):
            self.process_location_scan(barcode)
        else:
            self.process_product_scan(barcode)
        
        self.scan_input.clear()

    def process_location_scan(self, barcode):
        # Requirement: "si le code barre saisie / scanné commence par 000 et a une longueur de texte de 7, on lance une requete de recherche dans la table locations si on le trouve pas on lance un message d'erreur"
        
        db = next(get_db())
        location = db.query(Location).filter(Location.barcode == barcode).first()
        
        if not location:
            self.show_error("Erreur", "Emplacement non trouvé.")
            return

        # Select in Combo
        index = self.location_combo.findData(location.id)
        if index >= 0:
            self.location_combo.setCurrentIndex(index)
        
        self.current_location = location
        self.load_products()

    def process_product_scan(self, barcode):
        if not self.current_location:
            self.show_error("Attention", "Veuillez d'abord sélectionner un emplacement.")
            return

        db = next(get_db())
        
        # Check if product already exists in this location
        existing = db.query(Product).filter(Product.barcode == barcode, Product.location_id == self.current_location.id).first()
        if existing:
            self.show_error("Attention", "Ce produit existe déjà dans cet emplacement.")
            return

        # Fetch from XpertPharm
        product_data = get_product_from_xpertpharm(barcode)
        
        if not product_data:
            self.show_error("Erreur", "Code à barre non reconu.")
            return

        # Create Product
        new_product = Product(
            code=product_data['CODE_PRODUIT'],
            barcode=barcode,
            designation=product_data['designation'],
            expiry_date=product_data['expiry_date'],
            location_id=self.current_location.id
        )
        
        try:
            db.add(new_product)
            db.commit()
            self.load_products()
        except Exception as e:
            db.rollback()
            self.show_error("Erreur", f"Erreur lors de l'ajout du produit: {e}")

    def load_products(self):
        self.table.setRowCount(0)
        if not self.current_location:
            return

        db = next(get_db())
        products = db.query(Product).filter(Product.location_id == self.current_location.id).all()
        
        self.table.setRowCount(len(products))
        for row, prod in enumerate(products):
            # Removed Code column (index 0)
            self.table.setItem(row, 0, QTableWidgetItem(prod.designation))
            self.table.setItem(row, 1, QTableWidgetItem(str(prod.expiry_date)))
            self.table.setItem(row, 2, QTableWidgetItem(prod.barcode))
            
            # Actions Widget with Icons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)
            
            # Move Button - Changed Icon to SP_FileDialogDetailedView (List icon) or SP_DirIcon
            # Let's use SP_ArrowForward or something distinct if ArrowRight wasn't good.
            # User said "l'icon dédié à déplacer ne me plait pas".
            # Let's try SP_CommandLink (Arrow) or SP_ToolBarHorizontalExtensionButton
            # Or maybe SP_DialogYesButton (Check)? No.
            # Let's try SP_DirIcon (Folder) -> Move to folder?
            # Let's try SP_FileDialogListView.
            move_btn = QPushButton()
            move_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
            move_btn.setToolTip("Déplacer")
            move_btn.clicked.connect(lambda checked, p=prod: self.move_product(p))
            actions_layout.addWidget(move_btn)
            
            # Delete Button
            del_btn = QPushButton()
            del_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
            del_btn.setToolTip("Supprimer")
            del_btn.clicked.connect(lambda checked, p_id=prod.id: self.delete_product(p_id))
            actions_layout.addWidget(del_btn)
            
            actions_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 3, actions_widget)

    def delete_product(self, product_id):
        reply = QMessageBox.question(self, "Confirmer", "Voulez-vous vraiment supprimer ce produit de l'emplacement ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db = next(get_db())
            prod = db.query(Product).filter(Product.id == product_id).first()
            if prod:
                db.delete(prod)
                db.commit()
                self.load_products()

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
                    self.load_products() # Refresh
