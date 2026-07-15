from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy import stats

from backend.schemas.insights import Insight, InsightsResponse


# ---------------------------------------------------------------------------
# Plain-English helpers
# ---------------------------------------------------------------------------

def _approx_fraction(pct: float) -> str:
    """Turn a percentage into a human-readable fraction."""
    if pct >= 50:  return "more than half"
    if pct >= 33:  return "about 1 in 3"
    if pct >= 25:  return "about 1 in 4"
    if pct >= 20:  return "about 1 in 5"
    if pct >= 14:  return "about 1 in 7"
    if pct >= 10:  return "about 1 in 10"
    if pct >= 5:   return "roughly 1 in 20"
    return f"about {pct:.1f}%"


def _correlation_strength(r: float) -> str:
    a = abs(r)
    if a >= 0.9: return "almost perfectly"
    if a >= 0.7: return "strongly"
    if a >= 0.5: return "moderately"
    return "weakly"


def _direction_phrase(r: float) -> str:
    return "in the same direction" if r > 0 else "in opposite directions"


def _direction_example(r: float, c1: str, c2: str) -> str:
    if r > 0:
        return f"When **{c1}** goes up, **{c2}** tends to go up too."
    return f"When **{c1}** goes up, **{c2}** tends to go down."


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def generate_insights(df: pd.DataFrame, session_id: str) -> InsightsResponse:
    insights: list[Insight] = []
    num_df = df.select_dtypes(include="number")
    num_cols = list(num_df.columns)
    cat_cols = list(df.select_dtypes(include="object").columns)

    # ── 1. Correlations ──────────────────────────────────────────────────────
    if len(num_cols) >= 2:
        corr = num_df.corr()
        for i in range(len(num_cols)):
            for j in range(i + 1, len(num_cols)):
                c1, c2 = num_cols[i], num_cols[j]
                r = corr.loc[c1, c2]
                if np.isnan(r) or abs(r) < 0.7:
                    continue
                strength = _correlation_strength(r)
                direction = _direction_phrase(r)
                example = _direction_example(r, c1, c2)
                severity = "critical" if abs(r) >= 0.9 else "warning"
                insights.append(Insight(
                    category="correlation",
                    severity=severity,
                    title=f"'{c1}' and '{c2}' move {strength} {direction}",
                    description=(
                        f"**{c1}** and **{c2}** are {strength} linked. "
                        f"{example} "
                        f"This relationship is {'very reliable' if abs(r) >= 0.9 else 'consistent enough to be meaningful'}. "
                        f"If you're building a model, using both columns may be redundant — one might be enough."
                    ),
                    affected_columns=[c1, c2],
                    metric_value=round(r, 4),
                ))

    # ── 2. Outliers ───────────────────────────────────────────────────────────
    for col in num_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_count = int(((series < lower) | (series > upper)).sum())
        outlier_pct = outlier_count / len(series) * 100
        if outlier_pct <= 5:
            continue
        fraction = _approx_fraction(outlier_pct)
        severity = "critical" if outlier_pct > 20 else "warning"
        insights.append(Insight(
            category="outlier",
            severity=severity,
            title=f"'{col}' has an unusual number of extreme values",
            description=(
                f"**{fraction}** of the values in **{col}** are unusually high or low — "
                f"far outside the typical range. "
                f"These extreme values can distort averages and confuse machine learning models. "
                f"{'This is a large proportion and worth investigating closely.' if outlier_pct > 20 else 'Worth reviewing to check if they are genuine data or entry errors.'}"
            ),
            affected_columns=[col],
            metric_value=round(outlier_pct, 2),
        ))

    # ── 3. Skewness ───────────────────────────────────────────────────────────
    for col in num_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        skew = series.skew()
        if np.isnan(skew) or abs(skew) <= 1.0:
            continue
        severity = "warning" if abs(skew) > 2 else "info"
        if skew > 0:
            desc = (
                f"Most values in **{col}** are on the lower end, but a few very large values "
                f"are pulling the average upward. "
                f"The average alone is misleading here — the median (middle value) is a better summary."
            )
            title = f"'{col}' is dominated by a few very large values"
        else:
            desc = (
                f"Most values in **{col}** are on the higher end, but a few very small values "
                f"are pulling the average down. "
                f"The median (middle value) gives a more honest picture than the average here."
            )
            title = f"'{col}' is dominated by a few very small values"
        insights.append(Insight(
            category="skewness",
            severity=severity,
            title=title,
            description=desc,
            affected_columns=[col],
            metric_value=round(skew, 4),
        ))

    # ── 4. Missing Data ───────────────────────────────────────────────────────
    for col in df.columns:
        null_pct = df[col].isna().sum() / max(len(df), 1) * 100
        if null_pct <= 10:
            continue
        fraction = _approx_fraction(null_pct)
        severity = "critical" if null_pct > 50 else "warning"
        insights.append(Insight(
            category="missing_data",
            severity=severity,
            title=f"'{col}' is missing a lot of data",
            description=(
                f"**{fraction}** of the entries in **{col}** are blank. "
                f"{'More than half the data is missing — this column may not be reliable enough to use.' if null_pct > 50 else 'This is above the safe threshold. Consider filling in the blanks (imputation) or dropping this column before analysis.'}"
            ),
            affected_columns=[col],
            metric_value=round(null_pct, 2),
        ))

    # ── 5. Duplicate Rows ─────────────────────────────────────────────────────
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        dup_pct = dup_count / len(df) * 100
        fraction = _approx_fraction(dup_pct)
        severity = "critical" if dup_pct > 20 else "warning"
        insights.append(Insight(
            category="duplicate",
            severity=severity,
            title=f"{dup_count} rows appear more than once",
            description=(
                f"**{fraction}** of the rows in this dataset are exact duplicates of another row. "
                f"Duplicates can make a model over-confident by training on the same example multiple times. "
                f"It's usually safe to remove them before analysis."
            ),
            affected_columns=[],
            metric_value=round(dup_pct, 2),
        ))

    # ── 6. Normality Test ─────────────────────────────────────────────────────
    for col in num_cols:
        series = df[col].dropna()
        # Shapiro-Wilk reliable up to ~5000 rows; use D'Agostino above that
        if len(series) < 8:
            continue
        try:
            if len(series) <= 5000:
                _, p = stats.shapiro(series.sample(min(len(series), 5000), random_state=42))
            else:
                _, p = stats.normaltest(series)
            if p < 0.01:
                insights.append(Insight(
                    category="distribution",
                    severity="info",
                    title=f"'{col}' does not follow a normal (bell-curve) distribution",
                    description=(
                        f"**{col}** is not normally distributed — its values are not spread "
                        f"symmetrically around the centre like a bell curve. "
                        f"This matters if you plan to use statistical tests or models that assume normality "
                        f"(like linear regression). A log or square-root transformation may help."
                    ),
                    affected_columns=[col],
                    metric_value=round(p, 6),
                ))
        except Exception:
            pass

    # ── 7. Low Variance ───────────────────────────────────────────────────────
    for col in num_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        if series.max() == series.min():
            insights.append(Insight(
                category="distribution",
                severity="warning",
                title=f"'{col}' has only one unique value — it never changes",
                description=(
                    f"Every row in **{col}** has the exact same value. "
                    f"A column that never changes carries no information and should be removed — "
                    f"it cannot help any model or analysis."
                ),
                affected_columns=[col],
                metric_value=0.0,
            ))
        elif series.std() / (abs(series.mean()) + 1e-9) < 0.01:
            insights.append(Insight(
                category="distribution",
                severity="info",
                title=f"'{col}' barely changes across rows",
                description=(
                    f"**{col}** has very little variation — almost all rows have nearly the same value. "
                    f"Columns with low variation rarely help a model learn anything useful and can often be removed."
                ),
                affected_columns=[col],
                metric_value=round(series.std(), 6),
            ))

    # ── 8. High Cardinality ───────────────────────────────────────────────────
    for col in cat_cols:
        unique_count = df[col].nunique(dropna=True)
        unique_ratio = unique_count / max(len(df), 1)
        if unique_count > 50 and unique_ratio > 0.5:
            insights.append(Insight(
                category="distribution",
                severity="warning",
                title=f"'{col}' has too many unique text values",
                description=(
                    f"**{col}** contains **{unique_count} different values** — more than half the rows are unique. "
                    f"This is called high cardinality. Columns like IDs, names, or free-text fields "
                    f"are usually not useful for analysis or modelling and can be safely ignored."
                ),
                affected_columns=[col],
                metric_value=round(unique_ratio * 100, 1),
            ))

    # ── 9. Class Imbalance ────────────────────────────────────────────────────
    for col in cat_cols:
        vc = df[col].value_counts(normalize=True, dropna=True)
        if len(vc) < 2 or len(vc) > 20:
            continue
        dominant_pct = vc.iloc[0] * 100
        if dominant_pct >= 85:
            dominant_val = vc.index[0]
            fraction = _approx_fraction(dominant_pct)
            insights.append(Insight(
                category="distribution",
                severity="warning",
                title=f"'{col}' is dominated by one value: '{dominant_val}'",
                description=(
                    f"**{fraction}** of all rows in **{col}** have the value **'{dominant_val}'**. "
                    f"This heavy imbalance means a model could score well just by always guessing "
                    f"'{dominant_val}' — without actually learning anything. "
                    f"Consider whether this column is useful as a prediction target."
                ),
                affected_columns=[col],
                metric_value=round(dominant_pct, 2),
            ))

    # Sort: critical → warning → info
    order = {"critical": 0, "warning": 1, "info": 2}
    insights.sort(key=lambda x: order[x.severity])

    return InsightsResponse(
        session_id=session_id,
        insights=insights,
        total=len(insights),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
