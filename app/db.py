import secrets
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app import config


def connect():
    # serverless functions come and go, so just open a connection when we need one.
    # use neon's pooled connection string (the one with -pooler in the host).
    # prepare_threshold=None turns off prepared statements, which the pooler can trip over
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row, prepare_threshold=None)


def init_db():
    schema = (Path(__file__).parent.parent / "schema.sql").read_text()
    with connect() as conn:
        for statement in schema.split(";"):
            if statement.strip():
                conn.execute(statement)


# --- snow ---

def save_snapshots(reports, checked_at):
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO snapshots (slug, checked_at, overnight_in, last_24h_in, base_in, temp_c) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [(slug, checked_at, r.overnight_in, r.last_24h_in, r.base_in, r.temp_c)
             for slug, r in reports.items()],
        )


def latest_snapshots():
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT ON (slug) * FROM snapshots ORDER BY slug, checked_at DESC"
        ).fetchall()
    return {row["slug"]: row for row in rows}


# --- subscribers ---

def subscriber_by_email(email):
    with connect() as conn:
        return conn.execute("SELECT * FROM subscribers WHERE email = %s", (email,)).fetchone()


def subscriber_by_token(token):
    with connect() as conn:
        return conn.execute("SELECT * FROM subscribers WHERE token = %s", (token,)).fetchone()


def create_subscriber(email, mountains, threshold):
    with connect() as conn:
        return conn.execute(
            "INSERT INTO subscribers (email, token, mountains, threshold_in) "
            "VALUES (%s, %s, %s, %s) RETURNING *",
            (email, secrets.token_urlsafe(24), mountains, threshold),
        ).fetchone()


def update_prefs(subscriber_id, mountains, threshold):
    with connect() as conn:
        conn.execute(
            "UPDATE subscribers SET mountains = %s, threshold_in = %s WHERE id = %s",
            (mountains, threshold, subscriber_id),
        )


def mark_emailed(subscriber_id):
    with connect() as conn:
        conn.execute("UPDATE subscribers SET emailed_at = now() WHERE id = %s", (subscriber_id,))


def confirm(token):
    with connect() as conn:
        return conn.execute(
            "UPDATE subscribers SET confirmed = true WHERE token = %s RETURNING *", (token,)
        ).fetchone()


def delete_subscriber(token):
    with connect() as conn:
        conn.execute("DELETE FROM subscribers WHERE token = %s", (token,))


def confirmed_subscribers():
    with connect() as conn:
        return conn.execute("SELECT * FROM subscribers WHERE confirmed ORDER BY id").fetchall()


# --- alerts ---

def claim_alerts(subscriber_id, slugs, day):
    # returns only the mountains we hadn't already emailed this person about today.
    # doing it in one insert means two cron calls at once can't both send the email.
    with connect() as conn:
        rows = conn.execute(
            "INSERT INTO sent_alerts (subscriber_id, slug, day) "
            "SELECT %s, unnest(%s::text[]), %s::date "
            "ON CONFLICT DO NOTHING RETURNING slug",
            (subscriber_id, slugs, day),
        ).fetchall()
    return {row["slug"] for row in rows}


def release_alerts(subscriber_id, slugs, day):
    # if the email failed, undo the claim so the next run tries again
    with connect() as conn:
        conn.execute(
            "DELETE FROM sent_alerts WHERE subscriber_id = %s AND day = %s AND slug = ANY(%s)",
            (subscriber_id, day, slugs),
        )


if __name__ == "__main__":
    init_db()
    print("tables created")
