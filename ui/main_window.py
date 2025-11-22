from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gravity Stock Manager")
        self.resize(1024, 768)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Initialize Tabs
        self.create_tabs()

    def create_tabs(self):
        # 1. Inventaire
        from ui.inventory_widget import InventoryWidget
        self.inventory_tab = InventoryWidget()
        self.tabs.addTab(self.inventory_tab, "Inventaire")

        # 2. Recherche
        from ui.search_widget import SearchWidget
        self.search_tab = SearchWidget()
        self.tabs.addTab(self.search_tab, "Recherche")

        # 3. Colis
        from ui.parcel_widget import ParcelWidget
        self.parcel_tab = ParcelWidget()
        self.tabs.addTab(self.parcel_tab, "Colis")

        # 4. Manquant
        from ui.missing_widget import MissingWidget
        self.missing_tab = MissingWidget()
        self.tabs.addTab(self.missing_tab, "Manquant")

        # 6. Saisie (Entry)
        from ui.entry_widget import EntryWidget
        self.entry_tab = EntryWidget()
        self.tabs.addTab(self.entry_tab, "Saisie")

        # 7. Validation
        from ui.validation_widget import ValidationWidget
        self.validation_tab = ValidationWidget()
        self.tabs.addTab(self.validation_tab, "Validation")

        # 5. Paramètres
        from ui.settings_widget import SettingsWidget
        self.settings_tab = SettingsWidget()
        self.tabs.addTab(self.settings_tab, "Paramètres")

    def setup_placeholder_tab(self, tab, name):
        layout = QVBoxLayout()
        label = QLabel(f"{name} Module - Coming Soon")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        tab.setLayout(layout)
