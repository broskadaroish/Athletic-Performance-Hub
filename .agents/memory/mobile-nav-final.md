---
name: Mobile nav final architecture
description: How the mobile bottom navigation works after the full rewrite — segmented_control, no JS tricks
---

# Mobile bottom nav — final architecture (post-rewrite)

## The rule
Use ONE native `st.segmented_control` widget for the mobile bottom nav.
No hidden trigger buttons. No HTML `onclick`. No `img onerror/onload`. No CSS `:has()` tricks.

## Why
Previous approaches all caused hard failures in Streamlit 1.60 / React:
- `<a href="?nav=...">` → full page reload → new WebSocket → session lost
- `declare_component` → timed out in Replit mTLS proxy
- Hidden `st.button ⬡0–⬡20` + JS click → StreamlitAPIException (writing to widget key after instantiation)
- `<img onerror/onload>` → React Error #231 (Streamlit's React runtime intercepts ALL resource events via capture-phase listeners, even inside dangerouslySetInnerHTML)

## How to apply

### mobile.py
- `render_mobile_nav(current_section)`: renders `st.segmented_control` with key `_mobile_nav_sc`, 5 options, `on_change=_on_nav_change`.
- `_on_nav_change()`: sets `st.session_state["_nav_goto"]` (pending key) or `mobile_mehr_open = True`. Never writes to `nav_section` (owned by sidebar radio).
- `inject_mobile_mehr_overlay(alle_sektionen)`: returns True when `mobile_mehr_open` is True; renders native `st.button` list. Caller calls `render_mobile_nav()` then `st.stop()`.
- `inject_mobile_player_header()`: display-only HTML pill (no onclick). "Wechseln" button removed.

### app.py call pattern
```python
# line ~9948 — before page routing:
if inject_mobile_mehr_overlay(_MAIN_SECTIONS):
    render_mobile_nav(section)   # must appear before st.stop() so nav is always visible
    st.stop()

# line ~10005 — after page routing (normal path):
render_mobile_nav(section)
```

### theme.py CSS
- `[data-testid="stSegmentedControl"]` → `position:fixed; bottom:0` on ≤768px
- Hidden with `display:none` on ≥769px (desktop uses sidebar radio)
- No `.aph-bottom-nav` or `.aph-bn-item` classes (removed)
- `.aph-mehr-header` + `.aph-mehr-title` remain for the Mehr screen header
- `.aph-mehr-overlay`, `.aph-mehr-item`, `.aph-mehr-close` removed (no longer needed)

### Navigation flow
1. User taps option → `on_change` fires → sets `_nav_goto` → auto-rerun
2. app.py line ~9812: `_nav_goto` consumed, written to `nav_section` radio (BEFORE widget instantiation) → no StreamlitAPIException
3. Page renders new section
4. `render_mobile_nav()` shows widget with correct option highlighted

### Key constraint: widget key write timing
`nav_section` is the sidebar `st.radio` key (app.py line ~9836).
NEVER write to `nav_section` after line 9836. Always use `_nav_goto` pending key (applied at line ~9812, before the radio widget).

### Scroll-to-top on section change
`inject_scroll_to_top_if_needed(section)` in mobile.py compares `section` with `_prev_nav_section` in session_state. Only when they differ, a `st.components.v1.html` (height=0) iframe executes JS: `window.parent.document.querySelector('[data-testid="stMain"]').scrollTop = 0`. Called in app.py right after `section = st.radio(...)`. Does NOT fire on normal widget reruns — only real section changes.

### Segmented control CSS target safety
No other page in the app uses `st.segmented_control` → targeting `[data-testid="stSegmentedControl"]` globally is safe.
Selected state uses multiple selectors: `[aria-checked="true"]`, `[aria-pressed="true"]`, `[data-selected="true"]` (Streamlit version may vary).
