"""
Module: history_manager.py
Purpose: Persist and retrieve analysis history sessions using a JSON store.
Records: timestamp, dataset name, KPIs, forecast summary, insights, settings used.
"""

import json
import os
from datetime import datetime
from typing import List, Optional


HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "outputs", "analysis_history.json")


def _load_store() -> list:
    """Load history JSON file. Returns empty list if file doesn't exist."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_store(store: list):
    """Persist history list to JSON file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(store, f, indent=2, default=str)


def save_session(
    dataset_name: str,
    total_rows: int,
    date_range: str,
    num_products: int,
    num_areas: int,
    total_revenue: float,
    total_units: int,
    forecast_periods: int,
    forecast_freq: str,
    forecast_avg: float,
    best_season: str,
    top_area: str,
    insights_count: int,
    high_priority_count: int,
    filter_used: str,
    insights_text: str,
) -> str:
    """
    Save a completed analysis session to history.
    Returns the session ID.
    """
    store      = _load_store()
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    record = {
        "session_id":         session_id,
        "timestamp":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_name":       dataset_name,
        "total_rows":         total_rows,
        "date_range":         date_range,
        "num_products":       num_products,
        "num_areas":          num_areas,
        "total_revenue":      round(total_revenue, 2),
        "total_units":        total_units,
        "forecast_periods":   forecast_periods,
        "forecast_freq":      forecast_freq,
        "forecast_avg":       round(forecast_avg, 1),
        "best_season":        best_season,
        "top_area":           top_area,
        "insights_count":     insights_count,
        "high_priority_count":high_priority_count,
        "filter_used":        filter_used,
        "insights_text":      insights_text,
    }
    store.append(record)
    _save_store(store)
    return session_id


def load_history() -> List[dict]:
    """Return all sessions, newest first."""
    return list(reversed(_load_store()))


def delete_session(session_id: str):
    """Remove a session by ID."""
    store  = _load_store()
    store  = [s for s in store if s["session_id"] != session_id]
    _save_store(store)


def clear_all():
    """Wipe all history."""
    _save_store([])


def get_session(session_id: str) -> Optional[dict]:
    """Fetch a single session by ID."""
    for s in _load_store():
        if s["session_id"] == session_id:
            return s
    return None
