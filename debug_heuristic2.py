import pandas as pd
import re

df = pd.read_pickle('scraped_data.pkl')

def smart_extract(text):
    text = str(text)
    words = text.split()
    if not words: return pd.Series(["", ""])
    
    brand = words[0]
    
    # Strip non-alphanumeric (except hyphens, slashes, dots) for model candidates
    clean_words = [re.sub(r'[^A-Za-z0-9\-\/\.]', '', w) for w in words[1:]]
    # Filter for words containing BOTH at least one letter AND at least one number
    candidates = [w for w in clean_words if re.search(r'[A-Za-z]', w) and re.search(r'[0-9]', w)]
    
    if candidates:
        model = candidates[0]
    else:
        # Fallback: the first non-empty clean word
        fallback = [w for w in clean_words if w]
        model = fallback[0] if fallback else ""
        
    return pd.Series([brand, model])

result = df['상품명'].apply(smart_extract)
result.columns = ['brand', 'model']
result['original'] = df['상품명']

print(result.head(25))
