import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Version LUXSOFT - Website Content Crawler (STABLE VISUAL MODE).
    Utilise l'acteur industriel le plus fiable pour le RAG et les screenshots.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating STABLE VISUAL UPLINK...", "INFO", shared_storage, mission_id)
        log("Deploying Professional Crawler Engine...", "ACTION", shared_storage, mission_id)
        
        # On utilise Website Content Crawler (apify/website-content-crawler)
        # On force la capture et on configure le crawler pour être le plus "humain" possible
        run_input = {
            "startUrls": [{"url": str(url)}],
            "maxCrawlPages": 2,
            "crawlerType": "playwright:firefox", 
            "saveScreenshots": True,
            "performSelfCheck": False,
            "proxyConfiguration": {"useApifyProxy": True},
            "htmlTransformer": "readableText",
            "initialConcurrency": 1,
            "maxConcurrency": 1,
            "requestHandlerTimeoutSecs": 60,
            # Paramètres additionnels pour stabiliser le rendu visuel
            "dynamicContentWaitSecs": 10,
            "snapshotFullscreen": True
        }

        data_run = client.actor("apify/website-content-crawler").start(
            run_input=run_input,
            memory_mbytes=2048 # Augmenté à 2Go pour supporter le rendu Firefox sans crash
        )
        d_run_id = data_run["id"]

        # Pause initiale de 10 secondes pour l'initialisation du moteur
        time.sleep(10)

        last_log_offset = 0
        
        # 2. BOUCLE DE MONITORING
        while True:
            # Récupération de l'état du Run
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # --- MISE À JOUR DU VISUEL (URL UNIVERSELLE APIFY) ---
            if shared_storage is not None and mission_id in shared_storage:
                ts = int(time.time() * 10)
                # Lien direct vers la dernière capture d'écran disponible
                shared_storage[mission_id]["stream_url"] = f"https://api.apify.com/v2/runs/{d_run_id}/screenshots/last?token={token}&t={ts}"

            # --- MISE À JOUR DES LOGS ---
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if line_content:
                            if any(x in line_content.lower() for x in ["navigating", "request", "screenshot", "page", "browser"]):
                                log(f"[CRAWLER] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            time.sleep(4.0)

        # 3. FINALISATION
        if d_status == "SUCCEEDED":
            dataset_id = d_details.get("defaultDatasetId")
            log(f"✅ Visual Mission successful. Dataset {dataset_id} ready.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log(f"⚠️ Crawler stopped with status: {d_status}", "WARNING", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Critical Automation Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None