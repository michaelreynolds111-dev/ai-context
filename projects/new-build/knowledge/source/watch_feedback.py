"""
watch_feedback.py
=================
Closes the outcome arc: 24-48h after a scene is downloaded, queries Stash
to find out what actually happened (did you watch it, rate it, re-watch it,
use the o-counter?) and revises the provisional training label accordingly.

The fundamental problem this solves: the current label is "user clicked
download" which is an INTENT signal, not an OUTCOME signal. A downloaded
scene that was never opened (wrong grab, or just not right) currently gets
the same label=1 as one you watched 5 times and rated 100. This trains the
model to predict clicks, not satisfaction. 

With this module:
- label=1, confidence=0.5  initially  (provisional: you tried it)
- label=1, confidence=4.0  if rated 5-star  (explicit, strongest signal)
- label=1, confidence=3.0  if o_counter > 0  (strongest implicit signal)
- label=1, confidence=2.0  if played >80% through  (completed watch)
- label=1, confidence=1.5  if play_count > 1  (re-watched)
- label=1, confidence=1.0  if play_count == 1  (watched once)
- label=0, confidence=1.0  if never played after 7 days  (miss)
- label=0, confidence=0.5  if opened <60s and never returned  (rejected)
"""

import asyncio
import logging

import httpx

import db

log = logging.getLogger("bridge")

# Stash GraphQL query to find a scene by its StashDB UUID. Stash stores
# the cross-reference in stash_ids on each scene, so we query all scenes
# and filter. Not efficient at scale but this runs once per downloaded
# scene, 24h later, so it's fine.
_FIND_BY_STASHDB_ID = """
query ($stashdb_id: String!) {
  findScenes(
    scene_filter: {
      stash_id_endpoint: {endpoint: "https://stashdb.org", stash_id: $stashdb_id, modifier: EQUALS}
    }
    filter: {per_page: 1}
  ) {
    scenes {
      id title
      play_count
      play_duration
      o_counter
      rating100
      last_played_at
      files { duration }
    }
  }
}"""


def _compute_label_and_confidence(
    play_count: int,
    play_duration: float,
    o_counter: int,
    rating100: int | None,
    file_duration: float | None,
    days_since_download: float,
) -> tuple[int, float]:
    """Derives a revised (label, confidence) pair from Stash watch signals.
    Returns (label, confidence) where confidence is a sample_weight for
    training - higher = more reliable signal, lower = noisier."""

    # Explicit 5-star rating is the strongest possible signal
    if rating100 is not None and rating100 >= 80:
        return 1, 4.0 if rating100 == 100 else 2.5

    # o_counter is the strongest implicit signal in this domain
    if o_counter and o_counter > 0:
        return 1, 3.0

    # Completed watch (>80% of file duration)
    if play_duration and file_duration and play_duration >= file_duration * 0.8:
        return 1, 2.0

    # Re-watched (came back to it)
    if play_count and play_count > 1:
        return 1, 1.5

    # Watched once (at least opened and played)
    if play_count and play_count >= 1:
        return 1, 1.0

    # Low-rated - explicit negative signal
    if rating100 is not None and rating100 <= 40:
        return 0, 2.0

    # Never played after 7+ days - almost certainly a miss or wrong grab.
    # The provisional label=1 was too generous.
    if days_since_download >= 7 and not play_count:
        return 0, 1.0

    # Downloaded but not yet old enough to be sure - keep provisional positive
    # with low confidence so it doesn't dominate training
    return 1, 0.5


async def check_scene_in_stash(stash_url: str, stashdb_scene_id: str) -> dict | None:
    """Looks up a scene in Stash by its StashDB UUID. Returns the scene
    dict with play/rating fields, or None if not found (e.g. Stash hasn't
    scanned the file yet, or it was deleted)."""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                stash_url,
                json={"query": _FIND_BY_STASHDB_ID,
                      "variables": {"stashdb_id": stashdb_scene_id}},
            )
            resp.raise_for_status()
            data = resp.json()
            scenes = data.get("data", {}).get("findScenes", {}).get("scenes", [])
            return scenes[0] if scenes else None
    except Exception as e:  # noqa: BLE001
        log.warning("watch_feedback: Stash lookup failed for %s: %s", stashdb_scene_id, e)
        return None


async def run_watch_feedback_pass(stash_url: str, min_age_hours: int = 24) -> int:
    """Check all sent/ready scenes old enough to have meaningful watch signal
    and update their training labels with the outcome. Returns the count of
    scenes checked."""
    pending = db.scenes_awaiting_watch_feedback(min_age_hours)
    if not pending:
        return 0

    log.info("watch_feedback: checking %d scenes for outcome signal", len(pending))
    checked = 0

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    for row in pending:
        scene_id = row["scene_id"]
        decided_at = row["decided_at"]

        # How long since download?
        try:
            dt = datetime.fromisoformat(decided_at.replace("Z", "+00:00"))
            days_since = (now - dt).total_seconds() / 86400
        except Exception:
            days_since = 0

        scene = await check_scene_in_stash(stash_url, scene_id)

        if scene is None:
            # Not in Stash yet - if it's been >7 days and still not there,
            # it was probably a failed/wrong grab. Mark with low-confidence 0.
            if days_since >= 7:
                label, confidence = 0, 0.5
                db.upsert_watch_feedback(
                    scene_id, 0, 0.0, 0, None, label, confidence
                )
                log.info("watch_feedback: '%s' not in Stash after %.0fd -> label=0 (conf=%.1f)",
                         row["title"][:40], days_since, confidence)
                checked += 1
            continue

        # Extract signals
        play_count = scene.get("play_count") or 0
        play_duration = scene.get("play_duration") or 0.0
        o_counter = scene.get("o_counter") or 0
        rating100 = scene.get("rating100")
        files = scene.get("files") or []
        file_duration = files[0].get("duration") if files else None

        label, confidence = _compute_label_and_confidence(
            play_count, play_duration, o_counter, rating100,
            file_duration, days_since,
        )

        db.upsert_watch_feedback(
            scene_id, play_count, play_duration,
            o_counter, rating100, label, confidence,
        )
        log.info(
            "watch_feedback: '%s' -> play=%d dur=%.0fs o=%d rating=%s "
            "label=%d conf=%.1f",
            (row["title"] or "")[:40], play_count, play_duration,
            o_counter, rating100, label, confidence,
        )
        checked += 1

    log.info("watch_feedback: pass complete, %d scenes updated", checked)
    return checked
