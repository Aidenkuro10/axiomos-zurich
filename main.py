import uuid
import time
import asyncio
import os
import requests
import json
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.responses import Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Internal LuxSoft service imports
from agent.apify_client import launch_apify_automation
from services.smart_analyzer import generate_arbitrage_report
from config.secrets import AXIOMOS_INTERNAL_AUTH, get_apify_token
from utils.database import init_db, save_mission, load_mission
from utils.logger import log

# Initialisation de la base de données au démarrage
init_db()

app = FastAPI(title="LUXSOFT — Mission Control")
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
    return {"status": "online", "service": "LuxSoft Engine", "version": "5.1.0_PRODUCTION_HYBRID"}

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    mission = load_mission(mission_id)
    if not mission: return Response(status_code=404)
    stream_url = mission.get("stream_url")
    if stream_url and "apify.com" in stream_url:
        try:
            resp = requests.get(stream_url, timeout=10)
            if resp.status_code == 200:
                return Response(content=resp.content, media_type="image/png")
        except Exception: pass
    return RedirectResponse(url="https://images.unsplash.com/photo-1547996160-81dfa63595dd?q=80&w=1280")

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Pipeline d'orchestration Hybride : Œil (Puppeteer) + Cerveau (IA)"""
    loop = asyncio.get_event_loop()
    initial_state = load_mission(mission_id)
    shared_ref = {mission_id: initial_state}

    try:
        # Phase 1: L'ŒIL (Acquisition du texte brut)
        raw_text = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, shared_ref, mission_id
        )
        
        # Mise à jour immédiate du stream_url pour l'affichage live
        updated_in_ram = shared_ref.get(mission_id)
        if updated_in_ram: save_mission(mission_id, updated_in_ram)

        if raw_text:
            current_state = load_mission(mission_id)
            current_state["status"] = "analyzing"
            save_mission(mission_id, current_state)

            # Phase 2: LE CERVEAU (Analyse IA et génération du JSON)
            report_json_raw = await loop.run_in_executor(
                executor, generate_arbitrage_report, raw_text, goal, mission_id, shared_ref
            )
            
            # Phase 3: PARSING ET FORMATAGE POUR L'INTERFACE LUXSOFT
            final_state = load_mission(mission_id)
            try:
                # On transforme le string JSON du cerveau en dictionnaire Python
                ai_data = json.loads(report_json_raw)
                
                # On mappe les données sur la structure attendue par ton HTML (displayResults)
                final_state["report"] = {
                    "summary": ai_data.get("summary", "Analysis complete."),
                    "opportunities_found": ai_data.get("deals", [])
                }
            except Exception as e:
                # Fallback au cas où l'IA renverrait du texte brut au lieu de JSON
                print(f"Parsing error: {str(e)}")
                final_state["report"] = {
                    "summary": report_json_raw,
                    "opportunities_found": []
                }
            
            final_state["status"] = "completed"
            save_mission(mission_id, final_state)
            print(f"--- [SYNC SUCCESS] MISSION {mission_id} | DEALS: {len(ai_data.get('deals', []))} ---")
            
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
        "live_logs": [{"timestamp": time.strftime("%H:%M:%S"), "level": "INFO", "message": "Telemetry Online. Scanning luxury market..."}],
        "report": None
    }
    save_mission(mission_id, initial_data)
    background_tasks.add_task(execute_mission_task, mission_id, request.url, request.goal)
    return {"mission_id": mission_id, "status": "initiated"}

@app.get("/mission-status/{mission_id}")
async def get_mission_status(mission_id: str, x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")):
    received = str(x_axiomos_auth or "").strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")
    if received != expected:
         raise HTTPException(status_code=401, detail="Unauthorized")

    mission = load_mission(mission_id)
    if not mission: raise HTTPException(status_code=404, detail="Mission not found")
    return mission

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))