from datetime import datetime, timedelta
from unittest import mock

from app import weather
from app.mountains import MOUNTAINS
from app.weather import build_report, snowfall_cm


def fake_hourly(snow):
    # 48 hours starting jan 14, no snow except the hours given
    start = datetime(2027, 1, 14)
    times = [(start + timedelta(hours=h)).strftime("%Y-%m-%dT%H:00") for h in range(48)]
    return {
        "time": times,
        "snowfall": [snow.get(t, 0) for t in times],
        "snow_depth": [0.5] * 48,
        "temperature_2m": [-8.0] * 48,
    }


def test_window_skips_start_hour_includes_end_hour():
    hourly = fake_hourly({"2027-01-14T16:00": 5, "2027-01-14T17:00": 2, "2027-01-15T07:00": 3})
    assert snowfall_cm(hourly, datetime(2027, 1, 14, 16), datetime(2027, 1, 15, 7)) == 5


def test_six_inches_overnight():
    hourly = fake_hourly({"2027-01-14T22:00": 7.62, "2027-01-15T03:00": 7.62})
    report = build_report(hourly, datetime(2027, 1, 15, 6, 30))
    assert report.overnight_in == 6.0
    assert report.last_24h_in == 6.0
    assert report.base_in == 19.7
    assert report.temp_c == -8.0


def test_morning_snow_yesterday_isnt_overnight():
    hourly = fake_hourly({"2027-01-14T10:00": 10})
    report = build_report(hourly, datetime(2027, 1, 15, 6, 30))
    assert report.overnight_in == 0
    assert report.last_24h_in == 3.9


def test_no_snow_depth():
    hourly = fake_hourly({})
    hourly["snow_depth"] = [None] * 48
    assert build_report(hourly, datetime(2027, 1, 15, 6, 30)).base_in is None


def test_one_request_for_all_mountains():
    resp = mock.Mock()
    resp.json.return_value = [{"hourly": fake_hourly({"2027-01-15T02:00": i * 2.54})} for i in range(len(MOUNTAINS))]
    with mock.patch.object(weather.requests, "get", return_value=resp) as get:
        reports = weather.get_reports(MOUNTAINS, datetime(2027, 1, 15, 6, 30))

    assert get.call_count == 1
    assert get.call_args.kwargs["params"]["elevation"].count(",") == len(MOUNTAINS) - 1
    assert [reports[m.slug].overnight_in for m in MOUNTAINS] == [float(i) for i in range(len(MOUNTAINS))]
