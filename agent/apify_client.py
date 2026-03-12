import time
import requests
import base64
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version IMGBB PARALLÈLE + RETRY LOGIC.
    Déclenche le visuel et les données en simultané.
    Intègre une boucle de vérification pour éviter les records vides.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    # Diagnostic Clé ImgBB (Variable d'environnement Render)
    imgbb_key = os.environ.get("IMGBB_API_KEY")
    if not imgbb_key:
        log("❌ IMGBB_API_KEY missing from Render Environment", "ERROR", shared_storage, mission_id)
    else:
        log(f"🔎 Key detected (Prefix: {imgbb_key[:4]}...)", "INFO", shared_storage, mission_id)

    try:
        log(f"Uplink Initialized. Triggering Visual Agent...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DU VISUALISEUR (En arrière-plan via .start)
        visual_run = client.actor("apify/screenshot-url").start(
            run_input={
                "url": str(url),
                "waitUntil": "networkidle2",
                "width": 1280,
                "height": 720,
                "delay": 2000 
            }
        )
        v_run_id = visual_run["id"]

        # 2. LANCEMENT DE L'AGENT DATA (Extraction Core)
        log("Deploying Extraction Core...", "ACTION", shared_storage, mission_id)
        data_run = client.actor("apify/rag-web-browser").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "query": str(goal),
                "maxPagesPerCrawl": 1,
                "scrapingTool": "raw-http",
                "proxyConfiguration": {"useApifyProxy": True}
            },
            memory_mbytes=512
        )
        d_run_id = data_run["id"]

        # 3. BOUCLE DE TÉLÉMÉTRIE MIXTE (Logs Data + Check Visuel)
        last_log_offset = 0
        visual_secured = False
        
        while True:
            # État de l'agent Data (Indicateur de boucle principale)
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # Gestion de l'image : on tente l'upload dès que l'Actor visuel a fini
            if not visual_secured:
                v_details = client.run(v_run_id).get()
                v_status = v_details.get("status")
                
                if v_status == "SUCCEEDED":
                    v_store_id = v_details.get("defaultKeyValueStoreId")
                    
                    # --- BOUCLE DE PERSISTANCE POUR LE RECORD ---
                    record = None
                    for i in range(5): # On tente 5 fois (toutes les 2 sec)
                        record = client.key_value_store(v_store_id).get_record("OUTPUT")
                        if record and record.get('value'):
                            break
                        log(f"Syncing visual store (attempt {i+1}/5)...", "INFO", shared_storage, mission_id)
                        time.sleep(2)
                    
                    if record and imgbb_key:
                        log("Viewport captured. Syncing to ImgBB...", "ACTION", shared_storage, mission_id)
                        img_b64 = base64.b64encode(record['value']).decode('utf-8')
                        res = requests.post(
                            "https://api.imgbb.com/1/upload", 
                            data={"key": imgbb_key, "image": img_b64},
                            timeout=20
                        )
                        if res.status_code == 200:
                            public_url = res.json()['data']['url']
                            if shared_storage and mission_id in shared_storage:
                                shared_storage[mission_id]["stream_url"] = public_url
                                log(f"🚀 VISUAL UPLINK SECURED", "SUCCESS", shared_storage, mission_id)
                                visual_secured = True
                    else:
                        log("⚠️ Visual capture timeout: Output remained empty.", "WARNING", shared_storage, mission_id)
                        visual_secured = True 

            # Récupération et affichage des logs de l'agent Data
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        if line.strip():
                            log(f"[AGENT] {line.strip()}", "INFO", shared_storage, mission_id)
                    last_log_offset = len(full_log)

            # Sortie de boucle si l'extraction de données est terminée
            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            time.sleep(2)

        if d_status == "SUCCEEDED":
            dataset_id = d_details.get("defaultDatasetId")
            log(f"✅ Mission successful for session {mission_id}.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        
        return None
            
    except Exception as e:
        log(f"💥 Critical Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None