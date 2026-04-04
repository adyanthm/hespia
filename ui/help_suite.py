"""
Hespia Documentation Suite - Searchable, multi-page help system.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QListWidgetItem, QTextEdit, QLineEdit, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from ui.styles import (
    HESPIA_BG, HESPIA_TEXT, HESPIA_ORANGE, HESPIA_BORDER, HESPIA_TEXT_DIM, HESPIA_BG_DARK, HESPIA_INFO_BG
)

HELP_DOCS = {
    "Getting Started": {
        "icon": "⚡",
        "title": "Getting Started with Hespia",
        "content": """
            <h1>Getting Started with Hespia</h1>
            <p>Hespia is a professional-grade web security toolkit. follow these steps to begin testing:</p>
            <h3>1. Start the Proxy</h3>
            <p>On the main banner at the top, click <b>▶ Start Proxy</b>. By default, Hespia listens on <b>127.0.0.1:8080</b>.</p>
            <h3>2. Configure Browser Proxy</h3>
            <p><b>Recommended: Mozilla Firefox</b>. Firefox supports independent proxy settings and its own certificate store, allowing you to isolate your security testing from the rest of your system traffic.</p>
            <ul style='line-height:1.8;'>
                <li>Open Firefox <b>Settings → General</b></li>
                <li>Scroll to <b>Network Settings → Settings</b></li>
                <li>Select <b>Manual proxy configuration</b></li>
                <li>HTTP Proxy: <b>127.0.0.1</b> | Port: <b>8080</b></li>
                <li>Check the box <b>Also use this proxy for HTTPS</b></li>
                <li>Click <b>OK</b>. All Firefox traffic is now flowing through Hespia.</li>
            </ul>
        """
    },
    "CA Certificate": {
        "icon": "🔒",
        "title": "Installing CA Certificate",
        "content": """
            <h1>Installing CA Certificate</h1>
            <p>To intercept HTTPS (encrypted) traffic, Hespia must act as a 'Man-in-the-Middle'. Browsers will block this by default until you trust Hespia's Root CA.</p>
            <h3>Step-by-Step Certificate Installation:</h3>
            <ol style='line-height:1.8;'>
                <li>Ensure Hespia is <b>Running</b> and your browser proxy is configured.</li>
                <li>Navigate to: <b style='color:#2563eb;'>http://mitm.it</b></li>
                <li>Under the <b>Windows</b> or <b>Other</b> icon, click the <b>Download</b> button.</li>
                <li><b>Firefox Setup:</b> Open Firefox Settings → Privacy & Security → Certificates → <b>View Certificates</b>. Click <b>Import...</b>, select the downloaded file, check <b>Trust this CA to identify websites</b>, and click OK.</li>
                <li><b>System/Chrome Setup:</b> Double-click the <b>.cer</b> file → Install Certificate → Local Machine → Place in <b>Trusted Root Certification Authorities</b> store.</li>
            </ol>
            <div style='background-color:%s; padding:12px; border-radius:4px;'><b>Tip:</b> If mitm.it doesn't load, ensure the proxy is active and you are navigating to the exact URL (no https).</div>
        """ % HESPIA_INFO_BG
    },
    "Proxy & Intercept": {
        "icon": "🛡️",
        "title": "Proxy & Intercept",
        "content": """
            <h1>Proxy & Intercept</h1>
            <p>This tab captures everything. Use it to observe flow data or pause traffic for modification.</p>
            <h3>1. HTTP History</h3>
            <p>Every request/response is recorded here. Right-click any row to view options like <b>Send to Repeater</b> or <b>Send to Intruder</b>.</p>
            <h3>2. Manual Intercept</h3>
            <p>Toggle <b>Intercept is ON</b> to pause requests in real-time.</p>
            <ul style='line-height:1.6;'>
                <li><b>Editable Editor:</b> Modify headers (User-Agent, Cookies) or POST data before it leaves your machine.</li>
                <li><b>Forward:</b> Release the request to the destination server.</li>
                <li><b>Drop:</b> Kill the connection entirely before it reaches the server.</li>
                <li><b>Forward All:</b> Flush the entire intercepted queue at once (useful for multiple background API calls).</li>
            </ul>
        """
    },
    "Repeater": {
        "icon": "🔄",
        "title": "HTTP Repeater",
        "content": """
            <h1>HTTP Repeater</h1>
            <p>Repeater allows you to manually re-send a single request over and over while tweaking parameters.</p>
            <h3>Features:</h3>
            <ul>
                <li><b>Host Sync:</b> Hespia automatically updates the 'Host:' header to match the destination URL, preventing common 404/Invalid Host errors.</li>
                <li><b>Advanced History:</b> Use the <b>&lt;</b> and <b>&gt;</b> navigation buttons to jump between every version of the request you've sent.</li>
                <li><b>Raw Access:</b> Full manual control over HTTP methods, versions, and headers.</li>
            </ul>
        """
    },
    "Intruder": {
        "icon": "⚔️",
        "title": "Intruder (Automated Attacks)",
        "content": """
            <h1>Intruder (Automated Attacks)</h1>
            <p>Used for brute-forcing, ID enumeration, and automated fuzzing.</p>
            <h3>How to use:</h3>
            <ol>
                <li><b>Markers (§):</b> Highlight text in the request and click <b>Add §</b> to make it a payload position.</li>
                <li><b>Attack Modes:</b>
                    <ul>
                        <li><b>Sniper:</b> One list, one marker at a time. High performance.</li>
                        <li><b>Pitchfork:</b> Parallel lists for parallel markers (useful for synced creds).</li>
                        <li><b>Cluster Bomb:</b> Every combination of all payload lists (useful for exhaustive brute force).</li>
                    </ul>
                </li>
                <li><b>Start:</b> Choose your payload list and click <b>Start Attack</b>.</li>
            </ol>
        """
    },
    "Decoder": {
        "icon": "🔡",
        "title": "Decoder / Encoder",
        "content": """
            <h1>Decoder / Encoder</h1>
            <p>The Decoder tab is for rapid transformation of data types (Base64, URL, Hex, etc.).</p>
            <h3>Ways to use:</h3>
            <ol>
                <li><b>Manual Entry:</b> Type directly into the decoder panel.</li>
                <li><b>Context Menu:</b> Highlight text in Proxy, Repeater, or Intruder, right-click and select <b>Send to Decoder</b>.</li>
            </ol>
        """
    },
    "Comparer": {
        "icon": "🔍",
        "title": "Comparer",
        "content": """
            <h1>Comparer</h1>
            <p>Compare two requests or responses to find subtle differences in logic or bypasses.</p>
            <h3>Process:</h3>
            <ol>
                <li>Send two different responses to Comparer (via right-click).</li>
                <li>Select the two items in the Comparer list.</li>
                <li>Click <b>Compare (Words)</b> or <b>Compare (Bytes)</b>.</li>
            </ol>
        """
    },
    "Target / Scope": {
        "icon": "🎯",
        "title": "Target / Scope",
        "content": """
            <h1>Target / Scope</h1>
            <p>Define which hosts are in-scope to reduce noise in your HTTP history.</p>
            <h3>Scope Management:</h3>
            <ul>
                <li>Enable <b>Use Suite Scope</b> in the Proxy settings.</li>
                <li>Add regex patterns for allowed hosts in the Target tab.</li>
            </ul>
        """
    }
}

class HespiaHelpSuite(QWidget):
    """
    Searchable documentation suite with sidebar navigation.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._show_doc("Getting Started")

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(f"""
            background-color: {HESPIA_BG_DARK}; 
            border-right: 1px solid {HESPIA_BORDER};
        """)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        # Sidebar Header
        sidebar_hdr = QFrame()
        sidebar_hdr.setFixedHeight(50)
        sidebar_hdr.setStyleSheet(f"border-bottom: 1px solid {HESPIA_BORDER}44; background: {HESPIA_BG_DARK};")
        shl = QHBoxLayout(sidebar_hdr)
        shl.setContentsMargins(20, 0, 20, 0)
        hdr_label = QLabel("NAVIGATION")
        hdr_label.setStyleSheet(f"color: {HESPIA_TEXT_DIM}; font-weight: bold; font-size: 10px; letter-spacing: 1.2px;")
        shl.addWidget(hdr_label)
        sl.addWidget(sidebar_hdr)

        # Search Bar Area
        search_container = QWidget()
        sl_search = QVBoxLayout(search_container)
        sl_search.setContentsMargins(20, 15, 20, 10)
        sl_search.setSpacing(8)
        
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search help...")
        self._search_edit.textChanged.connect(self._filter_docs)
        self._search_edit.setFixedHeight(30)
        self._search_edit.setStyleSheet(f"""
            padding: 0 10px; 
            border: 1px solid {HESPIA_BORDER}; 
            border-radius: 6px; 
            background: {HESPIA_BG};
            font-size: 12px;
        """)
        sl_search.addWidget(self._search_edit)
        sl.addWidget(search_container)

        # Doc List
        self._doc_list = QListWidget()
        self._doc_list.setStyleSheet(f"""
            QListWidget {{ 
                border: none; 
                background: transparent; 
                outline: none;
            }}
            QListWidget::item {{ 
                padding: 14px 20px; 
                border-bottom: 1px solid {HESPIA_BORDER}11;
                margin: 2px 8px;
                border-radius: 6px;
                color: {HESPIA_TEXT};
                font-size: 13px;
            }}
            QListWidget::item:selected {{ 
                background-color: {HESPIA_BG}; 
                color: {HESPIA_ORANGE}; 
                font-weight: 600;
                border-left: 3px solid {HESPIA_ORANGE};
            }}
            QListWidget::item:hover:!selected {{ 
                background-color: {HESPIA_BORDER}33; 
            }}
        """)
        self._doc_list.currentItemChanged.connect(self._on_selection_changed)
        sl.addWidget(self._doc_list, 1) # Set stretch to 1 to occupy all space
        
        # Add items
        for title in HELP_DOCS.keys():
            item = QListWidgetItem(f"{HELP_DOCS[title]['icon']}  {title}")
            item.setData(Qt.ItemDataRole.UserRole, title)
            self._doc_list.addItem(item)

        layout.addWidget(sidebar)

        # ── Content Area
        content_container = QWidget()
        content_container.setStyleSheet(f"background-color: white;")
        self._content_layout = QVBoxLayout(content_container)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        self._viewer = QTextEdit()
        self._viewer.setReadOnly(True)
        self._viewer.setStyleSheet("border: none; background-color: transparent;")
        self._content_layout.addWidget(self._viewer)

        layout.addWidget(content_container, 1)

    def _on_selection_changed(self, current, previous):
        if not current: return
        key = current.data(Qt.ItemDataRole.UserRole)
        self._show_doc(key)

    def _show_doc(self, key):
        doc = HELP_DOCS.get(key)
        if not doc: return

        # Wrap content in theme-consistent HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
                    color: {HESPIA_TEXT};
                    line-height: 1.7;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 850px;
                    margin: 0 auto;
                    padding: 50px 60px;
                }}
                h1 {{
                    color: {HESPIA_TEXT};
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 24px;
                    letter-spacing: -0.5px;
                }}
                h3 {{
                    color: {HESPIA_ORANGE};
                    font-size: 18px;
                    margin-top: 32px;
                    margin-bottom: 12px;
                    font-weight: 600;
                }}
                p {{
                    font-size: 14px;
                    margin-bottom: 18px;
                }}
                ul, ol {{
                    font-size: 14px;
                    margin-bottom: 24px;
                    padding-left: 20px;
                }}
                li {{
                    margin-bottom: 8px;
                }}
                .footer {{
                    margin-top: 60px;
                    padding-top: 24px;
                    border-top: 1px solid {HESPIA_BORDER};
                    color: {HESPIA_TEXT_DIM};
                    font-size: 12px;
                    font-weight: 500;
                }}
                code {{
                    background-color: {HESPIA_BG_DARK};
                    padding: 2px 5px;
                    border-radius: 4px;
                    font-family: 'Consolas', monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {doc['content']}
                <div class="footer">
                    Hespia Advanced Security Suite — Documentation v1.0.0
                </div>
            </div>
        </body>
        </html>
        """
        self._viewer.setHtml(html)

    def _filter_docs(self, text):
        text = text.lower()
        for i in range(self._doc_list.count()):
            item = self._doc_list.item(i)
            item.setHidden(text not in item.text().lower())
