"""
Mobile-responsive helpers for Athletic Performance Hub.

Provides:
  - handle_mobile_nav_params()    — reads ?player_id= query param only;
                                    ?nav= as legacy deep-link fallback only
  - render_mobile_nav()           — fixed bottom nav bar (≤768 px only).
                                    Uses <button onclick> + hidden st.button
                                    triggers — NO <a href>, no page reload,
                                    same Streamlit WebSocket session preserved.
  - inject_mobile_player_header() — compact player pill on player pages
  - inject_mobile_player_selector() — inline <select> for player switching
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

# ── Trigger button registry ───────────────────────────────────────────────────
# Every possible nav target gets a hidden st.button with label ⬡IDX.
# onclick JS in the visual nav/overlay finds the right button by its label
# and calls .click() — this triggers a Streamlit rerun via WebSocket (no
# full page reload, same session, st.session_state preserved).
#
# ⬡ = U+2B21 (White Hexagon) — unlikely to appear elsewhere in the UI.

_ALL_TARGETS = [
    # Controls (indices 0-2)
    "__mehr__",
    "__close_mehr__",
    "__logout__",
    # Sections (indices 3+)
    "🏠  Startseite",
    "👤  Spieler",
    "🔬  Diagnostik",
    "📅  Training",
    "📈  Entwicklung",
    "⚖️  Vergleich",
    "👥  Mannschaft",
    "📄  Dokumente",
    "⚙️  Einstellungen",
    "👤  Mein Profil",
    "ℹ️  Über",
    "🧑‍💼  Trainerportal",
    "🔑  Benutzerverwaltung",
    "📋  Mein Vertrag",
    "💳  Lizenz",
    "🏢  Vereinsverwaltung",
    "💳  Lizenzverwaltung",
    "👥  Kundenverwaltung",
]
_TARGET_TO_IDX: dict[str, int] = {t: i for i, t in enumerate(_ALL_TARGETS)}


def _bn_onclick(target: str) -> str:
    """
    Return an inline onclick that finds the hidden trigger button ⬡IDX
    in the DOM and programmatically clicks it.
    No page reload — only Streamlit's internal widget mechanism fires.
    """
    idx = _TARGET_TO_IDX.get(target)
    if idx is None:
        return ""
    # JS: find button whose textContent === '⬡' + idx and call .click()
    return (
        f"(function(i){{"
        f"var bs=document.querySelectorAll('button');"
        f"for(var j=0;j<bs.length;j++){{"
        f"if(bs[j].textContent.trim()==='\u2B21'+i){{bs[j].click();return;}}"
        f"}}}})('{idx}')"
    )


def _apply_nav_signal(target: str) -> None:
    """
    Apply navigation: update st.session_state and call st.rerun().
    No page reload — the existing Streamlit WebSocket session continues.
    """
    if target == "__mehr__":
        st.session_state["mobile_mehr_open"] = True
    elif target == "__close_mehr__":
        st.session_state["mobile_mehr_open"] = False
    elif target == "__logout__":
        st.session_state["__mobile_logout_request__"] = True
    else:
        # Use the existing _nav_goto pending key — app.py applies it
        # BEFORE the nav_section widget is instantiated (line ~9812),
        # which avoids StreamlitAPIException when writing to a widget key.
        st.session_state["_nav_goto"] = target
        st.session_state["mobile_mehr_open"] = False
    st.rerun()


# ── Query-param navigation handler ───────────────────────────────────────────

def handle_mobile_nav_params() -> None:
    """
    Read ?player_id= query param; update session state.
    ?nav= is kept as a legacy deep-link fallback only (not used by the
    bottom nav — that now uses hidden st.button triggers instead).
    Must be called *before* the nav_section radio widget is instantiated.
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

        # Legacy deep-link support
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


# ── Bottom navigation bar ─────────────────────────────────────────────────────

