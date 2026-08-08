"""
db.py
=====
SQLite storage for the recommendations feature. Three tables:

  taste_profile   - current weighted score per performer/studio/tag,
                     rebuilt from your Stash library each refresh.
  recommendations - current state of every candidate scene the engine
                     has surfaced (pending / sent / skipped).
  feedback        - append-only log of every decision you make, with a
                     full feature snapshot at decision time. This is the
                     training set for Tier 2 (a learned ranking model) -
                     kept from day one even though nothing trains on it
                     yet, so there's history to learn from once it does.

DB file lives at /app/data/recommendations.db - mounted as a volume in
docker-compose.yml so it survives container rebuilds.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.environ.get("RECS_DB_PATH", "/app/data/recommendations.db")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # WAL lets readers and writers proceed concurrently instead of
    # blocking each other outright, and busy_timeout makes SQLite retry on
    # a lock for up to 5s instead of raising "database is locked"
    # immediately - cheap insurance now that the nightly refresh, a manual
    # refresh, and the web UI can genuinely overlap. journal_mode=WAL is a
    # persistent property of the file once set; PRAGMA busy_timeout is
    # per-connection and needs to be set on every connect.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS taste_profile (
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                weight REAL NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (entity_type, entity_id)
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                scene_id TEXT PRIMARY KEY,
                title TEXT,
                studio TEXT,
                performers TEXT,
                tags TEXT,
                release_date TEXT,
                image_url TEXT,
                score REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                features_json TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scene_id TEXT NOT NULL,
                label INTEGER NOT NULL,
                score_at_decision REAL,
                features_json TEXT NOT NULL,
                decided_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_recs_status ON recommendations(status);

            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tag_cooccurrence (
                tag_a TEXT NOT NULL,
                tag_b TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (tag_a, tag_b)
            );

            CREATE TABLE IF NOT EXISTS performer_cooccurrence (
                performer_a TEXT NOT NULL,
                performer_b TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (performer_a, performer_b)
            );
            """
        )
        # Migrations for columns added after the table already existed.
        for ddl in (
            "ALTER TABLE recommendations ADD COLUMN source TEXT NOT NULL DEFAULT 'profile'",
            "ALTER TABLE recommendations ADD COLUMN model_score REAL",
            "ALTER TABLE recommendations ADD COLUMN novelty_score REAL",
            "ALTER TABLE recommendations ADD COLUMN torbox_type TEXT",
            "ALTER TABLE recommendations ADD COLUMN torbox_id INTEGER",
            "ALTER TABLE recommendations ADD COLUMN torbox_name TEXT",
            "ALTER TABLE recommendations ADD COLUMN watch_due_at TEXT",
            "ALTER TABLE recommendations ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE recommendations ADD COLUMN failed_release_name TEXT",
            # JSON array replacing the single failed_release_name - stores ALL tried
            # release names so retries skip every previously-failed attempt, not just the last
            "ALTER TABLE recommendations ADD COLUMN failed_release_names TEXT",
            # Queuing support - stores full search context for dispatching when slot frees
            "ALTER TABLE recommendations ADD COLUMN queued_at TEXT",
            "ALTER TABLE recommendations ADD COLUMN queue_studio TEXT",
            "ALTER TABLE recommendations ADD COLUMN queue_title TEXT",
            "ALTER TABLE recommendations ADD COLUMN queue_performers TEXT",
            "ALTER TABLE recommendations ADD COLUMN queue_date TEXT",
            "ALTER TABLE recommendations ADD COLUMN check_failures INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE feedback ADD COLUMN confidence REAL NOT NULL DEFAULT 1.0",
            "ALTER TABLE feedback ADD COLUMN watch_checked INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE feedback ADD COLUMN play_count INTEGER",
            "ALTER TABLE feedback ADD COLUMN play_duration REAL",
            "ALTER TABLE feedback ADD COLUMN o_counter INTEGER",
            "ALTER TABLE feedback ADD COLUMN rating100 INTEGER",
        ):
            try:
                conn.execute(ddl)
            except sqlite3.OperationalError:
                pass  # column already exists

        # Watch feedback table - created here rather than executescript so
        # it can be added as a migration without touching the main DDL block.
        init_watch_feedback_table(conn)

        # One-time seed: the wildcard categories used to be hardcoded in
        # recommendation_engine.py (Oil/Big Ass/Wet Look/Anal Sex tags +
        # the BangBros network). Now that they live here so they're
        # editable from the Settings page, seed them once so nothing is
        # lost on the switchover - only runs if nothing's been saved yet.
        if conn.execute("SELECT 1 FROM meta WHERE key = 'wildcard_categories'").fetchone() is None:
            seed = [
                {"kind": "tag", "entity_id": "df9cd431-cd72-4455-8797-9a67a5b8ce45", "entity_name": "Oil"},
                {"kind": "tag", "entity_id": "2e2ec8e2-b2ae-4da3-9813-7adabe8046b1", "entity_name": "Big Ass"},
                {"kind": "tag", "entity_id": "f3ea6514-d4d0-4f70-8e38-c562500b8152", "entity_name": "Wet Look"},
                {"kind": "tag", "entity_id": "b70c78b7-a25a-4c82-9929-591a5795b54d", "entity_name": "Anal Sex"},
                {"kind": "studio", "entity_id": "525f8c32-d14f-42c0-939c-bb5d8eae8bcf", "entity_name": "BangBros"},
            ]
            conn.execute(
                "INSERT INTO meta (key, value) VALUES ('wildcard_categories', ?)",
                (json.dumps(seed),),
            )


