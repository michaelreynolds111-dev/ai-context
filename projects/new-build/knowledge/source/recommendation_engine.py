"""
recommendation_engine.py
=========================
Orchestrates a full recommendation refresh:
  1. Rebuild the taste profile from your Stash library.
  2. Pull candidate scenes from StashDB for your top performers/studios.
  3. Filter out anything you already own or have already decided on.
  4. Score what's left (taste-profile weight match + tag overlap + recency).
  5. Upsert into the recommendations table for the /recommendations page.
"""

from datetime import datetime, timezone
import json
import re as _re

import db
import ml_model

# StashDB-level compilation/best-of filter. The pack regex in prowlarr.py
# catches *release filenames*; this catches StashDB's own *canonical scene
# titles* for compilation content. Without this, "The Best Of Courthouse
# Sex" scores high on tag matches and dominates the top of the page because
# it legitimately matches many of your taste profile tags.
_STASHDB_COMPILATION_RE = _re.compile(
    r"""
    \bthe\s+best\s+of\b   |  # "The Best Of..."
    \bbest\s+of\b          |  # "Best Of..."
    \bselects?\b           |  # "MYLF Selects", "Reptyle Select"
    \brecap\b              |  # "2024 Recap"
    \ball\s+stars?\b       |  # "All Stars"
    \bcompilation\b           # "Compilation: ..."
    """,
    _re.IGNORECASE | _re.VERBOSE,
)


def _is_stashdb_compilation(scene: dict) -> bool:
    return bool(_STASHDB_COMPILATION_RE.search(scene.get("title") or ""))
import settings as cfg
import stashdb_candidates
import taste_profile


def _days_since(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        released = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - released).days


def compute_tag_affinity(weights: dict) -> dict[str, float]:
    """Tier 3: for every tag that's ever co-occurred (in your library) with
    a tag you're weighted on, precompute a single affinity score - how
    much, weighted by how much you like the tags it keeps company with,
    this tag shows up in similar contexts. This is what lets a candidate
    score well via tags it doesn't even have in your profile, by sharing
    context with tags it does have. Computed once per refresh, not once
    per candidate - O(cooccurrence rows), not O(candidates * tags).

    NORMALIZED: each tag's affinity is the co-occurrence-count-weighted
    *average* of its neighbours' profile weights, not the raw sum. Without
    this, a tag that simply appears in many scenes accumulated an unbounded
    sum (millions), and compilation scenes stuffed with 100+ tags dominated
    the rankings purely on tag count rather than relevance. Averaging keeps
    every tag's affinity on the same scale as an actual profile weight."""
    tag_weights = {tid: w for (t, tid), w in weights.items() if t == "tag"}
    affinity_num: dict[str, float] = {}
    affinity_den: dict[str, float] = {}
    for tag_a, tag_b, count in db.all_tag_cooccurrences():
        wa, wb = tag_weights.get(tag_a, 0.0), tag_weights.get(tag_b, 0.0)
        if wb > 0:
            affinity_num[tag_a] = affinity_num.get(tag_a, 0.0) + count * wb
            affinity_den[tag_a] = affinity_den.get(tag_a, 0.0) + count
        if wa > 0:
            affinity_num[tag_b] = affinity_num.get(tag_b, 0.0) + count * wa
            affinity_den[tag_b] = affinity_den.get(tag_b, 0.0) + count
    return {tid: affinity_num[tid] / affinity_den[tid] for tid in affinity_num}


def compute_performer_affinity(weights: dict) -> dict[str, float]:
    """Same idea as compute_tag_affinity, for performers: catches an
    unfamiliar performer who frequently appears alongside performers you
    already rate highly, even when they've never shared a scene with
    anyone currently in your top-N gate. Normalized the same way (weighted
    average of co-stars' weights, not an unbounded sum)."""
    performer_weights = {pid: w for (t, pid), w in weights.items() if t == "performer"}
    affinity_num: dict[str, float] = {}
    affinity_den: dict[str, float] = {}
    for perf_a, perf_b, count in db.all_performer_cooccurrences():
        wa, wb = performer_weights.get(perf_a, 0.0), performer_weights.get(perf_b, 0.0)
        if wb > 0:
            affinity_num[perf_a] = affinity_num.get(perf_a, 0.0) + count * wb
            affinity_den[perf_a] = affinity_den.get(perf_a, 0.0) + count
        if wa > 0:
            affinity_num[perf_b] = affinity_num.get(perf_b, 0.0) + count * wa
            affinity_den[perf_b] = affinity_den.get(perf_b, 0.0) + count
    return {pid: affinity_num[pid] / affinity_den[pid] for pid in affinity_num}


