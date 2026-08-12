"""
Mobile-responsive helpers for Athletic Performance Hub.

Provides:
  - handle_mobile_nav_params()    — reads ?nav= / ?player_id= query params,
                                    must be called before the nav_section radio
  - inject_mobile_nav()           — fixed bottom nav bar (≤768 px only)
  - inject_mobile_player_header() — compact player pill on player pages
  - inject_mobile_player_selector() — inline <select> for player switching on
                                       mobile (hidden on ≥769px via CSS)
  - inject_mobile_mehr_overlay()  — full-screen "Mehr" menu overlay
"""
import urllib.parse
import streamlit as st

# ── Bottom nav: (icon, label, target_section_key | None=Mehr) ─────────────────
_BOT_NAV = [
    ("🏠", "Start",    "🏠  Startseite"),
    ("👤", "Spieler",  "👤  Spieler"),
    ("🧪", "Tests",    "🔬  Diagnostik"),
    ("📅", "Training", "📅  Training"),
    ("⋯",  "Mehr",     None),
]

# Primary sections shown directly in the bottom nav (excluded from "Mehr" list)
_BOT_NAV_PRIMARY = frozenset({
    "🏠  Startseite",
    "👤  Spieler",
    "🔬  Diagnostik",
    "📅  Training",
})

