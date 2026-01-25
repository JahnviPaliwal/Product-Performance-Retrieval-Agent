import numpy as np

def distribution(df):
    return df.describe()

def missing_data(df):
    return df.isnull().sum()

def categorical_patterns(df):
    return {
        col: df[col].value_counts().head(5)
        for col in df.select_dtypes(include="object")
    }

def relationships(df):
    return df.select_dtypes(include="number").corr()

def outliers(df):
    summary = {}
    for col in df.select_dtypes(include="number"):
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        summary[col] = int(
            ((df[col] < q1 - 1.5 * iqr) |
             (df[col] > q3 + 1.5 * iqr)).sum()
        )
    return summary

def schema(df):
    return df.dtypes
