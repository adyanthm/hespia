"""
Burp Suite-inspired dark theme stylesheet for PySide6.
"""

BURP_ORANGE = "#ff6633"
BURP_ORANGE_DARK = "#e65c2e"
BURP_ORANGE_LIGHT = "#ff855c"
BURP_BG = "#f2f2f2"
BURP_BG_DARK = "#e6e6e6"
BURP_BG_LIGHT = "#ffffff"
BURP_BORDER = "#cccccc"
BURP_BORDER_LIGHT = "#dddddd"
BURP_TEXT = "#333333"
BURP_TEXT_DIM = "#666666"
BURP_TEXT_BRIGHT = "#000000"
BURP_SELECTION = "#cedef2"
BURP_TABLE_ALT = "#fafafa"
BURP_SUCCESS = "#008800"
BURP_ERROR = "#cc0000"
BURP_WARNING = "#886600"
BURP_INFO = "#004488"
BURP_INFO_BG = "#e1f5fe"
BURP_SUCCESS_BG = "#e8f5e9"
BURP_WARNING_BG = "#fff9c4"
BURP_ERROR_BG = "#ffebee"
BURP_INTERCEPT_ON = "#005a9e"
BURP_INTERCEPT_OFF = "#757575"
BURP_TAB_ACTIVE = "#ffffff"
BURP_TAB_INACTIVE = "#e6e6e6"
BURP_HEADER = "#f0f0f0"
BURP_INPUT = "#ffffff"
BURP_GREEN = "#2e7d32"
BURP_RED = "#d32f2f"

