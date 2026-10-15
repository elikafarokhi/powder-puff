import logging
import re
import smtplib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Form, Request

from app import db, notify
from app.mountains import MOUNTAINS, REGIONS
from app.templating import templates

log = logging.getLogger(__name__)
router = APIRouter()

THRESHOLDS = [2, 4, 6, 8, 10, 12]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SLUGS = [m.slug for m in MOUNTAINS]


def message(request, title, text, status_code=200, **extra):
    return templates.TemplateResponse(
        request, "message.html", {"title": title, "text": text, **extra}, status_code=status_code
    )


def bad_link(request):
    return message(request, "That link doesn't work",
                   "It might be old, or you may have already unsubscribed.", 404)


def clean(mountains, threshold):
    mountains = [s for s in SLUGS if s in mountains]  # keeps the usual order, drops junk
    if threshold not in THRESHOLDS:
        threshold = 6
    return mountains, threshold


def emailed_recently(sub):
    # stops someone from making us spam an address by submitting the form over and over
    return sub["emailed_at"] and datetime.now(timezone.utc) - sub["emailed_at"] < timedelta(minutes=10)


@router.post("/subscribe")
def subscribe(
    request: Request,
    email: str = Form(""),
    mountains: list[str] = Form([]),
    threshold: int = Form(6),
    website: str = Form(""),
):
    check_inbox = message(request, "Check your inbox",
                          "We just emailed you a link. If it's not there in a minute, look in spam.")

    # "website" is hidden from people, so only bots fill it in
    if website:
        return check_inbox

    email = email.strip().lower()
    mountains, threshold = clean(mountains, threshold)
    if not EMAIL_RE.match(email) or not mountains:
        return message(request, "Almost",
                       "Enter a real email address and pick at least one mountain.", 400)

    sub = db.subscriber_by_email(email)
    if sub is None:
        sub = db.create_subscriber(email, mountains, threshold)
        send = notify.send_confirm
    elif not sub["confirmed"]:
        db.update_prefs(sub["id"], mountains, threshold)
        send = notify.send_confirm
    else:
        # already subscribed: email them their settings link instead of changing anything,
        # otherwise anyone could change anyone's settings just by knowing their email
        send = notify.send_settings_link

    if not emailed_recently(sub):
        try:
            send(sub)
        except (smtplib.SMTPException, OSError):
            log.exception("couldn't send signup email")
            return message(request, "Couldn't send the email",
                           "Something went wrong on our end. Try again in a few minutes.", 500)
        db.mark_emailed(sub["id"])

    return check_inbox


@router.get("/confirm/{token}")
def confirm(request: Request, token: str):
    sub = db.confirm(token)
    if sub is None:
        return bad_link(request)
    return message(request, "You're in",
                   "You'll get an email around 6am whenever your mountains get a real dump overnight.",
                   link_url=f"/manage/{token}", link_label="Change my settings")


@router.get("/manage/{token}")
def manage(request: Request, token: str):
    sub = db.subscriber_by_token(token)
    if sub is None:
        return bad_link(request)
    return templates.TemplateResponse(request, "manage.html", {
        "sub": sub,
        "regions": REGIONS,
        "thresholds": THRESHOLDS,
        "selected": sub["mountains"],
        "threshold": int(sub["threshold_in"]),
    })


@router.post("/manage/{token}")
def save_settings(request: Request, token: str,
                  mountains: list[str] = Form([]), threshold: int = Form(6)):
    sub = db.subscriber_by_token(token)
    if sub is None:
        return bad_link(request)
    mountains, threshold = clean(mountains, threshold)
    if not mountains:
        return message(request, "Almost", "Pick at least one mountain, or unsubscribe instead.", 400,
                       link_url=f"/manage/{token}", link_label="Back to my settings")
    db.update_prefs(sub["id"], mountains, threshold)
    return message(request, "Saved", "Your new settings start with tomorrow morning's check.",
                   link_url=f"/manage/{token}", link_label="Back to my settings")


@router.get("/unsubscribe/{token}")
def unsubscribe_page(request: Request, token: str):
    # a button instead of unsubscribing straight away, because some email apps
    # open every link in an email to scan it
    sub = db.subscriber_by_token(token)
    if sub is None:
        return bad_link(request)
    return message(request, "Unsubscribe?", f"You'll stop getting powder alerts at {sub['email']}.",
                   post_url=f"/unsubscribe/{token}", post_label="Unsubscribe")


@router.post("/unsubscribe/{token}")
def unsubscribe(request: Request, token: str):
    db.delete_subscriber(token)
    return message(request, "You're unsubscribed",
                   "No more powder alerts. You can sign up again any time from the dashboard.")
