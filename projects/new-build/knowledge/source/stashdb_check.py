"""
stashdb_check.py
=================
Minimal StashDB + local-Stash lookups for the "Send to TorBox" overlay
button (see stash-plugin/stashdb-overlay.js). No browsing UI here on
purpose - StashDB's own website already does that well. This module only
answers two questions:
  1. What is this StashDB scene actually called? (title/studio/performers)
  2. Do I already have it in my local Stash library?
"""

import time

import httpx

STASHDB_URL = "https://stashdb.org/graphql"

# {stash_url: (fetched_at_monotonic, ids)} - module-level so it survives
# across requests within this process. 60s balances staleness (a newly
# Identified scene won't show as "have" for up to a minute) against
# actually preventing the "every overlay hover re-scans the whole
# library" problem this cache exists to fix.
_OWNED_IDS_CACHE: dict[str, tuple[float, set[str]]] = {}
_OWNED_IDS_TTL_SECONDS = 60


async def get_scene(scene_id: str, api_key: str) -> dict | None:
    query = """
    query ($id: ID!) {
      findScene(id: $id) {
        id title release_date
        studio { name }
        performers { performer { name } }
      }
    }"""
    headers = {"ApiKey": api_key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            STASHDB_URL, json={"query": query, "variables": {"id": scene_id}}, headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errors"):
            raise RuntimeError(str(data["errors"]))
        return data["data"]["findScene"]


async def local_stashdb_ids(stash_url: str) -> set[str]:
    """All StashDB scene IDs already linked in the local Stash library
    (i.e. scenes that have been Identified/Tagged against StashDB).
    Paginates through the whole library - genuinely cached for 60s now
    (keyed by stash_url), so rapid repeated calls like every StashDB
    overlay hover share one scan instead of each re-paginating the whole
    library from scratch. The full refresh path doesn't use this at all
    any more (taste_profile.rebuild() collects the same set in its own
    single library pass) - this function exists for the overlay's
    have/missing check, which has no other reason to scan the library.
    """
    cached = _OWNED_IDS_CACHE.get(stash_url)
    if cached is not None:
        fetched_at, ids = cached
        if time.monotonic() - fetched_at < _OWNED_IDS_TTL_SECONDS:
            return ids

    query = """
    query ($page: Int!) {
      findScenes(filter: {page: $page, per_page: 100}) {
        count
        scenes { stash_ids { endpoint stash_id } }
      }
    }"""
    ids: set[str] = set()
    page = 1
    async with httpx.AsyncClient(timeout=20) as client:
        while True:
            resp = await client.post(
                stash_url, json={"query": query, "variables": {"page": page}}
            )
            resp.raise_for_status()
            data = resp.json()["data"]["findScenes"]
            for scene in data["scenes"]:
                for sid in scene["stash_ids"]:
                    if "stashdb.org" in sid["endpoint"]:
                        ids.add(sid["stash_id"])
            if page * 100 >= data["count"]:
                break
            page += 1

    _OWNED_IDS_CACHE[stash_url] = (time.monotonic(), ids)
    return ids


async def get_stash_watch_signals(stash_id: str, stash_url: str) -> dict | None:
    """Looks up a scene in the LOCAL Stash library by its StashDB UUID
    (stored in stash_ids) and returns watch-signal fields. This is the
    watch-feedback arc: after a download completes and Stash has had time
    to scan and identify it, we read back play_count/play_duration/
    o_counter/rating100 to revise the provisional 'clicked download' label
    with an actual outcome label.

    Returns None if the scene isn't in Stash yet (not scanned/identified)
    or if Stash is unreachable."""
    query = """
    query ($stash_id: String!) {
      findScenes(
        scene_filter: {
          stash_id_endpoint: {
            stash_id: $stash_id
            endpoint: "https://stashdb.org"
          }
        }
        filter: { per_page: 1 }
      ) {
        scenes {
          id title
          play_count play_duration
          o_counter rating100
          last_played_at
        }
      }
    }"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                stash_url,
                json={"query": query, "variables": {"stash_id": stash_id}},
            )
            resp.raise_for_status()
            scenes = resp.json()["data"]["findScenes"]["scenes"]
            return scenes[0] if scenes else None
    except Exception:  # noqa: BLE001
        return None
