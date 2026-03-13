import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version HACKATHON STABLE (LIVE + AUTO-SYNC).
    Garantit le flux d'images ET l'extraction de données via une recherche sémantique souple.
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
                                .find(b => b.innerText.includes('OK') || b.innerText.includes('accepter') || b.innerText.includes('Accept'));
                            if (btn) btn.click();
                        });
                    } catch (e) { log.info('Cookies already handled.'); }

                    // --- 2. BOUCLE LIVE + EXTRACTION CONTINUE ---
                    for (let i = 0; i < 12; i++) {
                        // A. Capture visuelle pour le Dashboard (TON IMAGE)
                        const screenshot = await page.screenshot();
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        
                        // B. EXTRACTION SOUPLE (LE FILET DE PÊCHE)
                        // On ne cherche plus de classes CSS précises, on cherche du texte avec "CHF"
                        const visibleItems = await page.evaluate(() => {
                            const elements = document.querySelectorAll('div, article, section, li');
                            const items = [];

                            elements.forEach(el => {
                                const text = el.innerText || "";
                                // On cible les blocs qui ont l'air d'être des annonces (taille moyenne)
                                if (text.includes('CHF') && text.length < 600 && text.length > 40) {
                                    // Extraction du prix par Regex
                                    const priceMatch = text.match(/(\d[\d\s',.]*)\s?CHF/i);
                                    if (priceMatch) {
                                        const cleanPrice = parseInt(priceMatch[1].replace(/[^0-9]/g, ''));
                                        if (cleanPrice > 500) {
                                            items.push({
                                                "title": text.split('\\n')[0].substring(0, 60),
                                                "price": cleanPrice,
                                                "url": el.querySelector('a')?.href || window.location.href,
                                                "brand": "Rolex",
                                                "condition": "Pre-owned"
                                            });
                                        }
                                    }
                                }
                            });
                            // Dédoublonnage rapide
                            return items.filter((v,i,a)=>a.findIndex(t=>(t.price===v.price && t.title===v.title))===i);
                        });

                        // Envoi immédiat vers le Dataset
                        if (visibleItems.length > 0) {
                            await context.pushData(visibleItems);
                        }

                        // C. Scroll fluide
                        await page.evaluate(() => window.scrollBy(0, 600));
                        await new Promise(r => setTimeout(r, 1500));
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
                        if any(x in line.lower() for x in ["terminée", "extraction", "dataset", "montres", "sync"]):
                            log(f"[AGENT] {line.strip()}", "SUCCESS", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(2)

        return d_details.get("defaultDatasetId") if d_status == "SUCCEEDED" else None
            
    except Exception as e:
        log(f"💥 Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None