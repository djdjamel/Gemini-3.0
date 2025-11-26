from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QMessageBox, QApplication, QFrame, QStyle,
    QProgressDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database.connection import get_db
from database.models import Nomenclature, Product
from sqlalchemy import func, text
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DormantWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Top Bar: Parameters
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        
        # Field Selection
        l_field = QLabel("Critère:")
        l_field.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(l_field)
        
        self.field_combo = QComboBox()
        self.field_combo.addItem("Dernier Approvisionnement", "last_supply_date")
        self.field_combo.addItem("Dernière Recherche", "last_search_date")
        self.field_combo.addItem("Dernière Modification", "last_edit_date")
        self.field_combo.setFixedWidth(200)
        top_layout.addWidget(self.field_combo)
        
        # Interval
        l_days = QLabel("Jours inactifs >=")
        l_days.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(l_days)
        
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 3650) # Up to 10 years
        self.days_spin.setValue(30)
        self.days_spin.setFixedWidth(80)
        top_layout.addWidget(self.days_spin)
        
        # Search Button
        search_btn = QPushButton("Rechercher")
        search_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.clicked.connect(self.run_search)
        top_layout.addWidget(search_btn)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Table
        self.table = QTableWidget()
        columns = ["Code", "Désignation", "Jours inactifs", "Nb Emplacements"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
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
        layout.addWidget(self.table)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def run_search(self):
        self.table.setRowCount(0)
        self.status_label.setText("Recherche en cours...")
        
        field_name = self.field_combo.currentData()
        min_days = self.days_spin.value()
        
        # Progress Dialog
        progress = QProgressDialog("Recherche des produits dormants...", None, 0, 0, self)
        progress.setWindowTitle("Veuillez patienter")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        
        try:
            with get_db() as db:
                if not db: return
                
                # Calculate cutoff date
                cutoff_date = datetime.now() - timedelta(days=min_days)
                
                # Query:
                # Select Nomenclature where field <= cutoff OR field IS NULL
                # Join Product to count locations
                
                # Dynamic field selection
                target_field = getattr(Nomenclature, field_name)
                
                from sqlalchemy import or_
                
                query = db.query(
                    Nomenclature.code,
                    Nomenclature.designation,
                    target_field,
                    func.count(Product.id).label("location_count")
                ).outerjoin(Product, Nomenclature.code == Product.code)\
                 .filter(or_(target_field <= cutoff_date, target_field == None))\
                 .group_by(Nomenclature.id)\
                 .having(func.count(Product.id) > 0)\
                 .order_by(target_field.asc().nullsfirst()) # Nulls (Never) first
                
                results = query.all()
                
                self.table.setRowCount(len(results))
                
                for r, row in enumerate(results):
                    # row: (code, designation, date, count)
                    
                    code = row[0]
                    designation = row[1]
                    date_val = row[2]
                    loc_count = row[3]
                    
                    # Calculate days inactive
                    if date_val:
                        days_inactive = (datetime.now() - date_val).days
                        days_str = str(days_inactive)
                    else:
                        days_str = "Jamais"
                    
                    self.table.setItem(r, 0, QTableWidgetItem(str(code)))
                    self.table.setItem(r, 1, QTableWidgetItem(str(designation)))
                    
                    days_item = QTableWidgetItem(days_str)
                    days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(r, 2, days_item)
                    
                    count_item = QTableWidgetItem(str(loc_count))
                    count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(r, 3, count_item)
                
                self.status_label.setText(f"{len(results)} produits trouvés.")
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.status_label.setText("Erreur lors de la recherche.")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'exécution: {e}")
        finally:
            progress.close()
            QApplication.restoreOverrideCursor()
