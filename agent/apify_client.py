import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version DÉMO VISUELLE FORCÉE.
    Désactive le mode 'raw-http' pour garantir l'ouverture du navigateur.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating VISUAL UPLINK...", "INFO", shared_storage, mission_id)
        log("Deploying Autonomous Extraction Core...", "ACTION", shared_storage, mission_id)
        
        # CONFIGURATION DE FORÇAGE NAVIGATEUR
        run_input = {
            "startUrls": [{"url": str(url)}],
            "query": str(goal),
            "maxPagesPerCrawl": 2,
            "proxyConfiguration": {"useApifyProxy": True},
            # --- CES 3 LIGNES SONT LES PLUS IMPORTANTES ---
            "scrapingTool": "browser-playwright", 
            "useRawHttpFallback": False, 
            "saveScreenshot": True,
            # -----------------------------------------------
            "dynamicContentWaitSecs": 10,
            "maxResults": 3
        }

        data_run = client.actor("apify/rag-web-browser").start(
            run_input=run_input,
            memory_mbytes=1024 # 1GB minimum pour Playwright
        )
        d_run_id = data_run["id"]

        # On attend 10 secondes pour laisser le container charger Chrome/Firefox
        time.sleep(10)

        last_log_offset = 0
        
        # 2. BOUCLE DE MONITORING (Logs + Statut + Visuel)
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # MISE À JOUR VISUELLE (Cache-Buster)
            if shared_storage is not None and mission_id in shared_storage:
                ts = int(time.time() * 10)
                base_url = f"https://api.apify.com/v2/runs/{d_run_id}/screenshots/last?token={token}"
                shared_storage[mission_id]["stream_url"] = f"{base_url}&t={ts}"

            # MISE À JOUR DES LOGS
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if line_content:
                            if any(x in line_content.lower() for x in ["navigating", "extracting", "found", "clicking", "browser", "screenshot"]):
                                log(f"[AGENT] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            # On laisse 4s de battement pour la génération du screenshot
            time.sleep(4.0)

        # 3. FINALISATION
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