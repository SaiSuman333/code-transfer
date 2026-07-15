import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import HTTPException

from backend.schemas.visualize import ChartRequest


def build_chart(df: pd.DataFrame, req: ChartRequest) -> dict:
    chart_type = req.chart_type
    title = req.title or chart_type.replace("_", " ").title()

    try:
        if chart_type == "histogram":
            if not req.x_column:
                raise HTTPException(400, "x_column required for histogram")
            fig = px.histogram(df, x=req.x_column, color=req.color_column, title=title)

        elif chart_type == "bar":
            if not req.x_column:
                raise HTTPException(400, "x_column required for bar chart")
            if req.y_column:
                agg = df.groupby(req.x_column)[req.y_column].mean().reset_index()
                fig = px.bar(agg, x=req.x_column, y=req.y_column, title=title)
            else:
                counts = df[req.x_column].value_counts().reset_index()
                counts.columns = [req.x_column, "count"]
                fig = px.bar(counts, x=req.x_column, y="count", title=title)

        elif chart_type == "bar_horizontal":
            if not req.x_column:
                raise HTTPException(400, "x_column required for horizontal bar chart")
            if req.y_column:
                agg = df.groupby(req.x_column)[req.y_column].mean().reset_index()
                agg = agg.sort_values(req.y_column, ascending=True)
                fig = px.bar(agg, x=req.y_column, y=req.x_column, orientation="h", title=title)
            else:
                counts = df[req.x_column].value_counts().reset_index()
                counts.columns = [req.x_column, "count"]
                counts = counts.sort_values("count", ascending=True)
                fig = px.bar(counts, x="count", y=req.x_column, orientation="h", title=title)
            fig.update_layout(yaxis={"categoryorder": "total ascending"})

        elif chart_type == "scatter":
            if not req.x_column or not req.y_column:
                raise HTTPException(400, "x_column and y_column required for scatter")
            fig = px.scatter(df, x=req.x_column, y=req.y_column, color=req.color_column, title=title)

        elif chart_type == "box":
            if not req.y_column:
                raise HTTPException(400, "y_column required for box plot")
            fig = px.box(df, x=req.x_column, y=req.y_column, color=req.color_column, title=title)

        elif chart_type == "line":
            if not req.x_column or not req.y_column:
                raise HTTPException(400, "x_column and y_column required for line chart")
            fig = px.line(df, x=req.x_column, y=req.y_column, color=req.color_column, title=title)

        elif chart_type == "correlation_heatmap":
            num_df = df.select_dtypes(include="number")
            if num_df.shape[1] < 2:
                raise HTTPException(400, "At least 2 numeric columns required for correlation heatmap")
            corr = num_df.corr().round(2)
            fig = px.imshow(
                corr,
                text_auto=True,
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                title=title or "Correlation Heatmap",
            )

        elif chart_type == "pie":
            if not req.x_column:
                raise HTTPException(400, "x_column required for pie chart")
            counts = df[req.x_column].value_counts().reset_index()
            counts.columns = [req.x_column, "count"]
            if len(counts) > 15:
                top = counts.head(15)
                other_count = counts.iloc[15:]["count"].sum()
                top = pd.concat([
                    top,
                    pd.DataFrame([{req.x_column: "Other", "count": other_count}])
                ], ignore_index=True)
                counts = top
            fig = px.pie(counts, names=req.x_column, values="count", title=title)

        elif chart_type == "donut":
            if not req.x_column:
                raise HTTPException(400, "x_column required for donut chart")
            counts = df[req.x_column].value_counts().reset_index()
            counts.columns = [req.x_column, "count"]
            fig = px.pie(counts, names=req.x_column, values="count", hole=0.45, title=title)

        elif chart_type == "violin":
            if not req.y_column:
                raise HTTPException(400, "y_column required for violin plot")
            fig = px.violin(
                df, x=req.x_column, y=req.y_column, color=req.color_column,
                box=True, points="outliers", title=title,
            )

        elif chart_type == "area":
            if not req.x_column or not req.y_column:
                raise HTTPException(400, "x_column and y_column required for area chart")
            fig = px.area(df, x=req.x_column, y=req.y_column, color=req.color_column, title=title)

        elif chart_type == "kde":
            if not req.x_column:
                raise HTTPException(400, "x_column required for KDE plot")
            fig = px.histogram(
                df, x=req.x_column, color=req.color_column,
                marginal="violin", histnorm="density",
                title=title or f"KDE Distribution — {req.x_column}",
            )

        elif chart_type == "scatter_matrix":
            num_df = df.select_dtypes(include="number")
            if num_df.shape[1] < 2:
                raise HTTPException(400, "At least 2 numeric columns required for scatter matrix")
            cols_to_use = list(num_df.columns[:6])
            fig = px.scatter_matrix(
                df, dimensions=cols_to_use, color=req.color_column,
                title=title or "Scatter Matrix (Pairplot)",
            )
            fig.update_traces(diagonal_visible=False, marker=dict(size=3, opacity=0.6))

        else:
            raise HTTPException(400, f"Unknown chart type: {chart_type}")

        fig.update_layout(template="plotly_white")
        # Use Plotly's own JSON encoder to strip numpy/datetime types,
        # then parse back to a plain Python dict.
        return json.loads(fig.to_json())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Chart generation failed: {str(e)}")
