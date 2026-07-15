from typing import Literal
from pydantic import BaseModel


class ChartRequest(BaseModel):
    chart_type: Literal[
        "histogram", "bar", "bar_horizontal", "scatter", "box", "line", "correlation_heatmap",
        "pie", "donut", "violin", "area", "kde", "scatter_matrix"
    ]
    x_column: str | None = None
    y_column: str | None = None
    color_column: str | None = None
    title: str | None = None


class ChartResponse(BaseModel):
    session_id: str
    chart_type: str
    plotly_json: dict
