# BUILD_STATE_EDIT_SCRIPT_TEMPLATE

<!-- 
  This template defines the edit-script format for BUILD_STATE.md updates.
  LibreChat writes this file to ~/agent-workdir/BUILD_STATE_EDIT_SCRIPT.md.
  Goose reads it and applies each edit to the live ~/ai-context/BUILD_STATE.md
  using find-and-replace (the `edit` tool).

  RULES:
  - Copy `old`/`after` text EXACTLY from the live file read in step 1.
  - Goose validates every `old`/`after` string — if it doesn't match, Goose STOPS.
  - Use the minimal edit type needed (header for header lines, table_row for
    table rows, field_update for individual lines, event_log_append for log
    entries, section_replace for entire sections).
  - Do NOT include the full file — only the edits.
  - Omit any edit type that has no changes this session.
-->

# BUILD_STATE_EDIT_SCRIPT

## header
<!-- Replace the header line (last updated + current sub-step). -->
old: |
  **Last updated:** <old date and text from live file>
  **Current sub-step:** <old sub-step from live file>
new: |
  **Last updated:** <new date and summary>
  **Current sub-step:** <new sub-step>

## table_row
<!-- Insert a new row in the phase status table after the specified anchor row. -->
<!-- Omit this section if no new table rows are needed. -->
after: |
  | **9a — Remote mobile access + STT** | **✅ PASSED** | Mobile HTTPS + browser-native STT confirmed | 11 Aug 2026 |
add: |
  | **9B — MongoDB durability + backup** | **✅ PASSED** | Named volume + daily mongodump + restore drill | 11 Aug 2026 |

## field_update
<!-- Find/replace a specific line or field. Use for H3/H4 status updates, -->
<!-- environment fact changes, etc. -->
<!-- Omit this section if no field updates are needed. -->
old: |
  - H3: Password manager — UNDECIDED
new: |
  - H3: Password manager — **RESOLVED: Bitwarden** (decided 15 Aug 2026)

## event_log_append
<!-- Append lines to the "Session event log (append-only)" section. -->
<!-- Each line follows the SESSION_EVENT_LOG_TEMPLATE format. -->
<!-- Omit this section if no new event log entries. -->
- <date> [<phase_label>] [DONE] <one-line claim> — evidence: <source>
- <date> [<phase_label>] [DISCUSSED] <one-line claim> — evidence: user statement (unverified). Verify: <verification step>
- <date> [<phase_label>] [PLANNED] <one-line claim> — evidence: none yet

## section_replace
<!-- Replace an entire section (from the heading to the next ## heading). -->
<!-- Use for NEXT STEP updates and similar wholesale section changes. -->
<!-- Omit this section if no section replacements are needed. -->
section: |
  ## NEXT STEP
content: |
  **<new next step content here>**

  **After this completes:** <what comes next>
