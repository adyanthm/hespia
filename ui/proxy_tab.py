"""
Proxy Tab - Intercept, HTTP History, and Options subtabs.
The heart of the proxy tool.
"""
import time
from typing import Optional, Dict, List
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QLineEdit, QComboBox, QCheckBox,
    QMenu, QAbstractItemView, QGroupBox, QScrollArea,
    QSpinBox, QGridLayout, QMessageBox, QApplication,
    QToolBar, QSizePolicy, QTextEdit, QTabBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QSortFilterProxyModel, QRegularExpression
from PySide6.QtGui import QColor, QFont, QAction, QIcon, QKeySequence
from ui.request_editor import RequestEditor, RequestResponseSplitter
from ui.styles import (
    HESPIA_ORANGE, HESPIA_BG, HESPIA_BG_DARK, HESPIA_BG_LIGHT, HESPIA_TEXT, HESPIA_BORDER,
    HESPIA_INTERCEPT_ON, HESPIA_INTERCEPT_OFF, HESPIA_TEXT_DIM, HESPIA_WARNING_BG,
    HTTP_STATUS_COLORS, METHOD_COLORS, INTERCEPT_ON_STYLE, INTERCEPT_OFF_STYLE,
    MODERN_FORWARD_STYLE, MODERN_DROP_STYLE, MODERN_ACTION_STYLE
)


# ─── HTTP History Table ───────────────────────────────────────────────────────

HISTORY_COLS = ["#", "Host", "Method", "URL", "Params", "Edit", "Status",
                "Size", "Req Size", "MIME", "Ext", "TLS", "Time(ms)", "Comment"]
COL_NUM = 0
COL_HOST = 1
COL_METHOD = 2
COL_URL = 3
COL_PARAMS = 4
COL_EDIT = 5
COL_STATUS = 6
COL_LEN = 7
COL_REQ_LEN = 8
COL_MIME = 9
COL_EXT = 10
COL_TLS = 11
COL_TIME = 12
COL_COMMENT = 13


