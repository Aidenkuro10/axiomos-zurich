from pydantic import BaseModel, Field

class MissionRequest(BaseModel):
    """
    Paramètres d'entrée pour lancer l'agent Apify.
    """
    target_url: str = Field(..., example="https://www.chrono24.ch/rolex/index.htm")
    mission_goal: str = Field(..., example="Find Submariner below 10k CHF")
    depth_limit: int = Field(default=5, description="Nombre max de pages à scanner")