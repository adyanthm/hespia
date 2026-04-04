"""
Burp Suite-inspired dark theme stylesheet for PySide6.
"""

HESPIA_ORANGE = "#f97316"       # Hyper-Modern Orange (Vibrant)
HESPIA_ORANGE_DARK = "#ea580c"
HESPIA_ORANGE_LIGHT = "#fb923c"
HESPIA_BG = "#ffffff"          # Pure White Background
HESPIA_BG_DARK = "#f8fafc"     # Subtle Slate/Grey
HESPIA_BG_LIGHT = "#ffffff"
HESPIA_BORDER = "#e2e8f0"      # Modern Slate Border
HESPIA_BORDER_LIGHT = "#f1f5f9"
HESPIA_TEXT = "#0f172a"        # Deep Slate (Primary Text)
HESPIA_TEXT_DIM = "#64748b"     # Muted Slate Text
HESPIA_TEXT_BRIGHT = "#000000"
HESPIA_SELECTION = "#ffedd5"   # Soft Orange Selection Tint
HESPIA_TABLE_ALT = "#fafaf9"
HESPIA_SUCCESS = "#16a34a"      # Modern Green
HESPIA_ERROR = "#dc2626"        # Rose Red
HESPIA_WARNING = "#f59e0b"      # Amber
HESPIA_INFO = "#3b82f6"         # Blue
HESPIA_INFO_BG = "#eff6ff"
HESPIA_SUCCESS_BG = "#f0fdf4"
HESPIA_WARNING_BG = "#fffbeb"
HESPIA_ERROR_BG = "#fef2f2"
HESPIA_INTERCEPT_ON = "#ea580c"
HESPIA_INTERCEPT_OFF = "#64748b"
HESPIA_TAB_ACTIVE = "#ffffff"
HESPIA_TAB_INACTIVE = "#f8fafc"
HESPIA_HEADER = "#f1f5f9"
HESPIA_INPUT = "#ffffff"
HESPIA_GREEN = "#16a34a"
HESPIA_RED = "#dc2626"

