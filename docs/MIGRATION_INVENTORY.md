# Migration Inventory

Live tracking document for locating and migrating scattered project files,
folders, and Claude Projects into the new LibreChat/ai-context structure.

**Decision (8 Aug 2026):** Individual project migrations are deferred until
after Phase 9 cutover. Migrating projects mid-build fragments momentum and
some projects could each take a full session. More importantly, doing the
migration *using* the new system (rather than Claude Desktop) is itself the
real-world proof that it is replacing Claude Pro -- making it the natural
Phase 9 / parallel-run period work.

**Phase 6 scope (current):** prove the RAG + agent + INSTRUCTIONS.md pattern
works on one low-stakes project. New Build (Stash) satisfies that -- done.

**Post-cutover scope:** migrate remaining projects one at a time using
LibreChat itself, updating this inventory as each one completes.

---

Companion to Appendix A of BACKUP_AI_MASTER_BUILD_PLAN.md (the static
worksheet template) -- this file is the actual working inventory.

## Status legend
- NOT LOCATED -- exists but current file location on disk is unknown
- LOCATED -- found on disk, not yet classified or migrated
- MIGRATED -- files in ai-context/, RAG collection built, agent built
- DEFERRED -- deliberately deferred to post-cutover migration sessions
- STAYING PUT -- deliberately not migrated (reason given)

## Claude Projects inventory

| Project name | Status | Sensitivity | Notes |
|---|---|---|---|
| Building AI System | MIGRATED N/A | General | Is the infrastructure itself |
| New Build (Stash/recommendation system) | KNOWLEDGE-ONLY | General | Agent Stash Ops built Phase 6 -- proves the pattern. Live-access upgrade is Phase 7 Goose work. Location: C:\torbox-system\stash-torbox-bridge\ Commit: bf95d2e |
| Paperwork | DEFERRED | TBD | Migrate post-cutover using LibreChat |
| Achriom | DEFERRED | TBD | Migrate post-cutover |
| Ron Admin | DEFERRED | TBD | Migrate post-cutover |
| RateYourMusic Connector | DEFERRED | TBD | Migrate post-cutover |
| Tax Return | DEFERRED | SENSITIVE -- financial | Classify before migrating |
| Secondhand Search Engine | DEFERRED | TBD | Migrate post-cutover |
| Guitar Projects | DEFERRED | TBD | Migrate post-cutover |
| Workplace Efficiency Analysis | DEFERRED | TBD | Migrate post-cutover |
| Personal Finances | DEFERRED | SENSITIVE -- financial | Classify before migrating |
| Make a Power App | DEFERRED | TBD | Migrate post-cutover |
| Youth Mental Health Case M... | DEFERRED | SENSITIVE -- clinical | High priority once system proven. Local embeddings + DeepInfra/Anthropic only. |
| Investigate Chris Bank Acc... | DEFERRED | SENSITIVE -- third-party financial | Decide whether this belongs in a personal system at all before touching it |
| Design | DEFERRED | TBD | Migrate post-cutover |

## Scattered folder locations

| What | Location | Status | Notes |
|---|---|---|---|
| Household data pipeline | D:\Data (live), C:\HouseholdDataRaw\Data (snapshot) | LOCATED | Tier-1 quarantine first -- Session 10 |
| Cherry Studio exports/configs | D:\Data\Michael\Cherry Studio\ | LOCATED | Audit at Session 10 |
| C:\torbox-system non-bridge files | C:\torbox-system\ | LOCATED | Diagnostic scratch scripts -- STAYING PUT, not worth migrating |

## Post-cutover migration process

For each DEFERRED item, after cutover, using LibreChat (not Claude Desktop):
1. Open the Claude Project -- copy Instructions + list knowledge files
2. Locate associated files on disk (Michaels input needed per project)
3. Classify sensitivity
4. Write INSTRUCTIONS.md, copy knowledge files, create RAG collection in LibreChat, build agent
5. Test RAG retrieval with citations
6. Update this table to MIGRATED with commit SHA

## Open question
Should Investigate Chris Bank Accounts be migrated into this personal system
at all? Raise and decide before touching it.
