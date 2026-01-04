import pandas as pd
import numpy as np
import plotly.graph_objs as go
from statsmodels.tsa.arima.model import ARIMA


# Function to forecast NPS score using ARIMA model
def forecast_nps(data, date_coloumn, rating_column, months=6): #category
    # category_data = data[data[category_column] == category]
    # category_data = category_data[['Date', rating_column]].dropna()

    data_nps = data[date_coloumn, rating_column].dropna()

    # Convert the 'Date' column to datetime if necessary
    data_nps[date_coloumn] = pd.to_datetime(data_nps[date_coloumn])
    data_nps.set_index(date_coloumn, inplace=True)

    # Fit ARIMA model
    model = ARIMA(data_nps[rating_column], order=(5, 1, 0))
    model_fit = model.fit()

    # Forecast for future months
    forecast = model_fit.forecast(steps=months)

    future_dates = pd.date_range(start=data_nps.index[-1], periods=months + 1, freq='M')[1:]

    future_nps = np.mean(forecast)
    return future_nps


# Function to generate future graphs (NPS & User Satisfaction)
def generate_future_graphs(data, category_column, rating_column, category, months=6):
    future_nps = forecast_nps(data, category_column, rating_column, category, months)

    # Generate sample graphs (replace this with actual model-based graphs)
    nps_happy_graph = go.Figure()
    nps_happy_graph.add_trace(
        go.Scatter(x=np.arange(months), y=np.random.randn(months), mode='lines', name='NPS Over Time'))

    user_satisfaction_graph = go.Figure()
    user_satisfaction_graph.add_trace(go.Bar(x=np.arange(months), y=np.random.randn(months), name='User Satisfaction'))

    return future_nps, {'nps_happy_graph': nps_happy_graph, 'user_satisfaction_graph': user_satisfaction_graph}






