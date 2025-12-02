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
            engine.stop()
            del engine
        except Exception as e:
            # Suppress TTS errors as they're not critical
            pass

class InventoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_location = None
        self.cleaning_mode = False
        self.init_ui()
        self.load_locations()
        self.check_active_cleaning_session()

    def check_active_cleaning_session(self):
        with get_db() as db:
            if not db: return
            # Check if any product has cleaning=True
            active_cleaning = db.query(Product).filter(Product.cleaning == True).first()
            if active_cleaning:
                self.cleaning_mode = True
                self.update_cleaning_ui()

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
        self.btn_start_cleaning.setFixedSize(90, 30)
        self.btn_start_cleaning.clicked.connect(self.start_cleaning)
        cleaning_layout.addWidget(self.btn_start_cleaning)
        
        self.btn_verify_cleaning = QPushButton("Vérifier")
        self.btn_verify_cleaning.setToolTip("Vérifier les manquants")
        self.btn_verify_cleaning.setFixedSize(90, 30)
        self.btn_verify_cleaning.clicked.connect(self.verify_cleaning)
        cleaning_layout.addWidget(self.btn_verify_cleaning)
        
        self.btn_close_cleaning = QPushButton("Clôturer")
        self.btn_close_cleaning.setToolTip("Supprimer les manquants et terminer")
        self.btn_close_cleaning.setFixedSize(90, 30)
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
        
        # Add context menu for printing
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
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
                
                # Calculate delay (time since product creation in XpertPharm)
                delay = None
                try:
                    from datetime import timedelta
                    
                    created_on = product_data.get('CREATED_ON')
                    if created_on:
                        # Check if Thursday (weekday == 3), add 24h (Friday holiday)
                        if created_on.weekday() == 3:
                            adjusted_created_on = created_on + timedelta(hours=24)
                        else:
                            adjusted_created_on = created_on
                        
                        now = datetime.now()
                        delay_hours = (now - adjusted_created_on).total_seconds() / 3600
                        
                        # Only positive delays
                        if delay_hours > 0:
                            delay = delay_hours
                except Exception as e:
                    logger.error(f"Failed to calculate delay: {e}")
                
                # Log Event with delay
                from database.connection import log_event
                log_event('INVENTORY_ADD', details=product_data['CODE_PRODUIT'], source='InventoryWidget', delay=delay)
                
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
                
                # Create designation item and store product data for printing
                designation_item = QTableWidgetItem(designation)
                
                # Store product data for barcode printing
                product_data = {
                    'designation': designation,
                    'barcode': prod.barcode,
                    'expiry_date': prod.expiry_date
                }
                designation_item.setData(Qt.ItemDataRole.UserRole, product_data)
                
                # Set items in table
                self.table.setItem(row, 0, designation_item)
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
                    
                    # Log Event
                    from database.connection import log_event
                    log_event('PRODUCT_DELETED', details=f"ID: {product_id}, Code: {code}", source='InventoryWidget')
                    
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
                            
                            # Log Event
                            from database.connection import log_event
                            log_event('PRODUCT_MOVED', details=f"ID: {product.id} -> LocID: {new_loc_id}", source='InventoryWidget')
                            
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
                    
                    # Log Event
                    from database.connection import log_event
                    log_event('INVENTORY_CLEANING_LOSS', details=str(deleted_count), source='InventoryWidget')
                    
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
            self.btn_verify_cleaning.setEnabled(True)
        else:
            self.scan_input.setStyleSheet("") # Reset
            self.btn_start_cleaning.setEnabled(True)
            self.btn_verify_cleaning.setEnabled(False)

    def show_context_menu(self, position):
        """Show context menu for barcode printing"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu()
        
        # Print selected product
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            print_item = menu.addAction("Imprimer ce produit")
            print_item.triggered.connect(lambda: self.print_selected_product(selected_row))
        
        # Print all products
        if self.table.rowCount() > 0:
            print_all = menu.addAction("Imprimer tous")
            print_all.triggered.connect(self.print_all_products)
        
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    def print_selected_product(self, row):
        """Print barcode for selected product"""
        product_data = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if product_data:
            self.print_product_barcodes([product_data])
    
    def print_all_products(self):
        """Print barcodes for all products with confirmation"""
        count = self.table.rowCount()
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment imprimer {count} étiquette(s) de produits ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            products = []
            for row in range(count):
                product_data = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if product_data:
                    products.append(product_data)
            
            if products:
                self.print_product_barcodes(products)
    
    def print_product_barcodes(self, products):
        """Print barcode labels for products"""
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QPainter, QPageSize, QPageLayout, QPixmap, QFont
            from PyQt6.QtCore import QSizeF, QRectF, QMarginsF
            from io import BytesIO
            
            try:
                import barcode
                from barcode.writer import ImageWriter
            except ImportError:
                QMessageBox.critical(
                    self,
                    "Module manquant",
                    "Le module 'python-barcode' n'est pas installé.\n\n"
                    "Installez-le avec: pip install python-barcode pillow"
                )
                return
            
            # Create printer with custom page size (40mm x 20mm in landscape)
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            
            # Set custom page size for barcode labels (40mm width x 20mm height)
            page_size = QPageSize(QSizeF(40, 20), QPageSize.Unit.Millimeter)
            printer.setPageSize(page_size)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
            
            # Show native Windows print dialog
            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            # Force custom page size again after dialog
            printer.setPageSize(page_size)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
            
            # Start printing
            painter = QPainter()
            if not painter.begin(printer):
                QMessageBox.critical(self, "Erreur", "Impossible de démarrer l'impression.")
                return
            
            for idx, product in enumerate(products):
                if idx > 0:
                    printer.newPage()
                
                # Get page dimensions
                page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                width = page_rect.width()
                height = page_rect.height()
                
                # Draw product name at top (10pt)
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                painter.drawText(QRectF(0, 0, width, height * 0.2), Qt.AlignmentFlag.AlignCenter, product['designation'])
                
                # Generate barcode using python-barcode (without text)
                CODE128 = barcode.get_barcode_class('code128')
                barcode_obj = CODE128(product['barcode'], writer=ImageWriter())
                
                # Render barcode to PNG in memory (without text)
                buffer = BytesIO()
                barcode_obj.write(buffer, options={
                    'module_width': 0.25,
                    'module_height': 8,
                    'font_size': 0,
                    'text_distance': 0,
                    'quiet_zone': 1,
                    'write_text': False
                })
                buffer.seek(0)
                
                # Convert to QPixmap
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.read())
                
                # Draw barcode bars (30% of height)
                barcode_height = height * 0.3
                barcode_width = width * 0.95
                x_offset = (width - barcode_width) / 2
                y_offset = height * 0.25
                
                painter.drawPixmap(QRectF(x_offset, y_offset, barcode_width, barcode_height), pixmap, QRectF(pixmap.rect()))
                
                # Bottom section: Expiry date (left) and Barcode number (right)
                painter.setFont(QFont("Arial", 8))
                
                # Expiry date on the left (MM/YY format)
                expiry_text = ""
                if product.get('expiry_date'):
                    try:
                        if isinstance(product['expiry_date'], str):
                            expiry_text = product['expiry_date']
                        else:
                            expiry_text = product['expiry_date'].strftime('%m/%y')
                    except:
                        expiry_text = str(product.get('expiry_date', ''))
                
                painter.drawText(QRectF(0, height * 0.7, width * 0.4, height * 0.3), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, expiry_text)
                
                # Barcode number on the right
                painter.drawText(QRectF(width * 0.6, height * 0.7, width * 0.4, height * 0.3), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, product['barcode'])
            
            painter.end()
            QMessageBox.information(self, "Succès", f"{len(products)} étiquette(s) imprimée(s).")
            
        except Exception as e:
            logger.error(f"Error printing barcodes: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'impression: {e}")
