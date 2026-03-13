import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version HACKATHON STABLE.
    Gère le flux vidéo natif et synchronise la RAM pour un affichage fluide.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating NATIVE LIVE UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT
        log("Deploying Autonomous Extraction Core...", "ACTION", shared_storage, mission_id)
        data_run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 3,
                "proxyConfiguration": {"useApifyProxy": True}
            },
            memory_mbytes=512
        )
        d_run_id = data_run["id"]

        # --- CRITIQUE : DÉLAI D'INITIALISATION POUR LA DÉMO ---
        # On attend 5 secondes que le container démarre et capture le premier visuel
        time.sleep(5)

        # 2. INJECTION DE L'URL DE SCREENSHOT DANS LA RAM
        if shared_storage is not None and mission_id in shared_storage:
            native_live_url = f"https://api.apify.com/v2/runs/{d_run_id}/screenshots/last?token={token}"
            shared_storage[mission_id]["stream_url"] = native_live_url
            log(f"🚀 NATIVE UPLINK SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        last_log_offset = 0
        
        # 3. BOUCLE DE MONITORING
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # --- TÉLÉMÉTRIE LOGS ---
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if line_content:
                            # Filtrage des logs pour une présentation propre au jury
                            if any(x in line_content.lower() for x in ["navigating", "extracting", "found", "clicking", "browser", "page"]):
                                log(f"[AGENT] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            time.sleep(1.5)

        # 4. FINALISATION
        if d_status == "SUCCEEDED":
            dataset_id = d_details.get("defaultDatasetId")
            log(f"✅ Mission successful. Dataset {dataset_id} ready.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log(f"⚠️ Agent stopped with status: {d_status}", "WARNING", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Critical Automation Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None