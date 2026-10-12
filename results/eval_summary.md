# Router Evaluation Benchmark Summary

- **Total Test Cases:** 24
- **Correct Predictions:** 24
- **Overall Accuracy:** 100.00%
- **Average Latency:** 0.02 ms
- **Failure Types:** None

## Performance per Insight Route

| Insight Route | TP | FP | FN | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `categorical_patterns` | 6 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| `distribution` | 4 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| `missing_data` | 3 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| `outliers` | 4 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| `relationships` | 4 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| `schema` | 3 | 0 | 0 | 1.00 | 1.00 | 1.00 |

## Sample Test Case Results

| ID | Dataset | Question Snippet | Expected | Predicted | Status |
| :-: | :--- | :--- | :--- | :--- | :-: |
| 1 | `ecommerce_sales.csv` | What is the average, median, and range of uni... | `distribution` | `distribution` | PASS |
| 2 | `ecommerce_sales.csv` | Are there any missing discount rates or unrec... | `missing_data` | `missing_data` | PASS |
| 3 | `ecommerce_sales.csv` | Which product categories represent the highes... | `categorical_patterns` | `categorical_patterns` | PASS |
| 4 | `ecommerce_sales.csv` | Is there a linear correlation between quantit... | `relationships` | `relationships` | PASS |
| 5 | `ecommerce_sales.csv` | Are there extreme transaction prices that loo... | `outliers` | `outliers` | PASS |
| 6 | `ecommerce_sales.csv` | What are the data types and column structures... | `schema` | `schema` | PASS |
| 7 | `ecommerce_sales.csv` | Show the descriptive statistics and spread of... | `distribution` | `distribution` | PASS |
| 8 | `ecommerce_sales.csv` | What are the most popular payment methods use... | `categorical_patterns` | `categorical_patterns` | PASS |
| 9 | `customer_churn.csv` | What is the statistical distribution and spre... | `distribution` | `distribution` | PASS |
| 10 | `customer_churn.csv` | Check if total charges contain null or blank ... | `missing_data` | `missing_data` | PASS |