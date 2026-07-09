import time
from playwright.sync_api import sync_playwright

url = "https://smartstore.naver.com/unotradeint/category/ALL?cp=1"

def test_scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        text = page.locator("body").inner_text(timeout=15000)
        lines = [x.strip() for x in text.split("\n") if x.strip()]
        
        best_count = sum(1 for line in lines if "BEST" in line)
        print(f"Total lines: {len(lines)}")
        print(f"BEST count: {best_count}")
        browser.close()

if __name__ == "__main__":
    test_scrape()