MAIN_STYLESHEET = f"""
/* ─── Global ───────────────────────────────────────────── */
QWidget {{
    background-color: {HESPIA_BG};
    color: {HESPIA_TEXT};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
    selection-background-color: {HESPIA_SELECTION};
    selection-color: {HESPIA_TEXT_BRIGHT};
}}

QMainWindow {{
    background-color: {HESPIA_BG_DARK};
}}

/* ─── Menu Bar ──────────────────────────────────────────── */
QMenuBar {{
    background-color: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT};
    border-bottom: 1px solid {HESPIA_BORDER};
    padding: 2px 4px;
}}
QMenuBar::item {{
    padding: 4px 10px;
    border-radius: 3px;
}}
QMenuBar::item:selected {{
    background-color: {HESPIA_BG_LIGHT};
}}
QMenuBar::item:pressed {{
    background-color: {HESPIA_ORANGE};
    color: white;
}}
QMenu {{
    background-color: {HESPIA_BG_DARK};
    border: 1px solid {HESPIA_BORDER};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 2px;
}}
QMenu::item:selected {{
    background-color: {HESPIA_ORANGE};
    color: white;
}}
QMenu::separator {{
    height: 1px;
    background: {HESPIA_BORDER};
    margin: 3px 8px;
}}

/* ─── Status Bar ────────────────────────────────────────── */
QStatusBar {{
    background-color: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT_DIM};
    border-top: 1px solid {HESPIA_BORDER};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ─── Tab Widget ────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {HESPIA_BORDER};
    background-color: {HESPIA_BG};
    top: -1px;
}}
QTabWidget::tab-bar {{
    alignment: left;
}}
QTabBar {{
    background: {HESPIA_BG_DARK};
}}
QTabBar::tab {{
    background-color: {HESPIA_TAB_INACTIVE};
    color: {HESPIA_TEXT_DIM};
    padding: 6px 16px;
    border: 1px solid {HESPIA_BORDER};
    border-bottom: none;
    margin-right: 1px;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background-color: {HESPIA_TAB_ACTIVE};
    color: {HESPIA_ORANGE};
    border-bottom: 2px solid {HESPIA_ORANGE};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background-color: {HESPIA_BG_LIGHT};
    color: {HESPIA_TEXT};
}}

/* ─── Top-Level Tabs (larger) ───────────────────────────── */
QTabBar#mainTabBar::tab {{
    font-size: 13px;
    padding: 8px 18px;
    font-weight: 600;
}}

/* ─── Buttons ───────────────────────────────────────────── */
QPushButton {{
    background-color: {HESPIA_BG_LIGHT};
    color: {HESPIA_TEXT};
    border: 1px solid {HESPIA_BORDER};
    border-radius: 4px;
    padding: 6px 18px;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: {HESPIA_HEADER};
    border-color: {HESPIA_ORANGE};
    color: {HESPIA_TEXT_BRIGHT};
}}
QPushButton:pressed {{
    background-color: {HESPIA_ORANGE_DARK};
    border-color: {HESPIA_ORANGE};
}}
QPushButton:disabled {{
    color: {HESPIA_TEXT_DIM};
    border-color: {HESPIA_BORDER};
    background-color: {HESPIA_BG_DARK};
}}

/* ─── Table Widget ──────────────────────────────────────── */
QTableWidget {{
    background-color: {HESPIA_BG_LIGHT};
    alternate-background-color: {HESPIA_TABLE_ALT};
    color: {HESPIA_TEXT};
    gridline-color: #eeeeee;
    border: 1px solid {HESPIA_BORDER};
    selection-background-color: {HESPIA_SELECTION};
    selection-color: {HESPIA_TEXT_BRIGHT};
    font-size: 11px;
}}
QTableWidget::item {{
    padding: 3px 6px;
    border-bottom: 1px solid #f0f0f0;
}}
QTableWidget::item:selected {{
    background-color: {HESPIA_SELECTION};
    color: {HESPIA_TEXT_BRIGHT};
}}
QHeaderView::section {{
    background-color: {HESPIA_HEADER};
    color: {HESPIA_TEXT};
    padding: 5px 8px;
    border: 1px solid {HESPIA_BORDER};
    font-size: 11px;
    font-weight: bold;
}}
QHeaderView::section:hover {{
    background-color: {HESPIA_BG_LIGHT};
}}

/* ─── Text Editors ──────────────────────────────────────── */
QPlainTextEdit, QTextEdit {{
    background-color: #ffffff;
    color: #222222;
    border: 1px solid {HESPIA_BORDER};
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    selection-background-color: {HESPIA_SELECTION};
    padding: 4px;
}}
QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {HESPIA_ORANGE};
}}

/* ─── Line Edit ─────────────────────────────────────────── */
QLineEdit {{
    background-color: {HESPIA_INPUT};
    color: {HESPIA_TEXT};
    border: 1px solid {HESPIA_BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    font-size: 12px;
    selection-background-color: {HESPIA_SELECTION};
}}
QLineEdit:focus {{
    border-color: {HESPIA_ORANGE};
}}
QLineEdit:read-only {{
    background-color: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT_DIM};
}}

/* ─── Combo Box ─────────────────────────────────────────── */
QComboBox {{
    background-color: {HESPIA_INPUT};
    color: {HESPIA_TEXT};
    border: 1px solid {HESPIA_BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    min-width: 80px;
}}
QComboBox:focus {{
    border-color: {HESPIA_ORANGE};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {HESPIA_TEXT_DIM};
    margin-right: 4px;
}}
QComboBox QAbstractItemView {{
    background-color: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT};
    border: 1px solid {HESPIA_BORDER};
    selection-background-color: {HESPIA_ORANGE};
    selection-color: white;
}}

/* ─── Spin Box ──────────────────────────────────────────── */
QSpinBox {{
    background-color: {HESPIA_INPUT};
    color: {HESPIA_TEXT};
    border: 1px solid {HESPIA_BORDER};
    border-radius: 4px;
    padding: 4px 6px;
}}
QSpinBox:focus {{
    border-color: {HESPIA_ORANGE};
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
    color: {HESPIA_TEXT};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {HESPIA_BORDER};
    border-radius: 2px;
    background-color: {HESPIA_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {HESPIA_ORANGE};
    border-color: {HESPIA_ORANGE};
}}
QCheckBox::indicator:hover {{
    border-color: {HESPIA_BORDER_LIGHT};
}}

/* ─── Radio Button ──────────────────────────────────────── */
QRadioButton {{
    color: {HESPIA_TEXT};
    spacing: 6px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {HESPIA_BORDER};
    border-radius: 7px;
    background-color: {HESPIA_INPUT};
}}
QRadioButton::indicator:checked {{
    background-color: {HESPIA_ORANGE};
    border-color: {HESPIA_ORANGE};
}}

/* ─── Scroll Bars ───────────────────────────────────────── */
QScrollBar:vertical {{
    background: {HESPIA_BG_DARK};
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
    background: {HESPIA_ORANGE_LIGHT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {HESPIA_BG_DARK};
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
    background: {HESPIA_BORDER_LIGHT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ─── Group Box ─────────────────────────────────────────── */
QGroupBox {{
    color: {HESPIA_TEXT};
    border: 1px solid {HESPIA_BORDER};
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
    color: {HESPIA_ORANGE};
}}

/* ─── Splitter ──────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {HESPIA_BORDER};
}}
QSplitter::handle:horizontal {{
    width: 3px;
}}
QSplitter::handle:vertical {{
    height: 3px;
}}
QSplitter::handle:hover {{
    background-color: {HESPIA_ORANGE};
}}

/* ─── Tool Bar ──────────────────────────────────────────── */
QToolBar {{
    background-color: {HESPIA_BG_DARK};
    border-bottom: 1px solid {HESPIA_BORDER};
    spacing: 4px;
    padding: 3px 6px;
}}

/* ─── Labels ────────────────────────────────────────────── */
QLabel#titleLabel {{
    font-size: 16px;
    font-weight: bold;
    color: {HESPIA_ORANGE};
}}
QLabel#sectionLabel {{
    font-size: 12px;
    font-weight: bold;
    color: {HESPIA_TEXT};
    padding: 4px 0;
}}
QLabel#dimLabel {{
    color: {HESPIA_TEXT_DIM};
    font-size: 11px;
}}
QLabel#statusIndicator[status="running"] {{
    color: {HESPIA_GREEN};
    font-weight: bold;
}}
QLabel#statusIndicator[status="stopped"] {{
    color: {HESPIA_RED};
    font-weight: bold;
}}

/* ─── Tree Widget ───────────────────────────────────────── */
QTreeWidget {{
    background-color: {HESPIA_BG};
    color: {HESPIA_TEXT};
    border: 1px solid {HESPIA_BORDER};
    alternate-background-color: {HESPIA_TABLE_ALT};
}}
QTreeWidget::item:selected {{
    background-color: {HESPIA_SELECTION};
    color: {HESPIA_TEXT_BRIGHT};
}}
QTreeWidget::item:hover {{
    background-color: {HESPIA_TABLE_ALT};
}}

/* ─── List Widget ───────────────────────────────────────── */
QListWidget {{
    background-color: {HESPIA_BG};
    color: {HESPIA_TEXT};
    border: 1px solid {HESPIA_BORDER};
}}
QListWidget::item:selected {{
    background-color: {HESPIA_ORANGE};
    color: white;
}}
QListWidget::item:hover {{
    background-color: {HESPIA_TABLE_ALT};
}}

/* ─── Tool Tip ──────────────────────────────────────────── */
QToolTip {{
    background-color: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT_BRIGHT};
    border: 1px solid {HESPIA_ORANGE};
    padding: 4px 8px;
    border-radius: 3px;
    font-size: 11px;
}}

/* ─── Progress Bar ──────────────────────────────────────── */
QProgressBar {{
    background-color: {HESPIA_BG_DARK};
    border: 1px solid {HESPIA_BORDER};
    border-radius: 3px;
    text-align: center;
    color: {HESPIA_TEXT};
    height: 14px;
}}
QProgressBar::chunk {{
    background-color: {HESPIA_ORANGE};
    border-radius: 2px;
}}

/* ─── Dialogs ───────────────────────────────────────────── */
QDialog {{
    background-color: {HESPIA_BG};
}}

/* ─── Frame ─────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {HESPIA_BORDER};
}}
"""

