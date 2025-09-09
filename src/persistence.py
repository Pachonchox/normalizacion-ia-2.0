\
from __future__ import annotations
import json, os
from typing import Dict, Any, Iterable

def write_jsonl(rows: Iterable[Dict[str, Any]], outpath: str) -> int:
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    n = 0
    with open(outpath, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n
