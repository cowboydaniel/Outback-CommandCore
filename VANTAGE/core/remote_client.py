"""SSH-based remote metrics client."""
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Sent via stdin to `python3` on the remote host.
# Tries psutil first, falls back to /proc parsing for bare Linux servers.
_METRICS_SCRIPT = """\
import json, time, sys

def _proc_metrics():
    import os
    # CPU: two /proc/stat samples 100ms apart
    def _stat():
        with open('/proc/stat') as f:
            parts = f.readline().split()
        vals = [int(x) for x in parts[1:]]
        return sum(vals), vals[3]
    t1, i1 = _stat()
    time.sleep(0.1)
    t2, i2 = _stat()
    cpu = 100.0 * (1 - (i2-i1) / (t2-t1)) if t2 != t1 else 0.0
    # Memory
    mem = {}
    with open('/proc/meminfo') as f:
        for line in f:
            k, v = line.split(':')
            mem[k.strip()] = int(v.split()[0]) * 1024
    mem_total = mem.get('MemTotal', 0)
    mem_avail = mem.get('MemAvailable', mem.get('MemFree', 0))
    mem_used  = mem_total - mem_avail
    mem_pct   = 100.0 * mem_used / mem_total if mem_total else 0.0
    # Disk
    st = os.statvfs('/')
    disk_total = st.f_blocks * st.f_frsize
    disk_free  = st.f_bfree  * st.f_frsize
    disk_used  = disk_total - disk_free
    disk_pct   = 100.0 * disk_used / disk_total if disk_total else 0.0
    # Network
    net_sent = net_recv = 0
    with open('/proc/net/dev') as f:
        for line in f:
            if ':' in line:
                fields = line.split(':')[1].split()
                net_recv += int(fields[0])
                net_sent += int(fields[8])
    # Uptime
    with open('/proc/uptime') as f:
        uptime_seconds = float(f.read().split()[0])
    # Temperature (Raspberry Pi and other ARM boards)
    cpu_temp = None
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            cpu_temp = int(f.read().strip()) / 1000.0
    except Exception:
        pass
    return dict(cpu_percent=cpu, memory_percent=mem_pct, memory_used=mem_used,
                memory_total=mem_total, disk_percent=disk_pct, disk_used=disk_used,
                disk_total=disk_total, net_bytes_sent=net_sent, net_bytes_recv=net_recv,
                uptime_seconds=uptime_seconds, cpu_temp=cpu_temp,
                timestamp=time.time(), ok=True, source='proc')

try:
    import psutil
    cpu  = psutil.cpu_percent(interval=0.1)
    mem  = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net  = psutil.net_io_counters()
    uptime_seconds = time.time() - psutil.boot_time()
    # Temperature
    cpu_temp = None
    try:
        temps = psutil.sensors_temperatures()
        vals = [e.current for n, es in temps.items()
                if any(k in n.lower() for k in ('core','cpu','k10temp','coretemp','cpu_thermal'))
                for e in es if e.current and e.current > 0]
        if vals:
            cpu_temp = sum(vals) / len(vals)
    except Exception:
        pass
    # Fallback to thermal_zone0 for boards where psutil can't read sensors
    if cpu_temp is None:
        try:
            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                cpu_temp = int(f.read().strip()) / 1000.0
        except Exception:
            pass
    print(json.dumps(dict(
        cpu_percent=cpu, memory_percent=mem.percent,
        memory_used=mem.used, memory_total=mem.total,
        disk_percent=disk.percent, disk_used=disk.used, disk_total=disk.total,
        net_bytes_sent=net.bytes_sent, net_bytes_recv=net.bytes_recv,
        uptime_seconds=uptime_seconds, cpu_temp=cpu_temp,
        timestamp=time.time(), ok=True, source='psutil'
    )))
except Exception:
    try:
        print(json.dumps(_proc_metrics()))
    except Exception as e:
        print(json.dumps({'ok': False, 'error': str(e)}))
"""


@dataclass
class RemoteMetrics:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used: int = 0
    memory_total: int = 0
    disk_percent: float = 0.0
    disk_used: int = 0
    disk_total: int = 0
    net_bytes_sent: int = 0
    net_bytes_recv: int = 0
    uptime_seconds: float = 0.0
    cpu_temp: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


class RemoteClient:
    """Manages one SSH connection to a remote server and fetches metrics."""

    def __init__(self, host: str, port: int = 22, username: str = "",
                 password: Optional[str] = None, key_path: Optional[str] = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self._client = None
        self._lock = threading.Lock()
        self._connected = False

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        try:
            import paramiko
        except ImportError:
            logger.error("paramiko is not installed — cannot connect to remote servers")
            return False

        with self._lock:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                kwargs: dict = dict(hostname=self.host, port=self.port,
                                    username=self.username, timeout=10)
                if self.key_path:
                    kwargs['key_filename'] = self.key_path
                elif self.password:
                    kwargs['password'] = self.password
                    kwargs['look_for_keys'] = False
                client.connect(**kwargs)
                if self._client:
                    self._client.close()
                self._client = client
                self._connected = True
                logger.info("Connected to %s:%d", self.host, self.port)
                return True
            except Exception as exc:
                logger.warning("Cannot connect to %s:%d — %s", self.host, self.port, exc)
                self._connected = False
                return False

    def disconnect(self):
        with self._lock:
            if self._client:
                try:
                    self._client.close()
                except Exception:
                    pass
                self._client = None
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._client is not None

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def fetch_metrics(self) -> Optional[RemoteMetrics]:
        """Run the metrics script on the remote host and return parsed results."""
        if not self.is_connected:
            if not self.connect():
                return None

        with self._lock:
            try:
                stdin, stdout, _ = self._client.exec_command("python3", timeout=8)
                stdin.write(_METRICS_SCRIPT)
                stdin.channel.shutdown_write()
                raw = stdout.read().decode().strip()
                data = json.loads(raw)
                if not data.get('ok'):
                    logger.warning("Remote script error on %s: %s", self.host, data.get('error'))
                    return None
                return RemoteMetrics(
                    cpu_percent=float(data['cpu_percent']),
                    memory_percent=float(data['memory_percent']),
                    memory_used=int(data['memory_used']),
                    memory_total=int(data['memory_total']),
                    disk_percent=float(data['disk_percent']),
                    disk_used=int(data['disk_used']),
                    disk_total=int(data['disk_total']),
                    net_bytes_sent=int(data['net_bytes_sent']),
                    net_bytes_recv=int(data['net_bytes_recv']),
                    uptime_seconds=float(data.get('uptime_seconds', 0)),
                    cpu_temp=float(data['cpu_temp']) if data.get('cpu_temp') is not None else None,
                    timestamp=float(data['timestamp']),
                )
            except Exception as exc:
                logger.warning("Metrics fetch failed for %s: %s", self.host, exc)
                self._connected = False
                return None

    def test_connection(self) -> tuple[bool, str]:
        """Return (success, message). Disconnects after a successful test."""
        ok = self.connect()
        if ok:
            self.disconnect()
            return True, f"Successfully connected to {self.host}:{self.port}"
        return False, f"Could not connect to {self.host}:{self.port}"