# --------------------------------------------------------------- taste profile
def replace_taste_profile(rows: list[tuple[str, str, str, float]]) -> None:
    """rows: (entity_type, entity_id, entity_name, weight). Full replace each
    rebuild - simpler than incremental updates and the source of truth (your
    Stash library) is small enough to rescan completely each time."""
    now = _now()
    with _conn() as conn:
        conn.execute("DELETE FROM taste_profile")
        conn.executemany(
            "INSERT INTO taste_profile (entity_type, entity_id, entity_name, weight, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            [(t, i, n, w, now) for t, i, n, w in rows],
        )


def top_entities(entity_type: str, limit: int = 50) -> list[sqlite3.Row]:
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM taste_profile WHERE entity_type = ? "
            "ORDER BY weight DESC LIMIT ?",
            (entity_type, limit),
        ).fetchall()


def all_weights() -> dict[tuple[str, str], float]:
    with _conn() as conn:
        rows = conn.execute("SELECT entity_type, entity_id, weight FROM taste_profile").fetchall()
    return {(r["entity_type"], r["entity_id"]): r["weight"] for r in rows}


# --------------------------------------------------------------- recommendations
def upsert_candidate(rec: dict) -> None:
    """Insert a new candidate, or refresh its score if it's still pending.
    Scenes already decided (sent/skipped) are left alone - re-scoring a
    decision you've already made would be confusing and pointless."""
    with _conn() as conn:
        existing = conn.execute(
            "SELECT status FROM recommendations WHERE scene_id = ?", (rec["scene_id"],)
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO recommendations "
                "(scene_id, title, studio, performers, tags, release_date, "
                " image_url, score, status, features_json, created_at, source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)",
                (
                    rec["scene_id"], rec["title"], rec["studio"], rec["performers"],
                    rec["tags"], rec["release_date"], rec["image_url"], rec["score"],
                    json.dumps(rec["features"]), _now(), rec.get("source", "profile"),
                ),
            )
        elif existing["status"] == "pending":
            conn.execute(
                "UPDATE recommendations SET score = ?, features_json = ? WHERE scene_id = ?",
                (rec["score"], json.dumps(rec["features"]), rec["scene_id"]),
            )


def get_recommendation(scene_id: str) -> sqlite3.Row | None:
    """Non-mutating lookup - used by the download route to grab title/studio
    before attempting the Prowlarr/TorBox add, without marking it decided
    until that actually succeeds."""
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM recommendations WHERE scene_id = ?", (scene_id,)
        ).fetchone()


def pending_recommendations(limit: int = 60) -> list[sqlite3.Row]:
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM recommendations WHERE status = 'pending' "
            "ORDER BY (model_score IS NOT NULL) DESC, model_score DESC, score DESC LIMIT ?",
            (limit,),
        ).fetchall()


def explore_recommendations(limit: int, exclude_scene_ids: set[str]) -> list[sqlite3.Row]:
    """Epsilon-greedy exploration slice: pulls candidates the model has
    seen the LEAST training signal near (highest novelty_score - distance
    in feature space from every decided example), rather than ones whose
    predict_proba happens to sit closest to 0.5. The two are not the same
    thing: under class_weight="balanced" training, probabilities cluster
    artificially near 0.5 regardless of genuine uncertainty, and even with
    unweighted/calibrated training, a low base rate means almost nothing
    is a genuine coin-flip - "closest to 0.5" ends up just re-selecting
    near the top of the exploit ranking either way. Feature-space novelty
    targets actual coverage gaps in the training data instead, which is
    what an exploration slice is supposed to be doing. Falls back to a
    random draw if novelty hasn't been computed yet (no model trained,
    or this is a refresh before the first retrain)."""
    with _conn() as conn:
        has_novelty = conn.execute(
            "SELECT 1 FROM recommendations WHERE novelty_score IS NOT NULL LIMIT 1"
        ).fetchone()
        order = "novelty_score DESC" if has_novelty else "RANDOM()"
        if exclude_scene_ids:
            qmarks = ",".join("?" for _ in exclude_scene_ids)
            sql = (
                f"SELECT * FROM recommendations WHERE status = 'pending' "
                f"AND scene_id NOT IN ({qmarks}) ORDER BY {order} LIMIT ?"
            )
            params = (*exclude_scene_ids, limit)
        else:
            sql = f"SELECT * FROM recommendations WHERE status = 'pending' ORDER BY {order} LIMIT ?"
            params = (limit,)
        return conn.execute(sql, params).fetchall()


