"""
taste_profile.py
=================
Scans your local Stash library and turns it into weighted scores per
performer/studio/tag - the signal the recommendation engine ranks new
StashDB candidates against.

Per scene, an "interest score" is computed from signals Stash already
tracks (rating, play count, o-counter), then added to every performer/
studio/tag attached to that scene. Once every scene's been scanned, each
entity's accumulated total is compressed by a tunable exponent (see
settings.py: volume_dampening_exponent) so raw appearance count doesn't
dominate - a studio you own 80 scenes of shouldn't automatically outrank
one you've favorited but only own 3 of. Favoriting in Stash is then added
as a flat bonus per entity, applied once regardless of appearance count.
"""

import httpx
from itertools import combinations

import db
import settings as cfg

_SCENES_QUERY = """
query ($page: Int!) {
  findScenes(filter: {page: $page, per_page: 100}) {
    count
    scenes {
      rating100
      play_count
      o_counter
      stash_ids { endpoint stash_id }
      studio { id name favorite rating100 stash_ids { endpoint stash_id } }
      tags { id name favorite stash_ids { endpoint stash_id } }
      performers {
        id name favorite rating100 o_counter
        stash_ids { endpoint stash_id }
      }
    }
  }
}"""


async def _fetch_all_scenes(stash_url: str) -> list[dict]:
    scenes: list[dict] = []
    page = 1
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            resp = await client.post(stash_url, json={"query": _SCENES_QUERY, "variables": {"page": page}})
            resp.raise_for_status()
            data = resp.json()
            if data.get("errors"):
                raise RuntimeError(str(data["errors"]))
            block = data["data"]["findScenes"]
            scenes.extend(block["scenes"])
            if page * 100 >= block["count"]:
                break
            page += 1
    return scenes


def _interest_score(scene: dict, s: dict) -> float:
    score = 1.0  # base: it's in your library at all
    if scene.get("rating100"):
        score += (scene["rating100"] / 100) * s["rating_weight"]
    score += min(scene.get("play_count") or 0, s["play_cap"]) * s["play_weight"]
    score += min(scene.get("o_counter") or 0, s["o_cap"]) * s["o_weight"]
    return score


def _entity_multiplier(entity: dict, s: dict) -> float:
    """Entity-level preference multiplier - the missing signal.

    Previously the same base per-scene interest was added to every
    performer/studio/tag regardless of how you actually feel about that
    entity - a performer you rated 100 was treated like a random background
    performer with the same scene count. This is the biggest structural
    weakness in the taste profile: Stash exposes performer.rating100,
    performer.o_counter, studio.rating100 and none of them were reaching
    the model.

    Returns a multiplier applied to the scene's interest before it's added
    to the entity's total. 1.0 = no explicit signal (baseline); above 1.0
    = you've indicated you like this entity in Stash. Kept multiplicative
    (not additive) so a rated performer's presence in a scene proportionally
    amplifies the scene's whole interest contribution rather than adding
    a constant, which correctly scales with how much you already engaged
    with the scene itself."""
    mult = 1.0
    rating = entity.get("rating100")
    if rating:
        # 100 -> +1.5x, 80 -> +1.2x, 60 -> +0.9x, etc. Explicit rating is
        # your most deliberate signal so it earns the largest lift.
        mult += (rating / 100) * s["entity_rating_weight"]
    if entity.get("o_counter", 0) > 0:
        # Performer-level o_counter exists on Stash performers - a genuine
        # engagement signal separate from scene-level o-counter.
        mult += s["entity_ocounter_weight"]
    return mult


def _stashdb_id(entity: dict) -> str | None:
    """Stash's own id for a performer/studio/tag is a local row id - useless
    for querying StashDB. This pulls the actual StashDB UUID from the same
    stash_ids cross-reference scenes use, or None if this entity was never
    matched/tagged against StashDB (can't be used for discovery either way)."""
    for sid in entity.get("stash_ids") or []:
        if "stashdb.org" in sid["endpoint"]:
            return sid["stash_id"]
    return None


