from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, 
    QScrollArea, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from database.connection import get_db
from database.models import EventLog, MissingItem, SupplyList, SupplyListItem
from sqlalchemy import func
from datetime import datetime, timedelta, date

class TimelineWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(200)
        self.events = []
        self.start_hour = 8
        self.end_hour = 18
        
    def set_events(self, events):
        self.events = events
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Margins
        margin_left = 50
        margin_right = 20
        margin_top = 30
        margin_bottom = 30
        
        draw_width = width - margin_left - margin_right
        draw_height = height - margin_top - margin_bottom
        
        # Draw Time Axis
        painter.setPen(QPen(QColor("#888"), 1))
        painter.drawLine(margin_left, height - margin_bottom, width - margin_right, height - margin_bottom)
        
        total_hours = self.end_hour - self.start_hour
        pixels_per_hour = draw_width / total_hours
        
        for i in range(total_hours + 1):
            hour = self.start_hour + i
            x = margin_left + (i * pixels_per_hour)
            
            # Tick
            painter.drawLine(int(x), int(height - margin_bottom), int(x), int(height - margin_bottom + 5))
            
            # Label
            painter.drawText(int(x - 15), int(height - 5), 30, 20, Qt.AlignmentFlag.AlignCenter, f"{hour:02d}:00")
            
            # Grid line
            painter.setPen(QPen(QColor("#eee"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(int(x), int(margin_top), int(x), int(height - margin_bottom))
            painter.setPen(QPen(QColor("#888"), 1))

        # Lanes
        lanes = {
            'Saisie': {'y': margin_top, 'color': '#2196F3', 'label': 'Saisie'},
            'Appro': {'y': margin_top + 40, 'color': '#4CAF50', 'label': 'Appro'},
            'Inventaire': {'y': margin_top + 80, 'color': '#FF9800', 'label': 'Inventaire'},
            'Urgence': {'y': margin_top + 120, 'color': '#F44336', 'label': 'Urgence'}
        }
        
        # Draw Lane Labels
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        for key, lane in lanes.items():
            painter.setPen(QPen(QColor(lane['color']), 1))
            painter.drawText(5, int(lane['y']), margin_left - 10, 30, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, lane['label'])
            
            # Lane background line
            painter.setPen(QPen(QColor("#f5f5f5"), 1))
            painter.drawLine(margin_left, int(lane['y'] + 15), width - margin_right, int(lane['y'] + 15))

        # Draw Events
        for evt in self.events:
            # evt = {'type': '...', 'start': datetime, 'end': datetime (opt), 'details': '...'}
            
            # Calculate X position
            start_time = evt['start']
            start_hour_float = start_time.hour + start_time.minute / 60.0
            
            if start_hour_float < self.start_hour or start_hour_float > self.end_hour:
                continue # Out of bounds
                
            x_start = margin_left + ((start_hour_float - self.start_hour) * pixels_per_hour)
            
            lane_key = None
            if evt['type'] == 'LIST_STARTED':
                lane_key = 'Saisie'
            elif evt['type'] == 'LIST_VALIDATED':
                lane_key = 'Appro'
            elif evt['type'] == 'INVENTORY_ADD':
                lane_key = 'Inventaire'
            elif evt['type'] == 'VIEW_LOCATION':
                lane_key = 'Urgence'
                
            if not lane_key: continue
            
            lane = lanes[lane_key]
            color = QColor(lane['color'])
            
            if 'end' in evt and evt['end']:
                # Draw Block (Duration)
                end_time = evt['end']
                end_hour_float = end_time.hour + end_time.minute / 60.0
                if end_hour_float > self.end_hour: end_hour_float = self.end_hour
                
                x_end = margin_left + ((end_hour_float - self.start_hour) * pixels_per_hour)
                width_rect = max(2, x_end - x_start)
                
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(x_start, lane['y'] + 5, width_rect, 20), 4, 4)
                
            else:
                # Draw Point (Instant)
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.GlobalColor.white, 1))
                painter.drawEllipse(int(x_start - 6), int(lane['y'] + 9), 12, 12)

class StatCard(QFrame):
    def __init__(self, title, value, subtitle="", color="#e0f7fa"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                border: 1px solid #ccc;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        layout = QVBoxLayout()
        
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #555;")
        layout.addWidget(title_lbl)
        
        self.value_lbl = QLabel(str(value))
        self.value_lbl.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_lbl)
        
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setFont(QFont("Arial", 9))
            sub_lbl.setStyleSheet("color: #777;")
            sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(sub_lbl)
            
        self.setLayout(layout)

    def set_value(self, value):
        self.value_lbl.setText(str(value))

class StatsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_stats()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Tableau de Bord - Performance & Statistiques"))
        
        refresh_btn = QPushButton("Rafraîchir")
        refresh_btn.clicked.connect(self.load_stats)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        
        # 1. KPI Section
        kpi_group = QFrame()
        kpi_layout = QGridLayout()
        
        self.card_interventions = StatCard("Interventions Vendeurs", "0", "Aujourd'hui", "#ffebee") # Red tint for 'bad'
        self.card_saisie_avg = StatCard("Moyenne Saisie/Produit", "0s", "Temps administratif", "#e8f5e9")
        self.card_appro_avg = StatCard("Temps Approvisionnement", "0m", "Clôture -> Validation", "#e3f2fd")
        self.card_products_today = StatCard("Produits Traités", "0", "Entrée Stock Aujourd'hui", "#fff3e0")
        
        kpi_layout.addWidget(self.card_interventions, 0, 0)
        kpi_layout.addWidget(self.card_saisie_avg, 0, 1)
        kpi_layout.addWidget(self.card_appro_avg, 0, 2)
        kpi_layout.addWidget(self.card_products_today, 0, 3)
        
        kpi_group.setLayout(kpi_layout)
        self.content_layout.addWidget(kpi_group)
        
        # 2. Timeline Section
        self.content_layout.addWidget(QLabel("Chronologie de l'activité (Aujourd'hui):"))
        self.timeline = TimelineWidget()
        self.content_layout.addWidget(self.timeline)
        
        # 3. Missing Items Source Analysis
        self.content_layout.addWidget(QLabel("Analyse des Manquants (30 derniers jours):"))
        self.missing_table = QTableWidget()
        self.missing_table.setColumnCount(3)
        self.missing_table.setHorizontalHeaderLabels(["Source", "Nombre", "Pourcentage"])
        self.missing_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.missing_table.setMaximumHeight(150)
        self.content_layout.addWidget(self.missing_table)
        
        self.content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)

    def load_stats(self):
        with get_db() as db:
            if not db: return
            
            today = date.today()
            today_start = datetime.combine(today, datetime.min.time())
            
            # 1. Interventions Vendeurs (VIEW_LOCATION today)
            interventions = db.query(EventLog).filter(
                EventLog.event_type == 'VIEW_LOCATION',
                EventLog.timestamp >= today_start
            ).count()
            self.card_interventions.set_value(interventions)
            
            # 2. Produits Traités (INVENTORY_ADD today)
            products_added = db.query(EventLog).filter(
                EventLog.event_type == 'INVENTORY_ADD',
                EventLog.timestamp >= today_start
            ).count()
            self.card_products_today.set_value(products_added)
            
            # 3. Temps Moyen Saisie/Produit
            # Get LIST_CLOSED events
            closed_events = db.query(EventLog).filter(EventLog.event_type == 'LIST_CLOSED').all()
            total_saisie_time = 0
            total_items_saisie = 0
            
            timeline_events = []
            
            # Add instant events to timeline
            # View Location
            view_locs = db.query(EventLog).filter(
                EventLog.event_type == 'VIEW_LOCATION',
                EventLog.timestamp >= today_start
            ).all()
            for e in view_locs:
                timeline_events.append({'type': 'VIEW_LOCATION', 'start': e.timestamp})
                
            # Inventory Add
            inv_adds = db.query(EventLog).filter(
                EventLog.event_type == 'INVENTORY_ADD',
                EventLog.timestamp >= today_start
            ).all()
            for e in inv_adds:
                timeline_events.append({'type': 'INVENTORY_ADD', 'start': e.timestamp})
            
            for closed in closed_events:
                list_id = closed.details
                # Find corresponding START
                started = db.query(EventLog).filter(
                    EventLog.event_type == 'LIST_STARTED',
                    EventLog.details == list_id,
                    EventLog.timestamp < closed.timestamp
                ).order_by(EventLog.timestamp.desc()).first()
                
                if started:
                    duration = (closed.timestamp - started.timestamp).total_seconds()
                    
                    # Add to timeline if today
                    if started.timestamp >= today_start:
                        timeline_events.append({
                            'type': 'LIST_STARTED',
                            'start': started.timestamp,
                            'end': closed.timestamp
                        })
                    
                    # Get item count for this list
                    item_count = db.query(SupplyListItem).filter(SupplyListItem.supply_list_id == int(list_id)).count()
                    
                    if item_count > 0:
                        total_saisie_time += duration
                        total_items_saisie += item_count
            
            if total_items_saisie > 0:
                avg_saisie = total_saisie_time / total_items_saisie
                self.card_saisie_avg.set_value(f"{int(avg_saisie)}s")
            else:
                self.card_saisie_avg.set_value("N/A")

            # 4. Temps Moyen Approvisionnement (Validation - Closure)
            validated_events = db.query(EventLog).filter(EventLog.event_type == 'LIST_VALIDATED').all()
            total_appro_time = 0
            count_appro = 0
            
            for val in validated_events:
                list_id = val.details
                # Find corresponding CLOSE
                closed = db.query(EventLog).filter(
                    EventLog.event_type == 'LIST_CLOSED',
                    EventLog.details == list_id,
                    EventLog.timestamp < val.timestamp
                ).order_by(EventLog.timestamp.desc()).first()
                
                if closed:
                    duration = (val.timestamp - closed.timestamp).total_seconds()
                    total_appro_time += duration
                    count_appro += 1
                    
                    # Add to timeline if today
                    if closed.timestamp >= today_start:
                        timeline_events.append({
                            'type': 'LIST_VALIDATED',
                            'start': closed.timestamp, # Start of Appro phase
                            'end': val.timestamp       # End of Appro phase
                        })
            
            if count_appro > 0:
                avg_appro = total_appro_time / count_appro
                minutes = int(avg_appro // 60)
                self.card_appro_avg.set_value(f"{minutes}m")
            else:
                self.card_appro_avg.set_value("N/A")
                
            # Update Timeline
            self.timeline.set_events(timeline_events)

            # 5. Missing Items Source
            # Group by source
            missing_stats = db.query(MissingItem.source, func.count(MissingItem.id)).group_by(MissingItem.source).all()
            total_missing = sum(count for source, count in missing_stats)
            
            self.missing_table.setRowCount(len(missing_stats))
            for row, (source, count) in enumerate(missing_stats):
                percentage = (count / total_missing * 100) if total_missing > 0 else 0
                
                self.missing_table.setItem(row, 0, QTableWidgetItem(source or "Inconnu"))
                self.missing_table.setItem(row, 1, QTableWidgetItem(str(count)))
                self.missing_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))
