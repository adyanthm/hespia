"""
Request/Response Editor Widget.
Provides raw HTTP viewer with Pretty, Hex, and Base64 views.
"""
import json
import base64
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabBar, QStackedWidget,
    QPushButton, QPlainTextEdit, QLabel, QFrame, QSplitter,
    QMenu, QApplication, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QRect, QSize
from PySide6.QtGui import (
    QFont, QTextCharFormat, QColor, QSyntaxHighlighter,
    QTextDocument, QPainter, QAction, QKeySequence
)
from ui.styles import (
    HESPIA_ORANGE, HESPIA_BG, HESPIA_BG_DARK, HESPIA_BG_LIGHT, HESPIA_TEXT, HESPIA_BORDER,
    HESPIA_SELECTION, METHOD_COLORS, HTTP_STATUS_COLORS
)


# ─── HTTP Syntax Highlighter ──────────────────────────────────────────────────

class HttpSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for raw HTTP text."""

    def __init__(self, document: QTextDocument, mode: str = "request"):
        super().__init__(document)
        self.mode = mode
        self._first_line = True

        self.formats = {
            "method":    self._fmt("#0000bb", bold=True),  # Deep Blue
            "path":      self._fmt("#228b22"),             # Forest Green
            "version":   self._fmt("#888888"),             # Gray
            "header_key": self._fmt("#800000"),             # Maroon
            "header_val": self._fmt("#000000"),             # Black
            "status_ok":  self._fmt("#008800", bold=True),  # Green
            "status_err": self._fmt("#cc0000", bold=True),  # Red
            "status_warn": self._fmt("#886600", bold=True),  # Brown/Orange
            "json_key":  self._fmt("#000080"),             # Navy
            "json_str":  self._fmt("#008000"),             # Green
            "json_num":  self._fmt("#ff00ff"),             # Magenta
            "json_kw":   self._fmt("#0000ff", bold=True),  # Blue
            "param_key": self._fmt("#000080"),             # Navy
            "param_val": self._fmt("#663300"),             # Brown
        }

    def _fmt(self, color: str, bold: bool = False) -> QTextCharFormat:
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        if bold:
            f.setFontWeight(700)
        return f

    def highlightBlock(self, text: str):
        block_num = self.currentBlock().blockNumber()

        if block_num == 0:
            if self.mode == "request":
                # Highlight method path version
                parts = text.split(" ", 2)
                pos = 0
                if len(parts) >= 1:
                    self.setFormat(pos, len(parts[0]), self.formats["method"])
                    pos += len(parts[0]) + 1
                if len(parts) >= 2:
                    self.setFormat(pos, len(parts[1]), self.formats["path"])
                    pos += len(parts[1]) + 1
                if len(parts) >= 3:
                    self.setFormat(pos, len(parts[2]), self.formats["version"])
            else:
                # Response: HTTP/1.1 200 OK
                parts = text.split(" ", 2)
                pos = 0
                if len(parts) >= 1:
                    self.setFormat(pos, len(parts[0]), self.formats["version"])
                    pos += len(parts[0]) + 1
                if len(parts) >= 2:
                    code = parts[1].strip()
                    if code.startswith("2"):
                        fmt = self.formats["status_ok"]
                    elif code.startswith(("4", "5")):
                        fmt = self.formats["status_err"]
                    else:
                        fmt = self.formats["status_warn"]
                    self.setFormat(pos, len(parts[1]), fmt)
                    pos += len(parts[1]) + 1
                if len(parts) >= 3:
                    self.setFormat(pos, len(parts[2]), self.formats["version"])
            return

        # Header lines (before blank line)
        if text.strip() == "":
            return  # separator

        if ":" in text and not text.startswith("{") and not text.startswith("["):
            colon = text.index(":")
            self.setFormat(0, colon, self.formats["header_key"])
            self.setFormat(colon, len(text) - colon, self.formats["header_val"])
            return

        # JSON body
        stripped = text.strip()
        if stripped.startswith(("{", "[", '"', "}")):
            self._highlight_json(text)
        elif "&" in text and "=" in text:
            self._highlight_urlencoded(text)

    def _highlight_json(self, text: str):
        # Simple JSON highlighting
        patterns = [
            (r'"([^"\\]|\\.)*"\s*:', self.formats["json_key"]),
            (r':\s*"([^"\\]|\\.)*"', self.formats["json_str"]),
            (r':\s*-?\d+\.?\d*', self.formats["json_num"]),
            (r'\b(true|false|null)\b', self.formats["json_kw"]),
        ]
        for pattern, fmt in patterns:
            for m in re.finditer(pattern, text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)

    def _highlight_urlencoded(self, text: str):
        parts = text.split("&")
        pos = 0
        for part in parts:
            if "=" in part:
                eq = part.index("=")
                self.setFormat(pos, eq, self.formats["param_key"])
                self.setFormat(pos + eq, len(part) - eq, self.formats["param_val"])
            pos += len(part) + 1


# ─── Line Number Area ─────────────────────────────────────────────────────────

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor._line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor._paint_line_numbers(event)


# ─── Code Editor with Line Numbers ───────────────────────────────────────────

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None, mode: str = "request"):
        super().__init__(parent)
        self.mode = mode
        self.line_area = LineNumberArea(self)
        self._highlighter = HttpSyntaxHighlighter(self.document(), mode)

        font = QFont()
        font.setFamily("Cascadia Code")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(11)
        if not font.exactMatch():
            font.setFamily("Consolas")
        if not font.exactMatch():
            font.setFamily("Courier New")
        self.setFont(font)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width(0)

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabStopDistance(28)

    send_to_decoder = Signal(str)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        
        selected_text = self.textCursor().selectedText()
        if selected_text:
            menu.addSeparator()
            decoder_action = menu.addAction("Send to Decoder")
            decoder_action.triggered.connect(lambda: self.send_to_decoder.emit(selected_text))
            
        menu.exec(event.globalPos())

    def _line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return 8 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self._line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_area.scroll(0, dy)
        else:
            self.line_area.update(0, rect.y(), self.line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_area.setGeometry(QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height()))

    def _paint_line_numbers(self, event):
        painter = QPainter(self.line_area)
        painter.fillRect(event.rect(), QColor(HESPIA_BG_DARK))

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                num = str(block_num + 1)
                painter.setPen(QColor("#555555"))
                painter.drawText(
                    0, top, self.line_area.width() - 3,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, num
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_num += 1


# ─── Request/Response Editor Panel ───────────────────────────────────────────

class RequestEditor(QWidget):
    """
    Full request or response editor with Raw / Pretty / Hex / Base64 views.
    """
    content_changed = Signal(str)  # emits raw text when edited
    send_to_decoder = Signal(str)

    def __init__(self, title: str = "Request", mode: str = "request",
                 read_only: bool = False, parent=None):
        super().__init__(parent)
        self.title = title
        self.mode = mode
        self.read_only = read_only
        self._raw_text = ""

        self._setup_ui()
        self._raw_editor.send_to_decoder.connect(self.send_to_decoder.emit)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar
        header = QFrame()
        header.setFixedHeight(32)
        header.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.setSpacing(4)

        lbl = QLabel(self.title.upper())
        lbl.setStyleSheet(f"color:{HESPIA_ORANGE}; font-weight:bold; font-size:11px; letter-spacing:1px;")
        hl.addWidget(lbl)
        hl.addStretch()

        # View selector
        self._view_combo = QComboBox()
        self._view_combo.addItems(["Raw", "Pretty", "Hex", "Base64"])
        self._view_combo.setFixedWidth(90)
        self._view_combo.setStyleSheet(f"""
            QComboBox {{
                background:{HESPIA_BG_LIGHT};
                color:{HESPIA_TEXT};
                border:1px solid {HESPIA_BORDER};
                border-radius:2px;
                padding:2px 4px;
                font-size:11px;
            }}
        """)
        self._view_combo.currentTextChanged.connect(self._switch_view)
        hl.addWidget(self._view_combo)

        if not self.read_only:
            self._word_wrap_btn = QPushButton("⏎ Wrap")
            self._word_wrap_btn.setFixedHeight(22)
            self._word_wrap_btn.setCheckable(True)
            self._word_wrap_btn.setStyleSheet("font-size:10px; padding:0 6px;")
            self._word_wrap_btn.toggled.connect(self._toggle_wrap)
            hl.addWidget(self._word_wrap_btn)

        layout.addWidget(header)

        # ── Editor stack
        self._stack = QStackedWidget()

        # Raw view (editable)
        self._raw_editor = CodeEditor(mode=self.mode)
        self._raw_editor.setReadOnly(self.read_only)
        self._raw_editor.setPlaceholderText(f"No {self.title.lower()} captured yet...")
        if not self.read_only:
            self._raw_editor.textChanged.connect(self._on_text_changed)
        self._stack.addWidget(self._raw_editor)

        # Pretty view (read-only, formatted)
        self._pretty_editor = QPlainTextEdit()
        self._pretty_editor.setReadOnly(True)
        self._pretty_editor.setPlaceholderText("Switch to Raw to edit")
        self._pretty_editor.setFont(self._raw_editor.font())
        self._stack.addWidget(self._pretty_editor)

        # Hex view
        self._hex_editor = QPlainTextEdit()
        self._hex_editor.setReadOnly(True)
        self._hex_editor.setFont(self._raw_editor.font())
        self._stack.addWidget(self._hex_editor)

        # Base64 view
        self._b64_editor = QPlainTextEdit()
        self._b64_editor.setReadOnly(True)
        self._b64_editor.setFont(self._raw_editor.font())
        self._stack.addWidget(self._b64_editor)

        layout.addWidget(self._stack)

        # ── Status bar
        status_bar = QFrame()
        status_bar.setFixedHeight(22)
        status_bar.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-top:1px solid {HESPIA_BORDER};")
        sl = QHBoxLayout(status_bar)
        sl.setContentsMargins(8, 0, 8, 0)
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color:#888; font-size:10px;")
        sl.addWidget(self._status_lbl)
        sl.addStretch()
        self._length_lbl = QLabel("")
        self._length_lbl.setStyleSheet("color:#888; font-size:10px;")
        sl.addWidget(self._length_lbl)
        layout.addWidget(status_bar)

    def _on_text_changed(self):
        self._raw_text = self._raw_editor.toPlainText()
        size = len(self._raw_text.encode("utf-8"))
        self._length_lbl.setText(f"{size} bytes  |  {len(self._raw_text.splitlines())} lines")
        self.content_changed.emit(self._raw_text)

    def _switch_view(self, view: str):
        if view == "Raw":
            self._stack.setCurrentIndex(0)
        elif view == "Pretty":
            self._update_pretty()
            self._stack.setCurrentIndex(1)
        elif view == "Hex":
            self._update_hex()
            self._stack.setCurrentIndex(2)
        elif view == "Base64":
            self._update_b64()
            self._stack.setCurrentIndex(3)

    def _update_pretty(self):
        raw = self._raw_editor.toPlainText()
        # Try JSON pretty-print for body
        lines = raw.split("\n")
        out_lines = []
        in_body = False
        body_lines = []
        for line in lines:
            if not in_body:
                out_lines.append(line)
                if line.strip() == "":
                    in_body = True
            else:
                body_lines.append(line)
        body = "\n".join(body_lines)
        try:
            obj = json.loads(body)
            pretty_body = json.dumps(obj, indent=2)
            out_lines.append(pretty_body)
        except Exception:
            out_lines.extend(body_lines)
        self._pretty_editor.setPlainText("\n".join(out_lines))

    def _update_hex(self):
        raw = self._raw_editor.toPlainText()
        data = raw.encode("utf-8", errors="replace")
        hex_lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i + 16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            hex_lines.append(f"{i:08X}  {hex_part:<48}  |{ascii_part}|")
        self._hex_editor.setPlainText("\n".join(hex_lines))

    def _update_b64(self):
        raw = self._raw_editor.toPlainText()
        encoded = base64.b64encode(raw.encode("utf-8", errors="replace")).decode()
        self._b64_editor.setPlainText(encoded)

    def _toggle_wrap(self, checked: bool):
        mode = QPlainTextEdit.LineWrapMode.WidgetWidth if checked else QPlainTextEdit.LineWrapMode.NoWrap
        self._raw_editor.setLineWrapMode(mode)
        self._pretty_editor.setLineWrapMode(mode)

    # ── Public API ─────────────────────────────────────────────────────────

    def set_content(self, text: str, status_hint: str = ""):
        """Set the editor content."""
        self._raw_text = text
        self._raw_editor.setPlainText(text)
        self._status_lbl.setText(status_hint)
        size = len(text.encode("utf-8"))
        self._length_lbl.setText(f"{size} bytes  |  {len(text.splitlines())} lines")
        # Refresh current view
        view = self._view_combo.currentText()
        if view == "Pretty":
            self._update_pretty()
        elif view == "Hex":
            self._update_hex()
        elif view == "Base64":
            self._update_b64()

    def set_bytes_content(self, data: bytes, headers: dict = None):
        """Set content from raw bytes with headers."""
        if headers:
            hdr_lines = "\n".join(f"{k}: {v}" for k, v in headers.items())
            try:
                body = data.decode("utf-8", errors="replace")
            except Exception:
                body = repr(data)
            text = hdr_lines + "\n\n" + body
        else:
            text = data.decode("utf-8", errors="replace")
        self.set_content(text)

    def get_content(self) -> str:
        """Get current raw text content."""
        return self._raw_editor.toPlainText()

    def clear(self):
        """Clear all content."""
        self._raw_editor.setPlainText("")
        self._pretty_editor.setPlainText("")
        self._hex_editor.setPlainText("")
        self._b64_editor.setPlainText("")
        self._status_lbl.setText("")
        self._length_lbl.setText("")

    def set_read_only(self, ro: bool):
        self._raw_editor.setReadOnly(ro)

    def highlight_search(self, term: str):
        """Highlight search term in the editor."""
        if not term:
            return
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#ff8c00"))
        fmt.setForeground(QColor("#000000"))
        cursor = self._raw_editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        while True:
            cursor = self._raw_editor.document().find(term, cursor)
            if cursor.isNull():
                break
            cursor.mergeCharFormat(fmt)


# ─── Split Request/Response Viewer ───────────────────────────────────────────

class RequestResponseSplitter(QWidget):
    """
    A horizontally/vertically split widget showing request on left
    and response on right (or top/bottom).
    """
    send_to_decoder = Signal(str)

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._splitter = QSplitter(orientation)
        self._request_editor = RequestEditor("Request", mode="request")
        self._response_editor = RequestEditor("Response", mode="response", read_only=True)

        self._splitter.addWidget(self._request_editor)
        self._splitter.addWidget(self._response_editor)
        self._splitter.setSizes([400, 400])

        self._request_editor.send_to_decoder.connect(self.send_to_decoder.emit)
        self._response_editor.send_to_decoder.connect(self.send_to_decoder.emit)

        layout.addWidget(self._splitter)

    @property
    def request_editor(self) -> RequestEditor:
        return self._request_editor

    @property
    def response_editor(self) -> RequestEditor:
        return self._response_editor

    def set_flow(self, req_text: str, resp_text: str = "",
                 req_hint: str = "", resp_hint: str = ""):
        self._request_editor.set_content(req_text, req_hint)
        self._response_editor.set_content(resp_text, resp_hint)
