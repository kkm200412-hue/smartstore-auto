import pandas as pd
import os

if os.path.exists("scraped_data.pkl"):
    df = pd.read_pickle("scraped_data.pkl")
    print("Scraped Data Length:", len(df))
    print(df.head())
else:
    print("scraped_data.pkl not found")