def _score(scene: dict, weights: dict, s: dict, affinity: dict, performer_affinity: dict) -> tuple[float, dict]:
    matched = scene.get("matched_via", [])
    performer_weight_sum = sum(weights.get((t, i), 0.0) for t, i, _ in matched if t == "performer")
    studio_weight_sum = sum(weights.get((t, i), 0.0) for t, i, _ in matched if t == "studio")

    tag_matches = []
    raw_tag_weight = 0.0
    for tag in scene.get("tags") or []:
        w = weights.get(("tag", tag["id"]), 0.0)
        if w > 0:
            raw_tag_weight += w * s["tag_match_weight"]
            tag_matches.append((tag["id"], tag["name"], w))
    # Volume-dampened with the same exponent used in the taste profile, so a
    # compilation matching 100 of your tags scores more than one matching
    # 10 - but not 10x more, which is what let tag-stuffed "Best Of" scenes
    # dominate. sqrt(sum) keeps genuine multi-match relevance while killing
    # the runaway.
    tag_weight_sum = raw_tag_weight ** s["volume_dampening_exponent"]

    days = _days_since(scene.get("release_date"))
    recency_bonus = 0.0
    if days is not None and days < s["recency_window_days"]:
        recency_bonus = (s["recency_window_days"] - days) * s["recency_weight"]

    # Averaged, not summed: a compilation with 100 tags shouldn't out-score
    # a focused scene just by having more tags. This is the mean affinity
    # across the scene's tags - "are this scene's tags, on average, in good
    # company with what you like" - which is scale-invariant to tag count.
    scene_tags = scene.get("tags") or []
    if scene_tags:
        embedding_affinity_sum = sum(affinity.get(t["id"], 0.0) for t in scene_tags) / len(scene_tags)
    else:
        embedding_affinity_sum = 0.0
    # Performers come back wrapped as {"performer": {...}} (StashDB's
    # PerformerCredit shape), unlike the flat tag list above.
    scene_performers = scene.get("performers") or []
    if scene_performers:
        performer_affinity_sum = sum(
            performer_affinity.get(p["performer"]["id"], 0.0) for p in scene_performers
        ) / len(scene_performers)
    else:
        performer_affinity_sum = 0.0

    # `score` (the Tier 1 display/sort value) is still the sum of these -
    # but the components are now stored separately too, so Tier 2 can learn
    # its own weighting per signal instead of only seeing one blended number.
    score = (
        performer_weight_sum + studio_weight_sum + tag_weight_sum + recency_bonus
        + embedding_affinity_sum * s["embedding_weight"]
        + performer_affinity_sum * s["performer_embedding_weight"]
    )

    features = {
        "matched_via": matched,
        "tag_matches": tag_matches,
        "performer_weight_sum": performer_weight_sum,
        "studio_weight_sum": studio_weight_sum,
        "tag_weight_sum": tag_weight_sum,
        "embedding_affinity_sum": embedding_affinity_sum,
        "performer_affinity_sum": performer_affinity_sum,
        "days_since_release": days,
        "recency_bonus": recency_bonus,
    }
    return score, features


def _score_wildcard(scene: dict, s: dict) -> tuple[float, dict]:
    """Wildcard candidates don't compete against profile weights - they just
    need to rank sensibly among themselves, so this scores on how many
    wildcard categories matched plus the same recency bonus."""
    matched = scene.get("matched_via", [])
    score = s["wildcard_base_score"] * len(matched)

    days = _days_since(scene.get("release_date"))
    recency_bonus = 0.0
    if days is not None and days < s["recency_window_days"]:
        recency_bonus = (s["recency_window_days"] - days) * s["recency_weight"]
    score += recency_bonus

    features = {
        "matched_via": matched,
        "days_since_release": days,
        "recency_bonus": recency_bonus,
        "wildcard": True,
    }
    return score, features


def _to_record(scene_id: str, scene: dict, score: float, features: dict, source: str) -> dict:
    studio_name = (scene.get("studio") or {}).get("name", "")
    performer_names = ", ".join(
        p["performer"]["name"] for p in (scene.get("performers") or [])
    )
    tag_names = ", ".join(t["name"] for t in (scene.get("tags") or []))
    image_url = (scene.get("images") or [{}])[0].get("url", "")
    return {
        "scene_id": scene_id,
        "title": scene.get("title") or "(untitled)",
        "studio": studio_name,
        "performers": performer_names,
        "tags": tag_names,
        "release_date": scene.get("release_date") or "",
        "image_url": image_url,
        "score": round(score, 3),
        "features": features,
        "source": source,
    }


def retrain_and_rescore() -> dict:
    """Trains (or re-trains) the Tier 2 model on every decision logged so
    far, then re-scores every still-pending recommendation against it.
    Doesn't touch StashDB - this is purely local, so it's cheap enough to
    call from a manual 'retrain now' button as well as after every refresh."""
    train_summary = ml_model.train(db.feedback_with_source())
    db.set_meta("model_status", json.dumps(train_summary))

    rescored = 0
    if train_summary.get("trained"):
        pairs = []
        pending_rows = db.all_pending_for_scoring()
        for row in pending_rows:
            features = json.loads(row["features_json"])
            prob = ml_model.predict_proba(features, row["source"])
            if prob is not None:
                pairs.append((row["scene_id"], prob))
        db.set_model_scores(pairs)
        rescored = len(pairs)

        # Novelty scores for the explore slice - computed here (not inside
        # ml_model.train()) since it needs the *current* pending pool, not
        # just the training set.
        decided = [(fj, src) for fj, _, src, _, *_ in db.feedback_with_source()]
        pending_for_novelty = [(r["scene_id"], r["features_json"], r["source"]) for r in pending_rows]
        novelty_pairs = ml_model.compute_novelty_scores(decided, pending_for_novelty)
        if novelty_pairs:
            db.set_novelty_scores(novelty_pairs)

    return {"model": train_summary, "model_rescored": rescored}


