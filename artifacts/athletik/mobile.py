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
            # Also read ?nav= if present so the active section is preserved
            # after the full-page reload triggered by the player selector <select>.
            _nav_from_player_sel = st.query_params.get("nav", "")
            st.query_params.clear()
            try:
                st.session_state["global_player_id"] = int(player_id_val)
                st.session_state["mobile_mehr_open"] = False
            except (ValueError, TypeError):
                pass
            if _nav_from_player_sel:
                st.session_state["_nav_goto"] = _nav_from_player_sel
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


def detect_screen_width() -> None:
    """
    Public wrapper around _inject_screen_width_detect().
    Call this as early as possible — even on the login page — so the
    screen-width detection JS fires before the user logs in.  This ensures
    _screen_width is already set when the authenticated section runs,
    avoiding any extra Streamlit rerun after authentication.
    """
    _inject_screen_width_detect()


def _inject_screen_width_detect() -> None:
    """
    Detect the viewport width once per session WITHOUT a browser page reload.

    Mechanism
    ─────────
    1. Guard: if _screen_width is already in session_state → return immediately.

    2. Consume ?_sw= if present (set by a previous Streamlit rerun):
       - Read the value, write _screen_width to session_state, delete the param.
       - Return — no JS needed.

    3. If JS detection has failed twice in a row → default to 768 px (mobile-safe)
       so the app still loads instead of looping forever.

    4. First-time detection:
       - Inject a JS snippet that reads window.parent.innerWidth and writes the
         result to the URL via window.parent.history.replaceState() — this updates
         the URL in-place WITHOUT any browser page reload, HTTP request, or new
         WebSocket connection.
       - Wait 0.4 s (server-side) for the browser to execute the injected JS.
       - Call st.rerun() — a Streamlit-internal WebSocket-based rerun, NOT a
         browser reload.  session_state is fully preserved.
       - On that second render cycle, step 2 above finds ?_sw= in query_params,
         reads it, and the detection is complete.

    Safari note
    ───────────
    history.replaceState() mutates only the URL bar — no navigation event,
    no reload, no new WebSocket connection.  session_state is fully preserved
    across the st.rerun() that follows.
    """
    import streamlit.components.v1 as components
    import time

    # ── 1. Already detected ────────────────────────────────────────────────────
    if "_screen_width" in st.session_state:
        return

    # ── 2. Consume ?_sw= written by JS in the previous Streamlit rerun ────────
    sw_val = st.query_params.get("_sw", "")
    if sw_val:
        try:
            st.session_state["_screen_width"] = int(sw_val)
        except (ValueError, TypeError):
            st.session_state["_screen_width"] = 768
        try:
            del st.query_params["_sw"]
        except Exception:
            pass
        st.session_state.pop("_sw_detect_attempts", None)  # reset counter
        return

    # ── 3. Fallback after repeated JS failures ─────────────────────────────────
    _attempts = st.session_state.get("_sw_detect_attempts", 0)
    if _attempts >= 2:
        # JS never set ?_sw= — device quirk or very slow JS execution.
        # Default to mobile-safe width so the app continues loading.
        st.session_state["_screen_width"] = 768
        st.session_state.pop("_sw_detect_attempts", None)
        return

    st.session_state["_sw_detect_attempts"] = _attempts + 1

    # ── 4. Inject detection JS ─────────────────────────────────────────────────
    # history.replaceState() updates the URL without any page reload or new
    # WebSocket connection — Safari-safe.
    components.html(
        "<script>"
        "try {"
        "  var w = Math.round(window.parent.innerWidth || window.innerWidth || 0);"
        "  if (w > 0) {"
        "    var u = new URL(window.parent.location.href);"
        "    u.searchParams.set('_sw', String(w));"
        "    window.parent.history.replaceState(null, '', u.toString());"
        "  }"
        "} catch(e) {}"
        "</script>",
        height=0,
        scrolling=False,
    )

    # Wait for the browser to execute the JS, then trigger a Streamlit-internal
    # rerun (WebSocket message — NOT a browser page reload).
    time.sleep(0.4)
    st.rerun()


# ── Mobile sidebar open button ────────────────────────────────────────────────

