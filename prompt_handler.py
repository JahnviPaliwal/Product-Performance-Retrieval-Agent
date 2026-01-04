from calculations import (
    calculate_nps,
    get_best_product,
    get_worst_product,
    generate_full_report,
    generate_future_graphs
)
from column_mapper import normalize_columns


def process_plan(plan, df):
    results = {}

    column_map = normalize_columns(df)

    # REQUIRED columns check
    if "category" not in column_map or "rating" not in column_map:
        return {
            "error": "Dataset must contain category and rating columns"
        }

    category_col = column_map["category"]
    rating_col = column_map["rating"]
    product_col = column_map.get("product_name")
    date_col = column_map.get("date")

    for action in plan.get("actions", []):
        action_type = action["type"]
        category = action.get("category")
        months = action.get("months", 3)

        if action_type == "GET_NPS":
            results["nps"] = calculate_nps(
                df, category_col, rating_col, category
            )

        elif action_type == "GET_BEST_PRODUCT" and product_col:
            results["best_product"] = get_best_product(
                df, category_col, rating_col, category
            )

        elif action_type == "GET_WORST_PRODUCT" and product_col:
            results["worst_product"] = get_worst_product(
                df, category_col, rating_col, category
            )

        elif action_type == "GET_SUMMARY":
            results["summary"] = generate_full_report(df)

        elif action_type in ["FORECAST", "GET_GRAPH"] and date_col:
            forecast, graphs = generate_future_graphs(
                df, date_col, rating_col, months
            )
            results["forecast"] = forecast
            results["graphs"] = graphs

    return results
