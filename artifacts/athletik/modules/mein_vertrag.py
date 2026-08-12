"""
modules/mein_vertrag.py — "Mein Vertrag" Seite für Trainer und Vereinsadmin.
Zeigt Vertragsdaten (read-only) und bietet den Online-Kündigungsflow.
"""
from __future__ import annotations
import logging
import streamlit as st
from database import get_conn, kuendigung_einreichen, kuendigung_widerrufen

_log = logging.getLogger("athletik.kuendigung")

_STATUS_BADGE: dict[str, tuple[str, str]] = {
    "active":    ("#238636", "AKTIV"),
    "trial":     ("#1f6feb", "TESTPHASE"),
    "expired":   ("#da3633", "ABGELAUFEN"),
    "cancelled": ("#da3633", "GEKÜNDIGT"),
    "suspended": ("#d29922", "GESPERRT"),
}


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _laden(user: dict) -> dict:
    """Lädt Vertragsdaten für den aktuellen Benutzer aus der passenden Tabelle."""
    ist_verein = user.get("rolle") == "Vereinsadmin"
    eid = user.get("verein_id") if ist_verein else user.get("id")
    tabelle = "vereine" if ist_verein else "benutzer"
    with get_conn() as conn:
        row = conn.execute(f"SELECT * FROM {tabelle} WHERE id=?", (eid,)).fetchone()
    return dict(row) if row else {}


def _feld(label: str, wert) -> None:
    """Zeigt ein read-only Datenfeld mit Label und Wert."""
    v = str(wert) if wert else "Nicht hinterlegt"
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding:9px 0;border-bottom:1px solid #21262d'>"
        f"<span style='color:#8b949e;font-size:13px'>{label}</span>"
        f"<span style='color:#e6edf3;font-size:13px;text-align:right;"
        f"max-width:65%;word-break:break-word'>{v}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _preis_str(lizenztyp: str | None) -> str:
    """Versucht den Monatspreis aus LIZENZ_TYPEN zu lesen."""
    if not lizenztyp:
        return "Nicht hinterlegt"
    try:
        from license import LIZENZ_TYPEN  # noqa: F401
        td = LIZENZ_TYPEN.get(lizenztyp, {})
        pm = td.get("preis_monat") or td.get("preis") or td.get("preis_monatlich")
        if pm is not None:
            return f"€ {float(pm):.2f} / Monat"
    except Exception:
        pass
    return "Nicht hinterlegt"


# ── Hauptseite ────────────────────────────────────────────────────────────────

