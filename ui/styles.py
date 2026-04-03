"""
Burp Suite-inspired dark theme stylesheet for PySide6.
"""

BURP_ORANGE = "#f97316"       # Hyper-Modern Orange (Vibrant)
BURP_ORANGE_DARK = "#ea580c"
BURP_ORANGE_LIGHT = "#fb923c"
BURP_BG = "#ffffff"          # Pure White Background
BURP_BG_DARK = "#f8fafc"     # Subtle Slate/Grey
BURP_BG_LIGHT = "#ffffff"
BURP_BORDER = "#e2e8f0"      # Modern Slate Border
BURP_BORDER_LIGHT = "#f1f5f9"
BURP_TEXT = "#0f172a"        # Deep Slate (Primary Text)
BURP_TEXT_DIM = "#64748b"     # Muted Slate Text
BURP_TEXT_BRIGHT = "#000000"
BURP_SELECTION = "#ffedd5"   # Soft Orange Selection Tint
BURP_TABLE_ALT = "#fafaf9"
BURP_SUCCESS = "#16a34a"      # Modern Green
BURP_ERROR = "#dc2626"        # Rose Red
BURP_WARNING = "#f59e0b"      # Amber
BURP_INFO = "#3b82f6"         # Blue
BURP_INFO_BG = "#eff6ff"
BURP_SUCCESS_BG = "#f0fdf4"
BURP_WARNING_BG = "#fffbeb"
BURP_ERROR_BG = "#fef2f2"
BURP_INTERCEPT_ON = "#ea580c"
BURP_INTERCEPT_OFF = "#64748b"
BURP_TAB_ACTIVE = "#ffffff"
BURP_TAB_INACTIVE = "#f8fafc"
BURP_HEADER = "#f1f5f9"
BURP_INPUT = "#ffffff"
BURP_GREEN = "#16a34a"
BURP_RED = "#dc2626"

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
    border-radius: 4px;
    padding: 4px 6px;
}}
QSpinBox:focus {{
    border-color: {BURP_ORANGE};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    border: none;
    width: 18px;
    background: transparent;
}}
QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
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
    "2": "#059669",   # 2xx emerald
    "3": "#2563eb",   # 3xx blue
    "4": "#d97706",   # 4xx amber
    "5": "#dc2626",   # 5xx rose
}

METHOD_COLORS = {
    "GET": "#059669",
    "POST": "#2563eb",
    "PUT": "#7c3aed",
    "DELETE": "#dc2626",
    "PATCH": "#db2777",
    "HEAD": "#64748b",
    "OPTIONS": "#94a3b8",
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
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BURP_ORANGE_LIGHT}, stop:1 {BURP_ORANGE});
    color: white;
    border: 1px solid {BURP_ORANGE_DARK};
    border-radius: 4px;
    font-weight: bold;
    padding: 6px 16px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BURP_ORANGE}, stop:1 {BURP_ORANGE_DARK});
    border-color: {BURP_ORANGE};
}}
QPushButton:pressed {{
    background: {BURP_ORANGE_DARK};
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
