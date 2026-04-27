import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional

# ── Paleta do tema ──────────────────────────────────────────────────
COLORS = {
    "primary":    "#4F8EF7",
    "secondary":  "#7C5CBF",
    "success":    "#3FB950",
    "warning":    "#D29922",
    "danger":     "#F85149",
    "accent":     "#58A6FF",
    "surface":    "#161B22",
    "text":       "#E6EDF3",
    "grid":       "#21262D",
}

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="JetBrains Mono, monospace"),
        colorway=[COLORS["primary"], COLORS["secondary"], COLORS["success"],
                  COLORS["warning"], COLORS["danger"], COLORS["accent"]],
        xaxis=dict(gridcolor=COLORS["grid"], linecolor=COLORS["grid"]),
        yaxis=dict(gridcolor=COLORS["grid"], linecolor=COLORS["grid"]),
        margin=dict(t=80, b=40, l=40, r=40),
        title=dict(
            y=1,
        )
    )
)


def apply_template(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    return fig


# ── Gráficos ─────────────────────────────────────────────────────────

def bar_horizontal(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None,
    top_n: int = 20,
) -> go.Figure:
    df_plot = df.nlargest(top_n, x) if x in df.columns else df.head(top_n)
    fig = px.bar(
        df_plot,
        x=x,
        y=y,
        orientation="h",
        title=title,
        color=color or x,
        color_continuous_scale=[[0, COLORS["secondary"]], [1, COLORS["primary"]]],
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
    fig.update_traces(marker_line_width=0)
    return apply_template(fig)


def bar_vertical(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color_val: Optional[str] = None,
) -> go.Figure:
    fig = px.bar(df, x=x, y=y, title=title, text=y)
    fig.update_traces(
        marker_color=color_val or COLORS["primary"],
        textposition="outside",
        marker_line_width=0,
    )
    fig.update_layout(showlegend=False)
    return apply_template(fig)


def pie_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str,
) -> go.Figure:
    fig = px.pie(
        df,
        names=names,
        values=values,
        title=title,
        hole=0.4,
        color_discrete_sequence=[
            COLORS["primary"], COLORS["secondary"], COLORS["success"],
            COLORS["warning"], COLORS["danger"],
        ],
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return apply_template(fig)


def scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    hover_name: Optional[str] = None,
    size: Optional[str] = None,
) -> go.Figure:
    fig = px.scatter(
        df, x=x, y=y, title=title,
        hover_name=hover_name,
        size=size,
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig.update_traces(marker=dict(opacity=0.75, line=dict(width=0)))
    return apply_template(fig)


def heatmap(
    matrix: pd.DataFrame,
    title: str,
) -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
        colorscale=[[0, COLORS["surface"]], [0.5, COLORS["secondary"]], [1, COLORS["primary"]]],
        showscale=True,
    ))
    fig.update_layout(title=title)
    return apply_template(fig)


def treemap(
    df: pd.DataFrame,
    path: list,
    values: str,
    title: str,
) -> go.Figure:
    fig = px.treemap(
        df, path=path, values=values, title=title,
        color=values,
        color_continuous_scale=[[0, COLORS["secondary"]], [1, COLORS["primary"]]],
    )
    fig.update_traces(textinfo="label+value")
    return apply_template(fig)


def metric_card_html(label: str, value: str, delta: Optional[str] = None, color: str = "#4F8EF7") -> str:
    """Retorna HTML para um card de métrica customizado."""
    delta_html = f'<div style="font-size:0.75rem;color:#3FB950;margin-top:4px">{delta}</div>' if delta else ""
    return f"""
    <div style="
        background: #161B22;
        border: 1px solid #21262D;
        border-left: 3px solid {color};
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 8px;
    ">
        <div style="font-size:0.75rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.08em">{label}</div>
        <div style="font-size:1.8rem;font-weight:700;color:#E6EDF3;font-family:monospace">{value}</div>
        {delta_html}
    </div>
    """