async def refresh(stash_url: str, stashdb_api_key: str) -> dict:
    profile_summary = await taste_profile.rebuild(stash_url)
    # Single-pass scan: rebuild() already collected every owned scene's
    # StashDB id while scanning the library for the taste profile, so this
    # no longer needs stashdb_check.local_stashdb_ids() to scan the whole
    # library a second time just to build the same set. Popped out before
    # profile_summary gets spread into the response below - a set isn't
    # JSON-serializable and the caller doesn't need to see it anyway.
    owned = profile_summary.pop("owned_stashdb_ids", set())
    s = cfg.get_all()

    top_performers = db.top_entities("performer", s["top_performers"])
    top_studios = db.top_entities("studio", s["top_studios"])
    top_tags = db.top_entities("tag", s["top_tags"])
    weights = db.all_weights()
    affinity = compute_tag_affinity(weights)
    performer_affinity = compute_performer_affinity(weights)

    decided = db.decided_scene_ids()

    # Auto-clear 'ready' items that are now in the owned set - this means
    # Stash successfully identified them after the scan+identify the loop-
    # closer triggered. Moves them to 'identified' so they vanish from the
    # ready panel without needing a manual dismiss.
    newly_identified = 0
    for row in db.ready_items():
        if row["scene_id"] in owned:
            db.mark_identified(row["scene_id"])
            newly_identified += 1

    candidates = await stashdb_candidates.fetch_candidates(
        stashdb_api_key, top_performers, top_studios, per_entity=s["per_entity"]
    )
    if top_tags:
        # Tier 3, part two: fetching by your own top tags (not just
        # performers/studios) is what actually lets a scene from someone
        # you've never seen enter the pool at all, on tag match alone -
        # the embedding_affinity_sum feature only re-ranks what's already
        # fetched; this is what expands what gets fetched in the first place.
        tag_hits = await stashdb_candidates.fetch_by_tags(stashdb_api_key, top_tags, s["per_entity"])
        for scene_id, scene in tag_hits.items():
            entry = candidates.setdefault(scene_id, scene)
            if entry is not scene:
                entry["matched_via"].extend(scene["matched_via"])

    added = 0
    for scene_id, scene in candidates.items():
        if scene_id in owned or scene_id in decided:
            continue
        if _is_stashdb_compilation(scene):
            continue
        score, features = _score(scene, weights, s, affinity, performer_affinity)
        if score <= 0:
            continue
        db.upsert_candidate(_to_record(scene_id, scene, score, features, "profile"))
        added += 1

    wildcard_tags = db.get_wildcard_categories("tag")
    wildcard_studios = db.get_wildcard_categories("studio")
    # db stores {"kind", "entity_id", "entity_name"}; stashdb_candidates
    # expects {"entity_id", "entity_name"} - same data, different shape.
    wildcard_tags = [{"entity_id": c["entity_id"], "entity_name": c["entity_name"]} for c in wildcard_tags]
    wildcard_studios = [{"entity_id": c["entity_id"], "entity_name": c["entity_name"]} for c in wildcard_studios]

    wildcard_candidates: dict[str, dict] = {}
    wildcard_candidates.update(
        await stashdb_candidates.fetch_by_tags(stashdb_api_key, wildcard_tags, s["wildcard_per_entity"])
    )
    wildcard_studio_hits = await stashdb_candidates.fetch_candidates(
        stashdb_api_key, top_performers=[], top_studios=wildcard_studios, per_entity=s["wildcard_per_entity"]
    )
    for scene_id, scene in wildcard_studio_hits.items():
        entry = wildcard_candidates.setdefault(scene_id, scene)
        if entry is not scene:
            entry["matched_via"].extend(scene["matched_via"])

    wildcard_added = 0
    for scene_id, scene in wildcard_candidates.items():
        if scene_id in owned or scene_id in decided:
            continue
        if _is_stashdb_compilation(scene):
            continue
        score, features = _score_wildcard(scene, s)
        db.upsert_candidate(_to_record(scene_id, scene, score, features, "wildcard"))
        wildcard_added += 1

    retrain_result = retrain_and_rescore()

    db.set_meta("last_refresh_at", datetime.now(timezone.utc).isoformat())

    return {
        **profile_summary,
        "candidates_fetched": len(candidates),
        "candidates_scored": added,
        "wildcard_fetched": len(wildcard_candidates),
        "wildcard_scored": wildcard_added,
        "feedback_examples": db.feedback_count(),
        "newly_identified": newly_identified,
        **retrain_result,
    }