def pending_recommendations_mixed(
    limit: int = 60, wildcard_fraction: float = 1 / 3, explore_fraction: float = 1 / 6
) -> tuple[list[sqlite3.Row], set[str]]:
    """Same as pending_recommendations, but guarantees slices for both
    wildcard categories and low-confidence exploration - otherwise the
    highest-ranked picks would always crowd everything else out. Returns
    (mixed_rows, explore_scene_ids) so the caller can badge which cards
    were chosen specifically for exploration."""
    wildcard_n = round(limit * wildcard_fraction)
    explore_n = round(limit * explore_fraction)
    profile_n = limit - wildcard_n - explore_n
    rank = "(model_score IS NOT NULL) DESC, model_score DESC, score DESC"
    with _conn() as conn:
        profile_rows = conn.execute(
            f"SELECT * FROM recommendations WHERE status = 'pending' AND source = 'profile' "
            f"ORDER BY {rank} LIMIT ?",
            (profile_n,),
        ).fetchall()
        wildcard_rows = conn.execute(
            f"SELECT * FROM recommendations WHERE status = 'pending' AND source = 'wildcard' "
            f"ORDER BY {rank} LIMIT ?",
            (wildcard_n,),
        ).fetchall()

    chosen_ids = {r["scene_id"] for r in profile_rows} | {r["scene_id"] for r in wildcard_rows}
    explore_rows = explore_recommendations(explore_n, chosen_ids)
    explore_ids = {r["scene_id"] for r in explore_rows}

    # Interleave roughly 2 profile : 1 wildcard : 1 explore per cycle rather
    # than clumping any pool at the end of the page.
    mixed: list[sqlite3.Row] = []
    pi, wi, ei = 0, 0, 0
    while pi < len(profile_rows) or wi < len(wildcard_rows) or ei < len(explore_rows):
        for _ in range(2):
            if pi < len(profile_rows):
                mixed.append(profile_rows[pi])
                pi += 1
        if wi < len(wildcard_rows):
            mixed.append(wildcard_rows[wi])
            wi += 1
        if ei < len(explore_rows):
            mixed.append(explore_rows[ei])
            ei += 1
    return mixed, explore_ids


def decided_scene_ids() -> set[str]:
    """Scenes already sent or skipped - exclude these from new candidate
    batches so a skip doesn't just reappear next refresh."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT scene_id FROM recommendations WHERE status != 'pending'"
        ).fetchall()
    return {r["scene_id"] for r in rows}


def decide(scene_id: str, status: str, confidence: float | None = None) -> sqlite3.Row | None:
    """Mark a recommendation sent/skipped/not_interested and log it to the
    feedback table for future model training. confidence overrides the
    default per-status value:
      sent          -> label=1, confidence=1.0 (provisional; watch-feedback will revise)
      skipped       -> label=0, confidence=0.3 (weak - 'not now', not 'dislike')
      not_interested -> label=0, confidence=1.5 (deliberate rejection)
    The distinction matters: ambiguous skips were being treated as hard
    negatives (confidence=1.0) and distorting the model. Now they're
    down-weighted so the model learns mostly from genuine signals.
    Returns the row as it was before the update, or None if scene_id
    isn't a known recommendation."""
    _DEFAULT_CONFIDENCE = {
        "sent": 1.0,
        "skipped": 0.3,
        "not_interested": 1.5,
    }
    label = 1 if status == "sent" else 0
    conf = confidence if confidence is not None else _DEFAULT_CONFIDENCE.get(status, 0.5)

    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM recommendations WHERE scene_id = ?", (scene_id,)
        ).fetchone()
        if row is None:
            return None
        now = _now()
        conn.execute(
            "UPDATE recommendations SET status = ?, decided_at = ? WHERE scene_id = ?",
            (status, now, scene_id),
        )
        conn.execute(
            "INSERT INTO feedback (scene_id, label, score_at_decision, features_json, decided_at, confidence) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (scene_id, label, row["score"], row["features_json"], now, conf),
        )
        return row


def feedback_count() -> int:
    with _conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM feedback").fetchone()["c"]


