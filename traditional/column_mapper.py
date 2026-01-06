def normalize_columns(df):
    """
    Normalize column names for flexible CSV support.
    """
    normalized = {}
    print("4")
    for col in df.columns:
        col_clean = col.strip().lower()
        if (
                "category" in col_clean
                or "categories" in col_clean
                or "catgories" in col_clean
        ):
            normalized["category"] = col
        elif "category" in col_clean:
            normalized["category"] = col
        elif "rating" in col_clean or "score" in col_clean:
            normalized["rating"] = col
        elif "product" in col_clean and "name" in col_clean:
            normalized["product_name"] = col
        elif "date" in col_clean or "month" in col_clean:
            normalized["date"] = col

    return normalized
