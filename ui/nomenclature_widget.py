from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QMessageBox, QApplication, QFrame, QStyle,
    QProgressDialog, QDialog, QDialogButtonBox, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from database.connection import get_db, get_xpertpharm_connection
from database.models import Nomenclature
from sqlalchemy import func
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NomenclatureWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Debounce timer for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.interval = 300
        self.search_timer.timeout.connect(self.load_data)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Top Bar
        top_layout = QHBoxLayout()
        
        # Search
        l_search = QLabel("Rechercher:")
        top_layout.addWidget(l_search)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Code ou Désignation...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        top_layout.addWidget(self.search_input)
        
        top_layout.addStretch()
        
        # Buttons
        self.btn_obsolete = QPushButton("Vérifier Codes Obsolètes")
        self.btn_obsolete.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning))
        self.btn_obsolete.clicked.connect(self.check_obsolete)
        top_layout.addWidget(self.btn_obsolete)
        
        self.btn_sync = QPushButton("Synchroniser Noms")
        self.btn_sync.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.btn_sync.clicked.connect(self.sync_names)
        top_layout.addWidget(self.btn_sync)
        
        layout.addLayout(top_layout)

        # Table
        self.table = QTableWidget()
        columns = ["Code", "Désignation", "Dernière Modif"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        self.table.cellDoubleClicked.connect(self.edit_product)
        layout.addWidget(self.table)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        
        # Initial Load
        QTimer.singleShot(100, self.load_data)

    def on_search_text_changed(self):
        self.search_timer.start()

    def load_data(self):
        query_text = self.search_input.text().strip()
        
        try:
            with get_db() as db:
                if not db: return
                
                query = db.query(Nomenclature)
                
                if query_text:
                    query = query.filter(
                        (Nomenclature.code.ilike(f"%{query_text}%")) | 
                        (Nomenclature.designation.ilike(f"%{query_text}%"))
                    )
                
                query = query.order_by(Nomenclature.designation.asc()).limit(500) # Limit for performance
                results = query.all()
                
                self.table.setRowCount(len(results))
                for r, row in enumerate(results):
                    self.table.setItem(r, 0, QTableWidgetItem(str(row.code)))
                    self.table.setItem(r, 1, QTableWidgetItem(str(row.designation)))
                    self.table.setItem(r, 2, QTableWidgetItem(str(row.last_edit_date or "")))
                
                self.status_label.setText(f"{len(results)} produits affichés.")
            
        except Exception as e:
            logger.error(f"Error loading nomenclature: {e}")
            self.status_label.setText("Erreur de chargement.")

    def edit_product(self, row, column):
        code_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)
        if not code_item or not name_item:
            return
            
        code = code_item.text()
        current_name = name_item.text()
        
        dialog = ProductEditDialog(code, current_name, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = dialog.name_input.text().strip()
            # Code is read-only in this dialog for safety
            
            if new_name and new_name != current_name:
                try:
                    with get_db() as db:
                        if db:
                            nom = db.query(Nomenclature).filter(Nomenclature.code == code).first()
                            if nom:
                                nom.designation = new_name
                                nom.last_edit_date = datetime.now()
                                db.commit()
                                self.load_data()
                                QMessageBox.information(self, "Succès", "Désignation mise à jour.")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour: {e}")



    def check_obsolete(self):
        progress = QProgressDialog("Vérification des codes...", None, 0, 0, self)
        progress.setWindowTitle("Veuillez patienter")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            # 1. Get Local Codes
            with get_db() as db:
                if not db:
                    progress.close()
                    return
                    
                local_codes = [r[0] for r in db.query(Nomenclature.code).all()]
                local_set = set(local_codes)
                
                # 2. Get XP Codes
                conn = get_xpertpharm_connection()
                if not conn:
                    progress.close()
                    QMessageBox.critical(self, "Erreur", "Impossible de se connecter à XpertPharm.")
                    return
                    
                cursor = conn.cursor()
                cursor.execute("SELECT CODE_PRODUIT FROM dbo.View_STK_PRODUITS")
                xp_codes = [r[0] for r in cursor.fetchall()]
                xp_set = set(xp_codes)
                conn.close()
                
                # 3. Diff
                obsolete_codes = local_set - xp_set
                
                progress.close()
                
                if not obsolete_codes:
                    QMessageBox.information(self, "Résultat", "Aucun code obsolète trouvé.")
                    return
                    
                # Show Dialog
                self.show_results_dialog("Codes Obsolètes", ["Code", "Désignation (Local)"], obsolete_codes, db)
            
        except Exception as e:
            progress.close()
            logger.error(f"Error checking obsolete: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur: {e}")

    def sync_names(self):
        progress = QProgressDialog("Synchronisation des noms...", None, 0, 0, self)
        progress.setWindowTitle("Veuillez patienter")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        
        try:
            # 1. Get Local Data
            with get_db() as db:
                if not db:
                    progress.close()
                    return
                    
                local_noms = db.query(Nomenclature).all()
                local_map = {n.code: n for n in local_noms}
                
                # 2. Get XP Data
                conn = get_xpertpharm_connection()
                if not conn:
                    progress.close()
                    QMessageBox.critical(self, "Erreur", "Impossible de se connecter à XpertPharm.")
                    return
                    
                cursor = conn.cursor()
                cursor.execute("SELECT CODE_PRODUIT, DESIGNATION FROM dbo.View_STK_PRODUITS")
                xp_data = cursor.fetchall()
                conn.close()
                
                updates = []
                
                for row in xp_data:
                    code = row[0]
                    xp_name = row[1]
                    
                    if code in local_map:
                        local_nom = local_map[code]
                        if local_nom.designation != xp_name:
                            # Update
                            old_name = local_nom.designation
                            local_nom.designation = xp_name
                            local_nom.last_edit_date = datetime.now()
                            updates.append((code, old_name, xp_name))
                
                if updates:
                    db.commit()
                    progress.close()
                    self.show_sync_results(updates)
                    self.load_data()
                else:
                    progress.close()
                    QMessageBox.information(self, "Résultat", "Tous les noms sont à jour.")
                
        except Exception as e:
            progress.close()
            logger.error(f"Error syncing names: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur: {e}")

    def show_results_dialog(self, title, columns, codes, db):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Fetch designations for codes
        # We can't do WHERE IN with a huge list easily in one go if list is massive, but for now assume it fits
        # Or just loop (slow) or fetch all local again.
        # Since we have `db` session open, let's query.
        
        # Optimization: Query only needed codes
        # If list is huge, chunk it.
        
        code_list = list(codes)
        rows_data = []
        
        # Simple approach: fetch all local map again or filter
        # Let's just fetch relevant ones
        
        # If > 1000 items, might be issue with IN clause limits in some DBs, but Postgres handles large INs okay usually.
        # Let's cap display at 1000
        
        display_codes = code_list[:1000]
        
        noms = db.query(Nomenclature).filter(Nomenclature.code.in_(display_codes)).all()
        nom_map = {n.code: n.designation for n in noms}
        
        table.setRowCount(len(display_codes))
        for r, code in enumerate(display_codes):
            table.setItem(r, 0, QTableWidgetItem(str(code)))
            table.setItem(r, 1, QTableWidgetItem(str(nom_map.get(code, "Unknown"))))
            
        layout.addWidget(table)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dialog.close)
        layout.addWidget(btns)
        
        dialog.setLayout(layout)
        dialog.exec()

    def show_sync_results(self, updates):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Synchronisation ({len(updates)} mises à jour)")
        dialog.resize(800, 500)
        
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Code", "Ancien Nom", "Nouveau Nom (XP)"])
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        table.setRowCount(len(updates))
        for r, (code, old, new) in enumerate(updates):
            table.setItem(r, 0, QTableWidgetItem(str(code)))
            table.setItem(r, 1, QTableWidgetItem(str(old)))
            table.setItem(r, 2, QTableWidgetItem(str(new)))
            
            # Style
            table.item(r, 1).setForeground(QColor("red"))
            table.item(r, 2).setForeground(QColor("green"))
            
        layout.addWidget(table)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dialog.close)
        layout.addWidget(btns)
        
        dialog.setLayout(layout)
        dialog.exec()

class ProductEditDialog(QDialog):
    def __init__(self, code, name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Éditer Produit")
        self.setModal(True)
        self.resize(400, 150)
        
        layout = QVBoxLayout()
        
        # Code
        layout.addWidget(QLabel("Code Produit:"))
        self.code_input = QLineEdit(code)
        self.code_input.setReadOnly(True) # Prevent changing PK for now
        self.code_input.setStyleSheet("background-color: #f0f0f0; color: #666;")
        layout.addWidget(self.code_input)
        
        # Name
        layout.addWidget(QLabel("Désignation:"))
        self.name_input = QLineEdit(name)
        layout.addWidget(self.name_input)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
