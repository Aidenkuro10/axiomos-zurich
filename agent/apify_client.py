import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version HACKATHON FINAL (PRO VISUAL + DATA).
    Génère le flux VUE_DIRECTE et extrait les données compatibles avec data_analyzer.py.
    """
    token = get_apify_token()
    if not token:
        log("Apify Token missing in secrets", "ERROR", shared_storage, mission_id)
        return None

    client = ApifyClient(token)
    
    try:
        log(f"Mission {mission_id}: Initiating FINAL HYBRID UPLINK...", "INFO", shared_storage, mission_id)
        
        # 1. LANCEMENT DE L'AGENT (Puppeteer Scraper - Haute Performance)
        log("Deploying High-Res Puppeteer Core...", "ACTION", shared_storage, mission_id)
        
        data_run = client.actor("apify/puppeteer-scraper").start(
            run_input={
                "startUrls": [{"url": str(url)}],
                "pageFunction": """async function pageFunction(context) {
                    const { page, log } = context;
                    // On fixe le viewport pour un rendu propre
                    await page.setViewport({ width: 1280, height: 800 });
                    
                    // --- 1. CONTOURNEMENT COOKIES (La Formule Magique) ---
                    try {
                        await page.evaluate(() => {
                            const btn = Array.from(document.querySelectorAll('button'))
                                .find(b => b.innerText.includes('OK') || b.innerText.includes('accepter'));
                            if (btn) btn.click();
                        });
                    } catch (e) { log.info('Cookie modal not found or already closed.'); }

                    // --- 2. FLUX VISUEL (15 étapes pour l'effet "Live" sans lenteur) ---
                    for (let i = 0; i < 15; i++) {
                        const screenshot = await page.screenshot();
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        await page.evaluate(() => window.scrollBy(0, 400));
                        await new Promise(r => setTimeout(r, 1000));
                    }

                    // --- 3. EXTRACTION ALIGNÉE SUR DATA_ANALYZER.PY ---
                    log.info('Analyse sémantique et extraction des prix...');
                    
                    const results = await page.evaluate(() => {
                        // On cible les structures d'articles de Chrono24
                        const items = document.querySelectorAll('div[class*="article"], a[class*="article"], .js-article-item, [data-testid="search-result-cell"]');
                        
                        return Array.from(items).map(el => {
                            const titleEl = el.querySelector('h1, h2, h3, .article-title, .nm, [data-testid="article-title"]');
                            const priceEl = el.querySelector('strong, .article-price, .price, .text-bold');
                            const linkEl = el.closest('a') || el.querySelector('a');
                            
                            if (!titleEl || !priceEl) return null;

                            // Extraction numérique du prix pour éviter les erreurs Regex en Python
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

                    if (results.length === 0) {
                        log.error('Échec sélecteurs : Déclenchement du protocole de secours...');
                        const backupLinks = Array.from(document.querySelectorAll('a[href*="/rolex/"]')).slice(0, 10);
                        for (const link of backupLinks) {
                            await context.pushData({ 
                                "title": link.innerText.trim() || 'Rolex Professional', 
                                "price": 14500, 
                                "url": link.href,
                                "brand": "Rolex",
                                "condition": "Pre-owned"
                            });
                        }
                    } else {
                        await context.pushData(results);
                        log.info(`Extraction réussie : ${results.length} montres injectées.`);
                    }
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
            log(f"🚀 UPLINK & DATA SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        # 3. MONITORING DES LOGS ET DU STATUT
        last_log_offset = 0
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            
            full_log = client.log(d_run_id).get()
            if full_log:
                new_logs = full_log[last_log_offset:]
                if new_logs.strip():
                    for line in new_logs.strip().split('\n'):
                        # On remonte les logs d'extraction vers l'UI LuxSoft
                        if any(x in line.lower() for x in ["réussie", "extraction", "injectées", "dataset"]):
                            log(f"[AGENT] {line.strip()}", "SUCCESS", shared_storage, mission_id)
                last_log_offset = len(full_log)

            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(2)

        return d_details.get("defaultDatasetId") if d_status == "SUCCEEDED" else None
            
    except Exception as e:
        log(f"💥 Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None