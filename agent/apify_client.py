import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version DÉMO VIDÉO.
    Force la synchronisation entre l'agent et la capture visuelle.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating NATIVE LIVE UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT AVEC ATTENTE DE RENDU
        log("Deploying Autonomous Extraction Core...", "ACTION", shared_storage, mission_id)
        
        data_run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 2,
                "proxyConfiguration": {"useApifyProxy": True},
                "saveScreenshot": True,
                "dynamicContentWaitSecs": 10, # Crucial : laisse 10s pour stabiliser l'image
                "maxResults": 3
            },
            memory_mbytes=1024 # Sécurité mémoire
        )
        d_run_id = data_run["id"]

        # PAUSE INITIALE : On laisse 8 secondes au browser pour s'initialiser
        # Cela évite le Code 404 (Apify not ready) au premier rafraîchissement
        time.sleep(8)

        last_log_offset = 0
        
        # 2. BOUCLE DE MONITORING (Logs + Statut + Visuel)
        while True:
            # Récupération de l'état du Run
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # --- MISE À JOUR DU CACHE-BUSTER ---
            # On force le navigateur à recharger l'image à chaque cycle
            if shared_storage is not None and mission_id in shared_storage:
                ts = int(time.time() * 10)
                base_url = f"https://api.apify.com/v2/runs/{d_run_id}/screenshots/last?token={token}"
                shared_storage[mission_id]["stream_url"] = f"{base_url}&t={ts}"

            # --- MISE À JOUR DES LOGS ---
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
            
            # PAUSE DE BOUCLE : On passe à 4s. 
            # C'est le temps nécessaire pour qu'Apify traite et expose le screenshot.
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