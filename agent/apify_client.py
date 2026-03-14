import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version BLITZ STABLE.
    Vitesse accrue et protection de la VUE_DIRECTE.
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
                    await page.setViewport({ width: 1280, height: 1000 });
                    
                    const sentItems = new Set();

                    // --- A. CAPTURE IMMÉDIATE (ANTI-ÉCRAN NOIR) ---
                    const firstShot = await page.screenshot({ quality: 50 });
                    await context.setValue('VUE_DIRECTE', firstShot, { contentType: 'image/png' });

                    // --- B. CONTOURNEMENT COOKIES ---
                    try {
                        await page.evaluate(() => {
                            const btn = document.querySelector('#consent_prompt_submit') || 
                                        Array.from(document.querySelectorAll('button'))
                                        .find(b => b.innerText.includes('OK') || b.innerText.includes('accepter') || b.innerText.includes('Accept'));
                            if (btn) btn.click();
                        });
                        await new Promise(r => setTimeout(r, 1000));
                    } catch (e) { log.info('Cookies bypass skipped.'); }

                    // --- C. BOUCLE BLITZ (RÉDUITE À 5 POUR LA VITESSE) ---
                    for (let i = 0; i < 5; i++) {
                        // Capture visuelle conservée pour ton dashboard
                        const screenshot = await page.screenshot({ quality: 40 });
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        
                        const visibleItems = await page.evaluate((alreadySent) => {
                            const cards = document.querySelectorAll('.article-item, [data-testid="article-card"], .article-card');
                            const foundNow = [];

                            cards.forEach(card => {
                                const text = card.innerText || "";
                                const titleEl = card.querySelector('h1, h2, h3, .article-title');
                                const priceMatch = text.match(/(\\d[\\d\\s',.]*)\\s?(CHF|€|\\$)/i);

                                if (priceMatch) {
                                    const title = titleEl ? titleEl.innerText.trim() : "Rolex Submariner";
                                    const cleanPrice = parseInt(priceMatch[1].replace(/[^0-9]/g, ''));
                                    const itemID = `${title.substring(0,15)}-${cleanPrice}`;

                                    if (title.toLowerCase().includes('submariner') && !alreadySent.includes(itemID)) {
                                        foundNow.push({
                                            "id": itemID,
                                            "title": title,
                                            "price": cleanPrice,
                                            "url": card.querySelector('a')?.href || window.location.href
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

                        // Scroll plus large pour aller plus vite
                        await page.evaluate((step) => { window.scrollTo(0, step * 1500); }, i + 1);
                        await new Promise(r => setTimeout(r, 600)); 
                    }
                    
                    // --- D. MOISSON FINALE ---
                    const fullText = await page.evaluate(() => document.body.innerText);
                    await context.setValue('RAW_TEXT', fullText);
                    
                    log.info('Blitz Scan complete.');
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

        # 2. INJECTION FLUX VISUEL
        native_live_url = f"https://api.apify.com/v2/key-value-stores/{d_store_id}/records/VUE_DIRECTE?token={token}"
        
        if shared_storage and mission_id in shared_storage:
            shared_storage[mission_id]["stream_url"] = native_live_url
            save_mission(mission_id, shared_storage[mission_id])
            log(f"🚀 UPLINK SECURED: {d_run_id}", "SUCCESS", shared_storage, mission_id)

        # 3. MONITORING RÉACTIF
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(1) # Monitoring plus rapide (1s au lieu de 2s)

        raw_text_data = client.key_value_store(d_store_id).get_record("RAW_TEXT")
        return raw_text_data["value"] if raw_text_data else None
            
    except Exception as e:
        log(f"💥 Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None