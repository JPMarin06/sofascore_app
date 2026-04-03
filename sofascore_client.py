import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class SofascoreClient:
    """Cliente Selenium que ejecuta fetch() directamente en el navegador real."""

    BASE_URL = "https://www.sofascore.com/api/v1"

    def __init__(self):
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1280,800")
        opts.add_argument("--log-level=3")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts
        )
        self.driver.get("https://www.sofascore.com")
        time.sleep(3)

    def _get(self, endpoint, retries=3):
        url = f"{self.BASE_URL}{endpoint}"
        js = f"""
        const response = await fetch("{url}", {{
            method: "GET",
            headers: {{
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "es-ES,es;q=0.9",
                "Referer": "https://www.sofascore.com/",
            }},
            credentials: "include"
        }});
        if (!response.ok) return {{"__status": response.status}};
        return await response.json();
        """
        script = (
            "const done = arguments[arguments.length - 1];"
            "(async () => { try { done(await (async () => {" + js + "})()) }"
            " catch(e) { done({__error: e.toString()}) } })()"
        )
        for attempt in range(retries):
            try:
                time.sleep(random.uniform(0.3, 0.8))
                result = self.driver.execute_async_script(script)
                if result and "__status" in result:
                    return None
                if result and "__error" in result:
                    return None
                return result
            except Exception:
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def get_match(self, mid):
        return self._get(f"/event/{mid}")

    def get_statistics(self, mid):
        return self._get(f"/event/{mid}/statistics")

    def get_lineups(self, mid):
        return self._get(f"/event/{mid}/lineups")

    def get_incidents(self, mid):
        return self._get(f"/event/{mid}/incidents")

    def get_shotmap(self, mid):
        return self._get(f"/event/{mid}/shotmap")

    def get_heatmap(self, mid, pid):
        return self._get(f"/event/{mid}/player/{pid}/heatmap")

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    
