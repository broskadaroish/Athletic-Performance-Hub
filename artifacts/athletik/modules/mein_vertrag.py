"""
modules/mein_vertrag.py — "Mein Vertrag" Seite für Trainer und Vereinsadmin.
Zeigt Vertragsdaten (read-only) und bietet den Online-Kündigungsflow.

Datenquelle: IMMER aus `vereine` (per verein_id), für alle Rollen.
`benutzer` liefert nur Login/Profil-Felder.
"""
from __future__ import annotations
import logging
import streamlit as st
from database import get_conn, kuendigung_einreichen, kuendigung_widerrufen, rechnungen_laden
import logging as _logging_mv

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
    """Lädt Vertragsdaten für den aktuellen Benutzer immer aus `vereine`.

    Für alle Rollen (Vereinsadmin und Trainer) wird `verein_id` aus dem
    User-Objekt verwendet. `benutzer` liefert nur Profil-Felder (E-Mail, Name).

    Sonderfall technischer Mandant (Einzeltrainer):
    Vertragsdaten kommen aus `vereine`, aber die fachliche Kundennummer
    wird aus `benutzer.kundennummer` übernommen — der technische Mandant
    hat eine eigene (interne) Kundennummer, die nie dem Kunden angezeigt
    werden soll.
    """
    verein_id = user.get("verein_id")
    if not verein_id:
        _log.warning("_laden: user hat keine verein_id (user_id=%s)", user.get("id"))
        return {}
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM vereine WHERE id=?", (verein_id,)
        ).fetchone()
    if not row:
        return {}
    data = dict(row)
    # Für Trainer mit technischem Mandant: sichtbare Kundennummer aus benutzer,
    # nicht aus vereine (deren kundennummer ist eine interne Mandanten-Nummer).
    if data.get("ist_technischer_mandant"):
        benutzer_kn = user.get("kundennummer")
        if benutzer_kn:
            data["kundennummer"] = benutzer_kn
    return data


def _fmt_datum(raw: str | None) -> str | None:
    """Formatiert ISO-Datum YYYY-MM-DD → DD.MM.YYYY. None wenn kein Wert."""
    if not raw:
        return None
    try:
        s = str(raw)[:10]
        teile = s.split("-")
        if len(teile) == 3:
            return f"{teile[2]}.{teile[1]}.{teile[0]}"
    except Exception:
        pass
    return str(raw)[:10]


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


def _preis_str(lizenztyp: str | None, abo_intervall: str | None) -> str:
    """Liest Preis aus LIZENZ_TYPEN[lizenztyp] passend zum Abrechnungsintervall.

    Format: "9,99 € / Monat" oder "99,00 € / Jahr".
    Keine zweite Preistabelle — einzige Quelle ist license.py.
    """
    if not lizenztyp:
        return "Nicht hinterlegt"
    try:
        from license import LIZENZ_TYPEN
        td = LIZENZ_TYPEN.get(lizenztyp, {})
        if abo_intervall == "jahr":
            pm = td.get("preis_jahr")
            if pm is not None:
                return f"{float(pm):,.2f} € / Jahr".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            # Standardfall: monatlich
            pm = td.get("preis_monat")
            if pm is not None:
                return f"{float(pm):,.2f} € / Monat".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        pass
    return "Nicht hinterlegt"


def _intervall_label(abo_intervall: str | None) -> str:
    """Gibt lesbares Label für das Abrechnungsintervall zurück."""
    if abo_intervall == "jahr":
        return "Jährlich"
    if abo_intervall == "monat":
        return "Monatlich"
    if abo_intervall:
        return abo_intervall  # unbekannter Wert → roh anzeigen
    return "Nicht hinterlegt"


def _lizenztyp_label(lizenztyp: str | None) -> str:
    """Gibt lesbaren Anzeigenamen für den normalisierten Lizenztyp zurück."""
    if not lizenztyp:
        return "Nicht hinterlegt"
    try:
        from license import LIZENZ_TYPEN
        td = LIZENZ_TYPEN.get(lizenztyp, {})
        label = td.get("label")
        if label:
            return label
    except Exception:
        pass
    return lizenztyp  # Fallback: rohen Key anzeigen


# ── Hauptseite ────────────────────────────────────────────────────────────────

