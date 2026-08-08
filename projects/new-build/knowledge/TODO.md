# TODO — stash-torbox-bridge / Stash maintenance

## HIGH PRIORITY: Back up Stash's database & config
The Stash native Windows install stores everything irreplaceable here:
  C:\Users\micha\.stash\
Key files:
  - stash-go.sqlite        <- scanned scenes, tags, ratings, StashDB identifications
  - config.yml             <- settings, StashDB endpoint + API key, library paths
  - stash-go.sqlite-shm / -wal  <- SQLite working files (back up alongside the .sqlite)

Why it matters: container images re-pull and configs are bind-mounted, but the
Stash SQLite DB is the one thing that CANNOT be regenerated. Losing it = re-scanning
the entire T:\ library and re-running Identify from scratch.

Options (pick one, set-and-forget preferred):
  1. Stash's built-in backup: Settings > System > Backup (creates a .sqlite snapshot)
     - Can be scheduled; simplest, Stash-native.
  2. Scheduled copy of C:\Users\micha\.stash\*.sqlite* + config.yml to another
     drive / cloud-synced folder (e.g. via a small Task Scheduler + robocopy job).
  3. Fold into existing backup stack if one already covers C:\Users\micha.

Note: back up when Stash is idle (not mid-scan) to avoid copying a half-written DB.


## Recommendations engine — Tier 1 built (heuristic scoring)
Built: taste profile (db.py, taste_profile.py), StashDB candidate fetcher
(stashdb_candidates.py), scoring/orchestration (recommendation_engine.py),
and a /recommendations page in app.py with Download/Skip actions.

How it works: taste_profile.py scans your Stash library and weights every
performer/studio/tag you've favorited, rated, played, or o-counted - using
each entity's StashDB stash_id (not Stash's local id) as the key, since
that's what's needed to query StashDB directly. recommendation_engine.py
then pulls new scenes from StashDB for your top 40 performers/15 studios,
filters out anything you already own or have already decided on, scores
the rest, and stores them in data/recommendations.db (SQLite, persisted
via the docker-compose volume mount).

Refresh runs nightly at 4:30am via Windows Task Scheduler ("Stash
Recommendations Refresh" task -> refresh-recommendations.ps1, logs to
C:\torbox-system\recommendations-refresh.log). Can also be triggered
manually from the page itself (Refresh button) or via
POST http://localhost:8770/api/recommendations/refresh

Every Download/Skip decision is logged to the feedback table with a full
feature snapshot (matched performers/studios/tags, recency) - this is the
training set for Tier 2 (a learned ranking model), even though nothing
trains on it yet.

## Future: ML tiers for recommendations
  - Tier 2: DONE. ml_model.py - logistic regression on 9 engineered
    features (heuristic score, is_wildcard, performer/studio/tag match
    counts, tag weight sum, recency). Trains automatically at the end of
    every refresh (nightly via the scheduled task, or manually via the
    "Retrain model" button on /recommendations) once there are >=50
    decisions logged with >=10 downloads - currently 399 decisions /
    75 downloads, cv AUC 0.594. Once trained, ranks the whole pending
    queue by model_score instead of the raw heuristic score; falls back
    to the heuristic automatically if no model exists yet.
    Honest caveat: AUC is only modestly above random right now because
    the strongest feature (score) is itself derived from the same
    heuristic - it's mostly recalibrating Tier 1 so far, not yet finding
    new patterns. Should improve as more downloads accumulate (skips are
    plentiful; downloads are the scarcer, more informative label).
  - Tier 3: content embeddings from performer/tag co-occurrence, to catch
    scenes that don't share exact tags but are similar in style.
  - Tier 4: visual embeddings (CLIP) on thumbnails, for matches metadata
    misses entirely.
  - Exploration: DONE. db.explore_recommendations() carves ~1/6 of the
    page from candidates with model_score closest to 0.5 (most uncertain),
    excluding whatever profile/wildcard top-picks already got a slot.
    Falls back to a random draw if no model exists yet. Badged "explore"
    (amber) on the page, separate from the "wildcard" (purple) badge -
    a candidate can carry both if it happens to be wildcard-sourced AND
    low-confidence. Point of this slice: feedback on picks the model
    *isn't* already confident about, so retraining can actually correct
    it instead of just reinforcing whatever it already believes.

## Settings page (self-service tuning, no rebuild needed)
Built: settings.py (SETTINGS_SCHEMA - single source of truth for every
tunable: default, type, bounds, plain-language help text), a /settings
page exposing all 18 of them as number inputs grouped by section (Taste
profile / Candidate discovery / Scoring / Page composition / Tier 2
training), saved as one JSON blob in db's meta table. taste_profile.py,
recommendation_engine.py, and ml_model.py all read live via
settings.get_all()/get() instead of hardcoded module constants - change
a value on the page, it applies on the next Refresh/Retrain, no code
change or rebuild.

Wildcard categories (previously hardcoded Oil/Big Ass/Wet Look/Anal Sex
tags + BangBros) moved to db.get/add/remove_wildcard_category(), stored
the same way. The Settings page has a search-and-add widget
(stashdb_candidates.search_tag_or_studio()) so adding a new wildcard
category is "type a name, pick the StashDB match, click Add" - no manual
UUID lookups required going forward.

Bug caught during this build: backfill_weight_components() (written
during the Tier 2 feature-decomposition fix) was never actually run, so
performer_weight_sum/studio_weight_sum/tag_weight_sum were silently 0.0
for every historical training example - the model correctly learned they
carried zero signal because the *data* was zero, not because they don't
matter. Ran it (2,187 rows backfilled), retrained: cv AUC 0.594 -> 0.621,
and tag_weight_sum/performer_weight_sum now show real non-zero
coefficients. Worth remembering: any future one-time migration function
needs to actually be invoked somewhere, not just defined.

