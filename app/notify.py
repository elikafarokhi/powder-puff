import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app import config

env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=True)


def link(path):
    return config.DASHBOARD_URL.rstrip("/") + path


def send(to, subject, html, text, headers=None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("Powder Puff", config.SMTP_USER))
    msg["To"] = to
    for name, value in (headers or {}).items():
        msg[name] = value
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
        smtp.send_message(msg)


def render_alert(powder_days, sub=None):
    # sub is None for /email-preview, so the links just go nowhere
    token = sub["token"] if sub else ""
    return env.get_template("email.html").render(
        powder_days=powder_days,
        threshold=sub["threshold_in"] if sub else config.THRESHOLD_IN,
        dashboard_url=config.DASHBOARD_URL,
        manage_url=link(f"/manage/{token}") if sub else "#",
        unsubscribe_url=link(f"/unsubscribe/{token}") if sub else "#",
    )


def send_alert(sub, powder_days):
    # powder_days is a list of (mountain, report), biggest dump first
    top, report = powder_days[0]
    unsubscribe_url = link(f"/unsubscribe/{sub['token']}")

    text = "\n".join(f'{m.name}: {r.overnight_in}" overnight' for m, r in powder_days)
    text += f"\n\n{config.DASHBOARD_URL}\nUnsubscribe: {unsubscribe_url}"

    send(
        sub["email"],
        f'Powder day: {report.overnight_in}" at {top.name}',
        render_alert(powder_days, sub),
        text,
        # lets gmail show its own "unsubscribe" button next to the sender
        headers={
            "List-Unsubscribe": f"<{unsubscribe_url}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    )


def send_simple(to, subject, heading, body, button_text, button_url):
    html = env.get_template("simple_email.html").render(
        heading=heading, body=body, button_text=button_text, button_url=button_url,
    )
    send(to, subject, html, f"{body}\n\n{button_url}")


def send_confirm(sub):
    send_simple(
        sub["email"],
        "Confirm your powder alerts",
        "One click and you're in",
        "Confirm your email to start getting an alert when your mountains get fresh snow overnight. "
        "If you didn't sign up, just ignore this and you won't hear from us.",
        "Yes, send me alerts",
        link(f"/confirm/{sub['token']}"),
    )


def send_settings_link(sub):
    send_simple(
        sub["email"],
        "Your Powder Puff settings",
        "You're already signed up",
        "Someone (hopefully you) tried to sign up with this email. You're already getting alerts, "
        "so here's a link to change your mountains or unsubscribe.",
        "Change my settings",
        link(f"/manage/{sub['token']}"),
    )
