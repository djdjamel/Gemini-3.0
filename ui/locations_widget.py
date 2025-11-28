from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QDialog, QLabel, QLineEdit,
    QDialogButtonBox, QFormLayout, QStyle
)
from PyQt6.QtCore import Qt
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
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Label", "Code-barre", "Actions"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_locations(self):
        self.table.setRowCount(0)
        
        with get_db() as db:
            if not db:
                return
            
            locations = db.query(Location).order_by(Location.label).all()
            self.table.setRowCount(len(locations))
            
            for row, loc in enumerate(locations):
                self.table.setItem(row, 0, QTableWidgetItem(loc.label))
                self.table.setItem(row, 1, QTableWidgetItem(loc.barcode))
                
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
                self.table.setCellWidget(row, 2, actions_widget)
    
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
