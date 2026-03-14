class Settings:
    
    PROJECT_NAME = "Axiomos — GenAI Zürich Edition"
    VERSION = "2.1.0-ZURICH"
    
    
    DEFAULT_MAX_PAGES = 5
    MISSION_TIMEOUT_SECONDS = 300
    
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "https://axiomos-zurich.pages.dev" 
    ]
    
    
    DEMO_TARGETS = {
        "watch_arbitrage": "https://www.chrono24.ch/rolex/index.htm",
        "gpu_market": "https://lambdalabs.com/service/gpu-cloud",
        "event_sniper": "https://www.ticketcorner.ch"
    }

settings = Settings()