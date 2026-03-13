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
        # C'est l'acteur à 108K utilisations qui gère parfaitement le rendu visuel
        run_input = {
            "startUrls": [{"url": str(url)}],
            "maxCrawlPages": 2,
            "crawlerType": "playwright:firefox", # Firefox bypass souvent mieux les protections anti-bot
            "saveScreenshots": True,
            "performSelfCheck": False,
            "proxyConfiguration": {"useApifyProxy": True},
            "htmlTransformer": "readableText", # Optimisé pour ton analyse de prix
            "initialConcurrency": 1,
            "maxConcurrency": 1,
            "requestHandlerTimeoutSecs": 60
        }

        data_run = client.actor("apify/website-content-crawler").start(
            run_input=run_input,
            memory_mbytes=1024
        )
        d_run_id = data_run["id"]

        # PAUSE INITIALE : Indispensable pour laisser le container démarrer
        time.sleep(8)

        last_log_offset = 0
        
        # 2. BOUCLE DE MONITORING
        while True:
            # Récupération de l'état du Run
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # --- MISE À JOUR DU VISUEL (URL UNIVERSELLE APIFY) ---
            if shared_storage is not None and mission_id in shared_storage:
                ts = int(time.time() * 10)
                # Cette route d'API renvoie TOUJOURS le dernier screenshot capturé par l'acteur
                shared_storage[mission_id]["stream_url"] = f"https://api.apify.com/v2/runs/{d_run_id}/screenshots/last?token={token}&t={ts}"

            # --- MISE À JOUR DES LOGS ---
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if line_content:
                            # Filtrage des logs pour ne garder que l'essentiel
                            if any(x in line_content.lower() for x in ["navigating", "request", "screenshot", "page", "browser"]):
                                log(f"[CRAWLER] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            # Pause de 4s pour laisser le temps au screenshot de s'écrire sur le disque d'Apify
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