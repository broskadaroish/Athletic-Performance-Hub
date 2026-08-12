"""
Mobile-responsive helpers for Athletic Performance Hub.

Bottom navigation uses ONE native st.segmented_control widget.
No hidden trigger buttons, no HTML/JS bridges, no event-handler tricks,
no CSS :has() for hiding buttons.

Architecture:
  render_mobile_nav()          — single st.segmented_control, 5 options,
                                  position:fixed bottom via CSS in theme.py
  inject_mobile_mehr_overlay() — native st.button list for non-primary sections
  inject_mobile_player_header()— compact player pill (HTML, display-only)
  inject_mobile_player_selector()— native HTML <select> for player switching
  handle_mobile_nav_params()   — reads ?player_id= query param
"""
import streamlit as st

# ── Bottom nav options (5 items, fixed set) ───────────────────────────────────
_BOT_NAV_OPTS = ["🏠 Start", "👤 Spieler", "🧪 Tests", "📅 Training", "⋯ Mehr"]

# Maps mobile nav label → full section key used by desktop nav_section radio.
# None = "⋯ Mehr" (opens the Mehr overlay instead of navigating).
_BOT_NAV_TO_SECTION: dict[str, str | None] = {
    "🏠 Start":    "🏠  Startseite",
    "👤 Spieler":  "👤  Spieler",
    "🧪 Tests":    "🔬  Diagnostik",
    "📅 Training": "📅  Training",
    "⋯ Mehr":      None,
}

# Reverse lookup: primary section key → mobile nav label
_SECTION_TO_BOT_NAV: dict[str, str] = {
    v: k for k, v in _BOT_NAV_TO_SECTION.items() if v is not None
}

# Primary sections shown directly in the bottom nav (excluded from Mehr list)
_BOT_NAV_PRIMARY = frozenset(_SECTION_TO_BOT_NAV.keys())

# Sections where the active-player header pill is relevant
_PLAYER_SECTIONS = frozenset({
    "🔬  Diagnostik",
    "📅  Training",
    "📈  Entwicklung",
    "⚖️  Vergleich",
    "📄  Dokumente",
})


# ── Query-param navigation handler ───────────────────────────────────────────

def inject_scroll_to_top_if_needed(section: str) -> None:
    """
    Scroll to the top of the page only when the main section actually changes.

    Triggered by: mobile nav tap, desktop sidebar click — any real section change.
    NOT triggered by: form edits, widget changes, saves, reruns within a page.

    Implementation: st.components.v1.html (0-height iframe) executes JS that
    scrolls Streamlit's main scroll container in the parent window.
    The scroll container is [data-testid="stMain"] (confirmed from Streamlit DOM).

    Session key _prev_nav_section tracks the last rendered section.
    On first render (prev = None) no scroll is injected.
    """
    import streamlit.components.v1 as components

    prev = st.session_state.get("_prev_nav_section")
    st.session_state["_prev_nav_section"] = section

    if prev is not None and prev != section:
        components.html(
            "<script>"
            "try {"
            "  var p = window.parent;"
            "  var el = p.document.querySelector('[data-testid=\"stMain\"]');"
            "  if (el) { el.scrollTop = 0; el.scrollLeft = 0; }"
            "  else { p.scrollTo(0, 0); p.document.documentElement.scrollTop = 0; }"
            "} catch(e) {}"
            "</script>",
            height=0,
            scrolling=False,
        )


def handle_mobile_nav_params() -> None:
    """
    Read ?player_id= query param; update session state without page reload.
    ?nav= is kept as legacy deep-link fallback (sets _nav_goto).
    ?_sw= is used by the screen-width JS detector to persist viewport width.
    Must be called BEFORE nav_section widget is instantiated.
    """
    try:
        # ── Screen-width detection result (set by _inject_screen_width_detect JS) ──
        sw_val = st.query_params.get("_sw", "")
        if sw_val:
            try:
                st.session_state["_screen_width"] = int(sw_val)
            except (ValueError, TypeError):
                st.session_state["_screen_width"] = 1024
            try:
                del st.query_params["_sw"]
            except Exception:
                pass
            # Continue — other params may also be present

        player_id_val = st.query_params.get("player_id", "")
        if player_id_val:
            st.query_params.clear()
            try:
                st.session_state["global_player_id"] = int(player_id_val)
                st.session_state["mobile_mehr_open"] = False
            except (ValueError, TypeError):
                pass
            st.rerun()

        nav_val = st.query_params.get("nav", "")
        if not nav_val:
            return
        st.query_params.clear()
        if nav_val == "__mehr__":
            st.session_state["mobile_mehr_open"] = True
        elif nav_val == "__close_mehr__":
            st.session_state["mobile_mehr_open"] = False
        elif nav_val == "__logout__":
            st.session_state["__mobile_logout_request__"] = True
        else:
            st.session_state["_nav_goto"] = nav_val
            st.session_state["mobile_mehr_open"] = False
        st.rerun()
    except Exception:
        pass