class HttpHistoryTable(QWidget):
    """HTTP traffic history table with flow detail viewer."""

    flow_selected = Signal(object)   # FlowEntry
    send_to_repeater = Signal(object)
    send_to_intruder = Signal(object)
    send_to_decoder = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._flows: Dict[str, object] = {}   # flow_id -> FlowEntry
        self._row_map: Dict[str, int] = {}     # flow_id -> row index
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(6, 4, 6, 4)
        tl.setSpacing(6)

        tl.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Host, URL, method... (regex supported)")
        self._filter_edit.setFixedHeight(24)
        self._filter_edit.textChanged.connect(self._apply_filter)
        tl.addWidget(self._filter_edit, 1)

        method_label = QLabel("Method:")
        tl.addWidget(method_label)
        self._method_filter = QComboBox()
        self._method_filter.addItems(["All", "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
        self._method_filter.setFixedWidth(90)
        self._method_filter.currentTextChanged.connect(self._apply_filter)
        tl.addWidget(self._method_filter)

        status_label = QLabel("Status:")
        tl.addWidget(status_label)
        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "2xx", "3xx", "4xx", "5xx"])
        self._status_filter.setFixedWidth(75)
        self._status_filter.currentTextChanged.connect(self._apply_filter)
        tl.addWidget(self._status_filter)

        self._https_only = QCheckBox("HTTPS only")
        self._https_only.stateChanged.connect(self._apply_filter)
        tl.addWidget(self._https_only)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(24)
        clear_btn.clicked.connect(self._clear_all)
        tl.addWidget(clear_btn)

        layout.addWidget(toolbar)

        # ── Main splitter (table top, detail bottom)
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(len(HISTORY_COLS))
        self._table.setHorizontalHeaderLabels(HISTORY_COLS)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().setDefaultSectionSize(22)
        self._table.verticalHeader().hide()
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.currentItemChanged.connect(self._on_row_selected)

        # Column widths
        hdr = self._table.horizontalHeader()
        hdr.setDefaultSectionSize(80)
        hdr.resizeSection(COL_NUM, 45)
        hdr.resizeSection(COL_HOST, 200)
        hdr.resizeSection(COL_METHOD, 65)
        hdr.resizeSection(COL_URL, 380)
        hdr.resizeSection(COL_PARAMS, 60)
        hdr.resizeSection(COL_EDIT, 40)
        hdr.resizeSection(COL_STATUS, 60)
        hdr.resizeSection(COL_LEN, 75)
        hdr.resizeSection(COL_REQ_LEN, 75)
        hdr.resizeSection(COL_MIME, 120)
        hdr.resizeSection(COL_EXT, 40)
        hdr.resizeSection(COL_TLS, 40)
        hdr.resizeSection(COL_TIME, 75)
        hdr.resizeSection(COL_COMMENT, 120)

        splitter.addWidget(self._table)

        # Detail (request/response)
        self._detail = RequestResponseSplitter()
        self._detail.send_to_decoder.connect(self.send_to_decoder.emit)
        splitter.addWidget(self._detail)
        splitter.setSizes([400, 300])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter, 1)

        # ── Bottom status
        status = QFrame()
        status.setFixedHeight(22)
        status.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-top:1px solid {HESPIA_BORDER};")
        sl = QHBoxLayout(status)
        sl.setContentsMargins(8, 0, 8, 0)
        self._count_label = QLabel("0 requests")
        self._count_label.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:11px;")
        sl.addWidget(self._count_label)
        sl.addStretch()
        layout.addWidget(status)

    def add_flow(self, entry):
        """Add a new flow entry to the table."""
        if entry.id in self._row_map:
            return  # already exists
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._flows[entry.id] = entry
        self._row_map[entry.id] = row
        self._populate_row(row, entry)
        self._count_label.setText(f"{row + 1} requests")
        
        # Auto-scroll to bottom
        self._table.scrollToBottom()

    def update_flow(self, entry):
        """Update an existing row with response data."""
        self._flows[entry.id] = entry
        row = self._row_map.get(entry.id)
        if row is None:
            return
        self._populate_row(row, entry)

    def _populate_row(self, row: int, entry):
        """Fill a table row from a FlowEntry."""
        status_str = str(entry.status_code) if entry.status_code else "..."
        ext = entry.path.rsplit(".", 1)[-1][:6] if "." in entry.path else ""

        cells = [
            str(entry.number),
            entry.host,
            entry.method,
            entry.url,
            "✓" if entry.params else "",
            "✎" if entry.edited else "",
            status_str,
            self._fmt_size(entry.response_length),
            self._fmt_size(entry.request_length),
            entry.content_type,
            ext,
            "🔒" if entry.is_https else "",
            f"{entry.duration_ms:.0f}" if entry.duration_ms else "",
            entry.comment,
        ]
        for col, val in enumerate(cells):
            item = QTableWidgetItem(val)
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            # Color by status
            if col == COL_STATUS and entry.status_code:
                code_str = str(entry.status_code)
                color = HTTP_STATUS_COLORS.get(code_str[0], HESPIA_TEXT)
                item.setForeground(QColor(color))

            # Color method
            elif col == COL_METHOD:
                color = METHOD_COLORS.get(entry.method, HESPIA_TEXT)
                item.setForeground(QColor(color))

            # Highlight edited
            elif col == COL_EDIT and entry.edited:
                item.setForeground(QColor(HESPIA_ORANGE))

            self._table.setItem(row, col, item)

    def _fmt_size(self, n: int) -> str:
        if n < 1024:
            return f"{n} B"
        elif n < 1024 * 1024:
            return f"{n//1024} KB"
        return f"{n//(1024*1024)} MB"

    def _on_row_selected(self, current, _):
        if not current:
            return
        flow_id = current.data(Qt.ItemDataRole.UserRole)
        if not flow_id:
            return
        entry = self._flows.get(flow_id)
        if not entry:
            return
        self.flow_selected.emit(entry)

        # Build raw text for display
        def serialize_flow(headers, body, method_path=None, status_line=None):
            lines = []
            if method_path: lines.append(method_path)
            if status_line: lines.append(status_line)
            for k, v in headers.items():
                lines.append(f"{k}: {v}")
            lines.append("")
            try:
                body_text = body.decode("utf-8", errors="replace")
                if len(body_text) > 100000:
                    body_text = body_text[:100000] + "\n\n... CONTENT TRUNCATED FOR PERFORMANCE ..."
                lines.append(body_text)
            except Exception: lines.append("<binary content>")
            return "\r\n".join(lines)

        req_text = serialize_flow(entry.request_headers_raw, entry.request_body, method_path=f"{entry.method} {entry.path} HTTP/1.1")
        resp_text = ""
        if entry.status_code:
            resp_text = serialize_flow(entry.response_headers_raw, entry.response_body, status_line=f"HTTP/1.1 {entry.status_code} {entry.status_reason}")

        self._detail.set_flow(req_text, resp_text)

    def _show_context_menu(self, pos):
        item = self._table.itemAt(pos)
        if not item:
            return
        flow_id = item.data(Qt.ItemDataRole.UserRole)
        entry = self._flows.get(flow_id)
        if not entry:
            return

        menu = QMenu(self)
        send_rep = menu.addAction("📤 Send to Repeater")
        send_int = menu.addAction("🎯 Send to Intruder")
        menu.addSeparator()
        copy_url = menu.addAction("📋 Copy URL")
        copy_req = menu.addAction("📋 Copy Request")
        menu.addSeparator()
        highlight_m = menu.addMenu("🎨 Highlight")
        for color, name in [("#FF6633", "Orange"), ("#FF5555", "Red"), ("#55BB55", "Green"),
                            ("#5599FF", "Blue"), ("#FFCC55", "Yellow")]:
            act = highlight_m.addAction(name)
            act.setData(color)
        menu.addSeparator()
        comment_act = menu.addAction("💬 Add Comment")
        menu.addSeparator()
        delete_act = menu.addAction("🗑 Delete")

        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if not action:
            return
        if action == send_rep:
            self.send_to_repeater.emit(entry)
        elif action == send_int:
            self.send_to_intruder.emit(entry)
        elif action == copy_url:
            QApplication.clipboard().setText(entry.url)
        elif action == copy_req:
            req_lines = [f"{entry.method} {entry.path} HTTP/1.1"]
            for k, v in entry.request_headers_raw.items():
                req_lines.append(f"{k}: {v}")
            req_lines.append("")
            try:
                req_lines.append(entry.request_body.decode("utf-8", errors="replace"))
            except Exception:
                pass
            QApplication.clipboard().setText("\n".join(req_lines))
        elif action and action.parent() == highlight_m:
            row = self._row_map.get(flow_id)
            if row is not None:
                col_color = action.data()
                for c in range(self._table.columnCount()):
                    it = self._table.item(row, c)
                    if it:
                        it.setBackground(QColor(col_color + "33"))
        elif action == delete_act:
            row = self._row_map.get(flow_id)
            if row is not None:
                self._table.removeRow(row)
                del self._flows[flow_id]
                del self._row_map[flow_id]
                # Rebuild row map
                self._row_map = {}
                for r in range(self._table.rowCount()):
                    it = self._table.item(r, 0)
                    if it:
                        fid = it.data(Qt.ItemDataRole.UserRole)
                        if fid:
                            self._row_map[fid] = r

    def _apply_filter(self):
        text = self._filter_edit.text().lower()
        method = self._method_filter.currentText()
        status = self._status_filter.currentText()
        https_only = self._https_only.isChecked()

        for row in range(self._table.rowCount()):
            url_item = self._table.item(row, COL_URL)
            host_item = self._table.item(row, COL_HOST)
            method_item = self._table.item(row, COL_METHOD)
            status_item = self._table.item(row, COL_STATUS)
            tls_item = self._table.item(row, COL_TLS)

            visible = True
            if text:
                url_match = url_item and text in url_item.text().lower()
                host_match = host_item and text in host_item.text().lower()
                visible = visible and (url_match or host_match)
            if method != "All":
                visible = visible and (method_item and method_item.text() == method)
            if status != "All":
                code = status_item.text() if status_item else ""
                if code and code != "...":
                    visible = visible and code.startswith(status[0])
                else:
                    visible = False
            if https_only:
                visible = visible and (tls_item and tls_item.text() == "🔒")

            self._table.setRowHidden(row, not visible)

    def _clear_all(self):
        self._table.setRowCount(0)
        self._flows.clear()
        self._row_map.clear()
        self._detail.request_editor.clear()
        self._detail.response_editor.clear()
        self._count_label.setText("0 requests")

    def clear(self):
        self._clear_all()


