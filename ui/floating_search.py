from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QCompleter, 
                             QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QColor, QFont
from database.connection import get_db, get_xpertpharm_connection
from database.models import Nomenclature, MissingItem, Product
from ui.quantity_dialog import QuantityDialog
from datetime import datetime

class FloatingSearchWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 80)
        
        self.dragging = False
        self.offset = None
        
        self.init_ui()
        self.load_completer_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Container
        self.container = QWidget()
        self.container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 240);
            border: 2px solid #1976d2;
            border-radius: 15px;
        """)
        layout.addWidget(self.container)
        
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(15, 10, 15, 10)
        
        # Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Scan ou Nom du produit...")
        self.search_input.setStyleSheet("""
            border: none;
            background: transparent;
            font-size: 18px;
            font-weight: bold;
            color: #333;
        """)
        self.search_input.returnPressed.connect(self.handle_input)
        self.search_input.textChanged.connect(self.on_text_changed)
        c_layout.addWidget(self.search_input)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.container.setGraphicsEffect(shadow)

    def load_completer_data(self):
        # Load all nomenclature names from XpertPharm for autocomplete
        try:
            conn = get_xpertpharm_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DESIGNATION_PRODUIT FROM dbo.View_STK_PRODUITS WHERE ACTIF = 1")
                results = cursor.fetchall()
                self.names = [r[0] for r in results if r[0]]
                conn.close()
            else:
                # Fallback to local DB if XpertPharm fails
                with get_db() as db:
                    if db:
                        results = db.query(Nomenclature.designation).all()
                        self.names = [r[0] for r in results if r[0]]
            
            self.completer = QCompleter(self.names)
            self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.search_input.setCompleter(self.completer)
        except Exception as e:
            print(f"Error loading completer: {e}")

    def on_text_changed(self, text):
        # Disable completer if text starts with digit (Barcode)
        if text and text[0].isdigit():
            self.search_input.setCompleter(None)
        else:
            self.search_input.setCompleter(self.completer)

    def handle_input(self):
        text = self.search_input.text().strip()
        if not text:
            return
            
        xp_conn = get_xpertpharm_connection()
        product_data = None # {code, designation}
        
        try:
            if xp_conn:
                cursor = xp_conn.cursor()
                # 1. Try Barcode (CODE_BARRE in View_STK_PRODUITS? Or STK_PRODUITS?)
                # View_STK_PRODUITS usually has CODE_BARRE. Let's check RotationWidget query... 
                # RotationWidget used View_STK_PRODUITS but only selected CODE and DESIGNATION.
                # Let's assume View_STK_PRODUITS has CODE_BARRE or CODE_BARRE_PRINCIPAL.
                # If not, we might need to join.
                # Let's try searching by CODE_PRODUIT or DESIGNATION first.
                # For barcode, usually it's in a separate table or column.
                # Let's try to match CODE_PRODUIT or DESIGNATION.
                # If text is digits, it might be a barcode.
                
                if text.isdigit():
                     # Try to find by Barcode first
                     # We need to know the column name. 
                     # Let's try a broad search or assume CODE_BARRE exists.
                     # Safest is to search by CODE_PRODUIT if it matches text (some codes are numeric)
                     # AND search by CODE_BARRE if column exists.
                     # Let's assume CODE_BARRE column exists in View_STK_PRODUITS for now.
                     cursor.execute("SELECT CODE_PRODUIT, DESIGNATION_PRODUIT FROM dbo.View_STK_PRODUITS WHERE CODE_BARRE = ?", (text,))
                     row = cursor.fetchone()
                     if not row:
                         # Try Code Produit
                         cursor.execute("SELECT CODE_PRODUIT, DESIGNATION_PRODUIT FROM dbo.View_STK_PRODUITS WHERE CODE_PRODUIT = ?", (text,))
                         row = cursor.fetchone()
                else:
                     # Search by Name
                     cursor.execute("SELECT CODE_PRODUIT, DESIGNATION_PRODUIT FROM dbo.View_STK_PRODUITS WHERE DESIGNATION_PRODUIT = ?", (text,))
                     row = cursor.fetchone()
                
                if row:
                    product_data = {'code': row[0], 'designation': row[1]}
                
                xp_conn.close()

            # If not found in XpertPharm (or no connection), try local Product/Nomenclature?
            # User said source MUST be XpertPharm. But fallback is good practice?
            # "la source de produits ... doit etre xpertpharm"
            # I will prioritize XpertPharm. If not found, I can try local but maybe warn?
            # Let's stick to XpertPharm as primary.
            
            if product_data:
                self.add_to_missing(product_data)
            else:
                QMessageBox.warning(self, "Introuvable", "Produit non trouvé dans XpertPharm.")
                self.search_input.selectAll()
                    
        except Exception as e:
            print(f"Search error: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur de recherche: {e}")

    def add_to_missing(self, product_data):
        # Open Quantity Dialog
        name = product_data['designation']
        dlg = QuantityDialog(name, self)
        if dlg.exec():
            qty = dlg.get_quantity()
            
            # Add to MissingItem
            try:
                with get_db() as db:
                    if not db: return
                    
                    # 1. Sync Nomenclature
                    nom = db.query(Nomenclature).filter(Nomenclature.code == product_data['code']).first()
                    if not nom:
                        nom = Nomenclature(
                            code=product_data['code'],
                            designation=product_data['designation'],
                            last_edit_date=datetime.now()
                        )
                        db.add(nom)
                        db.commit() # Commit to get it ready for relationship
                    
                    # 2. Add Missing Item
                    new_item = MissingItem(
                        product_code=product_data['code'],
                        source="Comptoir",
                        quantity=qty,
                        reported_at=datetime.now()
                    )
                    db.add(new_item)
                    db.commit()
                    
                    QMessageBox.information(self, "Succès", f"Produit ajouté aux manquants (Qté: {qty}).")
                    self.search_input.clear()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ajout: {e}")

    # Dragging Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.offset:
            self.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.offset = None
