#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗂️ ARCHIVO ARCHIVADO - Categorización Legacy (Solo JSON)
===========================================================
Este archivo ha sido reemplazado por categorize_db.py con sistema híbrido BD+JSON.

📅 Archivado: 2025-09-09
🔄 Reemplazado por: src/categorize_db.py
⚠️  NOTA: No usar en producción - mantenido solo para referencia

Funcionalidad original:
- Categorización básica usando solo taxonomy_v1.json
- Sin soporte BD
- Sin cache inteligente
- Sin ponderación por fuente
"""

from __future__ import annotations
import json, re
from typing import Dict, Any, Tuple

def load_taxonomy(path: str) -> Dict[str, Any]:
    """LEGACY: Cargar taxonomía solo desde JSON"""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def categorize(name: str, metadata: Dict[str, Any], taxonomy: Dict[str, Any]) -> Tuple[str, float, list]:
    """LEGACY: Categorización básica sin BD ni mejoras avanzadas"""
    text = " ".join([
        str(metadata.get("search_name") or ""),
        str(metadata.get("search_term") or ""),
        str(name or ""),
    ]).lower()

    best = ("others", 0.0)
    for node in taxonomy["nodes"]:
        score = 0.0
        # exact id/name keywords
        if node["name"].lower() in text:
            score += 0.6
        for syn in node.get("synonyms", []):
            if re.search(rf"\b{re.escape(syn)}\b", text):
                score += 0.25
        if score > best[1]:
            best = (node["id"], score)

    if best[1] >= 0.6:
        return best[0], min(1.0, best[1]), []
    # suggestions: top 3 by raw score without threshold
    scored = []
    for node in taxonomy["nodes"]:
        score = 0.0
        if node["name"].lower() in text:
            score += 0.6
        for syn in node.get("synonyms", []):
            if re.search(rf"\b{re.escape(syn)}\b", text):
                score += 0.25
        scored.append((node["id"], score))
    scored.sort(key=lambda x: x[1], reverse=True)
    suggestions = [c for c,_ in scored[:3] if _>0]
    return best[0], best[1], suggestions