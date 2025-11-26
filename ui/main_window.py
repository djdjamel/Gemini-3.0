from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from ui.notification_overlay import NotificationOverlay
from ui.floating_search import FloatingSearchWidget
from database.connection import get_db
from database.models import Notification
from config import config
import logging

class MainWindow(QMainWindow):
    def __init__(self, splash=None):
        super().__init__()
        self.setWindowTitle("Gravity Stock Manager")
        self.resize(1024, 768)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Notification System
        self.active_overlays = []
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_notifications)
        self.notification_timer.start(5000) # Check every 5 seconds
        
        # Floating Search Widget
        self.floating_search = FloatingSearchWidget(self)
        self.floating_search.hide() # Hidden by default
        
        # Toggle Button (e.g., F12 shortcut or just a button in UI? User didn't specify.
        # Let's add a shortcut F12)
        from PyQt6.QtGui import QAction, QKeySequence
        self.toggle_search_action = QAction("Recherche Comptoir", self)
        self.toggle_search_action.setShortcut(QKeySequence("F12"))
        self.toggle_search_action.triggered.connect(self.toggle_floating_search)
        self.addAction(self.toggle_search_action)
        
        # Initialize Tabs synchronously
        self.create_tabs(splash)

    def create_tabs(self, splash=None):
        # Helper to update splash
        def update_splash(message):
            if splash:
                splash.showMessage(message, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
                # Force event processing to ensure splash updates
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()

        # 1. Inventaire
        update_splash("Chargement du module Inventaire...")
        from ui.inventory_widget import InventoryWidget
        self.inventory_tab = InventoryWidget()
        self.tabs.addTab(self.inventory_tab, "Inventaire")

        # 2. Recherche
        update_splash("Chargement du module Recherche...")
        from ui.search_widget import SearchWidget
        self.search_tab = SearchWidget()
        self.tabs.addTab(self.search_tab, "Recherche")

        # 3. Colis
        update_splash("Chargement du module Colis...")
        from ui.parcel_widget import ParcelWidget
        self.parcel_tab = ParcelWidget()
        self.tabs.addTab(self.parcel_tab, "Colis")

        # 4. Manquant
        update_splash("Chargement du module Manquant...")
        from ui.missing_widget import MissingWidget
        self.missing_tab = MissingWidget()
        self.tabs.addTab(self.missing_tab, "Manquant")

        # 6. Saisie (Entry)
        update_splash("Chargement du module Saisie...")
        from ui.entry_widget import EntryWidget
        self.entry_tab = EntryWidget()
        self.tabs.addTab(self.entry_tab, "Saisie")

        # 7. Validation
        update_splash("Chargement du module Validation...")
        from ui.validation_widget import ValidationWidget
        self.validation_tab = ValidationWidget()
        self.tabs.addTab(self.validation_tab, "Validation")

        # 8. Facture
        update_splash("Chargement du module Facture...")
        from ui.invoice_widget import InvoiceWidget
        self.invoice_tab = InvoiceWidget()
        self.tabs.addTab(self.invoice_tab, "Facture")

        # 9. Manquants Xp
        update_splash("Chargement du module Manquants Xp...")
        from ui.xp_missing_widget import XpMissingWidget
        self.xp_missing_tab = XpMissingWidget()
        self.tabs.addTab(self.xp_missing_tab, "Manquants Xp")

        # 10. Rotation
        update_splash("Chargement du module Rotation...")
        from ui.rotation_widget import RotationWidget
        self.rotation_tab = RotationWidget()
        self.tabs.addTab(self.rotation_tab, "Rotation")

        # 11. Produits Dormants
        update_splash("Chargement du module Produits Dormants...")
        from ui.dormant_widget import DormantWidget
        self.dormant_tab = DormantWidget()
        self.tabs.addTab(self.dormant_tab, "Produits Dormants")

        # 12. Nomenclature
        update_splash("Chargement du module Nomenclature...")
        from ui.nomenclature_widget import NomenclatureWidget
        self.nomenclature_tab = NomenclatureWidget()
        self.tabs.addTab(self.nomenclature_tab, "Nomenclature")

        # 13. Paramètres
        update_splash("Chargement du module Paramètres...")
        from ui.settings_widget import SettingsWidget
        self.settings_tab = SettingsWidget()
        self.tabs.addTab(self.settings_tab, "Paramètres")

        # 14. Messages
        update_splash("Chargement du module Messages...")
        from ui.messages_widget import MessagesWidget
        self.messages_tab = MessagesWidget()
        self.tabs.addTab(self.messages_tab, "Messages")

    def check_notifications(self):
        try:
            with get_db() as db:
                if not db: return
                
                # Server Logic: Check for pending requests
                if config.IS_SERVER:
                    pending = db.query(Notification).filter(Notification.status == 'pending').all()
                    for notif in pending:
                        # Check if already showing this notif (simple check)
                        if not any(o.notification_data['id'] == notif.id for o in self.active_overlays):
                            self.show_notification(notif)
                
                # Client Logic: Check for responses to my requests
                my_station = config.STATION_NAME
                if my_station:
                    responses = db.query(Notification).filter(
                        Notification.sender_station == my_station,
                        Notification.status.in_(['confirmed', 'rejected'])
                    ).all()
                    
                    for resp in responses:
                        msg = f"Votre demande pour '{resp.product_name}' a été {'CONFIRMÉE' if resp.status == 'confirmed' else 'REJETÉE'}."
                        QMessageBox.information(self, "Réponse Serveur", msg)
                        
                        # Mark as seen (closed)
                        resp.status = 'closed'
                        db.commit()

        except Exception as e:
            logging.error(f"Notification check error: {e}")

    def show_notification(self, notif):
        data = {
            'id': notif.id,
            'sender_station': notif.sender_station,
            'product_name': notif.product_name,
            'quantity': notif.quantity,
            'message': notif.message,
            'is_urgent': notif.is_urgent
        }
        overlay = NotificationOverlay(data, self)
        overlay.responded.connect(self.handle_notification_response)
        overlay.show()
        
        # Stack overlays
        offset = len(self.active_overlays) * 20
        overlay.move(100 + offset, 100 + offset)
        
        self.active_overlays.append(overlay)

    def handle_notification_response(self, notif_id, action):
        # Remove from active list
        self.active_overlays = [o for o in self.active_overlays if o.notification_data['id'] != notif_id]
        
        try:
            with get_db() as db:
                if db:
                    notif = db.query(Notification).filter(Notification.id == notif_id).first()
                    if notif:
                        notif.status = action
                        db.commit()
        except Exception as e:
            logging.error(f"Error updating notification: {e}")

    def toggle_floating_search(self):
        if self.floating_search.isVisible():
            self.floating_search.hide()
        else:
            self.floating_search.show()
            self.floating_search.search_input.setFocus()
            # Center on screen or position nicely
            # self.floating_search.move(100, 100)