# --------------------------------------------------------------- ML (Tier 2)
def feedback_with_source() -> list[tuple[str, float, str, int, float]]:
    """Returns all feedback rows for model training. Uses LEFT JOIN so
    feedback rows survive even when their recommendation row no longer
    exists (after a reset). Source falls back to 'profile' when the
    recommendation row is gone — this means a full reset no longer silently
    drops most of the training data, which was the cause of AUC falling to
    0.535 immediately after the recommendations table was cleared."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT f.features_json, f.score_at_decision, f.label, "
            "       COALESCE(f.confidence, 1.0) as confidence, "
            "       COALESCE(r.source, 'profile') as source "
            "FROM feedback f "
            "LEFT JOIN recommendations r ON r.scene_id = f.scene_id"
        ).fetchall()
    return [(r["features_json"], r["score_at_decision"], r["source"],
             r["label"], r["confidence"]) for r in rows]


def all_pending_for_scoring() -> list[sqlite3.Row]:
    with _conn() as conn:
        return conn.execute(
            "SELECT scene_id, features_json, score, source FROM recommendations WHERE status = 'pending'"
        ).fetchall()


def set_model_scores(pairs: list[tuple[str, float]]) -> None:
    with _conn() as conn:
        conn.executemany(
            "UPDATE recommendations SET model_score = ? WHERE scene_id = ?",
            [(score, scene_id) for scene_id, score in pairs],
        )


def set_novelty_scores(pairs: list[tuple[str, float]]) -> None:
    with _conn() as conn:
        conn.executemany(
            "UPDATE recommendations SET novelty_score = ? WHERE scene_id = ?",
            [(score, scene_id) for scene_id, score in pairs],
        )


def set_meta(key: str, value: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_meta(key: str) -> str | None:
    with _conn() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def backfill_weight_components(tag_match_weight: float = 1.0) -> int:
    """One-time migration: recomputes performer_weight_sum/studio_weight_sum/
    tag_weight_sum for every recommendations + feedback row whose
    features_json predates these fields, using *current* taste-profile
    weights as a proxy for what they were at decision time. The profile
    evolves slowly enough that this is a reasonable approximation - far
    better than the alternative of silently defaulting to zero for every
    historical example, which would have taught the model that those
    signals don't matter purely because old rows never had them."""
    weights = all_weights()
    updated = 0
    with _conn() as conn:
        for table, id_col in (("recommendations", "scene_id"), ("feedback", "id")):
            rows = conn.execute(f"SELECT {id_col} AS row_id, features_json FROM {table}").fetchall()
            for row in rows:
                if not row["features_json"]:
                    continue
                features = json.loads(row["features_json"])
                if "performer_weight_sum" in features:
                    continue  # already migrated
                matched = features.get("matched_via", [])
                features["performer_weight_sum"] = sum(
                    weights.get((m[0], m[1]), 0.0) for m in matched if m[0] == "performer"
                )
                features["studio_weight_sum"] = sum(
                    weights.get((m[0], m[1]), 0.0) for m in matched if m[0] == "studio"
                )
                tag_matches = features.get("tag_matches")
                if tag_matches:
                    features["tag_weight_sum"] = sum(t[2] for t in tag_matches) * tag_match_weight
                else:
                    features["tag_weight_sum"] = sum(
                        weights.get((m[0], m[1]), 0.0) for m in matched if m[0] == "tag"
                    )
                conn.execute(
                    f"UPDATE {table} SET features_json = ? WHERE {id_col} = ?",
                    (json.dumps(features), row["row_id"]),
                )
                updated += 1
    return updated


# --------------------------------------------------------------- browsing / transparency
def taste_profile_counts() -> dict[str, int]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT entity_type, COUNT(*) AS c FROM taste_profile GROUP BY entity_type"
        ).fetchall()
    return {r["entity_type"]: r["c"] for r in rows}


def search_taste_profile(entity_type: str | None, q: str | None, limit: int = 200) -> list[sqlite3.Row]:
    sql = "SELECT * FROM taste_profile WHERE 1=1"
    params: list = []
    if entity_type:
        sql += " AND entity_type = ?"
        params.append(entity_type)
    if q:
        sql += " AND entity_name LIKE ?"
        params.append(f"%{q}%")
    sql += " ORDER BY weight DESC LIMIT ?"
    params.append(limit)
    with _conn() as conn:
        return conn.execute(sql, params).fetchall()


_SORT_COLUMNS = {
    "score": "score",
    "model_score": "(model_score IS NOT NULL) DESC, model_score",
    "release_date": "release_date",
    "created_at": "created_at",
}


