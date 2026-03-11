from pydantic import BaseModel, Field, validator
from typing import Optional, Any

class MarketOpportunity(BaseModel):
    """
    Structure une opportunité détectée sur le marché.
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
        # Si l'IA renvoie "$12,400", on nettoie pour n'avoir que le float
        if isinstance(v, str):
            import re
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", v.replace(',', ''))
            return float(numbers[0]) if numbers else 0.0
        return float(v)