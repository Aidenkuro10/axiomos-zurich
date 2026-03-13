import uuid
import time
import asyncio
import os
import requests
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.responses import Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Internal LuxSoft service imports
from agent.apify_client import launch_apify_automation
from services.data_analyzer import analyze_market_deals
from services.report_builder import generate_final_report
from config.secrets import AXIOMOS_INTERNAL_AUTH, get_apify_token
from utils.database import init_db, save_mission, load_mission

# Initialisation de la base de données au démarrage
init_db()

app = FastAPI(title="LuxSoft Luxury Arbitrage Engine")
executor = ThreadPoolExecutor(max_workers=10)

# --- CACHE MÉMOIRE GLOBAL ---
active_missions: Dict[str, Any] = {}

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
    return {"status": "online", "version": "4.0.0_DIRECT_UPLINK"}

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """
    DIRECT REDIRECT: Élimine le goulot d'étranglement du serveur.
    Le navigateur client télécharge l'image directement depuis Apify.
    """
    mission = active_missions.get(mission_id) or load_mission(mission_id)
    if not mission:
        return Response(status_code=404)
    
    stream_url = mission.get("stream_url")
    
    if stream_url:
        # On redirige vers l'URL d'Apify. Le navigateur client fera le travail.
        return RedirectResponse(url=stream_url)

    # Image de secours (placeholder luxe) si l'URL n'est pas encore prête
    idle_url = "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?auto=format&fit=crop&q=80&w=1280"
    return RedirectResponse(url=idle_url)

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Pipeline d'orchestration LuxSoft."""
    loop = asyncio.get_event_loop()
    try:
        # Phase 1: Capture
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, active_missions, mission_id
        )
        
        # Sauvegarde RAM -> DB
        save_mission(mission_id, active_missions[mission_id])

        if dataset_id:
            active_missions[mission_id]["status"] = "analyzing"
            save_mission(mission_id, active_missions[mission_id])

            # Phase 2: Analyse
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, active_missions, mission_id
            )
            
            # Phase 3: Rapport
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, active_missions
            )
            
            active_missions[mission_id]["report"] = report.dict()
            active_missions[mission_id]["status"] = "completed"
            save_mission(mission_id, active_missions[mission_id])
            print(f"--- SUCCESS: Mission {mission_id} completed ---")
            
    except Exception as e:
        print(f"💥 Runner failure: {str(e)}")
        if mission_id in active_missions:
            active_missions[mission_id]["status"] = "error"
            save_mission(mission_id, active_missions[mission_id])

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
    initial_data = {
        "status": "running",
        "stream_url": None, 
        "live_logs": [{"timestamp": time.strftime("%H:%M:%S"), "level": "INFO", "message": "Establishing secure uplink..."}],
        "report": None
    }
    active_missions[mission_id] = initial_data
    save_mission(mission_id, initial_data)
    background_tasks.add_task(execute_mission_task, mission_id, request.url, request.goal)
    return {"mission_id": mission_id, "status": "initiated"}

@app.get("/mission-status/{mission_id}")
async def get_mission_status(mission_id: str, x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")):
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")
    if received != expected:
         raise HTTPException(status_code=401, detail="Unauthorized")

    mission = active_missions.get(mission_id) or load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))