def search_recommendations(
    status: str | None, source: str | None, q: str | None,
    sort: str = "score", limit: int = 50, offset: int = 0,
) -> tuple[list[sqlite3.Row], int]:
    """Browses the full recommendations table - every scene the engine has
    ever scored, not just the curated top of the /recommendations page.
    Returns (rows, total_count) for pagination."""
    sort_col = _SORT_COLUMNS.get(sort, "score")
    where = ["1=1"]
    params: list = []
    if status and status != "all":
        where.append("status = ?")
        params.append(status)
    if source and source != "all":
        where.append("source = ?")
        params.append(source)
    if q:
        where.append("(title LIKE ? OR studio LIKE ? OR performers LIKE ? OR tags LIKE ?)")
        params.extend([f"%{q}%"] * 4)
    where_sql = " AND ".join(where)
    with _conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM recommendations WHERE {where_sql}", params
        ).fetchone()["c"]
        rows = conn.execute(
            f"SELECT * FROM recommendations WHERE {where_sql} "
            f"ORDER BY {sort_col} DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
    return rows, total


# --------------------------------------------------------------- wildcard categories
def get_wildcard_categories(kind: str | None = None) -> list[dict]:
    """kind: 'tag' | 'studio' | None (both). Stored as a JSON list in meta
    rather than their own table - this is small, user-edited config, not
    data that needs querying/joining."""
    raw = get_meta("wildcard_categories")
    categories = json.loads(raw) if raw else []
    if kind:
        categories = [c for c in categories if c["kind"] == kind]
    return categories


def add_wildcard_category(kind: str, entity_id: str, entity_name: str) -> list[dict]:
    categories = get_wildcard_categories()
    if any(c["kind"] == kind and c["entity_id"] == entity_id for c in categories):
        return categories  # already there
    categories.append({"kind": kind, "entity_id": entity_id, "entity_name": entity_name})
    set_meta("wildcard_categories", json.dumps(categories))
    return categories


def remove_wildcard_category(kind: str, entity_id: str) -> list[dict]:
    categories = get_wildcard_categories()
    categories = [c for c in categories if not (c["kind"] == kind and c["entity_id"] == entity_id)]
    set_meta("wildcard_categories", json.dumps(categories))
    return categories


# --------------------------------------------------------------- tag co-occurrence (Tier 3)
def replace_tag_cooccurrence(pairs: dict[tuple[str, str], int]) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM tag_cooccurrence")
        conn.executemany(
            "INSERT INTO tag_cooccurrence (tag_a, tag_b, count) VALUES (?, ?, ?)",
            [(a, b, c) for (a, b), c in pairs.items()],
        )


def all_tag_cooccurrences() -> list[tuple[str, str, int]]:
    with _conn() as conn:
        rows = conn.execute("SELECT tag_a, tag_b, count FROM tag_cooccurrence").fetchall()
    return [(r["tag_a"], r["tag_b"], r["count"]) for r in rows]


def replace_performer_cooccurrence(pairs: dict[tuple[str, str], int]) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM performer_cooccurrence")
        conn.executemany(
            "INSERT INTO performer_cooccurrence (performer_a, performer_b, count) VALUES (?, ?, ?)",
            [(a, b, c) for (a, b), c in pairs.items()],
        )


def all_performer_cooccurrences() -> list[tuple[str, str, int]]:
    with _conn() as conn:
        rows = conn.execute("SELECT performer_a, performer_b, count FROM performer_cooccurrence").fetchall()
    return [(r["performer_a"], r["performer_b"], r["count"]) for r in rows]


# --------------------------------------------------------------- muted entities
def get_muted_entities() -> list[dict]:
    raw = get_meta("muted_entities")
    return json.loads(raw) if raw else []


def mute_entity(kind: str, entity_id: str, entity_name: str) -> list[dict]:
    muted = get_muted_entities()
    if any(m["kind"] == kind and m["entity_id"] == entity_id for m in muted):
        return muted
    muted.append({"kind": kind, "entity_id": entity_id, "entity_name": entity_name})
    set_meta("muted_entities", json.dumps(muted))
    return muted


def unmute_entity(kind: str, entity_id: str) -> list[dict]:
    muted = get_muted_entities()
    muted = [m for m in muted if not (m["kind"] == kind and m["entity_id"] == entity_id)]
    set_meta("muted_entities", json.dumps(muted))
    return muted


def muted_keys() -> set[tuple[str, str]]:
    return {(m["kind"], m["entity_id"]) for m in get_muted_entities()}


def backfill_embedding_affinity() -> int:
    """One-time migration: approximates embedding_affinity_sum for every
    recommendations + feedback row that predates Tier 3. Uses tag_matches
    from the stored feature snapshot (tags that already overlapped your
    profile at scoring time) rather than the candidate's full tag list,
    which wasn't stored for old rows - this systematically understates
    the value for historical examples versus what new candidates get
    going forward, but it's a real signal rather than a hard zero.
    Run this AFTER a refresh has populated tag_cooccurrence at least once."""
    weights = all_weights()
    tag_weights = {tid: w for (t, tid), w in weights.items() if t == "tag"}
    affinity: dict[str, float] = {}
    updated = 0
    with _conn() as conn:
        for tag_a, tag_b, count in conn.execute(
            "SELECT tag_a, tag_b, count FROM tag_cooccurrence"
        ).fetchall():
            wa, wb = tag_weights.get(tag_a, 0.0), tag_weights.get(tag_b, 0.0)
            if wb > 0:
                affinity[tag_a] = affinity.get(tag_a, 0.0) + count * wb
            if wa > 0:
                affinity[tag_b] = affinity.get(tag_b, 0.0) + count * wa

        for table, id_col in (("recommendations", "scene_id"), ("feedback", "id")):
            rows = conn.execute(f"SELECT {id_col} AS row_id, features_json FROM {table}").fetchall()
            for row in rows:
                if not row["features_json"]:
                    continue
                features = json.loads(row["features_json"])
                if "embedding_affinity_sum" in features:
                    continue
                tag_matches = features.get("tag_matches") or []
                approx = sum(affinity.get(tm[0], 0.0) for tm in tag_matches)
                features["embedding_affinity_sum"] = approx
                conn.execute(
                    f"UPDATE {table} SET features_json = ? WHERE {id_col} = ?",
                    (json.dumps(features), row["row_id"]),
                )
                updated += 1
    return updated


def backfill_performer_affinity() -> int:
    """One-time migration: approximates performer_affinity_sum for every
    recommendations + feedback row that predates performer co-occurrence.
    Uses matched_via performer entries from the stored feature snapshot
    (performers that already triggered inclusion via your top-N gate at
    scoring time) as a proxy for the candidate's full performer list,
    which wasn't stored for old rows - same approximation pattern as
    backfill_embedding_affinity, with the same caveat: understates the
    value for historical examples versus what new candidates get going
    forward. Run this AFTER a refresh has populated performer_cooccurrence
    at least once."""
    weights = all_weights()
    performer_weights = {pid: w for (t, pid), w in weights.items() if t == "performer"}
    affinity: dict[str, float] = {}
    updated = 0
    with _conn() as conn:
        for perf_a, perf_b, count in conn.execute(
            "SELECT performer_a, performer_b, count FROM performer_cooccurrence"
        ).fetchall():
            wa, wb = performer_weights.get(perf_a, 0.0), performer_weights.get(perf_b, 0.0)
            if wb > 0:
                affinity[perf_a] = affinity.get(perf_a, 0.0) + count * wb
            if wa > 0:
                affinity[perf_b] = affinity.get(perf_b, 0.0) + count * wa

        for table, id_col in (("recommendations", "scene_id"), ("feedback", "id")):
            rows = conn.execute(f"SELECT {id_col} AS row_id, features_json FROM {table}").fetchall()
            for row in rows:
                if not row["features_json"]:
                    continue
                features = json.loads(row["features_json"])
                if "performer_affinity_sum" in features:
                    continue
                matched = features.get("matched_via") or []
                approx = sum(
                    affinity.get(m[1], 0.0) for m in matched if m[0] == "performer"
                )
                features["performer_affinity_sum"] = approx
                conn.execute(
                    f"UPDATE {table} SET features_json = ? WHERE {id_col} = ?",
                    (json.dumps(features), row["row_id"]),
                )
                updated += 1
    return updated


# --------------------------------------------------------------- loop closing
def mark_torbox_sent(
    scene_id: str, torbox_type: str, torbox_id: int, torbox_name: str
) -> None:
    """Stores the TorBox download type/ID/name alongside the 'sent' status
    so the loop-closer poller can check completion without re-parsing the
    original grab response."""
    with _conn() as conn:
        conn.execute(
            "UPDATE recommendations SET torbox_type=?, torbox_id=?, torbox_name=? "
            "WHERE scene_id=?",
            (torbox_type, torbox_id, torbox_name, scene_id),
        )


def sent_awaiting_torbox() -> list[sqlite3.Row]:
    """All 'sent' recommendations that have a TorBox ID stored and haven't
    been marked ready yet - the poller's work queue."""
    with _conn() as conn:
        return conn.execute(
            "SELECT scene_id, title, torbox_type, torbox_id, torbox_name "
            "FROM recommendations WHERE status='sent' AND torbox_id IS NOT NULL"
        ).fetchall()


def mark_ready(scene_id: str, torbox_name: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE recommendations SET status='ready', torbox_name=? WHERE scene_id=?",
            (torbox_name, scene_id),
        )


def ready_items() -> list[sqlite3.Row]:
    """Downloads TorBox has completed - available on T:\\ and waiting to be
    pulled to staging."""
    with _conn() as conn:
        return conn.execute(
            "SELECT scene_id, title, studio, torbox_name, decided_at "
            "FROM recommendations WHERE status='ready' ORDER BY decided_at DESC"
        ).fetchall()

def mark_identified(scene_id: str) -> None:
    """Marks a 'ready' item as 'identified' - Stash has successfully
    matched it to StashDB metadata. Clears it from the ready panel."""
    with _conn() as conn:
        conn.execute(
            "UPDATE recommendations SET status='identified' WHERE scene_id=?",
            (scene_id,),
        )


def dismiss_ready(scene_id: str) -> None:
    """Manual dismiss of a 'ready' item - for downloads that won't ever
    be identified (wrong match, megapack, etc). Moves to 'dismissed'
    status so it no longer clutters the ready panel."""
    with _conn() as conn:
        conn.execute(
            "UPDATE recommendations SET status='dismissed' WHERE scene_id=? AND status='ready'",
            (scene_id,),
        )


def dismiss_all_ready() -> int:
    """Dismiss every currently-ready item at once."""
    with _conn() as conn:
        return conn.execute(
            "UPDATE recommendations SET status='dismissed' WHERE status='ready'"
        ).rowcount

# --------------------------------------------------------------- watch feedback

def init_watch_feedback_table(conn) -> None:
    """Called from init_db — separate function so it's clear this is a
    migration that runs once and is idempotent after that."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watch_feedback (
            scene_id TEXT PRIMARY KEY,
            checked_at TEXT NOT NULL,
            play_count INTEGER,
            play_duration REAL,
            o_counter INTEGER,
            rating100 INTEGER,
            label_revised INTEGER,
            confidence REAL
        )
    """)


