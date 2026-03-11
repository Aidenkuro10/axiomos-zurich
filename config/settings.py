class Settings:
    # Identité du projet
    PROJECT_NAME = "Axiomos — GenAI Zürich Edition"
    VERSION = "2.1.0-ZURICH"
    
    # Paramètres de Mission par défaut
    DEFAULT_MAX_PAGES = 5
    MISSION_TIMEOUT_SECONDS = 300
    
    # Configuration du Dashboard
    # C'est ici que tu mettras l'URL de ton Frontend Cloudflare une fois déployé
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "https://axiomos-zurich.pages.dev" 
    ]
    
    # Scénarios de Démo (Pour ton sélecteur sur l'UI)
    DEMO_TARGETS = {
        "watch_arbitrage": "https://www.chrono24.ch/rolex/index.htm",
        "gpu_market": "https://lambdalabs.com/service/gpu-cloud",
        "event_sniper": "https://www.ticketcorner.ch"
    }

settings = Settings()