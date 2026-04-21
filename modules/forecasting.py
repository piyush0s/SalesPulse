"""
Module: forecasting.py
Purpose: ARIMA forecasting — supports any number of weeks/days dynamically.
"""

import warnings
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")


def is_stationary(series: pd.Series, significance: float = 0.05) -> bool:
    result  = adfuller(series.dropna())
    p_value = result[1]
    return p_value < significance


def _auto_diff(series: pd.Series) -> tuple:
    d, s = 0, series.copy()
    while not is_stationary(s) and d < 2:
        s = s.diff().dropna()
        d += 1
    return s, d


def fit_and_forecast(series: pd.Series, periods: int = 8,
                     order: tuple = None, freq: str = "W") -> dict:
    """
    Fit ARIMA and return forecast for any number of periods.

    Parameters
    ----------
    series  : weekly or daily sales pd.Series
    periods : any integer — user-defined (e.g. 4, 12, 52 weeks or 7, 30, 90 days)
    freq    : 'W' weekly | 'D' daily
    """
    series = series.dropna()
    if len(series) < 10:
        raise ValueError(f"Series too short ({len(series)} points) for ARIMA. "
                         "Need at least 10 observations.")

    if order is None:
        _, d = _auto_diff(series)
        # Use more AR terms for longer series
        p = 3 if len(series) > 100 else 2
        order = (p, d, 1)

    print(f"[Forecasting] ARIMA{order} on {len(series)} "
          f"{'weekly' if freq=='W' else 'daily'} obs → {periods} periods ahead")

    model  = ARIMA(series, order=order)
    fitted = model.fit()

    fc          = fitted.get_forecast(steps=periods)
    fc_mean     = fc.predicted_mean.clip(lower=0)
    conf_int    = fc.conf_int().clip(lower=0)

    last_date        = series.index[-1]
    future_dates     = pd.date_range(start=last_date, periods=periods + 1, freq=freq)[1:]
    fc_mean.index    = future_dates
    conf_int.index   = future_dates

    return {
        "history":       series,
        "forecast":      fc_mean,
        "conf_int":      conf_int,
        "order":         order,
        "freq":          freq,
        "periods":       periods,
        "model_summary": fitted.summary().as_text(),
        "aic":           round(fitted.aic, 2),
        "hist_avg":      round(series[-min(8, len(series)):].mean(), 1),
        "fore_avg":      round(fc_mean.mean(), 1),
    }


def plot_forecast(result: dict, title: str = "Sales Forecast") -> go.Figure:
    hist, fc, ci = result["history"], result["forecast"], result["conf_int"]
    freq_label   = "Week" if result.get("freq","W") == "W" else "Day"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist.values, mode="lines",
        name="Historical", line=dict(color="#3B82F6", width=1.8),
    ))
    fig.add_trace(go.Scatter(
        x=list(ci.index) + list(ci.index[::-1]),
        y=list(ci.iloc[:, 1]) + list(ci.iloc[:, 0][::-1]),
        fill="toself", fillcolor="rgba(249,115,22,0.12)",
        line=dict(color="rgba(0,0,0,0)"), name="95% Confidence", showlegend=True
    ))
    fig.add_trace(go.Scatter(
        x=fc.index, y=fc.values, mode="lines+markers",
        name=f"Forecast ({result['periods']} {freq_label}s)",
        line=dict(color="#F97316", width=2.5, dash="dash"),
        marker=dict(size=6, symbol="diamond")
    ))
    fig.update_layout(
        title=title, xaxis_title=freq_label, yaxis_title="Sales Quantity",
        template="plotly_white", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
