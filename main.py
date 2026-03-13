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
from utils.logger import log

# Initialisation de la base de données au démarrage
init_db()

app = FastAPI(title="LuxSoft Luxury Arbitrage Engine")
executor = ThreadPoolExecutor(max_workers=10)

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
    import sqlite3
    mission_count = 0
    db_status = "NOT_FOUND"
    if os.path.exists("luxsoft_persistence.db"):
        db_status = "ACTIVE"
        try:
            conn = sqlite3.connect("luxsoft_persistence.db")
            cursor = conn.execute("SELECT COUNT(*) FROM missions")
            mission_count = cursor.fetchone()[0]
            conn.close()
        except:
            db_status = "CORRUPTED"
    return {
        "status": "online", 
        "service": "LuxSoft Engine", 
        "version": "3.6.0_STABLE_UPLINK",
        "database": db_status,
        "persisted_missions": mission_count
    }

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """
    PROXY SYNCHRONE (STABLE): Utilise requests pour garantir l'affichage 
    du flux Puppeteer sans les erreurs de timeout de httpx.
    """
    mission = load_mission(mission_id)
    if not mission:
        return Response(status_code=404)
    
    stream_url = mission.get("stream_url")
    
    if stream_url and "apify.com" in stream_url:
        try:
            # On garde requests ici car c'est ce qui marchait pour tes images
            resp = requests.get(stream_url, timeout=10)
            if resp.status_code == 200:
                return Response(content=resp.content, media_type="image/png")
        except Exception as e:
            print(f"DEBUG: Proxy Error: {str(e)}")

    idle_url = "https://images.unsplash.com/photo-1547996160-81dfa63595dd?auto=format&fit=crop&q=80&w=1280"
    return RedirectResponse(url=idle_url)

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Pipeline d'orchestration avec pause de synchronisation forcée."""
    loop = asyncio.get_event_loop()
    initial_state = load_mission(mission_id)
    shared_ref = {mission_id: initial_state}

    try:
        # Phase 1: Automation (L'agent travaille)
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, shared_ref, mission_id
        )
        
        # --- POINT CRITIQUE : PAUSE DE SYNCHRONISATION ---
        # On attend 12 secondes pour que les serveurs Apify finissent d'écrire le Dataset.
        # C'est ce qui évite d'avoir un rapport "0 items".
        log(f"Mission {mission_id}: Syncing cloud data... (12s)", "INFO", shared_ref, mission_id)
        await asyncio.sleep(12)
        
        # Sauvegarde du stream_url final
        updated_in_ram = shared_ref.get(mission_id)
        if updated_in_ram:
            save_mission(mission_id, updated_in_ram)

        if dataset_id:
            current_state = load_mission(mission_id)
            current_state["status"] = "analyzing"
            save_mission(mission_id, current_state)

            # Phase 2: Analyse
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, shared_ref, mission_id
            )
            
            # Phase 3: Rapport
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, shared_ref
            )
            
            final_state = load_mission(mission_id)
            final_state["report"] = report.dict()
            final_state["status"] = "completed"
            save_mission(mission_id, final_state)
            
            print(f"--- SUCCESS: Mission {mission_id} completed ---")
        else:
            final_state = load_mission(mission_id)
            final_state["status"] = "failed"
            save_mission(mission_id, final_state)
            
    except Exception as e:
        print(f"💥 Runner Critical Failure {mission_id}: {str(e)}")
        current = load_mission(mission_id)
        if current:
            current["status"] = "error"
            save_mission(mission_id, current)

@app.post("/run-mission")
async def start_mission(
    request: MissionRequest, 
    background_tasks: BackgroundTasks, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    received = str(x_axiomos_auth or "").strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")

    if received != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    mission_id = str(uuid.uuid4())[:8]
    initial_data = {
        "status": "running",
        "stream_url": None, 
        "live_logs": [{"timestamp": time.strftime("%H:%M:%S"), "level": "INFO", "message": "Uplink synchronization... Launching Autonomous Agent."}],
        "report": None
    }
    save_mission(mission_id, initial_data)
    background_tasks.add_task(execute_mission_task, mission_id, request.url, request.goal)
    return {"mission_id": mission_id, "status": "initiated"}

@app.get("/mission-status/{mission_id}")
async def get_mission_status(
    mission_id: str, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    received = str(x_axiomos_auth or "").strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")
    if received != expected:
         raise HTTPException(status_code=401, detail="Unauthorized")

    mission = load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)