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
        "version": "2.4.1_DOUBLE_UPLINK_STABLE",
        "active_missions": list(MissionManager.missions.keys())
    }

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """
    Relais Serveur -> Client avec Fallback Visuel.
    Sert l'image de l'agent en contournant les blocages CORS/403 d'Apify.
    """
    if mission_id not in MissionManager.missions:
        return Response(status_code=404, content="Mission expired or ID invalid")
    
    stream_url = MissionManager.missions[mission_id].get("stream_url")
    if not stream_url:
        # Uplink non établi : on renvoie l'image d'attente directement
        idle_url = "https://images.unsplash.com/photo-1547996160-81dfa63595dd?auto=format&fit=crop&q=80&w=1280"
        try:
            idle_resp = requests.get(idle_url, timeout=5)
            return Response(content=idle_resp.content, media_type="image/jpeg")
        except:
            return Response(status_code=204)

    try:
        # Tentative de récupération du visuel sur le store Apify
        resp = requests.get(stream_url, timeout=5)
        
        if resp.status_code == 200:
            return Response(content=resp.content, media_type="image/png")
        
        # Si Apify renvoie 404 (store pas encore prêt), on sert le Fallback Premium
        elif resp.status_code == 404:
            idle_url = "https://images.unsplash.com/photo-1547996160-81dfa63595dd?auto=format&fit=crop&q=80&w=1280"
            idle_resp = requests.get(idle_url)
            return Response(content=idle_resp.content, media_type="image/jpeg")
            
    except Exception as e:
        print(f"DEBUG PROXY: Critical Error - {str(e)}")
    
    return Response(status_code=404)

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Pipeline d'orchestration Double Uplink."""
    loop = asyncio.get_event_loop()
    try:
        storage = MissionManager.missions
        shared_mem = storage[mission_id]
        
        # Phase 1: Automatisation (Screenshot rapide + RAG Analysis)
        # La fonction launch_apify_automation met à jour stream_url en temps réel
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, storage, mission_id
        )

        if dataset_id:
            shared_mem["status"] = "analyzing"
            # Phase 2: Analyse des données extraites
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, storage, mission_id
            )
            # Phase 3: Construction du rapport final
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, storage
            )
            shared_mem["report"] = report.dict()
            shared_mem["status"] = "completed"
        else:
            shared_mem["status"] = "failed"
        
        # --- PERSISTENCE DE SÉCURITÉ ---
        # Garde la mission en RAM pendant 1 heure pour éviter les 404
        print(f"MISSION {mission_id} PERSISTENCE ENABLED (1H)")
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
    # Validation Auth
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
        raise HTTPException(status_code=404, detail="Mission ID not found in memory")
        
    return MissionManager.missions[mission_id]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)