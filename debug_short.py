import json

with open("store_models_cache.json", "r", encoding="utf-8") as f:
    store_models = json.load(f)

short_models = [m for m in store_models if len(m) < 4]
print(f"Number of models < 4 chars: {len(short_models)}")
print(short_models)
