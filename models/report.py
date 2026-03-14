from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from models.market_data import MarketOpportunity
from utils.logger import log

class StrategicReport(BaseModel):
    """
    Le bilan final de la mission pour l'UI LuxSoft.
    """
    mission_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    opportunities_found: List[MarketOpportunity] = []
    summary: str = Field(..., description="Analyse textuelle générée par l'IA")
    average_market_gap: float = Field(0.0, description="Ecart moyen par rapport au prix du marché")
    status: str = Field("completed")

def generate_final_report(mission_id: str, deals: List[MarketOpportunity], shared_storage=None):
    """
    Compile les opportunités détectées en un rapport stratégique structuré.
    """
    log(f"📋 Génération du rapport stratégique pour la mission {mission_id}...", "INFO", shared_storage, mission_id)

    
    total_gap = 0.0
    high_value_count = 0
    
    for deal in deals:
        if deal.high_value_signal:
            high_value_count += 1
    
    
    if high_value_count > 0:
        summary_text = f"Analyse terminée. {high_value_count} opportunités d'arbitrage critiques identifiées avec un signal de haute valeur."
    else:
        summary_text = "Scan terminé. Le marché semble stable, aucune anomalie de prix majeure détectée sous le seuil configuré."

    
    report = StrategicReport(
        mission_id=mission_id,
        opportunities_found=deals,
        summary=summary_text,
        average_market_gap=0.0 
    )

    log(f"✅ Rapport prêt : {len(deals)} items archivés.", "SUCCESS", shared_storage, mission_id)
    return report