"""
Intruder Tab - Automated payload fuzzing tool.
"""
import threading
import time
import re
from typing import List, Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox,
    QFrame, QTableWidget, QTableWidgetItem, QGroupBox,
    QSpinBox, QTextEdit, QPlainTextEdit, QProgressBar,
    QAbstractItemView, QScrollArea, QStackedWidget, QGridLayout,
    QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QApplication, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QTextDocument
from ui.request_editor import RequestEditor, CodeEditor, RequestResponseSplitter
from ui.styles import BURP_ORANGE, BURP_BG, BURP_BG_DARK, BURP_TEXT, BURP_BORDER, BURP_TEXT_DIM


# ─── Payload Position Highlighter ─────────────────────────────────────────────

class PayloadHighlighter(QSyntaxHighlighter):
    def __init__(self, doc: QTextDocument):
        super().__init__(doc)
        self._fmt = QTextCharFormat()
        self._fmt.setBackground(QColor("#5a3a00"))
        self._fmt.setForeground(QColor("#FFD700"))
        self._fmt.setFontWeight(700)

    def highlightBlock(self, text: str):
        pattern = re.compile(r"§[^§]*§")
        for m in pattern.finditer(text):
            self.setFormat(m.start(), m.end() - m.start(), self._fmt)


# ─── Positions Editor ─────────────────────────────────────────────────────────