def scenes_awaiting_watch_feedback(min_age_hours: int = 24) -> list[sqlite3.Row]:
    """Sent/ready items old enough for Stash to have real watch signal on -
    haven't been checked yet. scene_id IS the StashDB UUID, which is what
    stashdb_check.get_scene() and the Stash stash_ids lookup both use."""
    from datetime import datetime, timezone, timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=min_age_hours)).isoformat()
    with _conn() as conn:
        return conn.execute(
            "SELECT r.scene_id, r.title, r.decided_at "
            "FROM recommendations r "
            "LEFT JOIN watch_feedback wf ON wf.scene_id = r.scene_id "
            "WHERE r.status IN ('sent','ready','identified') "
            "AND r.decided_at < ? "
            "AND wf.scene_id IS NULL",
            (cutoff,),
        ).fetchall()


def upsert_watch_feedback(
    scene_id: str, play_count: int, play_duration: float,
    o_counter: int, rating100: int | None,
    label_revised: int, confidence: float,
) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as conn:
        conn.execute("""
            INSERT INTO watch_feedback
                (scene_id, checked_at, play_count, play_duration,
                 o_counter, rating100, label_revised, confidence)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(scene_id) DO UPDATE SET
                checked_at=excluded.checked_at,
                play_count=excluded.play_count,
                play_duration=excluded.play_duration,
                o_counter=excluded.o_counter,
                rating100=excluded.rating100,
                label_revised=excluded.label_revised,
                confidence=excluded.confidence
        """, (scene_id, now, play_count, play_duration,
              o_counter, rating100, label_revised, confidence))
        # Also update the feedback table label and confidence if revised
        conn.execute("""
            UPDATE feedback SET label=?, confidence=?
            WHERE scene_id=?
        """, (label_revised, confidence, scene_id))


