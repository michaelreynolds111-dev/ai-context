# BUILD PLAN — DEVIATIONS LOG

Append this to `BACKUP_AI_MASTER_BUILD_PLAN.md` (e.g. as a new section 19, or
fold into the revision history). It records where execution diverged from the
spine. **None of these change a locked design decision (§2)** — they are
implementation details discovered during the build.

---

## Phase 0 — Source of truth repo (executed 5 Aug 2026)

### D0.1 — gitleaks installed user-local, not system-wide
**Plan (§4.4a):** "Install gitleaks ... as a pre-commit hook."
**Deviation:** installed to `~/.local/bin/gitleaks` (user-writable) rather than
`/usr/local/bin`, to avoid `sudo` entirely.
**Consequence — load-bearing for anyone re-deriving this:** git hooks run in a
minimal **non-login** shell that does **not** source `~/.bashrc`, so `~/.local/bin`
is not on PATH inside the hook. The pre-commit hook therefore contains an explicit
`export PATH="$HOME/.local/bin:$PATH"` line. Without it the hook fails
"gitleaks not found" and — because it's `set -euo pipefail` — still blocks the
commit, but for the wrong reason (masking real scan results). First exit-test run
hit exactly this; fixed and re-passed.

### D0.2 — gitleaks version + project status
**Plan (§4.4a):** tool unversioned ("gitleaks or git-secrets").
**Actual:** gitleaks **8.30.1** (latest stable, released 21 Mar 2026), verified
by live search before install.
**New fact for the change-trigger list:** gitleaks is now **feature-complete** —
the original author (Zach Rice) moved to Aikido Security and launched a successor,
**Betterleaks**, Feb 2026. gitleaks receives security patches only. Not a problem
now (the tool works and migration is designed to be frictionless), but it belongs
on the §18 change-trigger radar: *if gitleaks stops receiving even security
patches, or a rule-set gap appears for AU identifiers, re-evaluate Betterleaks.*

### D0.3 — custom AU identifier rules are heuristic, not checksum-validated
**Plan (§4.4a):** "Add a custom rule set for Australian identifiers — TFN,
Medicare, passport patterns."
**Implementation note:** `.gitleaks.toml` extends the default rule set
(`useDefault = true`) and adds four regex rules: `au-tfn`, `au-medicare`,
`au-passport`, `au-drivers-licence`. These are **pattern-shaped heuristics**, not
checksum-validated (no TFN/Medicare check-digit logic). This is intentional and
matches the plan's own risk posture: false positives are cheap (a blocked commit),
false negatives are not (a committed identifier). Expect the TFN/Medicare rules in
particular to fire on innocent 9–11 digit strings. When they do, add a **scoped
allowlist entry** to `.gitleaks.toml` — never disable the hook.

### D0.4 — first real SKILL.md is `session-close`
**Plan (§4.5 exit test):** "At least one real SKILL.md written and committed."
**Actual:** wrote `skills/session-close/SKILL.md` (generic port of the
`robot-session-close` pattern named in §8.3). Satisfies the exit test with a skill
that's actually on the port list, rather than a throwaway.

### D0.5 — default branch kept as `master`
**Plan:** silent on branch naming.
**Decision:** left as git's default `master`. Rename was free before the first
commit but wasn't done; post-commit it needs a coordinated local+remote rename for
no functional gain on a single-user private repo. Recorded so it's a decision, not
an oversight.

### D0.6 — PAT persistence
**Plan (§3.3, §4.5):** "HTTPS + PAT ... goes directly into the git credential
helper inside Ubuntu."
**Actual:** used `credential.helper store` → token at `~/.git-credentials`,
perms `600`. Plaintext-at-rest, acceptable on a single-user, full-disk-encrypted
(BitLocker, §14.5) box. Noted alternative: `credential.helper cache` (timed,
in-memory) if plaintext persistence is ever unwanted.

### D0.7 — PROCESS FAILURE: PAT exposed in chat (security follow-up)
**What happened:** during troubleshooting of an invisible-password-prompt issue in
PowerShell 7, the working method became "echo the token into ~/.git-credentials on
a visible command line." The token was pasted into the **chat transcript** in the
process, exposing it in plaintext.
**Why it matters:** this is precisely the class of event the credential rule exists
to prevent — a live credential landing somewhere it shouldn't. The push succeeded
and the repo is fine; the **token** is burned.
**Required remediation (tracked in BUILD_STATE.md blockers):** revoke the exposed
PAT at https://github.com/settings/tokens, issue a fresh classic token (repo
scope), update `~/.git-credentials`.
**Status: RESOLVED 6 Aug 2026** — original token revoked, fresh classic token
(repo scope) issued and stored via `credential.helper store`. See BUILD_STATE.md
decisions log.
**Lesson for future phases — carry forward:** provider API keys (DeepInfra,
OpenRouter, Anthropic) in Phase 1–2 must be entered **directly into `.env` inside
Ubuntu by Michael**, never surfaced in chat, never echoed on a command line whose
output returns to chat. If a credential ever needs to reach a file, it goes there
by hand in a terminal Claude does not read — the same boundary that applies to
household Tier-1 material applies to build credentials.

---

## Suggested §18 change-trigger addition

> **(5 Aug 2026)** gitleaks entered security-patch-only maintenance (successor:
> Betterleaks). Re-evaluate the secret scanner if security patches lapse or an AU
> identifier rule-set gap emerges. Migration is designed to be low-friction.
