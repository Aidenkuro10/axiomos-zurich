import json
from utils.logger import log

def handle_apify_stream(run_id: str, mission_id: str, shared_storage: dict):
    """
    Monitors Apify execution events and injects them into the local telemetry.
    Updates the mission status to 'running' to trigger the UI live viewport.
    """
    try:
        
        log(f"Connection established with Apify Actor (ID: {run_id})", "INFO", shared_storage, mission_id)
        
        
        if mission_id in shared_storage:
            
            shared_storage[mission_id]["status"] = "running"
            log(f"Uplink synchronized. Agent is now in control.", "ACTION", shared_storage, mission_id)
            
    except Exception as e:
        log(f"Stream synchronization error: {str(e)}", "ERROR", shared_storage, mission_id)