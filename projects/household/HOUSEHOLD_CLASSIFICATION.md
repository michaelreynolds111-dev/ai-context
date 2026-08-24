# HOUSEHOLD_CLASSIFICATION.md — Appendix D Worksheet **[IDENTITY]**

**Status:** CLASSIFICATION CONFIRMED + F1–F3 CLEARED by Michael (2026-08-18). READY FOR STEP 2 (Goose vault build + copy).
**Last inventory:** 2026-08-18 — `GOOSE_RESULT_CLUSTER6_STEP1B_TREE_INVENTORY.md` (metadata only, tree untouched)
**Rule:** Records **structure only, never values**. Each row names an item/field, its tier, and where it goes. No actual numbers, passwords, or identifiers appear in this file.
**Classification question, in order:** 1) Does it authenticate → Tier 1. 2) Could it be used with other info to authenticate → Tier 1 (over-classify when unsure). 3) Does it identify a person/account → Tier 2. 4) Otherwise → Tier 3.

---

## Michael's confirmed decisions (2026-08-18)

1. **Seddon legal/forensic set → EXCLUDED** from household vault (stays with seddon-source + seddon skills)
2. **Sharon Azzopardi estate → INCLUDED** as own Tier 2 category (documents/estate/)
3. **Bulk photos/media → SKIPPED** — documents-only, no bulk photo indexing
4. **Master Vault registers → INGEST** as reference into documents/
5. **F1–F3 (Michael's credentials) → Bitwarden + delete** (Michael-manual, before Step 2)
6. **F4 (mother-in-law's Chrome Passwords.csv) → protected archive, NOT vault, NOT indexed** — moved to encrypted C: archive folder with pointer recorded in vault
7. All §3 Tier 2/3 rows → confirmed as proposed (Michael: "yes to all I haven't flagged")

---

## Section 1 — Known credential clusters (Tier 1)

| Item / field | Tier | Authenticates? | Current location | Destination | Done |
|---|---|---|---|---|---|
| Chrome passwords (CSV/XLSX + dup) | 1 | Yes | deleted 2026-08-17 | **Bitwarden** | ✅ |
| Passwords.docx (+ dup) | 1 | Yes | deleted 2026-08-17 | **Bitwarden** | ✅ |
| Keep Recovery Codes (.html/.json/.md) | 1 | Yes | deleted 2026-08-17 | **Bitwarden** | ✅ |
| Keep Last.fm Login | 1 | Yes | deleted 2026-08-17 (Michael) | **Bitwarden** | ✅ |
| CogLab Login.docx | 1 | Yes | deleted 2026-08-17 | **Bitwarden** | ✅ |
| Ahpra login.docx | 1 | Yes | deleted 2026-08-17 | **Bitwarden** | ✅ |
| .gateway_token | 1 | Yes | deleted (both drives) | **Bitwarden / retired** | ✅ |
| **F1** goddarnhooplehead Drive Dump/Passwords.docx | 1 | Yes | deleted 2026-08-18 (Michael) | **Bitwarden** | ✅ |
| **F2** goddarnhooplehead Drive Dump/School Pass.docx | 1 | Yes | deleted 2026-08-18 (Michael) | **Bitwarden** | ✅ |
| **F3** MIND Password.docx | 1 | Yes | deleted 2026-08-18 (Michael) | **Bitwarden** | ✅ |
| **F4** Chrome Passwords.csv (mother-in-law's, Mail attachment) | 1 | Yes | `Michael/Mail/attachments/2026-07-22_saztraz1_Passwords_Chrome Passwords.csv` | **Protected archive (NOT vault, NOT indexed)** — Goose moves to `Michael/Drive/Archive/Family/` + pointer in vault | ☐ |
| **F5** Sarah Keep codes | 1 | Yes | `Sarah/Keep/` | **Sarah's Bitwarden** (deferred, non-blocking) | ☐ (deferred) |
| **P5 .eml** credential cluster | 1 | Mixed | `Michael/Mail/messages/` + `Sarah/Mail/messages/` (34,160 files) | **Bitwarden after triage** (parked, non-blocking) | ☐ (parked) |

**P5 note:** Do NOT index any `.eml`. Standing secrets to preserve when triaged: Real-Debrid 2FA, eduPass Temporary Password, Toy Library password reset, ValAi OTP, Patient Portal login code.

---

## Section 2 — Legacy pipeline components (from audit — OFF the index list)

| Item | Tier | Current location | Decision | Done |
|---|---|---|---|---|
| find_pdf_passwords.py | 1 (scanner) | deleted both drives | RETIRE | ✅ |
| read_password_emails.py | 1 (scanner) | deleted both drives | RETIRE | ✅ |
| keep_convert.py | 3 | deleted | RETIRE | ✅ |
| seed_profile.py | 2 (facts extracted) | C: staging + D: | RETIRE after Cluster 6 (data in vault) | ☐ |
| profile.db | 2 | C: + D: | RETIRE after Cluster 6 (data in vault) | ☐ |
| .lancedb | 2 (embeddings) | C: deleted; D: 962MB live | RETIRE after Cluster 6 | ☐ (C: done) |
| archive_gateway.py | 2 | D: | RETIRE after Cluster 6 | ☐ |
| gateway_old/ | 1 (token) | D: removed | RETIRE | ✅ |
| daily_sync.ps1, register_tasks.ps1, embed_batch.py | 2/3 | D: | RETIRE with pipeline | ☐ |
| ArchiveDailySync scheduled task | — | Task Scheduler | disable at Cluster 6 Step 7 | ☐ |
| resource_watchdog.ps1 | 3 | D:\Data | **KEEP running** | — |
| gmail_forward_sync.gs, calendar_sync.gs | 3 | Drive/D: | **KEEP running** | — |
| rclone_sync.ps1, briefing_builder.py, profile_store.py | 3 | D: / vault ref | reference only | — |

---

## Section 3 — Household data to index (Tier 2 / Tier 3) — **CONFIRMED**

> Paths grounded in the 2026-08-18 metadata inventory. Michael has confirmed all tiers as proposed (2026-08-18). Content is copied at Step 2 by Goose.

### 3.1 Vehicles / insurance / leases — **Tier 2** ✅

| Item | Tier | Auth? | Path (staging) | Destination | Done |
|---|---|---|---|---|---|
| Car insurance + novated lease set | 2 | No | `Michael/Drive/Archive/Lease Info/` (Angle Auto settlement, Bingle PDS/schedule/policy, Pacific Motor TLA, Maxxia novated lease) | documents/ | ☐ |
| Tesla / Maxxia claim invoices | 2 | No | `Sarah/Drive/Maxxia claim/` | documents/ | ☐ |

### 3.2 Finance / money / tax — **Tier 2** ✅

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Household finances / spending / bank statements | 2 | No | `Michael/Drive/Archive/Money/` + `Michael/Drive/` (Reynolds_Finances, Reynolds_FullSnapshot, Bank Statement Analysis, Financial Statement, Finances Fact Sheet, Account 8940 pdf/csv, Statement) | documents/ + identifiers/ | ☐ |
| ATO / super / payslips (Sharon estate — see 3.5) | 2 | No | `Michael/Drive/Sharons Computer/ato/`, `.../payslips/`, `.../scanner/` | documents/estate/ | ☐ |

### 3.3 Property / home / NBN — **Tier 2** ✅

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| NBN / property notes | 2 | No | `Michael/Drive/NBN Notes.docx` (property title/rates not found as distinct staged files — facts already in vault identifiers) | documents/ | ☐ |

### 3.4 Health / medical — **Tier 2** ✅

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Health plan / medication / assessments | 2 | No | `Michael/Drive/` (Medication Fact Sheet, ADHD assessments, Bendigo Health, Youth Mental Health) + `Michael/Drive/Archive/Health Plan/` | documents/ + identifiers/ | ☐ |
| Sarah + family medical certs | 2 | No | `Sarah/Drive/La Trobe/Centrelink evidence/` (medical certs, Doctor certificate) | documents/ | ☐ |

### 3.5 Family / estate — **Tier 2** ✅ (Sharon Azzopardi estate = own category, CONFIRMED)

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| **Sharon Azzopardi estate** (death cert, eulogies, funeral options, ATO, payslips, scanner) | 2 | No | `Michael/Drive/` (SCAN Draft Death Certificate AZZOPARDI, Eulogy drafts, Funeral Options) + `Michael/Drive/Sharons Computer/` (photos, payslips/scanner, ATO) | **documents/estate/** | ☐ |
| Mother-in-law family doc (reclassified Tier 3) | 3 | No | `Michael/Drive/Archive/Family/Google Authenticator Screenshot.jpg` | documents/ | ☐ |

### 3.6 Employment / career / work ref — **Tier 2** ✅

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Resumes / covers / career | 2 | No | `Michael/goddarnhooplehead Drive Dump/`, `Michael/mreynoldspsych Drive Dump/`, `Michael/Drive/Archive/Career/`, `Sarah/Drive/Resume stuff/`, `Sarah/Drive/Other/Education Job/` | documents/ | ☐ |

### 3.7 Education / study — **Tier 2/3** ✅

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Michael's study (Masters of Social Work, essays, etc.) | 3 | No | `Michael/Drive/Archive/` (Masters of Social Work, Essay, Exam, School, VPTAS, Sensory) | documents/ | ☐ |
| Sarah's + kids' education | 3 | No | `Sarah/Drive/` (La Trobe, RMIT, Kismet, St Liborius, Centrelink evidence), `Sarah/Drive/NEIS/` | documents/ | ☐ |

### 3.8 Business / side projects — **Tier 3** ✅

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Charcuterie business + NEIS | 3 | No | `Sarah/Drive/Charcuterie Business/`, `Sarah/Drive/NEIS/` | documents/ | ☐ |

### 3.9 Contacts / master register — **Tier 3** ✅ (CONFIRMED: ingest registers)

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Master inventory / contacts / decisions / identity reg | 3 | No | `Michael/Drive/Master Vault/` (01_Master_Inventory, 02_Contacts_Register, 03_Decisions_Log, 00_START_HERE, 04_Identity_and_Docs) | documents/ + renewals.md | ☐ |

### 3.10 LEGAL — Seddon family-law matter — **EXCLUDED** ✅ (CONFIRMED: NOT in household vault)

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Seddon family-law / forensic (affidavits, court finance analysis) | 2 | No | `Michael/Drive/` (Seddon affidavits, lawyer docs, genuine steps, response, etc.) + `Michael/Drive/Court Finance Analysis/` + `Sarah/Drive/Lawyer Paperwork/` | **NOT household vault** — seddon-source / seddon skills | ✅ (excluded) |

### 3.11 Misc/ref + Keep notes — **Tier 3** ✅

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Reference notes / random data / personal ref | 3 | No | `Michael/Drive/` (Scripts I Need, Stuff, Random Data, Data Dump, Minimum Viable Life Plan, MICHAEL-PC, QUICK_REFERENCE) | documents/ | ☐ |
| Non-credential Keep notes | 3 | No | `Michael/Keep/` (~87 notes, excl. code/login) + `Sarah/Keep/` (~92 notes, excl. F5) | documents/ | ☐ |
| Misc dumps (Amplenote, Cherry Studio, Movielens, RYM) | 3 | No | `Michael/Amplenote Dump/`, `Cherry Studio/`, `Movielens Dump/`, `RYM Dump/` | documents/ | ☐ |

### 3.12 Photos / media — **SKIPPED** ✅ (CONFIRMED: documents-only, no bulk photo indexing)

| Item | Tier | Auth? | Path | Destination | Done |
|---|---|---|---|---|---|
| Family photos / media (bulk) | 3 | No | `Sarah/Drive/Backup/` (Camera, Photos, iphone, S6, wedding), Christmas, Tasmania, Other/family tree, Jared; `Michael/Drive/ordered/`, `pics/`, `PXL_*` | **SKIPPED — not indexed** | ✅ (skipped) |

### 3.13 Already in vault — no action

| Item | Tier | Auth? | Current location | Destination | Done |
|---|---|---|---|---|---|
| Profile facts (8) | 2 | No | `~/household-vault/identifiers/profile_facts.md` | identifiers/ | ✅ |

---

## Section 4 — Michael's confirmed decisions (2026-08-18)

| # | Item | Decision | Confirmed |
|---|---|---|---|
| 1 | Seddon legal/forensic set | **EXCLUDED** from household vault | ✅ |
| 2 | Sharon Azzopardi estate | **INCLUDED** as own Tier 2 category (documents/estate/) | ✅ |
| 3 | Bulk photos/media | **SKIPPED** — documents-only, no bulk indexing | ✅ |
| 4 | Master Vault registers | **INGEST** as reference into documents/ | ✅ |
| 5 | F1–F3 (Michael's credentials) | **Bitwarden + delete** (Michael-manual, before Step 2) | ☐ (pending Michael) |
| 6 | F4 (mother-in-law's passwords CSV) | **Protected archive** (NOT vault, NOT indexed) + pointer in vault | ☐ (Goose moves at Step 2) |
| 7 | All §3 Tier 2/3 rows | **Confirmed as proposed** | ✅ |

---

## Section 5 — Completion criteria (before Go to Step 2)

- [x] Michael has confirmed/adjusted every Section 3 tier + each Section 4 open item
- [x] Tier-1 flags F1–F3 moved to Bitwarden + cleartext deleted (Michael confirmed 2026-08-18). F4 → protected archive by Goose at Step 2; F5 deferred; P5 parked — none block vault build
- [x] Every known data item has a row in Section 3
- [ ] Old DB Tier-1 fields confirmed empty incl. backups/exports/sync copies
- [x] Nothing in this worksheet contains an actual value (only structure)

**All gates cleared.** Step 2 (Goose vault build + copy) is READY TO RUN.

---

*End of worksheet. Next: Michael clears F1–F3 → Goose runs Step 2 (vault creation + copy).*
