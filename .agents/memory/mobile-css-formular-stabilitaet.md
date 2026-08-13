---
name: Mobile CSS + Formular-Stabilität
description: Root causes and fixes for dark-theme form readability on mobile and post-login navigation resets
---

## CSS — Formular-Labels dunkel / Selectbox fast weiß

**Root cause:** 
- `label`-Farbe nur für Sidebar gesetzt (`[data-testid="stSidebarContent"] label`), nicht für Main-Content.
- Selectbox-CSS zielte auf `[data-testid="stSelectbox"] select` (native `<select>`) — Streamlit nutzt aber BaseWeb-Komponenten (`[data-baseweb="select"]`), kein natives select im DOM → CSS griff nie.
- iOS Safari überschreibt `color` mit eigenem Wert; `-webkit-text-fill-color` war nicht gesetzt → Inputs erschienen mit dunklem Text auf Mobile.

**Fix:** In `theme.py` ersetzt die bisherige 9-Zeilen-Input-Regel jetzt einen umfangreichen Block, der abdeckt:
- Alle Widget-Label-Selektoren im Main-Content
- `[data-baseweb="select"]`, `[data-baseweb="input"]`, `[data-baseweb="textarea"]`, `[data-baseweb="menu"]`, `[data-baseweb="popover"]`
- `-webkit-text-fill-color` auf jedem input/textarea (iOS Safari Fix)
- `::placeholder` und `::-webkit-input-placeholder` pro Widget-Typ
- NumberInput +/- Buttons, MultiSelect Tags, File-Uploader Hinweistexte

**Why:** BaseWeb-Komponenten rendern kein natives `<select>`. Alle früheren Selectbox-Regeln waren ohne Wirkung. Der Selector `[data-baseweb="select"] > div > div > div` erreicht den Value-Text ohne fragile class-name-Hashes.

---

## Login doppelt nötig / Startseiten-Sprung nach Login auf Mobile

**Root cause:**
`render_mobile_nav()` → `_inject_screen_width_detect()` wurde erst NACH dem Login-Gate aufgerufen (tief im Main-App-Bereich). Auf dem ersten echten Render nach erfolgreichem Login war `_screen_width` noch nicht in session_state → JS schrieb `?_sw=` via `location.replace()` → komplett neue Streamlit-Session → `nav_section` weg → Default "🏠 Startseite" + CookieController brauchte 2 Reruns für Session-Restore.

**Fix:** `detect_screen_width()` (öffentlicher Wrapper um `_inject_screen_width_detect`) wird in `app.py` aufgerufen **bevor** die Login-Gate-Prüfung (`if "user" not in st.session_state`). So wird die Breite schon auf der Login-Seite ermittelt; wenn der Nutzer sich danach anmeldet, ist kein Reload mehr nötig.

**How to apply:** Jede zukünftige Funktion, die auf Mobile-spezifisches Rendering angewiesen ist, muss sicherstellen, dass `detect_screen_width()` vor dem Login-Gate läuft — nicht innerhalb der Main-App.

---

## Mobile Spieler-Wechsel erhält jetzt die aktive Sektion

`inject_mobile_player_selector()` nutzt `window.location.href=?player_id=...` (voller Browser-Reload) → nav_section war nach dem Reload verloren.

**Fix:** 
- Neuer Parameter `current_section` in `inject_mobile_player_selector()`
- URL wird zu `?player_id=X&nav=<encoded_section>` erweitert
- `handle_mobile_nav_params()` liest `nav` bereits beim `player_id`-Branch (vor `st.query_params.clear()`) und setzt `_nav_goto`
- In `app.py` wird `section` als drittes Argument übergeben
