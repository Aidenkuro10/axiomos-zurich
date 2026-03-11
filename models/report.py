from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from .market_data import MarketOpportunity

class StrategicReport(BaseModel):
    """
    Le bilan final de la mission pour l'UI.
    """
    mission_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    opportunities_found: List[MarketOpportunity] = []
    summary: str = Field(..., description="Analyse textuelle générée par l'IA")
    average_market_gap: float = Field(0.0, description="Ecart moyen par rapport au prix du marché")
    status: str = Field("completed")