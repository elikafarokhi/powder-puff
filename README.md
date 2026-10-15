# Powder Puff 🐻‍❄️

Checks the snow at the hills I ski every morning and emails me when one of them gets a real dump overnight. There's also a small dashboard so I can see all of them at once.

Tracks 42 public ski resorts across Ontario and Quebec. Six are featured and pre-picked in the sign-up form: Blue Mountain, Horseshoe, Mount St. Louis Moonstone, Mont Tremblant, Le Massif and Stoneham. Add or remove hills in `app/mountains.py` (set `default=True` to feature one).

Runs for free on Vercel (Hobby plan) with a Neon Postgres database.

## How it works

- **Anyone can sign up** at the bottom of the dashboard: email, which mountains, and how many inches counts as a powder day for them. They get a confirmation email first, so nobody can sign up someone else. No passwords: each person has a secret link (in every email) to change their settings or unsubscribe.
- **Vercel Cron** calls `/api/cron/check` once a day. It gets hourly snowfall for every mountain from Open-Meteo in a single request, adds up everything since 4pm the day before, and saves it to Postgres.
- Then it goes through everyone who confirmed. If any of *their* mountains hit *their* threshold, they get one email. Before sending it records "emailed this person about X today" in `sent_alerts`, so even if Vercel calls the cron twice nobody gets a duplicate. If an email fails, that record is removed so the next run tries again.
- **The dashboard** reads the newest numbers from the database. Vercel's free cron only runs once a day, so if the numbers are more than 3 hours old when you open the page, it runs a quick check first (no email). There's also a Refresh button.

Emails go out through one Gmail account, which is fine for friends and a demo (Gmail allows a few hundred a day). For lots of strangers you'd want a proper sending service and your own domain.

### About the cron time

Vercel cron is always in UTC, and on the free plan it can fire any time within the hour you pick. `0 11 * * *` means 11:00 to 11:59 UTC, which is **6 to 7am in Toronto during ski season** (EST). After the clocks change in March it becomes 7 to 8am. Change it in `vercel.json`.

## Setup

### 1. Database (Neon)

1. Make a free project at [neon.com](https://neon.com).
2. Copy the **pooled** connection string (the host has `-pooler` in it).
3. Open the SQL Editor in Neon and run everything in `schema.sql`.

### 2. Vercel

1. Push this repo to GitHub and import it in Vercel. It picks up FastAPI by itself.
2. In Project Settings > Environment Variables, add everything from `.env.example`:
   - `DATABASE_URL` from Neon
   - `CRON_SECRET`: any long random string. Vercel sends it with the cron request and the app rejects anything without it, so nobody else can trigger emails.
   - Your Gmail address and an [app password](https://myaccount.google.com/apppasswords) (needs 2-step verification on)
   - `DASHBOARD_URL`: your `*.vercel.app` address
3. Redeploy so the variables are picked up. The cron shows up under Settings > Cron Jobs, and you can hit **Run** there to test it.

## Running locally

Uses [uv](https://docs.astral.sh/uv/).

```
cp .env.example .env    # fill in DATABASE_URL etc
uv sync
uv run uvicorn app.main:app --reload
```

- sign up with your own email on http://localhost:8000 to test the confirmation email
- `uv run python -m app.jobs` runs one full check now (and emails anyone with powder)
- `uv run python -m app.db` creates the tables if you'd rather not use the Neon editor
- `/email-preview` shows the email with the latest numbers
- `uv run pytest` runs the tests

## Notes

I pass each mountain's summit elevation to the API. Weather models work on a grid several km wide, so without it you get something closer to the valley. It matters most at Le Massif, which drops 770 m down to the river.

The numbers are model estimates, not what the resorts report, so they won't always match.

Weather data by [Open-Meteo](https://open-meteo.com/).