MAIN_STYLESHEET = f"""
/* ─── Global ───────────────────────────────────────────── */
QWidget {{
    background-color: {BURP_BG};
    color: {BURP_TEXT};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
    selection-background-color: {BURP_SELECTION};
    selection-color: {BURP_TEXT_BRIGHT};
}}

QMainWindow {{
    background-color: {BURP_BG_DARK};
}}

/* ─── Menu Bar ──────────────────────────────────────────── */
QMenuBar {{
    background-color: {BURP_BG_DARK};
    color: {BURP_TEXT};
    border-bottom: 1px solid {BURP_BORDER};
    padding: 2px 4px;
}}
QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 3px;
}}
QMenuBar::item:selected {{
    background-color: {BURP_BG_LIGHT};
}}
QMenuBar::item:pressed {{
    background-color: {BURP_ORANGE};
    color: white;
}}
QMenu {{
    background-color: {BURP_BG_DARK};
    border: 1px solid {BURP_BORDER};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 2px;
}}
QMenu::item:selected {{
    background-color: {BURP_ORANGE};
    color: white;
}}
QMenu::separator {{
    height: 1px;
    background: {BURP_BORDER};
    margin: 3px 8px;
}}

/* ─── Status Bar ────────────────────────────────────────── */
QStatusBar {{
    background-color: {BURP_BG_DARK};
    color: {BURP_TEXT_DIM};
    border-top: 1px solid {BURP_BORDER};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ─── Tab Widget ────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BURP_BORDER};
    background-color: {BURP_BG};
    top: -1px;
}}
QTabWidget::tab-bar {{
    alignment: left;
}}
QTabBar {{
    background: {BURP_BG_DARK};
}}
QTabBar::tab {{
    background-color: {BURP_TAB_INACTIVE};
    color: {BURP_TEXT_DIM};
    padding: 6px 16px;
    border: 1px solid {BURP_BORDER};
    border-bottom: none;
    margin-right: 1px;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background-color: {BURP_TAB_ACTIVE};
    color: {BURP_ORANGE};
    border-bottom: 2px solid {BURP_ORANGE};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background-color: {BURP_BG_LIGHT};
    color: {BURP_TEXT};
}}

/* ─── Top-Level Tabs (larger) ───────────────────────────── */
QTabBar#mainTabBar::tab {{
    font-size: 13px;
    padding: 8px 18px;
    font-weight: 600;
}}

/* ─── Buttons ───────────────────────────────────────────── */
QPushButton {{
    background-color: {BURP_BG_LIGHT};
    color: {BURP_TEXT};
    border: 1px solid {BURP_BORDER};
    border-radius: 4px;
    padding: 6px 18px;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: {BURP_HEADER};
    border-color: {BURP_ORANGE};
    color: {BURP_TEXT_BRIGHT};
}}
QPushButton:pressed {{
    background-color: {BURP_ORANGE_DARK};
    border-color: {BURP_ORANGE};
}}
QPushButton:disabled {{
    color: {BURP_TEXT_DIM};
    border-color: {BURP_BORDER};
    background-color: {BURP_BG_DARK};
}}
QPushButton#interceptBtn {{
    font-size: 13px;
    font-weight: bold;
    padding: 8px 20px;
    border-radius: 4px;
    min-width: 140px;
}}
QPushButton#interceptBtn[active="true"] {{
    background-color: {BURP_INTERCEPT_ON};
    border-color: #ff8547;
    color: white;
}}
QPushButton#interceptBtn[active="false"] {{
    background-color: {BURP_INTERCEPT_OFF};
    border-color: #5fa574;
    color: white;
}}
QPushButton#actionBtn {{
    background-color: {BURP_ORANGE};
    color: white;
    border: none;
    border-radius: 20px;
    font-weight: bold;
}}
QPushButton#actionBtn:hover {{
    background-color: #ff7c52;
}}
QPushButton#actionBtn:disabled {{
    background-color: #dddddd;
    color: #999999;
}}
QPushButton#dangerBtn {{
    background-color: #fceaea;
    color: {BURP_RED};
    border: 1px solid {BURP_RED};
    border-radius: 20px;
    font-weight: bold;
}}
QPushButton#dangerBtn:hover {{
    background-color: {BURP_RED};
    color: white;
}}
QPushButton#dangerBtn:disabled {{
    background-color: #f5f5f5;
    border-color: #dddddd;
    color: #bbbbbb;
}}

/* ─── Table Widget ──────────────────────────────────────── */
QTableWidget {{
    background-color: {BURP_BG_LIGHT};
    alternate-background-color: {BURP_TABLE_ALT};
    color: {BURP_TEXT};
    gridline-color: #eeeeee;
    border: 1px solid {BURP_BORDER};
    selection-background-color: {BURP_SELECTION};
    selection-color: {BURP_TEXT_BRIGHT};
    font-size: 11px;
}}
QTableWidget::item {{
    padding: 3px 6px;
    border-bottom: 1px solid #f0f0f0;
}}
QTableWidget::item:selected {{
    background-color: {BURP_SELECTION};
    color: {BURP_TEXT_BRIGHT};
}}
QHeaderView::section {{
    background-color: {BURP_HEADER};
    color: {BURP_TEXT};
    padding: 5px 8px;
    border: 1px solid {BURP_BORDER};
    font-size: 11px;
    font-weight: bold;
}}
QHeaderView::section:hover {{
    background-color: {BURP_BG_LIGHT};
}}

/* ─── Text Editors ──────────────────────────────────────── */
QPlainTextEdit, QTextEdit {{
    background-color: #ffffff;
    color: #222222;
    border: 1px solid {BURP_BORDER};
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    selection-background-color: {BURP_SELECTION};
    padding: 4px;
}}
QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {BURP_ORANGE};
}}

/* ─── Line Edit ─────────────────────────────────────────── */
QLineEdit {{
    background-color: {BURP_INPUT};
    color: {BURP_TEXT};
    border: 1px solid {BURP_BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 12px;
    selection-background-color: {BURP_SELECTION};
}}
QLineEdit:focus {{
    border-color: {BURP_ORANGE};
}}
QLineEdit:read-only {{
    background-color: {BURP_BG_DARK};
    color: {BURP_TEXT_DIM};
}}

/* ─── Combo Box ─────────────────────────────────────────── */
QComboBox {{
    background-color: {BURP_INPUT};
    color: {BURP_TEXT};
    border: 1px solid {BURP_BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    min-width: 80px;
}}
QComboBox:focus {{
    border-color: {BURP_ORANGE};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {BURP_TEXT_DIM};
    margin-right: 4px;
}}
QComboBox QAbstractItemView {{
    background-color: {BURP_BG_DARK};
    color: {BURP_TEXT};
    border: 1px solid {BURP_BORDER};
    selection-background-color: {BURP_ORANGE};
    selection-color: white;
}}

/* ─── Spin Box ──────────────────────────────────────────── */
QSpinBox {{
    background-color: {BURP_INPUT};
    color: {BURP_TEXT};
    border: 1px solid {BURP_BORDER};
    border-radius: 3px;
    padding: 4px;
}}
QSpinBox:focus {{
    border-color: {BURP_ORANGE};
}}

/* ─── Check Box ─────────────────────────────────────────── */
QCheckBox {{
    color: {BURP_TEXT};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {BURP_BORDER};
    border-radius: 2px;
    background-color: {BURP_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {BURP_ORANGE};
    border-color: {BURP_ORANGE};
}}
QCheckBox::indicator:hover {{
    border-color: {BURP_BORDER_LIGHT};
}}

/* ─── Radio Button ──────────────────────────────────────── */
QRadioButton {{
    color: {BURP_TEXT};
    spacing: 6px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {BURP_BORDER};
    border-radius: 7px;
    background-color: {BURP_INPUT};
}}
QRadioButton::indicator:checked {{
    background-color: {BURP_ORANGE};
    border-color: {BURP_ORANGE};
}}

/* ─── Scroll Bars ───────────────────────────────────────── */
QScrollBar:vertical {{
    background: {BURP_BG_DARK};
    width: 10px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: #555555;
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{
    background: {BURP_ORANGE_LIGHT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BURP_BG_DARK};
    height: 10px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: #555555;
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {BURP_BORDER_LIGHT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ─── Group Box ─────────────────────────────────────────── */
QGroupBox {{
    color: {BURP_TEXT};
    border: 1px solid {BURP_BORDER};
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 10px;
    top: -1px;
    color: {BURP_ORANGE};
}}

/* ─── Splitter ──────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {BURP_BORDER};
}}
QSplitter::handle:horizontal {{
    width: 3px;
}}
QSplitter::handle:vertical {{
    height: 3px;
}}
QSplitter::handle:hover {{
    background-color: {BURP_ORANGE};
}}

/* ─── Tool Bar ──────────────────────────────────────────── */
QToolBar {{
    background-color: {BURP_BG_DARK};
    border-bottom: 1px solid {BURP_BORDER};
    spacing: 4px;
    padding: 3px 6px;
}}

/* ─── Labels ────────────────────────────────────────────── */
QLabel#titleLabel {{
    font-size: 16px;
    font-weight: bold;
    color: {BURP_ORANGE};
}}
QLabel#sectionLabel {{
    font-size: 12px;
    font-weight: bold;
    color: {BURP_TEXT};
    padding: 4px 0;
}}
QLabel#dimLabel {{
    color: {BURP_TEXT_DIM};
    font-size: 11px;
}}
QLabel#statusIndicator[status="running"] {{
    color: {BURP_GREEN};
    font-weight: bold;
}}
QLabel#statusIndicator[status="stopped"] {{
    color: {BURP_RED};
    font-weight: bold;
}}

/* ─── Tree Widget ───────────────────────────────────────── */
QTreeWidget {{
    background-color: {BURP_BG};
    color: {BURP_TEXT};
    border: 1px solid {BURP_BORDER};
    alternate-background-color: {BURP_TABLE_ALT};
}}
QTreeWidget::item:selected {{
    background-color: {BURP_SELECTION};
    color: {BURP_TEXT_BRIGHT};
}}
QTreeWidget::item:hover {{
    background-color: {BURP_TABLE_ALT};
}}

/* ─── List Widget ───────────────────────────────────────── */
QListWidget {{
    background-color: {BURP_BG};
    color: {BURP_TEXT};
    border: 1px solid {BURP_BORDER};
}}
QListWidget::item:selected {{
    background-color: {BURP_ORANGE};
    color: white;
}}
QListWidget::item:hover {{
    background-color: {BURP_TABLE_ALT};
}}

/* ─── Tool Tip ──────────────────────────────────────────── */
QToolTip {{
    background-color: {BURP_BG_DARK};
    color: {BURP_TEXT_BRIGHT};
    border: 1px solid {BURP_ORANGE};
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 11px;
}}

/* ─── Progress Bar ──────────────────────────────────────── */
QProgressBar {{
    background-color: {BURP_BG_DARK};
    border: 1px solid {BURP_BORDER};
    border-radius: 3px;
    text-align: center;
    color: {BURP_TEXT};
    height: 14px;
}}
QProgressBar::chunk {{
    background-color: {BURP_ORANGE};
    border-radius: 2px;
}}

/* ─── Dialogs ───────────────────────────────────────────── */
QDialog {{
    background-color: {BURP_BG};
}}

/* ─── Frame ─────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {BURP_BORDER};
}}
"""

