from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QMessageBox, QApplication, QFrame, QStyle
)
from PyQt6.QtCore import Qt
from database.connection import get_xpertpharm_connection
import logging
import os

logger = logging.getLogger(__name__)

class XpMissingWidget(QWidget):
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
        
        # Nb Jours
        l1 = QLabel("Jours à analyser:")
        l1.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(l1)
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(7)
        self.days_spin.setFixedWidth(60)
        top_layout.addWidget(self.days_spin)
        
        # Stock Min
        l2 = QLabel("Stock Min:")
        l2.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(l2)
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 1000)
        self.min_stock_spin.setValue(0)
        self.min_stock_spin.setFixedWidth(60)
        top_layout.addWidget(self.min_stock_spin)
        
        # Stock Max
        l3 = QLabel("Stock Max:")
        l3.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(l3)
        self.max_stock_spin = QSpinBox()
        self.max_stock_spin.setRange(0, 1000)
        self.max_stock_spin.setValue(6)
        self.max_stock_spin.setFixedWidth(60)
        top_layout.addWidget(self.max_stock_spin)
        
        # Search Button
        search_btn = QPushButton("Lancer la recherche")
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
        search_btn.clicked.connect(self.run_query)
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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Désignation", "Stock", "Dernière Vente", "Vendu Par"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
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

    def run_query(self):
        self.table.setRowCount(0)
        self.status_label.setText("Recherche en cours...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents() # Force UI update
        
        try:
            nb_jours = self.days_spin.value()
            stock_min = self.min_stock_spin.value()
            stock_max = self.max_stock_spin.value()
            
            sql_file_path = os.path.join(os.getcwd(), "manquants.sql")
            if not os.path.exists(sql_file_path):
                 QMessageBox.critical(self, "Erreur", f"Fichier SQL introuvable: {sql_file_path}")
                 return

            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_query = f.read()
                
            import re
            sql_query = re.sub(r"DECLARE @NbJours INT = \d+;", f"DECLARE @NbJours INT = {nb_jours};", sql_query)
            sql_query = re.sub(r"DECLARE @StockMin INT = \d+;", f"DECLARE @StockMin INT = {stock_min};", sql_query)
            sql_query = re.sub(r"DECLARE @StockMax INT = \d+;", f"DECLARE @StockMax INT = {stock_max};", sql_query)
            
            conn = get_xpertpharm_connection()
            if not conn:
                QMessageBox.critical(self, "Erreur", "Impossible de se connecter à XpertPharm.")
                return
                
            cursor = conn.cursor()
            cursor.execute(sql_query)
            
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            
            for r, row in enumerate(rows):
                self.table.setItem(r, 0, QTableWidgetItem(str(row[3]))) # Designation Produit
                
                # Center align numbers
                stock_item = QTableWidgetItem(str(row[4]))
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, 1, stock_item) # Stock
                
                self.table.setItem(r, 2, QTableWidgetItem(str(row[1]))) # Date Doc
                self.table.setItem(r, 3, QTableWidgetItem(str(row[2]))) # Created By
                
            conn.close()
            self.status_label.setText(f"{len(rows)} résultats trouvés.")
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            self.status_label.setText("Erreur lors de la recherche.")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'exécution: {e}")
        finally:
            QApplication.restoreOverrideCursor()
