"""
Comparer Tab - Diff two pieces of text side by side.
"""
import difflib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QComboBox, QFrame, QPlainTextEdit,
    QTabWidget, QTextEdit, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import (
    QFont, QColor, QTextCursor, QTextCharFormat,
    QSyntaxHighlighter, QTextDocument
)
from ui.styles import HESPIA_ORANGE, HESPIA_BG, HESPIA_BG_DARK, HESPIA_BG_LIGHT, HESPIA_TEXT, HESPIA_BORDER, HESPIA_TEXT_DIM


class DiffHighlighter(QSyntaxHighlighter):
    """Highlights added/removed lines in diff output."""

    def __init__(self, doc: QTextDocument):
        super().__init__(doc)
        self._add_fmt = QTextCharFormat()
        self._add_fmt.setBackground(QColor("#e6ffec"))
        self._add_fmt.setForeground(QColor("#22863a"))

        self._del_fmt = QTextCharFormat()
        self._del_fmt.setBackground(QColor("#ffeef0"))
        self._del_fmt.setForeground(QColor("#cb2431"))

        self._hdr_fmt = QTextCharFormat()
        self._hdr_fmt.setBackground(QColor("#dbedff"))
        self._hdr_fmt.setForeground(QColor("#0366d6"))

        self._sep_fmt = QTextCharFormat()
        self._sep_fmt.setForeground(QColor("#888888"))

    def highlightBlock(self, text: str):
        if text.startswith("+++") or text.startswith("---"):
            self.setFormat(0, len(text), self._hdr_fmt)
        elif text.startswith("+"):
            self.setFormat(0, len(text), self._add_fmt)
        elif text.startswith("-"):
            self.setFormat(0, len(text), self._del_fmt)
        elif text.startswith("@@"):
            self.setFormat(0, len(text), self._hdr_fmt)
        elif text.startswith("\\"):
            self.setFormat(0, len(text), self._sep_fmt)


