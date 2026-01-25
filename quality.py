import numpy as np

def compute_data_quality(df):
    total_cells = df.shape[0] * df.shape[1]

    missing_ratio = df.isnull().sum().sum() / total_cells
    duplicate_ratio = df.duplicated().sum() / len(df)

    outlier_count = 0
    numeric_cols = df.select_dtypes(include="number")

    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        outlier_count += ((df[col] < q1 - 1.5 * iqr) |
                          (df[col] > q3 + 1.5 * iqr)).sum()

    outlier_ratio = (
        outlier_count / (len(df) * max(len(numeric_cols), 1))
    )

    score = 100 * (
        1
        - 0.4 * missing_ratio
        - 0.3 * duplicate_ratio
        - 0.3 * outlier_ratio
    )

    return max(0, round(score, 1))
