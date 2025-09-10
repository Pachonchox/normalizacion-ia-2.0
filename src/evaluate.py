from __future__ import annotations
import json, os, statistics as stats
from typing import List, Dict, Any

def main(normalized_path: str, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    cats = {}
    prices = []
    with open(normalized_path, "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip(): continue
            p = json.loads(line)
            cats[p["category"]] = cats.get(p["category"], 0) + 1
            prices.append(p["price_current"])

    report = {
        "count": sum(cats.values()),
        "by_category": cats,
        "price_current_avg": (sum(prices)/len(prices)) if prices else 0
    }
    with open(os.path.join(outdir, "evaluation.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    main(args.normalized, args.out)
