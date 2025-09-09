from __future__ import annotations
import sqlite3, json, os, time
from typing import Optional, Dict, Any
from .utils import now_iso

class Cache:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS product_cache(
            fingerprint TEXT PRIMARY KEY,
            product_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        self.conn.commit()

    def get(self, fp: str) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT product_json FROM product_cache WHERE fingerprint=?", (fp,))
        row = cur.fetchone()
        if not row: return None
        return json.loads(row[0])

    def put(self, fp: str, product: Dict[str, Any]):
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO product_cache(fingerprint,product_json,updated_at) VALUES(?,?,?)",
                    (fp, json.dumps(product, ensure_ascii=False), now_iso()))
        self.conn.commit()
