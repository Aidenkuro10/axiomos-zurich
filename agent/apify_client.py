import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version PRO LIVE (Puppeteer Engine).
    Adapté pour le flux VUE_DIRECTE et le contournement des 403.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating PRO PUPPETEER UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT (Puppeteer Scraper - Celui qui a marché !)
        log("Deploying High-Res Puppeteer Core...", "ACTION", shared_storage, mission_id)
        
        # On utilise l'Actor Puppeteer Scraper avec Proxy Résidentiel
        data_run = client.actor("apify/puppeteer-scraper").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "pageFunction": """async function pageFunction(context) {
                    const { page, log } = context;
                    await page.setViewport({ width: 1280, height: 800 });
                    try {
                        await page.evaluate(() => {
                            const btn = Array.from(document.querySelectorAll('button'))
                                .find(b => b.innerText.includes('OK') || b.innerText.includes('accepter'));
                            if (btn) btn.click();
                        });
                    } catch (e) {}
                    for (let i = 0; i < 100; i++) {
                        const screenshot = await page.screenshot();
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        await page.evaluate(() => window.scrollBy(0, 200));
                        await new Promise(r => setTimeout(r, 2000));
                    }
                }""",
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"] # CRUCIAL pour Chrono24
                },
                "useChrome": True,
                "headless": True # Obligatoire pour la stabilité du stream
            },
            memory_mbytes=4096  # Boosté à 4GB pour le flux visuel
        )
        
        d_run_id = data_run["id"]
        d_store_id = data_run["defaultKeyValueStoreId"] # On récupère l'ID du store

        # 2. INJECTION DE L'URL DE NOTRE FLUX "VUE_DIRECTE"
        # On ne pointe plus vers /screenshots/last (trop instable)
        # On pointe vers notre clé spécifique dans le Key-Value Store
        native_live_url = f"https://api.apify.com/v2/key-value-stores/{d_store_id}/records/VUE_DIRECTE?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = native_live_url
            save_mission(mission_id, shared_storage[mission_id])
            log(f"🚀 PRO LIVE UPLINK SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        # 3. BOUCLE DE MONITORING (Inchangée mais nécessaire)
        last_log_offset = 0
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # (Le reste du code de monitoring reste identique...)
            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(2)

        return d_details.get("defaultDatasetId") if d_status == "SUCCEEDED" else None
            
    except Exception as e:
        log(f"💥 Critical Automation Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None