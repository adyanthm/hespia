"""
Repeater Tab - Manually craft and replay HTTP requests.
"""
import threading
import re
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox,
    QFrame, QListWidget, QListWidgetItem, QGroupBox,
    QSpinBox, QSizePolicy, QMenu, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtGui import QColor, QFont, QTextCursor
from ui.request_editor import RequestEditor
from ui.styles import (
    HESPIA_ORANGE, HESPIA_BG, HESPIA_BG_DARK, HESPIA_TEXT, HESPIA_BORDER,
    HESPIA_TEXT_DIM, HESPIA_SUCCESS, HESPIA_ERROR, HESPIA_HEADER,
    MODERN_ACTION_STYLE, MODERN_DROP_STYLE
)


# ─── HTTP Send Worker ─────────────────────────────────────────────────────────

class SendWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, engine, host, port, is_https, raw):
        super().__init__()
        self.engine = engine
        self.host = host
        self.port = port
        self.is_https = is_https
        self.raw = raw

    def run(self):
        try:
            result = self.engine.send_raw_request(
                self.host, self.port, self.is_https, self.raw
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ─── Repeater Instance ────────────────────────────────────────────────────────

class RepeaterInstance(QWidget):
    """A single repeater request/response tab."""
    send_to_decoder = Signal(str)

    def __init__(self, engine, name: str = "Request", parent=None):
        super().__init__(parent)
        self.engine = engine
        self.name = name
        self._history = []       # list of (request_raw, response_raw)
        self._history_index = -1
        self._thread: Optional[QThread] = None
        
        # Debounce timer for auto-updates (Host, Content-Length)
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(500) # Wait 500ms before snapping
        self._debounce_timer.timeout.connect(self._apply_auto_updates)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Target bar
        target_grp = QGroupBox("Target")
        tg_layout = QHBoxLayout(target_grp)
        tg_layout.setSpacing(6)

        tg_layout.addWidget(QLabel("Host:"))
        self._host_edit = QLineEdit()
        self._host_edit.setPlaceholderText("example.com")
        self._host_edit.setFixedWidth(220)
        self._host_edit.textChanged.connect(self._sync_host_header)
        tg_layout.addWidget(self._host_edit)

        tg_layout.addWidget(QLabel("Port:"))
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(443)
        self._port_spin.setFixedWidth(75)
        tg_layout.addWidget(self._port_spin)

        self._https_check = QCheckBox("HTTPS")
        self._https_check.setChecked(True)
        self._https_check.stateChanged.connect(self._on_https_changed)
        tg_layout.addWidget(self._https_check)

        self._follow_redirects = QCheckBox("Follow Redirects")
        self._follow_redirects.setChecked(False)
        tg_layout.addWidget(self._follow_redirects)

        tg_layout.addStretch()
        layout.addWidget(target_grp)

        # ── Control toolbar
        ctrl = QFrame()
        ctrl.setFixedHeight(38)
        ctrl.setStyleSheet(f"background:{HESPIA_BG_DARK}; border:1px solid {HESPIA_BORDER}; border-radius:3px;")
        cl = QHBoxLayout(ctrl)
        cl.setContentsMargins(8, 4, 8, 4)
        cl.setSpacing(6)

        self._send_btn = QPushButton("▶ Send")
        self._send_btn.setStyleSheet(MODERN_ACTION_STYLE)
        self._send_btn.setFixedHeight(28)
        self._send_btn.setMinimumWidth(90)
        self._send_btn.setToolTip("Send request (Ctrl+Enter)")
        self._send_btn.clicked.connect(self._do_send)
        cl.addWidget(self._send_btn)

        self._cancel_btn = QPushButton("◼ Cancel")
        self._cancel_btn.setStyleSheet(MODERN_DROP_STYLE)
        self._cancel_btn.setFixedHeight(28)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._do_cancel)
        cl.addWidget(self._cancel_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{HESPIA_BORDER};")
        cl.addWidget(sep)

        # History navigation
        btn_style = f"""
            QPushButton {{
                color: {HESPIA_TEXT};
                font-weight: bold;
                font-size: 14px;
                border: 1px solid {HESPIA_BORDER};
                border-radius: 4px;
                background-color: {HESPIA_BG};
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {HESPIA_HEADER};
                color: {HESPIA_ORANGE};
            }}
            QPushButton:pressed {{
                background-color: {HESPIA_BG_DARK};
            }}
            QPushButton:disabled {{
                color: {HESPIA_TEXT_DIM};
                opacity: 0.5;
            }}
        """
        self._prev_btn = QPushButton("<")
        self._prev_btn.setFixedSize(28, 28)
        self._prev_btn.setStyleSheet(btn_style)
        self._prev_btn.clicked.connect(self._go_prev)
        cl.addWidget(self._prev_btn)

        self._history_label = QLabel("0 / 0")
        self._history_label.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:11px; min-width:50px;")
        self._history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self._history_label)

        self._next_btn = QPushButton(">")
        self._next_btn.setFixedSize(28, 28)
        self._next_btn.setStyleSheet(btn_style)
        self._next_btn.clicked.connect(self._go_next)
        cl.addWidget(self._next_btn)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet(f"color:{HESPIA_BORDER};")
        cl.addWidget(sep2)

        cl.addStretch()

        # Status label
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:11px;")
        cl.addWidget(self._status_label)

        # Response time
        self._time_label = QLabel("")
        self._time_label.setStyleSheet(f"color:{HESPIA_ORANGE}; font-size:11px; font-weight:bold;")
        cl.addWidget(self._time_label)

        layout.addWidget(ctrl)

        # ── Request / Response split
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._req_editor = RequestEditor("Request", mode="request", read_only=False)
        default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        self._req_editor.set_content(
            f"GET / HTTP/1.1\r\n"
            f"Host: example.com\r\n"
            f"User-Agent: {default_ua}\r\n"
            f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8\r\n"
            f"Accept-Language: en-US,en;q=0.9\r\n"
            f"Connection: close\r\n\r\n"
        )
        splitter.addWidget(self._req_editor)

        self._resp_editor = RequestEditor("Response", mode="response", read_only=True)
        splitter.addWidget(self._resp_editor)
        splitter.setSizes([500, 500])

        self._req_editor.send_to_decoder.connect(self.send_to_decoder.emit)
        self._req_editor.content_changed.connect(self._on_req_content_changed)
        self._resp_editor.send_to_decoder.connect(self.send_to_decoder.emit)

        layout.addWidget(splitter, 1)

    def _sync_host_header(self, host):
        """Trigger debounced update for Host: header."""
        self._debounce_timer.start()

    def _on_req_content_changed(self, content):
        """Trigger debounced update for Content-Length: header."""
        self._debounce_timer.start()

    def _apply_auto_updates(self):
        """Perform the actual synchronization of Host: and Content-Length: headers."""
        host = self._host_edit.text().strip()
        content = self._req_editor.get_content()
        if not content.strip():
            return

        new_content = content

        # 1. Host sync
        if host:
            new_content = re.sub(r"Host: [^\r\n]*", f"Host: {host}", new_content, flags=re.IGNORECASE)
            if new_content == content and "Host:" not in content.lower() and "HTTP/" in content:
                # If Host: is missing, inject it after request line
                lines = new_content.split("\n")
                if lines:
                    lines.insert(1, f"Host: {host}\r")
                    new_content = "\n".join(lines)

        # 2. Content-Length sync
        parts = new_content.replace("\r\n", "\n").split("\n\n", 1)
        if len(parts) >= 2:
            body = parts[1]
            length = len(body.encode("utf-8"))
            
            # Check if length changed
            match = re.search(r"Content-Length:\s*(\d+)", new_content, re.I)
            body_len_changed = True
            if match:
                current_len = int(match.group(1))
                if current_len == length:
                    body_len_changed = False
            
            if body_len_changed:
                updated_c_len = re.sub(r"Content-Length:\s*\d+", f"Content-Length: {length}", new_content, flags=re.I)
                if updated_c_len == new_content and "Content-Length:" not in new_content.lower():
                    # Inject after Host or request line
                    lines = new_content.split("\n")
                    if len(lines) > 1:
                        lines.insert(2, f"Content-Length: {length}\r")
                        updated_c_len = "\n".join(lines)
                new_content = updated_c_len

        # 3. Apply if changed
        if new_content != content:
            # Block signals to avoid recursion during refresh
            self._req_editor.blockSignals(True)
            # Use internal editor for cursor persistence
            raw_edit = self._req_editor._raw_editor
            cursor = raw_edit.textCursor()
            pos = cursor.position()
            anchor = cursor.anchor()
            
            self._req_editor.set_content(new_content)
            
            # Restore selection/position
            new_cursor = raw_edit.textCursor()
            new_cursor.setPosition(min(anchor, len(new_content)))
            new_cursor.setPosition(min(pos, len(new_content)), QTextCursor.MoveMode.KeepAnchor)
            raw_edit.setTextCursor(new_cursor)
            self._req_editor.blockSignals(False)

    def _on_https_changed(self, state):
        port = 443 if state == Qt.CheckState.Checked.value else 80
        self._port_spin.setValue(port)

    def _do_send(self):
        host = self._host_edit.text().strip()
        port = self._port_spin.value()
        is_https = self._https_check.isChecked()
        raw = self._req_editor.get_content()

        if not host:
            QMessageBox.warning(self, "Missing Host", "Please specify a target host.")
            return
        if not raw.strip():
            return

        self._send_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._status_label.setText("Sending...")
        self._status_label.setStyleSheet(f"color:{HESPIA_ORANGE}; font-size:11px;")
        self._resp_editor.clear()
        self._resp_editor.set_content("Waiting for response...", "Sending")

        import time
        self._send_start = time.time()

        # Run in thread
        self._thread = QThread()
        self._worker = SendWorker(self.engine, host, port, is_https, raw)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_response)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _do_cancel(self):
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait()
        self._send_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._status_label.setText("Cancelled")
        self._status_label.setStyleSheet(f"color:{HESPIA_ERROR}; font-size:11px;")

    def _on_response(self, resp_text: str):
        import time
        elapsed = (time.time() - self._send_start) * 1000
        self._resp_editor.set_content(resp_text, f"{elapsed:.0f}ms")
        self._time_label.setText(f"{elapsed:.0f} ms")
        self._send_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)

        # Parse status for color
        first_line = resp_text.split("\n")[0] if resp_text else ""
        parts = first_line.split(" ", 2)
        status_color = HESPIA_SUCCESS
        if len(parts) >= 2:
            try:
                code = int(parts[1])
                if code >= 400:
                    status_color = HESPIA_ERROR
                elif code >= 300:
                    status_color = "#FF9800"
            except ValueError:
                pass
        self._status_label.setText(f"Done: {first_line.strip()}")
        self._status_label.setStyleSheet(f"color:{status_color}; font-size:11px; font-weight:bold;")

        # Save to history
        req_raw = self._req_editor.get_content()
        self._history.append((req_raw, resp_text))
        self._history_index = len(self._history) - 1
        self._update_history_label()

    def _on_error(self, err: str):
        self._resp_editor.set_content(f"Error: {err}", "ERROR")
        self._send_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._status_label.setText(f"Error: {err}")
        self._status_label.setStyleSheet(f"color:{HESPIA_ERROR}; font-size:11px;")

    def _go_prev(self):
        if self._history_index > 0:
            self._history_index -= 1
            req, resp = self._history[self._history_index]
            self._req_editor.set_content(req)
            self._resp_editor.set_content(resp)
            self._update_history_label()

    def _go_next(self):
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            req, resp = self._history[self._history_index]
            self._req_editor.set_content(req)
            self._resp_editor.set_content(resp)
            self._update_history_label()

    def _update_history_label(self):
        total = len(self._history)
        idx = self._history_index + 1 if self._history else 0
        self._history_label.setText(f"{idx} / {total}")

    def load_from_flow(self, entry):
        """Load a flow entry into the repeater."""
        req_lines = [f"{entry.method} {entry.path} HTTP/1.1"]
        for k, v in entry.request_headers_raw.items():
            req_lines.append(f"{k}: {v}")
        req_lines.append("")
        try:
            req_lines.append(entry.request_body.decode("utf-8", errors="replace"))
        except Exception:
            pass
        self._req_editor.set_content("\r\n".join(req_lines))

        self._host_edit.setText(entry.host)
        self._port_spin.setValue(entry.port)
        self._https_check.setChecked(entry.is_https)

        resp_text = ""
        if entry.status_code:
            resp_lines = [f"HTTP/1.1 {entry.status_code} {entry.status_reason}"]
            for k, v in entry.response_headers_raw.items():
                resp_lines.append(f"{k}: {v}")
            resp_lines.append("")
            try:
                resp_lines.append(entry.response_body.decode("utf-8", errors="replace"))
            except Exception:
                pass
            resp_text = "\r\n".join(resp_lines)
        self._resp_editor.set_content(resp_text)


