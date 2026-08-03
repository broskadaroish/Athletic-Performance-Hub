"""
Session-Timeout für die Athletik App.
Meldet inaktive Benutzer automatisch ab.

Konfiguration über Umgebungsvariable:
  SESSION_TIMEOUT_MINUTES=60  (Standard: 60 Minuten)

Verwendung in app.py:
  from session_timeout import check_session_timeout
  # Am Anfang jeder authentifizierten Seite aufrufen:
  check_session_timeout()
"""

import os
from datetime import datetime, timedelta
import streamlit as st

# Timeout aus Umgebungsvariable (Standard: 60 Minuten)
_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MINUTES", "60"))
_WARN_MINUTES    = 5  # Warnung X Minuten vor Ablauf


def _now() -> datetime:
    return datetime.now()


def touch_session() -> None:
    """Zeitstempel der letzten Aktivität aktualisieren.
    Wird bei jeder Nutzerinteraktion aufgerufen (Streamlit re-run).
    """
    st.session_state["_last_active"] = _now().isoformat()


def check_session_timeout() -> bool:
    """Prüft ob die Session abgelaufen ist.

    Returns:
        True  → Session gültig, App kann weiterlaufen
        False → Session abgelaufen (Nutzer wurde ausgeloggt, Seite wird neu geladen)

    Seiteneffekte:
        - Setzt _last_active beim ersten Aufruf
        - Löscht session_state und zeigt Timeout-Meldung wenn abgelaufen
        - Zeigt Warnung wenn Ablauf bevorsteht
    """
    if "user" not in st.session_state:
        # Nicht eingeloggt — kein Timeout-Check nötig
        return True

    now = _now()

    # Beim ersten Aufruf nach Login: Zeitstempel setzen
    if "_last_active" not in st.session_state:
        touch_session()
        return True

    last_active_str = st.session_state.get("_last_active", "")
    try:
        last_active = datetime.fromisoformat(last_active_str)
    except (ValueError, TypeError):
        touch_session()
        return True

    elapsed   = now - last_active
    remaining = timedelta(minutes=_TIMEOUT_MINUTES) - elapsed

    # ── Session abgelaufen ────────────────────────────────────────────────────
    if remaining.total_seconds() <= 0:
        _user_name = st.session_state.get("user", {}).get("vorname", "")
        # Session vollständig löschen
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.warning(
            f"⏱️ Deine Sitzung ist nach {_TIMEOUT_MINUTES} Minuten Inaktivität abgelaufen. "
            "Bitte melde dich erneut an."
            + (f" — Bis bald, {_user_name}!" if _user_name else "")
        )
        st.rerun()
        return False

    # ── Warnung vor Ablauf ────────────────────────────────────────────────────
    if 0 < remaining.total_seconds() <= _WARN_MINUTES * 60:
        mins = max(1, int(remaining.total_seconds() / 60) + 1)
        st.toast(
            f"⏱️ Deine Sitzung läuft in ca. {mins} Minute{'n' if mins != 1 else ''} ab.",
            icon="⏱️",
        )

    # ── Aktivität registrieren ─────────────────────────────────────────────────
    touch_session()
    return True
