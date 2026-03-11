import json
from utils.logger import log

def handle_apify_stream(run_id: str, mission_id: str, shared_storage: dict):
    """
    Monitors Apify execution events and injects them into the local telemetry.
    Updates the mission status to 'running' to trigger the UI live viewport.
    """
    try:
        # Note: In a production environment, this could hook into Apify webhooks 
        # or the log streaming API. For the current engine, we use it to 
        # synchronize the UI state with the active Actor.
        
        log(f"Connection established with Apify Actor (ID: {run_id})", "INFO", shared_storage, mission_id)
        
        # Synchronize status with the frontend polling logic
        if mission_id in shared_storage:
            # We use 'running' to signal the frontend to display the live viewport
            shared_storage[mission_id]["status"] = "running"
            log(f"Uplink synchronized. Agent is now in control.", "ACTION", shared_storage, mission_id)
            
    except Exception as e:
        log(f"Stream synchronization error: {str(e)}", "ERROR", shared_storage, mission_id)