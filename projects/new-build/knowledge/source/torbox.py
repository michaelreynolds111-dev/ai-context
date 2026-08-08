"""TorBox API client -- the only thing the bridge does that mutates state.

Endpoints (base https://api.torbox.app, version v1):
  POST /v1/api/torrents/createtorrent          (magnet OR .torrent file)
  POST /v1/api/usenet/createusenetdownload     (.nzb file OR link)

Auth: Authorization: Bearer <API_KEY>
Note: createtorrent / createusenetdownload are rate-limited to 60/hour per key.
"""

import httpx

API_BASE = "https://api.torbox.app/v1/api"


def _headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}


async def add_torrent_magnet(magnet: str, *, api_key: str, name: str | None = None) -> dict:
    data = {"magnet": magnet, "seed": "1", "allow_zip": "false"}
    if name:
        data["name"] = name
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{API_BASE}/torrents/createtorrent",
            data=data,
            headers=_headers(api_key),
        )
    return _parse(resp)


async def add_torrent_file(
    torrent_bytes: bytes, *, api_key: str, name: str | None = None
) -> dict:
    files = {"file": ("release.torrent", torrent_bytes, "application/x-bittorrent")}
    data = {"seed": "1", "allow_zip": "false"}
    if name:
        data["name"] = name
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{API_BASE}/torrents/createtorrent",
            data=data,
            files=files,
            headers=_headers(api_key),
        )
    return _parse(resp)


async def add_usenet_file(
    nzb_bytes: bytes, *, api_key: str, name: str | None = None
) -> dict:
    files = {"file": ("release.nzb", nzb_bytes, "application/x-nzb")}
    data = {}
    if name:
        data["name"] = name
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{API_BASE}/usenet/createusenetdownload",
            data=data,
            files=files,
            headers=_headers(api_key),
        )
    return _parse(resp)


async def check_cached(hashes: list[str], *, api_key: str) -> set[str]:
    """Batch-checks which of the given torrent info-hashes TorBox already
    has cached, without creating anything. Verified live against the real
    API before this was written: GET .../torrents/checkcached?hash=h1,h2&
    format=list returns {data: [...]} with one entry per cached hash -
    hashes TorBox doesn't have are simply absent from the list, not an
    error. Returns the set of cached hashes (lowercased) for cheap
    membership testing by the caller."""
    if not hashes:
        return set()
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{API_BASE}/torrents/checkcached",
            params={"hash": ",".join(hashes), "format": "list"},
            headers=_headers(api_key),
        )
    if resp.status_code != 200:
        return set()  # fail open - caller just won't get a cache-priority reorder
    try:
        body = resp.json()
    except ValueError:
        return set()
    if not body.get("success"):
        return set()
    return {entry["hash"].lower() for entry in (body.get("data") or []) if entry.get("hash")}


def _parse(resp: httpx.Response) -> dict:
    """TorBox always returns {success, detail, data}; surface detail to the user."""
    try:
        body = resp.json()
    except ValueError:
        body = {"success": False, "detail": resp.text[:300]}
    return {
        "ok": bool(body.get("success")) and resp.status_code == 200,
        "status": resp.status_code,
        "detail": body.get("detail", ""),
        "data": body.get("data"),
    }

async def check_torrent_ready(torrent_id: int, *, api_key: str) -> dict | None:
    """Returns the torrent's current state dict from TorBox, or None on any
    error. Caller checks download_state == 'cached' / download_present for
    readiness. bypass_cache=true forces a live status check."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{API_BASE}/torrents/mylist",
            params={"id": torrent_id, "bypass_cache": "true"},
            headers=_headers(api_key),
        )
    try:
        body = resp.json()
    except ValueError:
        return None
    if not body.get("success") or not body.get("data"):
        return None
    data = body["data"]
    # mylist?id= returns a dict directly (not a list) for a single item
    return data if isinstance(data, dict) else None


async def check_usenet_ready(usenet_id: int, *, api_key: str) -> dict | None:
    """Same as check_torrent_ready but for usenet downloads."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{API_BASE}/usenet/mylist",
            params={"id": usenet_id, "bypass_cache": "true"},
            headers=_headers(api_key),
        )
    try:
        body = resp.json()
    except ValueError:
        return None
    if not body.get("success") or not body.get("data"):
        return None
    data = body["data"]
    return data if isinstance(data, dict) else None


async def delete_usenet(usenet_id: int, *, api_key: str) -> bool:
    """Deletes a usenet download from TorBox permanently, freeing the slot.
    The control endpoint uses usenet_id (not id) per the TorBox API spec.
    Returns True on success, False on any error (fail-open)."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{API_BASE}/usenet/controlusenetdownload",
            json={"usenet_id": usenet_id, "operation": "delete"},
            headers=_headers(api_key),
        )
    try:
        body = resp.json()
        return bool(body.get("success")) and resp.status_code == 200
    except ValueError:
        return False


async def delete_torrent(torrent_id: int, *, api_key: str) -> bool:
    """Deletes a torrent from TorBox permanently, freeing the slot."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            f"{API_BASE}/torrents/controltorrent",
            json={"torrent_id": torrent_id, "operation": "delete"},
            headers=_headers(api_key),
        )
    try:
        body = resp.json()
        return bool(body.get("success")) and resp.status_code == 200
    except ValueError:
        return False
