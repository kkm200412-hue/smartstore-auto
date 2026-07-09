import pandas as pd
import re

df = pd.DataFrame({'상품명': ['슈나이더 접촉기 LADR2', 'NEW', '와이엠 릴레이 EVR100A-24S']})

def smart_extract(text):
    text = str(text)
    words = text.split()
    if not words: return pd.Series(["", ""])
    brand = words[0]
    model_words = [w for w in words[1:] if bool(re.search(r'[A-Za-z0-9]', w))]
    model = " ".join(model_words)
    return pd.Series([brand, model])

df[['추출_브랜드', '추출_모델명']] = df['상품명'].apply(smart_extract)

print("df after apply:")
print(df)
