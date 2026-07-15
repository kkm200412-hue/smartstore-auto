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

def parse_price_after_name(lines, name_idx):
    for line in lines[name_idx: name_idx + 8]:
        if "원" in line and re.search(r"[\d,]+", line):
            if "배송" in line or "택배" in line:
                continue
            try:
                val = int(re.search(r"[\d,]+", line).group().replace(",", ""))
                if val > 100:
                    return f"{val:,}원"
            except: pass
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
    line = line.strip()
    if not line or len(line) <= 2: 
        return False
        
    # 가격(예: 3,000원, 3000) 형태면 상품명에서 제외
    if re.search(r"^[\d,]+\s*원?$", line) or re.fullmatch(r"[\d,]+", line): 
        return False
        
    # 스토어 메뉴나 버튼 이름이면 제외
    exact_bad = ["BEST", "무료배송", "오늘출발", "장바구니", "찜하기", "톡톡문의", "구매하기", "카테고리", "전체상품", "인기상품", "공지사항", "동영상", "재생시간", "판매가", "할인가", "적립", "스토어", "네이버", "로그인", "고객센터", "공지", "공유"]
    if line in exact_bad: 
        return False
        
    # 쓰레기 텍스트 패턴이 포함된 경우 제외
    if "썸네일" in line or "리뷰 " in line or "평점 " in line or "찜 " in line or "구매 " in line: 
        return False
        
    return True

def collect_best_from_text(page, source_url):
    results, lines = [], get_lines(page)
    store = get_store_name(source_url)
    for i, line in enumerate(lines):
        if line == "BEST" or "BEST" in line:
            nearby = lines[i:i + 12]
            name_idx = -1
            for j, candidate in enumerate(nearby):
                if is_name_candidate(candidate):
                    name = candidate
                    name_idx = i + j
                    break
            if name:
                results.append({
                    "수집방식": "BEST",
                    "스토어": store,
                    "상품명": name,
                    "가격": parse_price_after_name(lines, name_idx) if name_idx != -1 else "",
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
        name_idx = -1
        for j, candidate in enumerate(reversed(nearby)):
            if is_name_candidate(candidate):
                name = candidate
                name_idx = max(0, i - 12) + (len(nearby) - 1 - j)
                break
        if name:
            results.append({
                "수집방식": "리뷰많은순",
                "스토어": store,
                "상품명": name,
                "가격": parse_price_after_name(lines, name_idx) if name_idx != -1 else "",
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

def collect_individual_product(page, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        store = get_store_name(url)
        title = page.title()
        name = title.split(" : ")[0].strip() if " : " in title else title
        
        price = 0
        lines = get_lines(page)
        prices = []
        for line in lines[:50]:
            if "원" in line and re.search(r"[\d,]+", line):
                if "배송" in line or "택배" in line:
                    continue
                try:
                    p = int(re.search(r"[\d,]+", line).group().replace(",", ""))
                    if p > 100:
                        prices.append(p)
                except: pass
                
        if prices:
            price = min(prices)
                
        review_count = parse_review_count("\n".join(lines[:100]))
        
        return [{
            "수집방식": "개별URL",
            "스토어": store,
            "상품명": name,
            "가격": price if price > 0 else "가격 확인 불가",
            "리뷰수": review_count,
            "원본URL": url
        }]
    except Exception as e:
        return []

def run_collection(urls, use_best, use_review, headless=True, progress_callback=None, naver_id="", naver_pw=""):
    urls = [normalize_first_page(u.strip()) for u in urls if u.strip()]
    if not urls:
        return False, "URL이 없습니다.", None, []
    
    # We allow scraping to proceed if there are any individual URLs even if use_best and use_review are False
    has_individual = any("/product" in u for u in urls)
    if not use_best and not use_review and not has_individual:
        return False, "스토어 URL인 경우 수집 방식(BEST/리뷰)을 하나 이상 선택해주세요.", None, []
    
    all_results = []
    fail_list = []
    
    try:
        with sync_playwright() as p:
            profile_dir = os.path.join(os.getcwd(), "playwright_profile")
            context = p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=headless,
                channel="chrome",
                ignore_default_args=["--enable-automation"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ],
                viewport={"width": 1400, "height": 1000},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.pages[0] if context.pages else context.new_page()
            
            for idx, url in enumerate(urls, start=1):
                store = get_store_name(url)
                if progress_callback:
                    progress_callback(idx, len(urls), store, None)
                    
                before = len(all_results)
                try:
                    if "/products/" in url or "/product/" in url:
                        all_results.extend(collect_individual_product(page, url))
                    else:
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
                    
                if progress_callback:
                    progress_callback(idx, len(urls), store, all_results)
                    
            context.close()
            
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=["수집방식", "스토어", "상품명", "가격", "리뷰수", "원본URL"])
            
        return True, "수집 성공", df, fail_list
    except Exception as e:
        return False, f"크롤링 오류 발생: {str(e)}", None, []
