def get_stylesheet():
    return """
    /* Global Reset & Font */
    * {
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 14px;
        color: #495057; /* Softer dark gray text */
        outline: none;
    }

    /* Main Window & Backgrounds */
    QMainWindow, QDialog {
        background-color: #f0f2f5; /* Softer, slightly darker gray-blue background */
    }
    QWidget {
        background-color: transparent;
    }
    
    /* Tab Widget - Modern Card Style */
    QTabWidget::pane {
        border: 1px solid #d0ebff; /* Light blue border */
        background: #ebf3ff; /* Light Blue Background */
        border-radius: 12px;
        top: -1px; 
        padding: 10px;
    }
    QTabBar::tab {
        background: transparent;
        color: #6c757d;
        padding: 12px 24px;
        margin-right: 8px;
        border-bottom: 3px solid transparent;
        font-weight: 600;
        font-size: 15px;
    }
    QTabBar::tab:selected {
        color: #5c7cfa;
        border-bottom: 3px solid #5c7cfa;
        background-color: #f1f3f5;
        border-radius: 6px;
    }
    QTabBar::tab:hover {
        color: #4263eb;
        background-color: #e7f5ff;
        border-radius: 6px;
    }

    /* Buttons - Flat & Modern */
    QPushButton {
        background-color: #5c7cfa;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #4263eb;
    }
    QPushButton:pressed {
        background-color: #364fc7;
    }
    QPushButton:disabled {
        background-color: #e9ecef;
        color: #adb5bd;
    }
    
    /* Table Action Buttons (Icons) */
    QPushButton#TableActionBtn {
        background-color: transparent;
        color: #868e96;
        border: 1px solid transparent;
        border-radius: 6px;
        min-width: 36px;
        max-width: 36px;
        min-height: 36px;
        max-height: 36px;
        padding: 4px;
        margin: 0px;
        qproperty-iconSize: 24px 24px;
    }
    QPushButton#TableActionBtn:hover {
        background-color: #ffe3e3;
        color: #fa5252;
        border: 1px solid #ffc9c9;
    }
    
    /* Inputs - Clean & Spacious */
    QLineEdit, QComboBox, QSpinBox, QDateEdit {
        background-color: #fdfdfd; /* Softer off-white */
        border: 1px solid #ced4da;
        border-radius: 8px;
        padding: 8px 12px;
        color: #495057;
        font-size: 14px;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #5c7cfa;
        background-color: #ffffff; /* White on focus for clarity */
    }
    QLineEdit::placeholder {
        color: #adb5bd;
    }

    /* Tables - Card Style */
    QTableWidget {
        background-color: #fdfdfd; /* Softer off-white */
        border: 1px solid #dee2e6;
        border-radius: 12px;
        gridline-color: transparent;
        selection-background-color: #edf2ff;
        selection-color: #364fc7;
        alternate-background-color: #f8f9fa;
    }
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid #f1f3f5;
        background-color: transparent;
    }
    QTableWidget::item:selected {
        background-color: #edf2ff;
        color: #364fc7;
        border-bottom: 1px solid #edf2ff;
    }
    QHeaderView::section {
        background-color: #e9ecef; /* Light gray */
        color: #868e96;
        padding: 12px;
        border: none;
        border-bottom: 2px solid #dee2e6;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.5px;
    }

    /* Scrollbars - Minimalist */
    QScrollBar:vertical {
        border: none;
        background: #f1f3f5;
        width: 8px;
        margin: 0;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #ced4da;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #adb5bd;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    /* Labels */
    QLabel {
        color: #343a40;
        font-size: 14px;
    }
    """
