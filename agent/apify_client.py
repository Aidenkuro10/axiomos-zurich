import time
import os
from apify_client import ApifyClient
from config.secrets import get_apify_token
from utils.logger import log
from utils.database import save_mission

def launch_apify_automation(url, goal, shared_storage=None, mission_id=None):
    """
    Orchestrateur LuxSoft - Version ABSOLUTE SNIPER.
    Extraction chirurgicale liant chaque annonce à son URL exacte.
    Optimisé pour la stabilité RAM sur Render.
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
                    
                    // Optimisation RAM pour éviter le "Shutting down" de Render
                    await page.setViewport({ width: 1000, height: 800 });
                    
                    // --- A. CAPTURE IMMÉDIATE ---
                    const firstShot = await page.screenshot({ quality: 30 });
                    await context.setValue('VUE_DIRECTE', firstShot, { contentType: 'image/png' });

                    // --- B. CONTOURNEMENT COOKIES ---
                    try {
                        await page.evaluate(() => {
                            const btn = document.querySelector('#consent_prompt_submit') || 
                                        Array.from(document.querySelectorAll('button'))
                                        .find(b => b.innerText.includes('OK') || b.innerText.includes('accepter') || b.innerText.includes('Accept'));
                            if (btn) btn.click();
                        });
                        await new Promise(r => setTimeout(r, 1500));
                    } catch (e) { log.info('Cookies bypass skipped.'); }

                    // --- C. BOUCLE D'EXTRACTION ABSOLUTE SNIPER (6 CYCLES) ---
                    let accumulatedSniperData = "";
                    
                    for (let i = 0; i < 6; i++) {
                        // Capture visuelle pour le dashboard
                        const screenshot = await page.screenshot({ quality: 30 });
                        await context.setValue('VUE_DIRECTE', screenshot, { contentType: 'image/png' });
                        
                        // Extraction Absolute Sniper : On cible les liens réels d'annonces
                        const extractedPageData = await page.evaluate(() => {
                            // On cible tous les liens pointant vers une fiche Rolex
                            const links = Array.from(document.querySelectorAll('a[href*="/rolex/"]'));
                            
                            return links.map(link => {
                                const href = link.href;
                                // On récupère le texte du lien et du conteneur immédiat
                                const titleText = link.innerText.replace(/\\n/g, ' ').trim();
                                const containerText = link.parentElement ? link.parentElement.innerText.replace(/\\n/g, ' ').substring(0, 300) : "";
                                
                                // On ne valide que si c'est une annonce (contient un prix ou une devise)
                                if (containerText.includes('CHF') || containerText.includes('€') || containerText.match(/\\d/)) {
                                    return `IDENTIFIED_WATCH: ${titleText} | DIRECT_LINK: ${href} | CONTEXT: ${containerText}`;
                                }
                                return null;
                            }).filter(item => item !== null).join('\\n---\\n');
                        });
                        
                        accumulatedSniperData += extractedPageData + "\\n";

                        // Scroll Blitz (agressif)
                        await page.evaluate((step) => { window.scrollTo(0, (step + 1) * 1100); }, i);
                        await new Promise(r => setTimeout(r, 800)); 
                    }
                    
                    // --- D. SAUVEGARDE POUR LE SMART ANALYZER ---
                    const fullText = await page.evaluate(() => document.body.innerText);
                    await context.setValue('RAW_TEXT', accumulatedSniperData + "\\n\\nFULL_BODY_DUMP:\\n" + fullText);
                    
                    log.info('Mission Absolute Sniper terminée.');
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

        # 3. MONITORING DU STATUT (RÉACTIF 1S)
        while True:
            d_details = client.run(d_run_id).get()
            d_status = d_details.get("status")
            if d_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break
            time.sleep(1)

        # Renvoie le texte structuré au Cerveau (main.py)
        raw_text_data = client.key_value_store(d_store_id).get_record("RAW_TEXT")
        return raw_text_data["value"] if raw_text_data else None
            
    except Exception as e:
        log(f"💥 Failure: {str(e)}", "ERROR", shared_storage, mission_id)
        return None