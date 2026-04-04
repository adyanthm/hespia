"""
Decoder Tab - Encode/Decode data in various formats.
"""
import base64
import urllib.parse
import html
import binascii
import hashlib
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QComboBox, QFrame, QScrollArea,
    QSizePolicy, QPlainTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from ui.styles import (
    HESPIA_ORANGE, HESPIA_BG, HESPIA_BG_DARK, HESPIA_BG_LIGHT, HESPIA_TEXT,
    HESPIA_BORDER, HESPIA_TEXT_DIM
)


# ─── Decode/Encode Operations ─────────────────────────────────────────────────

ENCODE_OPS = {
    "URL encode":          lambda s: urllib.parse.quote(s, safe=""),
    "URL decode":          lambda s: urllib.parse.unquote(s),
    "URL encode (all chars)": lambda s: "".join(f"%{b:02X}" for b in s.encode()),
    "Base64 encode":       lambda s: base64.b64encode(s.encode()).decode(),
    "Base64 decode":       lambda s: base64.b64decode(s.encode() + b"==").decode("utf-8", errors="replace"),
    "Base64 URL encode":   lambda s: base64.urlsafe_b64encode(s.encode()).decode(),
    "Base64 URL decode":   lambda s: base64.urlsafe_b64decode(s.encode() + b"==").decode("utf-8", errors="replace"),
    "HTML encode":         lambda s: html.escape(s),
    "HTML decode":         lambda s: html.unescape(s),
    "Hex encode":          lambda s: binascii.hexlify(s.encode()).decode(),
    "Hex decode":          lambda s: binascii.unhexlify(s.encode()).decode("utf-8", errors="replace"),
    "ASCII Hex encode":    lambda s: " ".join(f"{ord(c):02x}" for c in s),
    "Gzip compress":       lambda s: _gzip_compress(s),
    "Gzip decompress":     lambda s: _gzip_decompress(s),
    "MD5":                 lambda s: hashlib.md5(s.encode()).hexdigest(),
    "SHA-1":               lambda s: hashlib.sha1(s.encode()).hexdigest(),
    "SHA-256":             lambda s: hashlib.sha256(s.encode()).hexdigest(),
    "SHA-512":             lambda s: hashlib.sha512(s.encode()).hexdigest(),
    "JSON pretty":         lambda s: json.dumps(json.loads(s), indent=2),
    "JSON compact":        lambda s: json.dumps(json.loads(s)),
}


def _gzip_compress(s: str) -> str:
    import gzip
    compressed = gzip.compress(s.encode())
    return base64.b64encode(compressed).decode()


def _gzip_decompress(s: str) -> str:
    import gzip
    data = base64.b64decode(s.encode() + b"==")
    return gzip.decompress(data).decode("utf-8", errors="replace")


# ─── Decoder Row ──────────────────────────────────────────────────────────────

