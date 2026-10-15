import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app import config, db, notify, weather
from app.mountains import MOUNTAINS

log = logging.getLogger(__name__)


def run_check(send_email=True):
    now = datetime.now(ZoneInfo(config.TIMEZONE))
    reports = weather.get_reports(MOUNTAINS, now)
    db.save_snapshots(reports, now)

    if not send_email:
        return 0
    return send_alerts(reports, now.date())


def send_alerts(reports, day):
    sent = 0
    for sub in db.confirmed_subscribers():
        powder_days = [
            (m, reports[m.slug]) for m in MOUNTAINS
            if m.slug in sub["mountains"] and reports[m.slug].overnight_in >= sub["threshold_in"]
        ]
        if not powder_days:
            continue

        claimed = db.claim_alerts(sub["id"], [m.slug for m, _ in powder_days], day)
        new = [(m, r) for m, r in powder_days if m.slug in claimed]
        if not new:
            continue
        new.sort(key=lambda pair: pair[1].overnight_in, reverse=True)

        try:
            notify.send_alert(sub, new)
            sent += 1
        except Exception:
            # one bad address shouldn't stop everyone else's email
            log.exception("couldn't email subscriber %s", sub["id"])
            db.release_alerts(sub["id"], [m.slug for m, _ in new], day)

    log.info("sent %d powder alerts", sent)
    return sent


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_check()
