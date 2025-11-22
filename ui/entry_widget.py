from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView, QInputDialog, QStyle, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QEvent
from database.connection import get_db
from database.models import Product, SupplyList, SupplyListItem
from sqlalchemy.orm import joinedload
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class EntryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_supply_list = None
        self.init_ui()
        self.load_draft_lists() # Load drafts on init
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

    def init_ui(self):
        layout = QVBoxLayout()

        # Top: Create/Select List
        list_layout = QHBoxLayout()
        
        # Draft Selection
        self.draft_combo = QComboBox()
        self.draft_combo.setPlaceholderText("Reprendre un brouillon...")
        self.draft_combo.setMinimumWidth(200)
        self.draft_combo.currentIndexChanged.connect(self.on_draft_selected)
        list_layout.addWidget(self.draft_combo)
        
        # Delete List Button
        self.delete_list_btn = QPushButton()
        self.delete_list_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.delete_list_btn.setToolTip("Supprimer le brouillon sélectionné")
        self.delete_list_btn.clicked.connect(self.delete_current_list)
        list_layout.addWidget(self.delete_list_btn)
        
        self.list_title_input = QLineEdit()
        self.list_title_input.setPlaceholderText("Titre de la nouvelle liste")
        create_btn = QPushButton("Créer Liste")
        create_btn.clicked.connect(self.create_list)
        list_layout.addWidget(self.list_title_input)
        list_layout.addWidget(create_btn)
        layout.addLayout(list_layout)

        self.current_list_label = QLabel("Aucune liste active")
        layout.addWidget(self.current_list_label)

        # Search Area
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Recherche Produit:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Results Table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Désignation", "Code", "Emplacement", "Date Exp"])
        r_header = self.results_table.horizontalHeader()
        r_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in [1, 2, 3]:
            r_header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.doubleClicked.connect(self.add_to_supply_list)
        self.results_table.verticalHeader().setDefaultSectionSize(48)
        
        # Install Event Filters for Navigation
        self.search_input.installEventFilter(self)
        self.results_table.installEventFilter(self)
        
        layout.addWidget(QLabel("Résultats de recherche (Double-cliquez pour ajouter):"))
        layout.addWidget(self.results_table)

        # Supply List Table
        self.supply_table = QTableWidget()
        self.supply_table.setColumnCount(9)
        self.supply_table.setHorizontalHeaderLabels(["Désignation", "Code Barre 1", "Emplacement 1", "Date Exp 1", "Code Barre 2", "Emplacement 2", "Date Exp 2", "Quantité", "Actions"])
        s_header = self.supply_table.horizontalHeader()
        s_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 9):
            s_header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.supply_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.supply_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.supply_table.verticalHeader().setDefaultSectionSize(48)
        layout.addWidget(QLabel("Contenu de la liste:"))
        layout.addWidget(self.supply_table)

        # Bottom Buttons
        bottom_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("Clôturer la liste")
        self.close_btn.clicked.connect(self.close_list)
        bottom_layout.addWidget(self.close_btn)

        clear_btn = QPushButton("Vider la liste")
        clear_btn.clicked.connect(self.clear_list)
        bottom_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("Exporter Excel")
        export_btn.clicked.connect(self.export_to_excel)
        bottom_layout.addWidget(export_btn)
        
        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress:
            if source == self.search_input:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Down):
                    if self.results_table.rowCount() > 0:
                        self.results_table.setFocus()
                        if self.results_table.currentRow() == -1:
                            self.results_table.selectRow(0)
                        return True
            elif source == self.results_table:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    if self.results_table.currentRow() != -1:
                        if self.add_to_supply_list(self.results_table.currentIndex()):
                            self.search_input.setFocus()
                            self.search_input.selectAll()
                        return True
                elif event.key() == Qt.Key.Key_Up:
                    if self.results_table.currentRow() == 0:
                        self.search_input.setFocus()
                        return True
                        
        return super().eventFilter(source, event)

    def load_draft_lists(self):
        self.draft_combo.blockSignals(True)
        self.draft_combo.clear()
        self.draft_combo.addItem("Sélectionner un brouillon...", None)
        
        db = next(get_db())
        # Fetch lists with status 'draft' or None
        drafts = db.query(SupplyList).filter((SupplyList.status == 'draft') | (SupplyList.status == None)).order_by(SupplyList.created_at.desc()).all()
        
        for d in drafts:
            self.draft_combo.addItem(f"{d.title} ({d.created_at.strftime('%d/%m %H:%M')})", d.id)
            
        self.draft_combo.blockSignals(False)

    def on_draft_selected(self, index):
        if index <= 0:
            return
            
        list_id = self.draft_combo.currentData()
        if not list_id:
            return
            
        db = next(get_db())
        self.current_supply_list = db.query(SupplyList).get(list_id)
        
        if self.current_supply_list:
            self.refresh_supply_table()
            # Update title input just for visual confirmation, but it's for new lists usually
            self.list_title_input.setText(self.current_supply_list.title)

    def create_list(self):
        title = self.list_title_input.text().strip()
        if not title:
            title = f"Liste du {datetime.now().strftime('%d/%m/%Y %H:%M')}"

        db = next(get_db())
        new_list = SupplyList(title=title, status='draft')
        db.add(new_list)
        db.commit()
        
        self.current_supply_list = new_list
        self.current_list_label.setText(f"Liste active: {title} (BROUILLON)")
        self.list_title_input.clear()
        self.refresh_supply_table()
        self.load_draft_lists() # Refresh combo

    def delete_current_list(self):
        if not self.current_supply_list:
            QMessageBox.warning(self, "Attention", "Aucune liste sélectionnée.")
            return

        reply = QMessageBox.question(
            self, "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer la liste '{self.current_supply_list.title}' et tout son contenu ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db = next(get_db())
                # Re-fetch to ensure attached to session
                lst = db.query(SupplyList).get(self.current_supply_list.id)
                if lst:
                    # Delete items first
                    db.query(SupplyListItem).filter(SupplyListItem.supply_list_id == lst.id).delete()
                    db.delete(lst)
                    db.commit()
                    
                    self.current_supply_list = None
                    self.current_list_label.setText("Aucune liste active")
                    self.list_title_input.clear()
                    self.supply_table.setRowCount(0)
                    self.load_draft_lists() # Refresh combo
                    QMessageBox.information(self, "Succès", "Liste supprimée avec succès.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {e}")

    def on_search_text_changed(self):
        self.search_timer.start(300)

    def perform_search(self):
        query_text = self.search_input.text().strip()
        self.results_table.setRowCount(0)
        
        if not query_text:
            return

        db = next(get_db())
        products = db.query(Product).options(joinedload(Product.location)).filter(Product.designation.ilike(f"%{query_text}%")).all()
        
        self.results_table.setRowCount(len(products))
        for row, prod in enumerate(products):
            loc_label = prod.location.label if prod.location else "N/A"
            
            item_desig = QTableWidgetItem(prod.designation)
            item_desig.setData(Qt.ItemDataRole.UserRole, prod) # Store object
            
            self.results_table.setItem(row, 0, item_desig)
            self.results_table.setItem(row, 1, QTableWidgetItem(str(prod.code)))
            self.results_table.setItem(row, 2, QTableWidgetItem(loc_label))
            self.results_table.setItem(row, 3, QTableWidgetItem(str(prod.expiry_date)))

    def add_to_supply_list(self, index):
        if not self.current_supply_list:
            QMessageBox.warning(self, "Attention", "Veuillez d'abord créer une liste.")
            return False

        # Check status
        if self.current_supply_list.status != 'draft' and self.current_supply_list.status is not None:
            QMessageBox.warning(self, "Attention", "Cette liste est clôturée ou validée. Impossible d'ajouter des produits.")
            return False

        row = index.row()
        item1 = self.results_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        # Check for duplicates
        db = next(get_db())
        existing_item = db.query(SupplyListItem).filter(
            SupplyListItem.supply_list_id == self.current_supply_list.id,
            SupplyListItem.product_code_1 == item1.code
        ).first()
        
        if existing_item:
             QMessageBox.warning(self, "Doublon", f"Le produit '{item1.designation}' est déjà dans la liste.")
             return False

        # Ask for Quantity
        qty, ok = QInputDialog.getInt(self, "Quantité", f"Quantité pour {item1.designation}:", 1, 1, 10000)
        if not ok:
            return False

        # Logic for Item 2: "l'element suivant dans la liste des résultats... qui porte la meme designation"
        item2 = None
        if row + 1 < self.results_table.rowCount():
            next_item = self.results_table.item(row + 1, 0).data(Qt.ItemDataRole.UserRole)
            if next_item.designation == item1.designation:
                item2 = next_item

        # Add to DB
        db = next(get_db())
        
        # Fix DetachedInstanceError: Merge the object into the current session
        if self.current_supply_list:
            self.current_supply_list = db.merge(self.current_supply_list)
        
        loc1 = item1.location.label if item1.location else ""
        loc2 = item2.location.label if item2 and item2.location else ""
        
        list_item = SupplyListItem(
            supply_list_id=self.current_supply_list.id,
            product_code_1=item1.code,
            designation_1=item1.designation,
            location_1=loc1,
            barcode_1=item1.barcode,
            expiry_date_1=item1.expiry_date,
            
            product_code_2=item2.code if item2 else None,
            designation_2=item2.designation if item2 else None,
            location_2=loc2 if item2 else None,
            barcode_2=item2.barcode if item2 else None,
            expiry_date_2=item2.expiry_date if item2 else None,
            
            quantity=qty
        )
        
        db.add(list_item)
        db.commit()
        
        self.refresh_supply_table()
        return True

    def refresh_supply_table(self):
        self.supply_table.setRowCount(0)
        if not self.current_supply_list:
            self.current_list_label.setText("Aucune liste active")
            self.close_btn.setEnabled(False)
            return

        # Use a fresh session to get the latest state
        db_gen = get_db()
        db = next(db_gen)
        try:
            # Re-query the list to get fresh data (avoid stale cache from merge)
            current_id = self.current_supply_list.id
            self.current_supply_list = db.query(SupplyList).get(current_id)
            
            if not self.current_supply_list:
                # List might have been deleted?
                self.current_list_label.setText("Liste introuvable")
                self.close_btn.setEnabled(False)
                return

            status_text = "BROUILLON" if self.current_supply_list.status == 'draft' or self.current_supply_list.status is None else "CLÔTURÉE" if self.current_supply_list.status == 'closed' else "VALIDÉE"
            self.current_list_label.setText(f"Liste active: {self.current_supply_list.title} ({status_text})")
            
            self.close_btn.setEnabled(self.current_supply_list.status == 'draft' or self.current_supply_list.status is None)

            items = self.current_supply_list.items
            
            self.supply_table.setRowCount(len(items))
            for row, item in enumerate(items):
                self.supply_table.setItem(row, 0, QTableWidgetItem(item.designation_1))
                self.supply_table.setItem(row, 1, QTableWidgetItem(item.barcode_1))
                self.supply_table.setItem(row, 2, QTableWidgetItem(item.location_1))
                self.supply_table.setItem(row, 3, QTableWidgetItem(str(item.expiry_date_1)))
                self.supply_table.setItem(row, 4, QTableWidgetItem(item.barcode_2 or ""))
                self.supply_table.setItem(row, 5, QTableWidgetItem(item.location_2 or ""))
                self.supply_table.setItem(row, 6, QTableWidgetItem(str(item.expiry_date_2 or "")))
                self.supply_table.setItem(row, 7, QTableWidgetItem(str(item.quantity)))
                
                # Actions: Delete (Only if draft)
                # Treat None as draft for legacy lists
                if self.current_supply_list.status == 'draft' or self.current_supply_list.status is None:
                    del_btn = QPushButton()
                    del_btn.setObjectName("TableActionBtn") # For styling
                    del_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
                    del_btn.setToolTip("Supprimer")
                    del_btn.clicked.connect(lambda checked, i_id=item.id: self.delete_item(i_id))
                    
                    # Center the button
                    widget = QWidget()
                    layout = QHBoxLayout()
                    layout.setContentsMargins(0,0,0,0)
                    layout.addWidget(del_btn)
                    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    widget.setLayout(layout)
                    
                    self.supply_table.setCellWidget(row, 8, widget)
        finally:
            # Close the session (or let the generator finish)
            try:
                next(db_gen)
            except StopIteration:
                pass

    def delete_item(self, item_id):
        print(f"DEBUG: delete_item {item_id} (Type: {type(item_id)}). Status: {self.current_supply_list.status}")
        if self.current_supply_list.status != 'draft' and self.current_supply_list.status is not None:
             print("DEBUG: Delete blocked by status")
             return

        reply = QMessageBox.question(self, "Confirmer", "Supprimer cet article ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            print("DEBUG: User confirmed delete")
            db = next(get_db())
            item = db.query(SupplyListItem).filter(SupplyListItem.id == item_id).first()
            if item:
                db.delete(item)
                db.commit()
                print("DEBUG: Item deleted and committed")
                self.refresh_supply_table()
            else:
                print("DEBUG: Item not found in DB. Existing IDs:")
                all_items = db.query(SupplyListItem).all()
                for i in all_items:
                    print(f" - ID: {i.id}, ListID: {i.supply_list_id}")
        else:
            print("DEBUG: User cancelled delete")

    def clear_list(self):
        if not self.current_supply_list:
            return
        
        print(f"DEBUG: clear_list. Status: {self.current_supply_list.status}")
        if self.current_supply_list.status != 'draft' and self.current_supply_list.status is not None:
             QMessageBox.warning(self, "Attention", "Impossible de vider une liste clôturée.")
             return
            
        reply = QMessageBox.question(self, "Confirmer", "Vider toute la liste ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            print("DEBUG: User confirmed clear")
            db = next(get_db())
            # Delete all items for this list
            deleted_count = db.query(SupplyListItem).filter(SupplyListItem.supply_list_id == self.current_supply_list.id).delete()
            db.commit()
            print(f"DEBUG: Deleted {deleted_count} items and committed")
            self.refresh_supply_table()
        else:
            print("DEBUG: User cancelled clear")

    def close_list(self):
        if not self.current_supply_list:
            return
            
        reply = QMessageBox.question(self, "Confirmer", "Voulez-vous clôturer cette liste ? Elle ne sera plus modifiable.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            db = next(get_db())
            self.current_supply_list = db.merge(self.current_supply_list)
            self.current_supply_list.status = 'closed'
            db.commit()
            self.refresh_supply_table()
            self.load_draft_lists() # Refresh combo
            QMessageBox.information(self, "Succès", "Liste clôturée. Elle est maintenant disponible pour validation.")

    def export_to_excel(self):
        if not self.current_supply_list:
            QMessageBox.warning(self, "Attention", "Aucune liste active.")
            return
            
        db = next(get_db())
        self.current_supply_list = db.merge(self.current_supply_list)
        items = self.current_supply_list.items
        
        if not items:
            QMessageBox.warning(self, "Attention", "La liste est vide.")
            return

        # Prepare data
        data = []
        for item in items:
            # Format Date as MM-YY
            date1 = item.expiry_date_1.strftime('%m-%y') if item.expiry_date_1 else ""
            date2 = item.expiry_date_2.strftime('%m-%y') if item.expiry_date_2 else ""
            
            # Truncate Product Name (Max ~40 chars for width 40.71)
            product_name = item.designation_1
            if product_name and len(product_name) > 40:
                product_name = product_name[:37] + "..."

            data.append({
                "Observ.1": item.barcode_1,
                "Empl.1": item.location_1,
                "Date.1": date1,
                "Qtt": item.quantity,
                "Produit": product_name,
                "Date.2": date2,
                "Empl.2": item.location_2,
                "Observ.2": item.barcode_2
            })
            
        df = pd.DataFrame(data)
        
        # Reorder columns to ensure exact match
        columns_order = ['Observ.1', 'Empl.1', 'Date.1', 'Qtt', 'Produit', 'Date.2', 'Empl.2', 'Observ.2']
        df = df[columns_order]
        
        # Save Dialog
        filename, _ = QFileDialog.getSaveFileName(self, "Exporter Excel", f"Liste_{self.current_supply_list.title}.xlsx", "Excel Files (*.xlsx)")
        if filename:
            try:
                # Save using Pandas first
                df.to_excel(filename, index=False)
                
                # Open with openpyxl to apply styles
                import openpyxl
                wb = openpyxl.load_workbook(filename)
                ws = wb.active
                
                # Apply Column Widths
                ws.column_dimensions['A'].width = 8.71
                ws.column_dimensions['B'].width = 7.71
                ws.column_dimensions['C'].width = 8.71
                ws.column_dimensions['D'].width = 7.71
                ws.column_dimensions['E'].width = 40.71
                ws.column_dimensions['F'].width = 8.71
                ws.column_dimensions['G'].width = 7.71
                ws.column_dimensions['H'].width = 8.71
                
                wb.save(filename)
                
                QMessageBox.information(self, "Succès", f"Liste exportée vers {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {e}")