def compute_watch_outcome(
    play_count: int,
    play_duration: float,
    o_counter: int,
    rating100: int | None,
    days_since_decision: float,
) -> tuple[int, float]:
    """Given Stash watch signals for a downloaded scene, returns
    (revised_label, confidence) to replace the provisional label=1/
    confidence=1.0 that 'clicked download' generated.

    This is the core of the outcome-based label pipeline: 'clicked
    download' is a noisy intent signal; actual watch behaviour is a
    genuine outcome signal. The two are very different things.

    Confidence scale:
        4.0 = explicit 5-star rating (most deliberate signal possible)
        3.0 = o_counter > 0 (strongest implicit signal in this domain)
        2.0 = played and watched >50% of expected duration
        1.5 = played at all
        0.5 = downloaded but never opened after 7+ days (likely a miss)
        1.0 = checked too soon to know yet (< min_age threshold)
    """
    # Explicit 5-star rating: strongest possible signal
    if rating100 and rating100 >= 80:
        return (1, 3.0 + (rating100 / 100) * 1.0)  # 80->3.8, 100->4.0

    # o_counter: genuine engagement, hard to fake
    if o_counter > 0:
        return (1, 3.0)

    # Played and engaged meaningfully
    if play_count and play_count > 0:
        if play_duration and play_duration > 300:  # >5 min of actual watching
            return (1, 2.0)
        return (1, 1.5)

    # Downloaded but never opened after enough time has passed
    if days_since_decision >= 7:
        # Label stays 1 (it was intentionally downloaded) but very low
        # confidence - it was either a wrong grab, or something you
        # downloaded and forgot about. Either way, not a strong signal.
        return (1, 0.3)

    # Still too early to draw conclusions - keep provisional
    return (1, 1.0)

