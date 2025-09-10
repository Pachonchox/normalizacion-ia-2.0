from __future__ import annotations
import argparse, json, os, time
from typing import Dict, Any, List
from .ingest import load_items
from .categorize import load_taxonomy, categorize
from .normalize import normalize_one
from .persistence import write_jsonl
from .cache import JsonCache
from .metrics import Metrics
from .match import load_normalized, do_match

def cmd_normalize(args):
    metrics = Metrics()
    taxonomy = load_taxonomy(args.taxonomy)
    cache = JsonCache(args.cache, ttl_days=args.ttl_days) if args.cache else None

    out_rows = []
    for rec in load_items(args.input):
        raw = rec["item"]
        meta = rec["metadata"]
        retailer = rec["retailer"]
        name = raw.get("name") or raw.get("title") or ""
        cat_id, conf, sugg = categorize(name, meta, taxonomy)
        row = normalize_one(raw, meta, retailer, cat_id)
        out_rows.append(row)
        metrics.inc("normalized")

    n = write_jsonl(out_rows, os.path.join(args.out, "normalized_products.jsonl"))
    metrics.dump(args.out)
    print(f"[OK] Normalized {n} items -> {os.path.join(args.out,'normalized_products.jsonl')}")

def cmd_profile(args):
    # simple field coverage profile on raw items
    from .profiling import profile_items, save_profile
    items = [rec["item"] for rec in load_items(args.input)]
    prof = profile_items(items)
    outp = os.path.join(args.out, "profile.json")
    save_profile(prof, outp)
    print(f"[OK] Profile saved to {outp}")

def cmd_match(args):
    rows = load_normalized(args.normalized)
    pairs = do_match(rows, threshold=args.sim, max_cands=args.max_cands)
    outp = os.path.join(args.out, "matches.jsonl")
    write_jsonl(pairs, outp)
    print(f"[OK] Matches: {len(pairs)} -> {outp}")

def main():
    ap = argparse.ArgumentParser(prog="retail-normalizer")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_norm = sub.add_parser("normalize", help="Normaliza JSONs crudos")
    ap_norm.add_argument("--input", required=True, help="Directorio con .json crudos")
    ap_norm.add_argument("--out", required=True, help="Directorio de salida")
    ap_norm.add_argument("--taxonomy", default="configs/taxonomy_v1.json")
    ap_norm.add_argument("--cache", default="out/cache.json")
    ap_norm.add_argument("--ttl-days", dest="ttl_days", type=int, default=7)
    ap_norm.set_defaults(func=cmd_normalize)

    ap_prof = sub.add_parser("profile", help="Perfil de campos crudos")
    ap_prof.add_argument("--input", required=True)
    ap_prof.add_argument("--out", required=True)
    ap_prof.set_defaults(func=cmd_profile)

    ap_match = sub.add_parser("match", help="Matching inter-retail")
    ap_match.add_argument("--normalized", required=True)
    ap_match.add_argument("--out", required=True)
    ap_match.add_argument("--sim", type=float, default=0.86)
    ap_match.add_argument("--max-cands", type=int, default=50)
    ap_match.set_defaults(func=cmd_match)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
