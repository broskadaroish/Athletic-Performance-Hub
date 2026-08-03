"""Benutzerverwaltung — für Superadmin und Vereinsadmin."""
import streamlit as st
from database import (
    benutzer_laden,
    benutzer_speichern,
    benutzer_aktivieren,
    benutzer_passwort,
    benutzer_aktualisieren,
    vereine_laden,
)


def page_benutzerverwaltung():
    st.title("👥 Benutzerverwaltung")

    user = st.session_state.get("user", {})
    rolle = user.get("rolle", "Trainer")
    meine_verein_id = user.get("verein_id")

    # Superadmin sieht alle Benutzer; Vereinsadmin nur seinen Verein
    alle_benutzer = benutzer_laden()
    if rolle == "Vereinsadmin":
        alle_benutzer = [b for b in alle_benutzer if b.get("verein_id") == meine_verein_id]

    vereine = vereine_laden()
    if rolle == "Vereinsadmin":
        vereine = [v for v in vereine if v["id"] == meine_verein_id]

    # ── Bestehende Benutzer ────────────────────────────────────────────────────
    st.subheader(f"Benutzer ({len(alle_benutzer)})")

    if not alle_benutzer:
        st.info("Noch keine Benutzer vorhanden.")
    else:
        for u in alle_benutzer:
            with st.expander(f"{u.get('vorname','')} {u.get('nachname','')} | {u.get('rolle','')} | {u.get('verein','—')}"):
                c1, c2 = st.columns(2)
                vorname  = c1.text_input("Vorname",      value=u.get("vorname",""),  key=f"vn_{u['id']}")
                nachname = c2.text_input("Nachname",     value=u.get("nachname",""), key=f"nn_{u['id']}")
                email    = c1.text_input("E-Mail/Login", value=u.get("email",""),    key=f"em_{u['id']}")

                rollen_choices = ["Trainer", "Vereinsadmin"] if rolle == "Vereinsadmin" else ["Trainer", "Vereinsadmin", "Superadmin"]
                cur_rolle = u.get("rolle","Trainer")
                rolle_idx = rollen_choices.index(cur_rolle) if cur_rolle in rollen_choices else 0
                neue_rolle = c2.selectbox("Rolle", rollen_choices, index=rolle_idx, key=f"rl_{u['id']}")

                if vereine:
                    cur_vid = u.get("verein_id")
                    vidx = next((i for i, v in enumerate(vereine) if v["id"] == cur_vid), 0)
                    sel_verein = c1.selectbox("Verein", vereine, index=vidx,
                                              format_func=lambda x: x["name"], key=f"vr_{u['id']}")
                    sel_verein_id = sel_verein["id"]
                else:
                    sel_verein_id = meine_verein_id

                aktiv = c2.checkbox("Aktiv", value=bool(u.get("aktiv", 1)), key=f"ak_{u['id']}")

                b1, b2 = st.columns(2)
                if b1.button("💾 Speichern", key=f"sv_{u['id']}"):
                    benutzer_aktualisieren(u["id"], sel_verein_id, vorname.strip(),
                                          nachname.strip(), email.strip(), neue_rolle)
                    benutzer_aktivieren(u["id"], 1 if aktiv else 0)
                    st.success("Benutzer gespeichert.")
                    st.rerun()

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

    # ── Neuen Benutzer anlegen ────────────────────────────────────────────────
    st.divider()
    st.subheader("Neuen Benutzer anlegen")

    nc1, nc2 = st.columns(2)
    n_vorname  = nc1.text_input("Vorname",       key="neu_vn")
    n_nachname = nc2.text_input("Nachname",      key="neu_nn")
    n_email    = nc1.text_input("E-Mail / Login",key="neu_em")
    n_pw       = nc2.text_input("Passwort",      type="password", key="neu_pw")

    n_rollen = ["Trainer", "Vereinsadmin"] if rolle == "Vereinsadmin" else ["Trainer", "Vereinsadmin", "Superadmin"]
    n_rolle  = nc1.selectbox("Rolle", n_rollen, key="neu_rl")

    if vereine:
        n_verein = nc2.selectbox("Verein", vereine, format_func=lambda x: x["name"], key="neu_vr")
        n_verein_id = n_verein["id"]
    else:
        n_verein_id = meine_verein_id

    if st.button("✅ Benutzer anlegen", key="neu_save_btn"):
        if not n_email.strip():
            st.error("E-Mail fehlt.")
        elif not n_pw:
            st.error("Passwort fehlt.")
        else:
            benutzer_speichern(n_verein_id, n_vorname.strip(), n_nachname.strip(),
                               n_email.strip(), n_pw, n_rolle)
            st.success(f"Benutzer **{n_vorname} {n_nachname}** angelegt.")
            st.rerun()
