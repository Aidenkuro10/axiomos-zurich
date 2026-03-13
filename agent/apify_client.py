import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version HACKATHON STABLE (LIVE + AUTO-SYNC).
    Force l'extraction pendant le scroll pour éviter les datasets vides en fin de page.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating FINAL HYBRID UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT
        log("Deploying High-Res Puppeteer Core...", "ACTION", shared_storage, mission_id)
        
        data_run = client.actor("apify/puppeteer-scraper").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "pageFunction": """async function pageFunction(context) {
                    const { page, log } = context;
                    await page.setViewport({ width: 1280, height: 800 });
                    
                    // --- 1. CONTOURNEMENT COOKIES ---
                    try {
                        await page.evaluate(() => {
                            const btn = Array.from(document.querySelectorAll('button'))
                                .find(b => b.innerText.includes('OK') || b.innerText.includes('accepter'));
                            if (btn) btn.click();
                        });
                    } catch (e) { log.info('Cookies already handled.'); }

                    // --- 2. BOUCLE LIVE + EXTRACTION CONTINUE ---
                    // On réduit à 12 étapes pour optimiser le temps (environ 1m15 de run)
                    for (let i = 0; i < 12; i++) {
                        // A. Capture visuelle pour le Dashboard
                        const screenshot = await page.screenshot();
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        
                        // B. EXTRACTION IMMÉDIATE de ce qui est visible à l'écran
                        const visibleItems = await page.evaluate(() => {
                            const cards = document.querySelectorAll('.article-item, [data-testid="search-result-cell"]');
                            return Array.from(cards).map(el => {
                                const titleEl = el.querySelector('h1, h2, h3, .article-title, .nm, [data-testid="article-title"]');
                                const priceEl = el.querySelector('strong, .article-price, .price, .text-bold');
                                const linkEl = el.closest('a') || el.querySelector('a');
                                
                                if (!titleEl || !priceEl) return null;
                                const rawPrice = priceEl.innerText.replace(/[^0-9]/g, '');

                                return {
                                    "title": titleEl.innerText.trim(),
                                    "price": parseInt(rawPrice) || 0,
                                    "url": linkEl?.href || window.location.href,
                                    "brand": "Rolex",
                                    "condition": "Pre-owned"
                                };
                            }).filter(item => item !== null && item.price > 1000);
                        });

                        // On pousse les données au fur et à mesure (évite le dataset vide à la fin)
                        if (visibleItems.length > 0) {
                            await context.pushData(visibleItems);
                        }

                        // C. Scroll pour la suite
                        await page.evaluate(() => window.scrollBy(0, 500));
                        await new Promise(r => setTimeout(r, 1200));
                    }
                    
                    log.info('Mission de navigation et synchronisation terminée.');
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

        # 2. INJECTION DE L'URL DE NOTRE FLUX
        native_live_url = f"https://api.apify.com/v2/key-value-stores/{d_store_id}/records/VUE_DIRECTE?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = native_live_url
            save_mission(mission_id, shared_storage[mission_id])
            log(f"🚀 UPLINK & DATA SYNC SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        # 3. MONITORING
        last_log_offset = 0
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        if any(x in line.lower() for x in ["terminée", "extraction", "dataset", "montres"]):
                            log(f"[AGENT] {line.strip()}", "SUCCESS", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(2)

        return d_details.get("defaultDatasetId") if d_status == "SUCCEEDED" else None
            
    except Exception as e:
        log(f"💥 Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None