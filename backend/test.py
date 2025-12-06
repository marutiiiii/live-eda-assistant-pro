# backend/test_eda.py

import pandas as pd
from eda_core import (
    dataset_overview,
    column_summary,
    outlier_report,
    correlation_analysis,
    detect_column_types,
)
from insights_engine import (
    generate_overview_insights,
    generate_column_insights,
    generate_correlation_insights,
)

def main():
    # Create a tiny sample DataFrame
    data = {
        "age": [18, 20, 22, 100, 21, 19, 18, 17],
        "salary": [20000, 22000, 21000, 900000, 23000, 24000, 22000, 21000],
        "gender": ["M", "F", "M", "M", "F", "F", "M", "F"],
    }
    df = pd.DataFrame(data)

    print("DF:")
    print(df)

    overview = dataset_overview(df)
    col_types = detect_column_types(df)
    col_summaries = column_summary(df)
    outliers = outlier_report(df)
    corr_info = correlation_analysis(df)

    # merge outlier_pct into col_summaries for insights
    for col, info in col_summaries.items():
        if col in outliers:
            info["outlier_pct"] = outliers[col]["outlier_pct"]
        else:
            info["outlier_pct"] = 0.0

    print("\nOverview:", overview)
    print("\nColumn Types:", col_types)
    print("\nColumn Summaries:", col_summaries)
    print("\nOutliers:", outliers)
    print("\nStrong Correlations:", corr_info["strong_pairs"])

    ov_ins = generate_overview_insights(overview)
    col_ins = generate_column_insights(col_summaries)
    corr_ins = generate_correlation_insights(corr_info)

    print("\nOverview Insights:")
    for ins in ov_ins:
        print("-", ins)

    print("\nColumn Insights:")
    for ins in col_ins:
        print("-", ins)

    print("\nCorrelation Insights:")
    for ins in corr_ins:
        print("-", ins)

if __name__ == "__main__":
    main()
