from __future__ import annotations
import argparse, os, json
from typing import List
from .orchestrator import run_pipeline
from .utils import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Retail Normalizer Pipeline")
    parser.add_argument("--input", required=False, default="/mnt/data", help="Carpeta con JSONs de scraping")
    parser.add_argument("--patterns", required=False, default="*.json", help="Patrones separados por coma")
    parser.add_argument("--outdir", required=False, default="./outputs", help="Carpeta de salida")
    parser.add_argument("--enable-cache", action="store_true", help="Habilita cache SQLite")
    parser.add_argument("--llm", choices=["off","mini","full"], default="off", help="Modo de LLM fallback")
    parser.add_argument("--stage", choices=["all","normalize","match"], default="all", help="Etapa a ejecutar")
    parser.add_argument("--normalized", help="Ruta a normalized_products.jsonl para etapa match")
    args = parser.parse_args()

    patterns = [p.strip() for p in args.patterns.split(",") if p.strip()]
    os.makedirs(args.outdir, exist_ok=True)

    if args.stage=="match" and args.normalized:
        # Carga productos normalizados y solo corre matching
        prods = []
        with open(args.normalized, "r", encoding="utf-8") as f:
            for line in f:
                prods.append(json.loads(line))
        from .match import find_matches
        from .metrics import Metrics
        from .utils import setup_logging
        setup_logging(os.path.join(args.outdir,"logs","run.log"))
        m = find_matches(prods)
        with open(os.path.join(args.outdir,"matches.jsonl"),"w",encoding="utf-8") as out:
            for r in m: out.write(json.dumps(r, ensure_ascii=False)+"\n")
        print(f"Matches: {len(m)}")
        return

    res = run_pipeline(args.input, patterns, args.outdir, args.enable_cache, args.llm, args.stage)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
