\
from src.cli import main as cli_main
import subprocess, sys, os, json

def test_normalize_runs(tmp_path):
    out = tmp_path / "out"
    os.makedirs(out, exist_ok=True)
    # call via CLI normalize
    import runpy
    from argparse import Namespace
    from src.cli import cmd_normalize
    args = Namespace(input="tests/data", out=str(out), taxonomy="configs/taxonomy_v1.json", cache=str(out / "cache.json"), ttl_days=1)
    cmd_normalize(args)
    assert (out / "normalized_products.jsonl").exists()
