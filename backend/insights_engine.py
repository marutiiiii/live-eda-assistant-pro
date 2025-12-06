# backend/insights_engine.py

def generate_overview_insights(overview: dict) -> list:
    """
    High-level comments about the whole dataset (missing values, duplicates, etc.)
    """
    insights = []
    miss = overview.get("missing_pct", 0.0)

    if miss > 30:
        insights.append(
            f"Dataset has a high missing value percentage ({miss:.1f}%). "
            "You will likely need strong cleaning strategies (dropping or imputing columns)."
        )
    elif miss > 10:
        insights.append(
            f"Dataset has moderate missing values ({miss:.1f}%). "
            "Consider using imputation methods before modeling."
        )
    else:
        insights.append(
            f"Dataset has low missing values ({miss:.1f}%), which is good for analysis."
        )

    dups = overview.get("duplicate_rows", 0)
    if dups > 0:
        insights.append(
            f"There are {dups} duplicate rows. Removing duplicates is recommended to avoid bias."
        )

    return insights

def generate_column_insights(col_summaries: dict) -> list:
    """
    Comments about each column: missing values, skewness, outliers, dominant categories.
    """
    insights = []

    for col, info in col_summaries.items():
        miss_pct = info.get("missing_pct", 0.0)

        # Missing value comments
        if miss_pct > 40:
            insights.append(
                f"Column '{col}' has very high missing values ({miss_pct:.1f}%). "
                "It might be a candidate to drop or replace with a proxy feature."
            )
        elif miss_pct > 10:
            insights.append(
                f"Column '{col}' has noticeable missing values ({miss_pct:.1f}%). "
                "Consider imputing values using mean/median/mode."
            )

        # Numeric column checks
        if "mean" in info:  # numeric
            skew = info.get("skewness", 0.0)
            if abs(skew) > 1:
                skew_side = "right" if skew > 0 else "left"
                insights.append(
                    f"Numeric column '{col}' is highly {skew_side}-skewed "
                    f"(skewness={skew:.2f}). Applying transformations (log/box-cox) may help."
                )

            out_pct = info.get("outlier_pct", 0.0)
            if out_pct > 10:
                insights.append(
                    f"Column '{col}' has many outliers ({out_pct:.1f}% of values). "
                    "Outlier handling (capping/removal) might improve model robustness."
                )

        # Categorical column checks
        if "top_values" in info:
            top_vals = info["top_values"]
            if top_vals:
                first_val, freq = list(top_vals.items())[0]
                insights.append(
                    f"In categorical column '{col}', value '{first_val}' is most frequent "
                    f"({freq*100:.1f}% of rows)."
                )

    return insights

def generate_correlation_insights(corr_info: dict) -> list:
    """
    Explain strong correlations between numeric columns.
    """
    pairs = corr_info.get("strong_pairs", [])
    insights = []

    if not pairs:
        insights.append("No strong linear correlations detected between numeric features.")
        return insights

    # Sort by absolute correlation strength
    pairs_sorted = sorted(pairs, key=lambda x: abs(x["corr"]), reverse=True)[:10]

    for p in pairs_sorted:
        relation = "positively" if p["corr"] > 0 else "negatively"
        insights.append(
            f"Columns '{p['col1']}' and '{p['col2']}' are strongly {relation} correlated "
            f"(corr={p['corr']:.2f}). They may carry similar information."
        )

    return insights
