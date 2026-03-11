from pydantic import BaseModel, Field, validator
from typing import Optional, Any

class MarketOpportunity(BaseModel):
    """
    Structure une opportunité détectée sur le marché LuxSoft.
    """
    model_name: str = Field(..., description="Nom précis du modèle (ex: Rolex Submariner)")
    brand: str = Field(default="Unknown", description="Marque du produit")
    listed_price: Any = Field(..., description="Prix affiché sur le site")
    currency: str = Field(default="CHF")
    condition: str = Field(default="Pre-owned")
    source_url: str = Field(..., description="Lien direct vers l'annonce")
    high_value_signal: bool = Field(default=False)

    @validator('listed_price')
    def clean_price(cls, v):
        """
        Nettoyage automatique du prix : convertit "$12,400" ou "12'400 CHF" en float 12400.0
        """
        if isinstance(v, str):
            import re
            # Supprime les espaces et séparateurs spécifiques pour ne garder que le format numérique
            v_clean = v.replace(',', '').replace("'", "").replace(" ", "")
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", v_clean)
            return float(numbers[0]) if numbers else 0.0
        
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0