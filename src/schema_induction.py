\
from __future__ import annotations
import json, os

REQUIRED_COVERAGE = 0.9

def induce_from_profile(profile_path: str, out_schema_path: str) -> str:
    with open(profile_path, "r", encoding="utf-8") as fh:
        prof = json.load(fh)
    coverage = prof.get("coverage", {})
    # simplistic: fields >=90% considered required in raw (for reference report)
    required = [k for k,v in coverage.items() if v >= REQUIRED_COVERAGE]
    schema = {
        "induced_required_fields": required,
        "total_items": prof.get("total", 0)
    }
    os.makedirs(os.path.dirname(out_schema_path), exist_ok=True)
    with open(out_schema_path, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, ensure_ascii=False, indent=2)
    return out_schema_path
