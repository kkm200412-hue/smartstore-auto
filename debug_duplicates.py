import pandas as pd
import json
import re

if __name__ == "__main__":
    df = pd.read_pickle("scraped_data.pkl")
    with open("store_models_cache.json", "r", encoding="utf-8") as f:
        store_models = json.load(f)

    # Let's mock the extraction logic used in Tab 2 for these items
    # Using the "smart_extract" fallback logic
    def smart_extract(text):
        text = str(text)
        words = text.split()
        if not words: return "", ""
        brand = words[0]
        model_words = [w for w in words[1:] if bool(re.search(r'[A-Za-z0-9]', w))]
        model = " ".join(model_words)
        return brand, model

    def check_registration(model_name):
        clean_model = str(model_name).replace(" ", "").lower()
        if not clean_model: return "확인 불가", None
        has_eng_or_num = bool(re.search(r'[a-z0-9]', clean_model))
        if len(clean_model) <= 2 or not has_eng_or_num:
            for sm in store_models:
                if clean_model == sm: return "✅ 기등록", sm
            return "❌ 미등록 (신규)", None
        for sm in store_models:
            if not sm or len(sm) < 2: continue
            if clean_model in sm or sm in clean_model: return "✅ 기등록", sm
        return "❌ 미등록 (신규)", None

    print(f"Testing {len(df)} products against {len(store_models)} store items...")
    matches = []
    for idx, row in df.iterrows():
        nm = row["상품명"]
        b, m = smart_extract(nm)
        status, matched_with = check_registration(m)
        if status == "✅ 기등록":
            matches.append((nm, m, matched_with))

    print(f"Total false/true positives: {len(matches)}")
    for nm, m, matched_with in matches[:20]:
        print(f"Product: {nm}")
        print(f"Extracted Model: {m}")
        print(f"Matched Store Item (no spaces): {matched_with}")
        print("-" * 40)