class PositionsEditor(QWidget):
    """Editor for marking payload positions in a request using § markers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        tb = QFrame()
        tb.setFixedHeight(36)
        tb.setStyleSheet(f"background:{BURP_BG_DARK}; border-bottom:1px solid {BURP_BORDER};")
        tl = QHBoxLayout(tb)
        tl.setContentsMargins(8, 4, 8, 4)
        tl.setSpacing(6)

        attack_label = QLabel("Attack type:")
        tl.addWidget(attack_label)
        self._attack_combo = QComboBox()
        self._attack_combo.addItems(["Sniper", "Battering ram", "Pitchfork", "Cluster bomb"])
        self._attack_combo.setFixedWidth(160)
        tl.addWidget(self._attack_combo)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{BURP_BORDER};")
        tl.addWidget(sep)

        self._add_btn = QPushButton("§ Add §")
        self._add_btn.setFixedHeight(26)
        self._add_btn.setToolTip("Wrap selection with § markers")
        self._add_btn.clicked.connect(self._add_marker)
        tl.addWidget(self._add_btn)

        self._clear_btn = QPushButton("Clear §")
        self._clear_btn.setFixedHeight(26)
        self._clear_btn.clicked.connect(self._clear_markers)
        tl.addWidget(self._clear_btn)

        self._auto_btn = QPushButton("Auto §")
        self._auto_btn.setFixedHeight(26)
        self._auto_btn.setToolTip("Automatically detect parameters and add markers")
        self._auto_btn.clicked.connect(self._auto_mark)
        tl.addWidget(self._auto_btn)

        tl.addStretch()

        self._positions_label = QLabel("0 positions")
        self._positions_label.setStyleSheet(f"color:{BURP_ORANGE}; font-size:11px; font-weight:bold;")
        tl.addWidget(self._positions_label)

        layout.addWidget(tb)

        # Editor
        self._editor = CodeEditor(mode="request")
        self._highlighter = PayloadHighlighter(self._editor.document())
        self._editor.textChanged.connect(self._count_positions)
        layout.addWidget(self._editor, 1)

    def _add_marker(self):
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"§{selected}§")
        else:
            pos = cursor.position()
            cursor.insertText("§§")
            cursor.setPosition(pos + 1)
            self._editor.setTextCursor(cursor)

    def _clear_markers(self):
        text = self._editor.toPlainText()
        self._editor.setPlainText(text.replace("§", ""))

    def _auto_mark(self):
        text = self._editor.toPlainText()
        # Clear existing
        text = text.replace("§", "")
        # Find parameter values in URL query string and body
        def replace_val(m):
            return f"{m.group(1)}=§{m.group(2)}§"
        text = re.sub(r"([a-zA-Z_][a-zA-Z0-9_]*)=([^&\s\r\n]+)", replace_val, text)
        self._editor.setPlainText(text)

    def _count_positions(self):
        text = self._editor.toPlainText()
        markers = re.findall(r"§([^§]*)§", text)
        count = len(markers)
        self._positions_label.setText(f"{count} position{'s' if count != 1 else ''}")
        # Notify parent to update payload sets with names
        parent = self.parent()
        while parent and not hasattr(parent, "_payloads_panel"):
            parent = parent.parent()
        if parent:
            parent._payloads_panel.update_sets_count(count, names=markers)

    def set_request(self, raw: str):
        self._editor.setPlainText(raw)

    def get_request(self) -> str:
        return self._editor.toPlainText()

    def get_attack_type(self) -> str:
        return self._attack_combo.currentText()

    def get_positions(self) -> List[str]:
        """Extract payload position content."""
        text = self._editor.toPlainText()
        return re.findall(r"§([^§]*)§", text)

    def count_positions(self) -> int:
        return self._editor.toPlainText().count("§") // 2


# ─── Payloads Panel ───────────────────────────────────────────────────────────

class PayloadsPanel(QWidget):
    """Configure payloads for each position."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Dictionary of set_index: {type, data, num_from, num_to, num_step}
        self._payload_sets: Dict[int, dict] = {
            1: {"type": "Simple list", "data": "", "num_from": 1, "num_to": 100, "num_step": 1}
        }
        self._current_set = 1
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Payload set selector
        set_grp = QGroupBox("Payload Sets")
        sg = QHBoxLayout(set_grp)
        sg.addWidget(QLabel("Payload set:"))
        self._set_combo = QComboBox()
        self._set_combo.addItems(["1"])
        self._set_combo.setFixedWidth(60)
        self._set_combo.currentIndexChanged.connect(self._on_set_changed)
        sg.addWidget(self._set_combo)
        
        sg.addWidget(QLabel("Payload type:"))
        self._type_combo = QComboBox()
        self._type_combo.addItems([
            "Simple list", "Numbers", "Brute forcer", "Null payloads"
        ])
        self._type_combo.setFixedWidth(200)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        sg.addWidget(self._type_combo)
        sg.addStretch()
        layout.addWidget(set_grp)

        # Stack for different payload types
        self._stack = QStackedWidget()

        # ── Simple list
        list_widget = QWidget()
        ll = QVBoxLayout(list_widget)
        ll.addWidget(QLabel("Payload list:"))
        self._payload_list = QPlainTextEdit()
        self._payload_list.setPlaceholderText("One payload per line...")
        self._payload_list.setFixedHeight(180)
        self._payload_list.textChanged.connect(self._save_current_set)
        ll.addWidget(self._payload_list)

        list_btns = QHBoxLayout()
        load_file_btn = QPushButton("Load from File")
        load_file_btn.clicked.connect(self._load_file)
        paste_btn = QPushButton("Paste")
        paste_btn.clicked.connect(self._paste_payloads)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self._payload_list.clear())
        list_btns.addWidget(load_file_btn)
        list_btns.addWidget(paste_btn)
        list_btns.addWidget(clear_btn)
        list_btns.addStretch()
        ll.addLayout(list_btns)
        ll.addWidget(QLabel(f"Add item:"))
        add_row = QHBoxLayout()
        self._add_item_edit = QLineEdit()
        self._add_item_edit.setPlaceholderText("Payload to add...")
        add_item_btn = QPushButton("Add")
        add_item_btn.clicked.connect(self._add_item)
        add_row.addWidget(self._add_item_edit, 1)
        add_row.addWidget(add_item_btn)
        ll.addLayout(add_row)
        self._stack.addWidget(list_widget)

        # ── Numbers
        num_widget = QWidget()
        nl = QVBoxLayout(num_widget)
        ng = QGroupBox("Number range")
        ngl = QGridLayout(ng)
        ngl.addWidget(QLabel("From:"), 0, 0)
        self._num_from = QSpinBox(); self._num_from.setRange(-999999, 999999); self._num_from.setValue(1)
        self._num_from.valueChanged.connect(self._save_current_set)
        ngl.addWidget(self._num_from, 0, 1)
        ngl.addWidget(QLabel("To:"), 1, 0)
        self._num_to = QSpinBox(); self._num_to.setRange(-999999, 999999); self._num_to.setValue(100)
        self._num_to.valueChanged.connect(self._save_current_set)
        ngl.addWidget(self._num_to, 1, 1)
        ngl.addWidget(QLabel("Step:"), 2, 0)
        self._num_step = QSpinBox(); self._num_step.setRange(1, 9999); self._num_step.setValue(1)
        self._num_step.valueChanged.connect(self._save_current_set)
        ngl.addWidget(self._num_step, 2, 1)
        nl.addWidget(ng)
        self._stack.addWidget(num_widget)

        layout.addWidget(self._stack)

        # ── Payload processing
        proc_grp = QGroupBox("Payload Processing")
        pl = QVBoxLayout(proc_grp)
        proc_info = QLabel("Rules applied to each payload before use:")
        proc_info.setStyleSheet("color:#888; font-size:11px;")
        pl.addWidget(proc_info)

        self._proc_table = QTableWidget()
        self._proc_table.setColumnCount(3)
        self._proc_table.setHorizontalHeaderLabels(["En", "Rule", "Value"])
        self._proc_table.setFixedHeight(100)
        self._proc_table.horizontalHeader().resizeSection(0, 30)
        self._proc_table.horizontalHeader().resizeSection(1, 160)
        self._proc_table.horizontalHeader().setStretchLastSection(True)
        pl.addWidget(self._proc_table)

        proc_btns = QHBoxLayout()
        add_proc = QPushButton("Add Rule")
        add_proc.clicked.connect(self._add_proc_rule)
        rem_proc = QPushButton("Remove")
        rem_proc.clicked.connect(lambda: self._proc_table.removeRow(self._proc_table.currentRow()))
        proc_btns.addWidget(add_proc)
        proc_btns.addWidget(rem_proc)
        proc_btns.addStretch()
        pl.addLayout(proc_btns)
        layout.addWidget(proc_grp)

        # ── Payload encoding
        enc_grp = QGroupBox("Payload Encoding")
        el = QVBoxLayout(enc_grp)
        self._url_encode_check = QCheckBox("URL-encode these characters:")
        self._url_encode_check.setChecked(True)
        el.addWidget(self._url_encode_check)
        self._encode_chars = QLineEdit("!@#$%^&*()=+[]{}|;':\",./<>?\\`~")
        el.addWidget(self._encode_chars)
        layout.addWidget(enc_grp)

        layout.addStretch()
        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _on_set_changed(self, idx: int):
        self._current_set = idx + 1
        # Load from storage
        config = self._payload_sets.get(self._current_set, {
            "type": "Simple list", "data": "", "num_from": 1, "num_to": 100, "num_step": 1
        })
        
        # Block signals briefly to avoid recursive saving
        self._type_combo.blockSignals(True)
        self._payload_list.blockSignals(True)
        self._num_from.blockSignals(True)
        self._num_to.blockSignals(True)
        self._num_step.blockSignals(True)

        self._type_combo.setCurrentText(config["type"])
        self._payload_list.setPlainText(config["data"])
        self._num_from.setValue(config["num_from"])
        self._num_to.setValue(config["num_to"])
        self._num_step.setValue(config["num_step"])
        
        self._on_type_changed(config["type"])

        self._type_combo.blockSignals(False)
        self._payload_list.blockSignals(False)
        self._num_from.blockSignals(False)
        self._num_to.blockSignals(False)
        self._num_step.blockSignals(False)

    def _save_current_set(self):
        self._payload_sets[self._current_set] = {
            "type": self._type_combo.currentText(),
            "data": self._payload_list.toPlainText(),
            "num_from": self._num_from.value(),
            "num_to": self._num_to.value(),
            "num_step": self._num_step.value()
        }

    def _on_type_changed(self, t: str):
        if t == "Numbers":
            self._stack.setCurrentIndex(1)
        else:
            self._stack.setCurrentIndex(0)
        self._save_current_set()

    def update_sets_count(self, count: int, names: List[str] = None):
        """Update available sets based on positions count and names."""
        count = max(1, count)
        self._set_combo.blockSignals(True)
        self._set_combo.clear()
        
        for i in range(count):
            name = f" (§{names[i]}§)" if names and i < len(names) else ""
            self._set_combo.addItem(f"{i + 1}{name}")
            
            # Initialize storage for new sets
            if (i + 1) not in self._payload_sets:
                self._payload_sets[i + 1] = {"type": "Simple list", "data": "", "num_from": 1, "num_to": 100, "num_step": 1}
        
        self._set_combo.blockSignals(False)
        
        # Adjust current selection
        if self._current_set > count:
            self._set_combo.setCurrentIndex(0)
        else:
            self._set_combo.setCurrentIndex(self._current_set - 1)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Payload List", "", "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, "r", errors="replace") as f:
                self._payload_list.setPlainText(f.read())
            self._save_current_set()

    def _paste_payloads(self):
        text = QApplication.clipboard().text()
        self._payload_list.setPlainText(text)
        self._save_current_set()

    def _add_item(self):
        text = self._add_item_edit.text().strip()
        if text:
            existing = self._payload_list.toPlainText()
            if existing and not existing.endswith("\n"):
                existing += "\n"
            self._payload_list.setPlainText(existing + text)
            self._add_item_edit.clear()
            self._save_current_set()

    def get_all_payload_sets(self) -> Dict[int, List[str]]:
        """Retrieve actual payload lists for each set."""
        result = {}
        for idx, config in self._payload_sets.items():
            if config["type"] == "Numbers":
                f, to, st = config["num_from"], config["num_to"], config["num_step"]
                result[idx] = [str(n) for n in range(f, to + 1, st)] if st > 0 else []
            else:
                raw = config["data"]
                result[idx] = [p for p in raw.splitlines() if p]
        return result

    def get_payloads(self) -> List[str]:
        t = self._type_combo.currentText()
        if t == "Numbers":
            f, to, st = self._num_from.value(), self._num_to.value(), self._num_step.value()
            return [str(n) for n in range(f, to + 1, st)]
        else:
            raw = self._payload_list.toPlainText()
            return [p for p in raw.splitlines() if p]

    def _add_proc_rule(self):
        row = self._proc_table.rowCount()
        self._proc_table.insertRow(row)
        chk = QTableWidgetItem("✓")
        chk.setCheckState(Qt.CheckState.Checked)
        self._proc_table.setItem(row, 0, chk)
        rule_combo = QComboBox()
        rule_combo.addItems(["URL encode", "Base64 encode", "MD5 hash",
                             "Add prefix", "Add suffix", "Match/replace"])
        self._proc_table.setCellWidget(row, 1, rule_combo)
        self._proc_table.setItem(row, 2, QTableWidgetItem(""))


