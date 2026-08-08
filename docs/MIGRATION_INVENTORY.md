# Migration Inventory

Live tracking document for locating and migrating scattered project files,
folders, and Claude Projects into the new LibreChat/ai-context structure.

Companion to Appendix A of `BACKUP_AI_MASTER_BUILD_PLAN.md` (the static
worksheet template) — this file is the actual working inventory, updated as
each item is located, classified, and migrated.

**Goal:** every current Claude Project and scattered working folder ends up
either fully migrated into `~/ai-context/projects/<name>/` (+ a LibreChat RAG
collection + agent), or explicitly marked as staying where it is with a reason.

## Status legend
- 🔴 **NOT LOCATED** — exists but current file location on disk is unknown
- 🟡 **LOCATED** — found on disk, not yet classified or migrated
- 🟢 **MIGRATED** — files moved/copied into ai-context/ or a RAG collection, agent built
- ⚪ **STAYING PUT** — deliberately not migrated (reason given)

## Claude Projects inventory

| Project name | Status | Current location | Sensitivity | Target | Notes |
|---|---|---|---|---|---|
| Building AI System | 🟢 N/A | This build itself | General | N/A — is the system | Not migrated, is the infrastructure |
| New Build (Stash/recommendation system) | 🔴 NOT LOCATED | Unknown | TBD | `projects/new-build/` (dir created 8 Aug 2026) | First Phase 6 candidate — awaiting Project Instructions + knowledge file details from Michael |
| Paperwork | 🔴 NOT LOCATED | Unknown | TBD | TBD | Pinned project — likely active/high-use |
| Achriom | 🔴 NOT LOCATED | Unknown | TBD | TBD | Pinned project — media/library tool per MCP tools available |
| Ron Admin | 🔴 NOT LOCATED | Unknown | TBD | TBD | |
| RateYourMusic Connector | 🔴 NOT LOCATED | Unknown | TBD | TBD | "make RYM work how I wish it would" |
| Tax Return | 🔴 NOT LOCATED | Unknown | Likely [SENSITIVE] — financial | TBD | Classify carefully — may overlap Tier 2/3 household model |
| Secondhand Search Engine | 🔴 NOT LOCATED | Unknown | TBD | TBD | |
| Guitar Projects | 🔴 NOT LOCATED | Unknown | TBD | TBD | |
| Workplace Efficiency Analysis | 🔴 NOT LOCATED | Unknown | TBD | TBD | |
| Personal Finances | 🔴 NOT LOCATED | Unknown | Likely [SENSITIVE] — financial | TBD | "work out any personal finances questions" |
| Make a Power App | 🔴 NOT LOCATED | Unknown | TBD | TBD | |
| Youth Mental Health Case M... | 🔴 NOT LOCATED | Unknown | **[SENSITIVE]** — clinical | `projects/` clinical collection, Clinical Work agent | "big project I'm working on" — high priority once low-stakes pattern proven |
| Investigate Chris's Bank Acc... | 🔴 NOT LOCATED | Unknown | **[SENSITIVE]** — financial/personal, third party | TBD | Third-party subject data — classify very carefully, may need special handling beyond Tier 1-3 model |
| Design | 🔴 NOT LOCATED | Unknown | TBD | TBD | |

*(This list was seeded from a screenshot of the Claude Projects home screen,
8 Aug 2026. Not exhaustive — more projects likely exist below the fold or in
Archived. Update as they're found.)*

## Scattered folder locations (non-Claude-Project files)

| What | Known/suspected location | Status | Target | Notes |
|---|---|---|---|---|
| Household data pipeline | `D:\Data` (unencrypted), snapshot at `C:\HouseholdDataRaw\Data` (encrypted) | 🟡 LOCATED | `~/household-vault/` (Session 10, after Tier-1 quarantine) | See plan §10.4.2 — full inventory already done |
| Cherry Studio exports/configs | `D:\Data\Michael\Cherry Studio\` | 🟡 LOCATED | TBD — audit for reusable content vs. discard | Confirmed to exist (deepinfra_models.md written here 8 Aug 2026) |

## Process for each item

1. **Locate** — find the actual files/folders on disk (may require Michael's input — Claude cannot browse Windows Explorer or search outside mounted/known paths)
2. **Classify** — General / [SENSITIVE] / [IDENTITY], per the Tier model in plan §10.4.1
3. **Decide target:**
   - Low-stakes, reusable → `~/ai-context/projects/<name>/` + RAG collection + agent
   - [SENSITIVE] → same, but scoped to DeepInfra/Anthropic-only agent, no browser/shell
   - [IDENTITY] → folds into the Household DB build (§10.4), not a separate project
   - Abandoned/superseded → mark ⚪ STAYING PUT with reason, do not migrate
4. **Migrate** — copy (never move originals until migration is verified working) knowledge files into `knowledge/`, write `INSTRUCTIONS.md`, build/update the agent, test retrieval
5. **Update this table** — status → 🟢 MIGRATED, note the commit that did it

## Open question
Should third-party subject data (e.g. "Investigate Chris's Bank Accounts") be
migrated into this personal system at all, versus staying as a one-off
Claude.ai conversation? Worth deciding deliberately rather than by default —
raise with Michael before touching that one.
