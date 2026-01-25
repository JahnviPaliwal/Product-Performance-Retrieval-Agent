import pandas as pd

def profile_dataframe(df: pd.DataFrame):
    return {
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": [
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "nulls": int(df[col].isna().sum()),
                "unique": int(df[col].nunique())
            }
            for col in df.columns
        ]
    }
