"""
loop_closer.py
==============
Closes the recommendation loop: after a scene is sent to TorBox, polls
until TorBox reports the download is ready on the cloud (accessible via
the T:\\ rclone mount, which is what Stash's own library path points at -
there's no local download or manual copy step; Stash scans and streams
directly from T:\\), marks it 'ready' in the DB, and triggers a Stash
library scan + Identify so the scene lands as a matched, tagged entry in
the library rather than a raw file.

Architecture: a single background asyncio task started at FastAPI startup,
sleeping between poll cycles. Does not block any request handling.
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

import db
import stashdb_check
import torbox

log = logging.getLogger("bridge")

POLL_INTERVAL_SECONDS = 300  # check every 5 minutes


def _is_torrent_ready(data: dict) -> bool:
    state = data.get("download_state", "")
    return state in ("cached", "completed") and bool(data.get("download_present"))


def _is_usenet_ready(data: dict) -> bool:
    state = data.get("download_state", "")
    progress = data.get("progress", 0)
    return state == "completed" and progress >= 1


def _is_failed(data: dict) -> bool:
    """download_state starting with 'failed' AND no file present."""
    state = data.get("download_state", "")
    return state.lower().startswith("failed") and not data.get("download_present")


def _is_stalled(data: dict) -> bool:
    """Torrent is stuck with no seeds and can't make progress. Not the same
    as failed — TorBox hasn't given up, but it can't proceed either. We
    treat stalled the same as failed: delete and try a different release."""
    state = data.get("download_state", "")
    return "stalled" in state.lower() and "no seeds" in state.lower()


def _is_frozen(data: dict) -> bool:
    """A download that is supposedly active (download_speed present) but has
    had speed=0 and no state change for > FROZEN_MINUTES. Uses updated_at
    since TorBox updates that field whenever progress changes — if it hasn't
    changed in a while while the download is 'active', it's genuinely stuck."""
    FROZEN_MINUTES = 20
    if not data.get("active"):
        return False
    if (data.get("download_speed") or 0) > 0:
        return False  # actually moving
    state = data.get("download_state", "")
    if state in ("completed", "cached") or state.startswith("failed"):
        return False
    updated_at_str = data.get("updated_at") or ""
    if not updated_at_str:
        return False
    try:
        updated = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
        stale_for = (datetime.now(timezone.utc) - updated).total_seconds() / 60
        return stale_for > FROZEN_MINUTES
    except Exception:  # noqa: BLE001
        return False


def _mount_folder_name(data: dict) -> str:
    """Derive the folder name as it actually appears on the T:\\ rclone
    mount. TorBox's top-level 'name' field is NOT what rclone exposes -
    e.g. name='Foo Bar XXX 1080p MP4-WRB [XC]' (spaces) but the mount
    shows the first path segment of the file entry:
    'Foo.Bar.XXX.1080p.MP4-WRB[XC]' (dots, no space before [XC]).
    Using the wrong string makes the targeted scan hit a nonexistent
    path and silently find nothing. We take the first path segment of
    files[0]['name']; if there's no nested path (single-file torrent
    with no containing folder), fall back to the top-level name."""
    files = data.get("files") or []
    if files:
        first = files[0].get("name") or ""
        # Path segments use forward slashes in TorBox's file listing
        segment = first.split("/")[0].strip()
        if segment and segment != first:  # there was a containing folder
            return segment
    return (data.get("name") or "").strip()


