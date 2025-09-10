from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class NormalizedProduct(BaseModel):
    product_id: str
    fingerprint: Optional[str] = None  # 🔑 Para matching inter-retail en BD
    retailer: str
    name: str
    brand: str
    model: Optional[str] = None
    category: str
    price_current: int
    price_original: Optional[int] = None
    currency: str = "CLP"
    url: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    source: Dict[str, Any] = Field(default_factory=dict)
    # 🎯 Metadatos para auditoría y BD
    ai_enhanced: bool = False
    ai_confidence: float = 0.0
    processing_version: str = "v1.0"