# ─── Attack Results Table ─────────────────────────────────────────────────────

class AttackResultsTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Filter bar
        fb = QFrame()
        fb.setFixedHeight(32)
        fb.setStyleSheet(f"background:{BURP_BG_DARK}; border-bottom:1px solid {BURP_BORDER};")
        fl = QHBoxLayout(fb)
        fl.setContentsMargins(6, 4, 6, 4)
        fl.setSpacing(6)
        fl.addWidget(QLabel("Filter:"))
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Search results...")
        self._filter.setFixedHeight(22)
        fl.addWidget(self._filter, 1)
        fl.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "2xx", "3xx", "4xx", "5xx"])
        self._status_filter.setFixedWidth(70)
        fl.addWidget(self._status_filter)
        layout.addWidget(fb)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["#", "Payload", "Status", "Error", "Timeout", "Length", "Comment"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().hide()
        self._table.verticalHeader().setDefaultSectionSize(22)
        self._table.horizontalHeader().resizeSection(0, 45)
        self._table.horizontalHeader().resizeSection(1, 200)
        self._table.horizontalHeader().resizeSection(2, 60)
        self._table.horizontalHeader().resizeSection(3, 55)
        self._table.horizontalHeader().resizeSection(4, 60)
        self._table.horizontalHeader().resizeSection(5, 70)
        self._table.currentItemChanged.connect(self._on_select)
        splitter.addWidget(self._table)

        self._detail = RequestResponseSplitter()
        splitter.addWidget(self._detail)
        splitter.setSizes([300, 250])

        layout.addWidget(splitter, 1)

        stats = QFrame()
        stats.setFixedHeight(22)
        stats.setStyleSheet(f"background:{BURP_BG_DARK};")
        sl = QHBoxLayout(stats)
        sl.setContentsMargins(8, 0, 8, 0)
        self._stats_label = QLabel("0 requests sent")
        self._stats_label.setStyleSheet(f"color:{BURP_TEXT_DIM}; font-size:11px;")
        sl.addWidget(self._stats_label)
        sl.addStretch()
        layout.addWidget(stats)

    def add_result(self, number, payload, status, length, req, resp, error=False, timeout=False):
        row = self._table.rowCount()
        self._table.insertRow(row)
        cells = [str(number), payload, str(status) if status else "-",
                 "✓" if error else "", "✓" if timeout else "", str(length)]
        for col, val in enumerate(cells):
            item = QTableWidgetItem(val)
            item.setData(Qt.ItemDataRole.UserRole + 1, req)
            item.setData(Qt.ItemDataRole.UserRole + 2, resp)
            if col == 2 and status:
                code = str(status)
                from ui.styles import HTTP_STATUS_COLORS
                color = HTTP_STATUS_COLORS.get(code[0], BURP_TEXT)
                item.setForeground(QColor(color))
            self._table.setItem(row, col, item)
        self._stats_label.setText(f"{row + 1} requests sent")

    def _on_select(self, current, _):
        if not current:
            return
        req = current.data(Qt.ItemDataRole.UserRole + 1) or ""
        resp = current.data(Qt.ItemDataRole.UserRole + 2) or ""
        self._detail.set_flow(req, resp)

    def clear(self):
        self._table.setRowCount(0)
        self._stats_label.setText("0 requests sent")


# ─── Intruder Worker ──────────────────────────────────────────────────────────

class IntruderWorker(QObject):
    result = Signal(int, str, object, int, str, str)  # num, payload, status, length, req, resp
    finished = Signal()
    progress = Signal(int, int)  # current, total

    def __init__(self, engine, host, port, is_https, template, payload_sets, attack_type, threads=5, delay_ms=0, timeout=3):
        super().__init__()
        self.engine = engine
        self.host = host
        self.port = port
        self.is_https = is_https
        self.template = template
        self.payload_sets = payload_sets # Dict[int, List[str]]
        self.attack_type = attack_type
        self.threads = max(1, threads)
        self.delay_ms = delay_ms
        self.timeout = timeout
        self._cancelled = False
        self._completed = 0

    def cancel(self):
        self._cancelled = True

    def run(self):
        from concurrent.futures import ThreadPoolExecutor
        import time
        import itertools

        # Find positions §...§
        pos_placeholders = re.findall(r"§[^§]*§", self.template)
        n_pos = len(pos_placeholders)
        
        # Prepare payload combinations
        combinations = []
        if self.attack_type == "Sniper":
            # For each position, try every payload in set 1
            payload_list = self.payload_sets.get(1, [])
            for p_idx in range(n_pos):
                for val in payload_list:
                    # combination is a list of values to insert into positions
                    # for sniper, we keep original value for other positions
                    # BUT our logic currently just replaces §...§ one by one.
                    # Let's simplify: sniper uses set 1 for all positions sequentially.
                    combo = [None] * n_pos
                    combo[p_idx] = val
                    combinations.append(combo)
        elif self.attack_type == "Battering ram":
            # Set 1 used for ALL positions at once
            for val in self.payload_sets.get(1, []):
                combinations.append([val] * n_pos)
        elif self.attack_type == "Pitchfork":
            # Parallel iteration: set 1 val 1 + set 2 val 1 ...
            lists = [self.payload_sets.get(i + 1, []) for i in range(n_pos)]
            for combo in zip(*lists):
                combinations.append(list(combo))
        elif self.attack_type == "Cluster bomb":
            # Cartesian product
            lists = [self.payload_sets.get(i + 1, []) for i in range(n_pos)]
            for combo in itertools.product(*lists):
                combinations.append(list(combo))

        total = len(combinations)
        self.progress.emit(0, total)
        self._completed = 0

        def do_attack(item):
            idx, combo = item
            if self._cancelled: return

            if self.delay_ms > 0:
                time.sleep(self.delay_ms / 1000.0)

            # Build request
            request = self.template
            # Combination is e.g. ["admin", "pass"]
            # Replace each §...§ with corresponding combo value
            temp_req = self.template
            for val in combo:
                # If sniper and val is None, we need to preserve the original marker text but without §
                # Actually, Burp Sniper replaces ONE position at a time.
                pass
            
            # Implementation for snippet replacement:
            final_req = ""
            parts = re.split(r"§[^§]*§", self.template)
            for i in range(len(parts)):
                final_req += parts[i]
                if i < len(combo):
                    val = combo[i]
                    if val is not None:
                        final_req += val
                    else:
                        # Restore original marker text
                        m = pos_placeholders[i]
                        final_req += m.replace("§", "")
            
            request = final_req

            try:
                resp = self.engine.send_raw_request(
                    self.host, self.port, self.is_https, request, timeout=self.timeout
                )
                
                status = None
                length = 0
                if resp:
                    if resp.startswith("Error:"):
                        status = None
                    else:
                        first_line = resp.split("\n")[0].strip()
                        parts = first_line.split(" ", 2)
                        if len(parts) >= 2:
                            try: status = int(parts[1])
                            except: status = None
                        length = len(resp)
                
                payload_str = ", ".join([str(v) for v in combo if v is not None])
                self.result.emit(idx + 1, payload_str, status, length, request, resp)
            except Exception as e:
                self.result.emit(idx + 1, "Error", None, 0, request, f"Error: {e}")

            self._completed += 1
            self.progress.emit(self._completed, total)

        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            list(executor.map(do_attack, enumerate(combinations)))

        self.finished.emit()


# ─── Main Intruder Tab ────────────────────────────────────────────────────────

class IntruderTab(QWidget):
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._thread: Optional[QThread] = None
        self._worker: Optional[IntruderWorker] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(30)
        header.setStyleSheet(f"background:{BURP_BG_DARK}; border-bottom:1px solid {BURP_BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 2, 8, 2)
        title = QLabel("Intruder — Automated Attack Tool")
        title.setStyleSheet(f"color:{BURP_ORANGE}; font-weight:bold; font-size:13px;")
        hl.addWidget(title)
        hl.addStretch()
        layout.addWidget(header)

        # Inner tabs
        self._tabs = QTabWidget()

        # ── Target tab
        target_w = self._build_target_tab()
        self._tabs.addTab(target_w, "Target")

        # ── Positions tab
        self._positions_editor = PositionsEditor()
        self._tabs.addTab(self._positions_editor, "Positions")

        # ── Payloads tab
        self._payloads_panel = PayloadsPanel()
        self._tabs.addTab(self._payloads_panel, "Payloads")

        # ── Options tab
        opts_w = self._build_options_tab()
        self._tabs.addTab(opts_w, "Options")

        # ── Results tab
        self._results = AttackResultsTable()
        self._tabs.addTab(self._results, "Results")

        layout.addWidget(self._tabs, 1)

        # ── Attack control bar
        attack_bar = QFrame()
        attack_bar.setFixedHeight(42)
        attack_bar.setStyleSheet(f"background:{BURP_BG_DARK}; border-top:1px solid {BURP_BORDER};")
        al = QHBoxLayout(attack_bar)
        al.setContentsMargins(8, 4, 8, 4)
        al.setSpacing(8)

        self._start_attack_btn = QPushButton("▶ Start Attack")
        self._start_attack_btn.setObjectName("actionBtn")
        self._start_attack_btn.setFixedHeight(32)
        self._start_attack_btn.clicked.connect(self._start_attack)
        al.addWidget(self._start_attack_btn)

        self._stop_attack_btn = QPushButton("◼ Stop")
        self._stop_attack_btn.setObjectName("dangerBtn")
        self._stop_attack_btn.setFixedHeight(32)
        self._stop_attack_btn.setEnabled(False)
        self._stop_attack_btn.clicked.connect(self._stop_attack)
        al.addWidget(self._stop_attack_btn)

        al.addStretch()

        self._progress = QProgressBar()
        self._progress.setFixedWidth(200)
        self._progress.setFixedHeight(18)
        self._progress.setVisible(False)
        al.addWidget(self._progress)

        self._attack_status = QLabel("Ready")
        self._attack_status.setStyleSheet(f"color:{BURP_TEXT_DIM}; font-size:11px;")
        al.addWidget(self._attack_status)

        layout.addWidget(attack_bar)

    def _build_target_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        grp = QGroupBox("Attack Target")
        gl = QGridLayout(grp)
        gl.addWidget(QLabel("Host:"), 0, 0)
        self._target_host = QLineEdit()
        self._target_host.setPlaceholderText("target.example.com")
        gl.addWidget(self._target_host, 0, 1)
        gl.addWidget(QLabel("Port:"), 1, 0)
        self._target_port = QSpinBox()
        self._target_port.setRange(1, 65535)
        self._target_port.setValue(443)
        gl.addWidget(self._target_port, 1, 1)
        gl.addWidget(QLabel("HTTPS:"), 2, 0)
        self._target_https = QCheckBox()
        self._target_https.setChecked(True)
        gl.addWidget(self._target_https, 2, 1)
        layout.addWidget(grp)

        thread_grp = QGroupBox("Resource Pool")
        tl = QGridLayout(thread_grp)
        tl.addWidget(QLabel("Concurrent requests:"), 0, 0)
        self._thread_count = QSpinBox()
        self._thread_count.setRange(1, 50)
        self._thread_count.setValue(10)
        tl.addWidget(self._thread_count, 0, 1)
        tl.addWidget(QLabel("Request delay (ms):"), 1, 0)
        self._req_delay = QSpinBox()
        self._req_delay.setRange(0, 60000)
        self._req_delay.setValue(0)
        tl.addWidget(self._req_delay, 1, 1)

        tl.addWidget(QLabel("Request timeout (s):"), 2, 0)
        self._req_timeout = QSpinBox()
        self._req_timeout.setRange(1, 60)
        self._req_timeout.setValue(3)
        tl.addWidget(self._req_timeout, 2, 1)

        layout.addWidget(thread_grp)
        layout.addStretch()
        return w

    def _build_options_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        redirect_grp = QGroupBox("Redirections")
        rl = QVBoxLayout(redirect_grp)
        self._follow_redirects = QCheckBox("Follow redirections")
        rl.addWidget(self._follow_redirects)
        l.addWidget(redirect_grp)

        grep_grp = QGroupBox("Grep - Match")
        gl_out = QVBoxLayout(grep_grp)
        grep_info = QLabel("Extract results where response contains:")
        grep_info.setStyleSheet("color:#888; font-size:11px;")
        gl_out.addWidget(grep_info)
        self._grep_table = QTableWidget()
        self._grep_table.setColumnCount(2)
        self._grep_table.setHorizontalHeaderLabels(["Enabled", "Expression"])
        self._grep_table.setFixedHeight(100)
        self._grep_table.horizontalHeader().setStretchLastSection(True)
        gl_out.addWidget(self._grep_table)
        gtb = QHBoxLayout()
        add_grep = QPushButton("Add")
        add_grep.clicked.connect(self._add_grep)
        rem_grep = QPushButton("Remove")
        rem_grep.clicked.connect(lambda: self._grep_table.removeRow(self._grep_table.currentRow()))
        gtb.addWidget(add_grep)
        gtb.addWidget(rem_grep)
        gtb.addStretch()
        gl_out.addLayout(gtb)
        l.addWidget(grep_grp)
        l.addStretch()
        return w

    def _add_grep(self):
        row = self._grep_table.rowCount()
        self._grep_table.insertRow(row)
        chk = QTableWidgetItem("✓")
        chk.setCheckState(Qt.CheckState.Checked)
        self._grep_table.setItem(row, 0, chk)
        self._grep_table.setItem(row, 1, QTableWidgetItem(""))

    def _start_attack(self):
        host = self._target_host.text().strip()
        # Clean hostname if user pasted a full URL
        if "://" in host:
            host = host.split("://")[-1].split("/")[0]
        # Remove trailing slash or spaces
        host = host.split("/")[0].strip()
        
        port = self._target_port.value()
        is_https = self._target_https.isChecked()
        template = self._positions_editor.get_request()
        payloads = self._payloads_panel.get_payloads()

        if not host:
            QMessageBox.warning(self, "No Target", "Please specify a target host in the Target tab.")
            return
        if not payloads:
            QMessageBox.warning(self, "No Payloads", "Add payloads in the Payloads tab.")
            return
        if self._positions_editor.count_positions() == 0:
            QMessageBox.warning(self, "No Positions", "Mark payload positions with § in the Positions tab.")
            return

        self._results.clear()
        self._tabs.setCurrentIndex(4)  # Switch to Results

        self._start_attack_btn.setEnabled(False)
        self._stop_attack_btn.setEnabled(True)
        self._progress.setVisible(True)
        
        payload_sets = self._payloads_panel.get_all_payload_sets()
        self._progress.setRange(0, 100) # Progress will be %
        self._progress.setValue(0)

        attack_type = self._positions_editor.get_attack_type()
        threads = self._thread_count.value()
        delay = self._req_delay.value()
        timeout = self._req_timeout.value()
        
        self._thread = QThread()
        self._worker = IntruderWorker(
            self.engine, host, port, is_https, template, payload_sets, 
            attack_type, threads=threads, delay_ms=delay, timeout=timeout
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.result.connect(self._on_result)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _stop_attack(self):
        if self._worker:
            self._worker.cancel()
        self._stop_attack_btn.setEnabled(False)
        self._attack_status.setText("Stopping...")

    def _on_result(self, num, payload, status, length, req, resp):
        self._results.add_result(num, payload, status, length, req, resp)

    def _on_progress(self, current, total):
        self._progress.setValue(current)
        self._attack_status.setText(f"{current}/{total} requests")

    def _on_finished(self):
        self._start_attack_btn.setEnabled(True)
        self._stop_attack_btn.setEnabled(False)
        self._progress.setVisible(False)
        total = self._results._table.rowCount()
        self._attack_status.setText(f"Attack complete — {total} results")

    def load_from_flow(self, entry):
        """Load a flow into the intruder."""
        self._target_host.setText(entry.host)
        self._target_port.setValue(entry.port)
        self._target_https.setChecked(entry.is_https)
        req_lines = [f"{entry.method} {entry.path} HTTP/1.1"]
        for k, v in entry.request_headers_raw.items():
            req_lines.append(f"{k}: {v}")
        req_lines.append("")
        try:
            req_lines.append(entry.request_body.decode("utf-8", errors="replace"))
        except Exception:
            pass
        self._positions_editor.set_request("\r\n".join(req_lines))
        self._tabs.setCurrentIndex(1)
