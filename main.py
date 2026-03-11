import uuid
import time
import asyncio
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import de tes services LuxSoft
from agent.apify_client import launch_apify_automation
from services.data_analyzer import analyze_market_deals
from services.report_builder import generate_final_report

class MissionManager:
    """Stockage centralisé pour le polling de LuxSoft."""
    missions: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="LuxSoft Luxury Arbitrage Engine")

# Exécuteur pour gérer les appels bloquants (Apify/Requests) sans geler l'API
executor = ThreadPoolExecutor(max_workers=10)

# --- CONFIGURATION CORS (Optimisée pour ton UI) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class MissionRequest(BaseModel):
    url: str
    goal: str

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "service": "LuxSoft Engine", 
        "version": "2.1.0_ZRH",
        "uptime_node": "Render Frankfurt"
    }

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """
    Orchestrateur de la mission. 
    Enchaîne l'extraction, l'analyse d'arbitrage et la génération du rapport.
    """
    loop = asyncio.get_event_loop()
    try:
        storage = MissionManager.missions
        shared_mem = storage[mission_id]
        
        # --- Phase 1: Extraction via Apify ---
        # On passe storage et mission_id pour que apify_client puisse logger en direct
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, storage, mission_id
        )

        if dataset_id:
            shared_mem["status"] = "analyzing"
            
            # --- Phase 2: Analyse LuxSoft (Arbitrage Réel) ---
            # Correction : on envoie le dataset_id réel pour l'analyse
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, storage, mission_id
            )
            
            # --- Phase 3: Rapport Stratégique ---
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, storage
            )
            
            shared_mem["report"] = report.dict()
            shared_mem["status"] = "completed"
            
            shared_mem["live_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "level": "SUCCESS",
                "message": "📡 Transmission du rapport final terminée. Mission Close."
            })
        else:
            shared_mem["status"] = "failed"
            shared_mem["live_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "level": "ERROR",
                "message": "❌ Échec de la mission : l'extraction a retourné un dataset vide."
            })
            
    except Exception as e:
        print(f"💥 Erreur Critique LuxSoft {mission_id}: {str(e)}")
        if mission_id in MissionManager.missions:
            MissionManager.missions[mission_id]["status"] = "error"

@app.post("/run-mission")
async def start_mission(request: MissionRequest, background_tasks: BackgroundTasks):
    mission_id = str(uuid.uuid4())[:8]
    
    # Initialisation de la structure de données pour le polling
    MissionManager.missions[mission_id] = {
        "status": "running",
        "live_logs": [{
            "timestamp": time.strftime("%H:%M:%S"),
            "level": "INFO",
            "message": f"Uplink LuxSoft établi. Session {mission_id} active."
        }],
        "report": None
    }
    
    # Lancement en arrière-plan
    background_tasks.add_task(execute_mission_task, mission_id, request.url, request.goal)
    
    return {
        "mission_id": mission_id, 
        "status": "initiated",
        "uplink": "stable"
    }

@app.get("/mission-status/{mission_id}")
async def get_mission_status(mission_id: str):
    if mission_id not in MissionManager.missions:
        raise HTTPException(status_code=404, detail="Mission ID introuvable")
    return MissionManager.missions[mission_id]