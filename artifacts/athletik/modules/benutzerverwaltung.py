"""Benutzerverwaltung — für Superadmin und Vereinsadmin."""
import streamlit as st
from database import (
    benutzer_laden,
    benutzer_speichern,
    benutzer_aktivieren,
    benutzer_passwort,
    benutzer_aktualisieren,
    vereine_laden,
    spieler_null_zuweisen,
    spieler_ohne_verein_zaehlen,
)


def page_benutzerverwaltung():
    st.title("👥 Benutzerverwaltung")

    user   = st.session_state.get("user", {})
    rolle  = user.get("rolle", "Trainer")
    meine_verein_id = user.get("verein_id")

    alle_benutzer = benutzer_laden()
    if rolle == "Vereinsadmin":
        alle_benutzer = [b for b in alle_benutzer if b.get("verein_id") == meine_verein_id]

    vereine = vereine_laden()
    if rolle == "Vereinsadmin":
        vereine = [v for v in vereine if v["id"] == meine_verein_id]

    # ── Bestehende Spieler zuweisen (Superadmin) ───────────────────────────────
    if rolle == "Superadmin":
        _null_count = spieler_ohne_verein_zaehlen()
        if _null_count > 0:
            st.warning(
                f"⚠️ **{_null_count} Spieler** haben noch keinen Verein und sind für "
                "Trainer unsichtbar. Weise sie einem Verein und Trainer zu."
            )
            _vereine_choice     = vereine_laden()
            _alle_benutzer_zuw  = benutzer_laden()
            if _vereine_choice:
                _zc1, _zc2, _zc3 = st.columns([2, 2, 1])
                _ziel_verein = _zc1.selectbox(
                    "Ziel-Verein", _vereine_choice,
                    format_func=lambda x: x["name"], key="zuw_verein"
                )
                _trainer_im_verein = [
                    b for b in _alle_benutzer_zuw
                    if b.get("verein_id") == _ziel_verein["id"]
                    and b.get("rolle") in ("Superadmin", "Trainer", "Vereinsadmin")
                ]
                if _trainer_im_verein:
                    _ziel_trainer = _zc2.selectbox(
                        "Ziel-Trainer/Admin", _trainer_im_verein,
                        format_func=lambda b: f"{b.get('vorname','')} {b.get('nachname','')} ({b.get('rolle','')})",
                        key="zuw_trainer"
                    )
                    if _zc3.button("✅ Zuweisen", key="zuw_btn", use_container_width=True):
                        try:
                            _n = spieler_null_zuweisen(_ziel_verein["id"], _ziel_trainer["id"])
                            st.success(f"✅ {_n} Spieler dem Verein **{_ziel_verein['name']}** zugewiesen.")
                            st.rerun()
                        except ValueError as _e:
                            st.error(f"❌ {_e}")
                else:
                    _zc2.warning("Kein Benutzer in diesem Verein — zuerst einen Trainer anlegen.")
        st.divider()

    # ── Bestehende Benutzer ────────────────────────────────────────────────────
    st.subheader(f"Benutzer ({len(alle_benutzer)})")

    if not alle_benutzer:
        st.info("Noch keine Benutzer vorhanden.")
    else:
        for u in alle_benutzer:
            _ev     = bool(u.get("email_verifiziert", 1))
            _aktiv  = bool(u.get("aktiv", 1))
            _gesperrt = bool(u.get("gesperrt_bis"))
            _status_icon = "✅" if _aktiv and _ev else ("📧" if not _ev else "⛔")
            with st.expander(
                f"{_status_icon} {u.get('vorname','')} {u.get('nachname','')} | "
                f"{u.get('rolle','')} | {u.get('verein','—')}"
            ):
                c1, c2 = st.columns(2)
                vorname  = c1.text_input("Vorname",      value=u.get("vorname",""),  key=f"vn_{u['id']}")
                nachname = c2.text_input("Nachname",     value=u.get("nachname",""), key=f"nn_{u['id']}")
                email    = c1.text_input("E-Mail/Login", value=u.get("email",""),    key=f"em_{u['id']}")

                rollen_choices = (["Trainer", "Vereinsadmin"]
                                  if rolle == "Vereinsadmin"
                                  else ["Trainer", "Vereinsadmin", "Superadmin"])
                cur_rolle  = u.get("rolle","Trainer")
                rolle_idx  = rollen_choices.index(cur_rolle) if cur_rolle in rollen_choices else 0
                neue_rolle = c2.selectbox("Rolle", rollen_choices, index=rolle_idx, key=f"rl_{u['id']}")

                if vereine:
                    cur_vid    = u.get("verein_id")
                    vidx       = next((i for i, v in enumerate(vereine) if v["id"] == cur_vid), 0)
                    sel_verein = c1.selectbox("Verein", vereine, index=vidx,
                                              format_func=lambda x: x["name"], key=f"vr_{u['id']}")
                    sel_verein_id = sel_verein["id"]
                else:
                    sel_verein_id = meine_verein_id

                aktiv = c2.checkbox("Aktiv", value=_aktiv, key=f"ak_{u['id']}")

                b1, b2 = st.columns(2)
                if b1.button("💾 Speichern", key=f"sv_{u['id']}"):
                    try:
                        benutzer_aktualisieren(u["id"], sel_verein_id, vorname.strip(),
                                              nachname.strip(), email.strip(), neue_rolle)
                        benutzer_aktivieren(u["id"], 1 if aktiv else 0)
                        st.success("Benutzer gespeichert.")
                        st.rerun()
                    except ValueError as _ve:
                        st.error(str(_ve))

                # Passwort ändern
                st.markdown("**🔒 Passwort ändern**")
                pc1, pc2 = st.columns(2)
                pw1 = pc1.text_input("Neues Passwort",       type="password", key=f"p1_{u['id']}")
                pw2 = pc2.text_input("Passwort wiederholen", type="password", key=f"p2_{u['id']}")
                if b2.button("🔑 Passwort setzen", key=f"pb_{u['id']}"):
                    if len(pw1) < 4:
                        st.error("Passwort muss mindestens 4 Zeichen haben.")
                    elif pw1 != pw2:
                        st.error("Passwörter stimmen nicht überein.")
                    else:
                        benutzer_passwort(u["id"], pw1)
                        st.success("Passwort geändert.")

                # ── Auth-Status (Superadmin) ───────────────────────────────────
                if rolle == "Superadmin":
                    st.markdown("---")
                    st.markdown("**🔍 Auth-Status**")

                    # Spec §9: E-Mail und Account als getrennte Zustandsanzeigen
                    _ev_label    = "✅ bestätigt"  if _ev     else "❌ nicht bestätigt"
                    _aktiv_label = "✅ freigeschaltet" if _aktiv else "⏳ wartet auf Freischaltung"
                    _as1, _as2, _as3, _as4 = st.columns(4)
                    _as1.metric("E-Mail",          _ev_label)
                    _as2.metric("Account",         _aktiv_label)
                    _as3.metric("Registriert am",  u.get("erstellt_am") or "—")
                    _as4.metric("Letzter Login",   u.get("letzter_login") or "—")

                    # Lizenz-Status
                    _lizenz_lbl = "—"
                    if u.get("verein_id"):
                        try:
                            from database import verein_by_id as _vbi
                            _vr = _vbi(u["verein_id"]) or {}
                            _lizenz_lbl = _vr.get("lizenz_status", "—")
                        except Exception:
                            pass
                    st.caption(f"Lizenz-Status: **{_lizenz_lbl}**")

                    def _get_base_url_bv() -> str:
                        import os as _os_bv
                        _custom = _os_bv.environ.get("APP_BASE_URL", "")
                        if _custom:
                            return _custom.rstrip("/")
                        _dev = _os_bv.environ.get("REPLIT_DEV_DOMAIN", "")
                        if _dev:
                            return f"https://{_dev}/athletik/app"
                        return "http://localhost:8082/app"

                    # Spec §9: Account freischalten (wenn E-Mail bestätigt aber noch nicht aktiv)
                    if _ev and not _aktiv:
                        if st.button(f"✅ Account freischalten", key=f"freischalten_{u['id']}",
                                     type="primary", use_container_width=True):
                            benutzer_aktivieren(u["id"], 1)
                            # Freischaltungs-E-Mail senden (Spec §10)
                            try:
                                from email_service import send_freischaltung_email as _sfe
                                from database import benutzer_by_id as _bbi_f
                                _bdata_f = _bbi_f(u["id"]) or {}
                                _sfe(_bdata_f.get("email",""),
                                     _bdata_f.get("vorname","Benutzer"),
                                     _get_base_url_bv())
                                st.success("✅ Account freigeschaltet — Freischaltungs-E-Mail gesendet.")
                            except Exception as _fee:
                                import logging as _log_bv
                                _log_bv.getLogger("athletik.email").error(
                                    "Freischaltungs-E-Mail fehlgeschlagen (%s)", type(_fee).__name__
                                )
                                st.success("✅ Account freigeschaltet.")
                                st.caption(f"⚠️ Freischaltungs-E-Mail konnte nicht gesendet werden ({type(_fee).__name__}).")
                            st.rerun()

                    # Spec §3: E-Mail-Verifikation manuell auslösen
                    if not _ev:
                        if st.button("📧 Bestätigungs-E-Mail erneut senden",
                                     key=f"verify_send_{u['id']}"):
                            from database import (
                                email_token_erzeugen as _ete,
                                benutzer_by_id as _bbi,
                            )
                            _bdata = _bbi(u["id"]) or {}
                            _btoken = _ete(u["id"])
                            try:
                                from email_service import send_verification_email as _sve
                                _sve(_bdata.get("email",""), _bdata.get("vorname","Benutzer"),
                                     _btoken, _get_base_url_bv())
                                st.success("✅ Bestätigungs-E-Mail gesendet.")
                            except Exception as _ee:
                                st.warning(f"E-Mail konnte nicht gesendet werden: {type(_ee).__name__}")

    # ── Neuen Benutzer anlegen ────────────────────────────────────────────────
    st.divider()
    st.subheader("Neuen Benutzer anlegen")

    nc1, nc2 = st.columns(2)
    n_vorname  = nc1.text_input("Vorname",        key="neu_vn")
    n_nachname = nc2.text_input("Nachname",       key="neu_nn")
    n_email    = nc1.text_input("E-Mail / Login", key="neu_em")
    n_pw       = nc2.text_input("Passwort",       type="password", key="neu_pw")

    n_rollen = (["Trainer", "Vereinsadmin"]
                if rolle == "Vereinsadmin"
                else ["Trainer", "Vereinsadmin", "Superadmin"])
    n_rolle  = nc1.selectbox("Rolle", n_rollen, key="neu_rl")

    if vereine:
        n_verein    = nc2.selectbox("Verein", vereine, format_func=lambda x: x["name"], key="neu_vr")
        n_verein_id = n_verein["id"]
    else:
        n_verein_id = meine_verein_id

    if st.button("✅ Benutzer anlegen", key="neu_save_btn"):
        if not n_email.strip():
            st.error("E-Mail fehlt.")
        elif not n_pw:
            st.error("Passwort fehlt.")
        else:
            try:
                benutzer_speichern(n_verein_id, n_vorname.strip(), n_nachname.strip(),
                                   n_email.strip(), n_pw, n_rolle, email_verifiziert=1)
                st.success(f"Benutzer **{n_vorname} {n_nachname}** angelegt.")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    # ── Superadmin: E-Mail-Versand testen ─────────────────────────────────────
    if rolle == "Superadmin":
        st.divider()
        st.subheader("📧 E-Mail-Versand testen")
        st.markdown(
            '<p style="color:#8b949e;font-size:12px">'
            "Sendet eine Testmail, um zu prüfen ob SMTP_PASSWORD korrekt konfiguriert ist.</p>",
            unsafe_allow_html=True,
        )
        _test_to = st.text_input("Ziel-E-Mail-Adresse", key="testmail_to",
                                 placeholder="empfaenger@example.com")
        if st.button("✉️ Testmail senden", key="testmail_btn"):
            if not _test_to.strip() or "@" not in _test_to:
                st.error("Bitte eine gültige E-Mail-Adresse eingeben.")
            else:
                try:
                    from email_service import send_test_mail as _stm
                    _stm(_test_to.strip())
                    st.success("✅ E-Mail erfolgreich versendet.")
                except RuntimeError as _re:
                    # SMTP_PASSWORD fehlt — zeige Hinweis ohne sensible Details
                    st.warning(str(_re))
                except Exception as _ex:
                    # SMTP-Fehler — keine sensiblen Details anzeigen
                    _ex_msg = str(_ex)
                    if "password" in _ex_msg.lower() or "auth" in _ex_msg.lower():
                        st.error("❌ SMTP-Authentifizierung fehlgeschlagen. Bitte SMTP_PASSWORD prüfen.")
                    else:
                        st.error(f"❌ E-Mail konnte nicht gesendet werden. Verbindungsfehler.")