# ─── Repeater Tab ─────────────────────────────────────────────────────────────

class RepeaterTab(QWidget):
    """
    Repeater tab - manages multiple repeater instances via sub-tabs.
    """
    send_to_decoder = Signal(str)

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._instance_count = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header
        header = QFrame()
        header.setFixedHeight(30)
        header.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 2, 8, 2)

        title = QLabel("HTTP Repeater")
        title.setStyleSheet(f"color:{HESPIA_ORANGE}; font-weight:bold; font-size:13px;")
        hl.addWidget(title)
        hl.addStretch()

        new_tab_btn = QPushButton("+ New Tab")
        new_tab_btn.setFixedHeight(22)
        new_tab_btn.clicked.connect(self._new_instance)
        hl.addWidget(new_tab_btn)

        layout.addWidget(header)

        # ── Instance tabs
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._close_tab)
        layout.addWidget(self._tabs, 1)

        # Start with one instance
        self._new_instance()

    def _new_instance(self, name: str = None) -> RepeaterInstance:
        self._instance_count += 1
        if not name:
            name = f"#{self._instance_count}"
        inst = RepeaterInstance(self.engine, name)
        inst.send_to_decoder.connect(self.send_to_decoder.emit)
        idx = self._tabs.addTab(inst, name)
        self._tabs.setCurrentIndex(idx)
        return inst

    def _close_tab(self, idx: int):
        if self._tabs.count() > 1:
            self._tabs.removeTab(idx)

    def load_from_flow(self, entry):
        """Accept a flow from the Proxy history."""
        # Reuse current tab if empty, else new tab
        current = self._tabs.currentWidget()
        if isinstance(current, RepeaterInstance):
            if not current._req_editor.get_content().strip():
                current.load_from_flow(entry)
                name = f"{entry.method} {entry.host}"
                self._tabs.setTabText(self._tabs.currentIndex(), name[:25])
                return
        inst = self._new_instance(f"{entry.method} {entry.host}"[:25])
        inst.load_from_flow(entry)