# Extra button-specific styles to apply dynamically
INTERCEPT_ON_STYLE = f"""
    QPushButton {{
        background-color: {BURP_ORANGE};
        color: white;
        border: 2px solid {BURP_ORANGE_LIGHT};
        font-weight: bold;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {BURP_ORANGE_LIGHT};
    }}
"""

INTERCEPT_OFF_STYLE = f"""
    QPushButton {{
        background-color: {BURP_INTERCEPT_OFF};
        color: white;
        border: 2px solid #5fa574;
        font-weight: bold;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: #5fa574;
    }}
"""

HTTP_STATUS_COLORS = {
    "2": "#4CAF50",   # 2xx green
    "3": "#FF9800",   # 3xx orange
    "4": "#F44336",   # 4xx red
    "5": "#E91E63",   # 5xx pink-red
}

METHOD_COLORS = {
    "GET": "#5a9e5a",
    "POST": "#9e8a5a",
    "PUT": "#5a7a9e",
    "DELETE": "#9e5a5a",
    "PATCH": "#7a5a9e",
    "HEAD": "#5a9e9e",
    "OPTIONS": "#888888",
}

# ─── New Modern Button Styles ──────────────────────────────────────────

BANNER_START_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #059669);
    color: white;
    border: 1px solid #047857;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
    padding: 4px 10px;
}}
QPushButton:hover {{
    background: #059669;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #059669, stop:1 #047857);
}}
QPushButton:pressed {{
    background: #065f46;
}}
QPushButton:disabled {{
    background: {BURP_BG_DARK};
    color: {BURP_TEXT_DIM};
    border: 1px solid {BURP_BORDER};
}}
"""

BANNER_STOP_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef4444, stop:1 #dc2626);
    color: white;
    border: 1px solid #b91c1c;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
    padding: 4px 10px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #b91c1c);
}}
QPushButton:pressed {{
    background: #991b1b;
}}
QPushButton:disabled {{
    background: {BURP_BG_DARK};
    color: {BURP_TEXT_DIM};
    border: 1px solid {BURP_BORDER};
}}
"""

