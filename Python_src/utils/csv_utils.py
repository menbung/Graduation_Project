import pandas as pd
from pathlib import Path

def save_df_csv(df: pd.DataFrame, path: str, index: bool = False):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index, encoding='utf-8-sig')

def load_df_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding='utf-8-sig')
