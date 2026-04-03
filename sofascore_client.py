import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class SofascoreClient:
    BASE_URL = "https://www.sofascore.com/api/v1"
    IMAGE_BASE = "https://api.sofascore.app/api/v1"

    def __init__(self):
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1280,800")
        opts.add_argument("--log-level=3") # Silenciar logs internos
        # Silenciar los errores de Chrome en tu terminal (DEPRECATED_ENDPOINT, etc)
        opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        self.driver.get("https://www.sofascore.com")
        time.sleep(3)

    def _get(self, endpoint, retries=3):
        url = f"{self.BASE_URL}{endpoint}"
        js = f"const response = await fetch('{url}'); if (!response.ok) return {{'__status': response.status}}; return await response.json();"
        script = "const done = arguments[arguments.length - 1]; (async () => { try { done(await (async () => {" + js + "})()) } catch(e) { done({__error: e.toString()}) } })()"
        for attempt in range(retries):
            try:
                time.sleep(random.uniform(0.3, 0.8))
                res = self.driver.execute_async_script(script)
                if res and "__status" not in res and "__error" not in res:
                    return res
            except Exception:
                time.sleep(2)
        return None

    def search(self, query: str) -> list:
        data = self._get(f"/search/all?q={query}&page=0")
        if not data or "results" not in data: return []
        teams = [item for item in data["results"] if item.get("type") == "team"]
        return teams[:5]

    def get_logo_url(self, entity_type: str, entity_id: int) -> str:
        return f"{self.IMAGE_BASE}/{entity_type}/{entity_id}/image"

    def get_team_events_paginated(self, team_id: int, page: int = 0) -> dict | None:
        return self._get(f"/team/{team_id}/events/last/{page}")

    def get_match(self, mid: int): return self._get(f"/event/{mid}")
    def get_statistics(self, mid: int): return self._get(f"/event/{mid}/statistics")
    def quit(self):
        if self.driver:
            try: self.driver.quit()
            except: pass
            self.driver = None