def render_mobile_nav(current_section: str) -> None:
    """
    Inject a fixed bottom nav bar visible only on mobile (≤768 px).

    Architecture:
      1. Visual nav: <nav class="aph-bottom-nav"> via st.markdown.
         CSS in theme.py applies position:fixed; bottom:0; z-index:9999.
         Each item is a <button onclick="..."> (NOT <a href>).

      2. <img onerror>: executes on every Streamlit rerun (onerror fires
         when the img is added to the DOM). It:
           • Sets document.documentElement.lang='de' — prevents Chrome
             mobile auto-translate (which caused "sündigen" instead of
             "Abmelden").
           • Sets translate='no' on the HTML element.
           • Starts a MutationObserver that hides trigger button columns
             off-screen as soon as they appear in the DOM.

      3. Hidden trigger buttons: st.button widgets labeled ⬡0…⬡N,
         rendered in st.columns at the end of the page. The MutationObserver
         moves their column containers to position:absolute;top:-9999px so
         users never see them. JavaScript .click() on off-screen elements
         works because the browser does not restrict programmatic clicks by
         CSS position — the React onClick handler fires normally.

      4. When a trigger button is clicked (via JS), it returns True in the
         next Streamlit rerun → _apply_nav_signal() updates session_state
         → st.rerun() → correct page renders. No new WebSocket session,
         no cookie restore needed, all session_state preserved.
    """
    mehr_open = bool(st.session_state.get("mobile_mehr_open"))

    # ── 1. Visual nav items ───────────────────────────────────────────────────
    items_html = ""
    for icon, label, key in _BOT_NAV:
        if key is None:
            nav_target = "__close_mehr__" if mehr_open else "__mehr__"
            is_active  = mehr_open
        else:
            nav_target = key
            is_active  = (current_section == key) and not mehr_open

        active_cls = " aph-bn-active" if is_active else ""
        oc = _bn_onclick(nav_target)
        items_html += (
            f'<button type="button" class="aph-bn-item{active_cls}"'
            f' onclick="{oc}" translate="no">'
            f'<span class="aph-bn-icon">{icon}</span>'
            f'<span class="aph-bn-label">{label}</span>'
            f'</button>'
        )

    # ── 2. Inline JS via onload on a valid 1×1 GIF ───────────────────────────
    # Fires on every Streamlit rerun when the img element is added to the DOM.
    # Using a valid data-URI image (not a broken src) avoids triggering React's
    # onError synthetic event handler, which was causing React error #231 and
    # crashing the WebSocket connection → "artifact encountered an error".
    #
    # The entire JS body is wrapped in try/catch so no exception can escape,
    # even if the DOM is in an unexpected state during a fast rerun.
    #
    # Sets document.documentElement.lang='de' to prevent Chrome Mobile
    # auto-translate (which caused "sündigen" instead of "Abmelden").
    # Starts MutationObserver to hide the hidden trigger button columns.
    # U+2B21 = ⬡ (White Hexagon) — unique prefix for trigger button labels.
    _TINY_GIF = (
        "data:image/gif;base64,"
        "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
    )
    onload_js = (
        "this.onload=null;"
        "try{"
        # Language + translate prevention
        "var h=document.documentElement;"
        "h.lang='de';"
        "h.setAttribute('translate','no');"
        # Cancel previous observer (new one created on every rerun)
        "if(window._aphNavOb){try{window._aphNavOb.disconnect();}catch(e){}}"
        # MutationObserver: hide trigger button columns off-screen
        "window._aphNavOb=new MutationObserver(function(m,ob){"
        "var bs=document.querySelectorAll('button'),f=0;"
        "for(var j=0;j<bs.length;j++){"
        "if(!bs[j]._aphH&&/^\\u2B21\\d+$/.test(bs[j].textContent.trim())){"
        "bs[j]._aphH=1;"
        "var el=bs[j];"
        "for(var k=0;k<8;k++){"
        "if(!el.parentElement)break;"
        "el=el.parentElement;"
        "if(el.getAttribute&&el.getAttribute('data-testid')==='stColumn'){"
        "el.style.cssText='position:absolute!important;"
        "top:-9999px!important;overflow:hidden!important;"
        "height:1px!important;width:1px!important';"
        "f++;break;"
        "}"
        "}"
        "}"
        "}"
        "if(f>0)ob.disconnect();"
        "});"
        "if(document.body)"
        "window._aphNavOb.observe(document.body,{childList:true,subtree:true});"
        "}catch(e){}"
    )

    st.markdown(
        f'<nav class="aph-bottom-nav" aria-label="Hauptnavigation" translate="no">'
        f'{items_html}'
        f'</nav>'
        f'<img src="{_TINY_GIF}" onload="{onload_js}"'
        f' style="display:none;position:absolute;width:0;height:0"'
        f' aria-hidden="true">',
        unsafe_allow_html=True,
    )

    # ── 3. Hidden trigger buttons (one per nav target) ────────────────────────
    # Rendered as columns; hidden off-screen by the MutationObserver above.
    # JavaScript calls .click() on these — no user interaction needed.
    n = len(_ALL_TARGETS)
    trg_cols = st.columns(n)
    for i, target in enumerate(_ALL_TARGETS):
        with trg_cols[i]:
            if st.button(
                f"\u2B21{i}",            # ⬡0, ⬡1, ..., ⬡N
                key=f"_aph_tbn_{i}",
                use_container_width=True,
            ):
                _apply_nav_signal(target)


