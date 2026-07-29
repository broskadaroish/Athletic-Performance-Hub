---
name: App nav widget quirk
description: Pre-existing Streamlit warning about empty radio labels in the navigation sidebar
---

## Observation
On every app start, Streamlit logs repeated warnings:
```
`label` got an empty value. This is discouraged for accessibility reasons...
  File "app.py", line ~2507, in <module>
    section = st.radio(
```

## Root cause
The sidebar navigation uses `st.radio` with `label=""` and `label_visibility="collapsed"` — an existing pattern in `app.py` before any help-system changes.

**Why it's not a bug to fix:** These are cosmetic accessibility warnings, not errors. The app works correctly. Fixing them would require refactoring the entire navigation widget (label must be non-empty string per Streamlit's own guidance, but `label_visibility="collapsed"` suppresses display).

**How to apply:** When reviewing logs, ignore these radio warnings. Only act if you see `ERROR` or `Exception` lines.
