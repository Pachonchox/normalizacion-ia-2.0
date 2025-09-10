from __future__ import annotations
import os, time
from typing import Optional, Dict, Any
from .utils import LOGGER

class LLMResult:
    def __init__(self, data: Optional[Dict[str, Any]], tokens_in: int=0, tokens_out: int=0, cost_usd: float=0.0, confidence: float=0.0):
        self.data = data
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.cost_usd = cost_usd
        self.confidence = confidence

def extract_with_llm(prompt: str, mode: str = "off") -> LLMResult:
    """Stub con costos aproximados; no llama a API si mode='off'."""
    if mode == "off":
        return LLMResult(None, 0, 0, 0.0, 0.0)
    # Simula conteo tokens ~ palabras*1.3
    tokens_in = int(len(prompt.split())*1.3)
    # Precios hipotéticos:
    if mode == "mini":
        cost = tokens_in/1000*0.002
    else:
        cost = tokens_in/1000*0.01
    # No hacemos llamada real; devolvemos None
    LOGGER.info(f"[LLM:{mode}] tokens_in={tokens_in} cost≈${cost:.4f}")
    return LLMResult(None, tokens_in, 0, cost, 0.0)
