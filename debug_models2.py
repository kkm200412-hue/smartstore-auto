import json
import os

if os.path.exists("store_models_cache.json"):
    with open("store_models_cache.json", "r", encoding="utf-8") as f:
        store_models = json.load(f)
    print("Shortest 10 models:")
    store_models.sort(key=len)
    for m in store_models[:20]:
        print(f"'{m}' (length {len(m)})")
