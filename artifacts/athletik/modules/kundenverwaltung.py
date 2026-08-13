"""
Kundenverwaltung — Superadmin-Übersicht über alle Vereine und Trainer-Kunden.
Zeigt Stammdaten, Rechnungsadressen, Lizenzen und Vertragsdaten.
"""
from __future__ import annotations
import streamlit as st
from database import (
    kunden_liste_laden,
    kunde_vollstaendig_laden,
    rechnungsadresse_speichern,
    rechnungsadresse_laden,
    superadmin_email_aendern,
    superadmin_benutzername_aendern,
    vertragsfelder_setzen,
    trainer_vertrag_setzen,
    kundenstamm_aendern,
    benutzer_aktivieren,
    audit_log_eintragen,
    lizenz_setzen,
    trainer_lizenz_setzen,
    normalize_email,
    kuendigung_liste_laden,
    kuendigung_bestaetigen,
    kunde_zusammenfassung_laden,
    kunde_loeschen,
    db_backup_erstellen,
)
from license import LIZENZ_TYPEN, FEATURE_LABELS


_STATUS_LABELS = {
    "trial":     "🟡 Testphase",
    "active":    "🟢 Aktiv",
    "expired":   "🔴 Abgelaufen",
    "suspended": "⛔ Gesperrt",
    "cancelled": "🚫 Gekündigt",
    "unbekannt": "❓ Unbekannt",
}


def _sa_id() -> int | None:
    return st.session_state.get("user", {}).get("id")


def _badge(text: str, color: str = "#30363d") -> str:
    return (
        f'<span style="background:{color};color:#e6edf3;padding:2px 8px;'
        f'border-radius:4px;font-size:11px;font-weight:600">{text}</span>'
    )


def _kpis(kunden: list[dict]) -> None:
    total       = len(kunden)
    aktiv       = sum(1 for k in kunden if k["aktiv"])
    trainer     = sum(1 for k in kunden if k["kundentyp"] == "Trainer")
    vereine     = sum(1 for k in kunden if k["kundentyp"] == "Verein")
    unverif     = sum(1 for k in kunden if not k["email_verifiziert"])
    liz_aktiv   = sum(1 for k in kunden if k["lizenz_status"] == "active")
    liz_ab      = sum(1 for k in kunden if k["lizenz_status"] in ("expired", "suspended"))
    gekuendigt  = sum(1 for k in kunden if k["kuendigungsstatus"] != "aktiv")
    cols = st.columns(8)
    data = [
        ("Gesamtkunden",          total,      "#1f6feb"),
        ("Aktiv",                 aktiv,      "#238636"),
        ("Trainer",               trainer,    "#6e7681"),
        ("Vereine",               vereine,    "#6e7681"),
        ("E-Mail ausstehend",     unverif,    "#d29922"),
        ("Aktive Lizenzen",       liz_aktiv,  "#238636"),
        ("Abgelaufene Lizenzen",  liz_ab,     "#da3633"),
        ("Gekündigt",             gekuendigt, "#da3633"),
    ]
    for col, (label, val, color) in zip(cols, data):
        col.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;'
            f'padding:12px 8px;text-align:center">'
            f'<div style="font-size:22px;font-weight:700;color:{color}">{val}</div>'
            f'<div style="font-size:11px;color:#8b949e;margin-top:2px">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)


