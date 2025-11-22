from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
from database.connection import get_db
from database.models import Location

class ChangeLocationDialog(QDialog):
    def __init__(self, current_location_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Changer l'emplacement")
        self.setFixedSize(300, 150)
        self.selected_location_id = None

        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Nouvel emplacement:"))
        self.location_combo = QComboBox()
        self.load_locations(current_location_id)
        layout.addWidget(self.location_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def load_locations(self, current_id):
        db = next(get_db())
        locations = db.query(Location).order_by(Location.label).all()
        for loc in locations:
            if loc.id != current_id:
                self.location_combo.addItem(loc.label, loc.id)

    def accept(self):
        self.selected_location_id = self.location_combo.currentData()
        super().accept()
