import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread

# Import de tes briques Axiomos
from config.settings import settings
from models.mission import MissionRequest
from agent.runner import run_mission_orchestrator
from utils.logger import log

app = FastAPI(title=settings.PROJECT_NAME)

# --- CONFIGURATION CORS (Pour ton déploiement Cloudflare) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage temporaire en RAM (Shared Storage)
# Pour une démo de hackathon, c'est plus rapide qu'une DB
missions_context = {}

@app.get("/")
async def root():
    return {"status": "online", "system": settings.PROJECT_NAME, "version": settings.VERSION}

@app.post("/run-mission")
async def start_mission(request: MissionRequest, background_tasks: BackgroundTasks):
    """
    Point d'entrée principal. Crée une mission et lance l'orchestrateur en arrière-plan.
    """
    mission_id = str(uuid.uuid4())[:8] # ID court pour l'UI
    
    # Initialisation du contexte de mission dans le stockage partagé
    missions_context[mission_id] = {
        "status": "initializing",
        "url": request.target_url,
        "goal": request.mission_goal,
        "live_logs": [],
        "report": None
    }
    
    log(f"Nouvelle mission reçue : {mission_id}", "ACTION", missions_context, mission_id)

    # Lancement du Runner dans un thread séparé (pour éviter de bloquer l'Event Loop de FastAPI)
    # On utilise BackgroundTasks pour la propreté FastAPI
    background_tasks.add_task(
        run_mission_orchestrator, 
        mission_id, 
        request.target_url, 
        request.mission_goal, 
        missions_context
    )

    return {"mission_id": mission_id, "status": "mission_started"}

@app.get("/mission-status/{mission_id}")
async def get_status(mission_id: str):
    """
    Endpoint de polling utilisé par ton JavaScript sur Cloudflare.
    """
    if mission_id not in missions_context:
        raise HTTPException(status_code=404, detail="Mission non trouvée")
    
    # On renvoie tout le contexte (logs, status, rapport final si prêt)
    return missions_context[mission_id]

# --- DÉMARRAGE ---
if __name__ == "__main__":
    import uvicorn
    # Le port est récupéré de l'env pour Render
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)