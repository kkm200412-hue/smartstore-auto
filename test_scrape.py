import requests
from bs4 import BeautifulSoup
import json

def test_smartstore_search(store_name, query):
    url = f"https://smartstore.naver.com/{store_name}/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Requesting: {url}")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Check if there's any text indicating "no results"
    text_content = soup.get_text()
    if "검색결과가 없습니다" in text_content or "조건에 맞는 상품이 없습니다" in text_content:
        print("결과: 상품 없음 (No results)")
    else:
        print("결과: 상품 있음 (Found results)")
        
        # Let's see if we can find product elements
        # Usually they are inside some div with specific classes
        # But just checking the window.__PRELOADED_STATE__ might be easier
        
        preloaded = None
        for script in soup.find_all('script'):
            if script.string and 'window.__PRELOADED_STATE__' in script.string:
                preloaded = script.string
                break
                
        if preloaded:
            print("Found __PRELOADED_STATE__")
        else:
            print("Did NOT find __PRELOADED_STATE__, Naver might have changed their structure.")

if __name__ == "__main__":
    print("Test 1: Store that exists, item that should exist")
    test_smartstore_search("samsung", "갤럭시")
    print("-" * 50)
    print("Test 2: Store that exists, item that should NOT exist")
    test_smartstore_search("samsung", "말도안되는상품명12345")