# Sections where the active-player header is relevant
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
    Read ?player_id= and ?nav= query params; update session state.
    Must be called *before* the nav_section radio widget is instantiated.
    Calls st.rerun() when a param was found (stops current script execution).
    """
    try:
        # ── Player switching (?player_id=<int>) ──────────────────────────────
        player_id_val = st.query_params.get("player_id", "")
        if player_id_val:
            st.query_params.clear()      # prevent infinite loop
            try:
                st.session_state["global_player_id"] = int(player_id_val)
                st.session_state["mobile_mehr_open"] = False
            except (ValueError, TypeError):
                pass
            st.rerun()

        # ── Section navigation (?nav=<section_key>) ──────────────────────────
        nav_val = st.query_params.get("nav", "")
        if not nav_val:
            return
        st.query_params.clear()          # prevent infinite loop
        if nav_val == "__mehr__":
            st.session_state["mobile_mehr_open"] = True
        elif nav_val == "__close_mehr__":
            st.session_state["mobile_mehr_open"] = False
        elif nav_val == "__logout__":
            # Handled separately by the sidebar logout block
            st.session_state["__mobile_logout_request__"] = True
        else:
            # Exact section key (e.g. "🔬  Diagnostik")
            st.session_state["nav_section"] = nav_val
            st.session_state["mobile_mehr_open"] = False
        st.rerun()
    except Exception:
        pass


# ── Bottom navigation bar ─────────────────────────────────────────────────────

def inject_mobile_nav(current_section: str) -> None:
    """
    Inject a fixed bottom nav bar visible only on mobile (≤768 px).
    Navigation uses ?nav= query params so Streamlit re-reads state cleanly.
    """
    mehr_open = bool(st.session_state.get("mobile_mehr_open"))

    items_html = ""
    for icon, label, key in _BOT_NAV:
        if key is None:
            # "Mehr" toggle
            is_active  = mehr_open
            nav_target = "__close_mehr__" if mehr_open else "__mehr__"
        else:
            is_active  = (current_section == key) and not mehr_open
            nav_target = urllib.parse.quote(key)

        active_cls = " aph-bn-active" if is_active else ""
        items_html += (
            f'<a class="aph-bn-item{active_cls}" href="?nav={nav_target}">'
            f'<span class="aph-bn-icon">{icon}</span>'
            f'<span class="aph-bn-label">{label}</span>'
            f'</a>'
        )

    st.markdown(
        f'<nav class="aph-bottom-nav" aria-label="Hauptnavigation">'
        f'{items_html}'
        f'</nav>',
        unsafe_allow_html=True,
    )


# ── Mobile active-player header ───────────────────────────────────────────────

def inject_mobile_player_header(player: dict | None, section: str) -> None:
    """
    On player-specific pages show a compact player pill (mobile only).
    On desktop the element is hidden via @media CSS.
    """
    if not player or section not in _PLAYER_SECTIONS:
        return
    name = player.get("name") or "—"
    pos  = player.get("hauptposition") or player.get("position") or ""
    team = player.get("mannschaft") or ""
    sub  = " · ".join(x for x in [pos, team] if x) or "Kein Team"
    spieler_param = urllib.parse.quote("👤  Spieler")
    st.markdown(
        f'<div class="aph-mph">'
        f'<span class="aph-mph-icon">👤</span>'
        f'<div class="aph-mph-info">'
        f'<div class="aph-mph-name">{name}</div>'
        f'<div class="aph-mph-sub">{sub}</div>'
        f'</div>'
        f'<a class="aph-mph-switch" href="?nav={spieler_param}">Wechseln&nbsp;›</a>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Mobile inline player selector ────────────────────────────────────────────

def inject_mobile_player_selector(alle_spieler: list | None, current_pid) -> None:
    """
    Mobile-only player switcher — native HTML <select> that navigates via
    ?player_id= query param (same pattern as ?nav= mobile navigation).
    Hidden on desktop (≥769px) via CSS .aph-mob-sel-wrap { display:none }.
    Does nothing when fewer than 2 players are available.
    """
    if not alle_spieler or len(alle_spieler) < 2:
        return

    opts: list[str] = []
    for p in alle_spieler:
        pid   = p["id"]
        name  = (
            p.get("name") or
            f"{p.get('vorname', '')} {p.get('nachname', '')}".strip() or
            f"Spieler #{pid}"
        )
        mannsch = p.get("mannschaft") or ""
        display = f"{name} – {mannsch}" if mannsch else name
        sel     = " selected" if pid == current_pid else ""
        opts.append(f'<option value="{pid}"{sel}>{display}</option>')

    opts_html = "\n".join(opts)
    st.markdown(
        f'<div class="aph-mob-sel-wrap">'
        f'<div class="aph-mob-sel-label">👤 Spieler wechseln</div>'
        f'<select class="aph-mob-sel" '
        f'onchange="window.location.href=\'?player_id=\'+encodeURIComponent(this.value)">'
        f'{opts_html}'
        f'</select>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── "Mehr" full-screen overlay ────────────────────────────────────────────────

def inject_mobile_mehr_overlay(alle_sektionen: list[str]) -> bool:
    """
    If mobile_mehr_open is True, render the full-screen "Mehr" overlay.
    The overlay is position:fixed so it covers main content on mobile.
    On desktop display:none — no visual impact.
    Returns True if the overlay is active (caller can skip heavy rendering).
    """
    if not st.session_state.get("mobile_mehr_open"):
        return False

    items_html = ""
    for sek in alle_sektionen:
        sek_s = sek.strip()
        if sek_s in _BOT_NAV_PRIMARY:
            continue                         # already in bottom bar
        param = urllib.parse.quote(sek)
        items_html += (
            f'<a class="aph-mehr-item" href="?nav={param}">'
            f'<span class="aph-mehr-item-text">{sek_s}</span>'
            f'<span class="aph-mehr-item-arrow">›</span>'
            f'</a>'
        )

    logout_html = (
        '<div class="aph-mehr-divider"></div>'
        '<a class="aph-mehr-item aph-mehr-logout" href="?nav=__logout__">'
        '<span class="aph-mehr-item-text">🚪&nbsp;Abmelden</span>'
        '<span class="aph-mehr-item-arrow">›</span>'
        '</a>'
    )

    st.markdown(
        f'<div class="aph-mehr-overlay">'
        f'<div class="aph-mehr-header">'
        f'<span class="aph-mehr-title">Weitere Bereiche</span>'
        f'<a class="aph-mehr-close" href="?nav=__close_mehr__">✕</a>'
        f'</div>'
        f'<div class="aph-mehr-section-label">Navigation</div>'
        f'{items_html}'
        f'{logout_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
    return True
