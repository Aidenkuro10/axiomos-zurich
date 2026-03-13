import time
import asyncio
from agent.apify_client import launch_apify_automation
from services.data_analyzer import analyze_market_deals
from services.report_builder import generate_final_report
from utils.logger import log

def run_mission_orchestrator(mission_id: str, url: str, goal: str, shared_storage: dict):
    """
    Executes the full mission lifecycle with safety buffers for data persistence.
    """
    try:
        # 1. Automation Launch (Apify Handshake)
        log(f"Initiating mission {mission_id} on target: {url}", "ACTION", shared_storage, mission_id)
        
        dataset_id = launch_apify_automation(url, goal, shared_storage, mission_id)
        
        if not dataset_id:
            log("Automation launch failed: No dataset ID returned.", "ERROR", shared_storage, mission_id)
            shared_storage[mission_id]["status"] = "failed"
            return

        # --- MODIFICATION CRITIQUE : BUFFER DE PERSISTENCE ---
        # On attend 5 secondes pour laisser Apify consolider le dataset avant l'analyse.
        log("Agent mission finished. Cooling down for data persistence...", "INFO", shared_storage, mission_id)
        time.sleep(5) 

        # 2. Data Retrieval & Analysis
        log("Extraction complete. Analyzing market opportunities...", "INFO", shared_storage, mission_id)
        
        shared_storage[mission_id]["status"] = "analyzing"
        
        # Analyze deals from the extracted dataset
        deals = analyze_market_deals(dataset_id, 0.10, shared_storage, mission_id)
        
        # 3. Final Strategic Reporting
        report = generate_final_report(mission_id, deals, shared_storage)
        
        # 4. Final Storage Update
        shared_storage[mission_id]["report"] = report.dict()
        shared_storage[mission_id]["status"] = "completed"
        
        log(f"Mission {mission_id} successfully closed. Strategic report ready.", "SUCCESS", shared_storage, mission_id)

    except Exception as e:
        log(f"Runner Critical Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        if mission_id in shared_storage:
            shared_storage[mission_id]["status"] = "error"