import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version NATIVE UPLINK (Hackathon Stable).
    Supprime ImgBB pour utiliser le flux de screenshots temps réel d'Apify.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating NATIVE LIVE UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT DATA (Extraction & Navigation)
        # On lance l'agent en mode .start() pour récupérer l'ID immédiatement
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

        # 2. INJECTION DE L'URL DE SCREENSHOT NATIVE
        # Cette URL pointe vers le dernier screenshot capturé par le container de l'agent.
        # Avantage : C'est du 100% Apify, pas de latence d'upload tiers.
        native_live_url = f"https://api.apify.com/v2/runs/{d_run_id}/screenshots/last?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            # On met à jour la RAM
            shared_storage[mission_id]["stream_url"] = native_live_url
            # On force la persistance SQLite pour le proxy du backend
            save_mission(mission_id, shared_storage[mission_id])
            log(f"🚀 NATIVE UPLINK SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        last_log_offset = 0
        
        # 3. BOUCLE DE MONITORING (Logs + Statut)
        while True:
            # Récupération des détails de l'exécution
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # --- TÉLÉMÉTRIE DES LOGS ---
            # On récupère les logs de l'agent pour les afficher sur ton dashboard
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if line_content:
                            # Filtrage simple pour garder des logs lisibles
                            if any(x in line_content.lower() for x in ["navigating", "extracting", "found", "clicking"]):
                                log(f"[AGENT] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            # --- VÉRIFICATION DE FIN ---
            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            # Pause de 2 secondes pour respecter les quotas de l'API Apify
            time.sleep(2)

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