# Extra button-specific styles to apply dynamically
INTERCEPT_ON_STYLE = f"""
    QPushButton {{
        background-color: {HESPIA_ORANGE};
        color: white;
        border: 2px solid {HESPIA_ORANGE_LIGHT};
        font-weight: bold;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {HESPIA_ORANGE_LIGHT};
    }}
"""

INTERCEPT_OFF_STYLE = f"""
    QPushButton {{
        background-color: {HESPIA_INTERCEPT_OFF};
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
    background: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT_DIM};
    border: 1px solid {HESPIA_BORDER};
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
    background: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT_DIM};
    border: 1px solid {HESPIA_BORDER};
}}
"""

MODERN_FORWARD_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {HESPIA_ORANGE_LIGHT}, stop:1 {HESPIA_ORANGE});
    color: white;
    border: 1px solid {HESPIA_ORANGE_DARK};
    border-radius: 4px;
    font-weight: bold;
    padding: 4px 14px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {HESPIA_ORANGE}, stop:1 {HESPIA_ORANGE_DARK});
}}
QPushButton:pressed {{
    background: #d94e10;
}}
QPushButton:disabled {{
    background: {HESPIA_BG_DARK}bb;
    color: {HESPIA_TEXT_DIM}aa;
    border: 1px solid {HESPIA_BORDER};
}}
"""

MODERN_ACTION_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {HESPIA_ORANGE_LIGHT}, stop:1 {HESPIA_ORANGE});
    color: white;
    border: 1px solid {HESPIA_ORANGE_DARK};
    border-radius: 4px;
    font-weight: bold;
    padding: 6px 16px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {HESPIA_ORANGE}, stop:1 {HESPIA_ORANGE_DARK});
    border-color: {HESPIA_ORANGE};
}}
QPushButton:pressed {{
    background: {HESPIA_ORANGE_DARK};
}}
QPushButton:disabled {{
    background: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT_DIM};
    border: 1px solid {HESPIA_BORDER};
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
    background: {HESPIA_BG_DARK};
    color: {HESPIA_TEXT_DIM};
    border: 1px solid {HESPIA_BORDER};
}}
"""
