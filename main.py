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
        "version": "2.3.0_DIAGNOSTIC",
        "active_missions": list(MissionManager.missions.keys())
    }

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """
    Relais Serveur -> Client avec Diagnostic.
    """
    # LOG DE DIAGNOSTIC : On liste ce que le serveur voit en RAM
    print(f"DEBUG PROXY: Request for {mission_id}. RAM State: {list(MissionManager.missions.keys())}")

    if mission_id not in MissionManager.missions:
        return Response(status_code=404, content=f"Mission {mission_id} not found in RAM")
    
    stream_url = MissionManager.missions[mission_id].get("stream_url")
    if not stream_url:
        return Response(status_code=204) # Toujours en vie, mais pas d'URL

    try:
        resp = requests.get(stream_url, timeout=5)
        if resp.status_code == 200:
            return Response(content=resp.content, media_type="image/png")
        
        # Si Apify ne répond pas encore, on renvoie un pixel pour garder le flux actif
        elif resp.status_code == 404:
            print(f"DEBUG PROXY: Apify store not ready for {mission_id}")
            empty_pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n\x2e\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            return Response(content=empty_pixel, media_type="image/png")
            
    except Exception as e:
        print(f"DEBUG PROXY: Error - {str(e)}")
    
    return Response(status_code=404)

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Pipeline LuxSoft avec persistence forcée."""
    loop = asyncio.get_event_loop()
    try:
        storage = MissionManager.missions
        shared_mem = storage[mission_id]
        
        # Phase 1: Navigation
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, storage, mission_id
        )

        if dataset_id:
            shared_mem["status"] = "analyzing"
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, storage, mission_id
            )
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, storage
            )
            shared_mem["report"] = report.dict()
            shared_mem["status"] = "completed"
        else:
            shared_mem["status"] = "failed"
        
        # --- PHASE DE PERSISTENCE FORCÉE (1 HEURE) ---
        # On ne supprime plus la mission pour permettre le debug manuel
        print(f"MISSION {mission_id} SLEEPING FOR 1 HOUR TO PRESERVE DATA")
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