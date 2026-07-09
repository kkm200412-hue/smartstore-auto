import os
import re
import time
import pandas as pd
from playwright.sync_api import sync_playwright

import platform
if platform.system() == "Windows":
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.expanduser(r"~\AppData\Local\ms-playwright")
def normalize_first_page(url):
    if "cp=" in url:
        return re.sub(r"cp=\d+", "cp=1", url)
    return url + ("&" if "?" in url else "?") + "cp=1"

def get_store_name(url):
    try:
        return url.split("smartstore.naver.com/")[1].split("/")[0]
    except:
        return ""

def scroll_page(page):
    for _ in range(18):
        page.mouse.wheel(0, 2600)
        time.sleep(0.45)

def get_lines(page):
    text = page.locator("body").inner_text(timeout=15000)
    return [x.strip() for x in text.split("\n") if x.strip()]

def parse_price_near(lines, idx):
    for line in lines[max(0, idx - 8): idx + 12]:
        if "원" in line and re.search(r"[\d,]+", line):
            return line
    return ""

def parse_review_count(text):
    for pattern in [r"리뷰\s*([\d,]+)", r"구매평\s*([\d,]+)", r"평점\s*[\d.]+\s*리뷰\s*([\d,]+)"]:
        m = re.search(pattern, text)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except:
                return 0
    return 0

def is_name_candidate(line):
    bad = ["BEST","원","배송","무료","리뷰","구매","톡톡","찜","오늘출발","할인","혜택","장바구니","평점","%","카테고리","전체상품","인기상품","공지","스토어","로그인","네이버","검색","공유","고객센터","대표","사업자"]
    if not line or len(line) <= 1:
        return False
    if any(w in line for w in bad):
        return False
    if re.fullmatch(r"[\d,]+", line):
        return False
    return True

def collect_best_from_text(page, source_url):
    results, lines = [], get_lines(page)
    store = get_store_name(source_url)
    for i, line in enumerate(lines):
        if line == "BEST" or "BEST" in line:
            nearby = lines[i:i + 12]
            name = ""
            for candidate in nearby:
                if is_name_candidate(candidate):
                    name = candidate
                    break
            if name:
                results.append({
                    "수집방식": "BEST",
                    "스토어": store,
                    "상품명": name,
                    "가격": parse_price_near(lines, i),
                    "리뷰수": parse_review_count("\n".join(nearby)),
                    "원본URL": source_url
                })
    return results

def click_review_sort(page):
    for word in ["리뷰 많은순", "리뷰많은순", "리뷰순"]:
        try:
            page.get_by_text(word).first.click(timeout=2500)
            time.sleep(3)
            return True
        except:
            pass
    try:
        items = page.locator("button, a").all()
        for item in items:
            try:
                t = item.inner_text(timeout=800).strip()
                if "리뷰" in t and ("많은" in t or "순" in t):
                    item.click(timeout=2500)
                    time.sleep(3)
                    return True
            except:
                continue
    except:
        pass
    return False

def collect_review_from_text(page, source_url):
    results, lines = [], get_lines(page)
    store = get_store_name(source_url)
    for i, line in enumerate(lines):
        m = re.search(r"리뷰\s*([\d,]+)", line)
        if not m:
            continue
        try:
            review_count = int(m.group(1).replace(",", ""))
        except:
            review_count = 0
        if review_count <= 0:
            continue
        nearby = lines[max(0, i - 12): i + 4]
        name = ""
        for candidate in reversed(nearby):
            if is_name_candidate(candidate):
                name = candidate
                break
        if name:
            results.append({
                "수집방식": "리뷰많은순",
                "스토어": store,
                "상품명": name,
                "가격": parse_price_near(lines, i),
                "리뷰수": review_count,
                "원본URL": source_url
            })
    results.sort(key=lambda x: int(x.get("리뷰수") or 0), reverse=True)
    return results

def wait_for_login_if_needed(page, naver_id="", naver_pw=""):
    # Check if we got redirected to login or captcha
    for _ in range(60): # Wait up to 5 minutes (60 * 5s)
        try:
            url = page.url
            title = page.title()
            if "nid.naver.com" in url or "로그인" in title or "접속이 불가" in title:
                # Attempt auto login if credentials provided
                if "nid.naver.com" in url and naver_id and naver_pw:
                    if page.locator("#id").is_visible() and not page.locator("#id").input_value():
                        page.evaluate(f"document.getElementById('id').value = '{naver_id}';")
                        page.evaluate(f"document.getElementById('pw').value = '{naver_pw}';")
                        page.locator(".btn_login").click()
                        time.sleep(3)
                        continue
                time.sleep(5)
            else:
                break
        except:
            time.sleep(5)

def run_collection(urls, use_best, use_review, headless=True, progress_callback=None, naver_id="", naver_pw=""):
    urls = [normalize_first_page(u.strip()) for u in urls if u.strip()]
    if not urls:
        return False, "URL이 없습니다.", None, []
    if not use_best and not use_review:
        return False, "수집 방식을 하나 이상 선택해주세요.", None, []
    
    all_results = []
    fail_list = []
    
    try:
        with sync_playwright() as p:
            profile_dir = os.path.join(os.getcwd(), "playwright_profile")
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=headless,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars"
                ],
                viewport={"width": 1400, "height": 1000},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.pages[0] if context.pages else context.new_page()
            
            for idx, url in enumerate(urls, start=1):
                store = get_store_name(url)
                if progress_callback:
                    progress_callback(idx, len(urls), store)
                    
                before = len(all_results)
                try:
                    if use_best:
                        page.goto(url, wait_until="domcontentloaded", timeout=60000)
                        wait_for_login_if_needed(page, naver_id, naver_pw)
                        time.sleep(5)
                        scroll_page(page)
                        all_results.extend(collect_best_from_text(page, url))
                    if use_review:
                        page.goto(url, wait_until="domcontentloaded", timeout=60000)
                        wait_for_login_if_needed(page, naver_id, naver_pw)
                        time.sleep(5)
                        click_review_sort(page)
                        scroll_page(page)
                        all_results.extend(collect_review_from_text(page, url))
                    if len(all_results) == before:
                        fail_list.append(store)
                except Exception as e:
                    fail_list.append(f"{store}: {str(e)}")
                    
            context.close()
            
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=["수집방식", "스토어", "상품명", "가격", "리뷰수", "원본URL"])
            
        return True, "수집 성공", df, fail_list
    except Exception as e:
        return False, f"크롤링 오류 발생: {str(e)}", None, []
