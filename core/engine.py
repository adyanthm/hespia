"""
Core Proxy Engine using mitmproxy.
Runs in a background thread with asyncio event loop.
Communicates with the PySide6 UI via Qt signals.
"""
import asyncio
import threading
import time
import json
import uuid
import socket
import traceback
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from PySide6.QtCore import QObject, Signal


# ─── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class FlowEntry:
    """Represents a captured HTTP flow."""
    id: str
    number: int
    method: str
    scheme: str
    host: str
    port: int
    path: str
    url: str
    params: str
    status_code: Optional[int]
    status_reason: str
    content_type: str
    request_length: int
    response_length: int
    duration_ms: float
    timestamp: float
    is_https: bool
    # Raw bytes for display
    request_headers_raw: Dict[str, str]
    request_body: bytes
    response_headers_raw: Dict[str, str]
    response_body: bytes
    # UI Metadata
    edited: bool = False
    highlighted: str = ""
    comment: str = ""
    tags: List[str] = field(default_factory=list)


def serialize_request(flow) -> str:
    """Convert mitmproxy request to raw HTTP text."""
    req = flow.request
    # Build the request line
    path = req.path if req.path else "/"
    lines = [f"{req.method} {path} HTTP/1.1"]
    for k, v in req.headers.items():
        lines.append(f"{k}: {v}")
    lines.append("")
    body = req.content or b""
    try:
        lines.append(body.decode("utf-8", errors="replace"))
    except Exception:
        lines.append("<binary content>")
    return "\r\n".join(lines)


def serialize_response(flow) -> str:
    """Convert mitmproxy response to raw HTTP text."""
    if not flow.response:
        return ""
    resp = flow.response
    lines = [f"HTTP/1.1 {resp.status_code} {resp.reason or ''}"]
    for k, v in resp.headers.items():
        lines.append(f"{k}: {v}")
    lines.append("")
    body = resp.content or b""
    try:
        lines.append(body.decode("utf-8", errors="replace"))
    except Exception:
        lines.append("<binary content>")
    return "\r\n".join(lines)