# ── Mobile active-player header ───────────────────────────────────────────────

def inject_mobile_player_header(player: dict | None, section: str) -> None:
    """
    On player-specific pages show a compact player pill (mobile only).
    On desktop the element is hidden via @media CSS.
    "Wechseln" uses onclick (no <a href>, no page reload).
    """
    if not player or section not in _PLAYER_SECTIONS:
        return
    name = player.get("name") or "—"
    pos  = player.get("hauptposition") or player.get("position") or ""
    team = player.get("mannschaft") or ""
    sub  = " · ".join(x for x in [pos, team] if x) or "Kein Team"
    oc   = _bn_onclick("👤  Spieler")
    st.markdown(
        f'<div class="aph-mph" translate="no">'
        f'<span class="aph-mph-icon">👤</span>'
        f'<div class="aph-mph-info">'
        f'<div class="aph-mph-name">{name}</div>'
        f'<div class="aph-mph-sub">{sub}</div>'
        f'</div>'
        f'<button class="aph-mph-switch" type="button" onclick="{oc}">'
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

    All items use onclick → hidden trigger button → Streamlit rerun.
    No <a href>, no page reload, session preserved.

    Returns True if the overlay is active (caller can skip heavy rendering).
    """
    if not st.session_state.get("mobile_mehr_open"):
        return False

    items_html = ""
    for sek in alle_sektionen:
        sek_s = sek.strip()
        if sek_s in _BOT_NAV_PRIMARY:
            continue
        oc = _bn_onclick(sek_s)
        if not oc:
            continue
        items_html += (
            f'<button class="aph-mehr-item" type="button" onclick="{oc}" translate="no">'
            f'<span class="aph-mehr-item-text">{sek_s}</span>'
            f'<span class="aph-mehr-item-arrow">›</span>'
            f'</button>'
        )

    oc_close  = _bn_onclick("__close_mehr__")
    oc_logout = _bn_onclick("__logout__")

    logout_html = (
        '<div class="aph-mehr-divider"></div>'
        f'<button class="aph-mehr-item aph-mehr-logout" type="button"'
        f' onclick="{oc_logout}" translate="no">'
        '<span class="aph-mehr-item-text">🚪&nbsp;Abmelden</span>'
        '<span class="aph-mehr-item-arrow">›</span>'
        '</button>'
    )

    st.markdown(
        f'<div class="aph-mehr-overlay" translate="no">'
        f'<div class="aph-mehr-header">'
        f'<span class="aph-mehr-title">Weitere Bereiche</span>'
        f'<button class="aph-mehr-close" type="button" onclick="{oc_close}">✕</button>'
        f'</div>'
        f'<div class="aph-mehr-section-label">Navigation</div>'
        f'{items_html}'
        f'{logout_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
    return True
