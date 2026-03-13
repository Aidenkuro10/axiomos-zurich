import asyncio
from pyppeteer import connect
import sys

async def run_live_test():
    BROWSERLESS_TOKEN = "2U8pU0KV8AsDyW15455bc735c6a50b3adf6de8ce34e340f5a"
    # URL modifiée avec /pyppeteer
    endpoint = f"wss://chrome.browserless.io/pyppeteer?token={BROWSERLESS_TOKEN}"
    
    print(f"🔗 Tentative de connexion à : {endpoint}")
    
    try:
        # On ajoute un timeout explicite de 20 secondes pour ne pas attendre pour rien
        browser = await connect(browserWSEndpoint=endpoint, dumpio=True)
        print("✅ CONNECTÉ AU NAVIGATEUR !")
        
        page = await browser.newPage()
        print("🌍 Navigation vers Google pour test rapide...")
        await page.goto('https://www.google.com', {'timeout': 60000})
        
        print("📡 SESSION ACTIVE ! Vérifie le dashboard maintenant.")
        await asyncio.sleep(120)
        await browser.close()

    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE : {type(e).__name__}")
        print(f"Détail : {e}")

if __name__ == "__main__":
    asyncio.run(run_live_test())