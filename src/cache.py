\
from __future__ import annotations
import json, os, time
from typing import Optional, Dict, Any

class JsonCache:
    def __init__(self, path: str, ttl_days: int = 7):
        self.path = path
        # ttl_days = 0 significa cache indefinido para metadatos IA 🤖
        self.ttl = ttl_days * 86400 if ttl_days > 0 else None
        self._load()

    def _load(self):
        self.data = {}
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    self.data = json.load(fh)
            except Exception:
                self.data = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False)
        os.replace(tmp, self.path)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        entry = self.data.get(key)
        if not entry:
            return None
        # Skip TTL check si cache indefinido (ttl=None)
        if self.ttl is not None and time.time() - entry.get("_ts", 0) > self.ttl:
            # expired
            self.data.pop(key, None)
            return None
        return entry.get("value")

    def set(self, key: str, value: Dict[str, Any]):
        self.data[key] = {"value": value, "_ts": time.time()}
        self._save()
