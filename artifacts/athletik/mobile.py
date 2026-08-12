"""
Mobile-responsive helpers for Athletic Performance Hub.

Provides:
  - handle_mobile_nav_params()    — reads ?player_id= query param only;
                                    must be called before the nav_section radio
  - render_mobile_nav()           — fixed bottom nav bar (≤768 px only).
                                    Uses a proper Streamlit custom component so
                                    clicks do NOT cause a full browser reload.
                                    The same Streamlit WebSocket session and
                                    st.session_state are preserved on every tap.
  - inject_mobile_player_header() — compact player pill on player pages
  - inject_mobile_player_selector() — inline <select> for player switching on
                                       mobile (hidden on ≥769px via CSS)
  - inject_mobile_mehr_overlay()  — full-screen "Mehr" menu overlay
"""
import os as _os
import urllib.parse
import streamlit as st
import streamlit.components.v1 as _stc

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

# ── Declare the custom component (served from the components/ directory) ───────
_COMPONENT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "components", "mobile_nav")
_mobile_nav_comp = _stc.declare_component("aph_mobile_nav", path=_COMPONENT_DIR)


# ── Query-param navigation handler ───────────────────────────────────────────

def handle_mobile_nav_params() -> None:
    """
    Read only ?player_id= query param; update session state.
    The old ?nav= param is no longer used for navigation (the bottom nav
    component handles all navigation internally via Streamlit's WebSocket).
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

        # ── Legacy ?nav= param (kept for deep links / bookmarks) ─────────────
        # If someone navigates to ?nav=xxx directly (e.g. a saved link), we
        # honour it once and then clear it. Normal bottom-nav taps no longer
        # use this mechanism.
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
            st.session_state["nav_section"] = nav_val
            st.session_state["mobile_mehr_open"] = False
        st.rerun()
    except Exception:
        pass


# ── Internal nav-signal handler ───────────────────────────────────────────────

def _apply_nav_signal(target: str) -> None:
    """
    Apply a navigation signal received from the mobile nav component.
    Updates st.session_state and triggers a Streamlit rerun.
    No page reload — the existing WebSocket session is preserved.
    """
    if target == "__mehr__":
        st.session_state["mobile_mehr_open"] = True
    elif target == "__close_mehr__":
        st.session_state["mobile_mehr_open"] = False
    elif target == "__logout__":
        st.session_state["__mobile_logout_request__"] = True
    else:
        st.session_state["nav_section"] = target
        st.session_state["mobile_mehr_open"] = False
    st.rerun()


# ── Bottom navigation bar (component-based, no <a href>) ─────────────────────

def render_mobile_nav(current_section: str) -> None:
    """
    Inject a fixed bottom nav bar visible only on mobile (≤768 px).

    Uses a Streamlit custom component (components/mobile_nav/index.html) that:
      • Renders the five nav items as real <button> elements (no <a href>).
      • Communicates taps back to Python via Streamlit.setComponentValue().
      • Positions itself as position:fixed at the bottom of the page by
        directly styling its own iframe element in the parent document.

    Result: tapping Start / Spieler / Tests / Training / Mehr does NOT cause
    a full browser reload. The same Streamlit WebSocket session continues, and
    all st.session_state (login, active player, tenant, role) is preserved.
    """
    mehr_open = bool(st.session_state.get("mobile_mehr_open"))

    items = []
    for icon, label, key in _BOT_NAV:
        if key is None:
            nav_target = "__close_mehr__" if mehr_open else "__mehr__"
            is_active  = mehr_open
        else:
            nav_target = key
            is_active  = (current_section == key) and not mehr_open
        items.append({
            "icon":   icon,
            "label":  label,
            "target": nav_target,
            "active": is_active,
        })

    # Render the component. It lives inside a hidden iframe on desktop and as
    # a position:fixed 62 px bottom bar on mobile.
    nav_signal = _mobile_nav_comp(
        items=items,
        mehr_open=mehr_open,
        key="aph_mobile_nav",
    )

    # Process the navigation signal (with ts-based deduplication so that
    # the same signal doesn't trigger infinite reruns across Streamlit reruns).
    if isinstance(nav_signal, dict):
        target = nav_signal.get("target", "")
        ts     = nav_signal.get("ts", 0)
        last   = st.session_state.get("_mobile_nav_last") or {}
        if target and (last.get("target") != target or last.get("ts") != ts):
            st.session_state["_mobile_nav_last"] = nav_signal
            _apply_nav_signal(target)


# ── postMessage inline JS helper ──────────────────────────────────────────────
# Used by the Mehr overlay and player header. Since <script> tags do not
# execute inside React's dangerouslySetInnerHTML, we use inline onclick
# attributes with self-contained JavaScript. The JS sends {aphNav: target}
# to all iframes; the nav component iframe picks it up and forwards it to
# Streamlit via setComponentValue.

def _pm_onclick(target: str) -> str:
    """Return an onclick attribute value that posts {aphNav: target} to all iframes."""
    safe = target.replace("\\", "\\\\").replace("'", "\\'")
    return (
        "(function(t){"
        "var fs=window.parent.document.querySelectorAll('iframe');"
        "for(var i=0;i<fs.length;i++){try{fs[i].contentWindow.postMessage({aphNav:t},'*');}catch(e){}}"
        "})('" + safe + "')"
    )


# ── Mobile active-player header ───────────────────────────────────────────────

def inject_mobile_player_header(player: dict | None, section: str) -> None:
    """
    On player-specific pages show a compact player pill (mobile only).
    On desktop the element is hidden via @media CSS.
    "Wechseln" uses an onclick postMessage — no <a href>, no page reload.
    """
    if not player or section not in _PLAYER_SECTIONS:
        return
    name = player.get("name") or "—"
    pos  = player.get("hauptposition") or player.get("position") or ""
    team = player.get("mannschaft") or ""
    sub  = " · ".join(x for x in [pos, team] if x) or "Kein Team"
    st.markdown(
        f'<div class="aph-mph">'
        f'<span class="aph-mph-icon">👤</span>'
        f'<div class="aph-mph-info">'
        f'<div class="aph-mph-name">{name}</div>'
        f'<div class="aph-mph-sub">{sub}</div>'
        f'</div>'
        f'<button class="aph-mph-switch" type="button"'
        f' onclick="{_pm_onclick("👤  Spieler")}">'
        f'Wechseln&nbsp;›</button>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Mobile inline player selector ────────────────────────────────────────────

def inject_mobile_player_selector(alle_spieler: list | None, current_pid) -> None:
    """
    Mobile-only player switcher — native HTML <select> that navigates via
    ?player_id= query param (handled by handle_mobile_nav_params()).
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

    All navigation links use onclick postMessage to the nav bridge component.
    No <a href> — no page reload — session state preserved.

    Returns True if the overlay is active (caller can skip heavy rendering).
    """
    if not st.session_state.get("mobile_mehr_open"):
        return False

    items_html = ""
    for sek in alle_sektionen:
        sek_s = sek.strip()
        if sek_s in _BOT_NAV_PRIMARY:
            continue                         # already in bottom bar
        items_html += (
            f'<button class="aph-mehr-item" type="button"'
            f' onclick="{_pm_onclick(sek)}">'
            f'<span class="aph-mehr-item-text">{sek_s}</span>'
            f'<span class="aph-mehr-item-arrow">›</span>'
            f'</button>'
        )

    close_onclick  = _pm_onclick("__close_mehr__")
    logout_onclick = _pm_onclick("__logout__")

    logout_html = (
        '<div class="aph-mehr-divider"></div>'
        f'<button class="aph-mehr-item aph-mehr-logout" type="button"'
        f' onclick="{logout_onclick}">'
        '<span class="aph-mehr-item-text">🚪&nbsp;Abmelden</span>'
        '<span class="aph-mehr-item-arrow">›</span>'
        '</button>'
    )

    st.markdown(
        f'<div class="aph-mehr-overlay">'
        f'<div class="aph-mehr-header">'
        f'<span class="aph-mehr-title">Weitere Bereiche</span>'
        f'<button class="aph-mehr-close" type="button"'
        f' onclick="{close_onclick}">✕</button>'
        f'</div>'
        f'<div class="aph-mehr-section-label">Navigation</div>'
        f'{items_html}'
        f'{logout_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
    return True
