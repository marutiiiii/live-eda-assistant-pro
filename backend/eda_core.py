# backend/eda_core.py

import pandas as pd
import numpy as np
from scipy import stats

def detect_column_types(df: pd.DataFrame, cat_threshold: int = 20):
    """
    Decide for each column: is it numeric, categorical, or datetime?
    cat_threshold = if unique values <= this and not numeric ⇒ treat as categorical.
    """
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []

    for col in df.columns:
        series = df[col]

        # Try to detect datetime columns (if user forgot to parse dates)
        if np.issubdtype(series.dtype, np.datetime64):
            datetime_cols.append(col)
        elif np.issubdtype(series.dtype, np.number):
            numeric_cols.append(col)
        else:
            # Non-numeric: could be text/categorical
            if series.nunique() <= cat_threshold:
                categorical_cols.append(col)
            else:
                # Long free text – we still treat as categorical for now
                categorical_cols.append(col)

    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
    }

def dataset_overview(df: pd.DataFrame) -> dict:
    """
    Overall dataset stats: rows, columns, missing %, duplicates, etc.
    """
    n_rows, n_cols = df.shape
    total_cells = n_rows * n_cols
    missing_cells = int(df.isna().sum().sum())

    overview = {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "columns": list(df.columns),
        "missing_cells": missing_cells,
        "missing_pct": float((missing_cells / total_cells) * 100) if total_cells > 0 else 0.0,
        "duplicate_rows": int(df.duplicated().sum()),
    }
    return overview

def column_summary(df: pd.DataFrame) -> dict:
    """
    Per-column statistics:
    - For numeric: mean, std, min, max, quartiles, skew, kurtosis
    - For categorical: top values & their frequencies
    """
    col_types = detect_column_types(df)
    summaries = {}

    for col in df.columns:
        series = df[col]
        info = {
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_pct": float(series.isna().mean() * 100),
            "unique_count": int(series.nunique()),
        }

        if col in col_types["numeric"]:
            desc = series.describe()
            info.update({
                "mean": float(desc.get("mean", np.nan)),
                "std": float(desc.get("std", np.nan)),
                "min": float(desc.get("min", np.nan)),
                "max": float(desc.get("max", np.nan)),
                "25%": float(desc.get("25%", np.nan)),
                "50%": float(desc.get("50%", np.nan)),
                "75%": float(desc.get("75%", np.nan)),
                "skewness": float(series.skew(skipna=True)),
                "kurtosis": float(series.kurtosis(skipna=True)),
            })
        else:
            # Categorical / text-like
            top_vals = series.value_counts(normalize=True, dropna=True).head(3)
            info["top_values"] = {str(k): float(v) for k, v in top_vals.items()}

        summaries[col] = info

    return summaries

def detect_outliers_iqr(series: pd.Series):
    """
    Outliers using IQR rule:
    lower = Q1 - 1.5*IQR, upper = Q3 + 1.5*IQR
    Returns (indices, (lower_bound, upper_bound)).
    """
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    indices = np.where(mask)[0]
    return indices, (float(lower), float(upper))

def outlier_report(df: pd.DataFrame) -> dict:
    """
    For each numeric column, count outliers and bounds.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    report = {}

    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        idx, bounds = detect_outliers_iqr(s)
        report[col] = {
            "outlier_count": int(len(idx)),
            "outlier_pct": float(len(idx) / len(s) * 100),
            "lower_bound": bounds[0],
            "upper_bound": bounds[1],
        }

    return report

def correlation_analysis(df: pd.DataFrame, min_corr: float = 0.3) -> dict:
    """
    Compute correlation matrix for numeric columns,
    and extract strong pairs (|corr| >= min_corr).
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return {
            "corr_matrix": None,
            "strong_pairs": [],
        }

    corr = numeric_df.corr()
    strong_pairs = []
    cols = corr.columns

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr.iloc[i, j]
            if abs(val) >= min_corr:
                strong_pairs.append({
                    "col1": cols[i],
                    "col2": cols[j],
                    "corr": float(val),
                })

    return {
        # We'll use strong_pairs for storage; corr_matrix is more for visualization.
        "corr_matrix": corr,
        "strong_pairs": strong_pairs,
    }
