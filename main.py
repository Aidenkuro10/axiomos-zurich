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

# ThreadPoolExecutor gère les appels I/O bloquants
executor = ThreadPoolExecutor(max_workers=10)

# --- CONFIGURATION CORS ULTRA-PERMISSIVE ---
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
    """Endpoint de santé vital pour Render."""
    return {
        "status": "online", 
        "service": "LuxSoft Engine", 
        "version": "2.2.7_VISUAL_FIX",
        "port": os.environ.get("PORT", "10000")
    }

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """
    PROXY CRITIQUE : Télécharge l'image d'Apify côté serveur 
    et la sert au front-end pour éviter les erreurs 403/CORS.
    """
    if mission_id not in MissionManager.missions:
        return Response(status_code=404)
    
    stream_url = MissionManager.missions[mission_id].get("stream_url")
    if not stream_url:
        return Response(status_code=404)

    try:
        # Le serveur Render possède les credentials pour accéder à l'image
        resp = requests.get(stream_url, timeout=5)
        if resp.status_code == 200:
            return Response(content=resp.content, media_type="image/png")
    except Exception as e:
        print(f"Proxy Error: {str(e)}")
    
    return Response(status_code=404)

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Orchestrateur de Mission."""
    loop = asyncio.get_event_loop()
    try:
        storage = MissionManager.missions
        shared_mem = storage[mission_id]
        
        # --- Phase 1: Extraction ---
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, storage, mission_id
        )

        if dataset_id:
            shared_mem["status"] = "analyzing"
            
            # --- Phase 2: Analyse ---
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, storage, mission_id
            )
            
            # --- Phase 3: Rapport ---
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, storage
            )
            
            shared_mem["report"] = report.dict()
            shared_mem["status"] = "completed"
            
            shared_mem["live_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "level": "SUCCESS",
                "message": "📡 Final report transmission complete. Mission closed."
            })
        else:
            shared_mem["status"] = "failed"
            shared_mem["live_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "level": "ERROR",
                "message": "❌ Mission failed: Extraction returned an empty dataset."
            })
        
        # --- PHASE 4: GRACE PERIOD ---
        await asyncio.sleep(180) # Augmenté à 3 min pour le polling final
        if mission_id in MissionManager.missions:
            del MissionManager.missions[mission_id]
            
    except Exception as e:
        print(f"💥 Critical Error {mission_id}: {str(e)}")
        if mission_id in MissionManager.missions:
            MissionManager.missions[mission_id]["status"] = "error"

@app.post("/run-mission")
async def start_mission(
    request: MissionRequest, 
    background_tasks: BackgroundTasks, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")

    if received != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    mission_id = str(uuid.uuid4())[:8]
    
    MissionManager.missions[mission_id] = {
        "status": "running",
        "stream_url": None, 
        "live_logs": [{
            "timestamp": time.strftime("%H:%M:%S"),
            "level": "INFO",
            "message": f"LuxSoft uplink established. Session {mission_id} active."
        }],
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
        raise HTTPException(status_code=404, detail="Mission expired or not found")
        
    return MissionManager.missions[mission_id]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)