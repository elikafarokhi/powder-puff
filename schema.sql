CREATE TABLE IF NOT EXISTS snapshots (
    id BIGSERIAL PRIMARY KEY,
    slug TEXT NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL,
    overnight_in REAL NOT NULL,
    last_24h_in REAL NOT NULL,
    base_in REAL,
    temp_c REAL
);

CREATE INDEX IF NOT EXISTS snapshots_slug_checked_at ON snapshots (slug, checked_at DESC);

-- token is the secret in each person's confirm / settings / unsubscribe links
CREATE TABLE IF NOT EXISTS subscribers (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    token TEXT NOT NULL UNIQUE,
    mountains TEXT[] NOT NULL,
    threshold_in REAL NOT NULL DEFAULT 6,
    confirmed BOOLEAN NOT NULL DEFAULT false,
    emailed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- one row per person, mountain and day we emailed about, so nobody gets the same alert twice
CREATE TABLE IF NOT EXISTS sent_alerts (
    subscriber_id BIGINT NOT NULL REFERENCES subscribers (id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    day DATE NOT NULL,
    PRIMARY KEY (subscriber_id, slug, day)
);

-- the old single-person table from before sign-ups
DROP TABLE IF EXISTS alerts;
