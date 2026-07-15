import pandas as pd
import numpy as np

from backend.schemas.profile import ColumnProfile, ProfileResponse


def _safe_float(val) -> float | None:
    try:
        f = float(val)
        return None if np.isnan(f) or np.isinf(f) else f
    except Exception:
        return None


def profile_dataframe(df: pd.DataFrame, session_id: str) -> ProfileResponse:
    numeric_cols = list(df.select_dtypes(include="number").columns)
    categorical_cols = []
    datetime_cols = []

    for col in df.columns:
        if col in numeric_cols:
            continue
        # Try to detect datetime
        try:
            converted = pd.to_datetime(df[col], errors="coerce")
            if converted.notna().sum() / max(len(df), 1) > 0.7:
                datetime_cols.append(col)
                continue
        except Exception:
            pass
        categorical_cols.append(col)

    column_profiles = []
    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        non_null_count = len(series) - null_count
        null_pct = round(null_count / max(len(series), 1) * 100, 2)
        unique_count = int(series.nunique(dropna=True))

        cp = ColumnProfile(
            name=col,
            dtype=str(series.dtype),
            non_null_count=non_null_count,
            null_count=null_count,
            null_percentage=null_pct,
            unique_count=unique_count,
        )

        if col in numeric_cols:
            cp.mean = _safe_float(series.mean())
            cp.median = _safe_float(series.median())
            cp.std = _safe_float(series.std())
            cp.min = _safe_float(series.min())
            cp.max = _safe_float(series.max())
            cp.q25 = _safe_float(series.quantile(0.25))
            cp.q75 = _safe_float(series.quantile(0.75))
            cp.skewness = _safe_float(series.skew())
            cp.kurtosis = _safe_float(series.kurtosis())
        elif col in categorical_cols:
            top = (
                series.value_counts(dropna=True)
                .head(10)
                .reset_index()
                .rename(columns={col: "value", "count": "count"})
                .to_dict(orient="records")
            )
            # Handle both old and new pandas value_counts output
            if top and "value" not in top[0]:
                top = [{"value": str(r.get(col, r.get("index", ""))), "count": int(r.get("count", 0))} for r in top]
            else:
                top = [{"value": str(r.get("value", "")), "count": int(r.get("count", 0))} for r in top]
            cp.top_values = top

        column_profiles.append(cp)

    return ProfileResponse(
        session_id=session_id,
        rows=len(df),
        total_columns=len(df.columns),
        memory_usage_mb=round(df.memory_usage(deep=True).sum() / 1024 / 1024, 3),
        duplicate_rows=int(df.duplicated().sum()),
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
        datetime_columns=datetime_cols,
        columns=column_profiles,
    )
