import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests

from app import config

API_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class SnowReport:
    overnight_in: float
    last_24h_in: float
    base_in: float | None
    temp_c: float | None


def fetch_hourly(mountains):
    # open-meteo takes comma separated coordinates, so this is one request for every mountain
    params = {
        "latitude": ",".join(str(m.lat) for m in mountains),
        "longitude": ",".join(str(m.lon) for m in mountains),
        "elevation": ",".join(str(m.summit_m) for m in mountains),
        "hourly": "snowfall,snow_depth,temperature_2m",
        "timezone": config.TIMEZONE,
        "past_days": 1,
        "forecast_days": 1,
    }
    # the cron only runs once a day, so a hiccup at open-meteo would mean no alerts that morning.
    # try a few times before giving up
    for wait in [2, 10, None]:
        try:
            resp = requests.get(API_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()  # sometimes comes back empty while they're having trouble
            break
        except requests.RequestException:
            if wait is None:
                raise
            time.sleep(wait)
    if isinstance(data, dict):  # only one location comes back as an object, not a list
        data = [data]
    return [location["hourly"] for location in data]


def snowfall_cm(hourly, start, end):
    # each value is the snow that fell in the hour *before* its timestamp,
    # so the window is (start, end]
    total = 0
    for t, cm in zip(hourly["time"], hourly["snowfall"]):
        if cm and start < datetime.fromisoformat(t) <= end:
            total += cm
    return total


def value_at(hourly, key, when):
    t = when.strftime("%Y-%m-%dT%H:00")
    if t not in hourly["time"]:
        return None
    return hourly[key][hourly["time"].index(t)]


def to_inches(cm):
    return round(cm / 2.54, 1)


def build_report(hourly, now):
    # open-meteo gives back local times without a timezone
    now = now.replace(tzinfo=None, minute=0, second=0, microsecond=0)
    overnight_start = (now - timedelta(days=1)).replace(hour=config.OVERNIGHT_START_HOUR)
    depth_m = value_at(hourly, "snow_depth", now)

    return SnowReport(
        overnight_in=to_inches(snowfall_cm(hourly, overnight_start, now)),
        last_24h_in=to_inches(snowfall_cm(hourly, now - timedelta(hours=24), now)),
        base_in=to_inches(depth_m * 100) if depth_m is not None else None,
        temp_c=value_at(hourly, "temperature_2m", now),
    )


def get_reports(mountains, now):
    hourly_list = fetch_hourly(mountains)
    return {m.slug: build_report(h, now) for m, h in zip(mountains, hourly_list)}