def _inject_screen_width_detect() -> None:
    """
    Inject a JS snippet (once per session) that detects window.innerWidth and
    writes it to the ?_sw= query param, triggering a page reload.

    On the reload handle_mobile_nav_params() reads ?_sw=, stores the value in
    st.session_state["_screen_width"], and clears the param.
    After that render_mobile_nav() uses the cached value as a Python-level guard
    so the widget is never instantiated on desktop (> 768 px).

    The one-time reload is harmless: authentication uses cookie-based persistence
    and survives a browser location.replace().
    """
    if "_screen_width" in st.session_state:
        return  # already detected — no further injection needed
    import streamlit.components.v1 as components
    components.html(
        "<script>"
        "try {"
        "  var w = Math.round(window.parent.innerWidth || window.innerWidth || 0);"
        "  if (w > 0) {"
        "    var u = new URL(window.parent.location.href);"
        "    u.searchParams.set('_sw', String(w));"
        "    window.parent.location.replace(u.toString());"
        "  }"
        "} catch(e) {}"
        "</script>",
        height=0,
        scrolling=False,
    )


# ── Bottom navigation bar ─────────────────────────────────────────────────────

def render_mobile_nav(current_section: str) -> None:
    """
    Render the mobile bottom navigation as a single st.segmented_control.

    Layout
    ──────
    The widget appears position:fixed at the bottom on ≤768px via CSS
    declared in theme.py ([data-testid="stSegmentedControl"]).
    On desktop (≥769px) the widget is NOT rendered (Python-level guard) after
    the first-load screen-width detection rerun. CSS provides an additional
    hide fallback for the one initial render on desktop before detection fires.

    Screen-width detection
    ──────────────────────
    On the very first render, _inject_screen_width_detect() injects a JS snippet
    that writes window.innerWidth to ?_sw= and triggers a location.replace()
    reload. handle_mobile_nav_params() (called before the nav radio widget in
    app.py) reads ?_sw= on that reload and stores it in
    st.session_state["_screen_width"]. From then on, render_mobile_nav() returns
    immediately when _screen_width > 768, so the widget is never instantiated on
    desktop. The one-time reload is harmless; cookie-based auth survives it.

    Navigation flow
    ───────────────
    1. User taps an option → on_change callback fires with the new value.
    2. Callback sets st.session_state["_nav_goto"] (the existing pending-key
       consumed at app.py line ~9812, BEFORE the nav_section radio widget).
       This avoids StreamlitAPIException when writing to a widget key.
    3. Streamlit auto-reruns after the widget change (no explicit st.rerun()
       needed in the callback).
    4. On the next rerun, _nav_goto is applied → section changes.

    "⋯ Mehr"
    ────────
    Setting "⋯ Mehr" sets mobile_mehr_open = True.
    In app.py, inject_mobile_mehr_overlay() detects this and renders a
    native Streamlit Mehr menu (st.button list) → caller calls st.stop().
    render_mobile_nav() is called before st.stop() so the nav is always visible.

    No hidden buttons. No JS event tricks. No HTML bridges.
    """
    # ── Screen-width guard: inject detector once; skip render on desktop ──────
    _inject_screen_width_detect()
    _sw = st.session_state.get("_screen_width", 0)
    if _sw > 768:
        return  # Desktop detected — sidebar handles navigation

    def _on_nav_change() -> None:
        choice = st.session_state.get("_mobile_nav_sc")
        if choice is None:
            return
        sec = _BOT_NAV_TO_SECTION.get(choice)
        if sec is None:          # "⋯ Mehr" selected
            st.session_state["mobile_mehr_open"] = True
        else:
            st.session_state["_nav_goto"] = sec
            st.session_state["mobile_mehr_open"] = False

    mehr_open = bool(st.session_state.get("mobile_mehr_open"))
    if mehr_open or current_section not in _BOT_NAV_PRIMARY:
        # Non-primary sections (e.g. Entwicklung, Vergleich) accessed via Mehr
        # → highlight "⋯ Mehr" in the nav bar (standard mobile UX)
        current_default = "⋯ Mehr"
    else:
        current_default = _SECTION_TO_BOT_NAV.get(current_section, "🏠 Start")

    st.segmented_control(
        label="Navigation",
        options=_BOT_NAV_OPTS,
        default=current_default,
        key="_mobile_nav_sc",
        on_change=_on_nav_change,
        label_visibility="collapsed",
    )


# ── "Mehr" full-screen navigation menu ───────────────────────────────────────

