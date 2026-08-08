# stash-torbox-bridge

A tiny glue service that turns a Stash scene page into a "Find Sources" button:
it searches your **Prowlarr** (which already aggregates Bitmagnet, your public
trackers, and NZBGeek), shows ranked results with quality badges, and grabs the
one you pick — torrents through your existing **Prowlarr → rdtclient → TorBox**
pipeline, NZBs straight to **TorBox's usenet API**.

```
Stash scene page
   │  (Find Sources button reads Studio + Title via Stash GraphQL)
   ▼
bridge  ──GET /search──►  Prowlarr  ──►  Bitmagnet + trackers + NZBGeek
   │                         (merged, de-duped, ranked)
   ▼
results page (quality badges, Add to TorBox)
   │
   ├─ torrent ─► Prowlarr grab ─► rdtclient ─► TorBox
   └─ usenet  ─► TorBox usenet API
```

## Why this shape

- **One search surface.** Everything (Bitmagnet, public trackers, NZBGeek) is
  already an indexer in your Prowlarr, so the bridge only talks to Prowlarr.
- **No parallel download path for torrents.** It asks Prowlarr to *grab*, so the
  release flows through the same rdtclient→TorBox plumbing as the rest of your
  stack, with the same categories and handling.
- **Fills your usenet gap.** You have no usenet download client wired up, so NZBs
  go directly to TorBox's usenet API instead.

## Setup

1. **Copy config**

   ```powershell
   cp .env.example .env
   notepad .env
   ```

   Fill in `PROWLARR_URL`, `PROWLARR_API_KEY`, `TORBOX_API_KEY`.

2. **Run the bridge**

   ```powershell
   docker compose up -d --build
   ```

   Sanity check: open `http://localhost:8770` and run a manual search.

3. **Add the Stash button**

   In Stash: **Settings → Interface → Custom Javascript** (enable Custom JS if
   needed). Paste the contents of `stash-plugin/find-sources.js`, set
   `BRIDGE_URL` near the top to wherever the bridge is reachable *from your
   browser* (e.g. `http://localhost:8770` or your Tailscale address), save, and
   reload Stash. A **Find Sources** button appears on scene pages.

## Add routing options

Set in `.env`:

| Var | Default | Meaning |
|---|---|---|
| `TORRENT_ADD_MODE` | `prowlarr` | Grab via Prowlarr → rdtclient → TorBox. Set `torbox` to push magnets straight to TorBox instead. |
| `USENET_ADD_MODE` | `torbox` | Push NZB to TorBox usenet API. Set `prowlarr` if you later add SABnzbd/NZBGet to Prowlarr. |
| `PROWLARR_CATEGORIES` | (blank) | Restrict to categories, e.g. `6000` for the XXX group. |

## Files

| File | Purpose |
|---|---|
| `app.py` | FastAPI service: `/search` (results page) + `/add` (grab) |
| `prowlarr.py` | Prowlarr search, quality classification, and grab |
| `torbox.py` | TorBox add client (magnet / .torrent / .nzb) |
| `stash-plugin/find-sources.js` | The Stash button |

## Notes & next steps

- The button reads metadata live from Stash, so it works on any scene Stash
  knows about — no extra StashDB calls needed.
- Quality ranking is a simple title parse (resolution weighted over source). If
  your indexers name releases oddly, tweak the regex tables in `prowlarr.py`.
- Natural upgrade later: replace the new-tab results page with an in-Stash modal
  using `window.csLib` from the CommunityScripts UI library, so you never leave
  the scene page. The bridge endpoints stay identical.
- TorBox grabs (`createtorrent` / `createusenetdownload`) are rate-limited to
  60/hour per API key; the Prowlarr grab path isn't subject to that.
- Acquire only content you're entitled to — this just points your existing
  stack at a nicer front door.
