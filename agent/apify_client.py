import time
import requests
import base64
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version UNIFIÉE (Web-Scraper).
    Fusionne capture visuelle et extraction de données.
    Bypasse totalement les problèmes de Key-Value Store d'Apify.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    imgbb_key = os.environ.get("IMGBB_API_KEY")

    try:
        log(f"Mission {mission_id}: Launching Unified Extraction Agent...", "INFO", shared_storage, mission_id)
        
        # On utilise Web Scraper qui est le plus robuste pour le JS et les screenshots
        run = client.actor("apify/web-scraper").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "runMode": "DEVELOPMENT", # Plus rapide pour les tests
                "pageFunction": """
                async def pageFunction(context) {
                    const { page, request, log } = context;
                    
                    // Attente de stabilisation de la page
                    await page.waitForTimeout(4000);
                    
                    // Capture du screenshot directement en Buffer
                    const screenshot = await page.screenshot({ fullPage: false, type: 'png' });
                    
                    // Retour des données + Image en Base64
                    return {
                        url: request.url,
                        screenshotB64: screenshot.toString('base64'),
                        pageTitle: await page.title()
                    };
                }
                """,
                "proxyConfiguration": {"useApifyProxy": True}
            }
        )
        
        run_id = run["id"]
        last_offset = 0

        while True:
            details = client.run(run_id).get()
            status = details.get("status")
            
            # Streaming des logs pour voir ce qu'il fait
            f_log = client.log(run_id).get()
            if f_log:
                new = f_log[last_offset:]
                if new.strip():
                    for line in new.strip().split('\n'):
                        log(f"[CORE] {line.strip()}", "INFO", shared_storage, mission_id)
                    last_offset = len(f_log)

            if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(2)

        if status == "SUCCEEDED":
            # 1. RÉCUPÉRATION DU SCREENSHOT DANS LE DATASET
            items = client.dataset(details["defaultDatasetId"]).list_items().items
            if items and "screenshotB64" in items[0] and imgbb_key:
                log("Uplink established. Syncing visual buffer to ImgBB...", "ACTION", shared_storage, mission_id)
                
                res = requests.post(
                    "https://api.imgbb.com/1/upload",
                    data={"key": imgbb_key, "image": items[0]["screenshotB64"]},
                    timeout=25
                )
                
                if res.status_code == 200:
                    public_url = res.json()['data']['url']
                    if shared_storage and mission_id in shared_storage:
                        shared_storage[mission_id]["stream_url"] = public_url
                        log(f"🚀 VISUAL UPLINK SECURED", "SUCCESS", shared_storage, mission_id)
                else:
                    log(f"ImgBB Error: {res.text}", "ERROR", shared_storage, mission_id)

            # 2. LANCEMENT DE L'AGENT DATA (RAG) SUR LE CONTENU
            # On réutilise le dataset pour que l'analyzer puisse travailler
            return details.get("defaultDatasetId")
        
        return None
            
    except Exception as e:
        log(f"💥 Unified Agent Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None