def _kunden_karte(k: dict) -> None:
    """
    Rendert eine responsive Kundenkarte.

    Desktop: horizontales Layout — Info links, Details-Button rechts.
    Navigation ausschließlich über st.button() — kein <a href> / kein Browser-Reload.
    """
    import html as _html

    kn    = k.get("kundennummer") or "—"
    typ   = k.get("kundentyp", "—")
    icon  = "🏢" if typ == "Verein" else "👤"
    vname = (k.get("vereinsname") or "").strip() if typ == "Verein" else ""
    ansp  = f"{k.get('vorname','') or ''} {k.get('nachname','') or ''}".strip() or "—"
    email = k.get("email") or "—"
    liz_raw = k.get("lizenz_status") or ""
    liz   = _STATUS_LABELS.get(liz_raw, liz_raw or "—")
    liz_cls = {"active": "active", "expired": "expired",
                "suspended": "suspended", "cancelled": "cancelled"}.get(liz_raw, "")
    paket = (k.get("lizenztyp") or "—").upper()
    ev    = "✅" if k.get("email_verifiziert") else "📧"
    ak    = "🟢" if k.get("aktiv") else "⛔"

    vid = k.get("verein_id") or 0
    bid = k.get("benutzer_id") or 0

    # HTML-Escaping aller kundenkontrollierten Werte
    kn_h    = _html.escape(kn)
    vname_h = _html.escape(vname)
    ansp_h  = _html.escape(ansp)
    email_h = _html.escape(email)
    liz_h   = _html.escape(liz)
    paket_h = _html.escape(paket)
    typ_h   = _html.escape(typ)

    vname_part = (
        f' <span class="aph-kc-vname">— {vname_h}</span>' if vname_h else ""
    )
    liz_chip = (
        f'<span class="aph-kc-chip aph-kc-chip-{liz_cls}">{liz_h}</span>'
        if liz_cls else
        f'<span class="aph-kc-chip">{liz_h}</span>'
    )

    # Karten-Info als reines <div> — kein <a href>, kein Overlay
    info_col, btn_col = st.columns([5, 1])
    with info_col:
        st.markdown(
            f'<div class="aph-kunden-karte" style="cursor:default">'
            f'  <div class="aph-kunden-info">'
            f'    <div class="aph-kc-header">'
            f'      <strong class="aph-kc-kn">{icon} {kn_h}</strong>'
            f'      {vname_part}'
            f'      <span class="aph-kc-chip">{typ_h}</span>'
            f'    </div>'
            f'    <div class="aph-kc-sub">{ansp_h} · {email_h}</div>'
            f'    <div class="aph-kc-meta">'
            f'      <span class="aph-kc-chip">{paket_h}</span>'
            f'      {liz_chip}'
            f'      <span style="color:#8b949e;font-size:11px">{ev} {ak}</span>'
            f'    </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with btn_col:
        # Eindeutiger Key pro Kunden-Kombination — kein doppelter Widget-Key
        if st.button("🔍 Details →", key=f"kd_details_{vid}_{bid}",
                     use_container_width=True):
            _vid_sel = int(vid) or None
            _bid_sel = int(bid) or None
            st.session_state["kunden_auswahl"] = (_vid_sel, _bid_sel)
            # _nav_goto-Pattern: vor Widget-Erstellung konsumiert → kein StreamlitAPIException
            st.session_state["_nav_goto"] = "👥  Kundenverwaltung"
            st.rerun()


def _detail_a_kundenkonto(daten: dict) -> None:
    """Section A: Kundenkonto — Stammdaten + Account-Status."""
    b = daten.get("benutzer") or {}
    v = daten.get("verein") or {}
    kundentyp = "Verein" if v else "Trainer"

    with st.expander("**A — Kundenkonto**", expanded=True):
        c1, c2 = st.columns(2)
        c1.markdown(f"**Kundennummer:** `{v.get('kundennummer') or b.get('kundennummer') or '—'}`")
        c2.markdown(f"**Kundentyp:** {kundentyp}")
        if kundentyp == "Verein":
            c1.markdown(f"**Vereinsname:** {v.get('name','—')}")
            c2.markdown(f"**Ansprechpartner:** {b.get('vorname','')} {b.get('nachname','')}")
        else:
            c1.markdown(f"**Name:** {b.get('vorname','')} {b.get('nachname','')}")
        c1.markdown(f"**Benutzername:** `{b.get('benutzername') or '—'}`")
        c2.markdown(f"**E-Mail:** {b.get('email','—')}")
        ev = "✅ Bestätigt" if b.get("email_verifiziert") else "❌ Ausstehend"
        c1.markdown(f"**E-Mail-Status:** {ev}")
        c2.markdown(f"**Telefon:** {b.get('telefon') or v.get('telefon') or '—'}")
        c1.markdown(f"**Registriert am:** {b.get('erstellt_am','—')}")
        c2.markdown(f"**Letzter Login:** {b.get('letzter_login','—')}")
        c1.markdown(f"**Account:** {'🟢 Aktiv' if b.get('aktiv') else '⛔ Deaktiviert'}")

        # ── DSGVO-Zustimmung (nur lesen) ─────────────────────────────────────
        _ds_ok  = bool(b.get("datenschutz_akzeptiert"))
        _agb_ok = bool(b.get("agb_akzeptiert"))
        if _ds_ok or _agb_ok:
            st.markdown("---")
            st.markdown("**📋 Rechtliche Zustimmungen**")
            zc1, zc2 = st.columns(2)
            if _ds_ok:
                zc1.markdown(
                    f"**Datenschutz:** ✅ akzeptiert am "
                    f"{b.get('datenschutz_akzeptiert_am','—')[:10]}  \n"
                    f"Version: `{b.get('datenschutz_version','—')}`"
                )
            else:
                zc1.markdown("**Datenschutz:** ❌ keine Zustimmung (Altdaten)")
            if _agb_ok:
                zc2.markdown(
                    f"**AGB:** ✅ akzeptiert am "
                    f"{b.get('agb_akzeptiert_am','—')[:10]}  \n"
                    f"Version: `{b.get('agb_version','—')}`"
                )
            else:
                zc2.markdown("**AGB:** ❌ keine Zustimmung (Altdaten)")

        unvollstaendig = not b.get("email") or (kundentyp == "Verein" and not v.get("name"))
        if unvollstaendig:
            st.warning("⚠️ Stammdaten unvollständig")

        st.markdown("---")
        st.markdown("**✏️ Stammdaten bearbeiten**")
        ec1, ec2 = st.columns(2)
        e_vn   = ec1.text_input("Vorname",   value=b.get("vorname",""),  key=f"ekd_vn_{b.get('id')}")
        e_nn   = ec2.text_input("Nachname",  value=b.get("nachname",""), key=f"ekd_nn_{b.get('id')}")
        e_tel  = ec1.text_input("Telefon",   value=b.get("telefon") or v.get("telefon") or "",
                                key=f"ekd_tel_{b.get('id')}")
        if kundentyp == "Verein":
            e_vname = ec2.text_input("Vereinsname", value=v.get("name",""), key=f"ekd_vname_{b.get('id')}")
            e_ansp  = ec1.text_input("Ansprechpartner (Nachname + Vorname getrennt)",
                                     value=v.get("ansprechpartner",""), key=f"ekd_ansp_{b.get('id')}")
        e_aktiv = st.checkbox("Konto aktiv", value=bool(b.get("aktiv")), key=f"ekd_ak_{b.get('id')}")

        if st.button("💾 Stammdaten speichern", key=f"ekd_save_{b.get('id')}"):
            kundenstamm_aendern(
                b["id"], v.get("id"),
                vorname=e_vn.strip() or None,
                nachname=e_nn.strip() or None,
                telefon=e_tel.strip() or None,
                vereinsname=e_vname.strip() if kundentyp == "Verein" else None,
                ansprechpartner=e_ansp.strip() if kundentyp == "Verein" else None,
                aktiv=1 if e_aktiv else 0,
                superadmin_id=_sa_id(),
            )
            benutzer_aktivieren(b["id"], 1 if e_aktiv else 0)
            audit_log_eintragen(b["id"], "account_status_geaendert",
                                f"aktiv={'1' if e_aktiv else '0'}", _sa_id())
            st.success("✅ Gespeichert.")
            st.rerun()

        st.markdown("---")
        st.markdown("**⚡ Account-Status**")
        _ist_aktiv = bool(b.get("aktiv"))
        if _ist_aktiv:
            st.success("🟢 Konto ist aktiv — Kunde kann sich einloggen.")
            if st.button("🔴 Account deaktivieren", key=f"deakt_btn_{b.get('id')}", type="secondary"):
                st.session_state[f"_deakt_confirm_{b.get('id')}"] = True
            if st.session_state.get(f"_deakt_confirm_{b.get('id')}"):
                st.warning(
                    "⚠️ Möchtest du den Zugang dieses Kunden wirklich deaktivieren? "
                    "Der Login wird blockiert. Alle Daten bleiben vollständig erhalten."
                )
                _dc1, _dc2 = st.columns(2)
                if _dc1.button("✅ Ja, deaktivieren", key=f"deakt_ja_{b.get('id')}", type="primary"):
                    kundenstamm_aendern(b["id"], v.get("id"), aktiv=0, superadmin_id=_sa_id())
                    benutzer_aktivieren(b["id"], 0)
                    audit_log_eintragen(b["id"], "konto_deaktiviert",
                                        "Superadmin hat Konto deaktiviert", _sa_id())
                    st.session_state.pop(f"_deakt_confirm_{b.get('id')}", None)
                    st.success("⛔ Konto deaktiviert.")
                    st.rerun()
                if _dc2.button("❌ Abbrechen", key=f"deakt_nein_{b.get('id')}"):
                    st.session_state.pop(f"_deakt_confirm_{b.get('id')}", None)
                    st.rerun()
        else:
            st.warning("⛔ Konto ist deaktiviert — Login blockiert.")
            if st.button("🟢 Account aktivieren", key=f"akt_btn_{b.get('id')}", type="primary"):
                st.session_state[f"_akt_confirm_{b.get('id')}"] = True
            if st.session_state.get(f"_akt_confirm_{b.get('id')}"):
                st.info("Möchtest du diesen Account reaktivieren? Der Kunde kann sich danach wieder einloggen.")
                _ac1, _ac2 = st.columns(2)
                if _ac1.button("✅ Ja, aktivieren", key=f"akt_ja_{b.get('id')}", type="primary"):
                    kundenstamm_aendern(b["id"], v.get("id"), aktiv=1, superadmin_id=_sa_id())
                    benutzer_aktivieren(b["id"], 1)
                    audit_log_eintragen(b["id"], "konto_aktiviert",
                                        "Superadmin hat Konto reaktiviert", _sa_id())
                    st.session_state.pop(f"_akt_confirm_{b.get('id')}", None)
                    st.success("✅ Konto aktiviert.")
                    st.rerun()
                if _ac2.button("❌ Abbrechen", key=f"akt_nein_{b.get('id')}"):
                    st.session_state.pop(f"_akt_confirm_{b.get('id')}", None)
                    st.rerun()

        st.markdown("---")
        st.markdown("**🔑 E-Mail-Adresse ändern**")
        ec3, ec4 = st.columns(2)
        e_email_neu = ec3.text_input("Neue E-Mail-Adresse", key=f"ekd_email_{b.get('id')}",
                                     placeholder="neu@verein.de")
        if ec4.button("✉️ E-Mail ändern + Verifikation senden", key=f"ekd_email_save_{b.get('id')}"):
            if not e_email_neu.strip() or "@" not in e_email_neu:
                st.error("Bitte gültige E-Mail-Adresse eingeben.")
            else:
                try:
                    import os as _os_ev
                    _token = superadmin_email_aendern(b["id"], e_email_neu.strip(), _sa_id())
                    _base = _os_ev.environ.get("APP_BASE_URL") or (
                        f"https://{_os_ev.environ.get('REPLIT_DEV_DOMAIN','localhost')}/athletik/app"
                    )
                    try:
                        from email_service import send_verification_email as _sve
                        _sve(normalize_email(e_email_neu.strip()), b.get("vorname","Kunde"),
                             _token, _base)
                        st.success("✅ E-Mail geändert — Bestätigungsmail gesendet.")
                    except Exception as _ee:
                        st.success("✅ E-Mail geändert (E-Mail-Versand ausstehend).")
                    st.rerun()
                except ValueError as _ve:
                    st.error(str(_ve))

        st.markdown("**👤 Benutzername ändern**")
        ec5, ec6 = st.columns(2)
        e_uname = ec5.text_input("Neuer Benutzername", key=f"ekd_uname_{b.get('id')}",
                                  value=b.get("benutzername") or "")
        if ec6.button("✅ Benutzername speichern", key=f"ekd_uname_save_{b.get('id')}"):
            if not e_uname.strip():
                st.error("Benutzername darf nicht leer sein.")
            else:
                try:
                    superadmin_benutzername_aendern(b["id"], e_uname.strip(), _sa_id())
                    st.success("✅ Benutzername geändert.")
                    st.rerun()
                except ValueError as _ve:
                    st.error(str(_ve))


def _detail_b_rechnungsadresse(daten: dict) -> None:
    """Section B: Rechnungsadresse — ansehen + bearbeiten."""
    b  = daten.get("benutzer") or {}
    ra = daten.get("rechnungsadresse") or {}

    with st.expander("**B — Rechnungsadresse**", expanded=False):
        if ra:
            c1, c2 = st.columns(2)
            c1.markdown(f"**Firma/Verein:** {ra.get('firma') or '—'}")
            c2.markdown(f"**USt-ID:** {ra.get('ust_id') or '—'}")
            c1.markdown(f"**Vorname:** {ra.get('vorname','—')}")
            c2.markdown(f"**Nachname:** {ra.get('nachname','—')}")
            c1.markdown(f"**Straße + Nr:** {ra.get('strasse','—')} {ra.get('hausnummer','')}")
            c2.markdown(f"**PLZ / Ort:** {ra.get('plz','—')} {ra.get('ort','—')}")
            c1.markdown(f"**Land:** {ra.get('land','—')}")
            c2.markdown(f"**Rechnungs-E-Mail:** {ra.get('rechnung_email','—')}")
            c1.markdown(f"**Telefon:** {ra.get('telefon') or '—'}")
        else:
            st.warning("⚠️ Keine Rechnungsadresse hinterlegt.")

        st.markdown("---")
        st.markdown("**✏️ Rechnungsadresse bearbeiten**")
        rb1, rb2 = st.columns(2)
        f_firma   = rb1.text_input("Firma/Verein (optional)", key=f"ra_firma_{b.get('id')}",
                                    value=ra.get("firma") or "")
        f_tel     = rb2.text_input("Telefon (optional)",      key=f"ra_tel_{b.get('id')}",
                                    value=ra.get("telefon") or "")
        rb3, rb4 = st.columns(2)
        f_vn      = rb3.text_input("Vorname *",   key=f"ra_vn_{b.get('id')}",
                                    value=ra.get("vorname") or "")
        f_nn      = rb4.text_input("Nachname *",  key=f"ra_nn_{b.get('id')}",
                                    value=ra.get("nachname") or "")
        rb5, rb6 = st.columns([3,1])
        f_str     = rb5.text_input("Straße *",    key=f"ra_str_{b.get('id')}",
                                    value=ra.get("strasse") or "")
        f_hnr     = rb6.text_input("Nr. *",       key=f"ra_hnr_{b.get('id')}",
                                    value=ra.get("hausnummer") or "")
        rb7, rb8 = st.columns([1,2])
        f_plz     = rb7.text_input("PLZ *",       key=f"ra_plz_{b.get('id')}",
                                    value=ra.get("plz") or "")
        f_ort     = rb8.text_input("Ort *",       key=f"ra_ort_{b.get('id')}",
                                    value=ra.get("ort") or "")
        rb9, rb10 = st.columns(2)
        f_land    = rb9.text_input("Land *",      key=f"ra_land_{b.get('id')}",
                                    value=ra.get("land") or "Deutschland")
        f_remail  = rb10.text_input("Rechnungs-E-Mail *", key=f"ra_remail_{b.get('id')}",
                                     value=ra.get("rechnung_email") or "")
        f_ustid   = st.text_input("Umsatzsteuer-ID (optional)", key=f"ra_ustid_{b.get('id')}",
                                   value=ra.get("ust_id") or "")

        if st.button("💾 Rechnungsadresse speichern", key=f"ra_save_{b.get('id')}"):
            pflicht = [f_vn, f_nn, f_str, f_hnr, f_plz, f_ort, f_land, f_remail]
            if any(not v.strip() for v in pflicht):
                st.error("Bitte alle Pflichtfelder (*) ausfüllen.")
            else:
                _bestaetigt = st.session_state.get(f"ra_bestaetigt_{b.get('id')}", False)
                if not _bestaetigt:
                    st.session_state[f"ra_bestaetigt_{b.get('id')}"] = True
                    st.warning("⚠️ **Rechnungsdaten wirklich ändern?** Nochmals speichern zum Bestätigen.")
                else:
                    rechnungsadresse_speichern(
                        b["id"],
                        firma=f_firma.strip() or None,
                        vorname=f_vn.strip(),
                        nachname=f_nn.strip(),
                        strasse=f_str.strip(),
                        hausnummer=f_hnr.strip(),
                        plz=f_plz.strip(),
                        ort=f_ort.strip(),
                        land=f_land.strip(),
                        rechnung_email=f_remail.strip(),
                        telefon=f_tel.strip() or None,
                        ust_id=f_ustid.strip() or None,
                    )
                    audit_log_eintragen(b["id"], "rechnungsadresse_geaendert",
                                        "", _sa_id())
                    st.session_state.pop(f"ra_bestaetigt_{b.get('id')}", None)
                    st.success("✅ Rechnungsadresse gespeichert.")
                    st.rerun()


def _detail_c_lizenz(daten: dict) -> None:
    """Section C: Lizenz/Paket — für Verein UND Trainer.
    Vereine: Daten aus vereine-Tabelle, schreibt via lizenz_setzen().
    Trainer: Daten aus benutzer-Tabelle, schreibt via trainer_lizenz_setzen().
    Bestehende Pakete aus license.py; keine Pakete/Preise verändern."""
    b = daten.get("benutzer") or {}
    v = daten.get("verein") or {}
    ist_verein = bool(v)

    # Einheitliche Datenquelle: Verein → v-Dict, Trainer → b-Dict
    src        = v if ist_verein else b
    entity_id  = v["id"] if ist_verein else b["id"]   # verein_id oder benutzer_id
    key_pfx    = f"v{entity_id}" if ist_verein else f"b{entity_id}"

    lizenztyp  = (src.get("lizenztyp") or "BASIC").upper()
    liz_status = src.get("lizenz_status") or "trial"
    liz_bis    = src.get("lizenz_bis") or "—"
    testphase  = src.get("testphase_bis") or "—"
    paket_def  = LIZENZ_TYPEN.get(lizenztyp, LIZENZ_TYPEN.get("BASIC", {}))

    with st.expander("**C — Lizenz / Paket**", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.metric("Paket",         paket_def.get("label", lizenztyp))
        c2.metric("Lizenzstatus",  _STATUS_LABELS.get(liz_status, liz_status))
        c3.metric("Lizenz bis",    liz_bis)

        if ist_verein:
            # Nutzungszähler nur für Vereinskunden sinnvoll
            from database import get_conn as _gc
            with _gc() as _conn:
                spieler_anz = _conn.execute(
                    "SELECT COUNT(*) FROM spieler WHERE verein_id=?", (entity_id,)
                ).fetchone()[0]
                trainer_anz = _conn.execute(
                    "SELECT COUNT(*) FROM benutzer WHERE verein_id=? AND aktiv=1", (entity_id,)
                ).fetchone()[0]
            c1.metric("Spieler",   f"{spieler_anz} / {paket_def.get('max_spieler','∞')}")
            c2.metric("Trainer",   f"{trainer_anz} / {paket_def.get('max_trainer','∞')}")
            c3.metric("Testphase bis", testphase)
        else:
            c3.metric("Testphase bis", testphase)
            st.caption("ℹ️ Trainer-Konto ohne Vereinsstruktur — Spieler-/Trainer-Limits entfallen.")

        # Preis & Abrechnung aus bestehenden Paketen (unveränderlich)
        if paket_def:
            st.markdown(
                f"**Preis:** {paket_def.get('preis_monat',0):.2f} € / Monat &nbsp;|&nbsp; "
                f"{paket_def.get('preis_jahr',0):.2f} € / Jahr"
            )

        st.markdown("---")
        paket_optionen = list(LIZENZ_TYPEN.keys())
        cur_idx = paket_optionen.index(lizenztyp) if lizenztyp in paket_optionen else 0

        if lizenztyp not in paket_optionen:
            st.info("⚠️ Noch kein Paket zugewiesen — bitte Paket auswählen und speichern.")
            st.markdown("**📦 Paket zuweisen**")
        else:
            st.markdown("**🔄 Paketwechsel (nur zwischen bestehenden Paketen)**")

        neues_paket = st.selectbox(
            "Paket", paket_optionen, index=cur_idx,
            format_func=lambda x: f"{x} — {LIZENZ_TYPEN[x]['label']}",
            key=f"liz_paket_{key_pfx}",
        )
        neuer_status = st.selectbox(
            "Lizenzstatus",
            ["trial", "active", "expired", "suspended", "cancelled"],
            index=(["trial","active","expired","suspended","cancelled"].index(liz_status)
                   if liz_status in ["trial","active","expired","suspended","cancelled"] else 0),
            format_func=lambda x: _STATUS_LABELS.get(x, x),
            key=f"liz_status_{key_pfx}",
        )
        lc1, lc2 = st.columns(2)
        neue_liz_bis  = lc1.text_input("Lizenz bis (YYYY-MM-DD)",
                                        value=src.get("lizenz_bis") or "",
                                        key=f"liz_bis_{key_pfx}")
        neue_test_bis = lc2.text_input("Testphase bis (YYYY-MM-DD)",
                                        value=src.get("testphase_bis") or "",
                                        key=f"liz_test_{key_pfx}")

        if st.button("💾 Lizenz / Paket speichern", key=f"liz_save_{key_pfx}"):
            _pk_key = f"liz_bestaetigt_{key_pfx}"
            if neues_paket != lizenztyp and lizenztyp in paket_optionen and not st.session_state.get(_pk_key):
                st.session_state[_pk_key] = True
                st.warning(
                    f"⚠️ **Paket wirklich von {lizenztyp} auf {neues_paket} ändern?**"
                    " Nochmals speichern zum Bestätigen."
                )
            elif lizenztyp not in paket_optionen and not st.session_state.get(_pk_key):
                # Erstmalige Zuweisung — einmalige Bestätigung
                st.session_state[_pk_key] = True
                st.warning(
                    f"⚠️ **Paket {neues_paket} wirklich diesem Kunden zuweisen?**"
                    " Nochmals speichern zum Bestätigen."
                )
            else:
                if ist_verein:
                    lizenz_setzen(entity_id, neues_paket, neuer_status,
                                  neue_liz_bis.strip() or None,
                                  neue_test_bis.strip() or None)
                else:
                    trainer_lizenz_setzen(entity_id, neues_paket, neuer_status,
                                          neue_liz_bis.strip() or None,
                                          neue_test_bis.strip() or None)
                audit_log_eintragen(
                    b.get("id"), "paket_geaendert",
                    f"{lizenztyp} → {neues_paket} status={neuer_status}", _sa_id(),
                )
                st.session_state.pop(_pk_key, None)
                st.success("✅ Lizenz gespeichert.")
                st.rerun()


def _detail_d_vertrag(daten: dict) -> None:
    """Section D: Vertragsdaten — für Verein UND Trainer.
    Vereine: schreibt via vertragsfelder_setzen().
    Trainer: schreibt via trainer_vertrag_setzen()."""
    b = daten.get("benutzer") or {}
    v = daten.get("verein") or {}
    ist_verein = bool(v)

    src       = v if ist_verein else b
    entity_id = v["id"] if ist_verein else b["id"]
    key_pfx   = f"v{entity_id}" if ist_verein else f"b{entity_id}"

    with st.expander("**D — Vertrag**", expanded=False):
        c1, c2 = st.columns(2)
        c1.markdown(f"**Vertragsstatus:** {src.get('kuendigungsstatus','aktiv') or 'aktiv'}")
        c2.markdown(f"**Vertragsbeginn:** {src.get('vertragsbeginn','—') or '—'}")
        c1.markdown(f"**Vertragsende:** {src.get('vertragsende','—') or '—'}")
        c2.markdown(f"**Kündigung eingegangen:** {src.get('kuendigung_eingegangen','—') or '—'}")
        c1.markdown(f"**Gekündigt zum:** {src.get('gekuendigt_zum','—') or '—'}")

        st.markdown("---")
        st.markdown("**✏️ Vertragsdaten bearbeiten**")
        vc1, vc2 = st.columns(2)
        e_vbeg  = vc1.text_input("Vertragsbeginn (YYYY-MM-DD)",
                                  value=src.get("vertragsbeginn") or "",
                                  key=f"vt_beg_{key_pfx}")
        e_vend  = vc2.text_input("Vertragsende (YYYY-MM-DD)",
                                  value=src.get("vertragsende") or "",
                                  key=f"vt_end_{key_pfx}")
        e_keing = vc1.text_input("Kündigung eingegangen (YYYY-MM-DD)",
                                  value=src.get("kuendigung_eingegangen") or "",
                                  key=f"vt_kein_{key_pfx}")
        e_kzum  = vc2.text_input("Gekündigt zum (YYYY-MM-DD)",
                                  value=src.get("gekuendigt_zum") or "",
                                  key=f"vt_kzum_{key_pfx}")
        kstatus_opts = ["aktiv", "Kündigung eingegangen", "gekündigt"]
        cur_ks  = src.get("kuendigungsstatus", "aktiv") or "aktiv"
        e_kstat = st.selectbox("Kündigungsstatus", kstatus_opts,
                                index=kstatus_opts.index(cur_ks) if cur_ks in kstatus_opts else 0,
                                key=f"vt_kstat_{key_pfx}")

        if st.button("💾 Vertragsdaten speichern", key=f"vt_save_{key_pfx}"):
            if ist_verein:
                vertragsfelder_setzen(
                    entity_id,
                    vertragsbeginn=e_vbeg.strip() or None,
                    vertragsende=e_vend.strip() or None,
                    kuendigung_eingegangen=e_keing.strip() or None,
                    gekuendigt_zum=e_kzum.strip() or None,
                    kuendigungsstatus=e_kstat,
                    superadmin_id=_sa_id(),
                )
            else:
                trainer_vertrag_setzen(
                    entity_id,
                    vertragsbeginn=e_vbeg.strip() or None,
                    vertragsende=e_vend.strip() or None,
                    kuendigung_eingegangen=e_keing.strip() or None,
                    gekuendigt_zum=e_kzum.strip() or None,
                    kuendigungsstatus=e_kstat,
                    superadmin_id=_sa_id(),
                )
            st.success("✅ Vertragsdaten gespeichert.")
            st.rerun()


def _detail_audit(daten: dict) -> None:
    """Audit-Verlauf der letzten 20 Änderungen."""
    audit = daten.get("audit") or []
    with st.expander(f"**🔍 Änderungshistorie** ({len(audit)} Einträge)", expanded=False):
        if not audit:
            st.info("Noch keine Änderungen protokolliert.")
        else:
            for a in audit:
                sa_name = f"{a.get('sa_vorname','')} {a.get('sa_nachname','')}".strip() or "System"
                st.markdown(
                    f"**{a.get('erstellt_am','—')}** — `{a.get('aktion','—')}`"
                    f"  _{a.get('details','')}_  *(Superadmin: {sa_name})*"
                )


def _detail_gefahrenbereich(daten: dict) -> None:
    """
    Gefahrenbereich — endgültige Kundenlöschung (Superadmin only).
    Zweistufige Bestätigung: Datenübersicht → Kundennummer-Eingabe → Löschen.
    Rechnungsdaten werden anonymisiert, nicht gelöscht (Aufbewahrungspflicht).

    FIX: st.expander ohne key verliert seinen Öffnungszustand beim Rerun und klappt zu.
    Lösung: key + expanded-State aus session_state + explizites st.rerun() nach Datenladen.
    """
    b   = daten.get("benutzer") or {}
    v   = daten.get("verein") or {}
    bid = b.get("id")
    vid = v.get("id")
    kn  = v.get("kundennummer") or b.get("kundennummer") or "—"
    name_str = (
        v.get("name")
        or f"{b.get('vorname','') or ''} {b.get('nachname','') or ''}".strip()
        or "—"
    )
    current_sa_id = _sa_id()
    if not bid:
        return

    # Expander bleibt offen, sobald Vorschaudaten geladen sind
    _preview_key  = f"_lz_{bid}"
    _has_preview  = _preview_key in st.session_state
    _deleted_key  = f"_lz_deleted_{bid}"

    # Expander key stabilisiert den Öffnungszustand über Reruns hinweg
    with st.expander(
        "☠️ **Gefahrenbereich — Endgültige Löschung**",
        expanded=_has_preview,
        # key= param erst ab Streamlit 1.32 — ältere Versionen ignorieren ihn,
        # daher wird expanded=_has_preview als primärer Stabilisator genutzt.
    ):
        # Eigenes Konto schützen
        if current_sa_id and current_sa_id == bid:
            st.error("🔒 Das aktuell verwendete Superadmin-Konto kann nicht gelöscht werden.")
            return

        st.markdown(
            '<div style="border:1px solid #f85149;border-radius:8px;padding:12px 14px;'
            'background:rgba(248,81,73,0.07);margin-bottom:14px">'
            '<b style="color:#f85149">⚠️ Achtung: Dieser Bereich enthält irreversible Aktionen.</b><br>'
            'Das endgültige Löschen entfernt <b>alle Spieler- und Testdaten</b> dauerhaft. '
            'Rechnungsdaten werden aus gesetzlichen Gründen anonymisiert aufbewahrt, nicht gelöscht. '
            'Nur Superadmin darf diese Aktion ausführen.</div>',
            unsafe_allow_html=True,
        )

        # ── Schritt 1: Datenübersicht laden ─────────────────────────────────
        # Kein href, kein nav_section-Wechsel — nur session_state + st.rerun()
        if st.button("🔍 Betroffene Daten prüfen", key=f"_lz_start_{bid}", type="secondary"):
            try:
                zs = kunde_zusammenfassung_laden(vid, bid)
                st.session_state[_preview_key] = zs
            except Exception as _ex:
                st.error(f"Fehler beim Laden der Zusammenfassung: {_ex}")
                return
            st.rerun()  # Seite neu laden — Vorschau wird sichtbar, kein Nav-Wechsel

        zs = st.session_state.get(_preview_key)
        if zs is None:
            return  # Noch keine Vorschau geladen — Seite bleibt auf Kundendetail

        # ── Vorschau: Betroffene Datenbereiche ──────────────────────────────
        st.markdown("---")
        st.markdown("**📋 Betroffene Daten dieses Kunden**")

        # Kopfzeile
        st.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;border-radius:6px;'
            f'padding:8px 12px;margin:8px 0;font-size:13px">'
            f'<b>Kundennummer:</b> <code>{kn}</code> &nbsp;·&nbsp; '
            f'<b>Name/Verein:</b> {name_str} &nbsp;·&nbsp; '
            f'<b>E-Mail:</b> {b.get("email","—")}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Zähler-Reihe
        _mc = st.columns(4)
        _mc[0].metric("Spieler",           zs.get("n_spieler", 0))
        _mc[1].metric("Testdatensätze",    zs.get("n_tests", 0))
        _mc[2].metric("Trainingspläne",    zs.get("n_plaene", 0))
        _mc[3].metric("TP-Einträge",       zs.get("n_tp_eintraege", 0))

        # Detailierte Bereichstabelle
        def _row(bereich: str, anzahl: int, status: str) -> str:
            farbe = {
                "wird gelöscht":            "#f85149",
                "wird anonymisiert":        "#d29922",
                "bleibt (Aufbewahrung)":    "#3fb950",
                "nicht vorhanden":          "#8b949e",
            }.get(status, "#8b949e")
            return (
                f'<tr>'
                f'<td style="padding:4px 10px;color:#e6edf3">{bereich}</td>'
                f'<td style="padding:4px 10px;text-align:right;color:#e6edf3">{anzahl if anzahl > 0 else "–"}</td>'
                f'<td style="padding:4px 10px;color:{farbe};font-size:12px">{status}</td>'
                f'</tr>'
            )

        _n_sp   = zs.get("n_spieler", 0)
        _n_ts   = zs.get("n_tests", 0)
        _n_pl   = zs.get("n_plaene", 0)
        _n_tp   = zs.get("n_tp_eintraege", 0)
        _n_rech = zs.get("n_rechnungsadressen", 0)
        _n_ses  = zs.get("n_sessions", 0)
        _n_aud  = zs.get("n_audit_eintraege", 0)
        _n_nb   = zs.get("n_benachrichtigungen", 0)
        _n_pt   = zs.get("n_push_tokens", 0)
        _n_bu   = zs.get("n_benutzerkonten", 0)
        _logo   = zs.get("logo_vorhanden", False)
        _vs     = zs.get("vertragsstatus", "—")

        st.markdown(
            '<table style="width:100%;border-collapse:collapse;background:#0d1117;'
            'border:1px solid #30363d;border-radius:6px;font-size:13px">'
            '<thead><tr>'
            '<th style="padding:6px 10px;text-align:left;color:#8b949e;border-bottom:1px solid #30363d">Datenbereich</th>'
            '<th style="padding:6px 10px;text-align:right;color:#8b949e;border-bottom:1px solid #30363d">Anzahl</th>'
            '<th style="padding:6px 10px;text-align:left;color:#8b949e;border-bottom:1px solid #30363d">Aktion</th>'
            '</tr></thead><tbody>'
            + _row("Benutzerkonto(en)",         _n_bu,   "wird gelöscht")
            + _row("Spieler (inkl. Diagnostik)",_n_sp,   "wird gelöscht" if _n_sp > 0 else "nicht vorhanden")
            + _row("Testdatensätze",            _n_ts,   "wird gelöscht" if _n_ts > 0 else "nicht vorhanden")
            + _row("Trainingsplan-Versionen",   _n_pl,   "wird gelöscht" if _n_pl > 0 else "nicht vorhanden")
            + _row("Trainingsplan-Einträge",    _n_tp,   "wird gelöscht" if _n_tp > 0 else "nicht vorhanden")
            + _row("Aktive Sessions",           _n_ses,  "wird gelöscht" if _n_ses > 0 else "nicht vorhanden")
            + _row("Push-Tokens",               _n_pt,   "wird gelöscht" if _n_pt > 0 else "nicht vorhanden")
            + _row("Benachrichtigungen",        _n_nb,   "wird gelöscht" if _n_nb > 0 else "nicht vorhanden")
            + _row("Logo / Profilbild",         1 if _logo else 0,
                   "wird gelöscht" if _logo else "nicht vorhanden")
            + _row("Rechnungsadresse",          _n_rech, "wird anonymisiert" if _n_rech > 0 else "nicht vorhanden")
            + _row(f"Lizenz/Paket ({_vs})",     1,       "wird gelöscht")
            + _row("Audit-Log (Einträge)",      _n_aud,  "bleibt (Aufbewahrung)")
            + '</tbody></table>',
            unsafe_allow_html=True,
        )

        st.error(
            "⚠️ **Achtung:** Dieser Vorgang ist **nicht rückgängig zu machen**. "
            "Alle Spieler- und Testdaten werden endgültig entfernt. "
            "Rechnungsdaten werden aus gesetzlichen Gründen anonymisiert — nicht gelöscht."
        )

        # ── Schritt 2: Zweite Bestätigung — Kundennummer eintippen ──────────
        st.markdown("---")
        st.markdown("**🔑 Zweite Bestätigung erforderlich**")
        st.caption(
            f"Gib die Kundennummer **`{kn}`** exakt ein, um die Löschung freizuschalten:"
        )
        _bestaetigung = st.text_input(
            "Kundennummer zur Bestätigung",
            key=f"_lz_confirm_{bid}",
            placeholder=kn,
            label_visibility="collapsed",
        )

        if _bestaetigung.strip() and _bestaetigung.strip() == kn.strip():
            st.error("☠️ Bestätigung akzeptiert. Der nächste Klick löscht diesen Kunden **endgültig**.")
            if st.button(
                "🗑️ Kunde endgültig und unwiderruflich löschen",
                key=f"_lz_execute_{bid}",
                type="primary",
            ):
                # Backup-Versuch vor der Löschung
                try:
                    _bk_ok, _bk_msg = db_backup_erstellen()
                except Exception as _bke:
                    _bk_ok, _bk_msg = False, str(_bke)

                try:
                    _result = kunde_loeschen(vid, bid, current_sa_id)
                    audit_log_eintragen(
                        None,
                        "kunde_endgueltig_geloescht",
                        (
                            f"kn={kn}, name={name_str}, "
                            f"n_spieler={_result.get('n_spieler', 0)}, "
                            f"n_benutzer={_result.get('n_benutzer', 0)}, "
                            f"backup={'ok' if _bk_ok else 'fehlgeschlagen'}"
                        ),
                        current_sa_id,
                    )
                    # Session-State bereinigen → zurück zur Kundenliste (nicht Startseite)
                    for _k in [_preview_key, f"_lz_confirm_{bid}",
                               f"_lz_start_{bid}", "kunden_auswahl"]:
                        st.session_state.pop(_k, None)
                    st.session_state["_nav_goto"] = "👥  Kundenverwaltung"
                    st.success(
                        f"✅ Kunde **{kn}** wurde endgültig gelöscht. "
                        f"{_result.get('n_spieler', 0)} Spieler, "
                        f"{_result.get('n_benutzer', 0)} Benutzerkonto(en) entfernt."
                    )
                    if _bk_ok:
                        st.info(f"💾 Backup vor Löschung: ✅ {_bk_msg}")
                    else:
                        st.warning(f"💾 Backup vor Löschung: ⚠️ {_bk_msg}")
                    st.rerun()
                except Exception as _le:
                    import logging
                    logging.exception("Kundenlöschung fehlgeschlagen")
                    st.error(
                        "❌ Kunde konnte nicht vollständig gelöscht werden. "
                        "Es wurden keine Änderungen übernommen."
                    )

        elif _bestaetigung.strip():
            st.warning(f"❌ Kundennummer stimmt nicht überein. Erwartet: **`{kn}`**")


def _kunde_detail(verein_id: int | None, benutzer_id: int | None) -> None:
    """Vollständige Kundendetailansicht mit 4 Sektionen + Audit."""
    if st.button("← Zurück zur Kundenliste", key="kd_zurueck"):
        st.session_state.pop("kunden_auswahl", None)
        st.session_state["_nav_goto"] = "👥  Kundenverwaltung"
        st.rerun()

    daten = kunde_vollstaendig_laden(verein_id=verein_id, benutzer_id=benutzer_id)
    if not daten:
        st.error("Kunde nicht gefunden.")
        return

    b   = daten.get("benutzer") or {}
    v   = daten.get("verein") or {}
    kn  = v.get("kundennummer") or b.get("kundennummer") or "—"
    typ = "Verein" if v else "Trainer"
    tit = v.get("name") or f"{b.get('vorname','')} {b.get('nachname','')}".strip() or "Unbekannt"

    st.markdown(
        f'<h2 style="color:#e6edf3;margin-bottom:4px">{kn} — {tit}</h2>'
        f'<p style="color:#8b949e;font-size:13px">{typ} · {b.get("email","—")}</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    _detail_a_kundenkonto(daten)
    _detail_b_rechnungsadresse(daten)
    _detail_c_lizenz(daten)
    _detail_d_vertrag(daten)
    _detail_audit(daten)
    _detail_gefahrenbereich(daten)


def _widerruf_frist_badge(eingegangen_str: str | None) -> str:
    """
    Gibt HTML-Badge für Widerruf-Frist zurück, oder '' wenn keine Frist konfiguriert.
    Liest KUENDIGUNG_WIDERRUF_STUNDEN aus der Umgebung (0 = unbegrenzt).
    """
    import os, datetime
    if not eingegangen_str:
        return ""
    try:
        frist_stunden = int(os.environ.get("KUENDIGUNG_WIDERRUF_STUNDEN", "0"))
    except (ValueError, TypeError):
        frist_stunden = 0
    if frist_stunden <= 0:
        return ""
    try:
        eingegangen = datetime.datetime.fromisoformat(eingegangen_str)
        ablauf      = eingegangen + datetime.timedelta(hours=frist_stunden)
        jetzt       = datetime.datetime.utcnow()
        ablauf_fmt  = ablauf.strftime("%d.%m.%Y %H:%M")
        if jetzt > ablauf:
            return (
                f'<span style="background:#3b0d0d;color:#f85149;border:1px solid #f85149;'
                f'border-radius:6px;padding:3px 9px;font-size:11px;font-weight:600">'
                f'⏰ Widerruf-Frist abgelaufen ({ablauf_fmt} Uhr)</span>'
            )
        rest_h = int((ablauf - jetzt).total_seconds() // 3600)
        return (
            f'<span style="background:#0d3b2e;color:#3fb950;border:1px solid #3fb950;'
            f'border-radius:6px;padding:3px 9px;font-size:11px;font-weight:600">'
            f'⏰ Widerruf möglich bis {ablauf_fmt} Uhr ({rest_h}h verbleibend)</span>'
        )
    except Exception:
        return ""


def _kuendigungen_uebersicht() -> None:
    """Superadmin-Tab: alle eingegangenen Kündigungen verwalten."""
    st.markdown("### 🚫 Kündigungen")

    filter_status = st.selectbox(
        "Status filtern",
        ["Alle", "eingegangen", "bestaetigt", "beendet"],
        key="kuend_sa_filter",
        label_visibility="visible",
    )

    kuendigungen = kuendigung_liste_laden(
        None if filter_status == "Alle" else filter_status
    )

    if not kuendigungen:
        st.info("Keine Kündigungen gefunden.")
        return

    st.caption(f"{len(kuendigungen)} Kündigung(en) gefunden")

    for k in kuendigungen:
        icon = "🏢" if k["kundentyp"] == "Verein" else "👤"
        kst  = k.get("kuendigungsstatus") or "—"
        eid  = k["entity_id"]
        iv   = bool(k["ist_verein"])
        kid  = f"{k['kundentyp']}_{eid}"

        # Gemeinsame Felder vorberechnen
        eingegangen_ts = k.get("kuendigung_eingegangen") or ""
        bestaetigt_ts  = k.get("kuendigung_bestaetigung_am") or ""
        letzte_ts      = (bestaetigt_ts or eingegangen_ts)[:16].replace("T", " ") or "—"
        eingegangen_fmt = eingegangen_ts[:16].replace("T", " ") or "—"
        bestaetigt_fmt  = bestaetigt_ts[:16].replace("T", " ") or "—"
        widerruf_badge  = _widerruf_frist_badge(eingegangen_ts) if kst == "eingegangen" else ""

        # ── Status-Badge CSS-Klasse ─────────────────────────────────────────
        badge_cls = {
            "eingegangen": "aph-kuend-badge-eingegangen",
            "bestaetigt":  "aph-kuend-badge-bestaetigt",
            "beendet":     "aph-kuend-badge-beendet",
        }.get(kst, "aph-kuend-badge-beendet")

        # ══ MOBILE: Karten-Darstellung (hidden on desktop via CSS :has()) ══
        with st.container():
            st.markdown(
                '<div class="aph-kuend-mobile-sentinel"></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="aph-kuend-card">
                  <div class="aph-kuend-card-header">
                    <span class="aph-kuend-badge {badge_cls}">{kst}</span>
                    <span class="aph-kuend-card-kn">{icon} {k.get('kundennummer','—')}</span>
                    <span class="aph-kuend-card-name">{k.get('name','—')}</span>
                  </div>
                  <div class="aph-kuend-card-meta">
                    <span><b>Paket:</b> {k.get('lizenztyp') or '—'}</span>
                    <span><b>Kundentyp:</b> {k['kundentyp']}</span>
                    <span><b>Eingegangen:</b> {eingegangen_fmt}</span>
                    <span><b>Vertrag endet am:</b> {k.get('gekuendigt_zum') or 'Nicht festgelegt'}</span>
                    <span><b>Letzte Statusänderung:</b> {letzte_ts}</span>
                    <span><b>Lizenzstatus:</b> {k.get('lizenz_status') or '—'}</span>
                    <span><b>Kündigungsgrund:</b> {k.get('kuendigung_grund') or 'Kein Grund angegeben'}</span>
                    <span><b>Bestätigt am:</b> {bestaetigt_fmt}</span>
                  </div>
                  {f'<div style="margin-top:8px">{widerruf_badge}</div>' if widerruf_badge else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if kst == "eingegangen":
                vende_m = st.text_input(
                    "Vertragsende setzen (YYYY-MM-DD, optional)",
                    key=f"kuend_vende_m_{kid}",
                    placeholder="z. B. 2026-09-30",
                )
                if st.button("✅ Bestätigen", key=f"kuend_best_m_{kid}",
                             type="primary", use_container_width=True):
                    ok_b, _ = kuendigung_bestaetigen(
                        eid, iv, vende_m.strip() or None, "bestaetigt",
                    )
                    if ok_b:
                        st.success("Kündigung bestätigt.")
                    else:
                        st.warning(
                            "⚠️ Die Kündigung konnte nicht bestätigt werden — "
                            "sie wurde inzwischen vom Kunden zurückgezogen. "
                            "Bitte die Liste neu laden."
                        )
                    st.rerun()

            if kst in ("eingegangen", "bestaetigt"):
                if st.button("🏁 Als beendet markieren",
                             key=f"kuend_end_m_{kid}",
                             use_container_width=True):
                    ok_e, _ = kuendigung_bestaetigen(
                        eid, iv, k.get("gekuendigt_zum") or None, "beendet",
                    )
                    if ok_e:
                        st.success("Kündigung als beendet markiert.")
                    else:
                        st.warning(
                            "⚠️ Die Kündigung konnte nicht beendet werden — "
                            "der Status hat sich zwischenzeitlich geändert. "
                            "Bitte die Liste neu laden."
                        )
                    st.rerun()

        # ══ DESKTOP: Expander-Darstellung (hidden on mobile via CSS :has()) ═
        with st.container():
            st.markdown(
                '<div class="aph-kuend-desktop-sentinel"></div>',
                unsafe_allow_html=True,
            )
            with st.expander(
                f"{icon} {k.get('kundennummer','—')} — {k.get('name','—')}  |  {kst}",
                expanded=False,
            ):
                c1, c2 = st.columns(2)
                c1.markdown(f"**Kundentyp:** {k['kundentyp']}")
                c1.markdown(f"**Paket:** {k.get('lizenztyp') or '—'}")
                c1.markdown(f"**Kündigung eingegangen:** {eingegangen_fmt}")
                c1.markdown(f"**Vertrag endet am:** {k.get('gekuendigt_zum') or 'Nicht festgelegt'}")
                c1.markdown(f"**Letzte Statusänderung:** {letzte_ts}")
                c2.markdown(f"**Lizenzstatus:** {k.get('lizenz_status') or '—'}")
                c2.markdown(f"**Kündigungsstatus:** {kst}")
                c2.markdown(f"**Kündigungsgrund:** {k.get('kuendigung_grund') or 'Kein Grund angegeben'}")
                c2.markdown(f"**Bestätigt am:** {bestaetigt_fmt}")

                if widerruf_badge:
                    st.markdown(widerruf_badge, unsafe_allow_html=True)

                st.markdown("")

                if kst == "eingegangen":
                    vende_input = st.text_input(
                        "Vertragsende setzen (YYYY-MM-DD, optional)",
                        key=f"kuend_vende_{kid}",
                        placeholder="z. B. 2026-09-30",
                    )
                    col_best, col_end, _ = st.columns([1, 1, 2])
                    if col_best.button("✅ Bestätigen", key=f"kuend_best_{kid}",
                                       type="primary"):
                        ok_b, _ = kuendigung_bestaetigen(
                            eid, iv, vende_input.strip() or None, "bestaetigt",
                        )
                        if ok_b:
                            st.success("Kündigung bestätigt.")
                        else:
                            st.warning(
                                "⚠️ Die Kündigung konnte nicht bestätigt werden — "
                                "sie wurde inzwischen vom Kunden zurückgezogen. "
                                "Bitte die Liste neu laden."
                            )
                        st.rerun()

                if kst in ("eingegangen", "bestaetigt"):
                    col_end2, _ = st.columns([1, 3])
                    if col_end2.button("🏁 Als beendet markieren",
                                       key=f"kuend_end_{kid}"):
                        ok_e, _ = kuendigung_bestaetigen(
                            eid, iv, k.get("gekuendigt_zum") or None, "beendet",
                        )
                        if ok_e:
                            st.success("Kündigung als beendet markiert.")
                        else:
                            st.warning(
                                "⚠️ Die Kündigung konnte nicht beendet werden — "
                                "der Status hat sich zwischenzeitlich geändert. "
                                "Bitte die Liste neu laden."
                            )
                        st.rerun()


def page_kundenverwaltung():
    """Hauptseite der Kundenverwaltung (nur Superadmin)."""
    user = st.session_state.get("user", {})
    if user.get("rolle") != "Superadmin":
        st.error("❌ Nur Superadmins können die Kundenverwaltung aufrufen.")
        return

    # Detail-Ansicht — geht direkt rein ohne Tab-Wrap
    auswahl = st.session_state.get("kunden_auswahl")
    if auswahl:
        verein_id, benutzer_id = auswahl
        _kunde_detail(verein_id, benutzer_id)
        return

    st.title("👥 Kundenverwaltung")

    tab_kunden, tab_kuend = st.tabs(["👥 Kunden", "🚫 Kündigungen"])

    # ── Tab: Kunden ────────────────────────────────────────────────────────────
    with tab_kunden:
        # Filter-Controls
        fc1, fc2, fc3, fc4 = st.columns([3, 1, 1, 1])
        such        = fc1.text_input("🔍 Suche", placeholder="Kundennummer, Name, E-Mail, Benutzername…",
                                      key="kv_such", label_visibility="collapsed")
        filter_typ  = fc2.selectbox("Kundentyp", ["Alle", "Verein", "Trainer"],
                                     key="kv_typ", label_visibility="collapsed")
        filter_st   = fc3.selectbox(
            "Accountstatus", ["Alle","Aktiv","Deaktiviert","Gesperrt","E-Mail nicht bestätigt"],
            key="kv_status", label_visibility="collapsed",
        )
        _liz_opts = ["Alle", "trial", "active", "expired", "suspended", "cancelled", "unbekannt"]
        filter_liz  = fc4.selectbox("Lizenzstatus", _liz_opts, key="kv_lizenz",
                                     label_visibility="collapsed")

        alle_kunden = kunden_liste_laden(
            such=such,
            filter_typ=filter_typ,
            filter_status=filter_st,
            filter_lizenz=filter_liz,
        )

        alle_kunden_gesamt = kunden_liste_laden()
        _kpis(alle_kunden_gesamt)

        st.caption(f"{len(alle_kunden)} Kunden gefunden")

        if not alle_kunden:
            st.info("Keine Kunden gefunden.")
        else:
            for k in alle_kunden:
                _kunden_karte(k)

    # ── Tab: Kündigungen ───────────────────────────────────────────────────────
    with tab_kuend:
        _kuendigungen_uebersicht()
