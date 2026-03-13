import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Version LUXSOFT - Capture d'état stable.
    Optimisé pour éviter les erreurs 404 en laissant le temps au serveur de générer l'image.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating NATIVE LIVE UPLINK...", "INFO", shared_storage, mission_id)
        log("Deploying Autonomous Extraction Core...", "ACTION", shared_storage, mission_id)
        
        # Configuration simplifiée pour la stabilité
        data_run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1, # Uniquement la page cible pour la rapidité
                "proxyConfiguration": {"useApifyProxy": True},
                "saveScreenshot": True,
                "dynamicContentWaitSecs": 10,
                "maxResults": 3
            },
            memory_mbytes=1024
        )
        d_run_id = data_run["id"]

        # PAUSE INITIALE : On laisse 12 secondes pour être sûr que le navigateur soit ouvert
        time.sleep(12)

        last_log_offset = 0
        
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # MISE À JOUR DU VISUEL - Cache-buster simple
            if shared_storage is not None and mission_id in shared_storage:
                ts = int(time.time())
                # On utilise l'URL directe qui est la plus stable
                shared_storage[mission_id]["stream_url"] = f"https://api.apify.com/v2/runs/{d_run_id}/screenshots/last?token={token}&v={ts}"

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
            
            # PAUSE DE BOUCLE : 6 secondes pour laisser l'infrastructure Apify respirer
            time.sleep(6.0)

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