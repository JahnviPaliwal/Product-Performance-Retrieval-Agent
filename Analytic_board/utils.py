import pandas as pd


def dict_category(keys):
    if keys == 'forecast':
        print('forecast')
        return 'forecast'
    elif keys == 'best_product':
        print('best_product')
        return 'best_product'
    elif keys == 'worst_product':
        print('worst_product')
        return 'worst_product'
    elif keys == 'general':
        print('general')
        return 'general'
    elif keys == 'graphical':
        print('graphical')
        return 'graphical'


def dict_values(values):
    if values == 'present':
        return 'present'
    else:
        return 'future'


# def forecast_best_product():
#     kl


# def forecast_worst_product():
#     jk


# def future_graphs():
#     bp


# def future_summary():
#     bp


def components_of_file(data: pd.DataFrame):
    date_columns = []
    int_columns = []
    string_columns = []
    review_columns = []

    for col in data.columns:
        series = data[col]

        # ---- DATE / DATETIME DETECTION ----
        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(col)
            continue

        # Try parsing strings as datetime
        if series.dtype == object:
            try:
                parsed = pd.to_datetime(series.dropna(), errors="raise")
                date_columns.append(col)
                continue
            except:
                pass

        # ---- INTEGER COLUMNS ----
        if pd.api.types.is_integer_dtype(series):
            int_columns.append(col)

        # ---- STRING COLUMNS ----
        if pd.api.types.is_object_dtype(series):
            string_columns.append(col)

        # ---- REVIEW COLUMNS (ONLY VALUES 1–5) ----
        if pd.api.types.is_numeric_dtype(series):
            valid = series.dropna()
            if not valid.empty and valid.between(1, 5).all():
                review_columns.append(col)

    return {
        "date_columns": date_columns,
        # "integer_columns": int_columns,
        # "string_columns": string_columns,
        "review_columns": review_columns
    }
