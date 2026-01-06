import pandas as pd
import numpy as np
import plotly.graph_objs as go
from statsmodels.tsa.arima.model import ARIMA
# from Analytic_board.analysis

# --- NPS Calculation ---


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

def calculate_nps(data, category_column, rating_column, category):
    n_data = calculate_data_for_num(data, category_column, rating_column, category)
    # print(n_data.head())
    # category_data = data[data[category_column] == category]
    # if len(n_data) == 0:
    #     print("None hora hai")
    #     return None
    df = n_data[n_data[category_column] == category]

    def nps_label(rating):
        if rating >= 4:
            return 'Promoter'
        elif rating <= 2:
            return 'Detractor'
        else:
            return 'Passive'
    print("some")
    df['nps_label'] = df['avg_review_rating'].apply(nps_label(3))

    total = len(df)
    # print(df.head())
    # if total == 0:
    #     return 0
    nps_score = (
                        (df['nps_label'] == 'Promoter').sum() -
                        (df['nps_label'] == 'Detractor').sum()
                )# / total * 100
    print(f"the nps_score is:{nps_score}")
    return nps_score


def get_best_product(data, category_column, rating_column, category):
    print("last")
    category_data = data[data[category_column] == category]
    print(f"{category_data}\n")
    if len(category_data) == 0:
        print("None hora h")
        return None
    best_product = category_data.loc[category_data[rating_column].idxmax()]["Product Name"]
    print(f"maybe some details about best product:{best_product}")
    return best_product

def get_worst_product(data, category_column, rating_column, category):
    category_data = data[data[category_column] == category]
    if len(category_data) == 0: return None
    worst_product = category_data.loc[category_data[rating_column].idxmin()]["Product Name"]
    return worst_product

def generate_full_report(data):
    report = "### Product Analysis Report\n"
    categories = data['Category'].unique()
    for category in categories:
        nps = calculate_nps(data, 'Category', 'Rating', category)
        best_product = get_best_product(data, 'Category', 'Rating', category)
        worst_product = get_worst_product(data, 'Category', 'Rating', category)
        report += f"\nCategory: {category}\n"
        report += f"NPS Score: {nps:.2f}\n" if nps is not None else "NPS Score: N/A\n"
        report += f"Best Product: {best_product}\n"
        report += f"Worst Product: {worst_product}\n"
    return report

# --- Forecast ---
def forecast_nps(data, date_column, rating_column, months=6):
    data_nps = data[[date_column, rating_column]].dropna()
    if len(data_nps) == 0:
        return np.array([0]*months), pd.date_range(start=pd.Timestamp.today(), periods=months, freq='M')
    data_nps[date_column] = pd.to_datetime(data_nps[date_column])
    data_nps.sort_values(date_column, inplace=True)
    data_nps.set_index(date_column, inplace=True)
    model = ARIMA(data_nps[rating_column], order=(5,1,0))
    model_fit = model.fit()
    forecast = model_fit.forecast(steps=months)
    future_dates = pd.date_range(start=data_nps.index[-1] + pd.Timedelta(days=1), periods=months, freq='M')
    return forecast.values, future_dates

def generate_future_graphs(data, date_column, rating_column, months=6):
    forecast_values, future_dates = forecast_nps(data, date_column, rating_column, months)
    nps_graph = go.Figure()
    nps_graph.add_trace(go.Scatter(x=future_dates, y=forecast_values, mode='lines+markers', name='Forecasted NPS'))
    nps_graph.update_layout(title="Future NPS Forecast", xaxis_title="Month", yaxis_title="NPS")
    user_satisfaction_graph = go.Figure()
    user_satisfaction_graph.add_trace(go.Bar(x=future_dates, y=np.random.randint(50, 100, size=months), name='User Satisfaction'))
    user_satisfaction_graph.update_layout(title="User Satisfaction Forecast", xaxis_title="Month", yaxis_title="Score")
    return forecast_values, {'nps_graph': nps_graph, 'user_satisfaction_graph': user_satisfaction_graph}
