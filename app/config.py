import os

from dotenv import load_dotenv

load_dotenv()

THRESHOLD_IN = float(os.getenv("POWDER_THRESHOLD_IN", 6))  # default for the sign-up form + dashboard labels
TIMEZONE = os.getenv("TIMEZONE", "America/Toronto")
OVERNIGHT_START_HOUR = int(os.getenv("OVERNIGHT_START_HOUR", 16))  # 4pm the day before
REFRESH_HOURS = int(os.getenv("REFRESH_HOURS", 3))  # dashboard re-checks if data is older than this

DATABASE_URL = os.getenv("DATABASE_URL", "")
CRON_SECRET = os.getenv("CRON_SECRET", "")
# links in emails start with this. on vercel it falls back to the project's real address,
# so the links still work if DASHBOARD_URL wasn't set there
VERCEL_URL = os.getenv("VERCEL_PROJECT_PRODUCTION_URL", "")
DASHBOARD_URL = os.getenv("DASHBOARD_URL") or (
    f"https://{VERCEL_URL}" if VERCEL_URL else "http://localhost:8000"
)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
