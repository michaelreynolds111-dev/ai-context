"""
stashdb_candidates.py
======================
Pulls candidate scenes from StashDB for your top-weighted performers and
studios (from taste_profile.py), sorted newest-first. This is the
"discovery" half of the pipeline - stashdb_check.py only ever looked up
one scene at a time for the browser overlay; this fetches batches.
"""

import asyncio

import httpx

STASHDB_URL = "https://stashdb.org/graphql"

# Bounds how many StashDB queries run at once. A refresh fires 85+ queries
# (top performers + studios + tags + wildcards) one per entity; running
# them one-at-a-time was why a refresh took ~2 minutes. Bounded rather than
# unbounded concurrency so this doesn't look like a burst attack against
# StashDB's API - 6 is generous headroom without being aggressive.
_CONCURRENCY = 6

_SCENE_FIELDS = """
fragment SceneFields on Scene {
  id title release_date
  studio { id name }
  tags { id name }
  performers { performer { id name } }
  images { url }
}
"""

_BY_PERFORMER_QUERY = _SCENE_FIELDS + """
query ($performerId: ID!, $perPage: Int!) {
  queryScenes(input: {
    performers: { value: [$performerId], modifier: INCLUDES }
    sort: DATE, direction: DESC, page: 1, per_page: $perPage
  }) { scenes { ...SceneFields } }
}"""

_BY_STUDIO_QUERY = _SCENE_FIELDS + """
query ($studioId: ID!, $perPage: Int!) {
  queryScenes(input: {
    parentStudio: $studioId
    sort: DATE, direction: DESC, page: 1, per_page: $perPage
  }) { scenes { ...SceneFields } }
}"""

_BY_TAG_QUERY = _SCENE_FIELDS + """
query ($tagId: ID!, $perPage: Int!) {
  queryScenes(input: {
    tags: { value: [$tagId], modifier: INCLUDES }
    sort: DATE, direction: DESC, page: 1, per_page: $perPage
  }) { scenes { ...SceneFields } }
}"""


async def _run(client: httpx.AsyncClient, query: str, variables: dict, api_key: str) -> list[dict]:
    resp = await client.post(
        STASHDB_URL,
        json={"query": query, "variables": variables},
        headers={"ApiKey": api_key, "Content-Type": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))
    return data["data"]["queryScenes"]["scenes"]


async def _fetch_one(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, query: str, variables: dict,
    api_key: str, entity_type: str, entity_id: str, entity_name: str,
) -> list[tuple[dict, str, str, str]]:
    """One entity's worth of a fetch_candidates/fetch_by_tags query, bounded
    by the semaphore. Returns (scene, entity_type, entity_id, entity_name)
    tuples rather than mutating a shared dict directly - the actual merge
    into the candidates dict happens back on the caller after every task
    has completed, so there's no concurrent-mutation risk to reason about
    even though many of these run in parallel."""
    async with semaphore:
        try:
            scenes = await _run(client, query, variables, api_key)
        except Exception:  # noqa: BLE001 - one bad entity shouldn't kill the batch
            return []
    return [(s, entity_type, entity_id, entity_name) for s in scenes]


def _merge(candidates: dict[str, dict], batches: list[list[tuple[dict, str, str, str]]]) -> None:
    for batch in batches:
        for scene, entity_type, entity_id, entity_name in batch:
            entry = candidates.setdefault(scene["id"], {**scene, "matched_via": []})
            entry["matched_via"].append((entity_type, entity_id, entity_name))


async def fetch_candidates(
    api_key: str,
    top_performers: list,
    top_studios: list,
    per_entity: int = 25,
) -> dict[str, dict]:
    """Returns {scene_id: scene_dict} merged across every top performer and
    studio query, deduplicated. Each scene_dict also carries a
    'matched_via' list of (entity_type, entity_id, entity_name) so the
    scorer and the feature snapshot know *why* it was suggested. Queries
    run concurrently (bounded by _CONCURRENCY) rather than one at a time -
    a refresh fires 40+ of these, and sequential awaiting was most of why
    a refresh took ~2 minutes."""
    candidates: dict[str, dict] = {}
    semaphore = asyncio.Semaphore(_CONCURRENCY)

    async with httpx.AsyncClient(timeout=20) as client:
        tasks = [
            _fetch_one(
                client, semaphore, _BY_PERFORMER_QUERY,
                {"performerId": perf["entity_id"], "perPage": per_entity}, api_key,
                "performer", perf["entity_id"], perf["entity_name"],
            )
            for perf in top_performers
        ] + [
            _fetch_one(
                client, semaphore, _BY_STUDIO_QUERY,
                {"studioId": studio["entity_id"], "perPage": per_entity}, api_key,
                "studio", studio["entity_id"], studio["entity_name"],
            )
            for studio in top_studios
        ]
        batches = await asyncio.gather(*tasks)

    _merge(candidates, batches)
    return candidates


async def fetch_by_tags(api_key: str, tags: list, per_entity: int = 40) -> dict[str, dict]:
    """Same shape as fetch_candidates, but queries scenes directly by tag id
    rather than by your top performers/studios - this is what lets explicit
    wildcard categories surface even if they're a minority of your library
    and would never make it into your top-N taste profile naturally. Also
    concurrent, same as fetch_candidates."""
    candidates: dict[str, dict] = {}
    semaphore = asyncio.Semaphore(_CONCURRENCY)

    async with httpx.AsyncClient(timeout=20) as client:
        tasks = [
            _fetch_one(
                client, semaphore, _BY_TAG_QUERY,
                {"tagId": tag["entity_id"], "perPage": per_entity}, api_key,
                "tag", tag["entity_id"], tag["entity_name"],
            )
            for tag in tags
        ]
        batches = await asyncio.gather(*tasks)

    _merge(candidates, batches)
    return candidates


async def _graphql(query: str, variables: dict, api_key: str) -> dict:
    """Generic StashDB GraphQL call - unlike _run() above, this doesn't
    assume a queryScenes shape, so it works for arbitrary lookups."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            STASHDB_URL,
            json={"query": query, "variables": variables},
            headers={"ApiKey": api_key, "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errors"):
            raise RuntimeError(str(data["errors"]))
        return data["data"]


async def search_tag_or_studio(api_key: str, kind: str, name: str) -> list[dict]:
    """Looks up candidate matches for a wildcard category by name - this is
    what powers the "search and add" UI on the Settings page, so adding a
    new wildcard category never requires looking up a StashDB UUID by hand."""
    if kind == "tag":
        data = await _graphql(
            "query ($name: String!) { findTagOrAlias(name: $name) { id name } }",
            {"name": name}, api_key,
        )
        match = data.get("findTagOrAlias")
        return [{"id": match["id"], "name": match["name"]}] if match else []

    data = await _graphql(
        "query ($term: String!) { searchStudio(term: $term, limit: 8) { id name parent { id name } } }",
        {"term": name}, api_key,
    )
    return [{"id": r["id"], "name": r["name"], "parent": (r.get("parent") or {}).get("name")}
            for r in (data.get("searchStudio") or [])]
