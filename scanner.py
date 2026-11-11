"""TCP port scanning engine for authorized security testing only."""
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class ScanResult:
    host: str
    ip: str
    port: int
    status: str
    service: str
    response_ms: Optional[float] = None

def resolve_target(target: str) -> str:
    target = target.strip()
    if not target:
        raise ValueError("Enter an IP address or hostname.")
    try:
        return socket.gethostbyname(target)
    except socket.gaierror as exc:
        raise ValueError("Could not resolve that hostname.") from exc

def scan_one(host: str, ip: str, port: int, timeout: float, cancel_event: threading.Event) -> ScanResult:
    if cancel_event.is_set():
        return ScanResult(host, ip, port, "cancelled", "")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    started = time.perf_counter()
    try:
        code = sock.connect_ex((ip, port))
        elapsed = (time.perf_counter() - started) * 1000
        try:
            service = socket.getservbyport(port, "tcp")
        except OSError:
            service = "unknown"
        if code == 0:
            status = "open"
        elif code in (111, 10061, 61, 113):
            status = "closed"
        else:
            status = "filtered / no response"
        return ScanResult(host, ip, port, status, service, elapsed)
    except socket.timeout:
        return ScanResult(host, ip, port, "filtered / timeout", "")
    except OSError:
        return ScanResult(host, ip, port, "unreachable / error", "")
    finally:
        sock.close()

def scan_ports(target: str, start_port: int, end_port: int, timeout: float = 0.8,
               workers: int = 64, cancel_event: Optional[threading.Event] = None,
               on_result: Optional[Callable[[ScanResult], None]] = None,
               on_progress: Optional[Callable[[int, int], None]] = None):
    """Yield TCP connection results. Only scan systems you are authorized to test."""
    if cancel_event is None:
        cancel_event = threading.Event()
    if not (1 <= start_port <= 65535 and 1 <= end_port <= 65535):
        raise ValueError("Ports must be between 1 and 65535.")
    if start_port > end_port:
        raise ValueError("Start port must not exceed end port.")
    if not (0.1 <= timeout <= 10):
        raise ValueError("Timeout must be between 0.1 and 10 seconds.")
    if not (1 <= workers <= 200):
        raise ValueError("Workers must be between 1 and 200.")
    ip = resolve_target(target)
    ports = range(start_port, end_port + 1)
    total, completed = len(ports), 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(scan_one, target, ip, p, timeout, cancel_event) for p in ports]
        for future in as_completed(futures):
            if cancel_event.is_set():
                for pending in futures:
                    pending.cancel()
            try:
                result = future.result()
            except Exception:
                continue
            completed += 1
            if on_result:
                on_result(result)
            if on_progress:
                on_progress(completed, total)
            yield result
            if cancel_event.is_set():
                break
