import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import config, db, notify, subscribe
from app.jobs import run_check
from app.mountains import DEFAULT_SLUGS, MOUNTAINS, REGIONS
from app.templating import HERE, templates
from app.weather import SnowReport

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI()
app.include_router(subscribe.router)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")


def status(snap):
    if snap is None:
        return "waiting", "no data yet"
    if snap["overnight_in"] >= config.THRESHOLD_IN:
        return "powder", "powder day"
    if snap["overnight_in"] >= 1:
        return "fresh", "a little fresh"
    return "calm", "nothing new"


def nice_time(dt):
    # "Fri Jan 15, 6:42 AM". %-d would be shorter but doesn't work on windows
    return f"{dt:%a %b} {dt.day}, {dt.hour % 12 or 12}:{dt:%M %p}"


def is_stale(snaps):
    if not snaps:
        return True
    newest = max(s["checked_at"] for s in snaps.values())
    return datetime.now(newest.tzinfo) - newest > timedelta(hours=config.REFRESH_HOURS)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    snaps = db.latest_snapshots()

    # vercel's free cron only runs once a day, so the page refreshes itself when it's old
    if is_stale(snaps):
        try:
            run_check(send_email=False)
            snaps = db.latest_snapshots()
        except requests.RequestException as e:
            log.warning("refresh failed, showing old data: %s", e)

    cards = {}
    for m in MOUNTAINS:
        snap = snaps.get(m.slug)
        css, label = status(snap)
        cards[m.slug] = {"mountain": m, "snap": snap, "css": css, "label": label}

    # the original six get big cards up top, then every resort is listed by region
    featured = [cards[m.slug] for m in MOUNTAINS if m.default]
    all_regions = [(province, region, [cards[m.slug] for m in ms]) for province, region, ms in REGIONS]

    last_checked = None
    if snaps:
        newest = max(s["checked_at"] for s in snaps.values())
        last_checked = nice_time(newest.astimezone(ZoneInfo(config.TIMEZONE)))

    return templates.TemplateResponse(request, "dashboard.html", {
        "featured": featured,
        "all_regions": all_regions,
        "last_checked": last_checked,
        # for the sign-up form
        "regions": REGIONS,
        "thresholds": subscribe.THRESHOLDS,
        "selected": DEFAULT_SLUGS,
        "default_threshold": int(config.THRESHOLD_IN),
    })


@app.post("/refresh")
def refresh():
    run_check(send_email=False)
    return RedirectResponse("/", status_code=303)


@app.get("/api/cron/check")
def cron_check(authorization: str | None = Header(default=None)):
    # vercel sends "Bearer <CRON_SECRET>" so random people can't trigger emails
    if not config.CRON_SECRET or authorization != f"Bearer {config.CRON_SECRET}":
        raise HTTPException(status_code=401)
    return {"emails_sent": run_check()}


@app.get("/email-preview", response_class=HTMLResponse)
def email_preview():
    # shows what the alert looks like with the latest numbers
    snaps = db.latest_snapshots()
    days = []
    for m in MOUNTAINS:
        s = snaps.get(m.slug)
        if s:
            days.append((m, SnowReport(s["overnight_in"], s["last_24h_in"], s["base_in"], s["temp_c"])))
    days.sort(key=lambda pair: pair[1].overnight_in, reverse=True)
    return notify.render_alert(days[:3])
