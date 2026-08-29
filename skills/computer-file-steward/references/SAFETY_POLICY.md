# SAFETY_POLICY.md — Computer File Steward safety and privacy policy

This skill inherits the build's safety architecture (Self-Improvement Protocol §3)
and applies read-only guarantees on top.

## 1. Credential Rule (absolute)
- Passwords, PINs, MFA seeds, recovery codes, security answers, and private keys
  **never enter this system in any form** — not in chat, RAG, memory, git, or skills.
- The skill may hold a **pointer** ("NRMA login is in Bitwarden, item X") but never the value.
- The skill never reads: `.env`, `.env.save`, `secrets.yaml`, OAuth stores,
  private keys, Bitwarden data, `conversations.json`, household/clinical/legal/
  financial bodies, mailbox bodies, database bodies, uploads, or recovery-package bodies.

## 2. No-mutation guarantee
- READ_ONLY_REVIEW performs no file operations on reviewed content.
- The skill ships no executable that can move, copy, rename, delete, quarantine,
  archive, restore, or purge user assets.
- All proposed actions are `blocked=true` in v1.

## 3. Reparse-point discipline
- Junctions, symlinks, mount points, and `.path` pointer files are **recorded and
  blocked**, never traversed.
- Resolve targets only through safe metadata, never by following.
- Report the limitation rather than copying files around a junction (per ai-workspace AGENTS.md).

## 4. Scope discipline
- Review only the ONE explicit target. Never scan a whole drive, home directory,
  workspace root, current directory, or live-system root.
- WSL/Docker data directories are never scanned.
- External recovery packages are never opened.

## 5. Sensitive-data minimisation
- Prefer metadata + known registries over content.
- Use category detection, not excerpts. Do not output matching content.
- Stop deeper inspection once sensitivity is established.
- Do not hash by default; hash only for a stated verification purpose; never hash
  protected/sensitive content to seek duplicates.

## 6. Level 4 invariants respected
- Does not change routing boundaries (stays general-purpose, never ingests sensitive content).
- Does not add tools to Clinical Work / Household Admin / Paperwork.
- Does not contradict a GOTCHAS entry.
- Does not modify the improver or agent-builder.

## 7. Stop conditions (from the governing task)
Stop safely and write a partial result if:
1. A required operation would read/expose a secret value.
2. The target resolves outside the explicitly supplied directory.
3. A reparse point would need traversing.
4. An existing live/sensitive directory would need modification.
5. Source reports are insufficient to build safe registries.
6. Registry conflicts cannot be represented without guessing.
7. Testing reveals any source mutation.
8. Report generation exposes sensitive content.
9. The build requires broad system access beyond the task.
10. A script attempts a move/rename/copy/delete/archive/restore/Git-write/service mutation.

Never weaken a safety check to make a test pass.
