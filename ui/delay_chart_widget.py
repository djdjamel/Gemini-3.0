from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath

class DelayChartWidget(QWidget):
    """Custom line chart widget for displaying delay evolution over time"""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.data = []  # List of (date, avg_delay) tuples
        
    def set_data(self, data):
        """data: list of (date, avg_delay_hours) tuples"""
        self.data = sorted(data, key=lambda x: x[0])  # Sort by date
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Margins
        margin_left = 60
        margin_right = 20
        margin_top = 30
        margin_bottom = 50
        
        draw_width = width - margin_left - margin_right
        draw_height = height - margin_top - margin_bottom
        
        if not self.data or len(self.data) < 2:
            # No data to display
            painter.setPen(QPen(QColor("#999"), 1))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(QRectF(0, 0, width, height), Qt.AlignmentFlag.AlignCenter, "Données insuffisantes")
            return
            
        # Find min/max values
        delays = [d[1] for d in self.data if d[1] is not None]
        if not delays:
            painter.setPen(QPen(QColor("#999"), 1))
            painter.setFont(QFont("Arial", 11))
            painter.drawText(QRectF(0, 0, width, height), Qt.AlignmentFlag.AlignCenter, "Aucune donnée de délai")
            return
            
        min_delay = min(delays)
        max_delay = max(delays)
        
        # Add 10% padding to Y-axis range
        delay_range = max_delay - min_delay
        if delay_range == 0:
            delay_range = max_delay * 0.1 if max_delay > 0 else 1
        min_delay = max(0, min_delay - delay_range * 0.1)
        max_delay = max_delay + delay_range * 0.1
        
        # Draw axes
        painter.setPen(QPen(QColor("#444"), 2))
        painter.drawLine(margin_left, height - margin_bottom, width - margin_right, height - margin_bottom)  # X-axis
        painter.drawLine(margin_left, margin_top, margin_left, height - margin_bottom)  # Y-axis
        
        # Draw Y-axis labels (delay in hours)
        painter.setPen(QPen(QColor("#666"), 1))
        painter.setFont(QFont("Arial", 9))
        
        num_y_ticks = 5
        for i in range(num_y_ticks + 1):
            delay_value = min_delay + (max_delay - min_delay) * (i / num_y_ticks)
            y_pos = height - margin_bottom - (draw_height * i / num_y_ticks)
            
            # Grid line
            painter.setPen(QPen(QColor("#eee"), 1, Qt.PenStyle.DashLine))
            painter.drawLine(margin_left, int(y_pos), width - margin_right, int(y_pos))
            
            # Label
            painter.setPen(QPen(QColor("#666"), 1))
            label_text = f"{delay_value:.1f}h"
            painter.drawText(5, int(y_pos - 10), margin_left - 10, 20, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label_text)
        
        # Y-axis title
        painter.save()
        painter.translate(15, height / 2)
        painter.rotate(-90)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(-50, 0, 100, 20, Qt.AlignmentFlag.AlignCenter, "Délai (heures)")
        painter.restore()
        
        # Draw X-axis labels (dates)
        num_points = len(self.data)
        step = max(1, num_points // 7)  # Show max 7 labels
        
        painter.setFont(QFont("Arial", 9))
        for i, (date_val, _) in enumerate(self.data):
            if i % step == 0 or i == num_points - 1:
                x_pos = margin_left + (draw_width * i / (num_points - 1))
                
                # Date label
                painter.setPen(QPen(QColor("#666"), 1))
                date_str = date_val.strftime("%d/%m")
                painter.drawText(int(x_pos - 20), height - margin_bottom + 5, 40, 20, Qt.AlignmentFlag.AlignCenter, date_str)
        
        # X-axis title
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(margin_left, height - 15, draw_width, 20, Qt.AlignmentFlag.AlignCenter, "Date")
        
        # Draw line chart
        painter.setPen(QPen(QColor("#2196F3"), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        path = QPainterPath()
        
        for i, (date_val, delay_val) in enumerate(self.data):
            if delay_val is None:
                continue
                
            x = margin_left + (draw_width * i / (num_points - 1))
            y_ratio = (delay_val - min_delay) / (max_delay - min_delay) if (max_delay - min_delay) > 0 else 0
            y = height - margin_bottom - (draw_height * y_ratio)
            
            if i == 0 or path.isEmpty():
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        
        painter.drawPath(path)
        
        # Draw data points
        painter.setBrush(QBrush(QColor("#1976D2")))
        for i, (date_val, delay_val) in enumerate(self.data):
            if delay_val is None:
                continue
                
            x = margin_left + (draw_width * i / (num_points - 1))
            y_ratio = (delay_val - min_delay) / (max_delay - min_delay) if (max_delay - min_delay) > 0 else 0
            y = height - margin_bottom - (draw_height * y_ratio)
            
            painter.drawEllipse(QRectF(x - 4, y - 4, 8, 8))
