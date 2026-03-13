import uuid
import time
import asyncio
import os
import requests
import json
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.responses import Response, StreamingResponse
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

app = FastAPI(title="LuxSoft Engine - Visual Uplink Edition")
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

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "service": "LuxSoft Engine", 
        "version": "4.2.0_TINY_HYBRID_STREAM",
        "engine": "Axiomos Visual Pipeline"
    }

# --- ARCHITECTURE TINYFIX : LE FLUX SSE ---
@app.get("/stream-uplink/{mission_id}")
async def stream_uplink(mission_id: str):
    """
    ROUTE CRITIQUE : Simule le mode SSE de TinyFix.
    Garde la connexion ouverte pour envoyer l'URL de stream dès qu'elle est prête.
    """
    async def event_generator():
        last_url = None
        # On garde le flux ouvert pendant 2 minutes max
        for _ in range(120):
            mission = active_missions.get(mission_id)
            if not mission:
                break
            
            current_url = mission.get("stream_url")
            # On n'envoie que si l'URL a changé (économie de bande passante Render)
            if current_url and current_url != last_url:
                last_url = current_url
                yield f"data: {json.dumps({'type': 'STREAMING_URL', 'url': current_url})}\n\n"
            
            # Heartbeat pour éviter que Render ne coupe la connexion
            yield "data: {\"type\": \"HEARTBEAT\"}\n\n"
            
            if mission.get("status") in ["completed", "failed", "error"]:
                yield f"data: {json.dumps({'type': 'COMPLETE', 'status': mission.get('status')})}\n\n"
                break
                
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """Tunnel binaire pour bypasser les sécurités CORS."""
    mission = active_missions.get(mission_id) or load_mission(mission_id)
    if not mission or not mission.get("stream_url"):
        return Response(status_code=404)
    
    try:
        resp = requests.get(mission["stream_url"], timeout=5)
        if resp.status_code == 200:
            return Response(content=resp.content, media_type="image/jpeg")
    except Exception as e:
        print(f"Proxy Error: {e}")
    
    return Response(status_code=404)

async def execute_mission_task(mission_id: str, url: str, goal: str):
    loop = asyncio.get_event_loop()
    try:
        # Phase 1: Navigation & Capture (Apify)
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, active_missions, mission_id
        )
        
        save_mission(mission_id, active_missions[mission_id])

        if dataset_id:
            active_missions[mission_id]["status"] = "analyzing"
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, active_missions, mission_id
            )
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, active_missions
            )
            active_missions[mission_id].update({"report": report.dict(), "status": "completed"})
            save_mission(mission_id, active_missions[mission_id])
    except Exception as e:
        print(f"Critical Failure {mission_id}: {str(e)}")
        if mission_id in active_missions:
            active_missions[mission_id]["status"] = "error"

@app.post("/run-mission")
async def start_mission(
    request: MissionRequest, 
    background_tasks: BackgroundTasks, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    if str(x_axiomos_auth).strip().replace('"', '').replace("'", "") != AXIOMOS_INTERNAL_AUTH:
        raise HTTPException(status_code=401)

    mission_id = str(uuid.uuid4())[:8]
    active_missions[mission_id] = {
        "status": "running",
        "run_id": None,
        "stream_url": None, 
        "live_logs": [],
        "report": None
    }
    
    background_tasks.add_task(execute_mission_task, mission_id, request.url, request.goal)
    return {"mission_id": mission_id, "status": "initiated"}

@app.get("/mission-status/{mission_id}")
async def get_mission_status(mission_id: str):
    mission = active_missions.get(mission_id) or load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404)
    return mission

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))