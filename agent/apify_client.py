import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version SNIPER ELITE.
    Capture immédiate pour éviter l'écran noir et attente active des données.
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
                        await page.waitForSelector('.article-item, [data-testid="article-card"]', { timeout: 15000 });
                        log.info('Content detected. Starting extraction.');
                    } catch (e) { 
                        log.info('Timeout waiting for cards, trying manual scroll.'); 
                    }

                    // --- C. CONTOURNEMENT COOKIES (MAINTENANT CIBLÉ SUR TA CAPTURE) ---
                    try {
                        await page.evaluate(() => {
                            // On cherche par ID (prioritaire), par texte, ou par classe de bouton bleu
                            const btn = document.querySelector('#consent_prompt_submit') || 
                                        Array.from(document.querySelectorAll('button'))
                                        .find(b => b.innerText.includes('OK') || b.innerText.includes('accepter') || b.innerText.includes('Accept'));
                            if (btn) btn.click();
                        });
                        await new Promise(r => setTimeout(r, 2000)); // Pause pour laisser le voile noir partir
                    } catch (e) { log.info('Cookies handling error or already cleared.'); }

                    // --- D. BOUCLE D'EXTRACTION (12 ÉTAPES) ---
                    for (let i = 0; i < 12; i++) {
                        // Capture visuelle à chaque étape pour le dashboard
                        const screenshot = await page.screenshot();
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        
                        const visibleItems = await page.evaluate((alreadySent) => {
                            const cards = document.querySelectorAll('.article-item, [data-testid="article-card"], .article-card, div[class*="item"]');
                            const foundNow = [];

                            cards.forEach(card => {
                                const text = card.innerText || "";
                                const titleEl = card.querySelector('h1, h2, h3, .article-title, .nm, [data-testid="article-title"]');
                                const priceMatch = text.match(/(\\d[\\d\\s',.]*)\\s?CHF/i);

                                if (titleEl && priceMatch) {
                                    const title = titleEl.innerText.trim();
                                    const cleanPrice = parseInt(priceMatch[1].replace(/[^0-9]/g, ''));
                                    const itemID = `${title.substring(0,20)}-${cleanPrice}`;

                                    const isSub = title.toLowerCase().includes('submariner');
                                    const isDuplicate = alreadySent.includes(itemID);

                                    if (isSub && !isDuplicate && cleanPrice > 5000 && cleanPrice < 50000) {
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
                    
                    // --- E. SAUVEGARDE TEXTE BRUT (POUR LE CERVEAU DANS MAIN.PY) ---
                    const fullText = await page.evaluate(() => document.body.innerText);
                    await context.setValue('RAW_TEXT', fullText);
                    
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

        # 2. INJECTION DE L'URL DE NOTRE FLUX VISUEL
        native_live_url = f"https://api.apify.com/v2/key-value-stores/{d_store_id}/records/VUE_DIRECTE?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = native_live_url
            save_mission(mission_id, shared_storage[mission_id])
            log(f"🚀 UPLINK & DATA SYNC SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        # 3. MONITORING DES LOGS ET STATUT
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(2)

        # Renvoie le texte brut pour le main.py
        raw_text_data = client.key_value_store(d_store_id).get_record("RAW_TEXT")
        return raw_text_data["value"] if raw_text_data else None
            
    except Exception as e:
        log(f"💥 Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None