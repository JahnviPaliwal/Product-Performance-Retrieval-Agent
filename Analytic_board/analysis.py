import pandas as pd
import matplotlib.pyplot as plt

def calculate_data_for_num(data, category_column, rating_column, category):
    df_filtered = data[data[category_column] == category]
    short_df = (
        df_filtered[[category_column, rating_column]]  # name
        .dropna(subset=[category_column, rating_column])
        .groupby([category_column], as_index=False)
        .agg(avg_review_rating=(rating_column, 'mean'),
             count_rating_1=(rating_column, lambda x: (x == 1).sum()),
             count_rating_5=(rating_column, lambda x: (x == 5).sum())
             ).reset_index().sort_values([category_column, 'avg_review_rating'], ascending=[True, False]))
    return short_df

def preprocess_reviews(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    required_cols = [
        'categories',
        # 'name',
        'avg_review_rating',
        'count_rating_1',
        'count_rating_5'
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    df['avg_review_rating'] = pd.to_numeric(df['avg_review_rating'], errors='coerce').fillna(1)
    df['count_rating_1'] = pd.to_numeric(df['count_rating_1'], errors='coerce').fillna(0)
    df['count_rating_5'] = pd.to_numeric(df['count_rating_5'], errors='coerce').fillna(0)

    return df

def calculate_nps(data, category_column, rating_column, category):
    df = preprocess_reviews(data)
    df = df[df[category_column] == category]

    def nps_label(rating):
        if rating >= 4:
            return 'Promoter'
        elif rating <= 2:
            return 'Detractor'
        else:
            return 'Passive'

    df['nps_label'] = df['avg_review_rating'].apply(nps_label)

    total = len(df)
    if total == 0:
        return 0
    nps_score = (
                        (df['nps_label'] == 'Promoter').sum() -
                        (df['nps_label'] == 'Detractor').sum()
                ) / total * 100
    print(f"the nps_score is:{nps_score}")
    return nps_score



# def get_best_product(data, category_column, rating_column, category):
#     category_data = data[data[category_column] == category]
#     best_product = category_data.loc[category_data[rating_column].idxmax()]["Product Name"]
#     return best_product
#
#
#
# def get_worst_product(data, category_column, rating_column, category):
#     category_data = data[data[category_column] == category]
#     worst_product = category_data.loc[category_data[rating_column].idxmin()]["Product Name"]
#     return worst_product


def best_worst_products(df, category, top_n=2):
    df = preprocess_reviews(df)
    df = df[df['categories'] == category]

    best = df.sort_values('count_rating_5', ascending=False).head(top_n)
    worst = df.sort_values('count_rating_1', ascending=False).head(top_n)

    return best, worst



# def generate_full_report(data):
#     report = "### Product Analysis Report\n"
#     categories = data['Category'].unique()
#
#     for category in categories:
#         nps = calculate_nps(data, 'Category', 'Rating', category)
#         best_product,worst_product = best_worst_products(data, category)
#
#
#         report += f"\nCategory: {category}\n"
#         report += f"NPS Score: {nps:.2f}\n"
#         report += f"Best Product: {best_product}\n"
#         report += f"Worst Product: {worst_product}\n"
#
#     return report
