\
from __future__ import annotations
import json, time, os
from typing import Dict, Any

class Metrics:
    def __init__(self):
        self.t0 = time.time()
        self.data = {"stages": {}, "counters": {}}

    def start(self, name: str):
        self.data["stages"].setdefault(name, {"t": 0.0, "count": 0})
        self.data["stages"][name]["_t0"] = time.time()

    def end(self, name: str, inc: int = 0):
        st = self.data["stages"].get(name, {})
        if "_t0" in st:
            st["t"] += time.time() - st["_t0"]
            st["count"] += inc
            del st["_t0"]
        self.data["stages"][name] = st

    def inc(self, key: str, by: int = 1):
        self.data["counters"][key] = self.data["counters"].get(key, 0) + by

    def dump(self, outdir: str):
        os.makedirs(outdir, exist_ok=True)
        self.data["total_seconds"] = time.time() - self.t0
        with open(os.path.join(outdir, "metrics.json"), "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, ensure_ascii=False, indent=2)
