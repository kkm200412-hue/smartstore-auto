import time
from playwright.sync_api import sync_playwright

url = "https://smartstore.naver.com/unotradeint/category/ALL?cp=1"

def test_scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1400, "height": 1000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        text = page.locator("body").inner_text(timeout=15000)
        with open("test_output2.txt", "w", encoding="utf-8") as f:
            f.write(text)
        browser.close()

if __name__ == "__main__":
    test_scrape()
