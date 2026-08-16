# BUILD_STATE_EDIT_SCRIPT_SUPPLEMENT_TEMPLATE

**Source:** state-update-guard skill.
**Purpose:** Bulky section-replacement content that would push the main
BUILD_STATE_EDIT_SCRIPT.md over ~3000 tokens. The main edit script references
this file; Goose reads both and applies the section_replace from here.

---

## When to use this file

Write this companion file ONLY when a `section_replace` in the main edit script
would exceed ~2000 tokens. The main script's `section_replace` block should
contain a short pointer:

```
section: |
  ## NEXT STEP
content: |
  See BUILD_STATE_EDIT_SCRIPT_SUPPLEMENT.md — section_replace for ## NEXT STEP
```

Then write the full replacement content here.

---

## Format

Same as the main `section_replace` block:

```
## section_replace
section: |
  ## NEXT STEP
content: |
  **<full replacement content here>**
```

---

*End of companion template.*
