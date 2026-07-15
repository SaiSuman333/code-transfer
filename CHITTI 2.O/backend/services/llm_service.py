"""
llm_service.py — Template-based explanation engine (no LLM API required).

Language is plain English, focused on anomalies and relationships rather than
raw numbers. Numbers are used only when they add meaning.
"""

from backend.schemas.insights import Insight


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _approx_fraction(pct: float) -> str:
    if pct >= 50:  return "more than half"
    if pct >= 33:  return "about a third"
    if pct >= 25:  return "about a quarter"
    if pct >= 20:  return "about 1 in 5"
    if pct >= 14:  return "about 1 in 7"
    if pct >= 10:  return "about 1 in 10"
    return f"around {pct:.0f}%"


def _r2_plain(r2: float) -> str:
    pct = round(r2 * 100)
    if r2 >= 0.9:
        return f"extremely well — it captures **{pct}%** of what drives the outcome"
    if r2 >= 0.75:
        return f"well — it explains **{pct}%** of the variation in the outcome"
    if r2 >= 0.5:
        return f"reasonably — it explains about **{pct}%** of the variation, with room to improve"
    if r2 >= 0.2:
        return f"weakly — only **{pct}%** of the variation is explained; the model is missing key patterns"
    return f"poorly — only **{pct}%** explained; this model is not reliable for decisions"


def _accuracy_plain(acc: float) -> str:
    pct = round(acc * 100)
    wrong = 100 - pct
    if pct >= 95:
        return f"gets it right **{pct}%** of the time — nearly perfect"
    if pct >= 85:
        return f"gets it right **{pct}%** of the time — a strong result"
    if pct >= 70:
        return f"gets it right **{pct}%** of the time — reasonable, but about 1 in {round(100/wrong)} predictions will be wrong"
    return f"gets it right only **{pct}%** of the time — too many mistakes for reliable use"


# ---------------------------------------------------------------------------
# Insight explanation
# ---------------------------------------------------------------------------

