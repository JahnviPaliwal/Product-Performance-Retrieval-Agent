import analysis_functions as af

INSIGHT_ROUTER = {
    "distribution": af.distribution,
    "missing_data": af.missing_data,
    "categorical_patterns": af.categorical_patterns,
    "relationships": af.relationships,
    "outliers": af.outliers,
    "schema": af.schema
}

def run_insight(insight_type, df):
    return INSIGHT_ROUTER[insight_type](df)
