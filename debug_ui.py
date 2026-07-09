import pandas as pd
import json
import re
import os

if __name__ == "__main__":
    if not os.path.exists("scraped_data.pkl"):
        print("scraped_data.pkl not found")
        exit()
    df_new = pd.read_pickle("scraped_data.pkl")
    
    with open("store_models_cache.json", "r", encoding="utf-8") as f:
        store_models = json.load(f)

    # Replicating App.py logic EXACTLY
    df_result = df_new.copy()
    col_name_new = "상품명"
    model_col_new = "(자동 추출 사용)"

    # smart_extract
    def smart_extract(text):
        text = str(text)
        words = text.split()
        if not words: return pd.Series(["", ""])
        brand = words[0]
        model_words = [w for w in words[1:] if bool(re.search(r'[A-Za-z0-9]', w))]
        model = " ".join(model_words)
        return pd.Series([brand, model])

    df_result[['추출_브랜드', '추출_모델명']] = df_result[col_name_new].apply(smart_extract)
    df_result['추출_브랜드'] = df_result['추출_브랜드'].fillna("").str.strip()
    df_result['추출_모델명'] = df_result['추출_모델명'].fillna("").str.strip()

    def keep_only_eng_num_words(text):
        return " ".join([w for w in str(text).split() if bool(re.search(r'[A-Za-z0-9]', w))])
    df_result['추출_모델명'] = df_result['추출_모델명'].apply(keep_only_eng_num_words)

    # check_registration
    def check_registration(model_name):
        clean_model = str(model_name).strip().lower()
        if not clean_model: return "확인 불가 (모델명 없음)"
        
        has_eng_or_num = bool(re.search(r'[a-z0-9]', clean_model))
        
        if len(clean_model) <= 2 or not has_eng_or_num:
            for store_model in store_models:
                if clean_model == store_model.strip(): return "✅ 기등록"
            return "❌ 미등록 (신규)"
            
        pattern = re.compile(rf'(?<![a-z0-9]){re.escape(clean_model)}(?![a-z0-9])')
        
        for store_model in store_models:
            if not store_model:
                continue
            if pattern.search(store_model):
                return "✅ 기등록"
        return "❌ 미등록 (신규)"

    df_result['스토어_등록여부'] = df_result['추출_모델명'].apply(check_registration)
    
    registered = df_result[df_result['스토어_등록여부'] == "✅ 기등록"]
    unregistered = df_result[df_result['스토어_등록여부'] != "✅ 기등록"]

    print(f"Total Original: {len(df_result)}")
    print(f"Registered (Filtered): {len(registered)}")
    print(f"Kept (Unregistered/Unknown): {len(unregistered)}")

    if len(registered) == 0:
        print("ERROR: 0 items were registered. Printing extracted models:")
        for idx, row in df_result.iterrows():
            print(f"Item {idx}: {row['상품명']}")
            print(f"   -> Extracted Model: '{row['추출_모델명']}'")
            print(f"   -> Registration Status: {row['스토어_등록여부']}")
            print()
