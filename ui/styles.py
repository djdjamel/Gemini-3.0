def get_stylesheet():
    return """
    /* Modern Soft Design for Gravity Stock Manager */
    
    /* Global Reset & Font */
    * {
        font-family: 'Segoe UI', 'SF Pro Display', 'Inter', sans-serif;
        font-size: 13px;
        color: #2d3748;
        outline: none;
    }

    /* Main Window & Backgrounds - Dark Theme */
    QMainWindow {
        background-color: #1a202c;
    }
    
    QDialog {
        background-color: #2d3748;
    }
    
    QWidget {
        background-color: transparent;
    }
    
    /* Tab Widget - Dark Theme */
    QTabWidget::pane {
        border: 1px solid #4a5568;
        background: #2d3748;
        border-radius: 12px;
        top: -1px;
        padding: 16px;
    }
    
    QTabBar::tab {
        background: transparent;
        color: #a0aec0;
        padding: 10px 20px;
        margin-right: 4px;
        border-bottom: 2px solid transparent;
        font-weight: 500;
        font-size: 14px;
    }
    
    QTabBar::tab:selected {
        color: #63b3ed;
        border-bottom: 2px solid #63b3ed;
        background-color: #1a202c;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    
    QTabBar::tab:hover {
        color: #90cdf4;
        background-color: #1a202c;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }

    /* Buttons - Modern Gradient Style */
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 #4299e1, stop:1 #3182ce);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 13px;
        min-height: 32px;
    }
    
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 #3182ce, stop:1 #2c5282);
    }
    
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 #2c5282, stop:1 #2a4365);
        padding: 11px 19px 9px 21px;
    }
    
    QPushButton:disabled {
        background: #e2e8f0;
        color: #a0aec0;
    }
    
    /* Table Action Buttons */
    QPushButton#TableActionBtn {
        background-color: transparent;
        color: #718096;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        min-width: 32px;
        max-width: 32px;
        min-height: 32px;
        max-height: 32px;
        padding: 4px;
        margin: 0px;
    }
    
    QPushButton#TableActionBtn:hover {
        background-color: #edf2f7;
        border: 1px solid #cbd5e0;
        color: #2d3748;
    }
    
    QPushButton#TableActionBtn:pressed {
        background-color: #e2e8f0;
    }
    
    /* Input Fields - Dark Theme */
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        border-radius: 8px;
        padding: 10px 14px;
        color: #ffffff;
        selection-background-color: #2c5282;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #4299e1;
        padding: 9px 13px;
        background-color: #1a202c;
    }
    
    QLineEdit:disabled, QTextEdit:disabled {
        background-color: #2d3748;
        color: #718096;
    }
    
    QLineEdit::placeholder {
        color: #718096;
    }

    /* ComboBox - Dark Theme */
    QComboBox {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        border-radius: 8px;
        padding: 10px 14px;
        color: #ffffff;
        min-height: 20px;
    }
    
    QComboBox:hover {
        border-color: #718096;
    }
    
    QComboBox:focus {
        border: 2px solid #4299e1;
        padding: 9px 13px;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #90cdf4;
        margin-right: 8px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        border-radius: 8px;
        selection-background-color: #2d3748;
        selection-color: #ffffff;
        padding: 4px;
        color: #ffffff;
    }

    /* Tables - Dark Theme */
    QTableWidget {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        border-radius: 12px;
        gridline-color: #2d3748;
        selection-background-color: #2c5282;
        selection-color: #ffffff;
        alternate-background-color: #2d3748;
        color: #ffffff;
    }
    
    QTableWidget::item {
        padding: 12px 8px;
        border-bottom: 1px solid #2d3748;
        color: #ffffff;
    }
    
    QTableWidget::item:selected {
        background-color: #2c5282;
        color: #ffffff;
        border-bottom: 1px solid #3182ce;
    }
    
    QTableWidget::item:hover {
        background-color: #2d3748;
    }
    
    QHeaderView::section {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 #2d3748, stop:1 #1a202c);
        color: #90cdf4;
        padding: 14px 8px;
        border: none;
        border-bottom: 2px solid #4a5568;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.8px;
    }
    
    QHeaderView::section:first {
        border-top-left-radius: 12px;
    }
    
    QHeaderView::section:last {
        border-top-right-radius: 12px;
    }

    /* Scrollbars - Minimalist & Smooth */
    QScrollBar:vertical {
        background-color: #f7fafc;
        width: 10px;
        border-radius: 5px;
        margin: 2px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #cbd5e0;
        border-radius: 5px;
        min-height: 30px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #a0aec0;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    
    QScrollBar:horizontal {
        background-color: #f7fafc;
        height: 10px;
        border-radius: 5px;
        margin: 2px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #cbd5e0;
        border-radius: 5px;
        min-width: 30px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #a0aec0;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
    }

    /* Labels - White on Dark */
    QLabel {
        color: #ffffff;
        font-size: 13px;
    }

    /* Group Boxes - Dark Theme */
    QGroupBox {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        border-radius: 12px;
        margin-top: 16px;
        padding-top: 20px;
        font-weight: 600;
        color: #ffffff;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 6px 14px;
        background-color: #2d3748;
        border-radius: 6px;
        margin-left: 12px;
        color: #90cdf4;
    }

    /* Progress Bar - Modern */
    QProgressBar {
        background-color: #edf2f7;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        text-align: center;
        height: 24px;
        color: #2d3748;
        font-weight: 600;
    }
    
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                   stop:0 #4299e1, stop:1 #3182ce);
        border-radius: 7px;
    }

    /* Spin Box */
    QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 10px;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus {
        border: 2px solid #4299e1;
        padding: 7px 9px;
    }

    /* Check Box - Modern Toggle Style */
    QCheckBox {
        spacing: 10px;
        color: #ffffff;
    }
    
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border: 2px solid #cbd5e0;
        border-radius: 5px;
        background-color: #ffffff;
    }
    
    QCheckBox::indicator:checked {
        background-color: #4299e1;
        border-color: #4299e1;
        image: none;
    }
    
    QCheckBox::indicator:hover {
        border-color: #4299e1;
    }

    /* Radio Button */
    QRadioButton {
        spacing: 10px;
        color: #ffffff;
    }
    
    QRadioButton::indicator {
        width: 20px;
        height: 20px;
        border: 2px solid #cbd5e0;
        border-radius: 10px;
        background-color: #ffffff;
    }
    
    QRadioButton::indicator:checked {
        background-color: #4299e1;
        border-color: #4299e1;
    }
    
    QRadioButton::indicator:hover {
        border-color: #4299e1;
    }

    /* Tool Tip - Modern Card */
    QToolTip {
        background-color: #1a202c;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
    }

    /* Menu Bar */
    QMenuBar {
        background-color: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        padding: 4px;
    }
    
    QMenuBar::item {
        background-color: transparent;
        padding: 8px 16px;
        border-radius: 6px;
        color: #2d3748;
    }
    
    QMenuBar::item:selected {
        background-color: #edf2f7;
        color: #2d3748;
    }

    /* Menu - Dropdown */
    QMenu {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 6px;
    }
    
    QMenu::item {
        padding: 10px 28px;
        border-radius: 6px;
        color: #2d3748;
    }
    
    QMenu::item:selected {
        background-color: #edf2f7;
        color: #2d3748;
    }

    /* Status Bar */
    QStatusBar {
        background-color: #ffffff;
        color: #718096;
        border-top: 1px solid #e2e8f0;
        padding: 4px;
    }
    
    /* Message Box - Dark Theme */
    QMessageBox {
        background-color: #2d3748;
    }
    
    QMessageBox QLabel {
        color: #ffffff;
        background-color: transparent;
    }
    
    QMessageBox QPushButton {
        min-width: 90px;
    }
    
    /* Dialog - Dark Theme */
    QDialog {
        background-color: #2d3748;
    }
    
    QDialog QLabel {
        color: #ffffff;
        background-color: transparent;
    }
    
    QDialog QLineEdit,
    QDialog QTextEdit,
    QDialog QComboBox,
    QDialog QSpinBox {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        color: #ffffff;
    }
    
    QDialog QLineEdit:focus,
    QDialog QTextEdit:focus,
    QDialog QComboBox:focus,
    QDialog QSpinBox:focus {
        border: 2px solid #4299e1;
        background-color: #1a202c;
    }
    
    /* Ensure white text on button gradients */
    QPushButton {
        color: #ffffff;
    }
    
    QPushButton:disabled {
        color: #a0aec0;
    }
    """
