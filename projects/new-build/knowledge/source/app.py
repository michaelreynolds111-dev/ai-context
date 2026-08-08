"""
stash-torbox-bridge
====================
FastAPI bridge between Stash, Prowlarr, and TorBox.

Two flows:
  /add  (POST title, studio?)
        -> search Prowlarr -> best result -> send to TorBox (or Prowlarr's
           own download client, depending on protocol) -> grabbed

  StashDB overlay (Tampermonkey) flow:
        -> looks up the scene on StashDB, checks it against the local Stash
           library, returns have/missing + a clean search query
        -> if missing, the userscript shows a "Send to TorBox" button
        -> click  -->  POST /api/send  -> Prowlarr search (with fallback
           query simplification) -> best result -> grabbed exactly like
           the /add flow above

Plus the recommendations engine (db.py / taste_profile.py /
stashdb_candidates.py / recommendation_engine.py / ml_model.py) at
/recommendations and friends.

Config via environment (see .env.example).

NOTE ON THIS FILE'S HISTORY: this file was accidentally overwritten by a
botched edit and rebuilt from the intact prowlarr.py/torbox.py/
stashdb_check.py modules plus the browser scripts that call it (whose
fetch() calls pin down the exact request/response shape every route below
needs to satisfy). Everything routing-and-glue is rebuilt to those exact
contracts. The one piece that's a faithful re-implementation rather than a
byte-for-byte recovery is search_with_fallback()'s exact query-simplification
steps - test the /search and "Send to TorBox" flows carefully.
"""

import html
import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

import db
import loop_closer
import ml_model
import prowlarr
import recommendation_engine
import settings as cfg
import stashdb_candidates
import stashdb_check
import torbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bridge")


def _describe(e: Exception) -> str:
    """str(e) on several httpx exceptions (ReadTimeout, ConnectTimeout) is
    an empty string, which produced unreadable 'failed: ' error messages
    with nothing after the colon. Fall back to the exception's class name
    when that happens."""
    text = str(e)
    return text if text else type(e).__name__

PROWLARR_URL = os.environ.get("PROWLARR_URL", "http://prowlarr:9696")
PROWLARR_API_KEY = os.environ.get("PROWLARR_API_KEY", "")
TORBOX_API_KEY = os.environ.get("TORBOX_API_KEY", "")
STASHDB_API_KEY = os.environ.get("STASHDB_API_KEY", "")
STASH_URL = os.environ.get("STASH_URL", "http://host.docker.internal:9999/graphql")
CATEGORIES = os.environ.get("PROWLARR_CATEGORIES", "")
TORRENT_ADD_MODE = os.environ.get("TORRENT_ADD_MODE", "prowlarr")
USENET_ADD_MODE = os.environ.get("USENET_ADD_MODE", "torbox")


@asynccontextmanager
async def _lifespan(app):
    db.init_db()
    # Start the loop-closer background poller if TorBox is configured.
    # It runs for the lifetime of the container and never blocks requests.
    if TORBOX_API_KEY and STASH_URL:
        import asyncio
        asyncio.create_task(loop_closer.run_background_poller(TORBOX_API_KEY, STASH_URL))
    yield


app = FastAPI(title="stash-torbox-bridge", lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://stashdb.org"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Extracts the BTIH info-hash from a literal magnet: URI (40-char hex or
# 32-char base32) - used to batch-check TorBox cache status before
# attempting a grab, so a cached release can be preferred over an uncached
# one that may sit in queue or never complete.
_MAGNET_HASH_RE = re.compile(r"urn:btih:([a-fA-F0-9]{40}|[A-Za-z2-7]{32})")


def clean_title(title: str) -> str:
    """Strips StashDB's episode/season notation (e.g. "S41:E6") and
    bracketed/parenthetical noise - canonical StashDB titles containing
    this produce zero hits on most indexers, since releases aren't named
    that way in the wild."""
    t = title
    t = re.sub(r"\bS\d{1,3}[:\s]*E\d{1,3}\b", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"\([^)]*\)", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" -:")
    return t


async def search_with_fallback(
    studio: str, title: str, *, performers: str = "", date: str = "",
    prowlarr_url: str, api_key: str, categories: str | None = None,
) -> tuple[list[dict], str]:
    """Tries the full studio+title query first, then progressively simpler
    fallbacks - StashDB's canonical titles often carry notation that doesn't
    match how releases are actually named on indexers. Returns (results,
    query_that_worked) - or (empty, last_query_tried) if nothing hit."""
    cleaned = clean_title(title)
    primary_performer = ""
    if performers:
        first = performers.split(",")[0].strip()
        primary_performer = first

    candidates: list[str] = []
    def add(q: str | None) -> None:
        q = (q or "").strip()
        if q and q not in candidates:
            candidates.append(q)

    # Format date as YY.MM.DD - how most indexers name adult releases
    short_date = ""
    if date and len(date) >= 10:
        try:
            y, m, d = date[:10].split("-")
            short_date = f"{y[2:]}.{m}.{d}"
        except ValueError:
            pass

    # Priority order: most specific first (most likely to match exactly one release)
    # 1. Studio + date + performer: "Brazzers 26.06.17 Jane Doe" - the gold standard
    if studio and short_date and primary_performer:
        add(f"{studio} {short_date} {primary_performer}")
    # 2. Studio + performer + date (different order some indexers use)
    if studio and primary_performer and short_date:
        add(f"{studio} {primary_performer} {short_date}")
    # 3. Studio + cleaned title (StashDB title without noise)
    add(f"{studio} {cleaned}" if studio else cleaned)
    # 4. Studio + full title (fallback with original title)
    add(f"{studio} {title}" if studio else title)
    # 5. Studio + performer only (wide net if title isn't on indexers)
    if primary_performer:
        add(f"{studio} {primary_performer}" if studio else primary_performer)
    # 6. Title alone (last resort)
    add(cleaned if cleaned != title else None)
    add(title)

    last_error: Exception | None = None
    for query in candidates:
        # Each fallback query is tried independently - a timeout or error on
        # one phrasing must not abort the whole chain before simpler
        # fallback queries get a chance. (A previous version let the first
        # exception propagate straight out of this loop, which combined
        # with a tightened per-query timeout silently broke every search.)
        try:
            results = await prowlarr.search(
                query, prowlarr_url=prowlarr_url, api_key=api_key,
                categories=categories, timeout=30.0,
            )
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue
        if results:
            return results, query
    # Every fallback query was tried; none returned results. If at least
    # one genuinely errored (timeout, connection issue) rather than
    # cleanly returning zero results, surface that - "no results found"
    # is misleading when the real story is "Prowlarr never answered."
    if last_error is not None:
        raise last_error
    return [], (candidates[-1] if candidates else title)

async def _add_via_prowlarr(guid: str, indexer_id: str) -> dict:
    return await prowlarr.grab(
        guid, int(indexer_id), prowlarr_url=PROWLARR_URL, api_key=PROWLARR_API_KEY
    )


async def _add_via_torbox(protocol: str, magnet_url: str | None, download_url: str | None, title: str) -> dict:
    # Case 1: a literal magnet URI - the simple, common case. No network
    # call needed before handing it to TorBox.
    if magnet_url and magnet_url.startswith("magnet:"):
        log.info("torbox add via literal magnet: %s", title)
        return await torbox.add_torrent_magnet(magnet_url, api_key=TORBOX_API_KEY, name=title)

    # Case 2: magnet_url (if present) is actually an HTTP URL - Prowlarr's
    # own download-proxy, used by indexers (e.g. The Pirate Bay here) that
    # don't expose a magnet directly. Blindly handing TorBox that proxy
    # URL as if it were a magnet string is exactly what produced "Invalid
    # Magnet Link" rejections - it needs to be resolved first. It either
    # redirects to a real magnet: URI, redirects to actual file content
    # (the nzbgeek/usenet case), or returns file bytes directly.
    fetch_url = magnet_url or download_url
    if not fetch_url:
        return {"ok": False, "detail": "No usable magnet or download URL on this release."}

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=45, follow_redirects=False) as client:
            resp = await client.get(fetch_url)
    except httpx.HTTPError as e:
        return {"ok": False, "detail": f"Couldn't fetch the release file: {_describe(e)}"}

    if resp.is_redirect:
        location = resp.headers.get("location", "")
        if location.startswith("magnet:"):
            log.info("torbox add via resolved magnet (%.1fs): %s", time.monotonic() - t0, title)
            return await torbox.add_torrent_magnet(location, api_key=TORBOX_API_KEY, name=title)
        # Redirects to something else (e.g. nzbgeek) - follow it for real
        # rather than re-implementing redirect-chasing by hand.
        try:
            async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
                resp = await client.get(fetch_url)
                resp.raise_for_status()
        except httpx.HTTPError as e:
            return {"ok": False, "detail": f"Couldn't fetch the release file: {_describe(e)}"}

    file_bytes = resp.content
    log.info("fetched %d bytes for '%s' in %.1fs", len(file_bytes), title, time.monotonic() - t0)

    # Guard against a redirect/error page sneaking through as if it were a
    # real .nzb/.torrent - those are the silent failures where TorBox would
    # accept garbage. Real files are binary-ish and not tiny.
    head = file_bytes[:64].lstrip()[:15].lower()
    if head.startswith(b"<!doctype") or head.startswith(b"<html"):
        return {"ok": False, "detail": "Download URL returned an HTML page, not a release file (indexer auth or rate limit?)."}
    if len(file_bytes) < 100:
        return {"ok": False, "detail": f"Release file suspiciously small ({len(file_bytes)} bytes) - likely an error response."}

    if protocol == "usenet":
        return await torbox.add_usenet_file(file_bytes, api_key=TORBOX_API_KEY, name=title)
    return await torbox.add_torrent_file(file_bytes, api_key=TORBOX_API_KEY, name=title)


