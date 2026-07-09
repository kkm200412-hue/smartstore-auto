import pandas as pd
import json
import re

if __name__ == "__main__":
    df = pd.read_pickle("scraped_data.pkl")
    with open("store_models_cache.json", "r", encoding="utf-8") as f:
        store_models = json.load(f)

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

    matches = []
    for idx, row in df.iterrows():
        nm = row["상품명"]
        m = nm  # Using the entire product name as the model
        status, matched_with = check_registration(m)
        if status == "✅ 기등록":
            matches.append((nm, matched_with))

    print(f"Total false/true positives when using FULL NAME: {len(matches)} out of {len(df)}")
    for nm, matched_with in matches[:10]:
        print(f"Product: {nm} -> Matched with: {matched_with}")
