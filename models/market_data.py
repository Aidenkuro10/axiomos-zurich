from pydantic import BaseModel, Field, validator
from typing import Optional, Any
import re

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

    @validator('listed_price', pre=True)
    def clean_price(cls, v):
        """
        Nettoyage automatique du prix : convertit "$12,400", "12'400 CHF" ou "12 400" en float 12400.0
        """
        if v is None:
            return 0.0
            
        if isinstance(v, (int, float)):
            return float(v)

        if isinstance(v, str):
            # 1. On vire les symboles monétaires et les espaces bizarres
            # On remplace la virgule par rien (séparateur de milliers US) 
            # et l'apostrophe par rien (séparateur CH)
            v_clean = v.replace(',', '').replace("'", "").replace(" ", "").strip()
            
            # 2. Extraction du premier nombre (entier ou décimal)
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", v_clean)
            if numbers:
                try:
                    return float(numbers[0])
                except ValueError:
                    return 0.0
        
        return 0.0

    class Config:
        # Permet d'accepter les types arbitraires si nécessaire
        arbitrary_types_allowed = True