def apply_request_modifications(flow, raw_text: str):
    """Apply edited raw HTTP text back to mitmproxy flow request."""
    try:
        # Normalize line endings
        raw_text = raw_text.replace("\r\n", "\n")
        
        # Split into header and body strictly at the first double newline
        if "\n\n" in raw_text:
            header_part, body = raw_text.split("\n\n", 1)
        else:
            header_part = raw_text
            body = ""
            
        lines = header_part.split("\n")
        if not lines:
            return

        # Parse request line
        first = lines[0].strip()
        parts = first.split(" ", 2)
        if len(parts) >= 2:
            flow.request.method = parts[0]
            flow.request.path = parts[1]

        # Parse headers
        from mitmproxy.http import Headers
        new_headers = Headers()
        for i in range(1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                new_headers[k.strip()] = v.strip()
        
        flow.request.headers = new_headers
        
        # Apply body and update Content-Length
        content = body.encode("utf-8", errors="replace")
        flow.request.content = content
        
        # CRITICAL: Update Content-Length header to match new body size
        if "Content-Length" in flow.request.headers:
            flow.request.headers["Content-Length"] = str(len(content))
            
    except Exception as e:
        print(f"[Engine] Failed to apply request modifications: {e}")


def apply_response_modifications(flow, raw_text: str):
    """Apply edited raw HTTP text back to mitmproxy flow response."""
    try:
        if not flow.response:
            return
            
        raw_text = raw_text.replace("\r\n", "\n")
        if "\n\n" in raw_text:
            header_part, body = raw_text.split("\n\n", 1)
        else:
            header_part = raw_text
            body = ""
            
        lines = header_part.split("\n")
        if not lines:
            return

        # Parse status line
        first = lines[0].strip()
        parts = first.split(" ", 2)
        if len(parts) >= 2:
            try:
                flow.response.status_code = int(parts[1])
            except ValueError:
                pass
        if len(parts) >= 3:
            flow.response.reason = parts[2]

        # Parse headers
        from mitmproxy.http import Headers
        new_headers = Headers()
        for i in range(1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                new_headers[k.strip()] = v.strip()
        
        flow.response.headers = new_headers
        
        # Apply body and update Content-Length
        content = body.encode("utf-8", errors="replace")
        flow.response.content = content
        
        if "Content-Length" in flow.response.headers:
            flow.response.headers["Content-Length"] = str(len(content))
            
    except Exception as e:
        print(f"[Engine] Failed to apply response modifications: {e}")


# ─── Qt Signal Bridge ─────────────────────────────────────────────────────────

class ProxySignals(QObject):
    """Thread-safe bridge from mitmproxy thread to Qt UI thread."""
    # New flow added (request received)
    flow_added = Signal(object)          # FlowEntry
    # Flow updated (response received)
    flow_updated = Signal(object)        # FlowEntry
    # Request intercepted - paused
    request_intercepted = Signal(str, str)  # flow_id, raw_request_text
    # Response intercepted - paused
    response_intercepted = Signal(str, str, str)  # flow_id, raw_request, raw_response
    # Proxy lifecycle
    proxy_started = Signal(str, int)     # host, port
    proxy_stopped = Signal()
    proxy_error = Signal(str)            # error message
    # Log
    log_message = Signal(str, str)       # level (info/warn/error), message
    # Flow count update
    flow_count = Signal(int)


# ─── mitmproxy Addon ─────────────────────────────────────────────────────────

class ProxyAddon:
    """
    mitmproxy addon that hooks into request/response lifecycle.
    """
    def __init__(self, signals: ProxySignals, engine: 'ProxyEngine'):
        self.signals = signals
        self.engine = engine
        self._counter = 0
        self._flows: Dict[str, Any] = {}       # flow_id_str -> mitmproxy flow
        self._flow_entries: Dict[str, FlowEntry] = {}
        self._start_times: Dict[str, float] = {}

    def request(self, flow):
        """Called when a full client request has been received."""
        self._counter += 1
        fid = flow.id
        self._flows[fid] = flow
        self._start_times[fid] = time.time()

        # Parse query params
        try:
            params = "&".join(f"{k}={v}" for k, v in flow.request.query)
        except Exception:
            params = ""

        entry = FlowEntry(
            id=fid,
            number=self._counter,
            method=flow.request.method,
            scheme=flow.request.scheme,
            host=flow.request.pretty_host,
            port=flow.request.port,
            path=flow.request.path,
            url=flow.request.pretty_url,
            params=params,
            status_code=None,
            status_reason="",
            content_type="",
            request_length=len(flow.request.content or b""),
            response_length=0,
            duration_ms=0.0,
            timestamp=time.time(),
            is_https=flow.request.scheme == "https",
            request_headers_raw=dict(flow.request.headers),
            request_body=flow.request.content or b"",
            response_headers_raw={},
            response_body=b"",
        )
        self._flow_entries[fid] = entry
        self.signals.flow_added.emit(entry)
        self.signals.flow_count.emit(self._counter)

        # Check intercept
        if self.engine.intercept_requests and self.engine._should_intercept(flow):
            raw = serialize_request(flow)
            flow.intercept()
            self.signals.request_intercepted.emit(fid, raw)
            self.signals.log_message.emit("info", f"[Intercept] Paused request: {flow.request.method} {flow.request.pretty_url}")

        # Apply match & replace rules
        self.engine._apply_match_replace_request(flow)

    def response(self, flow):
        """Called when a full server response has been received."""
        fid = flow.id
        entry = self._flow_entries.get(fid)
        if entry:
            start = self._start_times.get(fid, time.time())
            entry.duration_ms = (time.time() - start) * 1000
            entry.status_code = flow.response.status_code
            entry.status_reason = flow.response.reason or ""
            ct = flow.response.headers.get("content-type", "")
            entry.content_type = ct.split(";")[0].strip()
            entry.response_length = len(flow.response.content or b"")
            entry.response_headers_raw = dict(flow.response.headers)
            entry.response_body = flow.response.content or b""
            self.signals.flow_updated.emit(entry)

        # Check response intercept
        if self.engine.intercept_responses and self.engine._should_intercept(flow):
            raw_req = serialize_request(flow)
            raw_resp = serialize_response(flow)
            flow.intercept()
            self.signals.response_intercepted.emit(fid, raw_req, raw_resp)
            self.signals.log_message.emit("info", f"[Intercept] Paused response: {flow.response.status_code} {flow.request.pretty_url}")

        # Apply match & replace rules to response
        self.engine._apply_match_replace_response(flow)

    def error(self, flow):
        """Called when flow has an error."""
        fid = flow.id
        entry = self._flow_entries.get(fid)
        if entry:
            entry.status_code = -1
            entry.status_reason = str(flow.error) if flow.error else "Error"
            self.signals.flow_updated.emit(entry)
        
        # If it was intercepted, resume it to avoid stuck connections
        if flow.intercepted:
            self.signals.log_message.emit("warn", f"Resuming errored flow: {fid[:8]}")
            if self._loop:
                self._loop.call_soon_threadsafe(flow.resume)

    def tls_start_client(self, tls_start):
        pass  # handled by mitmproxy internally


# ─── Proxy Engine ─────────────────────────────────────────────────────────────

class ProxyEngine(QObject):
    """
    Manages the mitmproxy DumpMaster running in a background thread.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = ProxySignals()
        self._master = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._addon: Optional[ProxyAddon] = None
        self._running = False

        # Intercept mode (default to both)
        self.intercept_requests = False
        self.intercept_responses = False
        self.listen_host = "127.0.0.1"
        self.listen_port = 8080

        # Advanced Intercept Rules (AND logic)
        # Each rule: {"enabled": bool, "type": str, "match": str, "invert": bool}
        self.intercept_rules: List[Dict] = []

        # Scope: list of dicts {"enabled": bool, "protocol": str, "host": str, "port": str, "path": str}
        self.scope_rules: List[Dict] = []

        # Match & Replace rules: list of dicts with enabled, match_type, match, replace
        # match_type: request_header, response_header, request_body, response_body, url
        self.match_replace_rules: List[Dict] = []

        # SSL strip / upstream proxy
        self.upstream_proxy: Optional[str] = None  # "http://host:port"

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def start(self, host: str = "127.0.0.1", port: int = 8080):
        """Start the proxy server with automatic port incrementing."""
        if self._running:
            self.signals.log_message.emit("warn", f"Proxy already running on {self.listen_host}:{self.listen_port}")
            return

        def is_port_available(h, p):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((h, p))
                return True
            except Exception:
                return False

        # Port auto-increment logic
        current_port = port
        max_attempts = 10
        found_port = False
        
        for _ in range(max_attempts):
            if is_port_available(host, current_port):
                found_port = True
                port = current_port
                break
            current_port += 1

        if not found_port:
            self.signals.proxy_error.emit(f"Could not bind to any port in range {port}-{current_port-1}")
            return

        self.listen_host = host
        self.listen_port = port
        self._thread = threading.Thread(
            target=self._run_proxy,
            args=(host, port),
            daemon=True,
            name="ProxyThread"
        )
        self._thread.start()

    def stop(self):
        """Stop the proxy server."""
        if self._master and self._loop:
            self._loop.call_soon_threadsafe(self._master.shutdown)
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def _run_proxy(self, host: str, port: int):
        """Target for proxy background thread."""
        try:
            from mitmproxy.options import Options
            from mitmproxy.tools.dump import DumpMaster

            # Create a new event loop for this thread to avoid 'no running event loop' errors
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            opts_kwargs = dict(
                listen_host=host,
                listen_port=port,
                ssl_insecure=True,
                confdir=self._get_conf_dir(),
            )
            if self.upstream_proxy:
                opts_kwargs["mode"] = [f"upstream:{self.upstream_proxy}"]

            opts = Options(**opts_kwargs)

            # mitmproxy 10+ requires being initialized inside a running loop context
            # because its constructor calls asyncio.get_running_loop().
            async def run_mitm():
                self._master = DumpMaster(opts, with_termlog=False, with_dumper=False)
                self._addon = ProxyAddon(self.signals, self)
                self._master.addons.add(self._addon)
                
                self._running = True
                self.signals.proxy_started.emit(host, port)
                self.signals.log_message.emit("info", f"[Proxy] Listening on {host}:{port}")
                
                await self._master.run()

            # Run the inner async function
            self._loop.run_until_complete(run_mitm())

        except Exception as e:
            err_trace = traceback.format_exc()
            self.signals.proxy_error.emit(f"{str(e)}\n{err_trace}")
            self._running = False
        finally:
            self._running = False
            self.signals.proxy_stopped.emit()

    def _get_conf_dir(self) -> str:
        import os
        conf = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".mitmproxy")
        os.makedirs(conf, exist_ok=True)
        return conf

    # ── Intercept Control ──────────────────────────────────────────────────

    def set_intercept_requests(self, enabled: bool):
        self.intercept_requests = enabled

    def set_intercept_responses(self, enabled: bool):
        self.intercept_responses = enabled

    def forward_request(self, flow_id: str, modified_raw: Optional[str] = None):
        """Forward a paused request (optionally modified)."""
        if not self._addon:
            return
        flow = self._addon._flows.get(flow_id)
        if not flow:
            return
        if modified_raw:
            apply_request_modifications(flow, modified_raw)
            entry = self._addon._flow_entries.get(flow_id)
            if entry:
                entry.edited = True
        if self._loop:
            self._loop.call_soon_threadsafe(self._safe_resume, flow)
        self.signals.log_message.emit("info", f"[Intercept] Forwarded: {flow_id[:8]} ({flow.request.method} {flow.request.path})")

    def _safe_resume(self, flow):
        """Resume flow safely within the mitmproxy loop."""
        try:
            if flow.intercepted:
                flow.resume()
        except Exception as e:
            print(f"[Engine] Exception during flow.resume: {e}")

    def forward_response(self, flow_id: str, modified_raw: Optional[str] = None):
        """Forward a paused response (optionally modified)."""
        if not self._addon:
            return
        flow = self._addon._flows.get(flow_id)
        if not flow:
            return
        if modified_raw:
            apply_response_modifications(flow, modified_raw)
            entry = self._addon._flow_entries.get(flow_id)
            if entry:
                entry.edited = True
        if self._loop:
            self._loop.call_soon_threadsafe(flow.resume)

    def drop_flow(self, flow_id: str):
        """Drop/kill an intercepted flow."""
        if not self._addon:
            return
        flow = self._addon._flows.get(flow_id)
        if flow and self._loop:
            self._loop.call_soon_threadsafe(self._do_kill, flow)
        self.signals.log_message.emit("warn", f"[Intercept] Dropped: {flow_id[:8]}")

    def _do_kill(self, flow):
        flow.kill()

    # ── Scope ──────────────────────────────────────────────────────────────

    def _should_intercept(self, flow) -> bool:
        """
        Rugged interception check.
        Logic: Match ALL enabled intercept_rules (AND logic).
        If no rules enabled, intercept everything.
        """
        # If no rules at all, capture everything
        enabled_rules = [r for r in self.intercept_rules if r.get("enabled", True)]
        if not enabled_rules:
            return True
        
        import re
        for rule in enabled_rules:
            match_type = rule.get("type", "").lower()
            match_val = rule.get("match", "")
            if not match_val:
                continue
                
            matched = False
            try:
                if "url" in match_type:
                    matched = bool(re.search(match_val, flow.request.pretty_url))
                elif "method" in match_type:
                    matched = bool(re.search(match_val, flow.request.method))
                elif "status" in match_type:
                    if flow.response:
                        matched = bool(re.search(match_val, str(flow.response.status_code)))
                    else:
                        # If we are intercepting a request, status code rule can't match unless we want it to skip
                        # For requests, we usually skip status code rules or assume they match
                        matched = True 
                elif "host" in match_type:
                    matched = bool(re.search(match_val, flow.request.pretty_host))
            except Exception:
                matched = True # Default to intercept on regex error
                
            if not matched:
                return False # AND logic: fail if any enabled rule doesn't match
                
        return True

    # ── Match & Replace ────────────────────────────────────────────────────

    def _apply_match_replace_request(self, flow):
        """Apply match & replace rules to a request."""
        import re
        for rule in self.match_replace_rules:
            if not rule.get("enabled", True):
                continue
            match_type = rule.get("type", "")
            match_str = rule.get("match", "")
            replace_str = rule.get("replace", "")
            if not match_str:
                continue
            try:
                if match_type == "url":
                    new_url = re.sub(match_str, replace_str, flow.request.pretty_url)
                    # Apply path part
                    flow.request.path = new_url.split(flow.request.pretty_host, 1)[-1] or "/"
                elif match_type == "request_header":
                    for k in list(flow.request.headers.keys()):
                        flow.request.headers[k] = re.sub(match_str, replace_str, flow.request.headers[k])
                elif match_type == "request_body":
                    body = (flow.request.content or b"").decode("utf-8", errors="replace")
                    body = re.sub(match_str, replace_str, body)
                    flow.request.content = body.encode("utf-8")
            except Exception:
                pass

    def _apply_match_replace_response(self, flow):
        """Apply match & replace rules to a response."""
        import re
        if not flow.response:
            return
        for rule in self.match_replace_rules:
            if not rule.get("enabled", True):
                continue
            match_type = rule.get("type", "")
            match_str = rule.get("match", "")
            replace_str = rule.get("replace", "")
            if not match_str:
                continue
            try:
                if match_type == "response_header":
                    for k in list(flow.response.headers.keys()):
                        flow.response.headers[k] = re.sub(match_str, replace_str, flow.response.headers[k])
                elif match_type == "response_body":
                    body = (flow.response.content or b"").decode("utf-8", errors="replace")
                    body = re.sub(match_str, replace_str, body)
                    flow.response.content = body.encode("utf-8")
            except Exception:
                pass

    # ── Manual Repeater Request ────────────────────────────────────────────

    def send_raw_request(self, host: str, port: int, is_https: bool, raw: str, timeout: int = 10) -> str:
        """
        Send a raw HTTP request and return the raw response.
        """
        import socket
        import ssl as ssl_module

        try:
            lines = raw.replace("\r\n", "\n").split("\n")
            # Parse request line
            first = lines[0].strip()
            parts = first.split(" ", 2)
            method = parts[0] if parts else "GET"
            path = parts[1] if len(parts) > 1 else "/"

            # Parse headers
            headers = {}
            i = 1
            while i < len(lines) and lines[i].strip():
                if ":" in lines[i]:
                    k, v = lines[i].split(":", 1)
                    headers[k.strip()] = v.strip()
                i += 1

            # Body - Split by the blank line after headers
            parts = raw.replace("\r\n", "\n").split("\n\n", 1)
            body_bytes = b""
            if len(parts) > 1:
                # Use raw parts if possible to avoid split/join issues
                body_bytes = parts[1].encode("utf-8", errors="replace")

            # Build raw HTTP
            req_lines = [f"{method} {path} HTTP/1.1"]
            for k, v in headers.items():
                # Avoid duplicate Content-Length if we are calculating it
                if k.lower() == "content-length":
                    continue
                req_lines.append(f"{k}: {v}")
            
            if body_bytes:
                req_lines.append(f"Content-Length: {len(body_bytes)}")
            
            req_lines.append("")
            header_bytes = ("\r\n".join(req_lines) + "\r\n").encode("ascii", errors="replace")
            
            raw_request = header_bytes + body_bytes

            # Open socket
            sock = socket.create_connection((host, port), timeout=timeout)
            if is_https:
                ctx = ssl_module.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl_module.CERT_NONE
                sock = ctx.wrap_socket(sock, server_hostname=host)

            sock.sendall(raw_request)

            # Read response
            response_data = b""
            content_length = -1
            header_done = False
            
            while True:
                try:
                    chunk = sock.recv(32768)
                    if not chunk:
                        break
                    response_data += chunk
                    
                    if not header_done and b"\r\n\r\n" in response_data:
                        header_done = True
                        header_part = response_data.split(b"\r\n\r\n")[0].decode("ascii", errors="replace").lower()
                        import re
                        match = re.search(r"content-length:\s*(\d+)", header_part)
                        if match:
                            content_length = int(match.group(1))
                    
                    if header_done and content_length >= 0:
                        body_part = response_data.split(b"\r\n\r\n", 1)[1]
                        if len(body_part) >= content_length:
                            break # Finished reading body
                except socket.timeout:
                    break

            sock.close()
            return response_data.decode("utf-8", errors="replace")

        except Exception as e:
            return f"Error: {e}"

    # ── Flow Management ────────────────────────────────────────────────────

    def get_all_flows(self) -> List[FlowEntry]:
        if not self._addon:
            return []
        return list(self._addon._flow_entries.values())

    def clear_flows(self):
        if self._addon:
            self._addon._flows.clear()
            self._addon._flow_entries.clear()
            self._addon._start_times.clear()
            self._addon._counter = 0
            self.signals.flow_count.emit(0)

    def get_flow_entry(self, flow_id: str) -> Optional[FlowEntry]:
        if not self._addon:
            return None
        return self._addon._flow_entries.get(flow_id)
