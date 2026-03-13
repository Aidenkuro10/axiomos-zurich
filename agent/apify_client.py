import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version PRO LIVE (Puppeteer Engine).
    Adapté pour le flux VUE_DIRECTE, le contournement des 403 et l'extraction finale.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating PRO PUPPETEER UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT (Puppeteer Scraper - Formule Magique Stable)
        log("Deploying High-Res Puppeteer Core...", "ACTION", shared_storage, mission_id)
        
        data_run = client.actor("apify/puppeteer-scraper").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "pageFunction": """async function pageFunction(context) {
                    const { page, log } = context;
                    await page.setViewport({ width: 1280, height: 800 });
                    
                    // --- FORMULE MAGIQUE : CONTOURNEMENT COOKIES ---
                    try {
                        await page.evaluate(() => {
                            const btn = Array.from(document.querySelectorAll('button'))
                                .find(b => b.innerText.includes('OK') || b.innerText.includes('accepter'));
                            if (btn) btn.click();
                        });
                    } catch (e) {}

                    // --- FLUX VISUEL : 20 CAPTURES (Optimisé pour la vitesse) ---
                    for (let i = 0; i < 20; i++) {
                        const screenshot = await page.screenshot();
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        await page.evaluate(() => window.scrollBy(0, 300));
                        await new Promise(r => setTimeout(r, 1000));
                    }

                    // --- EXTRACTION FINALE : POUR LE RAPPORT ---
                    log.info('Lancement de l extraction des données...');
                    const results = await page.evaluate(() => {
                        return Array.from(document.querySelectorAll('.article-item, .article-card-container')).map(el => {
                            const priceText = el.querySelector('.article-price strong')?.innerText || el.querySelector('.price')?.innerText;
                            return {
                                brand: 'Rolex',
                                model_name: el.querySelector('.article-title')?.innerText || 'Submariner/GMT',
                                listed_price: priceText ? parseInt(priceText.replace(/[^0-9]/g, '')) : 0,
                                source_url: el.querySelector('a')?.href,
                                high_value_signal: true
                            };
                        });
                    });

                    // Envoi au dataset pour ton backend LuxSoft
                    await context.pushData(results);
                    log.info(`Extraction terminée: ${results.length} items trouvés.`);
                }""",
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"]
                },
                "useChrome": True,
                "headless": True
            },
            memory_mbytes=4096
        )
        
        d_run_id = data_run["id"]
        d_store_id = data_run["defaultKeyValueStoreId"]

        # 2. INJECTION DE L'URL DE NOTRE FLUX "VUE_DIRECTE"
        native_live_url = f"https://api.apify.com/v2/key-value-stores/{d_store_id}/records/VUE_DIRECTE?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = native_live_url
            save_mission(mission_id, shared_storage[mission_id])
            log(f"🚀 PRO LIVE UPLINK SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        # 3. BOUCLE DE MONITORING
        last_log_offset = 0
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            # Monitoring des logs
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        if any(x in line.lower() for x in ["terminée", "extraction", "trouvés"]):
                            log(f"[AGENT] {line.strip()}", "SUCCESS", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(2)

        return d_details.get("defaultDatasetId") if d_status == "SUCCEEDED" else None
            
    except Exception as e:
        log(f"💥 Critical Automation Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None