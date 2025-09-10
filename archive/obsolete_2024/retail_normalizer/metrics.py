from __future__ import annotations
import time, json, os
from typing import Dict, Any

class Metrics:
    def __init__(self):
        self.t0 = time.time()
        self.counts = {
            "products_processed": 0,
            "by_category": {},
            "cache_hits": 0,
            "cache_misses": 0,
            "llm_tokens_in": 0,
            "llm_tokens_out": 0,
            "llm_cost_usd": 0.0,
            "llm_mini_calls": 0,
            "llm_full_calls": 0,
            "matches_found": 0,
            "suggested_categories": 0
        }
        self.timings = {}

    def inc(self, key: str, n: int=1):
        self.counts[key] = self.counts.get(key,0) + n

    def inc_cat(self, cat: str):
        self.counts["by_category"][cat] = self.counts["by_category"].get(cat,0)+1

    def add_llm(self, tokens_in: int, tokens_out: int, cost: float, mode: str):
        self.counts["llm_tokens_in"] += tokens_in
        self.counts["llm_tokens_out"] += tokens_out
        self.counts["llm_cost_usd"] += cost
        if mode=="mini":
            self.counts["llm_mini_calls"] += 1
        elif mode=="full":
            self.counts["llm_full_calls"] += 1

    def record_timing(self, name: str, ms: float):
        self.timings[name] = self.timings.get(name,0) + ms

    def report(self, out_path: str):
        total_s = time.time()-self.t0
        out = {
            "counts": self.counts,
            "timings_ms": self.timings,
            "total_time_s": total_s
        }
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return out