def inject_mobile_sidebar_opener() -> None:
    """
    Inject a persistent floating ☰ button that opens the Streamlit sidebar
    drawer on narrow (≤768px) viewports.

    Architecture
    ────────────
    • Styling:  Defined entirely in theme.py (@media rules for #aph-menu-btn).
                theme.py CSS is re-injected on every Streamlit rerun → always
                wins over any older JS-injected style.  This function does NOT
                inject any <style> tag.

    • Button:   Appended to window.parent.document.body (outside Streamlit's
                React tree) via a hidden components.html() iframe.
                Survives Streamlit reruns because React manages only its own
                root element and leaves foreign body children untouched.
                On every call: reuse existing #aph-menu-btn if already present,
                otherwise create a new one.

    • Visibility: The button is ALWAYS visible on mobile (≤768px), regardless
                of sidebar state.  No MutationObserver, no state tracking,
                no .aph-sidebar-open class.

    • Click:    At click time the DOM is queried fresh (Streamlit replaces
                elements on reruns).  Selector chain:
                  1. [data-testid="stSidebarCollapseButton"] button
                  2. [data-testid="stSidebarHeader"] button
                  3. section[data-testid="stSidebar"] button
    """
    import streamlit.components.v1 as components

    components.html(
        """<script>
(function() {
  try {
    var W   = window.parent;
    var doc = W.document;
    if (!doc || !doc.body) return;

    /* Reuse existing button or create a new one — never duplicate. */
    var btn = doc.getElementById('aph-menu-btn');
    if (!btn) {
      btn = doc.createElement('button');
      btn.id = 'aph-menu-btn';
      btn.setAttribute('aria-label', 'Navigation öffnen');
      btn.setAttribute('title', 'Navigation öffnen');
      btn.textContent = '\\u2630';   /* ☰ */
      btn._aphLastClick = 0;

      /* findSidebarToggle — queries fresh each call because Streamlit's
         React tree replaces DOM nodes on reruns.
         Selector chain covers Streamlit 1.30–1.60+. */
      function findSidebarToggle() {
        return (
          doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
          doc.querySelector('[data-testid="stSidebarHeader"] button')         ||
          doc.querySelector('section[data-testid="stSidebar"] button')        ||
          doc.querySelector('button[aria-label*="sidebar"]')                  ||
          doc.querySelector('button[aria-label*="Sidebar"]')
        );
      }

      /* tryClick — retries up to `attempts` times with 200ms intervals.
         Needed when Streamlit is mid-rerun and sidebar button is not yet
         in the DOM. */
      function tryClick(attempts) {
        var target = findSidebarToggle();
        if (target) {
          target.click();
        } else if (attempts > 0) {
          setTimeout(function() { tryClick(attempts - 1); }, 200);
        }
      }

      /* Shared handler — attached once, reused across Streamlit reruns.
         Debounce: 400ms prevents double-trigger on rapid tap (mobile).
         Last-click time stored on the element (survives IIFE re-runs). */
      function handleOpen(e) {
        e.preventDefault();
        e.stopPropagation();
        var now = Date.now();
        if (now - (btn._aphLastClick || 0) < 400) return;
        btn._aphLastClick = now;
        tryClick(3);  /* retry up to 3×200ms = 600ms if DOM not ready */
      }

      btn.addEventListener('click',    handleOpen, { passive: false });
      /* touchend: eliminates ~300ms tap-to-click delay on older iOS/Android */
      btn.addEventListener('touchend', handleOpen, { passive: false });

      doc.body.appendChild(btn);
    }
  } catch(e) {}
})();
</script>""",
        height=0,
        scrolling=False,
    )


# ── Bottom navigation bar ─────────────────────────────────────────────────────

def render_mobile_nav(current_section: str) -> None:
    """
    No-op: Bottom navigation is disabled.

    Navigation on all viewports (mobile and desktop) is now handled exclusively
    by the Streamlit sidebar drawer.  On mobile (≤768px) Streamlit's built-in
    hamburger button (☰) opens the sidebar as a slide-in overlay — the same
    st.radio nav_section widget used on desktop.

    This function is kept as a stub so that existing call-sites in app.py
    require no import changes.  The screen-width detector is still injected
    so that _screen_width is available for other guards (e.g. inject_mobile_player_header).
    """
    _inject_screen_width_detect()


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
    On player-specific pages show a compact mobile-only player info pill.

    The confirmed, in-place player switcher is rendered by the active page so
    it can preserve the current section instead of navigating to player admin.
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

def inject_mobile_player_selector(
    alle_spieler: list | None,
    current_pid,
    current_section: str = "",
) -> None:
    """
    Mobile-only player switcher — native HTML <select> that navigates via
    ?player_id= query param (read by handle_mobile_nav_params()).
    Hidden on desktop (≥769px) via CSS .aph-mob-sel-wrap { display:none }.
    Does nothing when fewer than 2 players are available.

    current_section: the active nav_section value — passed as ?nav= so that
    handle_mobile_nav_params() can restore it after the page reload, preventing
    the app from falling back to Startseite after a player switch.
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

    # Encode nav section for the query string so the active page is preserved
    # after the browser reload that player switching causes.
    try:
        import urllib.parse as _up
        _nav_qs = ("&nav=" + _up.quote(current_section, safe="")) if current_section else ""
    except Exception:
        _nav_qs = ""

    st.markdown(
        f'<div class="aph-mob-sel-wrap">'
        f'<div class="aph-mob-sel-label">👤 Spieler wechseln</div>'
        f'<select class="aph-mob-sel" '
        f'onchange="window.location.href=\'?player_id=\''
        f'+encodeURIComponent(this.value)+\'{_nav_qs}\'">'
        + "\n".join(opts) +
        f'</select>'
        f'</div>',
        unsafe_allow_html=True,
    )
