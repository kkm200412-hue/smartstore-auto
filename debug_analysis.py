import pandas as pd
import os

if os.path.exists("last_analysis.pkl"):
    df = pd.read_pickle("last_analysis.pkl")
    print("last_analysis Data Length:", len(df))
    for col in df.columns:
        print(f"Column: {col}")
    
    if not df.empty and '추출_모델명' in df.columns:
        print("First 10 Models extracted:")
        print(df['추출_모델명'].head(10).tolist())
        print("First 10 Original Names:")
        print(df['상품명'].head(10).tolist())
else:
    print("last_analysis.pkl not found")
