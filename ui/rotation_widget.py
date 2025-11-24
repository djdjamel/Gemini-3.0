from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QMessageBox, QApplication, QFrame, QStyle,
    QLineEdit, QCompleter, QStyledItemDelegate, QListView, QProgressDialog
)
from PyQt6.QtCore import Qt, QStringListModel, QEvent, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QPalette, QFont
from database.connection import get_xpertpharm_connection
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class CheckableComboBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QStandardItemModel(self))
        self.view().setModel(self.model())
        self.setEditable(False) # Not editable, just selectable

    def handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)
        self.update_text()

    def addItem(self, text, data=None):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        item.setData(data, Qt.ItemDataRole.UserRole)
        self.model().appendRow(item)

    def update_text(self):
        # We don't change the display text of the combo box itself to list all items 
        # because it might be too long. We can show "X selected" or similar.
        # For now, let's just keep the default behavior which shows the current index text,
        # but that's confusing for multi-select.
        # Better approach: Set the line edit text (if editable) or use a custom paint.
        # Simple hack: Set the current index to -1 or something to show a placeholder?
        # Actually, let's just update the tooltip or something.
        # Or, we can set the text of the first item to "X selected" if we want.
        pass

    def get_checked_data(self):
        checked_data = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_data.append(item.data(Qt.ItemDataRole.UserRole))
        return checked_data

    def get_checked_texts(self):
        checked_texts = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_texts.append(item.text())
        return checked_texts
        
    def hidePopup(self):
        # Don't hide popup when clicking items
        # But we need to hide it when clicking outside.
        # The default behavior hides it on click.
        # We need to override this.
        # Actually, simpler: keep it open? 
        # A common workaround is to capture the event.
        # For simplicity in this iteration, we let it close and user re-opens, 
        # OR we try to keep it open.
        # Let's try to keep it open.
        super().hidePopup()

    # To really make it stay open is complex in Qt. 
    # Let's stick to standard behavior: click -> toggle -> close. 
    # User has to re-open to select another. It's annoying but safe.
    # IMPROVEMENT: Use a QListWidget in a menu for better UX if requested.
    # For now, standard behavior.

class RotationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_product_code = None
        self.init_ui()
        self.load_years()
        self.load_months()
        # Load products after UI init to avoid blocking
        QTimer.singleShot(100, self.load_products)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Top Bar: Parameters
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        
        # Product Search (Merged)
        l_prod = QLabel("Produit:")
        l_prod.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(l_prod)
        
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.product_combo.setFixedWidth(400)
        
        # Setup Completer for better search experience
        completer = QCompleter(self.product_combo.model())
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.product_combo.setCompleter(completer)
        
        self.product_combo.currentIndexChanged.connect(self.on_product_selected)
        top_layout.addWidget(self.product_combo)

        # Year
        l_year = QLabel("Année:")
        l_year.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(l_year)
        self.year_combo = QComboBox()
        self.year_combo.setFixedWidth(80)
        top_layout.addWidget(self.year_combo)
        
        # Months
        l_month = QLabel("Mois:")
        l_month.setStyleSheet("font-weight: bold;")
        top_layout.addWidget(l_month)
        self.month_combo = CheckableComboBox()
        self.month_combo.setFixedWidth(150)
        self.month_combo.setPlaceholderText("Sélectionner mois")
        top_layout.addWidget(self.month_combo)
        
        # Analyze Button
        analyze_btn = QPushButton("Analyser")
        analyze_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 5px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        analyze_btn.clicked.connect(self.run_analysis)
        top_layout.addWidget(analyze_btn)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # Table
        self.table = QTableWidget()
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
        
        # Stock Label
        self.stock_label = QLabel("Stock Actuel: -")
        self.stock_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-top: 5px;")
        layout.addWidget(self.stock_label)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def load_years(self):
        current_year = datetime.now().year
        for year in range(current_year, 2019, -1):
            self.year_combo.addItem(str(year), year)

    def load_months(self):
        months = [
            (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"),
            (5, "Mai"), (6, "Juin"), (7, "Juillet"), (8, "Août"),
            (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre")
        ]
        for m_id, m_name in months:
            self.month_combo.addItem(m_name, m_id)

    def load_products(self):
        self.status_label.setText("Chargement des produits...")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()
        
        try:
            conn = get_xpertpharm_connection()
            if not conn:
                self.status_label.setText("Erreur de connexion XpertPharm.")
                return
            
            cursor = conn.cursor()
            # SELECT [CODE_PRODUIT], [DESIGNATION_PRODUIT] ... FROM dbo.View_STK_PRODUIT WHERE [ACTIF] = 1
            sql = """
                SELECT CODE_PRODUIT, DESIGNATION_PRODUIT 
                FROM dbo.View_STK_PRODUITS 
                WHERE ACTIF = 1
                ORDER BY DESIGNATION_PRODUIT
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            self.product_combo.clear()
            for row in rows:
                # row[0] = CODE, row[1] = DESIGNATION
                self.product_combo.addItem(f"{row[1]}", row[0])
                
            conn.close()
            
            # Update completer model
            if self.product_combo.completer():
                self.product_combo.completer().setModel(self.product_combo.model())
                
            self.status_label.setText(f"{len(rows)} produits chargés.")
                
        except Exception as e:
            logger.error(f"Load products error: {e}")
            self.status_label.setText("Erreur lors du chargement des produits.")
        finally:
            QApplication.restoreOverrideCursor()

    def on_product_selected(self):
        self.selected_product_code = self.product_combo.currentData()

    def run_analysis(self):
        if not self.selected_product_code:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un produit.")
            return

        year = self.year_combo.currentData()
        selected_months = self.month_combo.get_checked_data()
        
        if not selected_months:
            mois_str = '' 
        else:
            mois_str = ','.join(map(str, selected_months))

        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.status_label.setText("Analyse en cours...")
        self.stock_label.setText("Stock Actuel: -")
        
        # Progress Dialog
        progress = QProgressDialog("Analyse en cours...", None, 0, 0, self)
        progress.setWindowTitle("Veuillez patienter")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents()

        try:
            sql_file_path = os.path.join(os.getcwd(), "rotation.sql")
            if not os.path.exists(sql_file_path):
                 progress.close()
                 QMessageBox.critical(self, "Erreur", f"Fichier SQL introuvable: {sql_file_path}")
                 return

            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_query = f.read()

            # Replace parameters
            import re
            sql_query = re.sub(r"DECLARE @EXERCICE varchar\(4\) = '[^']*';", f"DECLARE @EXERCICE varchar(4) = '{year}';", sql_query)
            sql_query = re.sub(r"DECLARE @CODE_PRODUIT varchar\(32\) = NULL;", f"DECLARE @CODE_PRODUIT varchar(32) = '{self.selected_product_code}';", sql_query)
            sql_query = re.sub(r"DECLARE @MOIS varchar\(100\) = '';", f"DECLARE @MOIS varchar(100) = '{mois_str}';", sql_query)

            conn = get_xpertpharm_connection()
            if not conn:
                progress.close()
                QMessageBox.critical(self, "Erreur", "Impossible de se connecter à XpertPharm.")
                return
            
            cursor = conn.cursor()
            cursor.execute(sql_query)
            
            rows = cursor.fetchall()
            
            # Columns: PRODUIT, MOIS, QUANTITE_VENDU
            columns = ["Produit", "Mois", "Quantité"]
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            
            self.table.setRowCount(len(rows))
            total_qty = 0
            
            for r, row in enumerate(rows):
                # row[0]=Code, row[1]=Produit, row[2]=Qty, row[3]=Mois
                
                self.table.setItem(r, 0, QTableWidgetItem(str(row[1]))) # Produit
                self.table.setItem(r, 1, QTableWidgetItem(str(row[3]))) # Mois
                
                qty = row[2] if row[2] is not None else 0
                total_qty += qty
                
                qty_item = QTableWidgetItem(str(qty))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(r, 2, qty_item) # Quantité
            
            # Add Total Row
            self.table.insertRow(len(rows))
            total_label_item = QTableWidgetItem("TOTAL")
            total_label_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_label_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.table.setItem(len(rows), 1, total_label_item)
            
            total_qty_item = QTableWidgetItem(str(total_qty))
            total_qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            total_qty_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.table.setItem(len(rows), 2, total_qty_item)
            
            # Resize columns
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            
            # Fetch Stock Quantity
            stock_sql = f"""
              DECLARE @CODE_PRODUIT varchar(32) = '{self.selected_product_code}';

              SELECT
                  ISNULL(stk.QTE_STOCK_TOTAL, 0) AS QTE_STOCK_TOTAL
              FROM dbo.STK_PRODUITS AS p
              LEFT JOIN (
                  SELECT CODE_PRODUIT, SUM(QUANTITE) AS QTE_STOCK_TOTAL
                  FROM dbo.STK_STOCK
                  WHERE (DATE_PEREMPTION > GETDATE() OR DATE_PEREMPTION IS NULL)
                      AND CODE_PRODUIT = @CODE_PRODUIT
                  GROUP BY CODE_PRODUIT
              ) AS stk ON stk.CODE_PRODUIT = p.CODE_PRODUIT
              WHERE p.CODE_PRODUIT = @CODE_PRODUIT;
            """
            cursor.execute(stock_sql)
            stock_row = cursor.fetchone()
            if stock_row:
                self.stock_label.setText(f"Stock Actuel: {stock_row[0]}")
            else:
                self.stock_label.setText("Stock Actuel: 0")
            
            conn.close()
            self.status_label.setText(f"Analyse terminée. {len(rows)} lignes.")

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            self.status_label.setText("Erreur lors de l'analyse.")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'exécution: {e}")
        finally:
            progress.close()
            QApplication.restoreOverrideCursor()
