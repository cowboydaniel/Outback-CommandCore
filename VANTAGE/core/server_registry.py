"""Shared server registry — persists to disk and emits Qt signals on change."""
import json
import logging
import os
from dataclasses import dataclass, asdict
from typing import Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

_REGISTRY_FILE = os.path.join(os.path.expanduser("~"), ".vantage", "servers.json")


@dataclass
class ServerEntry:
    server_id: str          # stable key, e.g. "host:port"
    display_name: str       # shown in dropdown and table
    host: str
    port: int = 22
    username: str = ""
    auth_type: str = "password"   # "password" | "key"
    password: str = ""
    key_path: str = ""
    status: str = "unknown"       # "online" | "offline" | "unknown"
    last_seen: str = "Never"


class ServerRegistry(QObject):
    """
    Singleton QObject that owns the list of remote servers.
    Persists entries to ~/.vantage/servers.json.
    """

    servers_changed = Signal()

    _instance: Optional["ServerRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        super().__init__()
        self._initialized = True
        self._servers: dict[str, ServerEntry] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        try:
            if os.path.exists(_REGISTRY_FILE):
                with open(_REGISTRY_FILE) as f:
                    for raw in json.load(f):
                        entry = ServerEntry(**raw)
                        entry.status = "unknown"   # reset on load; will re-check
                        self._servers[entry.server_id] = entry
        except Exception as exc:
            logger.warning("Could not load server registry: %s", exc)

    def _save(self):
        try:
            os.makedirs(os.path.dirname(_REGISTRY_FILE), exist_ok=True)
            with open(_REGISTRY_FILE, "w") as f:
                json.dump([asdict(s) for s in self._servers.values()], f, indent=2)
        except Exception as exc:
            logger.warning("Could not save server registry: %s", exc)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add_server(self, entry: ServerEntry):
        self._servers[entry.server_id] = entry
        self._save()
        self.servers_changed.emit()

    def remove_server(self, server_id: str):
        self._servers.pop(server_id, None)
        self._save()
        self.servers_changed.emit()

    def update_status(self, server_id: str, status: str, last_seen: str = ""):
        if server_id in self._servers:
            self._servers[server_id].status = status
            if last_seen:
                self._servers[server_id].last_seen = last_seen
            self._save()
            self.servers_changed.emit()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def all_servers(self) -> list[ServerEntry]:
        return list(self._servers.values())

    def get(self, server_id: str) -> Optional[ServerEntry]:
        return self._servers.get(server_id)
