"""
Main Window - HESPIA Suite-like main application window.
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTabBar, QLabel, QStatusBar, QPushButton,
    QFrame, QDialog, QDialogButtonBox, QSpinBox, QLineEdit,
    QGroupBox, QCheckBox, QMessageBox, QApplication, QMenuBar,
    QMenu, QToolBar, QSizePolicy, QSplashScreen, QGridLayout,
    QScrollArea, QPlainTextEdit, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import (
    QIcon, QAction, QFont, QColor, QPixmap, QPainter,
    QLinearGradient, QKeySequence
)
from ui.styles import (
    MAIN_STYLESHEET, HESPIA_ORANGE, HESPIA_BG, HESPIA_BG_DARK, HESPIA_BG_LIGHT,
    HESPIA_TEXT, HESPIA_BORDER, HESPIA_TEXT_DIM, HESPIA_SUCCESS, HESPIA_ERROR,
    HESPIA_INFO_BG, BANNER_START_STYLE, BANNER_STOP_STYLE
)
from ui.proxy_tab import ProxyTab
from ui.repeater_tab import RepeaterTab
from ui.intruder_tab import IntruderTab
from ui.decoder_tab import DecoderTab
from ui.comparer_tab import ComparerTab
from ui.target_tab import TargetTab
from ui.help_suite import HespiaHelpSuite
from core.engine import ProxyEngine


# ─── Proxy Start Dialog ───────────────────────────────────────────────────────

class ProxyConfigDialog(QDialog):
    def __init__(self, host: str = "127.0.0.1", port: int = 8080, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Proxy Listener")
        self.setFixedSize(380, 220)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        grp = QGroupBox("Listener Settings")
        gl = QVBoxLayout(grp)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("Bind address:"))
        self._host = QLineEdit(host)
        self._host.setFixedWidth(150)
        hl.addWidget(self._host)
        gl.addLayout(hl)

        pl = QHBoxLayout()
        pl.addWidget(QLabel("Bind port:"))
        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(port)
        self._port.setFixedWidth(80)
        pl.addWidget(self._port)
        pl.addStretch()
        gl.addLayout(pl)

        ssl_help = QLabel(
            "🔒 For HTTPS interception, install the CA:\n"
            "  Browse to http://mitm.it while using this proxy"
        )
        ssl_help.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:10px;")
        gl.addWidget(ssl_help)

        layout.addWidget(grp)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_config(self):
        return self._host.text().strip(), self._port.value()


# ─── Logger Widget (Log tab) ──────────────────────────────────────────────────

class LoggerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QPlainTextEdit, QComboBox
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setFixedHeight(32)
        toolbar.setStyleSheet(f"background:{HESPIA_BG_DARK}; border-bottom:1px solid {HESPIA_BORDER};")
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(8, 4, 8, 4)
        tl.setSpacing(6)
        tl.addWidget(QLabel("Level:"))
        self._level = QComboBox()
        self._level.addItems(["All", "Info", "Warning", "Error"])
        self._level.setFixedWidth(90)
        tl.addWidget(self._level)
        tl.addStretch()
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(22)
        clear_btn.clicked.connect(self._clear)
        tl.addWidget(clear_btn)
        layout.addWidget(toolbar)

        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        font = QFont()
        font.setFamily("Consolas")
        font.setPointSize(10)
        self._editor.setFont(font)
        self._editor.setStyleSheet(
            f"QPlainTextEdit {{ background:{HESPIA_BG_LIGHT}; color:{HESPIA_TEXT}; border:none; padding:4px; }}"
        )
        layout.addWidget(self._editor, 1)

    def append(self, level: str, message: str):
        import time as _time
        ts = _time.strftime("%H:%M:%S")
        colors = {"info": "#d4d4d4", "warn": "#FFCC55", "error": "#FF5555"}
        color = colors.get(level.lower(), "#d4d4d4")
        prefix_col = {"info": "#4ec994", "warn": "#ffcc55", "error": "#ff5555"}
        pc = prefix_col.get(level.lower(), "#888")
        html = (
            f'<span style="color:#555;">[{ts}]</span> '
            f'<span style="color:{pc}; font-weight:bold;">[{level.upper()}]</span> '
            f'<span style="color:{color};">{message}</span>'
        )
        self._editor.appendHtml(html)
        # Auto scroll
        sb = self._editor.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear(self):
        self._editor.clear()


# ─── Dashboard Widget ─────────────────────────────────────────────────────────

class DashboardWidget(QWidget):
    start_proxy_requested = Signal()
    stop_proxy_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Dashboard Header
        header = QFrame()
        header.setFixedHeight(120)
        header.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f8f8);
            border-bottom: 1px solid {HESPIA_BORDER};
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(30, 0, 30, 0)
        
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 20, 0, 20)
        t1 = QLabel("Workbench")
        t1.setStyleSheet(f"color:{HESPIA_TEXT}; font-size:28px; font-weight:700; font-family:'Segoe UI Semibold';")
        title_col.addWidget(t1)
        t2 = QLabel("Welcome to Hespia. Monitor and manage your security testing tasks here.")
        t2.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:13px;")
        title_col.addWidget(t2)
        hl.addLayout(title_col)
        hl.addStretch()

        layout.addWidget(header)

        # ── Main Content Area (Scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: #fdfdfd;")
        
        card_container = QWidget()
        cl = QGridLayout(card_container)
        cl.setContentsMargins(30, 30, 30, 30)
        cl.setSpacing(24)

        # ── CARD 1: Local Proxy Task
        proxy_card, pl = self._make_card("Local Proxy Service")
        pl.setContentsMargins(24, 24, 24, 24)
        pl.setSpacing(12)

        self._proxy_status = QLabel("● SERVICE STOPPED")
        self._proxy_status.setStyleSheet(f"color:{HESPIA_ERROR}; font-size:15px; font-weight:800; letter-spacing:1px;")
        pl.addWidget(self._proxy_status)

        self._proxy_addr = QLabel("The proxy listener is not active. Click start to begin capturing traffic.")
        self._proxy_addr.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:12px;")
        self._proxy_addr.setWordWrap(True)
        pl.addWidget(self._proxy_addr)

        pl.addSpacing(10)
        btn_layout = QHBoxLayout()
        self._start_btn = QPushButton("▶ START PROXY")
        self._start_btn.setObjectName("actionBtn")
        self._start_btn.setFixedHeight(44)
        self._start_btn.clicked.connect(self.start_proxy_requested)
        btn_layout.addWidget(self._start_btn, 1)

        self._stop_btn = QPushButton("◼ STOP PROXY")
        self._stop_btn.setObjectName("dangerBtn")
        self._stop_btn.setFixedHeight(44)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self.stop_proxy_requested)
        btn_layout.addWidget(self._stop_btn, 1)
        pl.addLayout(btn_layout)

        cl.addWidget(proxy_card, 0, 0)

        # ── CARD 2: Activity Stats
        stats_card, sl = self._make_card("Session Overview")
        sl.setContentsMargins(24, 24, 24, 24)
        sl.setSpacing(20)

        stats_row = QHBoxLayout()
        for attr, label in [("_stat_requests", "Total Flows"), ("_stat_intercepted", "Intercepted"), ("_stat_hosts", "Unique Hosts")]:
            scol = QVBoxLayout()
            v = QLabel("0")
            v.setStyleSheet(f"color:{HESPIA_ORANGE}; font-size:28px; font-weight:bold;")
            setattr(self, attr, v)
            scol.addWidget(v, 0, Qt.AlignmentFlag.AlignCenter)
            l = QLabel(label.upper())
            l.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:10px; font-weight:bold; letter-spacing:1px;")
            scol.addWidget(l, 0, Qt.AlignmentFlag.AlignCenter)
            stats_row.addLayout(scol)
        sl.addLayout(stats_row)
        
        sl.addStretch()
        cl.addWidget(stats_card, 0, 1)

        # ── CARD 3: Intercept Config
        intercept_card, il = self._make_card("Interception Rules")
        il.setContentsMargins(24, 24, 24, 24)
        il.setSpacing(8)
        il.addWidget(QLabel("● Request Interception: <span style='color:%s;'>OFF</span>" % HESPIA_ERROR))
        il.addWidget(QLabel("● Filter: All traffic"))
        il.addWidget(QLabel("● Scope: Global"))
        il.addStretch()
        view_rules = QPushButton("View Proxy Rules")
        view_rules.setFixedHeight(30)
        il.addWidget(view_rules)
        cl.addWidget(intercept_card, 1, 0)

        # ── CARD 4: Getting Started
        guide_card, gl = self._make_card("Getting Started")
        gl.setContentsMargins(20, 20, 20, 20)
        gl.setSpacing(8)
        for step in ["1. Start proxy service", "2. Configure browser proxy (8080)", "3. Install CA cert (mitm.it)", "4. Enable intercept (Proxy tab)"]:
            s = QLabel(step)
            s.setStyleSheet(f"color:{HESPIA_TEXT}; font-size:12px;")
            gl.addWidget(s)
        gl.addStretch()
        cl.addWidget(guide_card, 1, 1)

        # ── CARD 5: Event Log View (Large)
        log_card, ll = self._make_card("Task Event Log")
        ll.setContentsMargins(1, 1, 1, 1) # Full bleed editor
        self._quick_log = QPlainTextEdit()
        self._quick_log.setReadOnly(True)
        self._quick_log.setPlaceholderText("Capture events will appear here...")
        self._quick_log.setStyleSheet(f"border:none; border-bottom-left-radius:6px; border-bottom-right-radius:6px; background:#ffffff; color:{HESPIA_TEXT}; font-family:Consolas; font-size:11px; padding: 10px;")
        ll.addWidget(self._quick_log)
        cl.addWidget(log_card, 2, 0, 1, 2) # Span across (row 2, col 0, span 1 row, 2 cols)

        scroll.setWidget(card_container)
        layout.addWidget(scroll, 1)

    def _make_card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid {HESPIA_BORDER};
                border-radius: 6px;
            }}
        """)
        # Base layout
        l = QVBoxLayout(f)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(0)
        
        hdr = QFrame()
        hdr.setFixedHeight(34)
        hdr.setStyleSheet(f"background:{HESPIA_BG_DARK}; border:none; border-bottom:1px solid {HESPIA_BORDER}; border-top-left-radius:6px; border-top-right-radius:6px;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(12, 0, 12, 0)
        tl = QLabel(title.upper())
        tl.setStyleSheet(f"color:{HESPIA_TEXT}; font-size:11px; font-weight:bold; letter-spacing:1px;")
        hl.addWidget(tl)
        l.addWidget(hdr)

        # Content container with layout
        content = QWidget()
        content.setStyleSheet("border:none; background:transparent;")
        cl = QVBoxLayout(content)
        l.addWidget(content, 1)
        
        return f, cl

    def set_running(self, host: str, port: int):
        self._proxy_status.setText("● SERVICE RUNNING")
        self._proxy_status.setStyleSheet(f"color:{HESPIA_SUCCESS}; font-size:16px; font-weight:bold; letter-spacing:1px;")
        self._proxy_addr.setText(f"Hespia listening on {host}:{port}")
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

    def set_stopped(self):
        self._proxy_status.setText("● SERVICE STOPPED")
        self._proxy_status.setStyleSheet(f"color:{HESPIA_ERROR}; font-size:16px; font-weight:bold; letter-spacing:1px;")
        self._proxy_addr.setText("Proxy listener is not active.")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

    def update_stats(self, requests: int = None, intercepted: int = None, hosts: int = None):
        if requests is not None:
            self._stat_requests.setText(str(requests))
        if intercepted is not None:
            self._stat_intercepted.setText(str(intercepted))
        if hosts is not None:
            self._stat_hosts.setText(str(hosts))


# ─── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._engine = ProxyEngine()
        self._request_count = 0
        self._intercepted_count = 0
        self._is_running = False
        self._current_host = "127.0.0.1"
        self._current_port = 8080

        self.setWindowTitle("Hespia — Advanced Web Proxy Tool")
        self.setMinimumSize(1024, 700) # Smaller min-height for laptop screens
        self.resize(1440, 900)

        self._setup_style()
        self._setup_ui()
        self._connect_engine()
        self._setup_menus()
        self._setup_status_bar()

    def _setup_style(self):
        self.setStyleSheet(MAIN_STYLESHEET)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top banner
        banner = QFrame()
        banner.setFixedHeight(38)
        banner.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f" stop:0 #fff, stop:1 #f0f0f0);"
            f" border-bottom: 1px solid {HESPIA_BORDER};"
        )
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(12, 4, 12, 4)
        bl.setSpacing(12)

        logo = QLabel("Hespia")
        logo.setStyleSheet(
            f"color:{HESPIA_ORANGE}; font-size:18px; font-weight:bold; letter-spacing:1.5px;"
        )
        bl.addWidget(logo)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color:{HESPIA_BORDER}44;")
        bl.addWidget(sep)

        # Quick-start controls in banner
        self._banner_start_btn = QPushButton("▶ Start")
        self._banner_start_btn.setFixedHeight(26)
        self._banner_start_btn.setFixedWidth(70)
        self._banner_start_btn.setStyleSheet(BANNER_START_STYLE)
        self._banner_start_btn.clicked.connect(self._quick_start)
        bl.addWidget(self._banner_start_btn)

        self._banner_stop_btn = QPushButton("◼ Stop")
        self._banner_stop_btn.setFixedHeight(26)
        self._banner_stop_btn.setFixedWidth(70)
        self._banner_stop_btn.setEnabled(False)
        self._banner_stop_btn.setStyleSheet(BANNER_STOP_STYLE)
        self._banner_stop_btn.clicked.connect(self._stop_proxy)
        bl.addWidget(self._banner_stop_btn)

        self._banner_status = QLabel("Proxy: Stopped")
        self._banner_status.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:11px;")
        bl.addWidget(self._banner_status)

        bl.addStretch()

        # Request counter in banner
        self._banner_req_count = QLabel("0 requests")
        self._banner_req_count.setStyleSheet(f"color:{HESPIA_ORANGE}; font-size:11px; font-weight:bold;")
        bl.addWidget(self._banner_req_count)

        layout.addWidget(banner)

        # ── Main tab widget
        self._main_tabs = QTabWidget()
        self._main_tabs.setObjectName("mainTabWidget")
        tab_bar = self._main_tabs.tabBar()
        tab_bar.setObjectName("mainTabBar")
        tab_bar.setExpanding(False)

        # Create all tabs
        self._dashboard = DashboardWidget()
        self._dashboard.start_proxy_requested.connect(self._show_proxy_config)
        self._dashboard.stop_proxy_requested.connect(self._stop_proxy)
        self._main_tabs.addTab(self._dashboard, "Dashboard")

        self._target_tab = TargetTab()
        self._target_tab.scope_updated.connect(self._on_scope_updated)
        self._main_tabs.addTab(self._target_tab, "Target")

        self._proxy_tab = ProxyTab()
        self._proxy_tab.forward_request.connect(self._engine.forward_request)
        self._proxy_tab.forward_response.connect(self._engine.forward_response)
        self._proxy_tab.drop_flow.connect(self._engine.drop_flow)
        self._proxy_tab.intercept_changed.connect(self._on_intercept_changed)
        self._proxy_tab.settings_changed.connect(self._on_proxy_settings_changed)
        self._proxy_tab.send_to_repeater.connect(self._send_to_repeater)
        self._proxy_tab.send_to_intruder.connect(self._send_to_intruder)
        self._proxy_tab.send_to_decoder.connect(self._on_send_to_decoder)
        self._main_tabs.addTab(self._proxy_tab, "Proxy")

        self._intruder_tab = IntruderTab(self._engine)
        self._intruder_tab.send_to_decoder.connect(self._on_send_to_decoder)
        self._main_tabs.addTab(self._intruder_tab, "Intruder")

        self._repeater_tab = RepeaterTab(self._engine)
        self._repeater_tab.send_to_decoder.connect(self._on_send_to_decoder)
        self._main_tabs.addTab(self._repeater_tab, "Repeater")

        self._decoder_tab = DecoderTab()
        self._main_tabs.addTab(self._decoder_tab, "Decoder")

        self._comparer_tab = ComparerTab()
        self._main_tabs.addTab(self._comparer_tab, "Comparer")

        self._logger = LoggerWidget()
        self._main_tabs.addTab(self._logger, "Logger")

        self._main_tabs.addTab(self._make_help_tab(), "Help")

        # Style the main tab bar
        self._main_tabs.tabBar().setStyleSheet(f"""
            QTabBar::tab {{
                font-size: 12px;
                padding: 9px 18px;
                font-weight: 600;
                min-width: 80px;
            }}
        """)

        layout.addWidget(self._main_tabs, 1)

    def _make_help_tab(self) -> QWidget:
        self._help_suite = HespiaHelpSuite()
        return self._help_suite

    def _connect_engine(self):
        sig = self._engine.signals
        sig.flow_added.connect(self._on_flow_added)
        sig.flow_updated.connect(self._on_flow_updated)
        sig.request_intercepted.connect(self._on_request_intercepted)
        sig.response_intercepted.connect(self._on_response_intercepted)
        sig.proxy_started.connect(self._on_proxy_started)
        sig.proxy_stopped.connect(self._on_proxy_stopped)
        sig.proxy_error.connect(self._on_proxy_error)
        sig.log_message.connect(self._on_log_message)
        sig.flow_count.connect(self._on_flow_count)

    def _on_log_message(self, level: str, message: str):
        self._logger.append(level, message)
        # Also add to dashboard quick log
        import time
        ts = time.strftime("%H:%M:%S")
        self._dashboard._quick_log.appendPlainText(f"[{ts}] [{level.upper()}] {message}")
        # Auto scroll dashboard log
        sb = self._dashboard._quick_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _setup_menus(self):
        mb = self.menuBar()

        # Project menu
        project = mb.addMenu("Project")
        new_act = QAction("New Session", self)
        new_act.setShortcut(QKeySequence("Ctrl+N"))
        new_act.triggered.connect(self._new_session)
        project.addAction(new_act)

        save_act = QAction("Export Log...", self)
        save_act.setShortcut(QKeySequence("Ctrl+S"))
        save_act.triggered.connect(self._export_log)
        project.addAction(save_act)

        project.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence("Ctrl+Q"))
        quit_act.triggered.connect(self.close)
        project.addAction(quit_act)

        # Proxy menu
        proxy_m = mb.addMenu("Proxy")
        start_act = QAction("Start Proxy...", self)
        start_act.triggered.connect(self._show_proxy_config)
        proxy_m.addAction(start_act)
        stop_act = QAction("Stop Proxy", self)
        stop_act.triggered.connect(self._stop_proxy)
        proxy_m.addAction(stop_act)
        proxy_m.addSeparator()
        clear_act = QAction("Clear History", self)
        clear_act.triggered.connect(self._proxy_tab.clear_history)
        proxy_m.addAction(clear_act)

        # Tools menu
        tools = mb.addMenu("Tools")
        cert_act = QAction("View CA Certificate", self)
        cert_act.triggered.connect(self._show_cert_info)
        tools.addAction(cert_act)

        # Help
        help_m = mb.addMenu("Help")
        about_act = QAction("About Hespia", self)
        about_act.triggered.connect(self._show_about)
        help_m.addAction(about_act)

    def _setup_status_bar(self):
        sb = self.statusBar()
        # Left: proxy status
        self._status_proxy_lbl = QLabel("● Proxy: Stopped")
        self._status_proxy_lbl.setStyleSheet(f"color:{HESPIA_ERROR}; font-weight:bold;")
        sb.addWidget(self._status_proxy_lbl)

        # Center: message
        self._status_msg = QLabel("")
        sb.addWidget(self._status_msg, 1)

        # Right: counters
        self._status_reqs = QLabel("Requests: 0")
        self._status_reqs.setStyleSheet(f"color:{HESPIA_TEXT_DIM};")
        sb.addPermanentWidget(self._status_reqs)

    # ── Proxy lifecycle slots ──────────────────────────────────────────────

    def _show_proxy_config(self):
        dlg = ProxyConfigDialog(self._current_host, self._current_port, self)
        dlg.setStyleSheet(MAIN_STYLESHEET)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            host, port = dlg.get_config()
            self._current_host = host
            self._current_port = port
            self._start_proxy(host, port)

    def _quick_start(self):
        self._start_proxy(self._current_host, self._current_port)

    def _start_proxy(self, host: str, port: int):
        if self._is_running:
            return
        self._engine.start(host, port)
        self._logger.append("info", f"Starting proxy on {host}:{port}...")

    def _stop_proxy(self):
        if not self._is_running:
            return
        self._engine.stop()
        self._logger.append("info", "Stopping proxy...")

    def _on_proxy_started(self, host: str, port: int):
        self._is_running = True
        self._dashboard.set_running(host, port)
        self._status_proxy_lbl.setText(f"● Proxy: {host}:{port}")
        self._status_proxy_lbl.setStyleSheet(f"color:{HESPIA_SUCCESS}; font-weight:bold;")
        self._banner_status.setText(f"Proxy: {host}:{port}")
        self._banner_status.setStyleSheet(f"color:{HESPIA_SUCCESS}; font-size:11px; font-weight:bold;")
        self._banner_start_btn.setEnabled(False)
        self._banner_stop_btn.setEnabled(True)
        self._status_msg.setText(f"Listening on {host}:{port} — Configure browser proxy to use this address")

    def _on_proxy_stopped(self):
        self._is_running = False
        self._dashboard.set_stopped()
        self._status_proxy_lbl.setText("● Proxy: Stopped")
        self._status_proxy_lbl.setStyleSheet(f"color:{HESPIA_ERROR}; font-weight:bold;")
        self._banner_status.setText("Proxy: Stopped")
        self._banner_status.setStyleSheet(f"color:{HESPIA_TEXT_DIM}; font-size:11px;")
        self._banner_start_btn.setEnabled(True)
        self._banner_stop_btn.setEnabled(False)
        self._status_msg.setText("Proxy stopped")

    def _on_proxy_error(self, msg: str):
        self._is_running = False
        self._logger.append("error", f"Proxy error: {msg}")
        self._dashboard.set_stopped()
        self._banner_start_btn.setEnabled(True)
        self._banner_stop_btn.setEnabled(False)
        QMessageBox.critical(
            self, "Proxy Error",
            f"Failed to start proxy:\n\n{msg}\n\nCheck if the port is already in use."
        )

    # ── Flow slots ────────────────────────────────────────────────────────

    def _on_flow_added(self, entry):
        self._request_count += 1
        self._proxy_tab.on_flow_added(entry)
        self._target_tab.add_flow(entry)

    def _on_flow_updated(self, entry):
        self._proxy_tab.on_flow_updated(entry)
        self._target_tab.add_flow(entry)  # update

    def _on_flow_count(self, count: int):
        self._banner_req_count.setText(f"{count} requests")
        self._status_reqs.setText(f"Requests: {count}")
        self._dashboard.update_stats(requests=count)

    def _on_request_intercepted(self, flow_id: str, raw: str):
        self._intercepted_count += 1
        self._proxy_tab.on_request_intercepted(flow_id, raw)
        self._dashboard.update_stats(intercepted=self._intercepted_count)
        # Switch to Proxy tab
        self._main_tabs.setCurrentWidget(self._proxy_tab)

    def _on_response_intercepted(self, flow_id: str, raw_req: str, raw_resp: str):
        self._intercepted_count += 1
        self._proxy_tab.on_response_intercepted(flow_id, raw_req, raw_resp)
        self._dashboard.update_stats(intercepted=self._intercepted_count)
        self._main_tabs.setCurrentWidget(self._proxy_tab)

    def _on_intercept_changed(self, req: bool, resp: bool):
        self._engine.intercept_requests = req
        self._engine.intercept_responses = resp
        # Update all rules
        settings = self._proxy_tab.get_settings()
        self._engine.intercept_rules = settings.get("intercept_rules", [])
        self._engine.match_replace_rules = settings.get("match_replace", [])
        
        self._logger.append(
            "info",
            f"Intercept: requests={'ON' if req else 'OFF'}, responses={'ON' if resp else 'OFF'}"
        )

    def _on_proxy_settings_changed(self, settings: dict):
        self._engine.intercept_rules = settings.get("intercept_rules", [])
        self._engine.match_replace_rules = settings.get("match_replace", [])
        self._engine.upstream_proxy = settings.get("upstream_proxy")
        # Update in engine immediately if running
        self._logger.append("info", "Proxy settings updated.")

    def _on_scope_updated(self, rules: list):
        self._engine.scope_rules = rules
        self._logger.append("info", f"Target scope updated: {len(rules)} rules.")

    # ── Cross-tab routing ─────────────────────────────────────────────────

    def _send_to_repeater(self, entry):
        self._repeater_tab.load_from_flow(entry)
        self._main_tabs.setCurrentWidget(self._repeater_tab)
        self._logger.append("info", f"Sent to Repeater: {entry.method} {entry.url}")

    def _send_to_intruder(self, entry):
        self._intruder_tab.load_from_flow(entry)
        self._main_tabs.setCurrentWidget(self._intruder_tab)
        self._logger.append("info", f"Sent to Intruder: {entry.method} {entry.url}")

    # ── Menu actions ──────────────────────────────────────────────────────

    def _new_session(self):
        reply = QMessageBox.question(
            self, "New Session",
            "Clear all captured traffic and start fresh?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._engine.clear_flows()
            self._proxy_tab.clear_history()
            self._target_tab._site_map.clear()
            self._request_count = 0
            self._intercepted_count = 0
            self._dashboard.update_stats(requests=0, intercepted=0, hosts=0)
            self._banner_req_count.setText("0 requests")
            self._status_reqs.setText("Requests: 0")
            self._logger.append("info", "Session cleared.")

    def _export_log(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Log", "proxy_log.json", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        flows = self._engine.get_all_flows()
        import json
        data = []
        for f in flows:
            data.append({
                "number": f.number,
                "method": f.method,
                "url": f.url,
                "status": f.status_code,
                "length": f.response_length,
                "timing_ms": f.duration_ms,
                "timestamp": f.timestamp,
            })
        with open(path, "w") as fp:
            json.dump(data, fp, indent=2)
        self._logger.append("info", f"Exported {len(data)} flows to {path}")
        QMessageBox.information(self, "Export", f"Exported {len(data)} requests to:\n{path}")

    def _show_cert_info(self):
        import os
        cert_dir = os.path.expanduser("~/.mitmproxy")
        cert_path = os.path.join(cert_dir, "mitmproxy-ca-cert.pem")
        msg = (
            f"<b>mitmproxy CA Certificate</b><br><br>"
            f"Location: <code>{cert_path}</code><br><br>"
            f"To intercept HTTPS traffic:<br>"
            f"1. Start the proxy<br>"
            f"2. Navigate to <b>http://mitm.it</b> in your browser<br>"
            f"3. Download and install the certificate for your browser/OS<br><br>"
            f"The certificate is auto-generated on first use."
        )
        QMessageBox.information(self, "CA Certificate", msg)

    def _on_send_to_decoder(self, text: str):
        """Handle 'Send to Decoder' from any editor."""
        # Find index of Decoder tab
        idx = -1
        for i in range(self._main_tabs.count()):
            if self._main_tabs.tabText(i) == "Decoder":
                idx = i
                break
        
        if idx != -1:
            self._main_tabs.setCurrentIndex(idx)
            self._decoder_tab.set_content(text)

    def _show_about(self):
        QMessageBox.about(
            self, "About Hespia",
            "<b>Hespia</b> v1.0.0<br><br>"
            "A HESPIA Suite-inspired web proxy tool.<br>"
            "Built with Python, mitmproxy, and PySide6.<br><br>"
            "Features:<br>"
            "• HTTP/HTTPS Intercept<br>"
            "• HTTP History<br>"
            "• Repeater<br>"
            "• Intruder<br>"
            "• Decoder/Encoder<br>"
            "• Comparer<br>"
            "• Target/Scope<br>"
            "• Match & Replace<br>"
        )

    def closeEvent(self, event):
        if self._is_running:
            reply = QMessageBox.question(
                self, "Quit",
                "The proxy is running. Stop it and quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self._engine.stop()
        event.accept()