class DecoderRow(QFrame):
    """One encode/decode row in the chain decoder."""

    result_changed = Signal(str)
    add_row_requested = Signal(str)  # passes result down

    def __init__(self, initial_text: str = "", parent=None):
        super().__init__(parent)
        self._setup_ui(initial_text)

    def _setup_ui(self, initial_text: str):
        self.setStyleSheet(
            f"QFrame {{ background:{HESPIA_BG_LIGHT}; border:1px solid {HESPIA_BORDER};"
            f" border-radius:4px; margin:2px 0; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # ── Control row
        ctrl = QHBoxLayout()
        ctrl.setSpacing(6)

        self._op_combo = QComboBox()
        self._op_combo.addItem("— Select operation —")
        for op in ENCODE_OPS.keys():
            self._op_combo.addItem(op)
        self._op_combo.setFixedWidth(220)
        ctrl.addWidget(self._op_combo)

        self._decode_btn = QPushButton("▶ Apply")
        self._decode_btn.setFixedHeight(26)
        self._decode_btn.setFixedWidth(80)
        self._decode_btn.clicked.connect(self._apply)
        ctrl.addWidget(self._decode_btn)

        self._auto_detect_btn = QPushButton("🔍 Smart Decode")
        self._auto_detect_btn.setFixedHeight(26)
        self._auto_detect_btn.setToolTip("Auto-detect encoding and decode")
        self._auto_detect_btn.clicked.connect(self._smart_decode)
        ctrl.addWidget(self._auto_detect_btn)

        ctrl.addStretch()

        self._add_btn = QPushButton("+ Add step ↓")
        self._add_btn.setFixedHeight(26)
        self._add_btn.setToolTip("Add result as next decode step")
        self._add_btn.clicked.connect(self._add_next)
        ctrl.addWidget(self._add_btn)

        layout.addLayout(ctrl)

        # ── Text editor
        self._editor = QPlainTextEdit()
        self._editor.setPlainText(initial_text)
        self._editor.setMinimumHeight(80)
        self._editor.setMaximumHeight(200)
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(11)
        self._editor.setFont(font)
        self._editor.setStyleSheet(
            f"QPlainTextEdit {{ background:{HESPIA_BG}; color:{HESPIA_TEXT};"
            f" border:1px solid {HESPIA_BORDER}; padding:4px; }}"
        )
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        # ── Status
        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:10px;")
        layout.addWidget(self._status)

    def _apply(self):
        op_name = self._op_combo.currentText()
        if op_name not in ENCODE_OPS:
            return
        text = self._editor.toPlainText()
        try:
            result = ENCODE_OPS[op_name](text)
            self._editor.setPlainText(result)
            length = len(result.encode())
            self._status.setText(f"✓ {op_name} — {length} bytes")
            self._status.setStyleSheet(f"color:#4CAF50; font-size:10px;")
            self.result_changed.emit(result)
        except Exception as e:
            self._status.setText(f"✗ Error: {e}")
            self._status.setStyleSheet(f"color:#F44336; font-size:10px;")

    def _smart_decode(self):
        text = self._editor.toPlainText().strip()
        if not text:
            return
        # Try to auto-detect
        result, method = self._auto_detect(text)
        if result:
            self._editor.setPlainText(result)
            self._status.setText(f"✓ Auto-detected: {method}")
            self._status.setStyleSheet(f"color:{HESPIA_ORANGE}; font-size:10px;")
        else:
            self._status.setText("? Could not auto-detect encoding")
            self._status.setStyleSheet(f"color:#FF9800; font-size:10px;")

    def _auto_detect(self, text: str):
        """Try various decodings and return the first valid one."""
        # Base64
        try:
            padded = text + "==" * ((4 - len(text) % 4) % 4)
            decoded = base64.b64decode(padded).decode("utf-8")
            if decoded.isprintable():
                return decoded, "Base64 decode"
        except Exception:
            pass

        # URL encoded
        if "%" in text:
            try:
                decoded = urllib.parse.unquote(text)
                if decoded != text:
                    return decoded, "URL decode"
            except Exception:
                pass

        # HTML entities
        if "&" in text and ";" in text:
            try:
                decoded = html.unescape(text)
                if decoded != text:
                    return decoded, "HTML decode"
            except Exception:
                pass

        # Hex
        try:
            clean = text.replace(" ", "").replace("\n", "")
            if all(c in "0123456789abcdefABCDEF" for c in clean) and len(clean) % 2 == 0:
                decoded = binascii.unhexlify(clean).decode("utf-8")
                return decoded, "Hex decode"
        except Exception:
            pass

        return None, None

    def _add_next(self):
        self.add_row_requested.emit(self._editor.toPlainText())

    def _on_text_changed(self):
        text = self._editor.toPlainText()
        length = len(text.encode())
        self.result_changed.emit(text)

    def get_text(self) -> str:
        return self._editor.toPlainText()

    def set_text(self, text: str):
        self._editor.setPlainText(text)


# ─── Decoder Tab ─────────────────────────────────────────────────────────────

class DecoderTab(QWidget):
    """
    Decoder/Encoder tab — chain multiple encode/decode operations.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header
        header = QFrame()
        header.setFixedHeight(36)
        header.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 4, 10, 4)
        hl.setSpacing(8)

        title = QLabel("Decoder / Encoder")
        title.setStyleSheet(f"color:{HESPIA_ORANGE}; font-weight:bold; font-size:13px;")
        hl.addWidget(title)
        hl.addStretch()

        new_tab_btn = QPushButton("+ New Chain")
        new_tab_btn.setFixedHeight(26)
        new_tab_btn.clicked.connect(self._new_chain)
        hl.addWidget(new_tab_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedHeight(26)
        clear_btn.clicked.connect(self._clear_all)
        hl.addWidget(clear_btn)

        main_layout.addWidget(header)

        # ── Quick encode toolbar
        quick_bar = QFrame()
        quick_bar.setFixedHeight(34)
        quick_bar.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        ql = QHBoxLayout(quick_bar)
        ql.setContentsMargins(8, 4, 8, 4)
        ql.setSpacing(4)

        ql.addWidget(QLabel("Quick:"))
        for label, op in [
            ("URL↑", "URL encode"), ("URL↓", "URL decode"),
            ("B64↑", "Base64 encode"), ("B64↓", "Base64 decode"),
            ("HTML↑", "HTML encode"), ("HTML↓", "HTML decode"),
            ("HEX↑", "Hex encode"), ("HEX↓", "Hex decode"),
            ("MD5", "MD5"), ("SHA256", "SHA-256"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setMinimumWidth(56) # Dynamic width instead of fixed
            btn.setStyleSheet(f"padding: 0 4px; font-size: 11px;")
            btn.setToolTip(op)
            btn.setProperty("op", op)
            btn.clicked.connect(self._quick_op)
            ql.addWidget(btn)
        ql.addStretch()
        main_layout.addWidget(quick_bar)

        # ── Tabs for multiple chains
        self._chain_tabs = self._make_chain_tabs()
        main_layout.addWidget(self._chain_tabs, 1)

    def _make_chain_tabs(self):
        from PySide6.QtWidgets import QTabWidget
        tabs = QTabWidget()
        tabs.setTabsClosable(True)
        tabs.tabCloseRequested.connect(lambda i: tabs.removeTab(i) if tabs.count() > 1 else None)
        self._add_chain_tab(tabs, "Chain 1")
        return tabs

    def _add_chain_tab(self, tabs, name: str):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        container._row_layout = layout

        # First row
        row = DecoderRow("")
        row.add_row_requested.connect(lambda text: self._append_row(container, text))
        layout.addWidget(row)
        layout.addStretch()

        scroll.setWidget(container)
        tabs.addTab(scroll, name)
        return scroll

    def _append_row(self, container: QWidget, initial_text: str = ""):
        layout = container._row_layout
        # Remove stretch
        stretch_item = layout.takeAt(layout.count() - 1)
        row = DecoderRow(initial_text)
        row.add_row_requested.connect(lambda text: self._append_row(container, text))
        layout.addWidget(row)
        layout.addStretch()

    def _new_chain(self):
        count = self._chain_tabs.count() + 1
        self._add_chain_tab(self._chain_tabs, f"Chain {count}")
        self._chain_tabs.setCurrentIndex(self._chain_tabs.count() - 1)

    def _clear_all(self):
        while self._chain_tabs.count() > 0:
            self._chain_tabs.removeTab(0)
        self._add_chain_tab(self._chain_tabs, "Chain 1")

    def _quick_op(self):
        op = self.sender().property("op")
        if not op or op not in ENCODE_OPS:
            return
        # Get current chain container
        scroll = self._chain_tabs.currentWidget()
        if not scroll:
            return
        container = scroll.widget()
        layout = container._row_layout
        # Find last DecoderRow
        last_row = None
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.widget(), DecoderRow):
                last_row = item.widget()
        if last_row:
            text = last_row.get_text()
            try:
                result = ENCODE_OPS[op](text)
                self._append_row(container, result)
            except Exception as e:
                self._append_row(container, f"Error: {e}")

    def set_content(self, text: str):
        """Pre-populate the first row of current chain."""
        scroll = self._chain_tabs.currentWidget()
        if not scroll:
            return
        container = scroll.widget()
        layout = container._row_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.widget(), DecoderRow):
                item.widget().set_text(text)
                return
