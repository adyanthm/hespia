"""
Target Tab - Scope configuration and site map.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox,
    QFrame, QTableWidget, QTableWidgetItem, QGroupBox,
    QAbstractItemView, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QGridLayout, QRadioButton, QButtonGroup,
    QHeaderView, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QAction
from ui.styles import (
    HESPIA_ORANGE, HESPIA_BG, HESPIA_BG_DARK, HESPIA_TEXT, HESPIA_BORDER,
    HESPIA_TEXT_DIM, HESPIA_SUCCESS, HESPIA_ERROR, HTTP_STATUS_COLORS
)


# ─── Site Map Tree ────────────────────────────────────────────────────────────

class SiteMapTree(QWidget):
    """Hierarchical view of all discovered hosts and paths."""
    send_to_tool = Signal(str, object)  # tool_name, FlowEntry

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hosts = {}   # host -> {path -> FlowEntry}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        tb = QFrame()
        tb.setFixedHeight(32)
        tb.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        tl = QHBoxLayout(tb)
        tl.setContentsMargins(6, 4, 6, 4)
        tl.setSpacing(6)
        tl.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("Filter by host or path...")
        self._filter_edit.setFixedHeight(22)
        self._filter_edit.textChanged.connect(self._apply_filter)
        tl.addWidget(self._filter_edit, 1)
        self._scope_only_check = QCheckBox("In scope only")
        tl.addWidget(self._scope_only_check)
        layout.addWidget(tb)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["URL", "Status", "Length", "MIME"])
        self._tree.setAlternatingRowColors(True)
        self._tree.header().resizeSection(0, 280)
        self._tree.header().resizeSection(1, 60)
        self._tree.header().resizeSection(2, 70)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context)
        self._tree.currentItemChanged.connect(self._on_select)
        splitter.addWidget(self._tree)

        # Request/Response detail
        from ui.request_editor import RequestResponseSplitter
        self._detail = RequestResponseSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._detail)
        splitter.setSizes([300, 500])

        layout.addWidget(splitter, 1)

        # Status bar
        sb = QFrame()
        sb.setFixedHeight(22)
        sb.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-top:1px solid {HESPIA_BORDER};")
        sl = QHBoxLayout(sb)
        sl.setContentsMargins(8, 0, 8, 0)
        self._count_label = QLabel("0 hosts, 0 requests")
        self._count_label.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:11px;")
        sl.addWidget(self._count_label)
        sl.addStretch()
        layout.addWidget(sb)

    def add_flow(self, entry):
        host = entry.host
        path = entry.path

        if host not in self._hosts:
            self._hosts[host] = {}
            host_item = QTreeWidgetItem(self._tree)
            host_item.setText(0, host)
            host_item.setData(0, Qt.ItemDataRole.UserRole, "host")
            icon_color = "#4CAF50" if entry.is_https else "#FF9800"
            host_item.setForeground(0, QColor(icon_color))
            host_item.setExpanded(True)
        else:
            # Find existing host item
            host_item = None
            for i in range(self._tree.topLevelItemCount()):
                item = self._tree.topLevelItem(i)
                if item.text(0) == host:
                    host_item = item
                    break
            if not host_item:
                return

        self._hosts[host][path] = entry

        # Add/update path item
        for i in range(host_item.childCount()):
            child = host_item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole + 1) == path:
                self._update_path_item(child, entry)
                return

        path_item = QTreeWidgetItem(host_item)
        path_item.setText(0, path or "/")
        path_item.setData(0, Qt.ItemDataRole.UserRole, "path")
        path_item.setData(0, Qt.ItemDataRole.UserRole + 1, path)
        path_item.setData(0, Qt.ItemDataRole.UserRole + 2, entry)
        self._update_path_item(path_item, entry)

        # Update count
        total_paths = sum(len(v) for v in self._hosts.values())
        self._count_label.setText(f"{len(self._hosts)} hosts, {total_paths} requests")

    def _update_path_item(self, item: QTreeWidgetItem, entry):
        item.setData(0, Qt.ItemDataRole.UserRole + 2, entry)
        if entry.status_code:
            code = str(entry.status_code)
            item.setText(1, code)
            color = HTTP_STATUS_COLORS.get(code[0], HESPIA_TEXT)
            item.setForeground(1, QColor(color))
        item.setText(2, f"{entry.response_length} B")
        item.setText(3, entry.content_type[:20] if entry.content_type else "")
        # Method badge color
        from ui.styles import METHOD_COLORS
        method_color = METHOD_COLORS.get(entry.method, HESPIA_TEXT)
        item.setForeground(0, QColor(method_color))

    def _on_select(self, current, _):
        if not current:
            return
        entry = current.data(0, Qt.ItemDataRole.UserRole + 2)
        if not entry:
            return
        req_lines = [f"{entry.method} {entry.path} HTTP/1.1"]
        for k, v in entry.request_headers_raw.items():
            req_lines.append(f"{k}: {v}")
        req_lines.append("")
        try:
            req_lines.append(entry.request_body.decode("utf-8", errors="replace"))
        except Exception:
            pass
        req_text = "\n".join(req_lines)

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
            resp_text = "\n".join(resp_lines)

        self._detail.set_flow(req_text, resp_text)

    def _show_context(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        add_scope_act = menu.addAction("Add to scope")
        rem_scope_act = menu.addAction("Remove from scope")
        menu.addSeparator()
        send_rep_act = menu.addAction("Send to Repeater")
        send_int_act = menu.addAction("Send to Intruder")
        
        action = menu.exec(self._tree.viewport().mapToGlobal(pos))
        if not action:
            return

        entry = item.data(0, Qt.ItemDataRole.UserRole + 2)
        host = item.text(0) if item.data(0, Qt.ItemDataRole.UserRole) == "host" else item.parent().text(0)

        if action == add_scope_act:
            self._add_to_scope(host)
        elif action == rem_scope_act:
            self._remove_from_scope(host)
        elif action == send_rep_act and entry:
            self.send_to_tool.emit("repeater", entry)
        elif action == send_int_act and entry:
            self.send_to_tool.emit("intruder", entry)

    def _add_to_scope(self, host: str):
        # Find the main widget to get scope editor
        parent = self.parent()
        while parent and not hasattr(parent, "_scope_editor"):
            parent = parent.parent()
        if parent:
            parent._scope_editor.add_host_rule(host, include=True)

    def _remove_from_scope(self, host: str):
        parent = self.parent()
        while parent and not hasattr(parent, "_scope_editor"):
            parent = parent.parent()
        if parent:
            parent._scope_editor.remove_host_rule(host)

    def _apply_filter(self, text: str = ""):
        text = self._filter_edit.text().lower()
        scope_only = self._scope_only_check.isChecked()
        
        # Get in-scope hosts
        in_scope_hosts = []
        parent = self.parent()
        while parent and not hasattr(parent, "_scope_editor"):
            parent = parent.parent()
        if parent:
            in_scope_hosts = parent._scope_editor.get_in_scope_hosts()

        for i in range(self._tree.topLevelItemCount()):
            host_item = self._tree.topLevelItem(i)
            host = host_item.text(0).lower()
            
            # Visibility logic
            host_in_scope = any(h in host for h in in_scope_hosts)
            if scope_only and not host_in_scope:
                host_item.setHidden(True)
                continue

            host_visible = not text or text in host.lower()
            child_visible_any = False
            for j in range(host_item.childCount()):
                child = host_item.child(j)
                path_visible = host_visible or (text in child.text(0).lower())
                child.setHidden(not path_visible)
                if path_visible:
                    child_visible_any = True
            host_item.setHidden(not host_visible and not child_visible_any)

    def clear(self):
        self._tree.clear()
        self._hosts.clear()
        self._count_label.setText("0 hosts, 0 requests")


# ─── Scope Editor ─────────────────────────────────────────────────────────────

class ScopeEditor(QWidget):
    """Define in/out of scope rules."""

    scope_changed = Signal(list)  # list of rule dicts

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Use advanced scope
        mode_grp = QGroupBox("Scope Definition")
        ml = QVBoxLayout(mode_grp)
        self._simple_radio = QRadioButton("Use simple scope definition")
        self._advanced_radio = QRadioButton("Use advanced scope definition")
        self._simple_radio.setChecked(True)
        ml.addWidget(self._simple_radio)
        ml.addWidget(self._advanced_radio)
        layout.addWidget(mode_grp)

        # Include rules
        include_grp = QGroupBox("Include in scope")
        il = QVBoxLayout(include_grp)

        self._include_table = self._make_scope_table()
        il.addWidget(self._include_table)

        include_btns = QHBoxLayout()
        add_inc = QPushButton("+ Add")
        add_inc.clicked.connect(lambda: self._add_rule(self._include_table))
        rem_inc = QPushButton("− Remove")
        rem_inc.clicked.connect(lambda: self._remove_rule(self._include_table))
        include_btns.addWidget(add_inc)
        include_btns.addWidget(rem_inc)
        include_btns.addStretch()
        il.addLayout(include_btns)
        layout.addWidget(include_grp)

        # Exclude rules
        exclude_grp = QGroupBox("Exclude from scope")
        el = QVBoxLayout(exclude_grp)
        self._exclude_table = self._make_scope_table()
        el.addWidget(self._exclude_table)

        exclude_btns = QHBoxLayout()
        add_exc = QPushButton("+ Add")
        add_exc.clicked.connect(lambda: self._add_rule(self._exclude_table))
        rem_exc = QPushButton("− Remove")
        rem_exc.clicked.connect(lambda: self._remove_rule(self._exclude_table))
        exclude_btns.addWidget(add_exc)
        exclude_btns.addWidget(rem_exc)
        exclude_btns.addStretch()
        el.addLayout(exclude_btns)
        layout.addWidget(exclude_grp)

        # Quick add
        quick_grp = QGroupBox("Quick Add URL")
        ql = QHBoxLayout(quick_grp)
        self._quick_url = QLineEdit()
        self._quick_url.setPlaceholderText("https://example.com/path")
        ql.addWidget(self._quick_url, 1)
        quick_add = QPushButton("Add to Scope")
        quick_add.setObjectName("actionBtn")
        quick_add.clicked.connect(self._quick_add)
        ql.addWidget(quick_add)
        layout.addWidget(quick_grp)

        layout.addStretch()

    def _make_scope_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["En", "Protocol", "Host", "Port", "Path"])
        table.setFixedHeight(130)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().hide()
        table.horizontalHeader().resizeSection(0, 30)
        table.horizontalHeader().resizeSection(1, 80)
        table.horizontalHeader().resizeSection(2, 180)
        table.horizontalHeader().resizeSection(3, 60)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    def _add_rule(self, table: QTableWidget):
        row = table.rowCount()
        table.insertRow(row)
        chk = QTableWidgetItem("✓")
        chk.setCheckState(Qt.CheckState.Checked)
        table.setItem(row, 0, chk)

        proto_combo = QComboBox()
        proto_combo.addItems(["Any", "http", "https"])
        table.setCellWidget(row, 1, proto_combo)

        for col, placeholder in [(2, ".*"), (3, ".*"), (4, ".*")]:
            item = QTableWidgetItem("")
            table.setItem(row, col, item)

    def _remove_rule(self, table: QTableWidget):
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)

    def _quick_add(self):
        url = self._quick_url.text().strip()
        if not url:
            return
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            row = self._include_table.rowCount()
            self._include_table.insertRow(row)
            chk = QTableWidgetItem("✓")
            chk.setCheckState(Qt.CheckState.Checked)
            self._include_table.setItem(row, 0, chk)

            proto_combo = QComboBox()
            proto_combo.addItems(["Any", "http", "https"])
            proto_combo.setCurrentText(parsed.scheme if parsed.scheme else "Any")
            self._include_table.setCellWidget(row, 1, proto_combo)
            self._include_table.setItem(row, 2, QTableWidgetItem(parsed.netloc or ".*"))
            port = str(parsed.port) if parsed.port else ".*"
            self._include_table.setItem(row, 3, QTableWidgetItem(port))
            self._include_table.setItem(row, 4, QTableWidgetItem(parsed.path or ".*"))
            self._quick_url.clear()
        except Exception as e:
            pass

    def add_host_rule(self, host: str, include: bool = True):
        table = self._include_table if include else self._exclude_table
        # Check if already exists
        for row in range(table.rowCount()):
            item = table.item(row, 2)
            if item and item.text() == host:
                return
        
        row = table.rowCount()
        table.insertRow(row)
        chk = QTableWidgetItem("✓")
        chk.setCheckState(Qt.CheckState.Checked)
        table.setItem(row, 0, chk)
        
        proto_combo = QComboBox()
        proto_combo.addItems(["Any", "http", "https"])
        table.setCellWidget(row, 1, proto_combo)
        
        table.setItem(row, 2, QTableWidgetItem(host))
        table.setItem(row, 3, QTableWidgetItem(".*"))
        table.setItem(row, 4, QTableWidgetItem(".*"))
        
        self.scope_changed.emit(self.get_scope_rules())

    def remove_host_rule(self, host: str):
        for table in [self._include_table, self._exclude_table]:
            for row in range(table.rowCount()):
                item = table.item(row, 2)
                if item and item.text() == host:
                    table.removeRow(row)
                    self.scope_changed.emit(self.get_scope_rules())
                    return

    def get_in_scope_hosts(self) -> list:
        hosts = []
        for row in range(self._include_table.rowCount()):
            chk = self._include_table.item(row, 0)
            if chk and chk.checkState() == Qt.CheckState.Checked:
                host_item = self._include_table.item(row, 2)
                if host_item:
                    hosts.append(host_item.text().lower())
        return hosts

    def get_scope_rules(self) -> list:
        rules = []
        # Include
        for row in range(self._include_table.rowCount()):
            chk = self._include_table.item(row, 0)
            proto_w = self._include_table.cellWidget(row, 1)
            host_item = self._include_table.item(row, 2)
            port_item = self._include_table.item(row, 3)
            path_item = self._include_table.item(row, 4)
            if host_item:
                rules.append({
                    "enabled": chk and chk.checkState() == Qt.CheckState.Checked,
                    "protocol": proto_w.currentText() if proto_w else "Any",
                    "host": host_item.text(),
                    "port": port_item.text() if port_item else ".*",
                    "path": path_item.text() if path_item else ".*",
                    "include": True,
                })
        # Exclude
        for row in range(self._exclude_table.rowCount()):
            chk = self._exclude_table.item(row, 0)
            proto_w = self._exclude_table.cellWidget(row, 1)
            host_item = self._exclude_table.item(row, 2)
            port_item = self._exclude_table.item(row, 3)
            path_item = self._exclude_table.item(row, 4)
            if host_item:
                rules.append({
                    "enabled": chk and chk.checkState() == Qt.CheckState.Checked,
                    "protocol": proto_w.currentText() if proto_w else "Any",
                    "host": host_item.text(),
                    "port": port_item.text() if port_item else ".*",
                    "path": path_item.text() if path_item else ".*",
                    "include": False,
                })
        return rules


# ─── Target Tab ───────────────────────────────────────────────────────────────

class TargetTab(QWidget):
    """
    Target tab - Site Map and Scope configuration.
    """
    scope_updated = Signal(list)
    send_to_tool = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(30)
        header.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 2, 8, 2)
        title = QLabel("Target")
        title.setStyleSheet(f"color:{HESPIA_ORANGE}; font-weight:bold; font-size:13px;")
        hl.addWidget(title)
        hl.addStretch()
        layout.addWidget(header)

        inner_tabs = QTabWidget()

        # Site Map
        self._site_map = SiteMapTree()
        self._site_map.send_to_tool.connect(self.send_to_tool.emit)
        inner_tabs.addTab(self._site_map, "Site map")

        # Scope
        self._scope_editor = ScopeEditor()
        self._scope_editor.scope_changed.connect(self.scope_updated)
        inner_tabs.addTab(self._scope_editor, "Scope")

        layout.addWidget(inner_tabs, 1)

    def add_flow(self, entry):
        self._site_map.add_flow(entry)

    def get_scope_rules(self) -> list:
        return self._scope_editor.get_scope_rules()
