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
from config.secrets import AXIOMOS_INTERNAL_AUTH, get_apify_token
from utils.database import init_db, save_mission, load_mission

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
    """Diagnostic de survie pour vérifier la persistance SQLite."""
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
        "version": "2.8.0_STABLE_VIEW_FINAL",
        "database": db_status,
        "persisted_missions": mission_count
    }

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """
    Proxy Ultra-Résilient optimisé pour la clé fixe 'latest_view'.
    Bypasse intégralement le cache d'Apify et du navigateur.
    """
    mission = load_mission(mission_id)
    if not mission:
        return Response(status_code=404, content="Mission unknown")
    
    stream_url = mission.get("stream_url")
    idle_url = "https://images.unsplash.com/photo-1547996160-81dfa63595dd?auto=format&fit=crop&q=80&w=1280"
    
    if not stream_url:
        try:
            idle_resp = requests.get(idle_url, timeout=5)
            return Response(content=idle_resp.content, media_type="image/jpeg")
        except:
            return Response(status_code=204)

    # Reconstruction de l'URL pour forcer la clé latest_view et bypasser le cache
    token = get_apify_token()
    clean_base = stream_url.split('?')[0]
    # On s'assure que l'URL pointe bien vers latest_view avec un cache-buster temporel
    burst_url = f"{clean_base}?token={token}&disableRedirect=true&noCache={time.time_ns()}"

    try:
        # Timeout très court : si l'image n'est pas prête, on ne bloque pas le thread
        resp = requests.get(burst_url, timeout=3)
        if resp.status_code == 200 and len(resp.content) > 500:
            return Response(
                content=resp.content, 
                media_type="image/png",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    except Exception as e:
        print(f"Proxy Uplink Syncing... {e}")

    # Fallback silencieux (évite l'affichage d'erreur console côté client)
    return Response(status_code=204)

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Pipeline d'orchestration Dual-Core."""
    loop = asyncio.get_event_loop()
    
    # On initialise avec les données en DB
    initial_state = load_mission(mission_id)
    shared_ref = {mission_id: initial_state}

    try:
        # Phase 1: Capture Visuelle et Extraction Unifiée (Dual-Core)
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, shared_ref, mission_id
        )
        
        # On recharge l'état car les logs ont pu être mis à jour en DB par le logger
        current_state = load_mission(mission_id)

        if dataset_id:
            current_state["status"] = "analyzing"
            save_mission(mission_id, current_state)

            # Phase 2: Analyse du Dataset
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, shared_ref, mission_id
            )
            
            # Phase 3: Génération du Rapport Stratégique
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, shared_ref
            )
            
            # Finalisation et Persistance
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
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")

    if received != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    mission_id = str(uuid.uuid4())[:8]
    
    initial_data = {
        "status": "running",
        "stream_url": None, 
        "live_logs": [{"timestamp": time.strftime("%H:%M:%S"), "level": "INFO", "message": "Uplink synchronization... Initializing Dual-Core Agents."}],
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
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
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