# ─── Intercept Panel ──────────────────────────────────────────────────────────

class InterceptPanel(QWidget):
    """
    Control panel for manual request/response interception.
    """
    forward_clicked = Signal(str, str, bool)  # flow_id, raw, is_response
    drop_clicked = Signal(str)               # flow_id
    intercept_toggled = Signal(bool)          # enabled
    send_to_decoder = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._intercept_queue: List[dict] = []  # List of {id, raw, type, host, url}
        self._current_index = -1
        self._intercept_on = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Top control bar
        ctrl = QFrame()
        ctrl.setFixedHeight(48)
        ctrl.setStyleSheet(f"background:{HESPIA_BG_DARK}; border:1px solid {HESPIA_BORDER}; border-radius:4px;")
        cl = QHBoxLayout(ctrl)
        cl.setContentsMargins(10, 6, 10, 6)
        cl.setSpacing(8)

        self._intercept_btn = QPushButton("Intercept is OFF")
        self._intercept_btn.setFixedHeight(34)
        self._intercept_btn.setFixedWidth(160)
        self._intercept_btn.setCheckable(True)
        self._intercept_btn.setStyleSheet(INTERCEPT_OFF_STYLE)
        self._intercept_btn.toggled.connect(self._toggle_intercept)
        cl.addWidget(self._intercept_btn)

        self._forward_btn = QPushButton("▶ Forward")
        self._forward_btn.setFixedHeight(30)
        self._forward_btn.setEnabled(False)
        self._forward_btn.setStyleSheet(MODERN_FORWARD_STYLE)
        self._forward_btn.clicked.connect(self._do_forward)
        cl.addWidget(self._forward_btn)

        self._forward_all_btn = QPushButton("⏭ Forward All")
        self._forward_all_btn.setFixedHeight(30)
        self._forward_all_btn.setEnabled(False)
        self._forward_all_btn.setStyleSheet(MODERN_ACTION_STYLE)
        self._forward_all_btn.clicked.connect(self._do_forward_all)
        cl.addWidget(self._forward_all_btn)

        self._drop_btn = QPushButton("✕ Drop")
        self._drop_btn.setFixedHeight(30)
        self._drop_btn.setEnabled(False)
        self._drop_btn.setStyleSheet(MODERN_DROP_STYLE)
        self._drop_btn.clicked.connect(self._do_drop)
        cl.addWidget(self._drop_btn)

        self._drop_all_btn = QPushButton("🗑 Drop All")
        self._drop_all_btn.setFixedHeight(30)
        self._drop_all_btn.setEnabled(False)
        self._drop_all_btn.setStyleSheet(MODERN_DROP_STYLE)
        self._drop_all_btn.clicked.connect(self._do_drop_all)
        cl.addWidget(self._drop_all_btn)

        self._action_btn = QPushButton("⚡ Action")
        self._action_btn.setFixedHeight(30)
        self._action_btn.setEnabled(False)
        self._action_btn.setStyleSheet(MODERN_ACTION_STYLE)
        self._action_btn.clicked.connect(self._show_action_menu)
        cl.addStretch()

        # Intercept mode selector
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Intercept requests", "Intercept responses", "Both"])
        self._mode_combo.setFixedWidth(180)
        self._mode_combo.setCurrentIndex(2) # Default to Both
        cl.addWidget(self._mode_combo)

        layout.addWidget(ctrl)

        # ── Splitter for Table and Editor
        self._splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Queue Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(["Time", "Type", "Direction", "Method", "URL", "Status code", "Length"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().hide()
        self._table.itemSelectionChanged.connect(self._on_table_selection_changed)
        
        header = self._table.horizontalHeader()
        header.resizeSection(0, 80)
        header.resizeSection(1, 60)
        header.resizeSection(2, 70)
        header.resizeSection(3, 70)
        header.resizeSection(4, 400)
        header.resizeSection(5, 80)
        header.setStretchLastSection(True)
        
        self._splitter.addWidget(self._table)

        # Request editor
        self._editor = RequestEditor("Intercepted Flow", mode="request", read_only=False)
        self._splitter.addWidget(self._editor)
        
        self._splitter.setSizes([300, 500])
        layout.addWidget(self._splitter, 1)

        self._editor.send_to_decoder.connect(self.send_to_decoder.emit)

        # ── Info bar
        info = QFrame()
        info.setFixedHeight(26)
        info.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-top:1px solid {HESPIA_BORDER};")
        il = QHBoxLayout(info)
        il.setContentsMargins(8, 0, 8, 0)
        self._info_label = QLabel("Intercept is off. Enable it to capture requests.")
        self._info_label.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:11px;")
        il.addWidget(self._info_label)
        il.addStretch()
        layout.addWidget(info)

    def _toggle_intercept(self, checked: bool):
        self._intercept_on = checked
        if checked:
            self._intercept_btn.setText("Intercept is ON")
            self._intercept_btn.setStyleSheet(INTERCEPT_ON_STYLE)
            self._info_label.setText("Intercept ON — Waiting for requests...")
        else:
            self._intercept_btn.setText("Intercept is OFF")
            self._intercept_btn.setStyleSheet(INTERCEPT_OFF_STYLE)
            self._info_label.setText("Intercept is off.")
            # Forward everything in table - Batch operation
            self._table.setSortingEnabled(False)
            while self._table.rowCount() > 0:
                item = self._table.item(0, 0)
                data = item.data(Qt.ItemDataRole.UserRole)
                self.forward_clicked.emit(data["id"], data["raw"], data["is_response"])
                self._table.removeRow(0)
            self._table.setSortingEnabled(True)
            
            self._update_display()

        self.intercept_toggled.emit(checked)

    def show_intercepted_request(self, flow_id: str, raw: str):
        """Add a new request to the intercept queue table."""
        try:
            # Rugged parsing for table
            lines = raw.splitlines()
            method = "REQUEST"
            url = flow_id[:12]
            if lines and " " in lines[0]:
                parts = lines[0].split(" ")
                if len(parts) >= 2:
                    method = parts[0]
                    url = parts[1]
            
            ts = time.strftime("%H:%M:%S")
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            item = QTableWidgetItem(ts)
            item.setData(Qt.ItemDataRole.UserRole, {
                "id": flow_id, "raw": raw, "type": "REQUEST", "is_response": False
            })
            
            self._table.setItem(row, 0, item)
            self._table.setItem(row, 1, QTableWidgetItem("HTTP"))
            self._table.setItem(row, 2, QTableWidgetItem("➔ Request"))
            self._table.setItem(row, 3, QTableWidgetItem(method))
            self._table.setItem(row, 4, QTableWidgetItem(url))
            self._table.setItem(row, 5, QTableWidgetItem(""))
            self._table.setItem(row, 6, QTableWidgetItem(str(len(raw))))
            
            if self._table.selectedItems() == []:
                self._table.selectRow(row)
            self._update_display()
        except Exception as e:
            print(f"Error showing intercepted request: {e}")

    def show_intercepted_response(self, flow_id: str, raw: str):
        """Add a new response to the intercept queue table."""
        try:
            lines = raw.splitlines()
            status = ""
            if lines and " " in lines[0]:
                parts = lines[0].split(" ")
                if len(parts) >= 2:
                    status = parts[1]
            
            ts = time.strftime("%H:%M:%S")
            row = self._table.rowCount()
            self._table.insertRow(row)
            
            item = QTableWidgetItem(ts)
            item.setData(Qt.ItemDataRole.UserRole, {
                "id": flow_id, "raw": raw, "type": "RESPONSE", "is_response": True
            })
            
            self._table.setItem(row, 0, item)
            self._table.setItem(row, 1, QTableWidgetItem("HTTP"))
            self._table.setItem(row, 2, QTableWidgetItem("⇠ Response"))
            self._table.setItem(row, 3, QTableWidgetItem(""))
            self._table.setItem(row, 4, QTableWidgetItem(f"From {flow_id[:8]}..."))
            self._table.setItem(row, 5, QTableWidgetItem(status))
            self._table.setItem(row, 6, QTableWidgetItem(str(len(raw))))
            
            if self._table.selectedItems() == []:
                self._table.selectRow(row)
            self._update_display()
        except Exception as e:
            print(f"Error showing intercepted response: {e}")

    def _on_table_selection_changed(self):
        # Save previous raw if needed? Normally we just grab from editor on forward
        self._update_display()
    def _do_forward_all(self):
        """Forward every intercepted item currently in the queue."""
        self._table.setSortingEnabled(False)
        while self._table.rowCount() > 0:
            item = self._table.item(0, 0)
            data = item.data(Qt.ItemDataRole.UserRole)
            self.forward_clicked.emit(data["id"], data["raw"], data["is_response"])
            self._table.removeRow(0)
        self._table.setSortingEnabled(True)
        self._update_display()

    def _do_drop_all(self):
        """Drop everything in the queue."""
        while self._table.rowCount() > 0:
            item = self._table.item(0, 0)
            data = item.data(Qt.ItemDataRole.UserRole)
            self.drop_clicked.emit(data["id"])
            self._table.removeRow(0)
        self._update_display()

    def _update_display(self):
        """Update editor and buttons based on table selection."""
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            self._editor.clear()
            self._forward_btn.setEnabled(False)
            self._forward_all_btn.setEnabled(self._table.rowCount() > 0)
            self._drop_btn.setEnabled(False)
            self._drop_all_btn.setEnabled(self._table.rowCount() > 0)
            self._action_btn.setEnabled(False)
            self._info_label.setText("No intercepted flow selected.")
            return

        row_idx = rows[0].row()
        item = self._table.item(row_idx, 0)
        if not item: return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data: return
        
        self._editor.set_content(data["raw"], f"{data['type']} INTERCEPTED")
        self._forward_btn.setEnabled(True)
        self._forward_all_btn.setEnabled(True)
        self._drop_btn.setEnabled(True)
        self._drop_all_btn.setEnabled(True)
        self._action_btn.setEnabled(True)
        self._info_label.setText(f"{data['type']} intercepted ({data['id'][:12]}...)")

    def _do_forward(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows: return
        
        row_idx = rows[0].row()
        item = self._table.item(row_idx, 0)
        data = item.data(Qt.ItemDataRole.UserRole)
        
        modified = self._editor.get_content()
        self.forward_clicked.emit(data["id"], modified, data["is_response"])
        
        self._table.removeRow(row_idx)
        # Select next row if any
        if self._table.rowCount() > 0:
            next_row = min(row_idx, self._table.rowCount() - 1)
            self._table.selectRow(next_row)
        
        self._update_display()

    def _do_drop(self):
        rows = self._table.selectionModel().selectedRows()
        if not rows: return
        
        row_idx = rows[0].row()
        item = self._table.item(row_idx, 0)
        data = item.data(Qt.ItemDataRole.UserRole)
        
        self.drop_clicked.emit(data["id"])
        self._table.removeRow(row_idx)
        
        if self._table.rowCount() > 0:
            next_row = min(row_idx, self._table.rowCount() - 1)
            self._table.selectRow(next_row)
            
        self._update_display()

    def _show_action_menu(self):
        menu = QMenu(self)
        send_rep = menu.addAction("📤 Send to Repeater")
        send_int = menu.addAction("🎯 Send to Intruder")
        menu.addSeparator()
        drop_all = menu.addAction("🗑 Drop All")
        menu.addSeparator()
        menu.addAction("📋 Copy as cURL")
        menu.addAction("📋 Copy URL")
        menu.addSeparator()
        menu.addAction("🔄 Convert to GET")
        menu.addAction("🔄 Convert to POST")
        
        action = menu.exec(self._action_btn.mapToGlobal(self._action_btn.rect().bottomLeft()))
        if not action: return
        
        if action == drop_all:
            self._do_drop_all()
        # ... other actions ...
            self._update_display()
        # Other actions can be wired here later

    def is_intercept_on(self) -> bool:
        return self._intercept_on

    def get_intercept_mode(self) -> str:
        return self._mode_combo.currentText()


# ─── Proxy Options Panel ──────────────────────────────────────────────────────

class ProxyOptionsPanel(QWidget):
    """Options for proxy listeners, intercept rules, match & replace."""

    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._building_ui = True
        self._setup_ui()
        self._building_ui = False

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ── Proxy Listeners
        listener_grp = QGroupBox("Proxy Listeners")
        lg = QVBoxLayout(listener_grp)

        lh = QHBoxLayout()
        lh.addWidget(QLabel("Interface:"))
        self._host_edit = QLineEdit("127.0.0.1")
        self._host_edit.setFixedWidth(140)
        lh.addWidget(self._host_edit)
        lh.addWidget(QLabel("Port:"))
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(8080)
        self._port_spin.setFixedWidth(80)
        lh.addWidget(self._port_spin)
        lh.addStretch()
        lg.addLayout(lh)

        cert_info = QLabel(
            "⚠ To intercept HTTPS, configure your browser to use this proxy and install\n"
            "the mitmproxy CA certificate. Find it at: ~/.mitmproxy/mitmproxy-ca-cert.pem\n"
            "Or navigate to http://mitm.it in your browser while using this proxy."
        )
        cert_info.setStyleSheet(f"color:{HESPIA_TEXT}; background:{HESPIA_WARNING_BG}; padding:10px; border-radius:4px; border:1px solid {HESPIA_BORDER};")
        cert_info.setWordWrap(True)
        lg.addWidget(cert_info)

        layout.addWidget(listener_grp)

        # ── Upstream Proxy
        upstream_grp = QGroupBox("Upstream Proxy")
        ug = QVBoxLayout(upstream_grp)
        uh = QHBoxLayout()
        self._upstream_check = QCheckBox("Use upstream proxy")
        uh.addWidget(self._upstream_check)
        uh.addStretch()
        ug.addLayout(uh)
        uh2 = QHBoxLayout()
        uh2.addWidget(QLabel("Host:"))
        self._upstream_host = QLineEdit()
        self._upstream_host.setPlaceholderText("proxy.example.com")
        self._upstream_host.setFixedWidth(200)
        uh2.addWidget(self._upstream_host)
        uh2.addWidget(QLabel("Port:"))
        self._upstream_port = QSpinBox()
        self._upstream_port.setRange(1, 65535)
        self._upstream_port.setValue(8888)
        self._upstream_port.setFixedWidth(80)
        uh2.addWidget(self._upstream_port)
        uh2.addStretch()
        ug.addLayout(uh2)
        layout.addWidget(upstream_grp)

        # ── Intercept Rules
        rules_grp = QGroupBox("Intercept Rules (AND logic)")
        rl = QVBoxLayout(rules_grp)

        rules_info = QLabel("Intercept requests matching ALL enabled rules:")
        rules_info.setStyleSheet("color:#888; font-size:11px;")
        rl.addWidget(rules_info)

        rules_list = [
            ("URLs matching:", self._make_rule_row()),
            ("Methods matching:", self._make_rule_row()),
            ("Status codes matching:", self._make_rule_row()),
        ]
        self._rule_rows = []
        for label, (chk, combo, edit) in zip(*zip(*[(r[0], r[1]) for r in rules_list])):
            row_w = QHBoxLayout()
            chk.setText(label)
            row_w.addWidget(chk)
            row_w.addWidget(combo)
            row_w.addWidget(edit, 1)
            rl.addLayout(row_w)
            self._rule_rows.append((chk, combo, edit))

        layout.addWidget(rules_grp)

        # ── Match & Replace
        mr_grp = QGroupBox("Match and Replace")
        mrl = QVBoxLayout(mr_grp)

        mr_info = QLabel("Automatically replace content in requests/responses using regex:")
        mr_info.setStyleSheet("color:#888; font-size:11px;")
        mrl.addWidget(mr_info)

        self._mr_table = QTableWidget()
        self._mr_table.setColumnCount(5)
        self._mr_table.setHorizontalHeaderLabels(["En", "Type", "Match (regex)", "Replace", "Comment"])
        self._mr_table.setFixedHeight(160)
        self._mr_table.horizontalHeader().setStretchLastSection(True)
        self._mr_table.horizontalHeader().resizeSection(0, 30)
        self._mr_table.horizontalHeader().resizeSection(1, 130)
        self._mr_table.horizontalHeader().resizeSection(2, 150)
        self._mr_table.horizontalHeader().resizeSection(3, 150)
        mrl.addWidget(self._mr_table)

        mr_btns = QHBoxLayout()
        add_rule_btn = QPushButton("+ Add Rule")
        add_rule_btn.clicked.connect(self._add_mr_rule)
        remove_rule_btn = QPushButton("− Remove")
        remove_rule_btn.clicked.connect(self._remove_mr_rule)
        mr_btns.addWidget(add_rule_btn)
        mr_btns.addWidget(remove_rule_btn)
        mr_btns.addStretch()
        mrl.addLayout(mr_btns)

        layout.addWidget(mr_grp)

        # ── SSL/TLS
        ssl_grp = QGroupBox("SSL/TLS Options")
        sl = QVBoxLayout(ssl_grp)
        self._ssl_insecure = QCheckBox("Don't verify upstream certificates (INSECURE)")
        self._ssl_insecure.setChecked(True)
        sl.addWidget(self._ssl_insecure)
        self._allow_http2 = QCheckBox("Enable HTTP/2 support")
        sl.addWidget(self._allow_http2)
        layout.addWidget(ssl_grp)

        layout.addStretch()
        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _notify_changes(self):
        if self._building_ui:
            return
        self.settings_changed.emit(self.get_settings())

    def _make_rule_row(self):
        chk = QCheckBox()
        chk.toggled.connect(self._notify_changes)
        combo = QComboBox()
        combo.currentIndexChanged.connect(self._notify_changes)
        combo.addItems(["Contains", "Does not contain", "Matches regex", "Does not match regex"])
        combo.setFixedWidth(170)
        edit = QLineEdit()
        edit.textChanged.connect(self._notify_changes)
        edit.setPlaceholderText("Pattern...")
        return chk, combo, edit

    def _add_mr_rule(self):
        row = self._mr_table.rowCount()
        self._mr_table.insertRow(row)
        chk_item = QTableWidgetItem("✓")
        chk_item.setCheckState(Qt.CheckState.Checked)
        self._mr_table.setItem(row, 0, chk_item)

        type_combo = QComboBox()
        type_combo.addItems(["request_header", "response_header",
                             "request_body", "response_body", "url"])
        self._mr_table.setCellWidget(row, 1, type_combo)

        for col in [2, 3, 4]:
            self._mr_table.setItem(row, col, QTableWidgetItem(""))

    def _remove_mr_rule(self):
        row = self._mr_table.currentRow()
        if row >= 0:
            self._mr_table.removeRow(row)

    def get_intercept_rules(self) -> list:
        rules = []
        # URL
        chk, combo, edit = self._rule_rows[0]
        if chk.isChecked() and edit.text():
            rules.append({"enabled": True, "type": "url", "match": edit.text()})
        
        # Method
        chk, combo, edit = self._rule_rows[1]
        if chk.isChecked() and edit.text():
            rules.append({"enabled": True, "type": "method", "match": edit.text()})
            
        # Status
        chk, combo, edit = self._rule_rows[2]
        if chk.isChecked() and edit.text():
            rules.append({"enabled": True, "type": "status", "match": edit.text()})
            
        return rules

    def get_settings(self) -> dict:
        return {
            "host": self._host_edit.text(),
            "port": self._port_spin.value(),
            "upstream_proxy": f"http://{self._upstream_host.text()}:{self._upstream_port.value()}" if self._upstream_check.isChecked() else None,
            "ssl_insecure": self._ssl_insecure.isChecked(),
            "http2": self._allow_http2.isChecked(),
            "match_replace": self.get_match_replace_rules(),
            "intercept_rules": self.get_intercept_rules(),
        }

    def get_match_replace_rules(self) -> list:
        rules = []
        for row in range(self._mr_table.rowCount()):
            chk = self._mr_table.item(row, 0)
            type_w = self._mr_table.cellWidget(row, 1)
            match_item = self._mr_table.item(row, 2)
            repl_item = self._mr_table.item(row, 3)
            if type_w and match_item:
                rules.append({
                    "enabled": chk and chk.checkState() == Qt.CheckState.Checked,
                    "type": type_w.currentText(),
                    "match": match_item.text(),
                    "replace": repl_item.text() if repl_item else "",
                })
        return rules


# ─── Main Proxy Tab ───────────────────────────────────────────────────────────

class ProxyTab(QWidget):
    """
    Main Proxy tab - contains Intercept, HTTP History, WS History, Options.
    """
    # Signals to engine
    forward_request = Signal(str, str)         # flow_id, raw
    forward_response = Signal(str, str)        # flow_id, raw
    drop_flow = Signal(str)                    # flow_id
    intercept_changed = Signal(bool, bool)     # req_intercept, resp_intercept
    settings_changed = Signal(dict)            # all settings

    # Signals to other tabs
    send_to_repeater = Signal(object)
    send_to_intruder = Signal(object)
    send_to_decoder = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tabs = QTabWidget()

        # ── Intercept tab
        self._intercept_panel = InterceptPanel()
        self._intercept_panel.forward_clicked.connect(self._on_forward)
        self._intercept_panel.drop_clicked.connect(self._on_drop)
        self._intercept_panel.intercept_toggled.connect(self._on_intercept_toggled)
        self._intercept_panel.send_to_decoder.connect(self.send_to_decoder.emit)
        self._intercept_panel._mode_combo.currentIndexChanged.connect(self._sync_mode) # Sync when combo changes
        self._tabs.addTab(self._intercept_panel, "Intercept")

        # ── HTTP History tab
        self._history = HttpHistoryTable()
        self._history.send_to_repeater.connect(self.send_to_repeater)
        self._history.send_to_intruder.connect(self.send_to_intruder)
        self._history.send_to_decoder.connect(self.send_to_decoder.emit)
        self._tabs.addTab(self._history, "HTTP History")

        # ── WebSocket History tab
        self._ws_history = self._make_ws_tab()
        self._tabs.addTab(self._ws_history, "WebSockets history")

        # ── Options tab
        self._options = ProxyOptionsPanel()
        self._options.settings_changed.connect(self._on_options_changed)
        self._tabs.addTab(self._options, "Options")

        layout.addWidget(self._tabs)

    def _make_ws_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        lbl = QLabel("WebSocket traffic will appear here.\nEnable WebSocket interception in Options.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:13px;")
        l.addStretch()
        l.addWidget(lbl)
        l.addStretch()
        return w

    # ── Signal routing ────────────────────────────────────────────────────

    def _on_forward(self, flow_id: str, raw: str, is_response: bool):
        if is_response:
            self.forward_response.emit(flow_id, raw)
        else:
            self.forward_request.emit(flow_id, raw)

    def _on_drop(self, flow_id: str):
        self.drop_flow.emit(flow_id)

    def _on_intercept_toggled(self, enabled: bool):
        self._sync_mode()

    def _sync_mode(self):
        enabled = self._intercept_panel.is_intercept_on()
        mode = self._intercept_panel.get_intercept_mode()
        req = enabled and mode in ("Intercept requests", "Both")
        resp = enabled and mode in ("Intercept responses", "Both")
        self.intercept_changed.emit(req, resp)

    def _on_options_changed(self, settings: dict):
        # Notify engine of all settings changes (match/replace, intercept rules, etc)
        self.settings_changed.emit(settings)

    def get_settings(self) -> dict:
        settings = self._options.get_settings()
        # Add intercept mode from panel
        settings["intercept_requests"] = self._intercept_panel.is_intercept_on() and self._intercept_panel.get_intercept_mode() in ("Intercept requests", "Both")
        settings["intercept_responses"] = self._intercept_panel.is_intercept_on() and self._intercept_panel.get_intercept_mode() in ("Intercept responses", "Both")
        return settings

    def get_intercept_rules(self) -> list:
        return self._options.get_intercept_rules()

    def on_flow_added(self, entry):
        self._history.add_flow(entry)

    def on_flow_updated(self, entry):
        self._history.update_flow(entry)

    def on_request_intercepted(self, flow_id: str, raw: str):
        """Called when engine intercepts a request — switch to Intercept tab."""
        self._intercept_panel.show_intercepted_request(flow_id, raw)
        self._tabs.setCurrentIndex(0)

    def on_response_intercepted(self, flow_id: str, raw_req: str, raw_resp: str):
        self._intercept_panel.show_intercepted_response(flow_id, raw_resp)
        self._tabs.setCurrentIndex(0)

    def get_options(self) -> ProxyOptionsPanel:
        return self._options

    def clear_history(self):
        self._history.clear()
