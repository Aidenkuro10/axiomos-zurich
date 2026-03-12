import uuid
import time
import asyncio
import os
import requests
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Internal LuxSoft service imports
from agent.apify_client import launch_apify_automation
from services.data_analyzer import analyze_market_deals
from services.report_builder import generate_final_report
from config.secrets import AXIOMOS_INTERNAL_AUTH

class MissionManager:
    """Stockage centralisé en mémoire pour les sessions LuxSoft."""
    missions: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="LuxSoft Luxury Arbitrage Engine")

# ThreadPoolExecutor pour gérer les appels I/O bloquants
executor = ThreadPoolExecutor(max_workers=10)

# --- CONFIGURATION CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MissionRequest(BaseModel):
    url: str
    goal: str

@app.head("/")
@app.get("/")
def read_root():
    """Endpoint de santé pour Render."""
    return {
        "status": "online", 
        "service": "LuxSoft Engine", 
        "version": "2.4.0_DOUBLE_UPLINK",
        "active_missions": list(MissionManager.missions.keys())
    }

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """
    Relais Serveur -> Client avec Fallback Visuel.
    Supporte la transition entre le screenshot rapide et le screenshot final.
    """
    # Log de diagnostic RAM pour vérifier la présence de la session
    if mission_id not in MissionManager.missions:
        print(f"DEBUG PROXY: Request for {mission_id} - NOT FOUND")
        return Response(status_code=404, content="Mission expired")
    
    stream_url = MissionManager.missions[mission_id].get("stream_url")
    if not stream_url:
        return Response(status_code=204)

    try:
        # Tentative de récupération du visuel Apify
        resp = requests.get(stream_url, timeout=5)
        
        if resp.status_code == 200:
            return Response(content=resp.content, media_type="image/png")
        
        # Fallback si l'image n'est pas encore prête sur le store d'Apify
        elif resp.status_code == 404:
            idle_url = "https://images.unsplash.com/photo-1547996160-81dfa63595dd?auto=format&fit=crop&q=80&w=1280"
            idle_resp = requests.get(idle_url)
            return Response(content=idle_resp.content, media_type="image/jpeg")
            
    except Exception as e:
        print(f"DEBUG PROXY: Critical Error - {str(e)}")
    
    return Response(status_code=404)

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Pipeline LuxSoft avec exécution de l'automatisation et analyse."""
    loop = asyncio.get_event_loop()
    try:
        storage = MissionManager.missions
        shared_mem = storage[mission_id]
        
        # Phase 1: Automatisation (Double Uplink : Screenshot rapide + RAG Analysis)
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, storage, mission_id
        )

        if dataset_id:
            shared_mem["status"] = "analyzing"
            # Phase 2: Analyse des données extraites
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, storage, mission_id
            )
            # Phase 3: Construction du rapport stratégique
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, storage
            )
            shared_mem["report"] = report.dict()
            shared_mem["status"] = "completed"
        else:
            shared_mem["status"] = "failed"
        
        # --- PHASE DE PERSISTENCE ---
        # On maintient les données en RAM pour le polling post-mission (1 heure)
        print(f"MISSION {mission_id} PERSISTENCE ENABLED")
        await asyncio.sleep(3600) 
            
    except Exception as e:
        print(f"💥 Critical Failure {mission_id}: {str(e)}")
        if mission_id in MissionManager.missions:
            MissionManager.missions[mission_id]["status"] = "error"

@app.post("/run-mission")
async def start_mission(
    request: MissionRequest, 
    background_tasks: BackgroundTasks, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    # Validation de l'authentification interne
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")

    if received != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    mission_id = str(uuid.uuid4())[:8]
    MissionManager.missions[mission_id] = {
        "status": "running",
        "stream_url": None, 
        "live_logs": [],
        "report": None
    }
    
    background_tasks.add_task(execute_mission_task, mission_id, request.url, request.goal)
    return {"mission_id": mission_id, "status": "initiated"}

@app.get("/mission-status/{mission_id}")
async def get_mission_status(
    mission_id: str, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")

    if received != expected:
         raise HTTPException(status_code=401, detail="Unauthorized")

    if mission_id not in MissionManager.missions:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    return MissionManager.missions[mission_id]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)