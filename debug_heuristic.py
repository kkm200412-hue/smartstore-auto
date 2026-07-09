import pandas as pd
import re

df = pd.read_pickle('scraped_data.pkl')

def extract(text):
    # Find all contiguous words that contain English/Numbers/hyphens/slashes/dots
    words = re.findall(r'[A-Za-z0-9\-\/\.]+', str(text))
    # Filter words that contain BOTH at least one letter AND at least one number
    candidates = [w for w in words if re.search(r'[A-Za-z]', w) and re.search(r'[0-9]', w)]
    
    if candidates:
        return candidates[0]
    elif words:
        return words[0]
    else:
        return ""

print(df['상품명'].apply(extract).tolist())
