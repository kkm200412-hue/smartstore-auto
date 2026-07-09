import json
import os

if os.path.exists("store_models_cache.json"):
    with open("store_models_cache.json", "r", encoding="utf-8") as f:
        store_models = json.load(f)
    print(f"Loaded {len(store_models)} store models from cache.")
    print("First 5 models:", store_models[:5])
else:
    print("store_models_cache.json not found.")
