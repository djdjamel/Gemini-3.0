from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QComboBox, QCheckBox, QAbstractItemView, QDialog, QStyle, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QIcon
from database.connection import get_db, get_product_from_xpertpharm
from database.models import Location, Product, Nomenclature, MissingItem
from utils.barcode_utils import is_location_barcode, parse_location_barcode
from ui.dialogs import ChangeLocationDialog
from sqlalchemy.orm import Session
import logging
import pyttsx3
from datetime import datetime
import pandas as pd
import os

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
        self.cleaning_mode = False
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
        
        # Cleaning Mode Controls (Top Right)
        cleaning_group = QGroupBox("Nettoyage Stock")
        cleaning_group.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 0px; padding-top: 5px; }")
        cleaning_layout = QHBoxLayout()
        cleaning_layout.setContentsMargins(10, 10, 10, 10)
        cleaning_layout.setSpacing(10)
        
        self.btn_start_cleaning = QPushButton("Créer")
        self.btn_start_cleaning.setToolTip("Lancer un nettoyage de stock")
        self.btn_start_cleaning.setFixedSize(60, 25)
        self.btn_start_cleaning.clicked.connect(self.start_cleaning)
        cleaning_layout.addWidget(self.btn_start_cleaning)
        
        self.btn_verify_cleaning = QPushButton("Vérifier")
        self.btn_verify_cleaning.setToolTip("Vérifier les manquants")
        self.btn_verify_cleaning.setFixedSize(60, 25)
        self.btn_verify_cleaning.clicked.connect(self.verify_cleaning)
        cleaning_layout.addWidget(self.btn_verify_cleaning)
        
        self.btn_close_cleaning = QPushButton("Clôturer")
        self.btn_close_cleaning.setToolTip("Supprimer les manquants et terminer")
        self.btn_close_cleaning.setFixedSize(60, 25)
        self.btn_close_cleaning.clicked.connect(self.close_cleaning)
        self.btn_close_cleaning.setEnabled(False)
        cleaning_layout.addWidget(self.btn_close_cleaning)
        
        cleaning_group.setLayout(cleaning_layout)
        top_layout.addWidget(cleaning_group)

        layout.addLayout(top_layout)

        # Product Table
        self.table = QTableWidget()
        # Removed 'Code' column, now 4 columns
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Désignation", "Date Exp", "Code Barre", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Make table read-only
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(48)
        
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
        with get_db() as db:
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
            with get_db() as db:
                if db:
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
        
        with get_db() as db:
            if not db: return
            location = db.query(Location).filter(Location.barcode == barcode).first()
            
            if not location:
                self.show_error("Erreur", "Emplacement non trouvé.")
                return

            # Select in Combo
            index = self.location_combo.findData(location.id)
            if index >= 0:
                self.location_combo.setCurrentIndex(index)
            
            self.current_location = location
            self.speak(location.label)
            self.load_products()

    def process_product_scan(self, barcode):
        if not self.current_location:
            self.show_error("Attention", "Veuillez d'abord sélectionner un emplacement.")
            return

        with get_db() as db:
            if not db: return
            
            # Check if product already exists in this location
            existing = db.query(Product).filter(Product.barcode == barcode, Product.location_id == self.current_location.id).first()
            
            if self.cleaning_mode:
                if existing:
                    # Mark as present (cleaning=0)
                    existing.cleaning = False
                    db.commit()
                    self.load_products() # Refresh to show status change if any visual indicator
                    # Suppress warnings
                    return
                # If not existing in cleaning mode, we proceed to add it (assuming it was missed before)
                # Warnings are suppressed in cleaning mode
            else:
                if existing:
                    self.show_error("Attention", "Ce produit existe déjà dans cet emplacement.")
                    return

            # Fetch from XpertPharm
            product_data = get_product_from_xpertpharm(barcode)
            
            if not product_data:
                self.show_error("Erreur", "Code à barre non reconu.")
                return
            
            # Check for newer barcodes (same product code, created_on >= current)
            # Suppress in cleaning mode
            if not self.cleaning_mode:
                from database.connection import check_newer_barcodes
                created_on = product_data.get('CREATED_ON')
                product_code = product_data.get('CODE_PRODUIT')
                
                if created_on and product_code:
                    newer_count = check_newer_barcodes(barcode, product_code, created_on)
                    if newer_count > 0:
                        warning_msg = f"Attention ! {newer_count} code à barre plus récent détecté pour ce produit."
                        self.speak(warning_msg)
                        QMessageBox.warning(self, "Avertissement", warning_msg)

            # Create/Update Nomenclature
            nomenclature = db.query(Nomenclature).filter(Nomenclature.code == product_data['CODE_PRODUIT']).first()
            if not nomenclature:
                nomenclature = Nomenclature(
                    code=product_data['CODE_PRODUIT'],
                    designation=product_data['designation'],
                    last_edit_date=datetime.now(),
                    last_supply_date=datetime.now()
                )
                db.add(nomenclature)
            else:
                # Update designation if changed (optional, but good practice)
                nomenclature.designation = product_data['designation']
                nomenclature.last_edit_date = datetime.now()
            
            # Create Product
            new_product = Product(
                code=product_data['CODE_PRODUIT'],
                barcode=barcode,
                expiry_date=product_data['expiry_date'],
                location_id=self.current_location.id
            )
            
            try:
                db.add(new_product)
                db.commit()
                self.load_products()
                self.speak("Suivant")
            except Exception as e:
                db.rollback()
                self.show_error("Erreur", f"Erreur lors de l'ajout du produit: {e}")

    def load_products(self):
        self.table.setRowCount(0)
        if not self.current_location:
            return

        with get_db() as db:
            if not db: return
            products = db.query(Product).join(Nomenclature).filter(Product.location_id == self.current_location.id).all()
            
            self.table.setRowCount(len(products))
            for row, prod in enumerate(products):
                designation = prod.nomenclature.designation if prod.nomenclature else "Unknown"
                # Removed Code column (index 0)
                self.table.setItem(row, 0, QTableWidgetItem(designation))
                self.table.setItem(row, 1, QTableWidgetItem(str(prod.expiry_date)))
                self.table.setItem(row, 2, QTableWidgetItem(prod.barcode))
                
                # Actions Widget with Icons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)
                actions_layout.setSpacing(4)
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Move Button
                move_btn = QPushButton()
                move_btn.setObjectName("TableActionBtn")
                move_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
                move_btn.setToolTip("Déplacer")
                move_btn.clicked.connect(lambda checked, p=prod: self.move_product(p))
                actions_layout.addWidget(move_btn)
                
                # Delete Button
                del_btn = QPushButton()
                del_btn.setObjectName("TableActionBtn")
                del_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
                del_btn.setToolTip("Supprimer")
                del_btn.clicked.connect(lambda checked, p_id=prod.id: self.delete_product(p_id))
                actions_layout.addWidget(del_btn)
                
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 3, actions_widget)

    def delete_product(self, product_id):
        reply = QMessageBox.question(self, "Confirmer", "Voulez-vous vraiment supprimer ce produit de l'emplacement ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with get_db() as db:
                if not db: return
                prod = db.query(Product).filter(Product.id == product_id).first()
                if prod:
                    # Check if it's the last one
                    code = prod.code
                    count = db.query(Product).filter(Product.code == code).count()
                    
                    # Update Nomenclature last_edit_date
                    if prod.nomenclature:
                        prod.nomenclature.last_edit_date = datetime.now()
                    
                    db.delete(prod)
                    
                    if count == 1:
                        # It was the last one
                        designation = prod.nomenclature.designation if prod.nomenclature else "Inconnu"
                        
                        # Check if already in missing (just in case)
                        existing_missing = db.query(MissingItem).filter(MissingItem.product_code == code).first()
                        if not existing_missing:
                            new_missing = MissingItem(
                                product_code=code,
                                source="Inventaire",
                                reported_at=datetime.now()
                            )
                            db.add(new_missing)
                            self.show_error("Info", f"Le produit '{designation}' était le dernier en stock. Il a été ajouté aux manquants.")
                    
                    db.commit()
                    self.load_products()

    def move_product(self, product):
        dialog = ChangeLocationDialog(product.location_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_loc_id = dialog.selected_location_id
            if new_loc_id:
                with get_db() as db:
                    if db:
                        prod_db = db.query(Product).filter(Product.id == product.id).first()
                        if prod_db:
                            prod_db.location_id = new_loc_id
                            
                            # Update Nomenclature last_edit_date
                            if prod_db.nomenclature:
                                prod_db.nomenclature.last_edit_date = datetime.now()
                                
                            db.commit()
                            self.load_products() # Refresh

    def start_cleaning(self):
        reply = QMessageBox.question(self, "Confirmation", "Êtes-vous sûr de vouloir lancer un nettoyage de stock ?\nTous les produits seront marqués comme 'à vérifier'.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with get_db() as db:
                if not db: return
                try:
                    # Set cleaning=True for ALL products
                    db.query(Product).update({Product.cleaning: True})
                    db.commit()
                    self.cleaning_mode = True
                    self.update_cleaning_ui()
                    QMessageBox.information(self, "Info", "Nettoyage lancé. Scannez les produits présents.")
                except Exception as e:
                    db.rollback()
                    QMessageBox.critical(self, "Erreur", f"Erreur lors du lancement du nettoyage: {e}")

    def verify_cleaning(self):
        with get_db() as db:
            if not db: return
            # Find products still marked as cleaning=True
            missing_products = db.query(Product).join(Nomenclature).join(Location).filter(Product.cleaning == True).all()
            
            if not missing_products:
                QMessageBox.information(self, "Info", "Aucun produit manquant (non scanné) trouvé.")
                return

            # Show Dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Vérification Nettoyage - Produits Non Scannés")
            dialog.resize(600, 400)
            layout = QVBoxLayout()
            
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Désignation", "Emplacement"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            table.setRowCount(len(missing_products))
            
            for i, prod in enumerate(missing_products):
                designation = prod.nomenclature.designation if prod.nomenclature else "Inconnu"
                location = prod.location.label if prod.location else "Inconnu"
                table.setItem(i, 0, QTableWidgetItem(designation))
                table.setItem(i, 1, QTableWidgetItem(location))
                
            layout.addWidget(table)
            
            export_btn = QPushButton("Exporter vers Excel")
            export_btn.clicked.connect(lambda: self.export_cleaning_results(missing_products, dialog))
            layout.addWidget(export_btn)
            
            dialog.setLayout(layout)
            dialog.exec()

    def export_cleaning_results(self, products, dialog):
        try:
            data = []
            for prod in products:
                data.append({
                    "Désignation": prod.nomenclature.designation if prod.nomenclature else "Inconnu",
                    "Emplacement": prod.location.label if prod.location else "Inconnu",
                    "Code Barre": prod.barcode
                })
            
            df = pd.DataFrame(data)
            filename = f"nettoyage_stock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            path = os.path.join(os.path.expanduser("~"), "Documents", filename)
            df.to_excel(path, index=False)
            
            QMessageBox.information(dialog, "Succès", f"Exporté vers {path}")
            self.btn_close_cleaning.setEnabled(True) # Enable Close button
            dialog.accept()
        except Exception as e:
            QMessageBox.critical(dialog, "Erreur", f"Erreur lors de l'export: {e}")

    def close_cleaning(self):
        reply = QMessageBox.question(self, "Confirmation", "Voulez-vous vraiment CLÔTURER le nettoyage ?\nTous les produits non scannés seront SUPPRIMÉS définitivement.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            with get_db() as db:
                if not db: return
                try:
                    # Delete products with cleaning=True
                    deleted_count = db.query(Product).filter(Product.cleaning == True).delete()
                    db.commit()
                    
                    self.cleaning_mode = False
                    self.update_cleaning_ui()
                    self.btn_close_cleaning.setEnabled(False)
                    self.load_products() # Refresh current view
                    
                    QMessageBox.information(self, "Succès", f"Nettoyage clôturé. {deleted_count} produits supprimés.")
                except Exception as e:
                    db.rollback()
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la clôture: {e}")

    def update_cleaning_ui(self):
        if self.cleaning_mode:
            self.scan_input.setStyleSheet("background-color: #ffcdd2; color: #c62828;") # Red
            self.btn_start_cleaning.setEnabled(False)
        else:
            self.scan_input.setStyleSheet("") # Reset
            self.btn_start_cleaning.setEnabled(True)
