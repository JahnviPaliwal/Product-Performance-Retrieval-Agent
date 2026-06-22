"""
document_processors/csv_processor.py
Convert CSV to text representation for RAG, and expose DataFrame for analytics.
"""
import pandas as pd
import io


def load_dataframe(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def extract_text(file_path: str) -> str:
    df = load_dataframe(file_path)
    buf = io.StringIO()
    buf.write(f"CSV Dataset – {len(df)} rows × {len(df.columns)} columns\n")
    buf.write(f"Columns: {', '.join(df.columns.tolist())}\n\n")
    buf.write("Statistical Summary:\n")
    buf.write(df.describe(include="all").to_string())
    buf.write("\n\nFirst 20 rows:\n")
    buf.write(df.head(20).to_string(index=False))
    return buf.getvalue()