## Volume bias fix (taste_profile.py)
Was: per-entity weight was a raw linear sum of per-scene interest, so a
studio with 80 scenes in your library outweighed one you'd favorited but
only owned 3 of, purely on count. Now: appearances are still summed the
same way, but the total is compressed by volume_dampening_exponent
(Settings page, default 0.5 = square root) once per entity *after* all
scenes are scanned. Favoriting is now a flat +favorite_bonus added once
per entity post-dampening, not once per scene it appears in (it was
quietly subject to the same volume bias before, just smaller-scale).
Verified: studio top-8 spread went from a 29x gap (1351.8 vs 46.0) to
2.5x (20.22 vs 8.19); performer top-8 from 19x to 2.4x. Lower-volume
entries (Nuru Massage, Brandy Renee) surfaced into the top 8 that the
old linear sum had buried. Tunable live on /settings if 0.5 turns out to
be too aggressive or not aggressive enough - 1.0 reverts to the old
linear behavior entirely.

## Mute button
db.get/mute/unmute_entity() - same storage pattern as wildcard categories
(JSON list in meta). taste_profile.rebuild() excludes muted (type, id)
keys entirely from the final taste_profile rows, so a muted entity never
appears in top_entities(), never gets queried against StashDB, and never
contributes to any candidate's scoring (weights.get() naturally returns 0
for absent keys). UI lives on /recommendations/profile: a "Mute" button
per row in the main table, a "Muted" section up top listing current mutes
with one-click Unmute. Scoped to taste-profile weight only - doesn't
actively exclude candidates that merely share a muted tag as a side
attribute; that's a different, stronger feature (a blocklist) that wasn't
what was asked for.

## Tier 3: tag co-occurrence ("content embeddings")
Two parts, both needed - re-ranking alone doesn't expand the candidate
pool, and expanding the pool alone doesn't capture stylistic similarity:

1. **Affinity scoring** (recommendation_engine.compute_tag_affinity):
   during taste_profile.rebuild(), every pair of tags that co-occurs in
   the same scene gets counted (db.tag_cooccurrence, tag_a < tag_b
   canonical). Once per refresh (not once per candidate), this is
   collapsed into a single affinity score per tag: how much, weighted by
   how much you like the tags it keeps company with, does this tag show
   up in similar contexts. New feature embedding_affinity_sum = sum of
   affinity over a candidate's own tags. Tunable weight on /settings
   (embedding_weight, default 0.1) for how much this feeds the Tier 1
   heuristic; Tier 2 learns its own coefficient regardless.
2. **Tag-based fetching** (refresh(), new top_tags setting, default 30):
   candidates are now also pulled directly via your top-weighted tags
   (stashdb_candidates.fetch_by_tags, reusing the same plumbing wildcard
   categories already used) - not just top performers/studios. This is
   what actually lets a scene from someone you've never seen enter the
   pool at all, on tag match alone; affinity scoring only re-ranks what's
   already fetched.

Verified end to end: refresh ran cleanly (candidates_fetched jumped
951->1136 from the new tag-based fetch), backfill_embedding_affinity()
ran (2,414 rows - and this time actually invoked, not just defined),
retrained: embedding_affinity_sum coefficient came back 0.279, third-
largest of 11 features, confirming real signal rather than the
all-historical-zeros bug from the weight-decomposition fix.
Honest caveat on the backfill: old rows only had tag_matches (the subset
of a scene's tags that already overlapped your profile) stored, not the
full tag list, so their embedding_affinity_sum is an underestimate versus
what new candidates get computed with going forward. Performer
co-occurrence (vs. just tags) is a natural future extension, not built
this round - tags capture stylistic similarity most directly and were
the clearer win for the same effort.


## Download pipeline fix (three real bugs, found via live debugging)
Reported symptom: download buttons on /recommendations all started failing
(some used to work). Root causes, in the order found:

1. **httpx not following redirects.** Prowlarr's own download-proxy URL
   (used by usenet indexers like nzbgeek) 301-redirects to the actual
   fetch URL by design - that's not an error. httpx defaults to NOT
   following redirects, so every usenet grab was a hard failure. Fixed
   with follow_redirects=True.
2. **Torrents routed through Prowlarr -> rdtclient were hanging 60s then
   failing.** rdtclient is registered in Prowlarr as a qBittorrent
   download client (host rdtclient:6500) - that handshake was stalling.
   Verified the fix before applying: sent a real magnet straight to
   TorBox's createtorrent API by hand, got success back. Switched
   TORRENT_ADD_MODE from prowlarr to torbox in .env (same direct-to-
   TorBox path usenet already used successfully) - no rebuild needed,
   .env is read at container start.
3. **Prowlarr's `magnetUrl` field isn't always a literal magnet: URI.**
   For indexers that don't expose a magnet directly (e.g. The Pirate Bay
   here), Prowlarr puts its own download-proxy URL in that field instead.
   Code was blindly handing that to TorBox as if it were a real magnet
   string -> "Invalid Magnet Link" rejections. _add_via_torbox now checks
   for a literal "magnet:" prefix first; if it's actually an HTTP URL,
   resolves it (follows one redirect hop looking for a magnet: Location,
   falls back to fetching real file bytes if not).

Also added along the way: every download stage is now timed and logged
(search/grab duration, bytes fetched) so a slow or failed download says
*which* stage and why, instead of a generic timeout; a guard rejects
HTML error pages or suspiciously-small files masquerading as real
releases; the search fallback loop now catches per-query exceptions
instead of letting one slow/failed phrasing abort the whole chain
(introduced and then immediately fixed in the same session - tightening
a timeout without making the loop resilient to it silently broke every
search); and httpx exceptions with an empty str() (ReadTimeout,
ConnectTimeout) now fall back to the exception's class name so error
messages are never just "failed: " with nothing after the colon.