def inject_mobile_mehr_overlay(alle_sektionen: list[str]) -> bool:
    """
    When mobile_mehr_open is True, render the "Mehr" navigation screen
    using native Streamlit st.button elements (no HTML onclick, no CSS overlay).

    Returns True when the Mehr screen is active.

    Caller (app.py) pattern:
        if inject_mobile_mehr_overlay(_MAIN_SECTIONS):
            render_mobile_nav(section)   # show nav bar even on Mehr screen
            st.stop()                    # skip main page content

    Button clicks set _nav_goto + close Mehr, then rerun.
    The _nav_goto pending key is consumed at app.py line ~9812 (before the
    nav_section widget) → no StreamlitAPIException.
    """
    if not st.session_state.get("mobile_mehr_open"):
        return False

    # Header (HTML for styling, no interactive elements)
    st.markdown(
        '<div class="aph-mehr-header" translate="no">'
        '<span class="aph-mehr-title">Weitere Bereiche</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Non-primary section buttons — pure native st.button
    for sek in alle_sektionen:
        sek_s = sek.strip()
        if sek_s in _BOT_NAV_PRIMARY:
            continue
        if st.button(
            sek_s,
            key=f"_mob_mehr_{sek_s}",
            width="stretch",
        ):
            st.session_state["_nav_goto"] = sek_s
            st.session_state["mobile_mehr_open"] = False
            st.rerun()

    st.divider()

    if st.button(
        "🚪 Abmelden",
        key="_mob_mehr_logout",
        width="stretch",
        type="secondary",
    ):
        st.session_state["__mobile_logout_request__"] = True
        st.session_state["mobile_mehr_open"] = False
        st.rerun()

    return True


# ── Mobile active-player header pill ─────────────────────────────────────────

def inject_mobile_player_header(player: dict | None, section: str) -> None:
    """
    On player-specific pages show a compact player info pill + a native
    "Spieler wechseln" button (both mobile-only, hidden on ≥769px via CSS).

    The player pill is hidden on desktop via .aph-mph { display:none }.
    The switch button is hidden on desktop via the .aph-mob-switch-marker
    adjacent-sibling rule in theme.py:
        @media (min-width: 769px) {
            .aph-mob-switch-marker + div { display: none !important; }
        }

    Button click: sets _nav_goto = "👤  Spieler" → pending key consumed at
    app.py line ~9812, before the nav_section widget → no StreamlitAPIException.
    """
    if not player or section not in _PLAYER_SECTIONS:
        return
    name = player.get("name") or "—"
    pos  = player.get("hauptposition") or player.get("position") or ""
    team = player.get("mannschaft") or ""
    sub  = " · ".join(x for x in [pos, team] if x) or "Kein Team"
    st.markdown(
        f'<div class="aph-mph" translate="no">'
        f'<span class="aph-mph-icon">👤</span>'
        f'<div class="aph-mph-info">'
        f'<div class="aph-mph-name">{name}</div>'
        f'<div class="aph-mph-sub">{sub}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # Marker div — the adjacent-sibling CSS rule in theme.py hides the
    # following button on desktop (≥769px) without affecting other elements.
    st.markdown(
        '<div class="aph-mob-switch-marker"></div>',
        unsafe_allow_html=True,
    )
    if st.button(
        "👤 Spieler wechseln",
        key=f"_mob_switch_{section}",
    ):
        st.session_state["_nav_goto"] = "👤  Spieler"
        st.rerun()


# ── Mobile inline player selector ────────────────────────────────────────────

def inject_mobile_player_selector(alle_spieler: list | None, current_pid) -> None:
    """
    Mobile-only player switcher — native HTML <select> that navigates via
    ?player_id= query param (read by handle_mobile_nav_params()).
    Hidden on desktop (≥769px) via CSS .aph-mob-sel-wrap { display:none }.
    Does nothing when fewer than 2 players are available.
    """
    if not alle_spieler or len(alle_spieler) < 2:
        return

    opts: list[str] = []
    for p in alle_spieler:
        pid     = p["id"]
        name    = (
            p.get("name") or
            f"{p.get('vorname', '')} {p.get('nachname', '')}".strip() or
            f"Spieler #{pid}"
        )
        mannsch = p.get("mannschaft") or ""
        display = f"{name} – {mannsch}" if mannsch else name
        sel     = " selected" if pid == current_pid else ""
        opts.append(f'<option value="{pid}"{sel}>{display}</option>')

    st.markdown(
        f'<div class="aph-mob-sel-wrap">'
        f'<div class="aph-mob-sel-label">👤 Spieler wechseln</div>'
        f'<select class="aph-mob-sel" '
        f'onchange="window.location.href=\'?player_id=\''
        f'+encodeURIComponent(this.value)">'
        + "\n".join(opts) +
        f'</select>'
        f'</div>',
        unsafe_allow_html=True,
    )
