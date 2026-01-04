import pandas as pd
import matplotlib.pyplot as plt



def calculate_nps(data, category_column, rating_column, category):
    category_data = data[data[category_column] == category]
    promoters = category_data[category_data[rating_column] >= 9]
    detractors = category_data[category_data[rating_column] <= 6]
    nps_score = (len(promoters) - len(detractors)) / len(category_data) * 100
    return nps_score



def get_best_product(data, category_column, rating_column, category):
    category_data = data[data[category_column] == category]
    best_product = category_data.loc[category_data[rating_column].idxmax()]["Product Name"]
    return best_product



def get_worst_product(data, category_column, rating_column, category):
    category_data = data[data[category_column] == category]
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
        report += f"NPS Score: {nps:.2f}\n"
        report += f"Best Product: {best_product}\n"
        report += f"Worst Product: {worst_product}\n"

    return report