def page_mein_vertrag() -> None:
    """Hauptseite: Mein Vertrag."""
    user = st.session_state.get("user", {})
    ist_verein = user.get("rolle") == "Vereinsadmin"
    eid: int = user.get("verein_id") if ist_verein else user.get("id")

    st.title("📋 Mein Vertrag")

    data = _laden(user)
    if not data:
        st.error("Vertragsdaten konnten nicht geladen werden.")
        return

    # ── Vertragsinformationen (read-only) ────────────────────────────────────
    st.markdown("### Vertragsinformationen")

    lizenztyp    = data.get("lizenztyp") or data.get("lizenz_typ")
    lizenz_status = data.get("lizenz_status") or "unbekannt"
    sc, sl = _STATUS_BADGE.get(lizenz_status, ("#6e7681", lizenz_status.upper()))

    _feld("Kundennummer",                          data.get("kundennummer"))
    _feld("Kundentyp",                             "Verein" if ist_verein else "Trainer")
    _feld("Aktuelles Paket",                       lizenztyp)
    _feld("Paketpreis",                            _preis_str(lizenztyp))
    _feld("Abrechnungsintervall",                  "Monatlich")
    _feld("Vertragsbeginn",                        data.get("vertragsbeginn"))
    _feld("Vertragsende / Nächste Verlängerung",
          data.get("vertragsende") or data.get("lizenz_bis"))

    # Lizenzstatus-Badge
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding:9px 0;border-bottom:1px solid #21262d'>"
        f"<span style='color:#8b949e;font-size:13px'>Lizenzstatus</span>"
        f"<span style='background:{sc};color:#fff;font-size:11px;font-weight:700;"
        f"padding:3px 12px;border-radius:12px;letter-spacing:.5px'>{sl}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    kuend_status = data.get("kuendigungsstatus")
    _feld("Kündigungsstatus",
          kuend_status if kuend_status and kuend_status != "aktiv"
          else "Kein Kündigungsvorgang")

    if data.get("kuendigung_eingegangen"):
        _feld("Kündigung eingegangen am",
              (data["kuendigung_eingegangen"] or "")[:10])
        if data.get("gekuendigt_zum"):
            _feld("Vertrag endet am", data["gekuendigt_zum"])

    # ── Aktive Kündigung: Info + ggf. Widerruf ───────────────────────────────
    if data.get("kuendigung_eingegangen"):
        st.markdown("---")
        eingang   = (data.get("kuendigung_eingegangen") or "")[:10]
        vende     = data.get("gekuendigt_zum") or "Beendigungsdatum wird noch bestätigt."
        k_status  = data.get("kuendigungsstatus") or ""

        if k_status == "eingegangen":
            # ── Widerruf-Frist prüfen ────────────────────────────────────────
            import os as _os_mv, datetime as _dt_mv
            frist_ok   = True   # True = Widerruf noch innerhalb der Frist
            frist_text = ""
            try:
                _frist_h = int(_os_mv.environ.get("KUENDIGUNG_WIDERRUF_STUNDEN", "0"))
                if _frist_h > 0 and data.get("kuendigung_eingegangen"):
                    _eingeg = _dt_mv.datetime.fromisoformat(data["kuendigung_eingegangen"])
                    _ablauf = _eingeg + _dt_mv.timedelta(hours=_frist_h)
                    _jetzt  = _dt_mv.datetime.utcnow()
                    _ablauf_fmt = _ablauf.strftime("%d.%m.%Y %H:%M")
                    if _jetzt > _ablauf:
                        frist_ok   = False
                        frist_text = f"Die Widerruf-Frist ist abgelaufen ({_ablauf_fmt} Uhr)."
                    else:
                        _rest_h = int((_ablauf - _jetzt).total_seconds() // 3600)
                        _rest_m = int(((_ablauf - _jetzt).total_seconds() % 3600) // 60)
                        frist_text = (
                            f"Widerruf möglich bis **{_ablauf_fmt} Uhr** "
                            f"(noch {_rest_h}h {_rest_m}min)"
                        )
            except Exception:
                pass

            # Noch nicht vom Admin bestätigt → Widerruf ggf. möglich
            st.warning(
                f"**Deine Kündigung ist eingegangen und wird geprüft.**\n\n"
                f"Eingangsdatum: **{eingang}**  \n"
                "Solange sie noch nicht bestätigt wurde, kannst du sie "
                "ggf. zurückziehen."
            )
            if frist_text:
                if frist_ok:
                    st.info(f"⏰ {frist_text}")
                else:
                    st.error(f"⏰ {frist_text}")
            st.caption(
                "Bei Fragen wende dich an "
                "[support@aphsystem.de](mailto:support@aphsystem.de)."
            )

            if frist_ok:
                st.markdown("")
                st.markdown("#### Kündigung zurückziehen")
                st.markdown(
                    "Wenn du deine Meinung geändert hast, kannst du die Kündigung "
                    "jetzt noch zurückziehen. Dein Vertrag läuft dann wie gewohnt weiter."
                )
                wid_confirm = st.checkbox(
                    "Ja, ich möchte meine Kündigung zurückziehen und meinen Vertrag fortführen.",
                    key="wid_confirm",
                )
                if st.button(
                    "✅ Kündigung zurückziehen",
                    key="wid_btn",
                    disabled=not wid_confirm,
                    type="primary",
                ):
                    ok, grund = kuendigung_widerrufen(eid, ist_verein)
                    if ok:
                        _sende_widerruf_email(user, data, ist_verein=ist_verein)
                        st.success(
                            "✅ Deine Kündigung wurde zurückgezogen. "
                            "Dein Vertrag läuft weiter."
                        )
                        st.rerun()
                    elif grund == "frist_abgelaufen":
                        st.error(
                            "Die Widerruf-Frist ist soeben abgelaufen. "
                            "Ein Widerruf ist leider nicht mehr möglich. "
                            "Bitte wende dich an support@aphsystem.de."
                        )
                    else:
                        st.error(
                            "Die Kündigung kann nicht mehr zurückgezogen werden — "
                            "sie wurde bereits vom Support bestätigt. "
                            "Bitte wende dich an support@aphsystem.de."
                        )
            else:
                st.info(
                    "Ein Widerruf ist nicht mehr möglich, da die Widerruf-Frist "
                    "abgelaufen ist. Bitte wende dich bei Fragen an "
                    "[support@aphsystem.de](mailto:support@aphsystem.de)."
                )
        else:
            # Bereits bestätigt oder beendet → nur Information, kein Widerruf
            st.info(
                f"**Deine Kündigung ist eingegangen.**\n\n"
                f"Eingangsdatum: **{eingang}**  \n"
                f"Vertragsende: **{vende}**"
            )
            st.caption(
                "Bei Fragen wende dich an "
                "[support@aphsystem.de](mailto:support@aphsystem.de)."
            )
        return

    # ── Kündigungsbereich ────────────────────────────────────────────────────
    st.markdown("---")

    if lizenz_status not in ("active", "trial"):
        st.info("Eine Kündigung ist für den aktuellen Vertragsstatus nicht möglich.")
        return

    _kuendigung_flow(user, eid, ist_verein, data)


# ── Kündigungsflow ────────────────────────────────────────────────────────────

def _kuendigung_flow(user: dict, eid: int, ist_verein: bool, data: dict) -> None:
    """Dreistufiger Kündigungsflow (Schritt 0 → 1 → 2)."""
    step: int = st.session_state.get("_kuend_step", 0)

    # ── Schritt 0: Info + Einstieg ──────────────────────────────────────────
    if step == 0:
        st.markdown("### Vertrag kündigen")
        st.warning(
            "Eine Kündigung beendet deinen Vertrag zum vorgesehenen Termin. "
            "Der Zugang bleibt bis dahin vollständig erhalten. "
            "Deine Daten werden entsprechend der Datenschutzrichtlinie behandelt."
        )
        if st.button("Kündigung starten", key="kuend_start"):
            st.session_state["_kuend_step"] = 1
            st.rerun()
        return

    # ── Schritt 1: Grund + Bestätigung ─────────────────────────────────────
    if step == 1:
        st.markdown("### Kündigung bestätigen")

        lizenztyp    = data.get("lizenztyp") or data.get("lizenz_typ") or "—"
        lizenz_status = data.get("lizenz_status") or "—"
        vertragsende = data.get("vertragsende") or data.get("lizenz_bis") or "Nicht hinterlegt"

        st.markdown(
            f"**Aktuelles Paket:** {lizenztyp}  \n"
            f"**Vertragsstatus:** {lizenz_status}  \n"
            f"**Vertragsende / Nächste Verlängerung:** {vertragsende}"
        )
        st.markdown("")

        grund_opts = [
            "Kein Grund angeben",
            "Produkt wird nicht mehr benötigt",
            "Preis",
            "Funktionsumfang",
            "Wechsel zu anderer Lösung",
            "Sonstiges",
        ]
        auswahl = st.selectbox("Kündigungsgrund (optional)", grund_opts, key="kuend_grund_sel")
        grund: str | None = None
        if auswahl == "Sonstiges":
            grund = st.text_area("Freitext (optional)", key="kuend_freitext", max_chars=500) or None
        elif auswahl != "Kein Grund angeben":
            grund = auswahl

        st.markdown("")
        confirmed = st.checkbox(
            "Ich bestätige hiermit, meinen Vertrag verbindlich zu kündigen.",
            key="kuend_confirm",
        )

        c1, c2 = st.columns([1, 2])
        if c1.button("← Zurück", key="kuend_back"):
            st.session_state["_kuend_step"] = 0
            st.rerun()

        if c2.button(
            "Vertrag verbindlich kündigen",
            type="primary",
            key="kuend_final",
            disabled=not confirmed,
        ):
            ok, ergebnis = kuendigung_einreichen(eid, ist_verein, grund)
            if ok:
                _sende_email(user, data, ergebnis[:10], ist_verein=ist_verein, grund=grund)
                st.session_state["_kuend_step"] = 2
                st.session_state["_kuend_datum"] = ergebnis[:10]
                st.rerun()
            else:
                st.error("Für diesen Vertrag liegt bereits eine Kündigung vor.")
        return

    # ── Schritt 2: Bestätigungsseite ────────────────────────────────────────
    if step == 2:
        datum  = st.session_state.get("_kuend_datum", "—")
        data2  = _laden(user)
        vende  = (data2.get("gekuendigt_zum")
                  or data2.get("vertragsende")
                  or "Beendigungsdatum wird noch bestätigt.")

        st.success("✅ Kündigung erfolgreich übermittelt")
        st.markdown(
            f"**Eingangsdatum:** {datum}  \n"
            f"**Paket:** {data2.get('lizenztyp') or '—'}  \n"
            f"**Vertragsende:** {vende}  \n\n"
            "Eine Bestätigungs-E-Mail wurde an deine hinterlegte E-Mail-Adresse gesendet."
        )
        st.markdown("Bei Fragen: [support@aphsystem.de](mailto:support@aphsystem.de)")

        with st.expander("📄 Kündigungsbestätigung anzeigen"):
            st.markdown(
                f"**Kundennummer:** {data2.get('kundennummer') or '—'}  \n"
                f"**Kündigung eingegangen am:** "
                f"{(data2.get('kuendigung_eingegangen') or '')[:10]}  \n"
                f"**Kündigungsstatus:** {data2.get('kuendigungsstatus') or '—'}  \n"
                f"**Vertragsende:** {vende}"
            )

        if st.button("Zur Vertragsübersicht", key="kuend_done"):
            st.session_state["_kuend_step"] = 0
            st.rerun()


def _sende_widerruf_email(user: dict, data: dict, ist_verein: bool = False) -> None:
    """Sendet Widerrufs-Bestätigung an den Kunden und Admin-Benachrichtigung an Superadmin."""
    import datetime as _dt
    import os as _os

    kundennummer = data.get("kundennummer") or "—"
    lizenztyp    = data.get("lizenztyp") or data.get("lizenz_typ") or "—"
    kundenname   = user.get("vorname") or user.get("name") or ""
    kundenemail  = user.get("email") or ""
    zeitstempel  = _dt.datetime.now().strftime("%d.%m.%Y %H:%M Uhr")

    # ── 1. Bestätigungs-E-Mail an den Kunden ────────────────────────────────
    try:
        from email_service import send_kuendigung_widerrufen
        if kundenemail:
            send_kuendigung_widerrufen(
                to=kundenemail,
                name=kundenname or "Kunde",
                kundennummer=kundennummer,
                lizenztyp=lizenztyp,
            )
            _log.info("Widerrufs-Bestätigung an %s... gesendet", kundenemail[:4])
    except Exception as exc:
        _log.error("Widerrufs-Kunden-E-Mail fehlgeschlagen: %s", type(exc).__name__)

    # ── 2. Sofort-Benachrichtigung an Superadmin ─────────────────────────────
    # Nur senden wenn SUPERADMIN_EMAIL konfiguriert ist — kein PII-Fallback.
    try:
        from email_service import send_widerruf_admin_benachrichtigung
        admin_email = _os.environ.get("SUPERADMIN_EMAIL", "").strip()
        if not admin_email:
            _log.warning(
                "SUPERADMIN_EMAIL nicht konfiguriert — "
                "Widerruf-Admin-Benachrichtigung übersprungen"
            )
        else:
            kundentyp = "Verein" if ist_verein else "Einzeltrainer"
            send_widerruf_admin_benachrichtigung(
                to=admin_email,
                kundennummer=kundennummer,
                kundentyp=kundentyp,
                kundenname=kundenname,
                kundenemail=kundenemail,
                zeitstempel=zeitstempel,
            )
            _log.info("Widerruf-Admin-Benachrichtigung gesendet")
    except Exception as exc:
        _log.error("Widerruf-Admin-Benachrichtigung fehlgeschlagen: %s", type(exc).__name__)


def _sende_email(
    user: dict,
    data: dict,
    datum: str,
    ist_verein: bool = False,
    grund: str = "",
) -> None:
    """Sendet Kündigungsbestätigung an den Kunden und Admin-Benachrichtigung an Superadmin."""
    import os as _os

    kundennummer = data.get("kundennummer") or "—"
    lizenztyp    = data.get("lizenztyp") or data.get("lizenz_typ") or "—"
    kundenname   = user.get("vorname") or user.get("name") or ""
    kundenemail  = user.get("email") or ""

    # ── 1. Bestätigungs-E-Mail an den Kunden ────────────────────────────────
    try:
        from email_service import send_kuendigung_bestaetigung
        if kundenemail:
            send_kuendigung_bestaetigung(
                to=kundenemail,
                name=kundenname or "Kunde",
                kundennummer=kundennummer,
                lizenztyp=lizenztyp,
                kuendigung_datum=datum,
                vertragsende=(data.get("vertragsende")
                              or data.get("lizenz_bis")
                              or "Wird noch bestätigt"),
            )
            _log.info("Kündigungsbestätigung an %s... gesendet", kundenemail[:4])
    except Exception as exc:
        _log.error("Kündigungsbestätigungs-E-Mail fehlgeschlagen: %s", type(exc).__name__)

    # ── 2. Sofort-Benachrichtigung an Superadmin ─────────────────────────────
    try:
        from email_service import send_kuendigung_admin_benachrichtigung
        admin_email = (
            _os.environ.get("SUPERADMIN_EMAIL", "").strip()
            or "support@aphsystem.de"
        )
        kundentyp = "Verein" if ist_verein else "Einzeltrainer"
        send_kuendigung_admin_benachrichtigung(
            to=admin_email,
            kundennummer=kundennummer,
            kundentyp=kundentyp,
            lizenztyp=lizenztyp,
            datum=datum,
            kundenname=kundenname,
            kundenemail=kundenemail,
            grund=grund or "",
        )
        _log.info("Admin-Kündigung-Benachrichtigung gesendet")
    except Exception as exc:
        _log.error(
            "Admin-Kündigung-Benachrichtigung fehlgeschlagen: %s", type(exc).__name__
        )