async def _trigger_stash_scan_and_identify(stash_url: str, torbox_name: str) -> None:
    """Fires a targeted Stash scan + Identify restricted to the specific
    folder TorBox just made available. Using paths= keeps both operations
    fast - a full metadataScan on thousands of scenes takes hours, but
    scoping it to the one new folder completes in seconds. The scan must
    run first so the new file is in the Stash DB before Identify can
    match it against StashDB metadata. Both are async Stash jobs that
    return a job_id immediately and run in the background."""
    path = f"T:\\{torbox_name}" if torbox_name else None
    scan_query = {
        "query": "mutation ($p: [String!]) { metadataScan(input: {paths: $p}) }",
        "variables": {"p": [path] if path else None},
    }
    identify_query = {
        "query": "mutation ($p: [String!]) { metadataIdentify(input: {sources: [], paths: $p}) }",
        "variables": {"p": [path] if path else None},
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r1 = await client.post(stash_url, json=scan_query)
            r1.raise_for_status()
            scan_job = r1.json().get("data", {}).get("metadataScan")
            log.info("loop_closer: triggered targeted Stash scan path=%s job_id=%s", path, scan_job)
            # Small gap so the scan actually has time to queue before Identify starts
            await asyncio.sleep(5)
            r2 = await client.post(stash_url, json=identify_query)
            r2.raise_for_status()
            identify_job = r2.json().get("data", {}).get("metadataIdentify")
            log.info("loop_closer: triggered targeted Stash Identify path=%s job_id=%s", path, identify_job)
    except Exception as e:  # noqa: BLE001
        log.warning("loop_closer: failed to trigger Stash scan/identify: %s", e)

async def poll_once(torbox_api_key: str, stash_url: str) -> int:
    """One poll cycle. For each 'sent' item with a TorBox ID:
    - If ready: mark ready, trigger Stash scan+identify
    - If failed/stalled/frozen: delete from TorBox, reset to pending for retry
    Returns the count of newly-ready items."""
    pending = db.sent_awaiting_torbox()
    if not pending:
        return 0

    newly_ready: list[str] = []
    newly_ready_names: list[str] = []
    for row in pending:
        try:
            if row["torbox_type"] == "torrent":
                data = await torbox.check_torrent_ready(row["torbox_id"], api_key=torbox_api_key)
            elif row["torbox_type"] == "usenet":
                data = await torbox.check_usenet_ready(row["torbox_id"], api_key=torbox_api_key)
            else:
                continue

            if data is None:
                # Couldn't get status - either a transient network blip or
                # (confirmed to happen) the ID genuinely no longer exists
                # on TorBox's end, which returns a 500 with no useful body
                # rather than a clean 404. Track consecutive failures so a
                # permanently-gone item doesn't poll forever with no exit.
                failures = db.record_check_failure(row["scene_id"])
                if failures >= 3:
                    log.warning(
                        "loop_closer: '%s' unreachable on TorBox after %d checks "
                        "(likely purged/gone) — recycling for retry",
                        row["title"], failures,
                    )
                    db.mark_download_failed(row["scene_id"], row["torbox_name"] or "")
                continue
            db.reset_check_failures(row["scene_id"])

            # Determine disposition
            should_recycle = (
                _is_failed(data) or _is_stalled(data) or _is_frozen(data)
            )

            if should_recycle:
                state = data.get("download_state", "unknown")
                reason = ("frozen" if _is_frozen(data) else
                          "stalled" if _is_stalled(data) else "failed")
                failed_name = data.get("name") or ""
                log.warning(
                    "loop_closer: '%s' %s (state=%s) — deleting and resetting for retry",
                    row["title"], reason, state
                )
                if row["torbox_type"] == "usenet":
                    await torbox.delete_usenet(row["torbox_id"], api_key=torbox_api_key)
                else:
                    await torbox.delete_torrent(row["torbox_id"], api_key=torbox_api_key)
                db.mark_download_failed(row["scene_id"], failed_name)
                continue

            if row["torbox_type"] == "torrent":
                ready = _is_torrent_ready(data)
            else:
                ready = _is_usenet_ready(data)

            if ready:
                name = _mount_folder_name(data)
                db.mark_ready(row["scene_id"], name)
                newly_ready.append(row["title"] or row["scene_id"])
                newly_ready_names.append(name)
                log.info("loop_closer: '%s' ready on T:\\\\%s", row["title"], name)

        except Exception as e:  # noqa: BLE001
            log.warning("loop_closer: error checking %s id=%s: %s",
                        row["torbox_type"], row["torbox_id"], e)

    if newly_ready:
        log.info("loop_closer: %d newly ready", len(newly_ready))
        for name in newly_ready_names:
            await _trigger_stash_scan_and_identify(stash_url, name)

    return len(newly_ready)


async def dispatch_queued(torbox_api_key: str) -> int:
    """Third job the poller runs: if there are queued downloads waiting for
    a TorBox slot, check how many active downloads are currently running.
    If below the limit, dispatch the oldest queued item by re-searching
    Prowlarr and adding to TorBox. Imports _grab_best dynamically to avoid
    circular imports (app.py imports loop_closer; loop_closer can't import
    app at module level)."""
    queued = db.queued_items()
    if not queued:
        return 0

    # Count currently active downloads across usenet + torrents
    try:
        u_data = await torbox.check_usenet_ready(-1, api_key=torbox_api_key)
    except Exception:  # noqa: BLE001
        u_data = None
    # Use the full list endpoint instead
    active_count = 0
    try:
        async with __import__("httpx").AsyncClient(timeout=20) as client:
            import os
            ru = await client.get(
                "https://api.torbox.app/v1/api/usenet/mylist",
                params={"bypass_cache": "true"},
                headers={"Authorization": f"Bearer {torbox_api_key}"},
            )
            rt = await client.get(
                "https://api.torbox.app/v1/api/torrents/mylist",
                params={"bypass_cache": "true"},
                headers={"Authorization": f"Bearer {torbox_api_key}"},
            )
        u_items = ru.json().get("data") or []
        t_items = rt.json().get("data") or []
        u_active = sum(1 for i in u_items if i.get("active") and
                       i.get("download_state") not in ("completed", "cached"))
        t_active = sum(1 for i in t_items if i.get("active") and
                       i.get("download_state") not in ("completed", "cached", "seeding"))
        active_count = u_active + t_active
    except Exception as e:  # noqa: BLE001
        log.warning("loop_closer dispatch_queued: couldn't check active count: %s", e)
        return 0

    ACTIVE_LIMIT = 10
    slots_free = ACTIVE_LIMIT - active_count
    log.info("loop_closer dispatch_queued: %d active, %d queued, %d slots free",
             active_count, len(queued), slots_free)

    if slots_free <= 0:
        return 0

    # Dispatch from queue — oldest first, one per slot available
    dispatched = 0
    from app import _grab_best as grab_best, TORBOX_API_KEY  # deferred import
    import json

    for row in queued[:slots_free]:
        studio = row["queue_studio"] or row["studio"] or ""
        title = row["queue_title"] or row["title"] or ""
        performers = row["queue_performers"] or row["performers"] or ""
        date = row["queue_date"] or row["release_date"] or ""
        failed_names = json.loads(row["failed_release_names"] or "[]")

        log.info("loop_closer: dispatching queued '%s'", title[:50])
        try:
            res = await grab_best(studio, title, performers, date,
                                  skip_release_names=failed_names)
        except Exception as e:  # noqa: BLE001
            log.warning("loop_closer: dispatch failed for '%s': %s", title[:40], e)
            continue

        if res.get("ok"):
            # Update to sent status and store TorBox IDs
            with db._conn() as c:
                c.execute(
                    "UPDATE recommendations SET status='sent', torbox_type=?, torbox_id=?, "
                    "torbox_name=?, queued_at=NULL WHERE scene_id=?",
                    (
                        "usenet" if (res.get("data") or {}).get("usenetdownload_id") else "torrent",
                        (res.get("data") or {}).get("torrent_id") or
                        (res.get("data") or {}).get("usenetdownload_id"),
                        (res.get("data") or {}).get("name") or "",
                        row["scene_id"],
                    ),
                )
            log.info("loop_closer: dispatched '%s' -> sent", title[:50])
            dispatched += 1
        elif res.get("active_limit"):
            log.info("loop_closer: hit active limit while dispatching — stopping queue")
            break
        else:
            # All options exhausted for this scene
            with db._conn() as c:
                c.execute("UPDATE recommendations SET status='download_failed' WHERE scene_id=?",
                          (row["scene_id"],))

    return dispatched


async def run_watch_feedback_pass(stash_url: str) -> int:
    """Second job the poller runs on every cycle: for each downloaded scene
    that's old enough (>24h) and hasn't had its watch signals checked yet,
    query Stash by StashDB UUID and revise the label+confidence based on
    what actually happened (play count, o-counter, rating) rather than
    leaving the provisional 'clicked download = good' signal forever."""
    from datetime import timedelta
    pending = db.scenes_awaiting_watch_feedback(min_age_hours=24)
    if not pending:
        return 0

    updated = 0
    for row in pending:
        stash_data = await stashdb_check.get_stash_watch_signals(row["scene_id"], stash_url)
        if stash_data is None:
            continue  # not in Stash yet; will retry on a future cycle

        play_count = stash_data.get("play_count") or 0
        play_duration = stash_data.get("play_duration") or 0.0
        o_counter = stash_data.get("o_counter") or 0
        rating100 = stash_data.get("rating100")

        decided_at = row.get("decided_at") or ""
        try:
            then = datetime.fromisoformat(decided_at.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - then).total_seconds() / 86400
        except Exception:  # noqa: BLE001
            days = 7  # assume old enough

        label, confidence = db.compute_watch_outcome(
            play_count, play_duration, o_counter, rating100, days
        )

        db.upsert_watch_feedback(
            row["scene_id"], play_count, play_duration,
            o_counter, rating100, label, confidence,
        )
        log.info(
            "loop_closer watch_feedback: '%s' play=%d o=%d rating=%s -> "
            "label=%d confidence=%.1f",
            row.get("title", "")[:40], play_count, o_counter,
            rating100, label, confidence,
        )
        updated += 1

    return updated


async def run_background_poller(torbox_api_key: str, stash_url: str) -> None:
    """Long-running asyncio task. Three jobs per cycle:
    1. TorBox poll: ready/failed/stalled/frozen detection
    2. Queue dispatch: send queued items when slots free up
    3. Watch-feedback: revise labels from Stash play/rating signals"""
    log.info("loop_closer: background poller started (interval=%ds)", POLL_INTERVAL_SECONDS)
    while True:
        try:
            n = await poll_once(torbox_api_key, stash_url)
            if n:
                log.info("loop_closer: %d newly ready", n)
        except Exception as e:  # noqa: BLE001
            log.warning("loop_closer: poll cycle error: %s", e)
        try:
            d = await dispatch_queued(torbox_api_key)
            if d:
                log.info("loop_closer: dispatched %d queued downloads", d)
        except Exception as e:  # noqa: BLE001
            log.warning("loop_closer: dispatch_queued error: %s", e)
        try:
            w = await run_watch_feedback_pass(stash_url)
            if w:
                log.info("loop_closer: watch_feedback updated %d scenes", w)
        except Exception as e:  # noqa: BLE001
            log.warning("loop_closer: watch_feedback error: %s", e)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
