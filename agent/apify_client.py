import time
import os
import requests
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Version LUXSOFT - VISUAL BULLDOZER (STABLE STREAM).
    Optimisée pour alimenter le flux SSE du backend LuxSoft.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Launching VISUAL BULLDOZER...", "INFO", shared_storage, mission_id)
        
        # 1. CONFIGURATION DU SCRAPER (RENDU CHROME OBLIGATOIRE)
        run_input = {
            "startUrls": [{"url": str(url)}],
            "runMode": "DEVELOPMENT",
            "pageFunction": """async function pageFunction(context) {
                const { page, log } = context;
                const wait = (ms) => new Promise(res => setTimeout(res, ms));

                log.info('Browser Uplink Stable. Waiting for render...');
                await wait(8000);
                
                log.info('Executing telemetry scroll...');
                await page.evaluate(() => window.scrollBy(0, 500));
                
                await wait(8000);
                log.info('Finalizing capture...');
                
                return { 
                    title: await page.title(), 
                    url: page.url() 
                };
            }""",
            "proxyConfiguration": {"useApifyProxy": True},
            "browserLog": True,
            "saveScreenshot": True,
            "waitUntil": ["networkidle2"],
        }

        data_run = client.actor("apify/web-scraper").start(
            run_input=run_input,
            memory_mbytes=2048 
        )
        d_run_id = data_run["id"]

        # 2. BOUCLE DE MONITORING ET ALIMENTATION DU STREAM
        last_log_offset = 0
        
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            if shared_storage is not None and mission_id in shared_storage:
                # Injection de l'URL de l'image pour le flux SSE du backend
                ts = int(time.time())
                # On utilise l'ID du run pour construire l'URL de capture directe
                shared_storage[mission_id]["stream_url"] = f"https://api.apify.com/v2/runs/{d_run_id}/screenshot?token={token}&v={ts}"
                shared_storage[mission_id]["run_id"] = d_run_id

            # RÉCUPÉRATION DES LOGS DU NAVIGATEUR
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        line_content = line.strip()
                        if any(x in line_content.lower() for x in ["info", "scroll", "navigation", "render", "capture"]):
                            log(f"[BROWSER] {line_content}", "INFO", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            
            # Fréquence de rafraîchissement calée sur le flux SSE (2.5s)
            time.sleep(2.5)

        # 3. FINALISATION ET EXTRACTION
        if d_status == "SUCCEEDED":
            dataset_id = d_details.get("defaultDatasetId")
            log(f"✅ Mission successful. Dataset {dataset_id} ready.", "SUCCESS", shared_storage, mission_id)
            return dataset_id
        else:
            log(f"⚠️ Visual Engine stopped: {d_status}", "WARNING", shared_storage, mission_id)
            return None
            
    except Exception as e:
        log(f"💥 Visual Engine Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None