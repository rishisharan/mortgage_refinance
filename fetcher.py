"""
fetcher.py — Fetches mortgage rate data from FRED

FRED = Federal Reserve Economic Data
It's a free API from the St. Louis Fed with thousands of economic datasets.

The two series we care about:
  MORTGAGE30US — 30-year fixed mortgage rate (updated weekly)
  MORTGAGE15US — 15-year fixed mortgage rate (updated weekly)

Get your free API key at: https://fred.stlouisfed.org/docs/api/api_key.html
(takes 30 seconds, just needs an email)
"""

import os
import requests
from datetime import datetime, timedelta


# FRED API base URL
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"

# The two mortgage rate series we're tracking
SERIES = {
    "30yr Fixed": "MORTGAGE30US",
    "15yr Fixed": "MORTGAGE15US",
}


def fetch_rate(series_id: str, api_key: str) -> dict:
    """
    Fetches the most recent observations for a given FRED series.
    Returns the latest value and the previous week's value for comparison.
    """
    # Only fetch the last 14 days so we get current + previous week
    start_date = (datetime.today() - timedelta(days=14)).strftime("%Y-%m-%d")

    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "sort_order": "desc",          # Latest first
        "limit": 2                     # We only need latest + previous
    }

    response = requests.get(FRED_BASE, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    observations = data.get("observations", [])

    if len(observations) == 0:
        return {"current": None, "previous": None, "date": None}

    current = float(observations[0]["value"])
    date = observations[0]["date"]
    previous = float(observations[1]["value"]) if len(observations) > 1 else None

    return {
        "current": current,
        "previous": previous,
        "date": date,
        "change": round(current - previous, 2) if previous else None
    }


def fetch_all_rates() -> dict:
    """
    Fetches all tracked mortgage rates.
    Returns a dict with rate names as keys and rate data as values.
    """
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        raise ValueError(
            "FRED_API_KEY not set.\n"
            "Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html\n"
            "Then run: $env:FRED_API_KEY = 'your-key-here'"
        )

    rates = {}
    for name, series_id in SERIES.items():
        print(f"  Fetching {name}...")
        rates[name] = fetch_rate(series_id, api_key)

    return rates


def format_rates_for_prompt(rates: dict) -> str:
    """
    Formats rate data into a clean string for Claude to analyze.
    """
    lines = [f"Mortgage Rate Data as of {datetime.today().strftime('%B %d, %Y')}:\n"]

    for name, data in rates.items():
        current = data["current"]
        previous = data["previous"]
        change = data["change"]
        date = data["date"]

        if current is None:
            lines.append(f"{name}: Data unavailable")
            continue

        # Format the change arrow
        if change is not None:
            if change > 0:
                direction = f"▲ +{change}% from last week"
            elif change < 0:
                direction = f"▼ {change}% from last week"
            else:
                direction = "→ Unchanged from last week"
        else:
            direction = "No previous data"

        lines.append(f"{name}: {current}%  ({direction})  [as of {date}]")

    return "\n".join(lines)