def page_mein_vertrag() -> None:
    """Hauptseite: Mein Vertrag."""
    user = st.session_state.get("user", {})

    # verein_id für alle Rollen aus dem User-Objekt — vereine ist immer die Quelle
    verein_id: int | None = user.get("verein_id")
    # ist_verein steuert weiterhin die Anzeige von Kundentyp-Labels
    ist_verein = user.get("rolle") == "Vereinsadmin"

    st.title("📋 Mein Vertrag")

    if not verein_id:
        st.error("Kein Verein zugeordnet — Vertragsdaten können nicht geladen werden.")
        return

    data = _laden(user)
    if not data:
        st.error("Vertragsdaten konnten nicht geladen werden.")
        return

    # ── Paket- und Vertragsdaten ─────────────────────────────────────────────
    # Lizenztyp normalisieren (alt → neu), Preis und Intervall aus veriene-Zeile
    try:
        from license import normalize_lizenz_typ
        lizenztyp = normalize_lizenz_typ(
            data.get("lizenztyp"),
            ist_technischer_mandant=data.get("ist_technischer_mandant"),
        )
    except Exception:
        lizenztyp = data.get("lizenztyp") or "TRAINER_BASIC"

    lizenz_status = data.get("lizenz_status") or "unbekannt"
    abo_intervall = data.get("abo_intervall")            # 'monat' | 'jahr' | None
    sc, sl = _STATUS_BADGE.get(lizenz_status, ("#6e7681", lizenz_status.upper()))

    # ── Datumsfelder je nach Status ─────────────────────────────────────────
    # Trial:          subscription_current_period_end → "Erste Abbuchung am …"
    #                 (Fallback: testphase_bis → "Testphase endet am …")
    # Active:         subscription_current_period_end → "Nächste Verlängerung am …"
    # Cancelled:      gekuendigt_zum → "Vertragsende am …"
    datum_label: str | None = None
    datum_wert:  str | None = None

    if lizenz_status == "trial":
        cpe = _fmt_datum(data.get("subscription_current_period_end"))
        if cpe:
            datum_label = "Erste Abbuchung am"
            datum_wert  = cpe
        else:
            tpb = _fmt_datum(data.get("testphase_bis"))
            if tpb:
                datum_label = "Testphase endet am"
                datum_wert  = tpb

    elif lizenz_status == "active":
        cpe = _fmt_datum(data.get("subscription_current_period_end"))
        if cpe:
            datum_label = "Nächste Verlängerung am"
            datum_wert  = cpe

    elif lizenz_status == "cancelled":
        gkz = _fmt_datum(data.get("gekuendigt_zum"))
        if gkz:
            datum_label = "Vertragsende am"
            datum_wert  = gkz

    # ── Vertragsinformationen (read-only) ────────────────────────────────────
    st.markdown("### Vertragsinformationen")

    _feld("Kundennummer",       data.get("kundennummer"))
    _feld("Kundentyp",          "Verein" if ist_verein else "Trainer")
    _feld("Aktuelles Paket",    _lizenztyp_label(lizenztyp))
    _feld("Abrechnungsintervall", _intervall_label(abo_intervall))
    _feld("Paketpreis",         _preis_str(lizenztyp, abo_intervall))
    _feld("Vertragsbeginn",     _fmt_datum(data.get("vertragsbeginn")) or data.get("vertragsbeginn"))

    if datum_label and datum_wert:
        _feld(datum_label, datum_wert)

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
              _fmt_datum(data["kuendigung_eingegangen"])
              or (data["kuendigung_eingegangen"] or "")[:10])
        if data.get("gekuendigt_zum"):
            _feld("Vertrag endet am",
                  _fmt_datum(data["gekuendigt_zum"]) or data["gekuendigt_zum"])

    # ── Rechnungen & Zahlungen ───────────────────────────────────────────────
    # Sichtbar für: Vereinsadmin (ist_verein=True) und Einzeltrainer
    # (Trainer mit technischem Mandant, der eine eigene Lizenz hat).
    # Normaler Vereinstrainer (kein eigener Vertrag) sieht diesen Bereich nicht.
    _kann_rechnungen_sehen = (
        user.get("rolle") == "Vereinsadmin"
        or (user.get("rolle") == "Trainer" and data.get("ist_technischer_mandant"))
    )
    if _kann_rechnungen_sehen and verein_id:
        st.markdown("---")
        st.markdown("### 🧾 Rechnungen & Zahlungen")
        try:
            _rechnungen = rechnungen_laden(verein_id)
        except Exception:
            _rechnungen = []

        if not _rechnungen:
            st.info("Noch keine Rechnungen vorhanden.")
        else:
            _STATUS_COLOR = {
                "bezahlt":       ("#238636", "✅ Bezahlt"),
                "offen":         ("#d29922", "⏳ Offen"),
                "fehlgeschlagen":("#da3633", "❌ Fehlgeschlagen"),
                "storniert":     ("#6e7681", "🚫 Storniert"),
            }
            for _r in _rechnungen:
                _rn    = _r.get("rechnungsnummer") or "—"
                _dat   = _fmt_datum(_r.get("rechnungsdatum")) or _r.get("rechnungsdatum") or "—"
                _bet   = _r.get("betrag_eur")
                _bet_s = f"{float(_bet):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".") if _bet is not None else "—"
                _curr  = (_r.get("currency") or "EUR").upper()
                _paket = _r.get("lizenz_typ") or "—"
                _st    = _r.get("status") or "offen"
                _von   = _fmt_datum(_r.get("lizenz_von")) or _r.get("lizenz_von") or "—"
                _bis   = _fmt_datum(_r.get("lizenz_bis_r")) or _r.get("lizenz_bis_r") or "—"
                _url   = _r.get("hosted_invoice_url") or ""
                _pdf   = _r.get("invoice_pdf") or ""
                _sc, _sl = _STATUS_COLOR.get(_st, ("#6e7681", _st))

                st.markdown(
                    f'<div style="border:1px solid #30363d;border-radius:8px;'
                    f'padding:12px 16px;margin:6px 0;background:#161b22">'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">'
                    f'<div>'
                    f'<span style="font-weight:700;color:#e6edf3">{_rn}</span>'
                    f'&nbsp;<span style="color:#8b949e;font-size:13px">{_dat}</span>'
                    f'</div>'
                    f'<span style="background:{_sc}22;color:{_sc};border:1px solid {_sc}55;'
                    f'border-radius:12px;padding:2px 10px;font-size:11px;font-weight:700">{_sl}</span>'
                    f'</div>'
                    f'<div style="margin-top:6px;font-size:13px;color:#8b949e">'
                    f'Paket: <span style="color:#e6edf3">{_paket}</span>'
                    f' &nbsp;·&nbsp; Betrag: <span style="color:#e6edf3">{_bet_s} {_curr}</span>'
                    f' &nbsp;·&nbsp; Zeitraum: <span style="color:#e6edf3">{_von} – {_bis}</span>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                # Download-Buttons nur wenn URL vorhanden
                if _url or _pdf:
                    _bc1, _bc2, _ = st.columns([1, 1, 2])
                    if _url:
                        _bc1.link_button("🔗 Rechnung öffnen", _url, use_container_width=True)
                    if _pdf:
                        _bc2.link_button("📥 PDF herunterladen", _pdf, use_container_width=True)

    # ── Aktive Kündigung: Info + ggf. Widerruf ───────────────────────────────
    if data.get("kuendigung_eingegangen"):
        st.markdown("---")
        eingang  = (
            _fmt_datum(data.get("kuendigung_eingegangen"))
            or (data.get("kuendigung_eingegangen") or "")[:10]
        )
        vende    = (
            _fmt_datum(data.get("gekuendigt_zum"))
            or data.get("gekuendigt_zum")
            or "Beendigungsdatum wird noch bestätigt."
        )
        k_status = data.get("kuendigungsstatus") or ""

        if k_status in ("eingegangen", "vorgemerkt"):
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

            # ── Kündigungsstatus-Banner ──────────────────────────────────────
            if k_status == "vorgemerkt":
                _zugang_bis = (
                    _fmt_datum(data.get("gekuendigt_zum"))
                    or _fmt_datum(data.get("subscription_current_period_end"))
                    or "Periodenende"
                )
                st.warning(
                    f"**Kündigung vorgemerkt – Zugang bis {_zugang_bis}**\n\n"
                    "Dein Abo läuft bis zum Periodenende regulär weiter. "
                    "Du kannst die Kündigung noch zurücknehmen."
                )
            else:
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
                    # ── Stripe-Widerruf (wenn vorgemerkt via Stripe) ─────────
                    _wid_stripe_ok = True
                    if k_status == "vorgemerkt" and data.get("stripe_subscription_id"):
                        try:
                            from stripe_service import kuendigung_widerrufen_stripe
                            kuendigung_widerrufen_stripe(data["stripe_subscription_id"])
                        except Exception as _e:
                            _log.error("Stripe-Widerruf fehlgeschlagen: %s", _e)
                            st.error(
                                f"Die Kündigung konnte nicht bei Stripe zurückgenommen werden: {_e}\n\n"
                                "Bitte versuche es erneut oder kontaktiere support@aphsystem.de."
                            )
                            _wid_stripe_ok = False

                    if _wid_stripe_ok:
                        # Immer verein_id + ist_verein=True verwenden (Datenquelle: vereine)
                        ok, grund = kuendigung_widerrufen(verein_id, True)
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

    _kuendigung_flow(user, verein_id, ist_verein, data, lizenztyp)


# ── Kündigungsflow ────────────────────────────────────────────────────────────

def _kuendigung_flow(
    user: dict,
    verein_id: int,
    ist_verein: bool,
    data: dict,
    lizenztyp: str,
) -> None:
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

        lizenz_status = data.get("lizenz_status") or "—"
        abo_intervall = data.get("abo_intervall")

        # Nächstes Vertragsende für Anzeige im Bestätigungsschritt
        vertragsende_anzeige = (
            _fmt_datum(data.get("subscription_current_period_end"))
            or _fmt_datum(data.get("lizenz_bis"))
            or data.get("lizenz_bis")
            or "Nicht hinterlegt"
        )

        st.markdown(
            f"**Aktuelles Paket:** {_lizenztyp_label(lizenztyp)}  \n"
            f"**Vertragsstatus:** {lizenz_status}  \n"
            f"**Abrechnungsintervall:** {_intervall_label(abo_intervall)}  \n"
            f"**Vertragsende / Nächste Verlängerung:** {vertragsende_anzeige}"
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
            # ── Stripe-Kündigung vormerken (wenn Subscription vorhanden) ────
            stripe_sub_id = data.get("stripe_subscription_id")
            _stripe_ok = True
            _stripe_period_end: str | None = None
            _kuend_status = "eingegangen"  # Fallback: manuelle Lizenz

            if stripe_sub_id:
                try:
                    from stripe_service import kuendigung_vormerken
                    _sub = kuendigung_vormerken(stripe_sub_id)
                    import datetime as _dt_mv
                    _ts = _sub.get("current_period_end")
                    if _ts:
                        _stripe_period_end = _dt_mv.datetime.fromtimestamp(_ts).date().isoformat()
                    _kuend_status = "vorgemerkt"
                except Exception as _e:
                    _log.error("Stripe-Kündigung fehlgeschlagen: %s", _e)
                    st.error(
                        f"Die Kündigung konnte nicht bei Stripe vorgemerkt werden: {_e}\n\n"
                        "Bitte versuche es erneut oder kontaktiere support@aphsystem.de."
                    )
                    _stripe_ok = False
            else:
                # Kein Stripe-Abo — manuelle Lizenz, mit Hinweis fortfahren
                st.info(
                    "ℹ️ Diese Lizenz wird manuell verwaltet. "
                    "Deine Kündigung wird aufgezeichnet und vom Support bearbeitet."
                )

            if _stripe_ok:
                # Immer verein_id + True (Datenquelle: vereine für alle Rollen)
                ok, ergebnis = kuendigung_einreichen(
                    verein_id, True, grund,
                    kuendigungsstatus_override=_kuend_status,
                    cancel_at_period_end=bool(stripe_sub_id),
                    gekuendigt_zum=_stripe_period_end,
                )
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

        try:
            from license import normalize_lizenz_typ
            lt2 = normalize_lizenz_typ(
                data2.get("lizenztyp"),
                ist_technischer_mandant=data2.get("ist_technischer_mandant"),
            )
        except Exception:
            lt2 = data2.get("lizenztyp") or "—"

        # Priorität: gekuendigt_zum → subscription_current_period_end
        # → testphase_bis (nur bei Trial) → Fallback
        vende = (
            _fmt_datum(data2.get("gekuendigt_zum"))
            or _fmt_datum(data2.get("subscription_current_period_end"))
            or (
                _fmt_datum(data2.get("testphase_bis"))
                if data2.get("lizenz_status") == "trial"
                else None
            )
            or "Beendigungsdatum wird noch bestätigt."
        )

        st.success("✅ Kündigung erfolgreich übermittelt")
        st.markdown(
            f"**Eingangsdatum:** {datum}  \n"
            f"**Paket:** {_lizenztyp_label(lt2)}  \n"
            f"**Vertragsende:** {vende}  \n\n"
            "Eine Bestätigungs-E-Mail wurde an deine hinterlegte E-Mail-Adresse gesendet."
        )
        st.markdown("Bei Fragen: [support@aphsystem.de](mailto:support@aphsystem.de)")

        with st.expander("📄 Kündigungsbestätigung anzeigen"):
            st.markdown(
                f"**Kundennummer:** {data2.get('kundennummer') or '—'}  \n"
                f"**Kündigung eingegangen am:** "
                f"{_fmt_datum(data2.get('kuendigung_eingegangen')) or (data2.get('kuendigung_eingegangen') or '')[:10]}  \n"
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
    lizenztyp    = data.get("lizenztyp") or "—"
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
    lizenztyp    = data.get("lizenztyp") or "—"
    kundenname   = user.get("vorname") or user.get("name") or ""
    kundenemail  = user.get("email") or ""

    # Vertragsende: Priorität gekuendigt_zum → subscription_current_period_end
    # → testphase_bis (nur bei Trial) → Fallback
    vertragsende = (
        _fmt_datum(data.get("gekuendigt_zum"))
        or _fmt_datum(data.get("subscription_current_period_end"))
        or (
            _fmt_datum(data.get("testphase_bis"))
            if data.get("lizenz_status") == "trial"
            else None
        )
        or "Wird noch bestätigt"
    )

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
                vertragsende=vertragsende,
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
