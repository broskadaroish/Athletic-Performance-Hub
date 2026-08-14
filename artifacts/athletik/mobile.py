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
    screen-width JS fires before the user logs in.  This prevents the
    post-login location.replace() reload that would otherwise wipe
    session_state and force a double-rerun after authentication.
    """
    _inject_screen_width_detect()


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

    • Click:    Finds [data-testid="stSidebarCollapseButton"] button — the real
                Streamlit 1.60.0 toggle — and clicks it.  No custom routing.

    • State:    A MutationObserver registered on window.parent (not in the
                iframe, so it persists across reruns) watches the sidebar
                element for class/style/aria-expanded attribute changes and
                detects open/closed state via getBoundingClientRect().
                When sidebar is open: adds class .aph-sidebar-open (button
                hides via CSS rule in theme.py).
                When sidebar is closed: removes that class (button shows).

    • Guard:    window.parent.__aphSidebarObserverInstalled prevents duplicate
                observer registration across reruns.
                window.parent.__aphUpdateMenuBtn is stored on the parent so it
                remains callable after the iframe that created it is destroyed.
    """
    import streamlit.components.v1 as components

    components.html(
        """<script>
(function() {
  try {
    var W   = window.parent;
    var doc = W.document;
    if (!doc || !doc.body) return;

    /* ── ensureBtn: create / return #aph-menu-btn in doc.body ────── */
    function ensureBtn() {
      var btn = doc.getElementById('aph-menu-btn');
      if (btn) return btn;

      btn = doc.createElement('button');
      btn.id = 'aph-menu-btn';
      btn.setAttribute('aria-label', 'Navigation öffnen');
      btn.setAttribute('title', 'Navigation öffnen');
      btn.textContent = '\\u2630';   /* ☰ */

      btn.addEventListener('click', function(e) {
        e.preventDefault();
        /* Streamlit 1.60.0 confirmed DOM: toggle button lives inside
           stSidebarCollapseButton > button inside stSidebarHeader.
           It is always present even when sidebar is collapsed. */
        var target = (
          doc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
          doc.querySelector('[data-testid="stSidebarHeader"] button')         ||
          doc.querySelector('section[data-testid="stSidebar"] button')
        );
        if (target) target.click();
      });

      doc.body.appendChild(btn);
      return btn;
    }

    /* ── isSidebarOpen: uses bounding rect (works for transform/display hide) */
    function isSidebarOpen() {
      var sb = doc.querySelector('section[data-testid="stSidebar"]');
      if (!sb) return false;
      /* If sidebar is off-screen (collapsed via CSS transform), right <= 0 */
      return sb.getBoundingClientRect().right > 10;
    }

    /* ── updateBtn: stored on parent window so it survives iframe teardown */
    W.__aphUpdateMenuBtn = function() {
      var btn = ensureBtn();
      if (isSidebarOpen()) {
        btn.classList.add('aph-sidebar-open');
      } else {
        btn.classList.remove('aph-sidebar-open');
      }
    };

    /* Initial state */
    W.__aphUpdateMenuBtn();

    /* ── MutationObserver — registered ONCE on parent window ─────── */
    if (!W.__aphSidebarObserverInstalled) {
      W.__aphSidebarObserverInstalled = true;

      var obs = new W.MutationObserver(function() {
        if (W.__aphUpdateMenuBtn) W.__aphUpdateMenuBtn();
      });

      /* Watch sidebar for attribute changes (style/class/aria-expanded).
         The sidebar element is always present in Streamlit's React tree;
         React updates its attributes rather than recreating the element. */
      function attachToSidebar() {
        var sb = doc.querySelector('section[data-testid="stSidebar"]');
        if (sb) {
          obs.observe(sb, {
            attributes:      true,
            attributeFilter: ['class', 'aria-expanded', 'style']
          });
        }
      }

      /* Also watch body's direct children for structural changes
         (e.g. React root added after initial load). */
      obs.observe(doc.body, { childList: true });

      attachToSidebar();
    } else {
      /* Observer already running — just refresh button state */
      W.__aphUpdateMenuBtn();
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