def explain_insights(insights: list[Insight], profile_summary: str, detail_level: str) -> str:
    if not insights:
        return (
            "**Everything looks clean.** No significant issues were found in this dataset. "
            "It appears ready for analysis or modelling."
        )

    # Group by category
    groups: dict[str, list[Insight]] = {}
    for ins in insights:
        groups.setdefault(ins.category, []).append(ins)

    sections = ["## What We Found In Your Data\n"]
    sections.append(
        "> *This summary focuses on patterns, anomalies, and relationships — not just numbers.*\n"
    )

    # ── Relationships ──
    if "correlation" in groups:
        sections.append("### Relationships Between Columns")
        for ins in groups["correlation"]:
            c1, c2 = ins.affected_columns[0], ins.affected_columns[1]
            r = ins.metric_value or 0
            move = "rise and fall together" if r > 0 else "move in opposite directions"
            strength = "very reliably" if abs(r) >= 0.9 else "consistently"
            sections.append(
                f"- **{c1}** and **{c2}** {strength} {move}. "
                + (
                    f"This is one of the strongest relationships in your dataset. "
                    f"If you're building a model, you probably only need one of them."
                    if abs(r) >= 0.9
                    else f"This pattern is strong enough to be meaningful — not just random noise."
                )
            )
        if detail_level == "detailed":
            sections.append(
                "\n> **What does this mean?** When two columns move together reliably, "
                "they likely measure the same underlying thing. Including both in a model "
                "can actually make it worse, not better — a phenomenon called multicollinearity."
            )

    # ── Anomalies / Outliers ──
    if "outlier" in groups:
        sections.append("\n### Unusual Values (Outliers)")
        for ins in groups["outlier"]:
            col = ins.affected_columns[0]
            pct = ins.metric_value or 0
            fraction = _approx_fraction(pct)
            sections.append(
                f"- **{col}** — {fraction} of values are unusually extreme. "
                + (
                    f"This is a large proportion and could seriously distort any analysis. Investigate these rows."
                    if pct > 20
                    else f"These could be genuine rare events or data entry errors — worth a quick review."
                )
            )

    # ── Distribution Shape ──
    if "skewness" in groups:
        sections.append("\n### Uneven Distributions")
        for ins in groups["skewness"]:
            col = ins.affected_columns[0]
            skew = ins.metric_value or 0
            if skew > 0:
                sections.append(
                    f"- **{col}** — a small number of very high values are pulling the average up. "
                    f"The average is not a fair summary of this column; the middle value (median) is better."
                )
            else:
                sections.append(
                    f"- **{col}** — a small number of very low values are dragging the average down. "
                    f"Use the median instead of the mean for a truer picture."
                )

    # ── Data Quality ──
    quality_items = []
    if "missing_data" in groups:
        for ins in groups["missing_data"]:
            col = ins.affected_columns[0]
            pct = ins.metric_value or 0
            fraction = _approx_fraction(pct)
            quality_items.append(
                f"**{col}** is missing {fraction} of its values"
                + (" — too incomplete to rely on." if pct > 50 else " — consider filling or removing it.")
            )
    if "duplicate" in groups:
        ins = groups["duplicate"][0]
        pct = ins.metric_value or 0
        quality_items.append(
            f"**{ins.metric_value and round(ins.metric_value) or '?'} duplicate rows** detected "
            f"({_approx_fraction(pct)} of the dataset) — safe to remove before modelling."
        )
    if quality_items:
        sections.append("\n### Data Quality Issues")
        for item in quality_items:
            sections.append(f"- {item}")

    # ── Structural Issues ──
    dist_insights = groups.get("distribution", [])
    structural = [i for i in dist_insights if "cardinality" in i.title.lower()
                  or "never changes" in i.title.lower()
                  or "barely changes" in i.title.lower()
                  or "dominated" in i.title.lower()]
    if structural:
        sections.append("\n### Columns to Watch")
        for ins in structural:
            sections.append(f"- {ins.description}")

    # ── Normality ──
    nonnormal = [i for i in dist_insights if "bell-curve" in i.title.lower()
                 or "normal" in i.title.lower()]
    if nonnormal and detail_level == "detailed":
        sections.append("\n### Distribution Shape (For Modelling)")
        for ins in nonnormal:
            col = ins.affected_columns[0]
            sections.append(
                f"- **{col}** does not follow a bell-curve distribution. "
                f"Models that assume normality (like linear regression) may perform better "
                f"if you apply a log or square-root transformation to this column first."
            )

    # ── Footer ──
    critical = sum(1 for i in insights if i.severity == "critical")
    warnings = sum(1 for i in insights if i.severity == "warning")
    if critical > 0:
        footer = f"**Action needed:** {critical} critical issue{'s' if critical > 1 else ''} found — address these before using the data in any model or report."
    elif warnings > 0:
        footer = f"**No blockers found**, but {warnings} warning{'s' if warnings > 1 else ''} worth reviewing before proceeding."
    else:
        footer = "**Data looks usable.** Only minor observations — nothing that should block analysis."

    sections.append(f"\n---\n{footer}")
    return "\n\n".join(sections)


def answer_question(question: str, data_context: str, conversation_history: list[dict]) -> str:
    return "The Ask feature requires an LLM API and has been disabled in this version."


# ---------------------------------------------------------------------------
# Prediction explanation
# ---------------------------------------------------------------------------