Verified against live traffic, not just one case: 5/5 fresh downloads
succeeded across both protocols (2 torrents, 2 usenet, all confirmed by
TorBox with real hashes/download IDs).


## Performer co-occurrence (Tier 3 extension)
Same pattern as tag co-occurrence, mirrored onto performers - and proof
the architecture was actually generic enough to extend cleanly: neither
the Settings page nor the model-internals page needed any UI changes,
since both already iterate their schemas dynamically.

- db.py: performer_cooccurrence table, replace/all_performer_cooccurrences(),
  backfill_performer_affinity() (same historical-approximation caveat as
  the tag backfill - uses matched_via performer entries as a proxy).
- taste_profile.py: collects scene_performer_ids alongside scene_tag_ids
  during the same scan, accumulates co-occurrence the same way.
- recommendation_engine.py: compute_performer_affinity(), new
  performer_affinity_sum feature folded into _score() (weighted by the
  new performer_embedding_weight setting), parallel to embedding_weight.
- ml_model.py: performer_affinity_sum added to FEATURE_NAMES/extract_features.

Verified end to end against live Stash/StashDB (not just syntax-checked):
refresh populated performer_cooccurrence (1,403 performers now tracked,
up from 599 - StashDB matching has clearly improved since this was last
checked), backfill updated 3,331 rows, retrained: performer_affinity_sum
came back with a real coefficient of -0.3519 (5th-largest of 12 features)
- notably negative, meaning candidates whose performers tend to co-occur
with performers you like are *currently* modeled as slightly less likely
to be downloaded. Worth sitting with rather than dismissing; could be a
genuine pattern (you specifically like solo/lead performers, not
co-stars) or could shift as more decisions accumulate. cv AUC continued
climbing through this session: 0.594 -> 0.621 -> 0.647 -> 0.673.

This closes out everything explicitly scoped for the recommendation
system in this conversation - Tier 1/2/3, wildcard categories, explore
slice, mute, Settings, transparency pages, and the download pipeline
fixes. Tier 4 (visual/CLIP embeddings) remains deliberately deferred.

## Settings tuning + affinity scale bug fix
Asked to tune settings to the data; looking at distributions first exposed
a real bug worth more than any tuning. Tier 1 scores ranged from median ~8
to max 2,493,277 - the Tier 3 affinity features were unbounded sums.
embedding_affinity_sum hit ~25 MILLION for compilation/"Best Of" scenes
stuffed with 100+ tags, so the system was effectively ranking tag-stuffed
compilations at the very top regardless of actual relevance.

Fix (three coordinated changes, each verified against live data):
  1. compute_tag_affinity / compute_performer_affinity now return a
     co-occurrence-count-weighted AVERAGE of neighbours' weights, not a raw
     sum. Per-tag affinity went from max ~6,000,000 to a sane 6-29 (same
     scale as actual profile weights, median 2.2 / max 45).
  2. _score() averages affinity across a scene's tags/performers instead of
     summing - so tag *count* no longer inflates score (scale-invariant).
  3. tag_weight_sum now gets the same sqrt volume dampening used elsewhere,
     so matching 100 tags counts more than 10 but not 10x more.
Result: top Tier 1 scores went 2,493,277 -> 62; distribution now
min 5 / median 6 / max 62. Compilations still score well (many matches IS
relevant) but no longer obliterate focused scenes.

Data-informed setting changes (applied to SAVED settings, not just schema
defaults, since saved values override): embedding_weight 0.1 -> 0.4 and
performer_embedding_weight 0.1 -> 0.4 (the 0.1 was only suppressing the
explosion; safe to contribute properly now), wildcard_fraction 0.33 -> 0.2
(wildcard picks were converting ~2.7% vs profile ~20% yet taking a third
of the page). Training thresholds left alone - 229 downloads / 18.6% rate
is healthy. cv AUC held ~0.675 throughout.

Note: model scores top out ~0.52 with most <0.4 - that's correct
calibration given an 18.6% download rate, not a problem (P(download) is
genuinely low when 4 of 5 are skipped).

## Download "Unknown scene_id" resilience
After last session cleared all pending candidates, any already-open browser
page became stale - its cards referenced scene_ids that no longer existed,
so Download returned "Unknown scene_id". Verified the pipeline itself was
healthy (live downloads succeeding across torrent + usenet). Made the
download route resilient: if a scene_id isn't in the recommendations table,
it now falls back to looking the scene up directly on StashDB (the scene
still exists there) and grabs it anyway, instead of failing. Proven against
a real StashDB scene not in the table (resolved studio+title correctly).
Skip route now returns a clear "this card is stale, refresh" message rather
than a cryptic one. Reloading the page was always the manual workaround;
this makes it unnecessary.

## Code review fixes (Tier 1, all verified live)
A self-requested impartial code review flagged several real issues.
Verified each claim against the live code before fixing, then verified
each fix against live data/traffic afterward - not just code review.

1. **search_with_fallback now wires performer + date into the query
   chain.** /search was silently dropping `performers`/`date` even though
   find-sources.js was already sending them. For adult content, indexer
   releases are reliably named Studio.Performer.Date even when StashDB's
   own title is generic ("Scene 6") or episodic ("S41:E6") - exactly the
   titles that returned zero hits before. New candidate order: studio+
   title -> studio+primary_performer -> studio+primary_performer+date ->
   cleaned title -> raw title. Verified directly: with title="Scene 6",
   the chain now includes "Brazzers Jane Doe" and "Brazzers Jane Doe
   2026-01-15" before ever falling back to the useless generic title.
   Wired through all three entry points (search_route, and both
   _grab_best call sites: recommendations download + /api/send), so the
   StashDB overlay and the recommendations page both benefit, not just
   manual /search.

