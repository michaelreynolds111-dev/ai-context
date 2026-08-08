"""Prowlarr search client + release-quality classification.

Prowlarr aggregates every indexer you've configured (public trackers, your
TorBox BYOI indexer, NZBGeek, and Bitmagnet-via-Torznab) behind one search
endpoint, so this is the only search integration the bridge needs.
"""

import re
import httpx

# (regex, label, score) -- first match wins, highest score = best.
_RESOLUTION = [
    (r"2160p|\buhd\b|\b4k\b", "2160p", 4),
    (r"1080p", "1080p", 3),
    (r"720p", "720p", 2),
    (r"480p|\bsd\b", "480p", 1),
]
_SOURCE = [
    (r"remux", "REMUX", 4),
    (r"blu.?ray|bd.?remux|bdrip", "BluRay", 3),
    (r"web.?dl", "WEB-DL", 3),
    (r"webrip", "WEBRip", 2),
    (r"hdtv", "HDTV", 1),
]


_PACK_RE = re.compile(
    r"""
    \bpack\b          |  # explicit "pack" word
    \bcollection\b    |  # "collection"
    \bmegapack\b      |  # "megapack"
    \bcompilation\b   |  # "compilation" - a 19.2GB one slipped past both
                         # this regex and the size cap in live testing
    \banthology\b     |  # same idea, different word
    \bbundle\b        |  # "bundle"
    \bsiterip\b       |  # "siterip"
    \bsite\.rip\b     |  # "site.rip"
    \bvideo[\s._-]*pack\b | # "video pack", "videopack"
    \bclip[\s._-]*pack\b  | # "clip pack"
    \b\d{2,}\s*(?:scenes?|videos?|clips?|films?|movies?)\b  # "23 scenes", "100 videos"
    """,
    re.IGNORECASE | re.VERBOSE,
)

# A single adult scene file is almost always under 8 GB.
# Anything larger is almost certainly a pack/collection, even if not named as one.
_PACK_SIZE_BYTES = 8 * 1024 ** 3  # 8 GB


def classify(title: str, size_bytes: int | None = None) -> dict:
    """Pull resolution + source tier out of a release title for ranking/badges.
    Also detects packs by title keywords AND by file size (>8 GB heuristic)."""
    t = title.lower()
    res_label, res_score = "?", 0
    for pat, label, score in _RESOLUTION:
        if re.search(pat, t):
            res_label, res_score = label, score
            break
    src_label, src_score = "?", 0
    for pat, label, score in _SOURCE:
        if re.search(pat, t):
            src_label, src_score = label, score
            break
    is_pack = bool(_PACK_RE.search(title))
    if not is_pack and size_bytes is not None:
        is_pack = size_bytes > _PACK_SIZE_BYTES
    return {
        "resolution": res_label,
        "source": src_label,
        "is_pack": is_pack,
        # weight resolution heavier than source so 2160p WEBRip beats 1080p REMUX
        "quality_score": res_score * 10 + src_score,
    }


def _human_size(num_bytes) -> str:
    try:
        num = float(num_bytes)
    except (TypeError, ValueError):
        return "?"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} PB"


async def search(
    query: str,
    *,
    prowlarr_url: str,
    api_key: str,
    categories: str | None = None,
    indexer_ids: str | None = None,
    limit: int = 100,
    timeout: float = 45.0,
) -> list[dict]:
    """Run a Prowlarr search and return normalised, ranked release dicts."""
    params = {"query": query, "type": "search", "limit": limit}
    if categories:  # e.g. "6000" for the XXX category group
        params["categories"] = categories
    if indexer_ids:
        params["indexerIds"] = indexer_ids

    url = prowlarr_url.rstrip("/") + "/api/v1/search"
    headers = {"X-Api-Key": api_key}

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        raw = resp.json()

    results = []
    for r in raw:
        title = r.get("title", "(untitled)")
        size_bytes = r.get("size")
        info = classify(title, size_bytes)
        results.append(
            {
                "title": title,
                "guid": r.get("guid"),            # needed to grab via Prowlarr
                "indexer_id": r.get("indexerId"),  # needed to grab via Prowlarr
                "indexer": r.get("indexer", "?"),
                "protocol": r.get("protocol", "torrent"),  # 'torrent' | 'usenet'
                "size_bytes": r.get("size"),
                "size_human": _human_size(r.get("size")),
                "seeders": r.get("seeders"),
                "leechers": r.get("leechers"),
                "grabs": r.get("grabs"),
                "magnet_url": r.get("magnetUrl"),
                "download_url": r.get("downloadUrl"),  # Prowlarr-proxied .torrent / .nzb
                "info_url": r.get("infoUrl"),
                "publish_date": r.get("publishDate"),
                **info,
            }
        )

    # Best quality first; within a tier, more seeders/grabs first.
    results.sort(
        key=lambda x: (
            x["quality_score"],
            (x["seeders"] or 0) + (x["grabs"] or 0),
        ),
        reverse=True,
    )
    return results


async def grab(
    guid: str,
    indexer_id: int,
    *,
    prowlarr_url: str,
    api_key: str,
    timeout: float = 60.0,
) -> dict:
    """Push a release through Prowlarr's configured download client.

    For torrents that's your rdtclient -> TorBox path. Prowlarr picks the client
    by protocol + indexer automatically. Endpoint: POST /api/v1/search.
    """
    url = prowlarr_url.rstrip("/") + "/api/v1/search"
    headers = {"X-Api-Key": api_key}
    payload = {"guid": guid, "indexerId": indexer_id}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
    ok = resp.status_code in (200, 201)
    detail = ""
    if not ok:
        try:
            detail = resp.json()
        except ValueError:
            detail = resp.text[:300]
    return {"ok": ok, "status": resp.status_code, "detail": detail}
