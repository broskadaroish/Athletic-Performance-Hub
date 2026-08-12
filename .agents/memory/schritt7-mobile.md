---
name: SCHRITT 7 Mobile Responsive Design
description: Architecture of mobile responsive layer added in SCHRITT 7; key decisions and integration points.
---

## What was built

New file `artifacts/athletik/mobile.py` — all mobile helpers:
- `handle_mobile_nav_params()` — reads `?nav=` query params, must be called BEFORE the `nav_section` radio widget in `with st.sidebar:` (around line 9714 in app.py). Calls `st.rerun()` when param found.
- `inject_mobile_nav(current_section)` — fixed bottom nav bar, visible only ≤768px. Called at very end of app.py (after all route dispatch).
- `inject_mobile_player_header(player, section)` — compact player pill, hidden on desktop. Called inside route dispatch for Diagnostik, Training, Entwicklung, Vergleich, Dokumente sections.
- `inject_mobile_mehr_overlay(alle_sektionen)` — position:fixed full-screen overlay for "Mehr" sections. Called after `_check_save_ok()`, before route dispatch.

`artifacts/athletik/theme.py` — added @media CSS block (appended before closing `</style>`) covering:
- Mobile ≤768px: sidebar hidden, bottom padding 80px, compact headers, better contrast, touch targets
- Tablet 769–1024px: narrower sidebar
- Bottom nav styles (.aph-bottom-nav, .aph-bn-item, etc.)
- Player header styles (.aph-mph, .aph-mph-*)
- Mehr overlay styles (.aph-mehr-overlay, .aph-mehr-item, etc.)

`artifacts/athletik/app.py` changes:
- Import `from mobile import ...` added after line 28 (theme import)
- `handle_mobile_nav_params()` called inside `with st.sidebar:` before `_nav_goto` handling
- Mobile logout block: checks `st.session_state.pop("__mobile_logout_request__", False)` inside sidebar before the Abmelden button
- Route dispatch: `inject_mobile_mehr_overlay(_MAIN_SECTIONS)` after `_check_save_ok()`; `_mob_player()` helper; `inject_mobile_player_header()` on 5 sections
- `inject_mobile_nav(section)` at very last line of file

## Navigation mechanism
- Bottom nav items are `<a href="?nav=URL_ENCODED_SECTION_KEY">` links
- `handle_mobile_nav_params()` reads `st.query_params["nav"]`, clears it, updates session state, calls `st.rerun()`
- Special keys: `__mehr__`, `__close_mehr__`, `__logout__`, `__close_mehr__`
- Section keys use double spaces (e.g. "🏠  Startseite") — must match exactly

**Why:** Streamlit's `st.radio` widget reads `key="nav_section"` from session state. Setting `st.session_state["nav_section"]` before the widget renders changes the active section. Query params survive page reloads and work with the existing cookie-based session persistence.

## What was NOT changed
- No auth logic, no session logic, no business logic
- No DB changes
- No layout="wide" change (still wide)
- All pre-existing warnings (empty label, use_container_width) are pre-existing, not introduced by SCHRITT 7