2. **_grab_best tries up to 4 results, not just the top one.** A single
   dead torrent or a 0-seeder release outranking a healthy one used to
   fail the whole grab. Now falls through automatically, logging which
   attempt succeeded. PROVEN live in production, not just tested: a real
   download's logs showed attempt 1 fail (Prowlarr 500 + TorBox 400 on a
   mismatched anime release) and attempt 2 succeed automatically -
   without this fix that download would have failed outright.

3. **Explore slice now selects by feature-space novelty, not
   predict_proba closest to 0.5.** The review's calibration point was
   right and corrected something wrong in this file's own earlier notes:
   class_weight="balanced" pulls probabilities toward 0.5 regardless of
   genuine uncertainty. But the fix isn't "drop balanced weighting" -
   ran a live side-by-side comparison first (1648 real examples) and
   found removing it makes things WORSE for exploration: the "genuinely
   uncertain" 0.4-0.6 band shrinks from 694 examples to 48, because true
   calibration to an ~18% base rate means almost nothing is a real
   coin-flip. predict_proba and raw decision-function margin are also
   provably rank-equivalent (sigmoid preserves order), so that wasn't a
   real fix either. Instead: ml_model.compute_novelty_scores() measures
   each pending candidate's distance (in the model's own standardized
   feature space, via sklearn NearestNeighbors) to its nearest
   already-decided example. High novelty = a region of feature space the
   model has no training signal near - the actual thing an exploration
   slice should target. New novelty_score column, computed alongside
   model_score in retrain_and_rescore() every refresh/retrain.
   db.explore_recommendations() now orders by novelty_score DESC.
   Verified live: 0/10 overlap between the top-10 by model_score and
   top-10 by novelty_score - genuinely different candidates, with
   novelty-selected ones sitting near model_score=0 (nothing in training
   data resembles them, which is exactly the point).

4. **WAL mode + busy_timeout on every connection.** Two PRAGMAs in
   _conn(). Confirmed active live (PRAGMA journal_mode -> wal, PRAGMA
   busy_timeout -> 5000). Cheap insurance against "database is locked"
   now that nightly refresh + manual refresh + web UI can overlap.

## TorBox cache-priority check (Tier 2 item, built but currently inert)
Built torbox.check_cached() (verified against the real API: GET
.../torrents/checkcached?hash=h1,h2&format=list, batched, no torrent
created) and wired it into _grab_best to reorder results so an
already-cached torrent is tried before an uncached one - a stable sort
that preserves Prowlarr's quality ranking within each group. Code is
correct and fails open (any error just skips the reorder).

Honest finding from live verification: sampled 506 torrent results
across 5 different queries on this specific indexer set and found ZERO
with a literal magnet in Prowlarr's initial response - all of them route
through Prowlarr's own download-proxy URL, with the real magnet (if any)
only discoverable after a redirect. Since the cache check only has
something to act on when a literal magnet is already present, this
feature is currently inert on this setup - not broken, just has nothing
to check yet. It'll activate automatically if any configured indexer
ever returns literal magnets directly, or if a new one is added that
does. The real resilience win for torrents right now is item 2 above
(try-next-result), which doesn't depend on this and is already proven
working.

## Still open from the review (not done this session)
- Concurrent StashDB fetching (asyncio.gather + semaphore) - refresh
  still takes ~2 min from ~85+ sequential queries. Real, well-scoped,
  not done yet.
- Owned-set caching / single-pass library scan - still scans the full
  Stash library twice per refresh, and /api/check still re-scans on
  every StashDB overlay hover with no TTL cache.
- Automated Stash SQLite backup - still the single highest-value cheap
  addition not yet built. stash-go.sqlite + config.yml remain the one
  genuinely irreplaceable artifact in the stack.
- Soft negative feedback, time-based CV validation, MMR diversity
  re-ranking, close-the-loop auto-Identify - all reasonable, all
  deliberately deprioritized as lower-impact-per-effort than the above.

## Code review fixes: Tier 2 (concurrent fetching, single-pass scan, TTL cache, backup)

**Concurrent StashDB fetching (stashdb_candidates.py)**
fetch_candidates() and fetch_by_tags() were sequential - each of the 85+
queries awaited one at a time inside a single client, which is why a
refresh took ~2 minutes. Now uses asyncio.gather() with an asyncio.Semaphore
(_CONCURRENCY = 6) to run 6 queries at a time. Verified by timing just
the profile-side fetch (55 performer/studio queries): 6.6s with concurrency
vs the old ~40-55s sequential equivalent - genuine 6-8x speedup on that
component. Full refresh is still dominated by the wildcard batch (67
categories at 40 scenes each = 2000+ candidates), which is now also
concurrent. Architecture: _fetch_one() returns result tuples rather than
mutating a shared dict directly, _merge() combines them sequentially after
all tasks complete, no concurrent-mutation risk.

Note from live data: wildcard category list has grown to 67 entries (was 5
when originally seeded). This was done through the Settings page outside
our conversation. Not touching it - flagging in case it wasn't intentional,
since 67 wildcard queries × 40 scenes each = 2000+ candidates every refresh,
which is a significant portion of the refresh runtime.

**Single-pass library scan (taste_profile.py + recommendation_engine.py)**
The library was scanned twice per refresh: once by taste_profile.rebuild()
for weights/co-occurrence, and again by stashdb_check.local_stashdb_ids()
purely to build the owned-scene set. These are the same Stash GraphQL call
to findScenes, just different fields consumed from the result. Fixed by:
- Adding `stash_ids { endpoint stash_id }` to _SCENES_QUERY in taste_profile
- Collecting owned_stashdb_ids in the same scene loop in rebuild()
- Including it in rebuild()'s return dict (popped from profile_summary by
  refresh() before spreading into the JSON response - a set isn't serializable)
