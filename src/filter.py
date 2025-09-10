from __future__ import annotations
from typing import List, Dict, Any, Tuple

class ProductFilter:
    """
    Filtro opcional desacoplado de Scrappers.
    Implementación por defecto: passthrough (no filtra nada) con estadísticas básicas.
    Reemplazable por otra implementación manteniendo la misma interfaz.
    """

    def filter_products(self, products: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        total = len(products)
        stats = {
            'total_original': total,
            'total_filtered': 0,
            'total_remaining': total,
        }
        return products, stats

