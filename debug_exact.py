import pandas as pd
import json
import re
import os

if __name__ == "__main__":
    if not os.path.exists("scraped_data.pkl"):
        print("scraped_data.pkl not found")
        exit()
    df = pd.read_pickle("scraped_data.pkl")
    
    with open("store_models_cache.json", "r", encoding="utf-8") as f:
        store_models = json.load(f)

    print("First 3 store models:", store_models[:3])

    def smart_extract(text):
        text = str(text)
        words = text.split()
        if not words: return "", ""
        brand = words[0]
        model_words = [w for w in words[1:] if bool(re.search(r'[A-Za-z0-9]', w))]
        model = " ".join(model_words)
        return brand, model

    def check_registration(model_name):
        clean_model = str(model_name).strip().lower()
        if not clean_model: return "확인 불가 (모델명 없음)", None
        
        has_eng_or_num = bool(re.search(r'[a-z0-9]', clean_model))
        
        if len(clean_model) <= 2 or not has_eng_or_num:
            for store_model in store_models:
                if clean_model == store_model.strip(): return "✅ 기등록", store_model
            return "❌ 미등록 (신규)", None
            
        pattern = re.compile(rf'(?<![a-z0-9]){re.escape(clean_model)}(?![a-z0-9])')
        
        for store_model in store_models:
            if not store_model:
                continue
            if pattern.search(store_model):
                return "✅ 기등록", store_model
        return "❌ 미등록 (신규)", None

    matches = []
    unmatches = []
    for idx, row in df.iterrows():
        nm = row["상품명"]
        # To simulate exactly what app.py does, let's extract model:
        b, m = smart_extract(nm)
        
        # apply keep_only_eng_num_words
        def keep_only_eng_num_words(text):
            return " ".join([w for w in str(text).split() if bool(re.search(r'[A-Za-z0-9]', w))])
        
        m_cleaned = keep_only_eng_num_words(m)

        status, matched_with = check_registration(m_cleaned)
        if status == "✅ 기등록":
            matches.append((nm, m_cleaned, matched_with))
        else:
            unmatches.append((nm, m_cleaned, status))

    print(f"Total Matches (Filtered Out): {len(matches)}")
    print(f"Total Unmatched (Kept for Step 3): {len(unmatches)}")
    
    if len(matches) > 0:
        print("\n--- SAMPLE MATCHES ---")
        for nm, m, matched_with in matches[:5]:
            print(f"Product: {nm}")
            print(f"Extracted Model: '{m}'")
            print(f"Matched Store Item: '{matched_with}'")
            print("-")

    if len(unmatches) > 0:
        print("\n--- SAMPLE UNMATCHED ---")
        for nm, m, status in unmatches[:5]:
            print(f"Product: {nm}")
            print(f"Extracted Model: '{m}'")
            print(f"Status: {status}")
            print("-")
