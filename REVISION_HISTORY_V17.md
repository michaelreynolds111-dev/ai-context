# Staged revision-history entry for the master build plan (v1.6 → v1.7)

**Status:** STAGED — draft for review. To be merged into the "Revision
history" table near the top of `BACKUP_AI_MASTER_BUILD_PLAN.md` when promoted.

---

| 1.7 | 15 Aug 2026 | **Phase 9b — Remote Goose execution via SSH + Termius + tmux added (§13b).** Sibling to §13a's web-UI mobile access: extends remote access to the *execution* channel so Goose can be driven from the phone. Uses the same private tailnet (Tailscale, never Funnel/public), WSL2 `openssh-server` on a distinct port with key-only auth, tmux for session persistence, and Termius for the phone terminal. SSH key material is treated as Tier-1 (Michael-manual setup, never in the build). Rationale: closes the gap where a plan written in LibreChat requires sitting at the desktop to execute in Goose. No change to LibreChat access (§13a unchanged), routing, or the credential rule. |