class ComparerPane(QWidget):
    """One side of the comparer — label + text editor."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        hdr = QFrame()
        hdr.setFixedHeight(28)
        hdr.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(8, 4, 8, 4)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color:{HESPIA_ORANGE}; font-weight:bold; font-size:11px;")
        hl.addWidget(lbl)
        hl.addStretch()
        self._stat = QLabel("")
        self._stat.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:10px;")
        hl.addWidget(self._stat)
        layout.addWidget(hdr)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText(f"Paste {title} content here...")
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(11)
        self._editor.setFont(font)
        self._editor.setStyleSheet(
            f"QPlainTextEdit {{ background:{HESPIA_BG_LIGHT}; color:{HESPIA_TEXT}; border:none; padding:4px; }}"
        )
        self._editor.textChanged.connect(self._update_stat)
        layout.addWidget(self._editor, 1)

    def _update_stat(self):
        text = self._editor.toPlainText()
        lines = len(text.splitlines())
        chars = len(text)
        self._stat.setText(f"{lines} lines, {chars} chars")

    def get_text(self) -> str:
        return self._editor.toPlainText()

    def set_text(self, text: str):
        self._editor.setPlainText(text)

    def clear(self):
        self._editor.clear()


class ComparerTab(QWidget):
    """
    Comparer tab - side-by-side text diff tool.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header bar
        header = QFrame()
        header.setFixedHeight(36)
        header.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 4, 10, 4)
        hl.setSpacing(8)

        title = QLabel("Comparer")
        title.setStyleSheet(f"color:{HESPIA_ORANGE}; font-weight:bold; font-size:13px;")
        hl.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{HESPIA_BORDER};")
        hl.addWidget(sep)

        hl.addWidget(QLabel("Compare by:"))
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Words", "Lines", "Bytes (hex)"])
        self._mode_combo.setFixedWidth(130)
        hl.addWidget(self._mode_combo)

        self._compare_btn = QPushButton("⚡ Compare")
        self._compare_btn.setObjectName("actionBtn")
        self._compare_btn.setFixedHeight(26)
        self._compare_btn.clicked.connect(self._do_compare)
        hl.addWidget(self._compare_btn)

        self._swap_btn = QPushButton("⇄ Swap")
        self._swap_btn.setFixedHeight(26)
        self._swap_btn.clicked.connect(self._swap_panes)
        hl.addWidget(self._swap_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedHeight(26)
        self._clear_btn.clicked.connect(self._clear_all)
        hl.addWidget(self._clear_btn)

        hl.addStretch()

        # Stats
        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:11px;")
        hl.addWidget(self._stats_label)

        layout.addWidget(header)

        # ── Main area: input panes + diff output
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: two input panes side by side
        input_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._pane1 = ComparerPane("Item 1")
        self._pane2 = ComparerPane("Item 2")
        input_splitter.addWidget(self._pane1)
        input_splitter.addWidget(self._pane2)
        input_splitter.setSizes([500, 500])
        splitter.addWidget(input_splitter)

        # Bottom: diff output tabs
        diff_tabs = QTabWidget()

        # Unified diff
        self._unified_diff = QPlainTextEdit()
        self._unified_diff.setReadOnly(True)
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(11)
        self._unified_diff.setFont(font)
        self._unified_diff.setStyleSheet(
            f"QPlainTextEdit {{ background:{HESPIA_BG_LIGHT}; color:{HESPIA_TEXT}; border:none; padding:4px; }}"
        )
        self._diff_highlighter = DiffHighlighter(self._unified_diff.document())
        diff_tabs.addTab(self._unified_diff, "Unified Diff")

        # Side-by-side highlighted diff
        self._side_diff_widget = self._make_side_by_side()
        diff_tabs.addTab(self._side_diff_widget, "Side by Side")

        # Summary
        self._summary_widget = self._make_summary()
        diff_tabs.addTab(self._summary_widget, "Summary")

        splitter.addWidget(diff_tabs)
        splitter.setSizes([350, 300])

        layout.addWidget(splitter, 1)

    def _make_side_by_side(self) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)

        self._sbs_left = QPlainTextEdit()
        self._sbs_left.setReadOnly(True)
        self._sbs_right = QPlainTextEdit()
        self._sbs_right.setReadOnly(True)

        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        for ed in (self._sbs_left, self._sbs_right):
            ed.setFont(font)
            ed.setStyleSheet(
                f"QPlainTextEdit {{ background:{HESPIA_BG_LIGHT}; color:{HESPIA_TEXT}; border:none; padding:4px; }}"
            )

        # Sync scrolling
        self._sbs_left.verticalScrollBar().valueChanged.connect(
            self._sbs_right.verticalScrollBar().setValue
        )
        self._sbs_right.verticalScrollBar().valueChanged.connect(
            self._sbs_left.verticalScrollBar().setValue
        )

        l.addWidget(self._sbs_left, 1)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setStyleSheet(f"color:{HESPIA_BORDER};")
        l.addWidget(div)

        l.addWidget(self._sbs_right, 1)
        return w

    def _make_summary(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(8)
        self._summary_label = QLabel("Click 'Compare' to see summary.")
        self._summary_label.setStyleSheet(f"color:{HESPIA_TEXT}; font-size:12px;")
        self._summary_label.setWordWrap(True)
        l.addWidget(self._summary_label)
        l.addStretch()
        return w

    def _do_compare(self):
        mode = self._mode_combo.currentText()
        text1 = self._pane1.get_text()
        text2 = self._pane2.get_text()

        if mode == "Words":
            lines1 = text1.split()
            lines2 = text2.split()
        elif mode == "Bytes (hex)":
            lines1 = [f"{b:02X}" for b in text1.encode()]
            lines2 = [f"{b:02X}" for b in text2.encode()]
        else:  # Lines
            lines1 = text1.splitlines(keepends=True)
            lines2 = text2.splitlines(keepends=True)

        # Unified diff
        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile="Item 1", tofile="Item 2",
            lineterm="" if mode == "Lines" else " "
        ))
        self._unified_diff.setPlainText("".join(diff) if diff else "No differences found.")

        # Side by side
        self._update_sbs(text1, text2)

        # Stats
        additions = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
        self._stats_label.setText(
            f"+{additions} additions  −{deletions} deletions"
        )

        # Summary
        total_lines = max(len(text1.splitlines()), len(text2.splitlines()))
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio() * 100
        self._summary_label.setText(
            f"<b>Comparison Summary</b><br><br>"
            f"• Similarity: <span style='color:{HESPIA_ORANGE}'>{similarity:.1f}%</span><br>"
            f"• Item 1: {len(text1)} chars, {len(text1.splitlines())} lines<br>"
            f"• Item 2: {len(text2)} chars, {len(text2.splitlines())} lines<br>"
            f"• Additions: <span style='color:#4CAF50'>+{additions}</span><br>"
            f"• Deletions: <span style='color:#F44336'>−{deletions}</span><br>"
            f"• Changed ratio: {100-similarity:.1f}%"
        )

    def _update_sbs(self, text1: str, text2: str):
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        matcher = difflib.SequenceMatcher(None, lines1, lines2)

        left_lines = []
        right_lines = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for line in lines1[i1:i2]:
                    left_lines.append(line)
                    right_lines.append(line)
            elif tag == "replace":
                left_block = lines1[i1:i2]
                right_block = lines2[j1:j2]
                max_len = max(len(left_block), len(right_block))
                for k in range(max_len):
                    left_lines.append("[~] " + (left_block[k] if k < len(left_block) else ""))
                    right_lines.append("[~] " + (right_block[k] if k < len(right_block) else ""))
            elif tag == "delete":
                for line in lines1[i1:i2]:
                    left_lines.append("[-] " + line)
                    right_lines.append("")
            elif tag == "insert":
                for line in lines2[j1:j2]:
                    left_lines.append("")
                    right_lines.append("[+] " + line)

        self._sbs_left.setPlainText("\n".join(left_lines))
        self._sbs_right.setPlainText("\n".join(right_lines))

    def _swap_panes(self):
        t1 = self._pane1.get_text()
        t2 = self._pane2.get_text()
        self._pane1.set_text(t2)
        self._pane2.set_text(t1)

    def _clear_all(self):
        self._pane1.clear()
        self._pane2.clear()
        self._unified_diff.clear()
        self._sbs_left.clear()
        self._sbs_right.clear()
        self._stats_label.setText("")
        self._summary_label.setText("Click 'Compare' to see summary.")

    def load_texts(self, text1: str, text2: str):
        """Pre-populate both panes."""
        self._pane1.set_text(text1)
        self._pane2.set_text(text2)
        self._do_compare()
