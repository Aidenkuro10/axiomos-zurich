from pydantic import BaseModel, Field

class MissionRequest(BaseModel):
    """
    Input parameters to initialize the Apify Agent mission.
    Maps directly to the frontend 'Mission Config' panel.
    """
    url: str = Field(
        ..., 
        example="https://www.chrono24.ch/rolex/index.htm",
        description="The target marketplace URL to scan."
    )
    goal: str = Field(
        ..., 
        example="Identify Rolex Submariner anomalies -10% market price.",
        description="The specific search criteria for the agent."
    )
    depth_limit: int = Field(
        default=3, 
        description="Maximum number of pages the agent is allowed to crawl."
    )

    class Config:
        schema_extra = {
            "example": {
                "url": "https://www.chrono24.ch/rolex/index.htm",
                "goal": "Find Submariner below 10k CHF",
                "depth_limit": 3
            }
        }