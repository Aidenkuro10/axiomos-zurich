import uuid
import time
import asyncio
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Internal LuxSoft service imports
from agent.apify_client import launch_apify_automation
from services.data_analyzer import analyze_market_deals
from services.report_builder import generate_final_report
from config.secrets import AXIOMOS_INTERNAL_AUTH

class MissionManager:
    """Centralized in-memory storage for LuxSoft polling sessions."""
    missions: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="LuxSoft Luxury Arbitrage Engine")

# ThreadPoolExecutor handles blocking I/O calls (Apify/Requests)
executor = ThreadPoolExecutor(max_workers=10)

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"],
)

class MissionRequest(BaseModel):
    url: str
    goal: str

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "service": "LuxSoft Engine", 
        "version": "2.2.3_ZRH_SURVIVAL",
        "uptime_node": "Render Frankfurt"
    }

async def execute_mission_task(mission_id: str, url: str, goal: str):
    """
    Mission Orchestrator. 
    Sequentially executes extraction, arbitrage analysis, and report generation.
    Added a survival delay to prevent Render from recycling the process prematurely.
    """
    loop = asyncio.get_event_loop()
    try:
        storage = MissionManager.missions
        shared_mem = storage[mission_id]
        
        # --- Phase 1: Data Extraction via Apify ---
        dataset_id = await loop.run_in_executor(
            executor, launch_apify_automation, url, goal, storage, mission_id
        )

        if dataset_id:
            shared_mem["status"] = "analyzing"
            
            # --- Phase 2: LuxSoft Analysis ---
            deals = await loop.run_in_executor(
                executor, analyze_market_deals, dataset_id, 0.10, storage, mission_id
            )
            
            # --- Phase 3: Strategic Reporting ---
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
        
        # --- PHASE 4: SURVIVAL DELAY ---
        # Keeps the background task 'active' for Render, 
        # allowing the frontend to poll the final result before memory wipe.
        print(f"DEBUG: Mission {mission_id} enters grace period.")
        await asyncio.sleep(60) 
        print(f"DEBUG: Mission {mission_id} task finalized.")
            
    except Exception as e:
        print(f"💥 Critical LuxSoft Error {mission_id}: {str(e)}")
        if mission_id in MissionManager.missions:
            MissionManager.missions[mission_id]["status"] = "error"

@app.post("/run-mission")
async def start_mission(
    request: MissionRequest, 
    background_tasks: BackgroundTasks, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    # --- AUTHENTICATION ---
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")

    if received != expected:
        raise HTTPException(status_code=401, detail="Unauthorized Uplink")

    mission_id = str(uuid.uuid4())[:8]
    
    # Initialize data structure
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
    
    return {
        "mission_id": mission_id, 
        "status": "initiated",
        "uplink": "stable"
    }

@app.get("/mission-status/{mission_id}")
async def get_mission_status(
    mission_id: str, 
    x_axiomos_auth: Optional[str] = Header(None, alias="X-Axiomos-Auth")
):
    received = str(x_axiomos_auth).strip().replace('"', '').replace("'", "")
    expected = str(AXIOMOS_INTERNAL_AUTH).strip().replace('"', '').replace("'", "")

    if received != expected:
         raise HTTPException(status_code=401, detail="Unauthorized Status Request")

    if mission_id not in MissionManager.missions:
        raise HTTPException(status_code=404, detail="Mission ID not found")
        
    return MissionManager.missions[mission_id]