# Mainstream TV/film patterns that shouldn't match adult scene searches
# even if a keyword coincidentally lines up. Measured directly against
# the ~12% wrong-grab rate: "Elle S01E03", "Upload S03E05", "8 Out of 10
# Cats Does Countdown" - all real cases that poisoned training data.
_TV_FILM_PATTERNS = re.compile(
    r"""
    \bS\d{1,2}E\d{1,2}\b            |  # S01E03 style episode notation
    \bSeason\s*\d+\b                |  # "Season 3"
    \b(?:BluRay|BDRip|BRRip)\b      |  # movie release tags rarely used for adult
    \bAMZN\.WEB-DL\b                |  # Amazon Prime rips
    \bDDP\d\.\d\b                   |  # Dolby Digital Plus audio (mainstream)
    \bHDR10\+?\b                    |  # HDR (rare in adult, common in mainstream)
    \bHEVC\.x265\b                  |  # not exclusive to mainstream but suspicious
                                       # in combination with other tags
    \b(?:S\d+E\d+|Episode\.\d+)\b   |  # episode-style
    \b(?:EN|FR|DE|ES|IT|JP)\.SUB\b     # subtitle tags (mainstream indicator)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Junk/garbage release names - short random-looking strings, catalog IDs
# with no descriptive text. Real releases have studio/performer/title in
# the filename; junk ones look like "AOS3_720_2022" or "CiTRp1SeczAjMaGN2yNovH".
_JUNK_NAME_PATTERN = re.compile(
    r"""^
    (?:[a-z]{2,4}\d+_?)+          # short letter+digit chunks only
    (?:[._-]?\d{3,4}p?)?          # optional resolution
    (?:[._-]?\d{4})?              # optional year
    $""",
    re.IGNORECASE | re.VERBOSE,
)


def _score_relevance(result_title: str, studio: str, title: str,
                     performers: str, date: str) -> float:
    """Returns a relevance score in [0, 1] rather than a pass/fail.
    Callers apply a threshold. Score composition:
      +0.40  studio name appears in filename (STRONGEST single signal -
             "Brazzers", "Vixen", "Kink" don't show up in random files by chance)
      +0.40  primary performer's full name or surname in filename
      +0.20  release date in filename (yy.mm.dd or yymmdd form)
      +0.15  any distinctive title word (>=5 chars) present
      -1.00  mainstream TV/film pattern detected (immediate disqualification)
      -0.80  junk-name pattern (short letter-digit soup)
    Total capped at 1.0. A score < 0.4 (studio OR performer must match)
    means we shouldn't grab it. Studio and performer together = 0.8 = safe.
    """
    rt = result_title.lower()
    rt_alnum = re.sub(r"[^a-z0-9]", "", rt)  # for surname-in-filename check

    # Immediate disqualifiers
    if _TV_FILM_PATTERNS.search(result_title):
        return -1.0
    if _JUNK_NAME_PATTERN.match(result_title.strip()):
        return -0.8

    score = 0.0

    # Studio match: try full name and alphanum-collapsed version
    if studio:
        studio_norm = re.sub(r"[^a-z0-9]", "", studio.lower())
        studio_words = re.split(r"[\s._-]+", studio.lower())
        # "BrazzersExxtra" in "brazzersexxtra.26.07.05..." matches
        if studio_norm and studio_norm in rt_alnum:
            score += 0.40
        # multi-word studios: match if ALL words present
        elif len(studio_words) > 1 and all(w in rt for w in studio_words if len(w) > 2):
            score += 0.40

    # Performer match: check first (primary) performer's surname AND full name
    if performers:
        primary = performers.split(",")[0].strip()
        if primary:
            words = primary.split()
            surname = words[-1].lower() if words else ""
            firstname = words[0].lower() if words else ""
            full_norm = re.sub(r"[^a-z0-9]", "", primary.lower())
            # surname must be >=4 chars to avoid false positives ("Lee", "Ray", "Fox")
            if len(surname) >= 4 and surname in rt:
                score += 0.40
            elif full_norm and full_norm in rt_alnum:
                score += 0.40
            # weaker signal: only firstname matches (many performers share first names)
            elif len(firstname) >= 5 and firstname in rt:
                score += 0.20

    # Date match - very high-confidence signal when present
    if date and len(date) >= 10:
        try:
            y, m, d = date[:10].split("-")
            date_forms = [f"{y[2:]}.{m}.{d}", f"{y[2:]}{m}{d}",
                          f"{y}.{m}.{d}", f"{y}-{m}-{d}"]
            if any(df in rt for df in date_forms):
                score += 0.20
        except ValueError:
            pass

    # Title word match: any distinctive word (>=5 chars, not a stopword)
    if title:
        _STOP = {"scene", "video", "movie", "porn", "sex", "the", "and"}
        title_words = [w for w in re.findall(r"\w+", title.lower())
                       if len(w) >= 5 and w not in _STOP]
        if any(w in rt for w in title_words):
            score += 0.15

    return min(1.0, score)


async def _grab_best(studio: str, title: str, performers: str = "", date: str = "",
                     skip_release_names: list | None = None) -> dict:
    """Shared download path for the recommendations page, /add, and /api/send.
    Searches Prowlarr, picks the best result, and pushes it to TorBox (or
    Prowlarr's own client). Every stage is timed and logged so a slow or
    failed download tells us *which* stage was responsible, instead of a
    generic timeout. Returns {ok, detail, sent?, used_query?}."""
    if not PROWLARR_API_KEY:
        return {"ok": False, "detail": "PROWLARR_API_KEY not set in .env"}

    t0 = time.monotonic()
    try:
        results, used_query = await search_with_fallback(
            studio, title, performers=performers, date=date, prowlarr_url=PROWLARR_URL,
            api_key=PROWLARR_API_KEY, categories=CATEGORIES or None,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("prowlarr search failed for '%s': %s", title, _describe(e))
        return {"ok": False, "detail": f"Prowlarr search failed: {_describe(e)}"}
    log.info("search '%s' -> %d results via '%s' in %.1fs", title, len(results), used_query, time.monotonic() - t0)
    if not results:
        return {"ok": False, "detail": f"No results found for '{used_query}'"}

    # Prefer already-cached torrents over uncached ones, since an uncached
    # torrent can sit waiting on real seeders (or never complete) while a
    # cached one is available near-instantly. Only meaningful for the
    # direct-to-TorBox path with a literal magnet hash to check; usenet and
    # the Prowlarr->rdtclient path are left in their original order. This
    # is a stable reorder - within "cached" and "not cached" groups,
    # Prowlarr's own quality/seeder ranking is preserved.
    if TORRENT_ADD_MODE == "torbox" and TORBOX_API_KEY:
        hash_by_index: dict[int, str] = {}
        for i, r in enumerate(results):
            if r["protocol"] != "torrent":
                continue
            magnet = r.get("magnet_url") or ""
            if not magnet.startswith("magnet:"):
                continue
            m = _MAGNET_HASH_RE.search(magnet)
            if m:
                hash_by_index[i] = m.group(1).lower()
        if hash_by_index:
            try:
                cached = await torbox.check_cached(list(set(hash_by_index.values())), api_key=TORBOX_API_KEY)
            except Exception as e:  # noqa: BLE001
                cached = set()
                log.warning("checkcached failed, skipping cache-priority reorder: %s", _describe(e))
            if cached:
                # Pair each result with its original index for a stable,
                # unambiguous sort key - relying on results.index(r) would
                # be both slow (O(n) per comparison) and fragile if two
                # results ever compared equal as dicts.
                indexed = list(enumerate(results))
                indexed.sort(key=lambda pair: hash_by_index.get(pair[0]) in cached, reverse=True)
                results = [r for _, r in indexed]

    # HARD size cap - applied before anything else so no fallback path can
    # bypass it. This is the primary megapack defence: the pack-title regex
    # and relevance filter below have a "better a pack than nothing"
    # fallback, which is exactly how multi-hundred-scene packs kept getting
    # grabbed. Size doesn't lie the way titles can - anything over the cap
    # is simply never a candidate. Results with unknown size are kept
    # (usenet indexers sometimes omit it; the pack regex still covers those).
    cap_bytes = cfg.get("max_download_gb") * 1024 ** 3
    within_cap = [r for r in results if (r.get("size_bytes") or 0) <= cap_bytes]
    if not within_cap:
        sizes = ", ".join(r.get("size_human", "?") for r in results[:5])
        return {"ok": False, "detail": f"All {len(results)} results exceed the "
                f"{cfg.get('max_download_gb')}GB size cap ({sizes}). Likely only packs exist for this scene."}
    if len(within_cap) < len(results):
        log.info("_grab_best '%s': size cap removed %d/%d results (> %dGB)",
                 title, len(results) - len(within_cap), len(results), cfg.get("max_download_gb"))
    results = within_cap

    # Score each result for relevance and reject anything below the floor.
    # This replaces the old "better a pack than nothing" fallback that was
    # the direct cause of ~12% wrong grabs (measured against real data:
    # mainstream TV, junk-name releases, wrong-scene-same-studio).
    # threshold=0.4 requires studio OR performer match; nothing else is
    # sufficient. If NOTHING clears the bar we refuse - a missed download
    # is far better than a poisoned training label.
    RELEVANCE_FLOOR = 0.4
    scored_results = []
    for r in results:
        if r.get("is_pack"):
            continue  # size cap + pack regex should already handle this;
                      # keeping the check for defence in depth
        # Skip ALL releases known to have failed on TorBox (missing articles,
        # stalled, frozen) so retries exhaust every available option rather
        # than cycling back to the same broken NZB. skip_release_names is a
        # list accumulated across all previous attempts for this scene.
        if skip_release_names and r["title"].strip() in skip_release_names:
            log.info("_grab_best: skipping previously-failed release '%s'", r["title"][:60])
            continue
        rel = _score_relevance(r["title"], studio, title, performers, date)
        if rel >= RELEVANCE_FLOOR:
            scored_results.append((rel, r))

    log.info(
        "_grab_best '%s': %d total results, %d passed relevance floor (%.1f)",
        title, len(results), len(scored_results), RELEVANCE_FLOOR,
    )
    if not scored_results:
        # Give the user a concrete reason rather than silent failure.
        # Include the top-3 rejected titles + their scores so it's clear
        # WHY nothing was grabbed - "wrong studio" vs "wrong performer" etc.
        top_rejects = sorted(
            [(_score_relevance(r["title"], studio, title, performers, date), r["title"])
             for r in results[:10] if not r.get("is_pack")],
            reverse=True,
        )[:3]
        rejected_summary = "; ".join(f"'{t[:50]}' ({s:+.2f})" for s, t in top_rejects)
        return {"ok": False, "detail":
                f"No results passed the relevance floor (>={RELEVANCE_FLOOR}). "
                f"Top candidates: {rejected_summary}. Refused rather than grab a "
                f"likely-wrong file that would poison training data."}

    # Sort by quality first (highest resolution/source tier tried first -
    # quality_score already computed by prowlarr.classify() from the
    # release title: 2160p > 1080p > 720p > 480p, REMUX > BluRay > WEB-DL
    # > WEBRip > HDTV as tiebreak within a resolution). Only fall through
    # to a lower-quality result if every higher-quality option fails or
    # doesn't exist - that fallthrough already happens naturally via the
    # attempt loop below trying candidates_to_try in order. Relevance
    # score (correctness - already floor-filtered above) is the secondary
    # sort key, so within the same quality tier the best-matching release
    # is still tried first.
    scored_results.sort(
        key=lambda pair: (pair[1].get("quality_score", 0), pair[0]),
        reverse=True,
    )
    candidates_to_try = [r for _, r in scored_results]

    # Try every valid result in ranked order — no hard cap. We exhaust all
    # options before giving up. The loop terminates naturally when all
    # candidates have been tried or one succeeds.
    attempt_failures: list[str] = []
    for attempt_n, best in enumerate(candidates_to_try, start=1):
        mode = USENET_ADD_MODE if best["protocol"] == "usenet" else TORRENT_ADD_MODE
        log.info("grabbing '%s' [%s/%s] (%s, via %s) [attempt %d/%d]",
                  best["title"], best.get("resolution", "?"), best.get("source", "?"),
                  best["protocol"], mode, attempt_n, len(candidates_to_try))
        t1 = time.monotonic()
        try:
            if mode == "prowlarr":
                res = await _add_via_prowlarr(best["guid"], str(best["indexer_id"]))
            else:
                res = await _add_via_torbox(
                    best["protocol"], best.get("magnet_url"), best.get("download_url"), best["title"]
                )
        except Exception as e:  # noqa: BLE001
            res = {"ok": False, "detail": _describe(e)}
        log.info("add '%s' -> ok=%s in %.1fs", best["title"], res.get("ok"), time.monotonic() - t1)

        if res.get("ok"):
            res = dict(res)
            res["used_query"] = used_query
            res["sent"] = best["title"]
            res["sent_size"] = best.get("size_human", "?")
            res["attempts"] = attempt_n
            if not res.get("detail"):
                res["detail"] = best["title"]
            return res

        # ACTIVE_LIMIT: TorBox's active download slots are full. Don't keep
        # trying other results — they'll all hit the same wall. Signal the
        # caller to queue this download for later dispatch.
        detail = res.get("detail", "")
        raw_data = res.get("data") or {}
        if (res.get("error") == "ACTIVE_LIMIT" or
                "ACTIVE_LIMIT" in detail or
                "active download" in detail.lower() or
                "active slot" in detail.lower()):
            return {
                "ok": False,
                "active_limit": True,
                "used_query": used_query,
                "detail": "TorBox active download limit reached — queued for later",
            }

        attempt_failures.append(f"{best['title']}: {detail or 'unknown error'}")
        log.warning("attempt %d/%d failed for '%s', trying next",
                    attempt_n, len(candidates_to_try), best["title"])

    return {
        "ok": False,
        "exhausted": True,
        "used_query": used_query,
        "detail": (f"All {len(attempt_failures)} available releases tried and failed — "
                   f"no more options exist on these indexers for this scene."),
    }

PAGE_CSS = """
*{box-sizing:border-box}
body{background:#15171c;color:#e6e8ec;font:14px/1.5 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;
  margin:0;padding:24px;max-width:1100px}
h1{font-size:20px;margin:0 0 4px}
p.sub{color:#9aa0aa;margin:4px 0}
a{color:#7dd3fc}
button{cursor:pointer;border:0;border-radius:8px;padding:9px 16px;font-weight:600;
  background:#2a2f38;color:#e6e8ec;font-size:14px}
button.go{background:#16a34a;color:#fff;margin-right:8px}
button.add{background:#16a34a;color:#fff}
input[type=text]{background:#1e2128;border:1px solid #333a45;color:#e6e8ec;
  border-radius:6px;padding:8px 10px;font-size:14px}
.empty{color:#9aa0aa;padding:30px 0;text-align:center}
.result{background:#1e2128;border:1px solid #262a32;border-radius:10px;padding:12px 16px;
  margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:16px}
.result .meta{color:#9aa0aa;font-size:12px;margin-top:3px}
.result .badge{display:inline-block;background:#2a2f38;border-radius:4px;padding:2px 6px;
  font-size:11px;margin-right:4px;color:#9aa0aa}
"""

REC_CSS = """
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;margin-top:16px}
.card{background:#1e2128;border:1px solid #262a32;border-radius:10px;overflow:hidden;display:flex;flex-direction:column}
.card img{width:100%;aspect-ratio:16/9;object-fit:cover;background:#0e0f12}
.card-body{padding:10px 12px;display:flex;flex-direction:column;gap:4px}
.card-title{font-weight:600;font-size:14px;line-height:1.3}
.card-meta{color:#9aa0aa;font-size:12px}
.card-score{color:#7dd3fc;font-size:11px;font-weight:700}
.card-actions{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap}
.card-actions button{padding:7px 10px;font-size:12px;border:none;border-radius:6px;cursor:pointer;flex:1}
button.add{background:#1d4ed8;color:#fff}
button.add:hover{background:#2563eb}
button.skip{background:#3a3f4a;color:#9aa0aa}
button.skip:hover{background:#4b5563;color:#e6e8ec}
button.nope{background:#450a0a;color:#fca5a5;border:1px solid #7f1d1d}
button.nope:hover{background:#7f1d1d;color:#fff}
#status{margin:10px 0;font-size:13px;color:#9aa0aa}
.wc-badge{display:inline-block;background:#7c3aed;color:#fff;font-size:9px;font-weight:700;
  text-transform:uppercase;letter-spacing:.04em;padding:2px 6px;border-radius:4px;vertical-align:middle}
.ex-badge{display:inline-block;background:#d97706;color:#fff;font-size:9px;font-weight:700;
  text-transform:uppercase;letter-spacing:.04em;padding:2px 6px;border-radius:4px;vertical-align:middle}
.retry-badge{display:inline-block;background:#7c2d12;color:#fdba74;font-size:9px;font-weight:700;
  text-transform:uppercase;letter-spacing:.04em;padding:2px 6px;border-radius:4px;vertical-align:middle}
.retry-note{font-size:11px;color:#fdba74;background:#431407;border-radius:4px;padding:4px 8px;margin:4px 0}
.navbar{margin:6px 0 16px;font-size:13px}
.navbar a{color:#9aa0aa;text-decoration:none;margin-right:16px}
.navbar a.active{color:#e6e8ec;font-weight:600}
.filters{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:14px 0}
.filters select,.filters input[type=text]{background:#1e2128;border:1px solid #333a45;color:#e6e8ec;
  border-radius:6px;padding:6px 10px;font-size:13px}
.filters button{padding:6px 14px}
table.data{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
table.data th{text-align:left;color:#9aa0aa;font-weight:600;padding:8px 10px;border-bottom:1px solid #333a45;
  position:sticky;top:0;background:#15171c}
table.data td{padding:7px 10px;border-bottom:1px solid #21242b;vertical-align:top}
table.data tr:hover td{background:#1c1f26}
.bar-wrap{display:flex;align-items:center;gap:8px}
.bar-track{flex:1;height:8px;background:#262a32;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px}
.bar-fill.pos{background:#22c55e}
.bar-fill.neg{background:#ef4444}
.pager{margin-top:14px;font-size:13px;color:#9aa0aa}
.pager a{color:#7dd3fc;text-decoration:none;margin-right:12px}
.feature-desc{color:#9aa0aa;font-size:12px}
.ready-panel{background:#14291f;border:1px solid #166534;border-radius:10px;padding:14px 16px;margin-bottom:16px}
.ready-header-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.ready-header{color:#4ade80;font-weight:700;font-size:14px}
.ready-item{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #1a3a28}
.ready-item:last-of-type{border-bottom:none}
.ready-title{font-size:13px;color:#e6e8ec;flex:1;min-width:0}
.ready-path{font-size:11px;color:#4ade80;font-family:monospace}
.dismiss-btn{background:none;border:1px solid #374151;color:#9aa0aa;border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer}
.dismiss-btn:hover{border-color:#6b7280;color:#e6e8ec}
.settings-section{margin-top:24px}
.settings-section h2{font-size:15px;margin-bottom:10px;color:#e6e8ec}
.settings-row{display:grid;grid-template-columns:240px 110px 1fr;gap:12px;align-items:center;
  padding:8px 0;border-bottom:1px solid #21242b}
.settings-row label{font-size:13px}
.settings-row input[type=number]{background:#1e2128;border:1px solid #333a45;color:#e6e8ec;
  border-radius:6px;padding:6px 8px;font-size:13px;width:95px}
.wc-list{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.wc-chip{background:#1e2128;border:1px solid #333a45;border-radius:20px;padding:6px 12px;
  font-size:12px;display:flex;align-items:center;gap:8px}
.wc-chip button{background:none;color:#9aa0aa;padding:0;font-size:15px;line-height:1}
.wc-search-results{margin-top:10px;display:flex;flex-direction:column;gap:6px}
.wc-result{display:flex;justify-content:space-between;align-items:center;background:#1e2128;
  border:1px solid #262a32;border-radius:8px;padding:8px 12px;font-size:13px}
"""

NAV_LINKS = [
    ("/recommendations", "Recommendations"),
    ("/recommendations/candidates", "All candidates"),
    ("/recommendations/profile", "Taste profile"),
    ("/recommendations/model", "Model internals"),
    ("/settings", "Settings"),
]


def _navbar(active_path: str) -> str:
    links = " ".join(
        f'<a href="{href}"{" class=\"active\"" if href == active_path else ""}>{label}</a>'
        for href, label in NAV_LINKS
    )
    return f'<div class="navbar">{links}</div>'


def _render_card(row, explore_ids: set[str]) -> str:
    title = html.escape(row["title"] or "")
    studio = html.escape(row["studio"] or "")
    performers = html.escape(row["performers"] or "")
    release_date = html.escape(row["release_date"] or "")
    image_url = html.escape(row["image_url"] or "")
    scene_id = row["scene_id"]
    retry_count = row["retry_count"] or 0
    badges = []
    if row["source"] == "wildcard":
        badges.append('<span class="wc-badge">wildcard</span>')
    if scene_id in explore_ids:
        badges.append('<span class="ex-badge">explore</span>')
    if retry_count > 0:
        badges.append(f'<span class="retry-badge">&#9888; retry {retry_count}</span>')
    badge_html = " ".join(badges)
    retry_note = ""
    if retry_count > 0:
        failed = html.escape((row["failed_release_name"] or "")[:60])
        retry_note = (f'<div class="retry-note">Previous NZB failed on TorBox (missing articles). '
                      f'Download will skip: <em>{failed}</em></div>')
    return f"""
    <div class="card" id="card-{scene_id}">
      <img src="{image_url}" loading="lazy" alt="">
      <div class="card-body">
        <div class="card-title">{title} {badge_html}</div>
        <div class="card-meta">{studio} &middot; {release_date}</div>
        <div class="card-meta">{performers}</div>
        {retry_note}
        <div class="card-score">score {row['score']:.1f}</div>
        <div class="card-actions">
          <button class="add" onclick="decide('{scene_id}','download',this)">Download</button>
          <button class="skip" onclick="decide('{scene_id}','skip',this)" title="Not now - passes without teaching the model to avoid this">Not now</button>
          <button class="nope" onclick="decide('{scene_id}','not-interested',this)" title="Not interested - hard negative, actively teaches the model to avoid this type of content">Not interested</button>
        </div>
      </div>
    </div>"""


def _model_status_line(model_status: dict) -> str:
    if model_status.get("trained"):
        auc = model_status.get("cv_auc")
        auc_part = f", cv AUC {auc}" if auc is not None else ""
        return (f"Tier 2 model active &mdash; trained on {model_status['n_examples']} decisions "
                f"({model_status['n_positive']} downloads{auc_part}). Ranking by learned score.")
    reason = html.escape(model_status.get("reason", "not trained yet"))
    return f"Tier 2 model not active yet ({reason}). Ranking by Tier 1 heuristic score."


def render_recommendations(rows, model_status: dict, explore_ids: set[str],
                           ready_items: list, queued_items: list, health: str = "") -> str:
    cards = "".join(_render_card(r, explore_ids) for r in rows) or '<div class="empty">Nothing pending. Hit Refresh to scan for new scenes.</div>'

    ready_html = ""
    if ready_items:
        ready_rows = "".join(
            f'<div class="ready-item" id="ri-{html.escape(r["scene_id"])}">'
            f'<span class="ready-title">{html.escape(r["title"] or "")}</span>'
            f'<span class="ready-path">T:\\{html.escape(r["torbox_name"] or "")}</span>'
            f'<button class="dismiss-btn" onclick="dismissItem(\'{html.escape(r["scene_id"])}\')">&#10005; Dismiss</button>'
            f'</div>'
            for r in ready_items
        )
        ready_html = f"""
<div class="ready-panel" id="readyPanel">
  <div class="ready-header-row">
    <span class="ready-header">&#9989; {len(ready_items)} download{"s" if len(ready_items)!=1 else ""} ready on T:\\</span>
    <button class="dismiss-btn" onclick="dismissAll()">Dismiss all</button>
  </div>
  {ready_rows}
  <p class="feature-desc" style="margin-top:6px">Already visible to Stash on the T:\\ mount it scans directly -
  no copy step. A targeted scan + Identify was triggered automatically for each folder; give it a minute to finish matching.
  Next Refresh will auto-clear any that Stash successfully identified.</p>
</div>"""

    queued_html = ""
    if queued_items:
        q_rows = "".join(
            f'<div class="ready-item">'
            f'<span class="ready-title">{html.escape(r["title"] or "")}</span>'
            f'<span class="ready-path" style="color:#60a5fa">&#9202; Queued — TorBox slot full</span>'
            f'</div>'
            for r in queued_items
        )
        queued_html = f"""
<div class="ready-panel" style="border-color:#1e40af;background:#0f172a;">
  <div class="ready-header" style="color:#60a5fa">&#9202; {len(queued_items)} download{"s" if len(queued_items)!=1 else ""} queued — waiting for TorBox slot</div>
  {q_rows}
  <p class="feature-desc" style="margin-top:6px">TorBox's 10 active download limit was reached.
  These will be dispatched automatically every 5 minutes as slots free up — no action needed.</p>
</div>"""

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recommendations</title><style>{PAGE_CSS}{REC_CSS}</style></head><body>
<h1>Recommendations</h1>
{_navbar("/recommendations")}
{ready_html}
{queued_html}
<p class="sub">Scored against your Stash library, sourced from StashDB. {len(rows)} pending. {health}</p>
<p class="sub">{_model_status_line(model_status)}</p>
<p class="sub">{len(explore_ids)} marked <span class="ex-badge">explore</span> &mdash;
  low-confidence picks mixed in deliberately so deciding on them actually teaches the model
  something, rather than just confirming what it already thinks. Don't expect them all to be winners.</p>
<button id="refreshBtn" class="go" onclick="doRefresh()">Refresh</button>
<button id="trainBtn" class="go" onclick="doTrain()">Retrain model</button>
<button class="go" onclick="doPoll(this)">Check downloads</button>
<div id="status"></div>
<div class="grid">{cards}</div>
<script>
async function decide(sceneId, action, btn) {{
  btn.disabled = true;
  const card = document.getElementById('card-' + sceneId);
  card.style.opacity = '0.5';
  try {{
    const resp = await fetch('/api/recommendations/' + action, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: 'scene_id=' + encodeURIComponent(sceneId),
    }});
    const data = await resp.json();
    if (data.ok) {{
      card.remove();
      if (action === 'download' && data.sent) {{
        const st = document.getElementById('status');
        st.textContent = 'Sent: ' + data.sent + ' (' + (data.sent_size || '?') + ')';
      }}
    }}
    else {{ card.style.opacity = '1'; btn.disabled = false; alert('Failed: ' + data.detail); }}
  }} catch (e) {{ card.style.opacity = '1'; btn.disabled = false; alert('Request failed: ' + e); }}
}}
async function doRefresh() {{
  const btn = document.getElementById('refreshBtn');
  btn.disabled = true;
  btn.textContent = 'Refreshing (this can take a minute)...';
  try {{
    const resp = await fetch('/api/recommendations/refresh', {{method: 'POST'}});
    const data = await resp.json();
    if (data.ok) {{ location.reload(); }}
    else {{ alert('Refresh failed: ' + data.detail); btn.disabled = false; btn.textContent = 'Refresh'; }}
  }} catch (e) {{ alert('Refresh failed: ' + e); btn.disabled = false; btn.textContent = 'Refresh'; }}
}}
async function doTrain() {{
  const btn = document.getElementById('trainBtn');
  btn.disabled = true;
  btn.textContent = 'Retraining...';
  try {{
    const resp = await fetch('/api/recommendations/train', {{method: 'POST'}});
    const data = await resp.json();
    if (data.ok) {{ location.reload(); }}
    else {{ alert('Retrain failed: ' + data.detail); btn.disabled = false; btn.textContent = 'Retrain model'; }}
  }} catch (e) {{ alert('Retrain failed: ' + e); btn.disabled = false; btn.textContent = 'Retrain model'; }}
}}
async function doPoll(btn) {{
  btn.disabled = true;
  btn.textContent = 'Checking...';
  try {{
    const resp = await fetch('/api/recommendations/poll', {{method: 'POST'}});
    const data = await resp.json();
    if (data.ok && data.newly_ready > 0) {{ location.reload(); }}
    else {{ btn.textContent = 'Check downloads'; btn.disabled = false; }}
  }} catch (e) {{ btn.textContent = 'Check downloads'; btn.disabled = false; }}
}}
async function dismissItem(sceneId) {{
  await fetch('/api/recommendations/dismiss/' + sceneId, {{method: 'POST'}});
  const el = document.getElementById('ri-' + sceneId);
  if (el) el.remove();
  const remaining = document.querySelectorAll('.ready-item').length;
  if (remaining === 0) document.getElementById('readyPanel').remove();
}}
async function dismissAll() {{
  await fetch('/api/recommendations/dismiss-all', {{method: 'POST'}});
  const panel = document.getElementById('readyPanel');
  if (panel) panel.remove();
}}
</script>
</body></html>"""


def _health_line() -> str:
    """One-line freshness indicator: when the last refresh ran, styled as a
    warning if it's overdue (nightly task runs at 4:30am, so anything past
    ~30h means the schedule silently failed - expired key, Stash down, etc)."""
    raw = db.get_meta("last_refresh_at")
    if not raw:
        return '<span style="color:#9aa0aa">No refresh recorded yet.</span>'
    try:
        then = datetime.fromisoformat(raw)
    except ValueError:
        return ""
    hours = (datetime.now(timezone.utc) - then).total_seconds() / 3600
    when = f"{hours:.0f}h ago" if hours >= 1 else f"{hours*60:.0f}m ago"
    if hours > 30:
        return f'<span style="color:#f87171">&#9888; Last refresh: {when} - nightly refresh may be failing</span>'
    return f'<span style="color:#9aa0aa">Last refresh: {when}</span>'


@app.get("/recommendations", response_class=HTMLResponse)
async def recommendations_page():
    rows, explore_ids = db.pending_recommendations_mixed(
        60,
        wildcard_fraction=cfg.get("wildcard_fraction"),
        explore_fraction=cfg.get("explore_fraction"),
    )
    raw_status = db.get_meta("model_status")
    model_status = json.loads(raw_status) if raw_status else {"trained": False, "reason": "not trained yet"}
    ready = db.ready_items()
    queued = db.queued_items()
    return HTMLResponse(render_recommendations(rows, model_status, explore_ids, ready, queued, _health_line()))


@app.post("/api/recommendations/refresh")
async def api_recommendations_refresh():
    if not STASHDB_API_KEY:
        return {"ok": False, "detail": "STASHDB_API_KEY not set in .env"}
    try:
        summary = await recommendation_engine.refresh(STASH_URL, STASHDB_API_KEY)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"Refresh failed: {e}"}
    return {"ok": True, **summary}


@app.post("/api/recommendations/train")
async def api_recommendations_train():
    result = recommendation_engine.retrain_and_rescore()
    return {"ok": True, **result}


@app.post("/api/recommendations/poll")
async def api_recommendations_poll():
    """Manually trigger one loop-closer poll cycle - useful for checking
    if something's ready without waiting the 5-minute background interval."""
    if not TORBOX_API_KEY:
        return {"ok": False, "detail": "TORBOX_API_KEY not set"}
    try:
        n = await loop_closer.poll_once(TORBOX_API_KEY, STASH_URL)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": str(e)}
    return {"ok": True, "newly_ready": n}


@app.post("/api/recommendations/dismiss/{scene_id}")
async def api_recommendations_dismiss(scene_id: str):
    db.dismiss_ready(scene_id)
    return {"ok": True}


@app.post("/api/recommendations/dismiss-all")
async def api_recommendations_dismiss_all():
    n = db.dismiss_all_ready()
    return {"ok": True, "dismissed": n}


@app.post("/api/recommendations/watch-check")
async def api_recommendations_watch_check():
    """Manually trigger the watch-feedback pass - queries Stash for all
    downloaded scenes >24h old and revises training labels with outcomes."""
    if not STASH_URL:
        return {"ok": False, "detail": "STASH_URL not configured"}
    try:
        n = await loop_closer.run_watch_feedback_pass(STASH_URL)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": str(e)}
    return {"ok": True, "scenes_checked": n}


@app.post("/api/recommendations/skip")
async def api_recommendations_skip(scene_id: str = Form(...)):
    """'Not now' - low-confidence negative (0.3). The model treats this as
    weak signal: you're passing, not actively rejecting. These scenes won't
    reappear but they won't count heavily against their performers/studios
    in training either. Use this for 'wrong mood', 'already have something
    queued', 'seen it', etc."""
    row = db.decide(scene_id, "skipped")
    if row is None:
        return {"ok": False, "detail": "This card is stale (already cleared or decided). Refresh the page."}
    return {"ok": True}


@app.post("/api/recommendations/not-interested")
async def api_recommendations_not_interested(scene_id: str = Form(...)):
    """'Not interested' - hard negative (1.5 confidence, 5x the weight of
    a passive skip). Use this when you actively don't want this type of
    content - wrong performer, wrong act, wrong studio, actively dislike it.
    This is the signal that actually teaches the model what to avoid."""
    row = db.decide(scene_id, "not_interested")
    if row is None:
        return {"ok": False, "detail": "This card is stale (already cleared or decided). Refresh the page."}
    return {"ok": True}


@app.post("/api/recommendations/download")
async def api_recommendations_download(scene_id: str = Form(...)):
    row = db.get_recommendation(scene_id)
    if row is not None:
        studio, title = row["studio"], row["title"]
        performers, date = row["performers"] or "", row["release_date"] or ""
    else:
        # The candidate row is gone - usually a stale browser page after a
        # refresh cleared/replaced the pending set. The scene still exists
        # on StashDB, so look it up there directly rather than failing with
        # a confusing "Unknown scene_id". This makes the Download button
        # robust to the page being out of date.
        if not STASHDB_API_KEY:
            return {"ok": False, "detail": "Unknown scene_id (not in pending list, and STASHDB_API_KEY not set to look it up)"}
        try:
            scene = await stashdb_check.get_scene(scene_id, STASHDB_API_KEY)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "detail": f"scene_id not in pending list and StashDB lookup failed: {_describe(e)}"}
        if scene is None:
            return {"ok": False, "detail": "Unknown scene_id - not in pending list and not found on StashDB. Try refreshing the page."}
        studio = (scene.get("studio") or {}).get("name", "")
        title = scene.get("title") or ""
        performers = ", ".join(p["performer"]["name"] for p in (scene.get("performers") or []))
        date = scene.get("release_date") or ""

    # Pass ALL previously-failed release names so _grab_best skips every
    # release that's already been tried and failed on TorBox, not just the
    # last one. This lets retries exhaust every available option in order.
    import json as _json
    if row is not None:
        failed_names = _json.loads(row["failed_release_names"] or "[]")
    else:
        failed_names = []
    res = await _grab_best(studio, title, performers, date, skip_release_names=failed_names)
    if res["ok"]:
        db.decide(scene_id, "sent")
        data = res.get("data") or {}
        tb_id = data.get("torrent_id") or data.get("usenetdownload_id")
        tb_type = "usenet" if data.get("usenetdownload_id") else "torrent"
        tb_name = data.get("name") or ""
        if tb_id:
            db.mark_torbox_sent(scene_id, tb_type, int(tb_id), tb_name)
    elif res.get("active_limit"):
        # TorBox is full — queue this download for automatic dispatch
        # when a slot frees up. The recommendation stays visible on the
        # page with a "queued" status indicator.
        db.mark_queued(scene_id, studio, title, performers, date, failed_names)
    elif res.get("exhausted"):
        # Every available Prowlarr result has been tried. Mark permanently
        # so the card stops cycling and the user knows it's genuinely unavailable.
        with db._conn() as c:
            c.execute("UPDATE recommendations SET status='download_failed' WHERE scene_id=?",
                      (scene_id,))
    return res


def render_taste_profile(rows, counts: dict, entity_type: str, q: str, muted: list[dict]) -> str:
    type_options = "".join(
        f'<option value="{t}"{" selected" if t == entity_type else ""}>{t} ({counts.get(t, 0)})</option>'
        for t in ("performer", "studio", "tag")
    )
    body_rows = "".join(
        f"<tr><td>{html.escape(r['entity_name'])}</td><td>{r['entity_type']}</td>"
        f"<td>{r['weight']:.2f}</td><td>"
        f'<button type="button" class="skip" data-kind="{html.escape(r["entity_type"])}" '
        f'data-id="{html.escape(r["entity_id"])}" data-name="{html.escape(r["entity_name"])}" '
        f'onclick="muteEntity(this)">Mute</button>'
        f"</td></tr>"
        for r in rows
    ) or '<tr><td colspan="4">No matches.</td></tr>'

    muted_chips = "".join(
        f'<span class="wc-chip">{html.escape(m["kind"])}: {html.escape(m["entity_name"])} '
        f'<button type="button" data-kind="{html.escape(m["kind"])}" data-id="{html.escape(m["entity_id"])}" '
        f'onclick="unmuteEntity(this)">&times;</button></span>'
        for m in muted
    ) or '<span class="feature-desc" id="noneMutedMsg">Nothing muted.</span>'

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Taste profile</title><style>{PAGE_CSS}{REC_CSS}</style></head><body>
<h1>Taste profile</h1>
{_navbar("/recommendations/profile")}
<p class="sub">Every performer/studio/tag the engine has weighted from your Stash library -
  this is the raw data your recommendations are scored against. Weight comes from how often it
  appears (volume-dampened), plus a flat bonus if you've favorited it.</p>

<div class="settings-section">
<h2>Muted</h2>
<p class="sub">Zeroed out entirely - excluded from the taste profile, never queried as a top
  performer/studio/tag, contributes nothing to scoring. For when something's just wrong for you
  regardless of volume, rather than over-weighted because of it.</p>
<div class="wc-list" id="mutedList">{muted_chips}</div>
</div>

<form method="get" class="filters">
  <select name="type">{type_options}</select>
  <input type="text" name="q" placeholder="search name..." value="{html.escape(q)}">
  <button type="submit" class="go">Filter</button>
</form>
<table class="data"><thead><tr><th>Name</th><th>Type</th><th>Weight</th><th></th></tr></thead>
<tbody>{body_rows}</tbody></table>
<p class="sub feature-desc">Mute takes effect immediately for future scoring, but the weight
  shown above won't disappear from /recommendations/candidates until the next Refresh.</p>
<script>
async function muteEntity(btn) {{
  const kind = btn.dataset.kind, id = btn.dataset.id, name = btn.dataset.name;
  btn.disabled = true;
  btn.textContent = 'Muting...';
  try {{
    await fetch('/api/profile/mute', {{
      method: 'POST', headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: 'kind=' + encodeURIComponent(kind) + '&entity_id=' + encodeURIComponent(id) + '&entity_name=' + encodeURIComponent(name),
    }});
  }} catch (e) {{ btn.disabled = false; btn.textContent = 'Mute'; alert('Mute failed: ' + e); return; }}
  const row = btn.closest('tr');
  if (row) row.remove();
  addMutedChip(kind, id, name);
}}

function addMutedChip(kind, id, name) {{
  const placeholder = document.getElementById('noneMutedMsg');
  if (placeholder) placeholder.remove();
  const chip = document.createElement('span');
  chip.className = 'wc-chip';
  chip.append(kind + ': ' + name + ' ');
  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.textContent = '\\u00d7';
  removeBtn.dataset.kind = kind;
  removeBtn.dataset.id = id;
  removeBtn.onclick = () => unmuteEntity(removeBtn);
  chip.appendChild(removeBtn);
  document.getElementById('mutedList').appendChild(chip);
}}

async function unmuteEntity(btn) {{
  const kind = btn.dataset.kind, id = btn.dataset.id;
  btn.disabled = true;
  try {{
    await fetch('/api/profile/unmute', {{
      method: 'POST', headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: 'kind=' + encodeURIComponent(kind) + '&entity_id=' + encodeURIComponent(id),
    }});
  }} catch (e) {{ btn.disabled = false; alert('Unmute failed: ' + e); return; }}
  const chip = btn.closest('.wc-chip');
  if (chip) chip.remove();
  const list = document.getElementById('mutedList');
  if (list && !list.querySelector('.wc-chip')) {{
    list.innerHTML = '<span class="feature-desc" id="noneMutedMsg">Nothing muted.</span>';
  }}
}}
</script>
</body></html>"""


@app.get("/recommendations/profile", response_class=HTMLResponse)
async def taste_profile_page(type: str = "performer", q: str = ""):
    rows = db.search_taste_profile(type if type in ("performer", "studio", "tag") else None, q or None, 200)
    muted_keys = db.muted_keys()
    rows = [r for r in rows if (r["entity_type"], r["entity_id"]) not in muted_keys]
    counts = db.taste_profile_counts()
    muted = db.get_muted_entities()
    return HTMLResponse(render_taste_profile(rows, counts, type, q, muted))


@app.post("/api/profile/mute")
async def api_profile_mute(kind: str = Form(...), entity_id: str = Form(...), entity_name: str = Form(...)):
    muted = db.mute_entity(kind, entity_id, entity_name)
    return {"ok": True, "muted": muted}


@app.post("/api/profile/unmute")
async def api_profile_unmute(kind: str = Form(...), entity_id: str = Form(...)):
    muted = db.unmute_entity(kind, entity_id)
    return {"ok": True, "muted": muted}


def render_results(results: list[dict], used_query: str, studio: str, title: str) -> str:
    rows = []
    for r in results:
        badges = "".join(
            f'<span class="badge">{html.escape(b)}</span>'
            for b in (r.get("resolution"), r.get("source")) if b and b != "?"
        )
        if r.get("is_pack"):
            badges += '<span class="badge">PACK</span>'
        size = r.get("size_human", "?")
        seeders = r.get("seeders")
        seed_info = f" &middot; {seeders} seeders" if seeders is not None else ""
        payload = html.escape(json.dumps(r))
        rows.append(f"""
        <div class="result">
          <div>
            <div>{html.escape(r.get('title', ''))}</div>
            <div class="meta">{badges}{html.escape(r.get('indexer', '?'))} &middot; {size}{seed_info}</div>
          </div>
          <button class="add" data-release='{payload}' onclick="addRelease(this)">Add</button>
        </div>""")
    body = "".join(rows) or '<div class="empty">No results.</div>'
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Search results</title><style>{PAGE_CSS}</style></head><body>
<h1>{html.escape(title)}</h1>
<p class="sub">{html.escape(studio)} &middot; searched for &quot;{html.escape(used_query)}&quot; &middot; {len(results)} results</p>
<div id="results">{body}</div>
<script>
async function addRelease(btn) {{
  const r = JSON.parse(btn.dataset.release);
  btn.disabled = true;
  btn.textContent = 'Adding...';
  const body = new URLSearchParams({{
    guid: r.guid || '', indexer_id: r.indexer_id || '', protocol: r.protocol || '',
    magnet_url: r.magnet_url || '', download_url: r.download_url || '', title: r.title || '',
  }});
  try {{
    const resp = await fetch('/add', {{method: 'POST', body: body}});
    const data = await resp.json();
    btn.textContent = data.ok ? 'Added' : 'Failed';
    if (!data.ok) alert('Add failed: ' + (data.detail || ''));
  }} catch (e) {{ btn.textContent = 'Error'; alert('Request failed: ' + e); }}
}}
</script>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(f"""<!doctype html><html><head><meta charset="utf-8">
<title>stash-torbox-bridge</title><style>{PAGE_CSS}</style></head><body>
<h1>stash-torbox-bridge</h1>
<p class="sub">Manual search, or use the Find Sources button in Stash / Send to TorBox on StashDB.</p>
<form method="get" action="/search">
  <input type="text" name="studio" placeholder="studio (optional)">
  <input type="text" name="title" placeholder="title" required>
  <button type="submit" class="go">Search</button>
</form>
<p class="sub"><a href="/recommendations">Recommendations &rarr;</a></p>
</body></html>""")


@app.get("/search", response_class=HTMLResponse)
async def search_route(studio: str = "", title: str = "", performers: str = "", date: str = ""):
    if not title:
        return HTMLResponse(f'<html><body style="background:#15171c;color:#e6e8ec;padding:20px">Missing title.</body></html>')
    try:
        results, used_query = await search_with_fallback(
            studio, title, performers=performers, date=date,
            prowlarr_url=PROWLARR_URL, api_key=PROWLARR_API_KEY, categories=CATEGORIES or None,
        )
    except Exception as e:  # noqa: BLE001
        return HTMLResponse(f'<html><body style="background:#15171c;color:#e6e8ec;padding:20px">Search failed: {html.escape(str(e))}</body></html>')
    return HTMLResponse(render_results(results, used_query, studio, title))


@app.post("/add")
async def add_route(
    guid: str = Form(""), indexer_id: str = Form(""), protocol: str = Form("torrent"),
    magnet_url: str = Form(""), download_url: str = Form(""), title: str = Form(""),
):
    mode = USENET_ADD_MODE if protocol == "usenet" else TORRENT_ADD_MODE
    try:
        if mode == "prowlarr":
            if not guid or not indexer_id:
                return {"ok": False, "detail": "Missing guid/indexer_id for Prowlarr grab."}
            res = await _add_via_prowlarr(guid, indexer_id)
        else:
            res = await _add_via_torbox(protocol, magnet_url or None, download_url or None, title)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"Add failed: {e}"}
    return res


@app.get("/api/check")
async def api_check(scene_id: str):
    if not STASHDB_API_KEY:
        return {"error": "STASHDB_API_KEY not set in .env"}
    try:
        scene = await stashdb_check.get_scene(scene_id, STASHDB_API_KEY)
    except Exception as e:  # noqa: BLE001
        return {"error": f"StashDB lookup failed: {e}"}
    if scene is None:
        return {"error": "Scene not found on StashDB"}
    title = scene.get("title") or "(untitled)"
    studio = (scene.get("studio") or {}).get("name", "")
    try:
        owned = await stashdb_check.local_stashdb_ids(STASH_URL)
    except Exception as e:  # noqa: BLE001
        return {"error": f"Stash lookup failed: {e}"}
    have = scene_id in owned
    query = f"{studio} {clean_title(title)}".strip()
    return {"have": have, "title": title, "query": query}


@app.post("/api/send")
async def api_send(scene_id: str = Form(...)):
    if not STASHDB_API_KEY:
        return {"ok": False, "detail": "STASHDB_API_KEY not set in .env"}
    try:
        scene = await stashdb_check.get_scene(scene_id, STASHDB_API_KEY)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"StashDB lookup failed: {e}"}
    if scene is None:
        return {"ok": False, "detail": "Scene not found on StashDB"}
    title = scene.get("title") or "(untitled)"
    studio = (scene.get("studio") or {}).get("name", "")
    performers = ", ".join(p["performer"]["name"] for p in (scene.get("performers") or []))
    date = scene.get("release_date") or ""
    return await _grab_best(studio, title, performers, date)


def render_candidates(rows, total: int, status: str, source: str, q: str, sort: str, page: int, per_page: int) -> str:
    def opts(options, current):
        return "".join(
            f'<option value="{v}"{" selected" if v == current else ""}>{label}</option>'
            for v, label in options
        )

    status_opts = opts([("pending", "pending"), ("sent", "sent"), ("skipped", "skipped"), ("all", "all")], status)
    source_opts = opts([("all", "all"), ("profile", "profile"), ("wildcard", "wildcard")], source)
    sort_opts = opts([("score", "Tier 1 score"), ("model_score", "Model score"),
                      ("release_date", "Release date"), ("created_at", "Date found")], sort)

    body_rows = []
    for r in rows:
        ms = f"{r['model_score']:.3f}" if r["model_score"] is not None else "&mdash;"
        body_rows.append(
            f"<tr><td>{html.escape(r['title'] or '')}</td>"
            f"<td>{html.escape(r['studio'] or '')}</td>"
            f"<td>{html.escape(r['performers'] or '')}</td>"
            f"<td>{html.escape(r['tags'] or '')}</td>"
            f"<td>{r['score']:.1f}</td><td>{ms}</td>"
            f"<td>{r['status']}</td><td>{r['source']}</td>"
            f"<td>{html.escape(r['release_date'] or '')}</td></tr>"
        )
    body_html = "".join(body_rows) or '<tr><td colspan="9">No matches.</td></tr>'


    has_prev = page > 1
    has_next = (page * per_page) < total
    qs_base = f"status={status}&source={source}&q={html.escape(q)}&sort={sort}"
    pager = (
        f'<div class="pager">Showing {min((page-1)*per_page+1, total)}-{min(page*per_page, total)} of {total}. '
        + (f'<a href="/recommendations/candidates?{qs_base}&page={page-1}">&larr; Prev</a>' if has_prev else "")
        + (f'<a href="/recommendations/candidates?{qs_base}&page={page+1}">Next &rarr;</a>' if has_next else "")
        + "</div>"
    )

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All candidates</title><style>{PAGE_CSS}{REC_CSS}</style></head><body>
<h1>All candidates</h1>
{_navbar("/recommendations/candidates")}
<p class="sub">Every scene the engine has ever scored - not just the curated top of the
  /recommendations page. {total} total matching this filter.</p>
<form method="get" class="filters">
  <select name="status">{status_opts}</select>
  <select name="source">{source_opts}</select>
  <select name="sort">{sort_opts}</select>
  <input type="text" name="q" placeholder="search title/studio/performer/tag..." value="{html.escape(q)}">
  <button type="submit" class="go">Filter</button>
</form>
<table class="data"><thead><tr>
  <th>Title</th><th>Studio</th><th>Performers</th><th>Tags</th>
  <th>Tier 1 score</th><th>Model score</th><th>Status</th><th>Source</th><th>Release date</th>
</tr></thead>
<tbody>{body_html}</tbody></table>
{pager}
</body></html>"""


@app.get("/recommendations/candidates", response_class=HTMLResponse)
async def candidates_page(
    status: str = "pending", source: str = "all", q: str = "", sort: str = "score", page: int = 1,
):
    per_page = 50
    rows, total = db.search_recommendations(status, source, q or None, sort, per_page, (page - 1) * per_page)
    return HTMLResponse(render_candidates(rows, total, status, source, q, sort, page, per_page))


def _feature_rows(importances: list[dict] | None) -> str:
    if not importances:
        return "".join(
            f"<tr><td>{name}</td><td class='feature-desc'>{html.escape(ml_model.FEATURE_DESCRIPTIONS.get(name, ''))}</td>"
            f"<td>&mdash;</td></tr>"
            for name in ml_model.FEATURE_NAMES
        )
    max_abs = max((abs(f["coefficient"]) for f in importances), default=1) or 1
    rows = []
    for f in importances:
        coef = f["coefficient"]
        pct = round(abs(coef) / max_abs * 100)
        cls = "pos" if coef >= 0 else "neg"
        desc = html.escape(ml_model.FEATURE_DESCRIPTIONS.get(f["feature"], ""))
        rows.append(f"""
        <tr><td>{f['feature']}</td><td class="feature-desc">{desc}</td>
        <td><div class="bar-wrap"><span>{coef:+.3f}</span>
        <div class="bar-track"><div class="bar-fill {cls}" style="width:{pct}%"></div></div></div></td></tr>""")
    return "".join(rows)


def render_model_page(model_status: dict) -> str:
    importances = model_status.get("feature_importances")
    feature_table = _feature_rows(importances)

    if model_status.get("trained"):
        stats = f"""
        <table class="data">
        <tr><td>Decisions trained on</td><td>{model_status['n_examples']}</td></tr>
        <tr><td>Downloads (positive)</td><td>{model_status['n_positive']}</td></tr>
        <tr><td>Skips (negative)</td><td>{model_status['n_negative']}</td></tr>
        <tr><td>Cross-validated AUC</td><td>{model_status.get('cv_auc', '&mdash;')}
          <span class="feature-desc">(0.5 = random guessing, 1.0 = perfect separation)</span></td></tr>
        <tr><td>Last trained</td><td>{html.escape(model_status.get('trained_at', '?'))}</td></tr>
        </table>"""
    else:
        stats = f"<p class='sub'>Not trained yet: {html.escape(model_status.get('reason', 'unknown'))}</p>"

    raw_json = html.escape(json.dumps(model_status, indent=2))

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Model internals</title><style>{PAGE_CSS}{REC_CSS}</style></head><body>
<h1>How the recommendation model works</h1>
{_navbar("/recommendations/model")}

<p class="sub"><b>Algorithm:</b> Logistic Regression (scikit-learn). It's a simple, fully
interpretable statistical model - it learns exactly one number (a coefficient) per feature.
A positive coefficient pushes the prediction toward "you'd download this"; negative pushes
toward "you'd skip it." There's no hidden layer, no black box - every number below is the
whole model.</p>

<p class="sub"><b>Pipeline:</b> for each candidate scene, {len(ml_model.FEATURE_NAMES)} numbers are computed (the table
below) &rarr; each is standardized to mean 0 / standard deviation 1, so they're on comparable
scales &rarr; the logistic regression combines them into a single probability between 0 and 1
&rarr; that probability re-ranks everything pending on the /recommendations page. Coefficients
below are shown in that standardized space deliberately - it's what makes a "+2.1" on one
feature directly comparable in size to a "+2.1" on another, even though the raw features are
in completely different units (a weight sum vs. a day count vs. a 0/1 flag).</p>

<p class="sub"><b>Training:</b> every Download/Skip you make on the /recommendations page
becomes one labeled example (1 = downloaded, 0 = skipped). It retrains automatically after
every nightly refresh, or on demand from the Retrain button on the main page. Below is the
state from the last time it actually trained.</p>

<h2 style="font-size:16px;margin-top:24px">Training data</h2>
{stats}

<h2 style="font-size:16px;margin-top:24px">Features and learned coefficients</h2>
<table class="data"><thead><tr><th>Feature</th><th>What it means</th><th>Coefficient</th></tr></thead>
<tbody>{feature_table}</tbody></table>

<details style="margin-top:20px"><summary style="cursor:pointer;color:#9aa0aa">Raw model status JSON</summary>
<pre style="background:#1e2128;border:1px solid #262a32;border-radius:8px;padding:12px;overflow:auto;font-size:12px">{raw_json}</pre>
</details>
</body></html>"""


@app.get("/recommendations/model", response_class=HTMLResponse)
async def model_page():
    raw_status = db.get_meta("model_status")
    model_status = json.loads(raw_status) if raw_status else {"trained": False, "reason": "not trained yet"}
    return HTMLResponse(render_model_page(model_status))


def render_settings(values: dict, wildcard_categories: list, saved: bool) -> str:
    sections: dict[str, list[str]] = {}
    for key, spec in cfg.SETTINGS_SCHEMA.items():
        step = "1" if spec["type"] == "int" else "any"
        row = f"""
        <div class="settings-row">
          <label for="{key}">{html.escape(spec['label'])}</label>
          <input type="number" id="{key}" name="{key}" value="{values[key]}"
                 min="{spec['min']}" max="{spec['max']}" step="{step}">
          <span class="feature-desc">{html.escape(spec['help'])}</span>
        </div>"""
        sections.setdefault(spec["section"], []).append(row)

    sections_html = "".join(
        f'<div class="settings-section"><h2>{html.escape(name)}</h2>{"".join(rows)}</div>'
        for name, rows in sections.items()
    )

    wc_chips = "".join(
        f'<span class="wc-chip">{html.escape(c["kind"])}: {html.escape(c["entity_name"])} '
        f'<button type="button" data-kind="{html.escape(c["kind"])}" data-id="{html.escape(c["entity_id"])}" '
        f'onclick="removeWildcard(this.dataset.kind,this.dataset.id)">&times;</button></span>'
        for c in wildcard_categories
    ) or '<span class="feature-desc">None configured.</span>'

    saved_banner = '<p class="sub" style="color:#22c55e">Saved.</p>' if saved else ""
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Settings</title><style>{PAGE_CSS}{REC_CSS}</style></head><body>
<h1>Settings</h1>
{_navbar("/settings")}
<p class="sub">Every tunable knob in the engine, live. Changes apply on the next Refresh/Retrain -
  nothing here needs a code change or a rebuild.</p>
{saved_banner}
<form method="post" action="/api/settings">
{sections_html}
<div style="margin-top:20px;display:flex;gap:10px">
  <button type="submit" class="go">Save settings</button>
  <button type="submit" formaction="/api/settings/reset" class="skip">Reset to defaults</button>
</div>
</form>

<div class="settings-section">
<h2>Wildcard categories</h2>
<p class="sub">Tags/studios that bypass your taste profile entirely and always get guaranteed page
  space (the wildcard fraction above). Search StashDB by name and pick the right match - no
  manual UUID lookups needed.</p>
<div class="wc-list" id="wcList">{wc_chips}</div>
<div class="filters">
  <select id="wcKind"><option value="tag">tag</option><option value="studio">studio</option></select>
  <input type="text" id="wcQuery" placeholder="search name...">
  <button type="button" class="go" onclick="searchWildcard()">Search</button>
</div>
<div class="wc-search-results" id="wcResults"></div>
</div>

<script>
async function searchWildcard() {{
  const kind = document.getElementById('wcKind').value;
  const name = document.getElementById('wcQuery').value;
  const box = document.getElementById('wcResults');
  box.innerHTML = '<div class="feature-desc">Searching...</div>';
  try {{
    const resp = await fetch('/api/settings/wildcard/search', {{
      method: 'POST', headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: 'kind=' + encodeURIComponent(kind) + '&name=' + encodeURIComponent(name),
    }});
    const data = await resp.json();
    if (!data.ok) {{ box.innerHTML = '<div class="feature-desc">' + data.detail + '</div>'; return; }}
    if (data.results.length === 0) {{ box.innerHTML = '<div class="feature-desc">No matches.</div>'; return; }}
    box.innerHTML = '';
    data.results.forEach(r => {{
      const row = document.createElement('div');
      row.className = 'wc-result';
      const label = document.createElement('span');
      label.textContent = r.name + (r.parent ? ' (network: ' + r.parent + ')' : '');
      const btn = document.createElement('button');
      btn.className = 'add';
      btn.textContent = 'Add';
      btn.onclick = () => addWildcard(kind, r.id, r.name);
      row.appendChild(label);
      row.appendChild(btn);
      box.appendChild(row);
    }});
  }} catch (e) {{ box.innerHTML = '<div class="feature-desc">Search failed: ' + e + '</div>'; }}
}}
async function addWildcard(kind, id, name) {{
  await fetch('/api/settings/wildcard/add', {{
    method: 'POST', headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
    body: 'kind=' + encodeURIComponent(kind) + '&entity_id=' + encodeURIComponent(id) + '&entity_name=' + encodeURIComponent(name),
  }});
  location.reload();
}}
async function removeWildcard(kind, id) {{
  await fetch('/api/settings/wildcard/remove', {{
    method: 'POST', headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
    body: 'kind=' + encodeURIComponent(kind) + '&entity_id=' + encodeURIComponent(id),
  }});
  location.reload();
}}
</script>
</body></html>"""


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(saved: int = 0):
    values = cfg.get_all()
    wildcard_categories = db.get_wildcard_categories()
    return HTMLResponse(render_settings(values, wildcard_categories, saved=bool(saved)))


@app.post("/api/settings")
async def save_settings(request: Request):
    form = await request.form()
    cfg.set_values(dict(form))
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.post("/api/settings/reset")
async def reset_settings_route():
    cfg.reset_defaults()
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.post("/api/settings/wildcard/search")
async def settings_wildcard_search(kind: str = Form(...), name: str = Form(...)):
    if not STASHDB_API_KEY:
        return {"ok": False, "detail": "STASHDB_API_KEY not set in .env"}
    if kind not in ("tag", "studio"):
        return {"ok": False, "detail": "kind must be 'tag' or 'studio'"}
    try:
        results = await stashdb_candidates.search_tag_or_studio(STASHDB_API_KEY, kind, name)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"Search failed: {e}"}
    return {"ok": True, "results": results}


@app.post("/api/settings/wildcard/add")
async def settings_wildcard_add(kind: str = Form(...), entity_id: str = Form(...), entity_name: str = Form(...)):
    categories = db.add_wildcard_category(kind, entity_id, entity_name)
    return {"ok": True, "categories": categories}


@app.post("/api/settings/wildcard/remove")
async def settings_wildcard_remove(kind: str = Form(...), entity_id: str = Form(...)):
    categories = db.remove_wildcard_category(kind, entity_id)
    return {"ok": True, "categories": categories}