def retroactively_downweight_ambiguous_skips() -> int:
    """One-time fix: all historical skips were logged at confidence=1.0
    (same weight as a deliberate 'not interested'), but most were just
    'not now' decisions. Down-weight them to 0.3 so they no longer
    pollute the model with false hard-negative signal.

    Only touches rows where confidence is exactly 1.0 and label=0
    (the old default). 'Not interested' actions going forward will be
    confidence=1.5 and are intentionally left alone."""
    with _conn() as conn:
        n = conn.execute(
            "UPDATE feedback SET confidence=0.3 WHERE label=0 AND confidence=1.0"
        ).rowcount
    return n


def mark_download_failed(scene_id: str, failed_release_name: str) -> bool:
    """Called by the loop-closer when TorBox reports a download failed or
    is frozen. Resets the recommendation to 'pending' so it reappears,
    appends the failed release name to the JSON array of all previously-
    tried names so retries skip EVERY failed attempt (not just the last),
    and increments retry_count for visibility.

    No hard retry limit — keeps going until Prowlarr returns no new valid
    results that aren't in the failed names list. Returns True if reset
    to pending, False if the recommendation row wasn't found."""
    import json
    with _conn() as conn:
        row = conn.execute(
            "SELECT retry_count, failed_release_names FROM recommendations WHERE scene_id=?",
            (scene_id,)
        ).fetchone()
        if row is None:
            return False
        # Append to the JSON array of all previously-failed release names
        existing = json.loads(row["failed_release_names"] or "[]")
        if failed_release_name and failed_release_name not in existing:
            existing.append(failed_release_name)
        new_count = (row["retry_count"] or 0) + 1
        conn.execute(
            "UPDATE recommendations SET status='pending', torbox_id=NULL, torbox_type=NULL, "
            "torbox_name=NULL, retry_count=?, failed_release_names=?, failed_release_name=?, "
            "check_failures=0 "
            "WHERE scene_id=?",
            (new_count, json.dumps(existing), failed_release_name, scene_id),
        )
        return True


def permanently_failed_items() -> list[sqlite3.Row]:
    """Downloads that exhausted all retries - shown on page so user knows."""
    with _conn() as conn:
        return conn.execute(
            "SELECT scene_id, title, studio, failed_release_name, decided_at "
            "FROM recommendations WHERE status='download_failed' ORDER BY decided_at DESC"
        ).fetchall()


def mark_queued(scene_id: str, studio: str, title: str,
                performers: str, date: str, failed_names: list) -> None:
    """Marks a recommendation as queued when TorBox's active slot limit
    is hit. Stores all search context so the loop-closer can dispatch it
    automatically when a slot frees up."""
    import json
    with _conn() as conn:
        conn.execute(
            "UPDATE recommendations SET status='queued', queued_at=?, "
            "queue_studio=?, queue_title=?, queue_performers=?, queue_date=?, "
            "failed_release_names=?, torbox_id=NULL, torbox_type=NULL "
            "WHERE scene_id=?",
            (_now(), studio, title, performers, date,
             json.dumps(failed_names), scene_id),
        )


def queued_items() -> list[sqlite3.Row]:
    """All downloads waiting for a TorBox slot, in queue order."""
    with _conn() as conn:
        return conn.execute(
            "SELECT scene_id, title, studio, performers, release_date, "
            "queue_studio, queue_title, queue_performers, queue_date, "
            "failed_release_names, queued_at "
            "FROM recommendations WHERE status='queued' ORDER BY queued_at"
        ).fetchall()


def record_check_failure(scene_id: str) -> int:
    """Increments check_failures when a TorBox status lookup fails to
    return usable data (network error, or the ID no longer exists on
    TorBox's end — confirmed to happen: a 500 with empty body for IDs
    that are genuinely gone from TorBox's full list). Returns the new
    count so the caller can decide whether to give up."""
    with _conn() as conn:
        row = conn.execute(
            "UPDATE recommendations SET check_failures = check_failures + 1 "
            "WHERE scene_id=? RETURNING check_failures",
            (scene_id,),
        ).fetchone()
        return row["check_failures"] if row else 0


def reset_check_failures(scene_id: str) -> None:
    """Called whenever a status check succeeds - clears the failure
    streak so a single transient blip doesn't compound toward the
    give-up threshold."""
    with _conn() as conn:
        conn.execute(
            "UPDATE recommendations SET check_failures = 0 WHERE scene_id=?",
            (scene_id,),
        )
