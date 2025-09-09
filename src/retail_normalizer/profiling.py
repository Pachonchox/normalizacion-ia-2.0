from __future__ import annotations
import json, os, glob, re
from collections import Counter, defaultdict
from typing import List, Dict, Any

def profile_json_files(input_dir: str, patterns: List[str]) -> Dict[str, Any]:
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(input_dir, pat)))
    field_counts = Counter()
    type_counts = defaultdict(Counter)
    samples = []
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            # detect shape
            if isinstance(data, dict) and "products" in data:
                items = data["products"]
            elif isinstance(data, list):
                items = data
            else:
                items = []
            for it in items[:200]:
                samples.append(it)
                for k,v in it.items():
                    field_counts[k]+=1
                    type_counts[k][type(v).__name__]+=1
        except Exception as e:
            pass
    return {
        "num_files": len(files),
        "field_counts": field_counts.most_common(),
        "type_counts": {k: dict(v) for k,v in type_counts.items()},
        "samples": samples[:10]
    }
