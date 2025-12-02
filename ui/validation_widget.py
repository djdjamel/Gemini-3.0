from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QDialog, QDialogButtonBox, QStyle
)
from PyQt6.QtCore import Qt
from database.connection import get_db
from database.models import SupplyList, SupplyListItem, Location, Product, MissingItem
from ui.dialogs import ChangeLocationDialog
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ValidationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_list = None
        self.init_ui()
        self.load_lists()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top: Select List
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Liste à valider:"))
        self.list_combo = QComboBox()
        self.list_combo.currentIndexChanged.connect(self.on_list_selected)
        top_layout.addWidget(self.list_combo)
        
        refresh_btn = QPushButton("Rafraîchir")
        refresh_btn.clicked.connect(self.load_lists)
        top_layout.addWidget(refresh_btn)
        
        layout.addLayout(top_layout)

        # List Info
        self.info_label = QLabel("")
        layout.addWidget(self.info_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Désignation", "Emplacement Actuel", "Nouvel Emplacement", "Quantité", "Résultat", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Validate Button
        self.validate_btn = QPushButton("Valider la liste")
        self.validate_btn.clicked.connect(self.validate_list)
        layout.addWidget(self.validate_btn)

        self.setLayout(layout)

    def load_lists(self):
        self.list_combo.blockSignals(True)
        self.list_combo.clear()
        with get_db() as db:
            if not db: return
            
            # Filter: Only 'closed' or 'validated' lists
            lists = db.query(SupplyList).filter(SupplyList.status.in_(['closed', 'validated'])).order_by(SupplyList.created_at.desc()).all()
            
            for lst in lists:
                status_label = " (ARCHIVÉ)" if lst.status == 'validated' else ""
                self.list_combo.addItem(f"{lst.title} - {lst.created_at.strftime('%Y-%m-%d %H:%M')}{status_label}", lst.id)
            
        self.list_combo.blockSignals(False)
        if self.list_combo.count() > 0:
            self.on_list_selected()
        else:
            self.table.setRowCount(0)
            self.current_list = None
            self.info_label.setText("")
            self.validate_btn.setEnabled(False)

    def on_list_selected(self):
        list_id = self.list_combo.currentData()
        if not list_id:
            return

        with get_db() as db:
            if not db: return
            self.current_list = db.query(SupplyList).filter(SupplyList.id == list_id).first()
            
            if self.current_list:
                status_text = "VALIDÉE / ARCHIVÉE" if self.current_list.status == 'validated' else "EN ATTENTE DE VALIDATION"
                self.info_label.setText(f"Statut: {status_text}")
                self.validate_btn.setEnabled(self.current_list.status == 'closed')
                self.load_items()

    def load_items(self):
        self.table.setRowCount(0)
        if not self.current_list:
            return

        items = self.current_list.items
        self.table.setRowCount(len(items))
        
        is_read_only = self.current_list.status == 'validated'

        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item.designation_1))
            self.table.setItem(row, 1, QTableWidgetItem(item.location_1))
            self.table.setItem(row, 2, QTableWidgetItem(item.location_2 or ""))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.quantity)))
            
            # Result Column (V, S, X, or New Loc)
            res_item = QTableWidgetItem(item.result)
            if is_read_only:
                res_item.setFlags(res_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, res_item)
            
            # Actions
            if not is_read_only:
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                # Delete (Mark as S/X)
                del_btn = QPushButton()
                del_btn.setObjectName("TableActionBtn")
                del_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
                del_btn.setToolTip("Supprimer / Marquer comme Manquant")
                del_btn.clicked.connect(lambda checked, r=row, i=item: self.mark_delete(r, i))
                actions_layout.addWidget(del_btn)
                
                # Move
                move_btn = QPushButton()
                move_btn.setObjectName("TableActionBtn")
                move_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogListView))
                move_btn.setToolTip("Déplacer")
                move_btn.clicked.connect(lambda checked, r=row, i=item: self.mark_move(r, i))
                actions_layout.addWidget(move_btn)
                
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                actions_widget.setLayout(actions_layout)
                self.table.setCellWidget(row, 5, actions_widget)
            else:
                self.table.setCellWidget(row, 5, QLabel(""))

    def mark_delete(self, row, item):
        # Toggle between V and S (or X)
        current = self.table.item(row, 4).text()
        new_val = 'S' if current != 'S' else 'V'
        self.table.item(row, 4).setText(new_val)
        
        # Update DB
        with get_db() as db:
            if db:
                item_db = db.merge(item)
                item_db.result = new_val
                db.commit()

    def mark_move(self, row, item):
        # Open Dialog to select new location
        # We need the current location ID to exclude it, but item stores label.
        # Let's just pass None or try to find it.
        dialog = ChangeLocationDialog(-1, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_loc_id = dialog.selected_location_id
            if new_loc_id:
                with get_db() as db:
                    if db:
                        new_loc = db.query(Location).filter(Location.id == new_loc_id).first()
                        if new_loc:
                            self.table.item(row, 4).setText(new_loc.label)
                            item_db = db.merge(item)
                            item_db.result = new_loc.label
                            db.commit()

    def validate_list(self):
        if not self.current_list or self.current_list.status != 'closed':
            return

        reply = QMessageBox.question(self, "Confirmer", "Valider définitivement cette liste ? Cette action mettra à jour les stocks.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        with get_db() as db:
            if not db: return
            
            self.current_list = db.merge(self.current_list)
            
            # Process items
            for i in range(self.table.rowCount()):
                result = self.table.item(i, 4).text()
                # Logic:
                # If 'S' or 'X' -> Delete product from location_1
                # If result is a Location Label -> Move product to that location
                # If 'V' -> Do nothing (Confirmed)
                
                # Note: We need to identify the specific product instance.
                # SupplyListItem stores product_code_1 and barcode_1.
                
                item = self.current_list.items[i]
                
                if result in ['S', 'X']:
                    # Delete logic
                    # Find product by barcode and location
                    prod = db.query(Product).join(Location).filter(Product.barcode == item.barcode_1, Location.label == item.location_1).first()
                    if prod:
                        # Check if it's the last one
                        code = prod.code
                        count = db.query(Product).filter(Product.code == code).count()

                        # Update Nomenclature last_edit_date
                        if prod.nomenclature:
                            prod.nomenclature.last_edit_date = datetime.now()
                        
                        db.delete(prod)
                        
                        # Log Event
                        from database.connection import log_event
                        log_event('PRODUCT_DELETED', details=f"Code: {code} (Validation)", source='ValidationWidget')

                        if count == 1:
                            # It was the last one
                            designation = prod.nomenclature.designation if prod.nomenclature else "Inconnu"
                            
                            # Check if already in missing
                            existing_missing = db.query(MissingItem).filter(MissingItem.product_code == code).first()
                            if not existing_missing:
                                new_missing = MissingItem(
                                    product_code=code,
                                    source="Validation",
                                    reported_at=datetime.now()
                                )
                                db.add(new_missing)
                                # We can't easily show a message for each item in a loop, maybe log it or just do it silently.
                                # Or accumulate messages? For now, let's just do it.
                                logger.info(f"Auto-added {designation} to missing list during validation.")
                
                elif result != 'V':
                    # Assume it's a location label
                    new_loc = db.query(Location).filter(Location.label == result).first()
                    if new_loc:
                         prod = db.query(Product).join(Location).filter(Product.barcode == item.barcode_1, Location.label == item.location_1).first()
                         if prod:
                             prod.location_id = new_loc.id
                             # Update Nomenclature last_edit_date
                             if prod.nomenclature:
                                 prod.nomenclature.last_edit_date = datetime.now()
                                 
                             # Log Event
                             from database.connection import log_event
                             log_event('PRODUCT_MOVED', details=f"Code: {prod.code} -> {new_loc.label} (Validation)", source='ValidationWidget')

            # Mark list as validated
            self.current_list.status = 'validated'
            db.commit()
            
            # Log Event
            from database.connection import log_event
            log_event('LIST_VALIDATED', details=str(self.current_list.id), source='ValidationWidget')
        
        QMessageBox.information(self, "Succès", "Validation terminée.")
        self.load_lists()
