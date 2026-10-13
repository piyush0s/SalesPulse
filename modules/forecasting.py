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


def periods_for_horizon(last_date: pd.Timestamp, months: int,
                        freq: str = "W",
                        horizon_from: pd.Timestamp | None = None) -> int:
    """Return forecast steps through the selected calendar-month horizon."""
    if months < 1:
        raise ValueError("Forecast horizon must be at least one month.")

    last_date = pd.Timestamp(last_date)
    horizon_start = pd.Timestamp(horizon_from) if horizon_from is not None else last_date
    horizon_end = horizon_start + pd.DateOffset(months=months)
    if freq == "D":
        return max(0, (horizon_end.normalize() - last_date.normalize()).days)
    if freq == "W":
        first_future_day = last_date.normalize() + pd.Timedelta(days=1)
        return len(pd.date_range(
            start=first_future_day, end=horizon_end.normalize(), freq="W"))
    if freq == "MS":
        last_month = last_date.to_period("M").start_time
        final_month = horizon_end.to_period("M").start_time
        return max(
            0,
            (final_month.year - last_month.year) * 12
            + final_month.month - last_month.month,
        )
    raise ValueError(f"Unsupported forecast frequency: {freq}")


def is_stationary(series: pd.Series, significance: float = 0.05) -> bool:
    values = series.dropna()
    if len(values) < 4 or values.nunique() < 2:
        return True
    result  = adfuller(values)
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

    freq_label = {"W": "weekly", "D": "daily", "MS": "monthly"}.get(
        freq, "periodic")
    print(f"[Forecasting] ARIMA{order} on {len(series)} "
          f"{freq_label} obs -> {periods} periods ahead")

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


def plot_forecast(result: dict, title: str = "Sales Forecast",
                  show_history: bool = True) -> go.Figure:
    hist, fc, ci = result["history"], result["forecast"], result["conf_int"]
    freq_label = {"W": "Week", "D": "Day", "MS": "Month"}.get(
        result.get("freq", "W"), "Period")

    fig = go.Figure()
    if show_history:
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
    if not show_history and not fc.empty:
        if len(fc) == 1:
            if result.get("freq") == "MS":
                point_end = fc.index[0] + pd.DateOffset(months=1)
            elif result.get("freq") == "W":
                point_end = fc.index[0] + pd.Timedelta(days=7)
            else:
                point_end = fc.index[0] + pd.Timedelta(days=1)
            fig.update_xaxes(range=[fc.index[0], point_end])
        else:
            fig.update_xaxes(range=[fc.index[0], fc.index[-1]])
    fig.update_layout(
        title=title, xaxis_title=freq_label, yaxis_title="Sales Quantity",
        template="plotly_white", hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
