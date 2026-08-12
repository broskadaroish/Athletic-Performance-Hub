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

def handle_mobile_nav_params() -> None:
    """
    Read ?player_id= query param; update session state without page reload.
    ?nav= is kept as legacy deep-link fallback (sets _nav_goto).
    Must be called BEFORE nav_section widget is instantiated.
    """
    try:
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


# ── Bottom navigation bar ─────────────────────────────────────────────────────

def render_mobile_nav(current_section: str) -> None:
    """
    Render the mobile bottom navigation as a single st.segmented_control.

    Layout
    ──────
    The widget appears position:fixed at the bottom on ≤768px via CSS
    declared in theme.py ([data-testid="stSegmentedControl"]).
    On desktop (≥769px) the widget is hidden entirely (display:none).

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
    On player-specific pages show a compact player info pill (mobile only).
    Hidden on desktop via CSS (.aph-mph { display:none } / @media override).
    Display-only: no onclick events, no navigation buttons.
    Users can tap '👤 Spieler' in the bottom nav to switch players.
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