MODERN_FORWARD_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BURP_ORANGE_LIGHT}, stop:1 {BURP_ORANGE});
    color: white;
    border: 1px solid {BURP_ORANGE_DARK};
    border-radius: 4px;
    font-weight: bold;
    padding: 4px 14px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BURP_ORANGE}, stop:1 {BURP_ORANGE_DARK});
}}
QPushButton:pressed {{
    background: #d94e10;
}}
QPushButton:disabled {{
    background: {BURP_BG_DARK}bb;
    color: {BURP_TEXT_DIM}aa;
    border: 1px solid {BURP_BORDER};
}}
"""

MODERN_ACTION_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #42a5f5, stop:1 #1e88e5);
    color: white;
    border: 1px solid #1565c0;
    border-radius: 4px;
    font-weight: bold;
    padding: 6px 16px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #64b5f6, stop:1 #2196f3);
    border-color: #0d47a1;
}}
QPushButton:pressed {{
    background: #1565c0;
}}
QPushButton:disabled {{
    background: {BURP_BG_DARK};
    color: {BURP_TEXT_DIM};
    border: 1px solid {BURP_BORDER};
}}
"""

MODERN_DROP_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef5350, stop:1 #d32f2f);
    color: white;
    border: 1px solid #b71c1c;
    border-radius: 4px;
    font-weight: bold;
    padding: 6px 16px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e57373, stop:1 #f44336);
    border-color: #880e4f;
}}
QPushButton:pressed {{
    background: #b71c1c;
}}
QPushButton:disabled {{
    background: {BURP_BG_DARK};
    color: {BURP_TEXT_DIM};
    border: 1px solid {BURP_BORDER};
}}
"""
