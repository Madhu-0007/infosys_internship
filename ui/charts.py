"""
ui/charts.py — Plotly chart builders for Sparklines, Divergence/Forecasts, and Sentiment Donut.
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.graph_objects as go


def render_sparkline_chart(series: pd.Series, is_winner: bool = True) -> go.Figure:
    """Renders minimalist 14-day sparkline."""
    color = "#22c55e" if is_winner else "#8b949e"
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(series.index),
            y=series.values,
            mode="lines",
            line=dict(color=color, width=2),
            hoverinfo="y+x",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=0, r=0, t=0, b=0),
        height=45,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        showlegend=False,
    )
    return fig


def render_divergence_chart(
    fk_hist: pd.Series,
    az_hist: pd.Series,
    dates: List[Any],
    fc_fk: Dict[str, Any],
    fc_az: Dict[str, Any],
    has_az: bool,
    diff: float,
    cheaper_store: str,
) -> go.Figure:
    """Renders 30-day historical divergence with 7-day Holt-Winters forecast bands."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=fk_hist.values,
            mode="lines",
            name="Flipkart (Historical)",
            line=dict(color="#38bdf8", width=2.5),
            hovertemplate="Flipkart: ₹%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=fc_fk["future_dates"],
            y=fc_fk["forecast_series"].values,
            mode="lines",
            name="Flipkart (7D Forecast)",
            line=dict(color="#38bdf8", width=2, dash="dash"),
            hovertemplate="Flipkart Forecast: ₹%{y:,.0f}<extra></extra>",
        )
    )

    if has_az:
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=az_hist.values,
                mode="lines",
                name="Amazon (Historical)",
                line=dict(color="#f59e0b", width=2.5),
                hovertemplate="Amazon: ₹%{y:,.0f}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=fc_az["future_dates"],
                y=fc_az["forecast_series"].values,
                mode="lines",
                name="Amazon (7D Forecast)",
                line=dict(color="#f59e0b", width=2, dash="dash"),
                hovertemplate="Amazon Forecast: ₹%{y:,.0f}<extra></extra>",
            )
        )
        active_fc = fc_az if diff > 0 else fc_fk
        fig.add_trace(
            go.Scatter(
                x=active_fc["future_dates"] + active_fc["future_dates"][::-1],
                y=list(active_fc["upper_band"].values) + list(active_fc["lower_band"].values)[::-1],
                fill="toself",
                fillcolor="rgba(34, 197, 94, 0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                name=f"{cheaper_store} Confidence Band",
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="#161b22",
        plot_bgcolor="#161b22",
        xaxis=dict(title="Timeline", showgrid=True, gridcolor="#21262d"),
        yaxis=dict(title="Price (₹ INR)", tickprefix="₹", tickformat=",", showgrid=True, gridcolor="#21262d"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def render_sentiment_donut(positive: int, neutral: int, negative: int) -> go.Figure:
    """Renders 3-way sentiment breakdown donut chart."""
    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Positive", "Neutral", "Negative"],
                values=[positive, neutral, negative],
                hole=0.6,
                marker=dict(colors=["#22c55e", "#8b949e", "#ef4444"]),
            )
        ]
    )
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=10, r=10, t=20, b=10),
        height=260,
        paper_bgcolor="#161b22",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15),
    )
    return fig