async def rebuild(stash_url: str) -> dict:
    """Rescans the whole library and replaces the taste profile. Returns a
    small summary dict so the caller (and the /refresh endpoint) can report
    what happened - including the full set of owned StashDB scene IDs,
    collected in this same pass (the scene query already fetches each
    scene's own stash_ids alongside its performers/studio/tags). The
    library used to be scanned twice per refresh - once here, once again
    by stashdb_check.local_stashdb_ids() purely to build that owned set -
    so refresh() now uses this instead of calling that separately."""
    scenes = await _fetch_all_scenes(stash_url)
    s = cfg.get_all()
    raw: dict[tuple[str, str], list] = {}  # (type, id) -> [name, raw_interest_sum]
    favorited: set[tuple[str, str]] = set()
    cooc: dict[tuple[str, str], int] = {}  # (tag_a, tag_b), tag_a < tag_b -> co-occurrence count
    performer_cooc: dict[tuple[str, str], int] = {}  # same idea, for performers
    owned_stashdb_ids: set[str] = set()  # scene-level - which StashDB scenes you already have

    def bump(entity_type: str, entity_id: str, name: str, amount: float) -> None:
        key = (entity_type, entity_id)
        if key not in raw:
            raw[key] = [name, 0.0]
        raw[key][1] += amount

    for scene in scenes:
        interest = _interest_score(scene, s)
        scene_stashdb_id = _stashdb_id(scene)
        if scene_stashdb_id:
            owned_stashdb_ids.add(scene_stashdb_id)
        studio = scene.get("studio")
        if studio:
            sid = _stashdb_id(studio)
            if sid:
                bump("studio", sid, studio["name"], interest * _entity_multiplier(studio, s))
                if studio.get("favorite"):
                    favorited.add(("studio", sid))
        scene_tag_ids: list[str] = []
        for tag in scene.get("tags") or []:
            sid = _stashdb_id(tag)
            if sid:
                # Tags don't have rating100/o_counter in Stash - only
                # favorite. Multiplier is always 1.0 here, but pass through
                # _entity_multiplier for consistency + future-proofing.
                bump("tag", sid, tag["name"], interest * _entity_multiplier(tag, s))
                if tag.get("favorite"):
                    favorited.add(("tag", sid))
                scene_tag_ids.append(sid)
        scene_performer_ids: list[str] = []
        for performer in scene.get("performers") or []:
            sid = _stashdb_id(performer)
            if sid:
                # This is where the biggest change lands: a performer you
                # rated 100 contributes ~2.5x what an unrated one does per
                # scene appearance (1.0 base + 1.5 rating lift with default
                # entity_rating_weight=1.5).
                bump("performer", sid, performer["name"], interest * _entity_multiplier(performer, s))
                if performer.get("favorite"):
                    favorited.add(("performer", sid))
                scene_performer_ids.append(sid)

        # Tier 3 signal: which tags/performers keep company with which, in
        # your library. This is what lets a future candidate score well via
        # tags/performers it doesn't even have, by sharing context with
        # ones it does have.
        for a, b in combinations(sorted(set(scene_tag_ids)), 2):
            cooc[(a, b)] = cooc.get((a, b), 0) + 1
        for a, b in combinations(sorted(set(scene_performer_ids)), 2):
            performer_cooc[(a, b)] = performer_cooc.get((a, b), 0) + 1

    # Volume dampening happens here, once per entity, after all appearances
    # are summed - not per scene. A studio with 80 scenes and one with 3
    # both get compressed by the same curve, rather than the raw sum
    # scaling linearly (and therefore unfairly) with how much you own.
    # Favoriting is a flat bonus per entity regardless of appearance count,
    # added after dampening so it isn't itself diluted by volume either.
    exponent = s["volume_dampening_exponent"]
    muted = db.muted_keys()
    weights: dict[tuple[str, str], list] = {}
    for key, (name, raw_sum) in raw.items():
        if key in muted:
            continue  # muted entirely - excluded from the profile, not just down-weighted
        weight = raw_sum ** exponent
        if key in favorited:
            weight += s["favorite_bonus"]
        weights[key] = [name, weight]

    db.replace_tag_cooccurrence(cooc)
    db.replace_performer_cooccurrence(performer_cooc)
    rows = [(t, i, name, weight) for (t, i), (name, weight) in weights.items()]
    db.replace_taste_profile(rows)
    return {
        "scenes_scanned": len(scenes),
        "performers": sum(1 for t, _ in weights if t == "performer"),
        "studios": sum(1 for t, _ in weights if t == "studio"),
        "tags": sum(1 for t, _ in weights if t == "tag"),
        "owned_stashdb_ids": owned_stashdb_ids,
    }
