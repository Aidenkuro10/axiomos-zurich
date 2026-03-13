import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version UNIVERSAL SNIPER.
    Capture immédiate, attente active et détection multi-devises.
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
                    
                    const sentItems = new Set();

                    // --- A. CAPTURE IMMÉDIATE (ANTI-ÉCRAN NOIR) ---
                    const firstShot = await page.screenshot();
                    await context.setValue('VUE_DIRECTE', firstShot, { contentType: 'image/png' });

                    // --- B. ATTENTE ACTIVE DU CONTENU ---
                    try {
                        await page.waitForSelector('.article-item, [data-testid="article-card"], .article-card', { timeout: 15000 });
                        log.info('Content detected. Starting extraction.');
                    } catch (e) { 
                        log.info('Timeout waiting for specific cards, trying general extraction.'); 
                    }

                    // --- C. BOUCLE D'EXTRACTION ---
                    for (let i = 0; i < 12; i++) {
                        const screenshot = await page.screenshot();
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        
                        const visibleItems = await page.evaluate((alreadySent) => {
                            // On cible les cartes d'annonces ou les conteneurs de produits
                            const cards = document.querySelectorAll('.article-item, [data-testid="article-card"], .article-card, div[class*="item"]');
                            const foundNow = [];

                            cards.forEach(card => {
                                const text = card.innerText || "";
                                // DÉTECTION UNIVERSELLE : On cherche n'importe quelle devise (CHF, €, $, £)
                                const priceMatch = text.match(/(\\d[\\d\\s',.]*)\\s?(CHF|€|\\$|£|EUR|USD)/i);
                                
                                if (priceMatch) {
                                    const cleanPrice = parseInt(priceMatch[1].replace(/[^0-9]/g, ''));
                                    const titleEl = card.querySelector('h1, h2, h3, .article-title, .nm, [data-testid="article-title"]');
                                    const title = titleEl ? titleEl.innerText.trim() : text.split('\\n')[0].substring(0, 50).trim();
                                    
                                    const itemID = `${title.substring(0,20)}-${cleanPrice}`;
                                    const isSub = title.toLowerCase().includes('submariner');
                                    const isDuplicate = alreadySent.includes(itemID);

                                    // Filtre : Submariner entre 4k et 60k (fourchette luxe large)
                                    if (isSub && !isDuplicate && cleanPrice > 4000 && cleanPrice < 60000) {
                                        foundNow.push({
                                            "id": itemID,
                                            "title": title,
                                            "price": cleanPrice,
                                            "url": card.querySelector('a')?.href || window.location.href,
                                            "brand": "Rolex",
                                            "condition": "Pre-owned"
                                        });
                                    }
                                }
                            });
                            return foundNow;
                        }, Array.from(sentItems));

                        if (visibleItems.length > 0) {
                            visibleItems.forEach(item => sentItems.add(item.id));
                            await context.pushData(visibleItems);
                        }

                        await page.evaluate(() => window.scrollBy(0, 800));
                        await new Promise(r => setTimeout(r, 2000));
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

        native_live_url = f"https://api.apify.com/v2/key-value-stores/{d_store_id}/records/VUE_DIRECTE?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = native_live_url
            save_mission(mission_id, shared_storage[mission_id])
            log(f"🚀 UPLINK & DATA SYNC SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        last_log_offset = 0
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        if any(x in line.lower() for x in ["terminée", "extraction", "dataset", "submariner", "sync"]):
                            log(f"[AGENT] {line.strip()}", "SUCCESS", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(2)

        return d_details.get("defaultDatasetId") if d_status == "SUCCEEDED" else None
            
    except Exception as e:
        log(f"💥 Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None