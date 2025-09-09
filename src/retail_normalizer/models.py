from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

class SourceInfo(BaseModel):
    retailer: Optional[str] = None
    product_code: Optional[str] = None
    url: Optional[str] = None
    scraped_at: Optional[str] = None

class NormalizedProduct(BaseModel):
    model_config = ConfigDict(extra="ignore")
    product_id: str
    source: SourceInfo = Field(default_factory=SourceInfo)
    name: str
    brand: str
    model: Optional[str] = None
    variant: Optional[str] = None
    category: str
    price_current: float
    price_original: Optional[float] = None
    price_card: Optional[float] = None
    currency: str = "CLP"
    attributes: Dict[str, Any] = Field(default_factory=dict)
    fingerprint: str
    created_at: str
    updated_at: str
