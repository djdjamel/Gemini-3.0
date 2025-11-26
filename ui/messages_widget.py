from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLabel, QDateEdit, 
                             QComboBox, QPushButton, QAbstractItemView)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from database.connection import get_db
from database.models import Notification
from config import config
from sqlalchemy import or_, desc

class MessagesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_messages()

    def showEvent(self, event):
        self.load_messages()
        super().showEvent(event)

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Filters
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Du:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.dateChanged.connect(self.load_messages)
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("Au:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_messages)
        filter_layout.addWidget(self.date_to)
        
        filter_layout.addWidget(QLabel("Statut:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tous", "En attente", "Confirmé", "Rejeté"])
        self.status_filter.currentTextChanged.connect(self.load_messages)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["Tous", "Reçus", "Envoyés"])
        self.type_filter.currentTextChanged.connect(self.load_messages)
        filter_layout.addWidget(self.type_filter)
        
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.clicked.connect(self.load_messages)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Date", "Type", "De/Vers", "Produit", "Qté", "Message", "Urgent", "Statut"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.setLayout(layout)

    def load_messages(self):
        try:
            with get_db() as db:
                if not db: return
                
                query = db.query(Notification)
                
                # Date Filter
                d_from = self.date_from.date().toPyDate()
                d_to = self.date_to.date().addDays(1).toPyDate() # Include end date
                query = query.filter(Notification.created_at >= d_from, Notification.created_at < d_to)
                
                # Status Filter
                status_map = {
                    "En attente": "pending",
                    "Confirmé": "confirmed",
                    "Rejeté": "rejected"
                }
                status_txt = self.status_filter.currentText()
                if status_txt in status_map:
                    query = query.filter(Notification.status == status_map[status_txt])
                    
                # Type Filter
                my_station = config.STATION_NAME or "Unknown"
                type_txt = self.type_filter.currentText()
                
                if type_txt == "Reçus":
                    # If I am server, I receive everything sent to SERVER (or explicitly to me if we had that)
                    # But currently target_role is SERVER.
                    if config.IS_SERVER:
                        query = query.filter(Notification.target_role == 'SERVER')
                    else:
                        # Clients don't really receive requests, they receive responses.
                        # But let's show responses as "Received" updates?
                        # Or maybe "Reçus" means requests sent TO me?
                        # For now, let's assume "Reçus" means I am the target.
                        # Since clients aren't targets of requests, this might be empty for them unless we count responses.
                        # Let's stick to: Reçus = I am target (Server only basically), Envoyés = I am sender.
                        pass
                elif type_txt == "Envoyés":
                    query = query.filter(Notification.sender_station == my_station)
                else:
                    # Tous: Show both Sent by me AND Received by me (if Server)
                    conditions = [Notification.sender_station == my_station]
                    if config.IS_SERVER:
                        conditions.append(Notification.target_role == 'SERVER')
                    query = query.filter(or_(*conditions))

                # Order by date desc
                items = query.order_by(desc(Notification.created_at)).all()
                
                self.table.setRowCount(len(items))
                for row, item in enumerate(items):
                    # Determine Type (Sent/Received)
                    is_sent = item.sender_station == my_station
                    type_str = "Envoyé" if is_sent else "Reçu"
                    
                    # De/Vers
                    other_party = "Serveur" if is_sent else item.sender_station
                    
                    # Date
                    date_str = item.created_at.strftime("%d/%m/%Y %H:%M")
                    
                    self.table.setItem(row, 0, QTableWidgetItem(date_str))
                    self.table.setItem(row, 1, QTableWidgetItem(type_str))
                    self.table.setItem(row, 2, QTableWidgetItem(other_party))
                    self.table.setItem(row, 3, QTableWidgetItem(item.product_name))
                    self.table.setItem(row, 4, QTableWidgetItem(str(item.quantity)))
                    self.table.setItem(row, 5, QTableWidgetItem(item.message))
                    
                    urgent_item = QTableWidgetItem("OUI" if item.is_urgent else "NON")
                    if item.is_urgent:
                        urgent_item.setForeground(QColor("red"))
                        urgent_item.setBackground(QColor("#ffebee"))
                    self.table.setItem(row, 6, urgent_item)
                    
                    status_item = QTableWidgetItem(item.status.upper())
                    if item.status == 'confirmed':
                        status_item.setForeground(QColor("green"))
                    elif item.status == 'rejected':
                        status_item.setForeground(QColor("red"))
                    self.table.setItem(row, 7, status_item)

        except Exception as e:
            print(f"Error loading messages: {e}")
