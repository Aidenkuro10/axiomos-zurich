import uuid
import time
import asyncio
import os
import httpx  # Plus performant que requests pour FastAPI
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
from config.secrets import AXIOMOS_INTERNAL_AUTH
from utils.database import init_db, save_mission, load_mission
from utils.logger import log # Utilisation du vrai logger

init_db()

app = FastAPI(title="LuxSoft Luxury Arbitrage Engine")
executor = ThreadPoolExecutor(max_workers=10)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # À restreindre si possible à ton domaine .pages.dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MissionRequest(BaseModel):
    url: str
    goal: str

@app.get("/")
def read_root():
    return {"status": "online", "service": "LuxSoft Engine", "version": "3.5.0_ASYNC"}

@app.get("/proxy-live/{mission_id}")
async def proxy_live_image(mission_id: str):
    """
    PROXY ASYNC: Télécharge l'image sans bloquer le serveur.
    """
    mission = load_mission(mission_id)
    if not mission or not mission.get("stream_url"):
        return Response(status_code=404)
    
    stream_url = mission.get("stream_url")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(stream_url, timeout=15.0)
            if resp.status_code == 200:
                return Response(content=resp.content, media_type="image/png")
        except Exception:
            pass

    # Fallback Branding
    return RedirectResponse(url="https://images.unsplash.com/photo-1547996160-81dfa63595dd?q=80&w=1280")

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """Pipeline d'orchestration optimisé."""
    loop = asyncio.get_event_loop()
    
    # On initialise en RAM pour éviter les lectures disques constantes
    shared_ref = {mission_id: load_mission(mission_id)}

    try:
        # Phase 1: Automation
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, shared_ref, mission_id
        )
        
        # Buffer de persistence
        await asyncio.sleep(5)

        if dataset_id:
            shared_ref[mission_id]["status"] = "analyzing"
            save_mission(mission_id, shared_ref[mission_id])

            # Phase 2: Analyse
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, shared_ref, mission_id
            )
            
            # Phase 3: Rapport
            report = await loop.run_in_executor(
                executor, generate_final_report, mission_id, deals, shared_ref
            )
            
            shared_ref[mission_id]["report"] = report.dict()
            shared_ref[mission_id]["status"] = "completed"
            save_mission(mission_id, shared_ref[mission_id])
            
            log(f"Mission {mission_id} completed successfully.", "SUCCESS", shared_ref, mission_id)
        else:
            shared_ref[mission_id]["status"] = "failed"
            save_mission(mission_id, shared_ref[mission_id])
            
    except Exception as e:
        log(f"Critical Runner Error: {str(e)}", "ERROR", shared_ref, mission_id)

@app.post("/run-mission")
async def start_mission(
    request: MissionRequest, 
    background_tasks: BackgroundTasks, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    # Nettoyage de la clé d'auth
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")

    if received != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")

    mission_id = str(uuid.uuid4())[:8]
    
    initial_data = {
        "status": "initializing",
        "stream_url": None, 
        "live_logs": [],
        "report": None
    }
    save_mission(mission_id, initial_data)
    
    log(f"Handshake successful. Mission ID: {mission_id}", "INFO", {mission_id: initial_data}, mission_id)
    
    background_tasks.add_task(execute_mission_task, mission_id, request.url, request.goal)
    return {"mission_id": mission_id, "status": "initiated"}

@app.get("/mission-status/{mission_id}")
async def get_mission_status(mission_id: str):
    # On retire l'auth sur le status pour simplifier le polling frontend (optionnel)
    mission = load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)