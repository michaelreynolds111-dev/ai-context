# Stash Identification & Metadata Runbook

Goal: get the maximum number of scenes identified against StashDB with quality metadata.
Current baseline: ~3,219 / 10,097 identified (32%). Realistic target: 60–80%.

The core truth: **Identification quality is driven by fingerprint matching (phash + oshash)
against StashDB.** Everything else is a fallback. If a scene has no phash, or StashDB has
never had that scene fingerprinted, it will not auto-identify — no amount of re-running helps.

---

## PART A — THE AUTOMATED SETUP (run in this order)

### Step 1. Generate phashes  [FOUNDATION — do this first, always]
Settings → Tasks → Generate
  ✅ Phashes
  ✅ Covers
  ⬜ everything else (previews/sprites/transcodes are cosmetic + slow)
Run on the whole library. Hours on 10k scenes. This is the single highest-impact action.
Without phashes, StashDB can only match on filename guesses.

  > Status: LAUNCHED (job 67) on 2026-07-02. Covers the ~6,800 unidentified + any missing.

### Step 2. Identify against StashDB + ThePornDB  [THE MAIN EVENT]
Settings → Tasks → Identify → Configure sources IN THIS ORDER:
  1. StashDB          (primary — best data, community-curated)
  2. ThePornDB        (secondary — fills scenes StashDB lacks; already connected)

Field options (per source, click the gear):
  - Set every field to "Overwrite" ONLY if empty  → i.e. don't clobber good data
    Practically: Title/Date/Studio/Code/Details/Director = Merge (fill if blank)
  - Performers  = Merge  (create missing)
  - Tags        = Merge
  - Studio      = Merge (create missing)
  - Cover image = Overwrite if empty
  Include male performers: your call (ON = more complete).
  Set Organized flag on match: ON — this is your "identified & trusted" marker.

Options:
  - "Skip scenes that already have a match at this endpoint" = ON  → makes re-runs fast
  Run on the whole library. Fingerprint matches are near-instant; the slow part is
  network calls per scene.

### Step 3. Re-run Identify after phashes finish
Because Step 1 (phashes) and Step 2 (Identify) touch the same scenes, the FIRST identify
pass only benefits scenes that already had phashes. Once job 67 completes, run Identify
AGAIN — now the freshly-phashed 6,800 scenes become matchable. This second pass is where
the big jump happens.

### Step 4. Schedule it to stay maintained (set-and-forget)
Settings → Tasks → Scheduled Tasks (or the Scan/Generate/Identify scheduler):
  - Nightly (or after each Scan): Generate phashes for NEW files only (overwrite OFF)
  - Nightly: Identify with "skip already-matched" ON
  This means every new TorBox download that lands via your loop-closer gets auto-phashed
  and auto-identified overnight without you touching anything.
  (Your loop-closer already fires a targeted Identify per new file — this scheduled pass
   is the safety net that catches anything the targeted pass missed.)

---

## PART B — THE MANUAL FALLBACK (for what automation misses)

After A, you'll have a residue of unidentified scenes. Work them in this order — easiest
wins first.

### B1. Bulk manual match via StashDB tagger view  [highest yield]
Go to the Scenes page → switch to the "Tagger" view (top-right icon).
  - Set the tagger source to StashDB.
  - It shows each scene with StashDB's best fuzzy guesses side by side.
  - phash matches show a green fingerprint icon — those are safe one-click confirms.
  - Filter the scene list to "Not Organized" first so you only see un-trusted scenes.
This is the workhorse for near-misses: scenes that have a phash but the auto-Identify
wasn't confident enough to auto-apply.

### B2. Per-scene scrape by name
On an individual unidentified scene → "Scrape with…" → StashDB → search by title.
Use when the filename has a real title in it. Confirm the match, save.

### B3. Studio-specific scrapers  [for content StashDB doesn't have]
For studio rips that StashDB lacks but the studio site has:
  Scene → Scrape with… → [studio scraper] (Babes, ManyVids, Javbus, etc.)
These need either a URL on the scene or NAME support. Check what each supports:
  - NAME-capable (search by title): Babes, ManyVids, Javbus, FreeonesCommunity, avbase
  - URL-only (needs a URL in the scene first): IAFD, CamSoda, Baberotica, most cam sites

### B4. IAFD — use on PERFORMERS, not scenes
IAFD scene scraping is URL-only (that's why it "sometimes doesn't appear" — it only
shows when the scene already has a URL). Its real strength is performers:
  Performer → Scrape with… → IAFD → searches by name. Fills bio, aliases, measurements,
  career dates, etc. Run this across your performers once for a big quality bump.

### B5. The genuinely-unidentifiable residue
Accept that some scenes never match: obscure/defunct studios, OnlyFans/cam customs,
old 540p rips, homemade megapack content. For these:
  - Filename parsing + Auto Tag (Settings → Tasks → Auto Tag) can at least attach
    performers/studios/tags by matching names in the path against your existing entities.
  - Then manually title what's worth titling; leave the rest.

---

## MEASURING PROGRESS
Identified % = scenes with a StashDB stash_id ÷ total scenes.
Re-check after each phase. Expect: 32% → ~50% after first Identify → 65–80% after
phashes complete + second Identify + tagger-view cleanup.

## ORDER SUMMARY (the whole thing in one line)
phash ALL → Identify (StashDB→TPDB) → wait for phash to finish → Identify AGAIN →
Tagger-view cleanup → studio scrapers for the rest → IAFD on performers → Auto Tag the residue.
