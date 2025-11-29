from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QDialog, QLabel, QLineEdit,
    QDialogButtonBox, QFormLayout, QStyle, QCheckBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database.connection import get_db
from database.models import Location, Product
import logging

logger = logging.getLogger(__name__)


class LocationDialog(QDialog):
    def __init__(self, location=None, parent=None):
        super().__init__(parent)
        self.location = location
        self.setWindowTitle("Modifier l'emplacement" if location else "Ajouter un emplacement")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # Label input
        self.label_input = QLineEdit()
        self.label_input.setMaxLength(10)
        self.label_input.setPlaceholderText("ex: A1, B12, etc.")
        if self.location:
            self.label_input.setText(self.location.label)
        layout.addRow("Label:", self.label_input)
        
        # Barcode input
        self.barcode_input = QLineEdit()
        self.barcode_input.setMaxLength(20)
        self.barcode_input.setPlaceholderText("ex: 000AA01")
        if self.location:
            self.barcode_input.setText(self.location.barcode)
        layout.addRow("Code-barre:", self.barcode_input)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def validate_and_accept(self):
        label = self.label_input.text().strip()
        barcode = self.barcode_input.text().strip()
        
        if not label:
            QMessageBox.warning(self, "Erreur", "Le label est obligatoire.")
            return
        
        if not barcode:
            QMessageBox.warning(self, "Erreur", "Le code-barre est obligatoire.")
            return
        
        self.accept()
    
    def get_data(self):
        return {
            'label': self.label_input.text().strip(),
            'barcode': self.barcode_input.text().strip()
        }


class LocationsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_locations()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Top buttons
        top_layout = QHBoxLayout()
        add_btn = QPushButton("Ajouter un emplacement")
        add_btn.clicked.connect(self.add_location)
        top_layout.addWidget(add_btn)
        
        # Selection buttons
        select_all_btn = QPushButton("Tout sélectionner")
        select_all_btn.clicked.connect(self.toggle_select_all)
        top_layout.addWidget(select_all_btn)
        
        # Print barcodes button
        print_btn = QPushButton("Imprimer codes-barres")
        print_btn.clicked.connect(self.print_barcodes)
        top_layout.addWidget(print_btn)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["☑", "Label", "Code-barre", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # Track selection state for toggle
        self.all_selected = False
    
    def load_locations(self):
        self.table.setRowCount(0)
        
        with get_db() as db:
            if not db:
                return
            
            locations = db.query(Location).order_by(Location.label).all()
            self.table.setRowCount(len(locations))
            
            for row, loc in enumerate(locations):
                # Checkbox
                checkbox = QCheckBox()
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout()
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.addWidget(checkbox)
                checkbox_widget.setLayout(checkbox_layout)
                self.table.setCellWidget(row, 0, checkbox_widget)
                
                # Store location data
                label_item = QTableWidgetItem(loc.label)
                label_item.setData(Qt.ItemDataRole.UserRole, loc)
                self.table.setItem(row, 1, label_item)
                self.table.setItem(row, 2, QTableWidgetItem(loc.barcode))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)
                actions_layout.setSpacing(4)
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Edit button
                edit_btn = QPushButton()
                edit_btn.setObjectName("TableActionBtn")
                edit_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
                edit_btn.setToolTip("Modifier")
                edit_btn.clicked.connect(lambda checked, l=loc: self.edit_location(l))
                actions_layout.addWidget(edit_btn)
                
                # Delete button
                del_btn = QPushButton()
                del_btn.setObjectName("TableActionBtn")
                del_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
                del_btn.setToolTip("Supprimer")
                del_btn.clicked.connect(lambda checked, l_id=loc.id: self.delete_location(l_id))
                actions_layout.addWidget(del_btn)
                
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 3, actions_widget)
    
    def toggle_select_all(self):
        self.all_selected = not self.all_selected
        
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(self.all_selected)
    
    def get_selected_locations(self):
        selected = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    label_item = self.table.item(row, 1)
                    if label_item:
                        location = label_item.data(Qt.ItemDataRole.UserRole)
                        if location:
                            selected.append(location)
        return selected
    
    def print_barcodes(self):
        selected = self.get_selected_locations()
        
        if not selected:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner au moins un emplacement.")
            return
        
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QPainter, QPageSize, QPageLayout, QPixmap
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
            
            # Set custom page size for barcode labels (40mm width x 20mm height for landscape)
            page_size = QPageSize(QSizeF(40, 20), QPageSize.Unit.Millimeter)
            printer.setPageSize(page_size)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            
            # Set zero margins using QMarginsF
            printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
            
            # Show native Windows print dialog
            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec() != QDialog.DialogCode.Accepted:
                return
            
            # FORCE custom page size again after dialog (dialog may have changed it to A4)
            printer.setPageSize(page_size)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
            
            # Start printing
            painter = QPainter()
            if not painter.begin(printer):
                QMessageBox.critical(self, "Erreur", "Impossible de démarrer l'impression.")
                return
            
            for idx, location in enumerate(selected):
                if idx > 0:
                    # New page for each label
                    printer.newPage()
                
                # Get page dimensions in pixels
                page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                width = page_rect.width()
                height = page_rect.height()
                
                # Convert 2mm to pixels (at printer DPI)
                dpi = printer.resolution()
                margin_2mm = (2 / 25.4) * dpi  # 2mm in pixels
                
                # DEBUG: Print dimensions in mm
                width_mm = (width / dpi) * 25.4
                height_mm = (height / dpi) * 25.4
                text_zone_height_mm = height_mm * 0.3
                barcode_zone_height_mm = height_mm * 0.65
                
                print(f"\n=== DEBUG ÉTIQUETTE {location.label} ===")
                print(f"Résolution imprimante: {dpi} DPI")
                print(f"Dimensions page: {width_mm:.2f}mm x {height_mm:.2f}mm")
                print(f"Zone texte (haut): {text_zone_height_mm:.2f}mm (30% de {height_mm:.2f}mm)")
                print(f"Zone code-barres: {barcode_zone_height_mm:.2f}mm (65% de {height_mm:.2f}mm)")
                print(f"Marge gauche/droite: 2.00mm")
                print(f"Police emplacement: 24pt = {24 * 0.353:.2f}mm")
                print(f"Police numéro: 16pt = {16 * 0.353:.2f}mm")
                print(f"Hauteur barres code-barres: 8mm")
                print(f"Largeur barre individuelle: 0.25mm")
                print("="*40)
                
                # Draw location label and barcode number on same line at top
                # Location on the left, larger font with 2mm left margin
                painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
                painter.drawText(QRectF(margin_2mm, 0, width * 0.5, height * 0.3), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, location.label)
                
                # Barcode number on the right with 2mm right margin
                painter.setFont(QFont("Arial", 16))
                painter.drawText(QRectF(width * 0.4, 0, width * 0.6 - margin_2mm, height * 0.3), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, location.barcode)
                
                # Generate barcode using python-barcode (without text below)
                CODE128 = barcode.get_barcode_class('code128')
                barcode_obj = CODE128(location.barcode, writer=ImageWriter())
                
                # Render barcode to PNG in memory (without text)
                buffer = BytesIO()
                barcode_obj.write(buffer, options={
                    'module_width': 0.25,
                    'module_height': 8,
                    'font_size': 0,  # Hide the text below barcode
                    'text_distance': 0,
                    'quiet_zone': 1,
                    'write_text': False  # Don't write text
                })
                buffer.seek(0)
                
                # Convert to QPixmap
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.read())
                
                # Draw barcode bars below the text
                barcode_height = height * 0.65
                barcode_width = width * 0.95
                x_offset = (width - barcode_width) / 2
                y_offset = height * 0.3
                
                painter.drawPixmap(QRectF(x_offset, y_offset, barcode_width, barcode_height), pixmap, QRectF(pixmap.rect()))
            
            painter.end()
            QMessageBox.information(self, "Succès", f"{len(selected)} code(s)-barre(s) imprimé(s).")
            
        except Exception as e:
            logger.error(f"Error printing barcodes: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'impression: {e}")
    
    def add_location(self):
        dialog = LocationDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            
            try:
                with get_db() as db:
                    if not db:
                        return
                    
                    # Check for duplicates
                    existing_label = db.query(Location).filter(Location.label == data['label']).first()
                    if existing_label:
                        QMessageBox.warning(self, "Erreur", f"Un emplacement avec le label '{data['label']}' existe déjà.")
                        return
                    
                    existing_barcode = db.query(Location).filter(Location.barcode == data['barcode']).first()
                    if existing_barcode:
                        QMessageBox.warning(self, "Erreur", f"Un emplacement avec le code-barre '{data['barcode']}' existe déjà.")
                        return
                    
                    # Create new location
                    new_loc = Location(
                        label=data['label'],
                        barcode=data['barcode']
                    )
                    db.add(new_loc)
                    db.commit()
                    
                    QMessageBox.information(self, "Succès", "Emplacement ajouté avec succès.")
                    self.load_locations()
            except Exception as e:
                logger.error(f"Error adding location: {e}")
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout: {e}")
    
    def edit_location(self, location):
        dialog = LocationDialog(location=location, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            
            try:
                with get_db() as db:
                    if not db:
                        return
                    
                    # Re-fetch to attach to session
                    loc = db.query(Location).get(location.id)
                    if not loc:
                        QMessageBox.warning(self, "Erreur", "Emplacement introuvable.")
                        return
                    
                    # Check for duplicates (excluding current)
                    existing_label = db.query(Location).filter(
                        Location.label == data['label'],
                        Location.id != loc.id
                    ).first()
                    if existing_label:
                        QMessageBox.warning(self, "Erreur", f"Un emplacement avec le label '{data['label']}' existe déjà.")
                        return
                    
                    existing_barcode = db.query(Location).filter(
                        Location.barcode == data['barcode'],
                        Location.id != loc.id
                    ).first()
                    if existing_barcode:
                        QMessageBox.warning(self, "Erreur", f"Un emplacement avec le code-barre '{data['barcode']}' existe déjà.")
                        return
                    
                    # Update
                    loc.label = data['label']
                    loc.barcode = data['barcode']
                    db.commit()
                    
                    QMessageBox.information(self, "Succès", "Emplacement modifié avec succès.")
                    self.load_locations()
            except Exception as e:
                logger.error(f"Error editing location: {e}")
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification: {e}")
    
    def delete_location(self, location_id):
        try:
            with get_db() as db:
                if not db:
                    return
                
                # Check if location is used
                products_count = db.query(Product).filter(Product.location_id == location_id).count()
                if products_count > 0:
                    QMessageBox.warning(
                        self,
                        "Impossible de supprimer",
                        f"Cet emplacement est utilisé par {products_count} produit(s).\n\n"
                        "Vous devez d'abord retirer ou déplacer ces produits avant de supprimer l'emplacement."
                    )
                    return
                
                # Confirm deletion
                loc = db.query(Location).get(location_id)
                if not loc:
                    return
                
                reply = QMessageBox.question(
                    self,
                    "Confirmer la suppression",
                    f"Voulez-vous vraiment supprimer l'emplacement '{loc.label}' ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    db.delete(loc)
                    db.commit()
                    QMessageBox.information(self, "Succès", "Emplacement supprimé avec succès.")
                    self.load_locations()
        except Exception as e:
            logger.error(f"Error deleting location: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {e}")
