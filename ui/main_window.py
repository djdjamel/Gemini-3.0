from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer

class MainWindow(QMainWindow):
    def __init__(self, splash=None):
        super().__init__()
        self.setWindowTitle("Gravity Stock Manager")
        self.resize(1024, 768)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
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

        # 5. Paramètres
        update_splash("Chargement du module Paramètres...")
        from ui.settings_widget import SettingsWidget
        self.settings_tab = SettingsWidget()
        self.tabs.addTab(self.settings_tab, "Paramètres")

    def setup_placeholder_tab(self, tab, name):
        layout = QVBoxLayout()
        label = QLabel(f"{name} Module - Coming Soon")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        tab.setLayout(layout)