def explain_prediction(
    metrics: dict,
    feature_importances: list,
    task_type: str,
    target_column: str,
    model_name: str,
) -> str:
    sections = [f"## Prediction Summary: '{target_column}'\n"]

    # ── What the model does ──
    sections.append(
        f"> A **Random Forest** model was trained to predict **{target_column}**. "
        f"It learns by building hundreds of decision trees and combining their answers."
    )

    # ── How well it performed ──
    sections.append("### How Well Did It Do?")
    if task_type == "regression":
        r2   = metrics.get("r2", 0)
        rmse = metrics.get("rmse", 0)
        mae  = metrics.get("mae", 0)
        sections.append(
            f"The model performs **{_r2_plain(r2)}**. "
            f"On average, its predictions are off by about **{mae:.2g} units** from the real value. "
            + (
                f"The larger error measure (RMSE = {rmse:.2g}) is higher because it penalises big mistakes more — "
                f"meaning occasional large errors are pulling it up."
                if rmse > mae * 1.3 else
                f"The errors are fairly consistent — no single prediction is wildly off."
            )
        )
    else:
        acc  = metrics.get("accuracy", 0)
        f1   = metrics.get("f1_weighted", 0)
        prec = metrics.get("precision_weighted", 0)
        rec  = metrics.get("recall_weighted", 0)
        sections.append(
            f"The model **{_accuracy_plain(acc)}**. "
        )
        if abs(prec - rec) > 0.1:
            if prec > rec:
                sections.append(
                    f"When it does make a prediction, it's usually right (high precision). "
                    f"But it misses some cases it should have caught (lower recall). "
                    f"Think of it as cautious — it only speaks up when it's confident."
                )
            else:
                sections.append(
                    f"It catches most cases (high recall), but sometimes flags things incorrectly (lower precision). "
                    f"Think of it as sensitive — it rarely misses, but occasionally raises false alarms."
                )
        else:
            sections.append(
                f"It strikes a good balance between catching real cases and avoiding false alarms (F1 = {f1:.2f})."
            )

    # ── What drives the prediction ──
    if feature_importances:
        sections.append("\n### What Drives the Prediction?")
        top   = feature_importances[:10]
        top1  = top[0]
        top1_name = top1["feature"].replace("num__", "").replace("cat__", "")
        total_top3 = sum(f["importance"] for f in top[:3])

        sections.append(
            f"The single biggest factor is **{top1_name}** — it has more influence on the prediction "
            f"than any other column. "
            + (
                f"Together, the top 3 features account for most of what the model uses to decide."
                if total_top3 > 0.5 else
                f"The model spreads its attention fairly evenly — no single column dominates."
            )
        )

        # Top features in plain language
        for i, f in enumerate(top[1:5], 2):
            name = f["feature"].replace("num__", "").replace("cat__", "")
            rel  = f["importance"] / (top1["importance"] + 1e-9)
            if rel > 0.75:
                desc = "almost as important as the top feature"
            elif rel > 0.4:
                desc = "notably influential"
            elif rel > 0.15:
                desc = "has some influence"
            else:
                desc = "plays a minor supporting role"
            sections.append(f"- **{name}** — {desc}")

        if len(top) > 5:
            sections.append(
                f"- *...plus {len(top) - 5} more columns contributing smaller amounts.*"
            )

    # ── What to do next ──
    sections.append("\n### What Should You Do Next?")
    if task_type == "regression":
        r2 = metrics.get("r2", 0)
        if r2 >= 0.75:
            sections.append(
                "- The model is performing well. You can start using its predictions with reasonable confidence."
            )
            sections.append(
                "- Double-check that none of the top features are ones that would only be available *after* the fact — that would be data leakage."
            )
        else:
            sections.append(
                "- The model is not yet reliable enough for high-stakes decisions. Try adding more relevant columns or collecting more data."
            )
            sections.append(
                "- Look at the top features — if they seem unrelated to the outcome, something may be off with the data."
            )
    else:
        acc = metrics.get("accuracy", 0)
        if acc >= 0.85:
            sections.append(
                "- Strong accuracy. Validate on a new batch of data to confirm the model generalises well."
            )
        else:
            sections.append(
                "- Consider gathering more data or adding more informative columns to improve accuracy."
            )
            sections.append(
                "- Also check whether the classes are imbalanced — if one category vastly outnumbers others, the model may be cheating."
            )

    sections.append(
        "- Always test model predictions against real outcomes before using them for decisions."
    )

    return "\n\n".join(sections)