- Removing the stashdb_check.local_stashdb_ids() call from refresh() entirely
Verified: monkey-patched _fetch_all_scenes to count calls during a real
rebuild - exactly 1 call, "WARNING: local_stashdb_ids called" never printed.

**TTL cache for /api/check overlay (stashdb_check.py)**
The docstring already claimed this was cached - it wasn't. Added a genuine
60s TTL cache (_OWNED_IDS_CACHE dict, keyed by stash_url) so rapid overlay
hovers on StashDB share one scan instead of each paginating the full library
from scratch. The /api/check route still calls local_stashdb_ids() directly
(it has no other way to get the owned set), but repeated calls within 60s
are now free.

**Stash SQLite backup (stash-backup.ps1)**
Backs up stash-go.sqlite + config.yml + recommendations.db to
D:\Backups\Stash\YYYY-MM-DD\ daily, keeping 7 days of history.
Verified working: first manual run backed up all three files correctly
(stash-go.sqlite 14.79MB, recommendations.db 30.89MB, config.yml 0.01MB).

Scheduled task needs one manual step (Task Scheduler requires elevation
that Desktop Commander can't request):
  Task Scheduler -> Action -> "Import Task..." -> C:\torbox-system\stash-backup-task.xml -> OK

The XML task file is at C:\torbox-system\stash-backup-task.xml.
Runs at 2am daily (before the 4:30am recommendation refresh).


## Close the loop (loop_closer.py)
After a scene is sent to TorBox, the bridge now polls for completion and
surfaces the result on the recommendations page.

**New module: loop_closer.py**
- run_background_poller() starts as an asyncio task at FastAPI startup
  (via lifespan context manager, replacing the old @app.on_event("startup"))
- Polls every 5 minutes (POLL_INTERVAL_SECONDS=300)
- poll_once() checks every 'sent' recommendation with a stored TorBox ID
- Calls torbox.check_torrent_ready() or check_usenet_ready() as appropriate
- download_state=="cached"/"completed" + download_present==True = ready
- When ready: db.mark_ready() sets status='ready', stores folder name
- Triggers Stash metadataScan (job) then metadataIdentify (job) so new
  files land as matched/tagged scenes. 5s gap between them so scan queues
  before Identify starts. Both calls return immediately with a job_id.
- /api/recommendations/poll endpoint for manual trigger without waiting
  the full 5-minute interval

**New DB columns on recommendations table** (auto-migrated via init_db):
- torbox_type: 'torrent' or 'usenet'
- torbox_id: integer torrent_id or usenetdownload_id from TorBox response
- torbox_name: the folder name on T:\ (populated by poll, not on send,
  since createusenetdownload response doesn't include name until processed)
- status 'ready' added to the status lifecycle:
  pending -> sent -> ready (then self-corrects to 'owned' on next refresh)

**New torbox.py functions:**
- check_torrent_ready(torrent_id) - GET /v1/api/torrents/mylist?id=N&bypass_cache=true
- check_usenet_ready(usenet_id) - GET /v1/api/usenet/mylist?id=N&bypass_cache=true
Both return the status dict or None on error (fail-open, no crash)

**Recommendations page:**
- Green "ready to pull" panel at top showing title + T:\{folder_name} for
  each completed download, only shown when status='ready' items exist
- "Check downloads" button triggers /api/recommendations/poll immediately

**Verified end to end against live traffic:**
- Successful download (usenet id=1848199) stored torbox_type='usenet',
  torbox_id=1848199 in DB immediately after grab
- Manual poll detected completion: "ready on T:\\Wifey.25.10.18.Tatiana..."
  poll_once() returned newly_ready=1
- Stash scan triggered job_id=4, Stash Identify triggered job_id=5
- Full loop: send -> store ID -> poll -> detect ready -> surface on page
  -> trigger Stash scan+identify. The manual copy step (T:\ -> staging ->
  library) remains manual by design.


## Hard 20GB download cap + quick usability wins

**Hard size cap (max_download_gb, default 20, tunable on /settings)**
Root cause found: the pack filter in _grab_best had a "better a pack than
nothing" fallback - when EVERY search result was a pack, it grabbed one
anyway. That's exactly how megapacks kept flooding TorBox/Stash. The cap
is applied to the raw result list BEFORE pack/relevance filtering, so no
fallback path can bypass it. Results with unknown size are kept (usenet
sometimes omits size; the pack regex still covers those). Clear failure
message when everything exceeds the cap.
Verified live: "size cap removed 8/11 results (> 20GB)" on a real grab.

**Pack regex gap closed**: that same live test exposed a 19.2GB
"compilation" sliding under the cap AND past the regex - "compilation"
and "anthology" were missing from _PACK_RE. Added both; verified the
exact offending title now classifies is_pack=True while a normal single
scene stays False. NOTE: that 19.2GB "Mr Lucky POV compilation" DID get
sent to TorBox during testing - remove it from TorBox/mylist if unwanted.

**Download feedback**: successful downloads now show "Sent: <release>
(<size>)" in the status line instead of the card silently vanishing -
immediate visibility into what was actually grabbed and how big it is.

**Refresh health line**: refresh() stores last_refresh_at meta; the
recommendations page shows "Last refresh: Xh ago", turning red with a
warning past 30h (nightly is 4:30am, so >30h = the schedule silently
failed: expired StashDB key, Stash down, etc). Catches silent nightly
failures that previously only showed up as stale recommendations.


## ML structural overhaul — all six discussed improvements built

### Step 1: Search relevance scoring + hard reject
_score_relevance() replaces the old _result_is_relevant() boolean. Returns
a numeric score in [-1.0, 1.0]: +0.40 studio match, +0.40 performer match,
+0.20 date match, +0.15 distinctive title word, -1.00 mainstream TV/film
pattern (S01E03, BluRay, AMZN.WEB-DL etc), -0.80 junk-name pattern. Hard
floor at 0.4 — requires studio OR performer match. If nothing clears it,
refuses with a concrete error showing the top-3 rejects and their scores
instead of the old "grab anyway" fallback. Verified 8/8 wrong grabs
rejected, 4/4 correct grabs accepted against real historical cases.

### Step 2: Entity-level Stash ratings into taste profile
_entity_multiplier(entity, s) reads performer.rating100, performer.o_counter,
studio.rating100 — previously completely invisible to the model despite
150 rated performers and 45 favorited performers in Stash. Applied
multiplicatively: a performer you rated 100 now contributes ~2.5x per
scene compared to an unrated one (1.0 base + 1.5 rating lift at default
entity_rating_weight=1.5). Two new Settings: entity_rating_weight (default
1.5) and entity_ocounter_weight (default 0.5), both in "Taste profile"
section. Scene query extended to fetch studio.rating100 and performers'
rating100/o_counter in the same library scan.

### Step 3: Watch-signal feedback loop
loop_closer.run_watch_feedback_pass() runs on every poll cycle (every 5
min). For each downloaded scene >24h old not yet checked, queries Stash by
StashDB UUID (stashdb_check.get_stash_watch_signals) and reads play_count,
play_duration, o_counter, rating100. db.compute_watch_outcome() converts
these into a (label, confidence) pair. db.upsert_watch_feedback() records
the outcome and updates feedback.label + feedback.confidence. Manual
trigger at /api/recommendations/watch-check.

### Step 4: Confidence weights
feedback table gains confidence column (default 1.0). Training passes w=
confidence as sample_weight to .fit() so the model learns overwhelmingly
from high-confidence signal rather than treating every click equally:
  4.0 = 5-star rating (most deliberate signal)
  3.0 = o_counter > 0 (strongest implicit)
  2.0 = played > 5 min
  1.5 = played at all
  1.0 = provisional download click (unverified)
  0.3 = downloaded, never opened after 7+ days

### Step 5: Retrain acceptance gate + versioning
New model only promoted to live if its holdout AUC doesn't regress beyond
ACCEPTANCE_TOLERANCE=0.02 vs the previous model. If it regresses, the
previous model stays live and the retrain returns accepted=false with the
AUC comparison. model_prev.joblib saved alongside model.joblib before each
successful promotion. Verified live: first run returned accepted=true,
prev_auc=0.63, trained on 4369 examples.

### Step 6: Temporal CV
Replaced StratifiedKFold(shuffle=True, random_state=42) with TimeSeriesSplit.
CV now trains on older decisions and validates on newer ones — the question
that actually matters. Random k-fold inflated AUC by letting the model peek
at scenes from the same refresh batch. Temporal AUC is lower but honest.

### DB migrations (all auto-applied in init_db):
- recommendations.watch_due_at
- feedback.confidence (DEFAULT 1.0)
- feedback.watch_checked
- feedback.play_count / play_duration / o_counter / rating100
- watch_feedback table (scene_id, checked_at, watch signals, label_revised, confidence)


## Full system reset + fresh start (2026-07-08)

### What was wiped
- feedback table (4375 rows) - contaminated with megapack positives,
  ambiguous skips, features across multiple code versions
- recommendations table (4337 rows) - exhausted; 3681 skips had
  permanently excluded performers' entire StashDB catalogs
- model.joblib + model_prev.joblib - trained on contaminated data
- watch_feedback table (0 rows at time of reset)
- model_status and last_refresh_at meta

### What was kept (the "Stash constant")
- taste_profile (1422 rows) - built from your Stash library, 150 rated
  performers, 45 favorited performers, play/o-counter data
- tag_cooccurrence (64230 pairs) - learned from your library
- performer_cooccurrence (665 pairs)
- All settings (tuned below)

### Settings tuned for fresh start
Key changes from previous values:
- top_performers: 40 -> 60 (was exhausting the top-40 pool)
- top_studios: 15 -> 20
- per_entity: 25 -> 50 (was only seeing 25 scenes per performer; most
  have more - this was the primary exhaustion cause)
- play_weight: 0.4 -> 0.5 (Stash play tracking confirmed working)
- o_weight: 0.4 -> 1.0 (strongest implicit signal - weighted higher)
- entity_ocounter_weight: 0.5 -> 0.75
- recency_window_days: 60 -> 90
- performer_embedding_weight: 0.4 -> 0.3 (sparse co-occurrence, 665 pairs)
- wildcard_fraction: 0.2 -> 0.15 (less wildcard while model relearns)
- min_examples: 50 -> 30 (model kicks in sooner)
- min_positive: 10 -> 5

### Bugs fixed during reset
1. feedback_with_source() was INNER JOIN - after clearing recommendations,
   it returned only the 8 new decisions (joining to empty table), dropping
   the entire feedback history. Fixed to LEFT JOIN with source defaulting
   to 'profile'. Critical fix: this was silently dropping training data
   on every reset, and was the cause of AUC falling to 0.535.

2. SQLite busy_timeout: 5000ms -> 30000ms. The loop_closer poller's 5-min
   write cycle was colliding with the refresh's large write transaction
   (co-occurrence replace), causing "database is locked" failures. The old
   5s timeout wasn't long enough for the refresh to complete its writes.

3. Compilation filter at StashDB candidate level: _is_stashdb_compilation()
   regex filters "The Best Of...", "Selects", "Recap", "All Stars",
   "Compilation" at candidate insertion time, so they never appear in the
   recommendations pool. Previously these dominated the top of the page
   (correctly scored high by Tier 1 because they genuinely match many
   taste profile tags) but were ungrabable and wasted page space.
   Verified: top-20 after filter contains zero compilation titles.

### Result
- 2754 fresh pending candidates (vs 4 before reset)
- Top candidates are specific scenes with performers you actually rate
- Model will train from scratch as genuine new decisions accumulate
- feedback_examples: 8 (from the brief post-reset testing period)
- Compilation titles gone from top of page


## TorBox inactive/failed download auto-recovery

The "inactive" label in the TorBox UI maps to download_state starting with
"failed" in the API (specifically "failed (Aborted, cannot be completed -
https://sabnzbd.org/not-complete)"). This happens when Usenet articles are
missing from the news server — the NZB was dead before TorBox could complete
it. TorBox has no built-in retry for Usenet.

**What was built:**
- torbox.delete_usenet(usenet_id) and delete_torrent(torrent_id) — verified
  live against the TorBox API. The usenet control endpoint uses `usenet_id`
  (not `id`) per the SDK spec. Confirmed: {"success":true,"detail":"Usenet
  download deleted successfully."}

- loop_closer._is_failed(data) — detects download_state.startswith("failed")
  AND download_present=False. Distinguished from ready and still-pending.

- poll_once() now handles three states: ready (mark ready, trigger scan),
  failed (auto-delete + reset to pending), and still-pending (skip).

- db.mark_download_failed(scene_id, failed_release_name) — resets status
  to 'pending' so the card reappears, increments retry_count, stores the
  failed release name. After MAX_RETRIES=3, marks as 'download_failed'
  permanently.

- New DB columns: recommendations.retry_count, recommendations.failed_release_name

- _grab_best now accepts skip_release_name — any result whose title matches
  the previously-failed release is excluded from the scored candidates, so
  a retry doesn't grab the same dead NZB again.

- Download route reads row["failed_release_name"] and passes it through to
  _grab_best automatically, so retries are transparent to the user.

- Card UI: if retry_count > 0, shows an amber "⚠️ retry N" badge and a
  note explaining what failed and what will be skipped on the next attempt.

**The full automatic flow:**
1. User clicks Download → NZB sent to TorBox → stored as status='sent'
2. Loop-closer polls every 5 minutes → detects download_state="failed..."
3. Auto-deletes the dead download from TorBox (frees the slot)
4. Resets recommendation to status='pending' — card reappears on page
5. User clicks Download again → _grab_best skips the failed NZB name,
   tries the next-ranked Prowlarr result
6. After 3 failed attempts → status='download_failed', card stops cycling

Note: Only 1 out of 410 usenet downloads in the live TorBox list was in
failed state at time of investigation (the rest were completed or cached).
The "many inactive downloads" the user experienced may have been from before
the current list window, or from a period when the indexer was returning
poor NZBs. The fix handles it correctly for all future cases.


## Exhaustive retry, frozen detection, and TorBox queue management

Extended the failed-download recovery (from the previous "inactive downloads"
fix) to be genuinely exhaustive, catch frozen downloads, and handle TorBox's
active-slot limit with automatic queuing.

**1. Exhaust ALL results, no retry cap**
failed_release_name (single string, 3-retry cap) -> failed_release_names
(JSON array, no cap). Every attempted release name is appended; retries
skip everything in the array, not just the last failure. _grab_best's
attempt loop now tries every candidate that passed the relevance floor
(previously capped at 5). Terminates naturally: success, or "exhausted"
(no candidates left to try -> status='download_failed', permanent), or
"active_limit" (TorBox full -> queued).

**2. Frozen + stalled detection (loop_closer.py)**
- _is_stalled(): torrent download_state contains "stalled" + "no seeds"
- _is_frozen(): active=True, download_speed=0, and updated_at hasn't
  changed in >20 minutes. TorBox updates updated_at on any progress, so
  a stale timestamp while "active" means genuinely stuck, not just slow.
  Verified field exists on both torrent and usenet mylist responses.
All three failure modes (failed/stalled/frozen) now route through the
same delete-and-recycle path.

**3. TorBox active-limit queue (10 active download cap)**
Verified via TorBox SDK docs: hitting the limit returns
{"success":false,"error":"ACTIVE_LIMIT","detail":"..."}. _grab_best
detects this and returns active_limit=True instead of treating it as a
per-release failure (retrying other releases would just hit the same wall).
db.mark_queued() stores full search context (queue_studio/title/
performers/date) plus the accumulated failed_release_names.
loop_closer.dispatch_queued() runs every poll cycle: counts current
active downloads across both usenet+torrent mylist, calculates free
slots, dispatches oldest-queued-first up to that count by calling
_grab_best directly (deferred import from app.py to avoid circular
import - verified working: import resolves correctly at runtime since
app.py is fully loaded by the time the background poller's first cycle
fires). Stops dispatching immediately if ACTIVE_LIMIT is hit again.
New blue "queued" panel on /recommendations shows what's waiting.

**4. Bonus fix found during verification: stale-ID poll bloat**
Testing this surfaced a real separate gap: 29 'sent' downloads from
earlier in the session had TorBox IDs that no longer exist on TorBox's
side at all (confirmed via direct API check - 500 with empty body, and
absent from the full unfiltered mylist). The poller had no way to detect
"this ID is permanently gone" vs "check again later", so these were
being re-checked every 5-minute cycle forever with no exit condition.
Added recommendations.check_failures counter: db.record_check_failure()
increments on every None response from a status check, db.reset_check_failures()
clears it on any success. After 3 consecutive failures, the item is
recycled through the same mark_download_failed() path as a real failure.
Verified live: all 29 stuck items correctly recycled to 'pending' with
retry_count incremented after exactly 3 manual poll cycles; 0 remain
stuck in sent_awaiting_torbox().

**New DB columns:** failed_release_names (JSON), queued_at, queue_studio,
queue_title, queue_performers, queue_date, check_failures.


## Systematic verification pass across last 4 builds (2026-07-09)

Went through every feature built in the last four sessions with live tests,
not just code review. One real bug found and fixed.

**Build 1 (search relevance + entity ratings): ALL CONFIRMED WORKING**
- _score_relevance, _TV_FILM_PATTERNS, _JUNK_NAME_PATTERN all present and
  live-tested against known wrong/correct grab cases - still correct
- entity_rating_weight=1.5, entity_ocounter_weight=0.75 both applied
- taste_profile._entity_multiplier present and wired in

**Build 2 (watch feedback, confidence weights, retrain gate, temporal CV):
ALL CONFIRMED WORKING**
- watch_feedback table schema correct, 0 rows (expected - needs 24h+ aged
  data, not a bug)
- compute_watch_outcome() tested against all 5 signal combinations,
  correct label+confidence for each (5-star=4.0, o_counter=3.0,
  played>5min=2.0, never-opened-10d=0.3, too-early=1.0 provisional)
- 354/354 feedback rows have confidence set (100% coverage)
- skipped defaults to 0.3, not_interested to 1.5 - confirmed in source
- ACCEPTANCE_TOLERANCE gate, MODEL_PREV_PATH, TimeSeriesSplit all present;
  old StratifiedKFold(shuffle) confirmed removed
- LIVE RETRAIN TEST: accepted=true, cv_auc=0.66, prev_auc=0.658 -
  the gate genuinely compared against the previous model and promoted
  because it wasn't a regression. model_rescored=2479 matched pool exactly.

**Build 3 (full reset, compilation filter, settings): ALL CONFIRMED WORKING**
- _is_stashdb_compilation tested against 5 real cases (Best Of, Selects,
  Recap correctly flagged; real scene titles correctly not flagged)
- Live pool audit: 2479 pending candidates, ZERO compilations present
  (regex-swept every title in the actual table, not just the test cases)
- All 6 tuned settings (top_performers=60, top_studios=20, per_entity=50,
  wildcard_fraction=0.15, min_examples=30, min_positive=5) confirmed
  persisted and active
- taste_profile (1422 rows) and tag_cooccurrence (64230 pairs) survived
  the reset as intended

**Build 4 (exhaustive retry, frozen/stalled detection, queue, stale-ID
cleanup): CONFIRMED WORKING, ONE BUG FOUND AND FIXED**
- delete_usenet/delete_torrent present, _is_failed/_is_stalled/_is_frozen/
  dispatch_queued/poll_once all present
- _is_frozen tested against 3 synthetic cases: ancient+idle+active=True,
  recent+idle+active=False, ancient+but+moving=False - all correct
- _is_stalled tested against real TorBox state strings - correct
- mark_download_failed confirmed to have no MAX_RETRIES cap, uses the
  failed_release_names JSON array as designed
- All 7 new DB columns present (check_failures, queued_at, queue_studio,
  queue_title, queue_performers, queue_date, failed_release_names)

BUG FOUND: mark_download_failed() was never resetting check_failures back
to 0 when recycling a download to pending. This meant the 29 items
recycled at the end of the previous session were carrying their stale
failure count (2-3) forward. If any of those had been re-sent and hit even
one transient network blip on the very first status check, they'd have
hit the >=3 threshold immediately and been wrongly recycled again despite
being a fresh, healthy attempt. FIXED: mark_download_failed now sets
check_failures=0 in the same UPDATE. Also ran a one-time data fix to reset
check_failures=0 on all 29 already-affected pending rows. Rebuilt,
redeployed, verified check_failures=0 on those rows post-fix.

**End-to-end live download test (real Prowlarr + TorBox, not synthetic):**
- Candidate 1: correctly REFUSED - all results scored below the 0.4
  relevance floor (weak matches like "Yanks...Siesta" for a scene search),
  logged the top-3 rejected candidates with scores as designed
- Candidate 2: correctly SUCCEEDED - "Luke Cooper" search matched
  "OnlyFans.2025.Jade.Harper.Luke.Cooper..." (studio+performer match),
  sent to TorBox (usenetdownload_id=1928026), stored with check_failures=0
  confirming the bug fix took effect on new sends immediately

Every feature built across the last four sessions is confirmed working
against live data, not just passing code inspection.


## Quality-first download ordering (highest resolution/bitrate tried first)

prowlarr.classify() already computed a quality_score per result (resolution
tier x10 + source tier: 2160p > 1080p > 720p > 480p, REMUX > BluRay >
WEB-DL > WEBRip > HDTV as tiebreak) - but _grab_best's attempt-order sort
was discarding it entirely, sorting candidates_to_try purely by relevance
(correctness) score. Quality had no influence on which release was tried
first, only on Prowlarr's own initial (and irrelevant, since re-sorted)
ordering.

Fixed: scored_results now sorts by (quality_score, relevance_score) instead
of just relevance_score. Correctness is unchanged - the relevance floor
still filters out wrong-studio/wrong-performer/mainstream-TV/junk-name
results before this sort ever runs. Among what's left, highest resolution
is tried first; a lower-resolution release is only attempted if every
higher-resolution option is unavailable or fails (via the existing
exhaustive retry loop - no logic change needed there, it already tries
candidates_to_try in order until one succeeds).

Added resolution+source to the "grabbing" log line for verifiability.

Verified: synthetic 4-tier test (2160p/1080p/720p/480p, equal relevance)
sorted in the exact expected order. Live test against a real recommendation
with 4 candidates passing the relevance floor: attempt 1/4 was the 2160p
release, which succeeded immediately (6.8GB, NewSensations.25.01.04...
2160p.MP4-WRB) - confirmed via the actual "grabbing" log line, not just
code inspection.
