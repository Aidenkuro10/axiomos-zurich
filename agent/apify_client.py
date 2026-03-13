import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Version LUXSOFT - Direct Uplink Protocol.
    Injecte le run_id en temps réel pour permettre au frontend de bypasser le proxy Render.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating VISUAL FOCUS UPLINK...", "INFO", shared_storage, mission_id)
        
        # LANCEMENT DE L'AGENT
        data_run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1,
                "proxyConfiguration": {"useApifyProxy": True},
                "saveScreenshot": True,
                "dynamicContentWaitSecs": 15, # On laisse du temps au rendu
                "waitUntil": "networkidle",
                "maxResults": 3
            },
            memory_mbytes=1024
        )
        d_run_id = data_run["id"]

        # --- ÉTAPE CRUCIALE : On expose l'ID au reste du système immédiatement ---
        if shared_storage is not None and mission_id in shared_storage:
            shared_storage[mission_id]["run_id"] = d_run_id
            log(f"Uplink established. Run ID synchronized: {d_run_id}", "INFO", shared_storage, mission_id)

        # PAUSE INITIALE : Pour laisser le temps à la première image d'exister sur Apify
        time.sleep(12)

        last_log_offset = 0
        
        while True:
            # Récupération de l'état du Run
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # MISE À JOUR DU VISUEL (Pour compatibilité, même si le frontend va bypasser)
            if shared_storage is not None and mission_id in shared_storage:
                ts = int(time.time())
                shared_storage[mission_id]["stream_url"] = f"https://api.apify.com/v2/runs/{d_run_id}/screenshot?token={token}&v={ts}"

            # MISE À JOUR DES LOGS
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if any(x in line_content.lower() for x in ["navigating", "extracting", "found", "clicking", "browser"]):
                            log(f"[AGENT] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            # On boucle toutes les 5 secondes pour la télémétrie
            time.sleep(5.0)

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