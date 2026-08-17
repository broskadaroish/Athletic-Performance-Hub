"""Trainerportal — vollständige Trainerverwaltung + eigenes Profil."""

import datetime
import re
import streamlit as st
from database import (
    benutzer_laden, benutzer_by_id, benutzer_speichern,
    benutzer_aktualisieren, benutzer_profil_aktualisieren,
    benutzer_aktivieren, benutzer_passwort, benutzer_loeschen,
    benutzer_foto_speichern, trainer_statistiken,
    benutzer_benutzername_setzen,
    vereine_laden,
    trainer_mandanten_fuer_benutzer,
    trainer_mandant_hinzufuegen,
    trainer_mandant_entfernen,
    trainer_mandanten_fuer_verein,
)
from auth import hash_password

_BN_RE = re.compile(r'^[a-zA-Z0-9_\-]+$')

_LIZENZEN = [
    "UEFA C", "UEFA B", "UEFA A", "UEFA Pro",
    "DFB Torwarttrainer", "DFB Fitness-Trainer", "Athletiktrainer",
    "Sportphysiotherapeut", "Sonstiges",
]

def _liz_to_list(raw: str | None) -> list[str]:
    """Kommagetrennte DB-Lizenz-Zeichenkette → Python-Liste."""
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip() in _LIZENZEN]

def _liz_to_str(selected: list[str]) -> str | None:
    """Multiselect-Liste → kommagetrennte Zeichenkette für DB (None wenn leer)."""
    cleaned = [x for x in selected if x in _LIZENZEN]
    return ", ".join(cleaned) if cleaned else None

_ROLLEN = ["Trainer", "Vereinsadmin"]
_ROLLEN_SUPER = ["Trainer", "Vereinsadmin", "Superadmin"]


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _avatar(name: str, foto_blob=None, size: int = 52):
    """Zeigt Profilfoto oder farbigen Initial-Avatar."""
    if foto_blob:
        try:
            st.image(bytes(foto_blob), width=size)
            return
        except Exception:
            pass
    farben = ["#1f6feb","#3fb950","#d29922","#f85149","#58a6ff","#bc8cff","#ff7b72","#ffa657"]
    farbe   = farben[hash(name or "?") % len(farben)]
    initial = (name or "?")[0].upper()
    st.markdown(
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f'background:{farbe}22;border:2px solid {farbe};display:flex;'
        f'align-items:center;justify-content:center;font-size:{size//2}px;'
        f'font-weight:800;color:{farbe}">{initial}</div>',
        unsafe_allow_html=True,
    )


def _rollen_badge(rolle: str) -> str:
    farben = {"Superadmin": "#d29922", "Vereinsadmin": "#58a6ff", "Trainer": "#3fb950"}
    c = farben.get(rolle, "#6e7681")
    return (f'<span style="background:{c}22;color:{c};font-size:10px;font-weight:700;'
            f'padding:2px 8px;border-radius:10px;border:1px solid {c}44">{rolle}</span>')


def _aktiv_badge(aktiv) -> str:
    if aktiv:
        return ('<span style="background:#23863633;color:#3fb950;font-size:10px;font-weight:700;'
                'padding:2px 8px;border-radius:10px;border:1px solid #23863655">AKTIV</span>')
    return ('<span style="background:#6e768122;color:#6e7681;font-size:10px;font-weight:700;'
            'padding:2px 8px;border-radius:10px;border:1px solid #6e768144">INAKTIV</span>')


def _login_ago(letzter_login: str | None) -> str:
    if not letzter_login:
        return "Noch nie"
    try:
        ts   = datetime.datetime.strptime(letzter_login, "%Y-%m-%d %H:%M")
        diff = datetime.datetime.now() - ts
        if diff.days == 0:
            mins = diff.seconds // 60
            if mins < 2:
                return "Gerade eben"
            if mins < 60:
                return f"Vor {mins} Min."
            return f"Vor {diff.seconds // 3600} Std."
        if diff.days == 1:
            return "Gestern"
        if diff.days < 30:
            return f"Vor {diff.days} Tagen"
        return ts.strftime("%d.%m.%Y")
    except Exception:
        return letzter_login


def _vollname(b: dict) -> str:
    return f"{b.get('vorname','')} {b.get('nachname','')}".strip() or b.get("email","")


# ── Trainerportal (Admin-Ansicht) ─────────────────────────────────────────────

def page_trainerportal():
    user = st.session_state.get("user", {})
    rolle = user.get("rolle", "Trainer")
    if rolle not in ("Superadmin", "Vereinsadmin"):
        st.error("⛔ Nur für Vereinsadmin und Superadmin zugänglich.")
        return

    if "tp_edit_id"  not in st.session_state:
        st.session_state["tp_edit_id"] = None
    if "tp_neu"      not in st.session_state:
        st.session_state["tp_neu"] = False
    if "tp_verein_filter" not in st.session_state:
        st.session_state["tp_verein_filter"] = None

    alle_benutzer = benutzer_laden()
    vereine       = vereine_laden()
    meine_verein  = user.get("verein_id")

    # ── Rollenbasierter Filter ────────────────────────────────────────────────
    # Vereinsadmin: sieht alle Trainer die über trainer_mandanten seinem Verein
    # zugeordnet sind — nicht nur jene mit benutzer.verein_id == meine_verein.
    # Superadmin: sieht alle (optional nach Verein gefiltert).
    if rolle == "Vereinsadmin":
        # Maßgeblich: trainer_mandanten-Tabelle (aktive Mitgliedschaften).
        # Der Legacy-FK benutzer.verein_id wird bewusst NICHT als Fallback
        # verwendet — er bleibt Rückwärtskompatibilitäts-Feld, kein Autorisierungsfeld.
        try:
            _meine_trainer = trainer_mandanten_fuer_verein(meine_verein)
            _tm_bid_set = {t["benutzer_id"] for t in _meine_trainer}
        except Exception:
            _tm_bid_set = set()
        benutzer = [b for b in alle_benutzer if b["id"] in _tm_bid_set]
    else:
        vf = st.session_state["tp_verein_filter"]
        benutzer = [b for b in alle_benutzer if vf is None or b.get("verein_id") == vf]

    # ── Kopfzeile ─────────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([5, 1])
    with hc1:
        st.title("🧑‍💼 Trainerportal")
        st.caption(f"{len(benutzer)} Trainer / Benutzer verwalten")
    with hc2:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        if st.button("➕ Neuer Trainer", type="primary",
                     use_container_width=True, key="tp_neu_btn"):
            st.session_state["tp_neu"]    = True
            st.session_state["tp_edit_id"] = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Verein-Filter (nur Superadmin) ────────────────────────────────────────
    if rolle == "Superadmin" and vereine:
        fc1, fc2 = st.columns([3, 1])
        with fc1:
            optionen = [{"id": None, "name": "Alle Vereine"}] + list(vereine)
            sel_idx = next(
                (i for i, v in enumerate(optionen)
                 if v["id"] == st.session_state["tp_verein_filter"]), 0
            )
            sel_v = fc1.selectbox(
                "Verein filtern",
                optionen,
                index=sel_idx,
                format_func=lambda x: x["name"],
                key="tp_vf_sel",
                label_visibility="collapsed",
            )
            if sel_v["id"] != st.session_state["tp_verein_filter"]:
                st.session_state["tp_verein_filter"] = sel_v["id"]
                st.rerun()

    # ── Metriken ──────────────────────────────────────────────────────────────
    aktive = [b for b in benutzer if b.get("aktiv")]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Benutzer gesamt",  len(benutzer))
    m2.metric("Aktiv",            len(aktive))
    m3.metric("Inaktiv",          len(benutzer) - len(aktive))
    m4.metric("Trainer",          sum(1 for b in benutzer if b.get("rolle") == "Trainer"))

    st.divider()

    # ── Trainer-Karten ────────────────────────────────────────────────────────
    if not benutzer:
        st.info("Keine Trainer / Benutzer vorhanden.")
    else:
        for b in benutzer:
            _trainer_karte(b, rolle, user)

    # ── Formular: Neuer Trainer ───────────────────────────────────────────────
    if st.session_state.get("tp_neu"):
        st.divider()
        st.subheader("➕ Neuen Trainer anlegen")
        _neuer_trainer_form(user, rolle, vereine)

    # ── Formular: Bearbeiten ──────────────────────────────────────────────────
    eid = st.session_state.get("tp_edit_id")
    if eid:
        b = benutzer_by_id(eid)
        if b:
            st.divider()
            _trainer_edit_form(b, user, rolle, vereine)


def _trainer_karte(b: dict, admin_rolle: str, admin_user: dict):
    vid    = b["id"]
    name   = _vollname(b)
    verein = b.get("verein_name") or b.get("verein") or "—"
    lizenz = b.get("lizenz") or "—"
    tel    = b.get("telefon") or ""
    email  = b.get("email") or ""
    is_editing = st.session_state.get("tp_edit_id") == vid

    st.markdown(
        f'<div style="background:#161b22;border:1px solid '
        f'{"#58a6ff" if is_editing else "#30363d"};border-radius:10px;'
        f'padding:14px 18px;margin-bottom:4px">',
        unsafe_allow_html=True,
    )
    c_av, c_info, c_stats, c_act = st.columns([1, 4, 3, 2])

    with c_av:
        _avatar(name, b.get("foto_blob"), size=52)

    with c_info:
        kontakt = " · ".join(filter(None, [email, tel]))
        # Mandanten-Badges (alle aktiven Vereine dieses Trainers)
        try:
            _mlist = trainer_mandanten_fuer_benutzer(vid)
            _mhtml = "".join(
                f'<span style="background:#1f2d1f;color:#3fb950;font-size:10px;'
                f'font-weight:600;padding:1px 6px;border-radius:8px;'
                f'border:1px solid #3fb95044;margin-right:3px">'
                f'🏢 {m["verein_name"]}</span>'
                for m in _mlist
                if not m.get("ist_technischer_mandant")
            ) if len(_mlist) > 1 else ""
        except Exception:
            _mhtml = ""
        st.markdown(
            f'<div style="padding:4px 0">'
            f'<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:4px">'
            f'<span style="font-size:15px;font-weight:700;color:#e6edf3">{name}</span>'
            f'&nbsp;{_rollen_badge(b.get("rolle","Trainer"))}'
            f'&nbsp;{_aktiv_badge(b.get("aktiv",1))}'
            f'</div>'
            + (f'<div style="font-size:11px;color:#8b949e">🏢 {verein}</div>' if verein != "—" else "")
            + (_mhtml if _mhtml else "")
            + (f'<div style="font-size:11px;color:#6e7681;margin-top:2px">{kontakt}</div>' if kontakt else "")
            + (f'<div style="font-size:10px;color:#6e7681">🎖 {lizenz}</div>' if lizenz != "—" else "")
            + f'</div>',
            unsafe_allow_html=True,
        )

    with c_stats:
        stats = trainer_statistiken(vid)
        letzte = _login_ago(b.get("letzter_login"))
        st.markdown(
            f'<div style="padding:6px 0">'
            f'<div style="display:flex;gap:16px;margin-bottom:8px">'
            f'<div style="text-align:center">'
            f'<div style="font-size:18px;font-weight:800;color:#e6edf3">{stats["spieler"]}</div>'
            f'<div style="font-size:9px;color:#8b949e">SPIELER</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:18px;font-weight:800;color:#e6edf3">{stats["diagnostiken"]}</div>'
            f'<div style="font-size:9px;color:#8b949e">DIAG.</div></div>'
            f'</div>'
            f'<div style="font-size:10px;color:#6e7681">🕐 {letzte}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with c_act:
        st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
        btn_lbl = "✖ Schließen" if is_editing else "✏️ Bearbeiten"
        if st.button(btn_lbl, key=f"tp_ed_{vid}", use_container_width=True):
            st.session_state["tp_edit_id"] = None if is_editing else vid
            st.session_state["tp_neu"] = False
            st.rerun()

        # Deaktivieren / Aktivieren
        aktiv = b.get("aktiv", 1)
        if st.button("✅ Aktivieren" if not aktiv else "🚫 Deaktivieren",
                     key=f"tp_ak_{vid}", use_container_width=True):
            try:
                benutzer_aktivieren(vid, 0 if aktiv else 1)
            except ValueError as _bav_e:
                st.error(str(_bav_e))
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)


def _neuer_trainer_form(admin_user: dict, admin_rolle: str, vereine: list):
    with st.form("tp_neu_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        f_vn   = c1.text_input("Vorname")
        f_nn   = c2.text_input("Nachname")
        f_em   = c1.text_input("E-Mail / Login *")
        f_pw   = c2.text_input("Passwort *", type="password")
        f_tel  = c1.text_input("Telefonnummer")
        f_liz  = c2.multiselect("Trainer-Lizenzen", _LIZENZEN)

        rollen_choices = _ROLLEN_SUPER if admin_rolle == "Superadmin" else _ROLLEN
        f_rol  = c1.selectbox("Rolle", rollen_choices)

        if admin_rolle == "Superadmin" and vereine:
            f_ver  = c2.selectbox("Verein", vereine, format_func=lambda x: x["name"])
            f_vid  = f_ver["id"]
        else:
            f_vid  = admin_user.get("verein_id")
            c2.info(f"Verein: {admin_user.get('verein_name','')}")

        s1, s2 = st.columns(2)
        save   = s1.form_submit_button("✅ Anlegen", type="primary",
                                       use_container_width=True)
        cancel = s2.form_submit_button("Abbrechen", use_container_width=True)

        if save:
            if not f_em.strip() or not f_pw:
                st.error("E-Mail und Passwort sind erforderlich.")
            else:
                neu_id = benutzer_speichern(
                    f_vid, f_vn.strip(), f_nn.strip(),
                    f_em.strip(), f_pw, f_rol,
                )
                if f_liz:
                    benutzer_profil_aktualisieren(
                        neu_id, f_vn.strip(), f_nn.strip(),
                        f_em.strip(), f_tel.strip() or None,
                        _liz_to_str(f_liz),
                    )
                st.session_state["tp_neu"] = False
                st.success(f"✅ Trainer **{f_vn} {f_nn}** angelegt.")
                st.rerun()
        if cancel:
            st.session_state["tp_neu"] = False
            st.rerun()


def _trainer_edit_form(b: dict, admin_user: dict, admin_rolle: str, vereine: list):
    vid  = b["id"]
    name = _vollname(b)

    st.markdown(
        f'<div style="background:#161b22;border:1px solid #58a6ff;border-radius:12px;'
        f'padding:20px 24px;margin-bottom:16px">'
        f'<h3 style="color:#e6edf3;margin:0 0 2px">✏️ {name}</h3>'
        f'<p style="color:#8b949e;font-size:11px;margin:0">Benutzer-ID {vid}</p></div>',
        unsafe_allow_html=True,
    )

    tab_profil, tab_mandanten, tab_foto, tab_sicherheit, tab_loeschen = st.tabs(
        ["📋 Profil", "🏢 Mandanten", "📷 Profilfoto", "🔑 Passwort", "⚠ Löschen"]
    )

    # ── Tab: Profil ────────────────────────────────────────────────────────────
    with tab_profil:
        with st.form(f"tp_prof_{vid}"):
            c1, c2 = st.columns(2)
            f_vn  = c1.text_input("Vorname",       value=b.get("vorname","")  or "")
            f_nn  = c2.text_input("Nachname",      value=b.get("nachname","") or "")
            f_em  = c1.text_input("E-Mail / Login",value=b.get("email","")    or "")
            f_tel = c2.text_input("Telefon",       value=b.get("telefon","")  or "")
            f_liz = c1.multiselect("Trainer-Lizenzen", _LIZENZEN,
                                    default=_liz_to_list(b.get("lizenz")))
            rollen_choices = _ROLLEN_SUPER if admin_rolle == "Superadmin" else _ROLLEN
            cur_r = b.get("rolle","Trainer")
            r_idx = rollen_choices.index(cur_r) if cur_r in rollen_choices else 0
            f_rol = c2.selectbox("Rolle", rollen_choices, index=r_idx)

            if admin_rolle == "Superadmin" and vereine:
                cur_vid = b.get("verein_id")
                v_idx   = next((i for i,v in enumerate(vereine) if v["id"]==cur_vid), 0)
                f_ver   = c1.selectbox("Verein", vereine, index=v_idx,
                                       format_func=lambda x: x["name"])
                f_vid   = f_ver["id"]
            else:
                f_vid = b.get("verein_id")

            f_aktiv = st.checkbox("Aktiv", value=bool(b.get("aktiv", 1)))

            if st.form_submit_button("💾 Profil speichern", type="primary",
                                     use_container_width=True):
                try:
                    benutzer_aktualisieren(
                        vid, f_vid, f_vn.strip(), f_nn.strip(),
                        f_em.strip(), f_rol,
                        caller_rolle=admin_rolle,
                        caller_verein_id=admin_user.get("verein_id"),
                    )
                    benutzer_profil_aktualisieren(vid, f_vn.strip(), f_nn.strip(),
                                                   f_em.strip(),
                                                   f_tel.strip() or None,
                                                   _liz_to_str(f_liz))
                    benutzer_aktivieren(vid, 1 if f_aktiv else 0)
                    st.success("✅ Profil gespeichert.")
                    st.rerun()
                except (ValueError, PermissionError) as _tp_e:
                    st.error(str(_tp_e))

    # ── Tab: Mandanten ────────────────────────────────────────────────────────
    with tab_mandanten:
        st.markdown("**Vereine / Mandanten dieses Trainers**")
        st.caption(
            "Ein Trainer kann mehreren Vereinen angehören. "
            "Hier können Zugehörigkeiten verwaltet werden."
        )
        try:
            _tm_list = trainer_mandanten_fuer_benutzer(vid)
        except Exception:
            _tm_list = []

        if _tm_list:
            for _tm in _tm_list:
                _tm_c1, _tm_c2 = st.columns([4, 1])
                _tm_echt = not _tm.get("ist_technischer_mandant")
                _tm_c1.markdown(
                    f'<div style="padding:6px 0">'
                    f'<span style="color:#e6edf3;font-weight:600">'
                    f'{"🏢" if _tm_echt else "👤"} {_tm["verein_name"]}</span>'
                    f'<br><span style="font-size:10px;color:#8b949e">'
                    f'Rolle: {_tm["rolle_im_verein"]} · '
                    f'Seit: {_tm["beigetreten_am"] or "—"}</span></div>',
                    unsafe_allow_html=True,
                )
                # Entfernen-Button nur für den eigenen Verein (Vereinsadmin)
                # oder für alle Vereine (Superadmin).
                _darf_entfernen = (
                    _tm_echt
                    and admin_rolle == "Superadmin"
                ) or (
                    _tm_echt
                    and admin_rolle == "Vereinsadmin"
                    and _tm["verein_id"] == admin_user.get("verein_id")
                )
                if _darf_entfernen:
                    if _tm_c2.button(
                        "✖ Entfernen",
                        key=f"tp_tm_del_{vid}_{_tm['verein_id']}",
                        use_container_width=True,
                    ):
                        try:
                            trainer_mandant_entfernen(
                                vid,
                                _tm["verein_id"],
                                caller_rolle=admin_rolle,
                                caller_verein_id=admin_user.get("verein_id"),
                            )
                            st.success(
                                f"✅ {name} aus **{_tm['verein_name']}** entfernt."
                            )
                            st.rerun()
                        except (PermissionError, Exception) as _tm_e:
                            st.error(str(_tm_e))
        else:
            st.info("Keine Mandanten gefunden.", icon="ℹ️")

        # Mandant hinzufügen (nur Superadmin)
        if admin_rolle == "Superadmin" and vereine:
            st.divider()
            st.markdown("**Mandant hinzufügen**")
            _vorhandene_vid = {_m["verein_id"] for _m in _tm_list}
            _verfuegbar = [v for v in vereine if v["id"] not in _vorhandene_vid]
            if _verfuegbar:
                _neu_ver = st.selectbox(
                    "Verein",
                    _verfuegbar,
                    format_func=lambda x: x["name"],
                    key=f"tp_tm_add_v_{vid}",
                )
                if st.button(
                    "➕ Mandant hinzufügen",
                    key=f"tp_tm_add_btn_{vid}",
                    type="primary",
                ):
                    try:
                        trainer_mandant_hinzufuegen(
                            vid, _neu_ver["id"],
                            rolle=b.get("rolle", "Trainer"),
                        )
                        st.success(
                            f"✅ {name} zu **{_neu_ver['name']}** hinzugefügt."
                        )
                        st.rerun()
                    except Exception as _tm_e:
                        st.error(str(_tm_e))
            else:
                st.info("Dieser Trainer ist bereits in allen Vereinen eingetragen.")

    # ── Tab: Foto ──────────────────────────────────────────────────────────────
    with tab_foto:
        fc1, fc2 = st.columns([1, 2])
        with fc1:
            st.markdown("**Aktuelles Foto**")
            _avatar(name, b.get("foto_blob"), size=90)
        with fc2:
            st.markdown("**Neues Foto hochladen**")
            up = st.file_uploader("PNG, JPG oder WEBP",
                                   type=["png","jpg","jpeg","webp"],
                                   key=f"tp_foto_up_{vid}")
            if up:
                from utils.file_magic import validate_image
                import config as _cfg
                _raw = up.read()
                _ok, _err = validate_image(_raw, max_mb=_cfg.MAX_SPIELERBILD_MB)
                if not _ok:
                    st.error(f"❌ {_err}")
                else:
                    from utils.file_magic import optimize_image as _opt_img
                    benutzer_foto_speichern(vid, _opt_img(_raw))
                    st.success("✅ Foto gespeichert.")
                    st.rerun()
            if b.get("foto_blob"):
                if st.button("🗑 Foto entfernen", key=f"tp_foto_del_{vid}"):
                    benutzer_foto_speichern(vid, None)
                    st.rerun()

    # ── Tab: Passwort ──────────────────────────────────────────────────────────
    with tab_sicherheit:
        st.markdown("**Passwort zurücksetzen**")
        st.caption("Als Admin kannst du das Passwort direkt setzen — ohne altes Passwort.")
        with st.form(f"tp_pw_{vid}"):
            pc1, pc2 = st.columns(2)
            npw1 = pc1.text_input("Neues Passwort",        type="password")
            npw2 = pc2.text_input("Passwort bestätigen",   type="password")
            if st.form_submit_button("🔑 Passwort setzen", type="primary",
                                     use_container_width=True):
                if len(npw1) < 4:
                    st.error("Passwort muss mindestens 4 Zeichen haben.")
                elif npw1 != npw2:
                    st.error("Passwörter stimmen nicht überein.")
                else:
                    benutzer_passwort(vid, npw1)
                    st.success(f"✅ Passwort für **{name}** geändert.")

    # ── Tab: Löschen ──────────────────────────────────────────────────────────
    with tab_loeschen:
        stats = trainer_statistiken(vid)
        if stats["spieler"] > 0:
            st.warning(
                f"⚠ Dieser Trainer hat noch **{stats['spieler']} Spieler** zugeordnet. "
                "Bitte zuerst die Spieler einem anderen Trainer zuweisen."
            )
        st.markdown(
            '<div style="padding:16px;background:#1a0a0a;border-radius:8px;'
            'border:1px solid #6e1a1a;margin-bottom:12px">'
            '<div style="color:#f85149;font-weight:700;font-size:12px;margin-bottom:4px">'
            '⚠ GEFAHRENZONE</div>'
            '<div style="color:#8b949e;font-size:12px">Der Benutzer wird dauerhaft gelöscht '
            '— nur möglich ohne zugeordnete Spieler.</div></div>',
            unsafe_allow_html=True,
        )
        confirmed = st.checkbox(
            f'Ich möchte **{name}** unwiderruflich löschen',
            key=f"tp_del_confirm_{vid}",
        )
        if st.button("🗑 Trainer löschen", key=f"tp_del_btn_{vid}",
                     disabled=not confirmed, type="secondary"):
            ok, msg = benutzer_loeschen(vid)
            if ok:
                st.session_state["tp_edit_id"] = None
                st.success(f"✅ **{name}** wurde gelöscht.")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# ── Mein Profil (alle Benutzer) ───────────────────────────────────────────────

def page_mein_profil():
    user = st.session_state.get("user", {})
    uid  = user.get("id")
    if not uid:
        st.error("Kein eingeloggter Benutzer.")
        return

    b = benutzer_by_id(uid)
    if not b:
        st.error("Profil nicht gefunden.")
        return

    name   = _vollname(b)
    verein = b.get("verein_name") or user.get("verein_name") or "—"

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("👤 Mein Profil")
    st.caption(f"{b.get('rolle','Trainer')} · {verein}")

    # ── Foto + Stammdaten nebeneinander ───────────────────────────────────────
    fc1, fc2 = st.columns([1, 3])
    with fc1:
        st.markdown("**Profilfoto**")
        _avatar(name, b.get("foto_blob"), size=100)
        st.markdown("<div style='margin-top:8px'>", unsafe_allow_html=True)
        up = st.file_uploader("Neues Foto", type=["png","jpg","jpeg","webp"],
                               key="mp_foto_up", label_visibility="collapsed")
        if up:
            from utils.file_magic import validate_image
            import config as _cfg
            _raw = up.read()
            _ok, _err = validate_image(_raw, max_mb=_cfg.MAX_SPIELERBILD_MB)
            if not _ok:
                st.error(f"❌ {_err}")
            else:
                from utils.file_magic import optimize_image as _opt_img
                _raw = _opt_img(_raw)
                benutzer_foto_speichern(uid, _raw)
                # Sofort im session_state aktualisieren
                st.session_state["user"]["foto_blob"] = _raw
                st.success("✅ Foto gespeichert.")
                st.rerun()
        if b.get("foto_blob"):
            if st.button("🗑 Entfernen", key="mp_foto_del"):
                benutzer_foto_speichern(uid, None)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with fc2:
        with st.form("mp_profil_form"):
            pc1, pc2 = st.columns(2)
            f_vn  = pc1.text_input("Vorname",  value=b.get("vorname","")  or "")
            f_nn  = pc2.text_input("Nachname", value=b.get("nachname","") or "")
            f_em  = pc1.text_input("E-Mail / Benutzername",
                                    value=b.get("email","") or "")
            f_tel = pc2.text_input("Telefonnummer",
                                    value=b.get("telefon","") or "")
            f_liz = st.multiselect("Trainer-Lizenzen", _LIZENZEN,
                                    default=_liz_to_list(b.get("lizenz")))

            if st.form_submit_button("💾 Profil speichern", type="primary",
                                     use_container_width=True):
                if not f_em.strip():
                    st.error("E-Mail darf nicht leer sein.")
                else:
                    benutzer_profil_aktualisieren(
                        uid, f_vn.strip(), f_nn.strip(), f_em.strip(),
                        f_tel.strip() or None,
                        _liz_to_str(f_liz),
                    )
                    # Session aktualisieren
                    st.session_state["user"]["vorname"]  = f_vn.strip()
                    st.session_state["user"]["nachname"] = f_nn.strip()
                    st.session_state["user"]["email"]    = f_em.strip()
                    st.success("✅ Profil gespeichert.")
                    st.rerun()

    # ── Info-Karte ────────────────────────────────────────────────────────────
    letzte = _login_ago(b.get("letzter_login"))
    st.markdown(
        f'<div style="margin:16px 0;padding:12px 16px;background:#161b22;'
        f'border-radius:8px;border:1px solid #30363d;display:flex;gap:24px;flex-wrap:wrap">'
        f'<div><div style="font-size:9px;color:#8b949e;letter-spacing:1px">ROLLE</div>'
        f'<div style="font-size:13px;font-weight:600;color:#e6edf3">{b.get("rolle","")}</div></div>'
        f'<div><div style="font-size:9px;color:#8b949e;letter-spacing:1px">VEREIN</div>'
        f'<div style="font-size:13px;font-weight:600;color:#e6edf3">{verein}</div></div>'
        f'<div><div style="font-size:9px;color:#8b949e;letter-spacing:1px">LETZTE ANMELDUNG</div>'
        f'<div style="font-size:13px;font-weight:600;color:#e6edf3">{letzte}</div></div>'
        f'<div><div style="font-size:9px;color:#8b949e;letter-spacing:1px">STATUS</div>'
        f'<div style="font-size:13px">{_aktiv_badge(b.get("aktiv",1))}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Meine Vereine / Mandanten ─────────────────────────────────────────────
    try:
        _mp_mandanten = trainer_mandanten_fuer_benutzer(uid)
        _mp_echte = [m for m in _mp_mandanten if not m.get("ist_technischer_mandant")]
        if _mp_echte:
            st.divider()
            st.subheader("🏢 Meine Vereine")
            st.caption(
                "Vereine, denen du als Trainer zugeordnet bist. "
                "Du kannst einen Verein über die Abmelden-Schaltfläche wechseln."
            )
            for _mp_m in _mp_echte:
                _mp_c1, _mp_c2 = st.columns([5, 1])
                _mp_c1.markdown(
                    f'<div style="padding:6px 0">'
                    f'<span style="font-size:14px;font-weight:600;color:#e6edf3">'
                    f'🏢 {_mp_m["verein_name"]}</span>'
                    f'<br><span style="font-size:11px;color:#8b949e">'
                    f'Rolle: {_mp_m["rolle_im_verein"]} · '
                    f'Mitglied seit: {_mp_m["beigetreten_am"] or "—"}'
                    f'</span></div>',
                    unsafe_allow_html=True,
                )
                _ist_aktiver = (
                    _mp_m["verein_id"] == user.get("verein_id")
                )
                if _ist_aktiver:
                    _mp_c2.markdown(
                        '<div style="padding-top:6px">'
                        '<span style="color:#3fb950;font-size:12px;font-weight:700">✓ Aktiv</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    if _mp_c2.button(
                        "Wechseln",
                        key=f"mp_mandant_sw_{_mp_m['verein_id']}",
                        use_container_width=True,
                    ):
                        import streamlit as _st_inner
                        _st_inner.session_state["user"]["verein_id"] = _mp_m["verein_id"]
                        _st_inner.session_state["user"]["verein_name"] = _mp_m["verein_name"]
                        _st_inner.session_state["_aktiver_mandant_id"] = _mp_m["verein_id"]
                        _st_inner.session_state["_mandant_gewaehlt"] = True
                        _st_inner.rerun()
    except Exception:
        pass

    # ── Passwort ändern ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("🔒 Passwort ändern")
    with st.form("mp_pw_form"):
        pwc1, pwc2, pwc3 = st.columns(3)
        alt_pw  = pwc1.text_input("Aktuelles Passwort",  type="password")
        neu_pw1 = pwc2.text_input("Neues Passwort",       type="password")
        neu_pw2 = pwc3.text_input("Passwort bestätigen",  type="password")
        if st.form_submit_button("🔑 Passwort ändern", type="primary",
                                  use_container_width=True):
            if hash_password(alt_pw) != b.get("passwort_hash",""):
                st.error("❌ Aktuelles Passwort ist falsch.")
            elif len(neu_pw1) < 4:
                st.error("Neues Passwort muss mindestens 4 Zeichen haben.")
            elif neu_pw1 != neu_pw2:
                st.error("Neue Passwörter stimmen nicht überein.")
            else:
                benutzer_passwort(uid, neu_pw1)
                # Sessions wurden in benutzer_passwort() serverseitig invalidiert.
                # Flag setzen → per-Rerun-Token-Check in app.py erkennt ungültige
                # Session und führt den vollständigen Logout durch.
                st.session_state["__pw_changed__"] = True
                st.rerun()

    # ── Benutzername ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🏷 Benutzername")
    st.caption(
        "Optionale Alternative zur E-Mail beim Login. "
        "Nur Buchstaben, Ziffern, _ und - erlaubt. Muss eindeutig sein."
    )

    current_bn = b.get("benutzername") or ""
    if current_bn:
        st.markdown(
            f'<div style="display:inline-block;background:#0d3b2e;border:1px solid #3fb950;'
            f'border-radius:8px;padding:6px 14px;margin-bottom:12px">'
            f'<span style="font-size:11px;color:#8b949e;letter-spacing:.8px">BENUTZERNAME&nbsp;&nbsp;</span>'
            f'<span style="font-size:14px;font-weight:700;color:#3fb950">@{current_bn}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "Noch kein Benutzername festgelegt — du meldest dich mit deiner E-Mail an.",
            icon="ℹ️",
        )

    with st.form("mp_bn_form"):
        bn_c1, bn_c2 = st.columns([3, 1])
        new_bn = bn_c1.text_input(
            "Benutzername",
            value=current_bn,
            placeholder="z. B. trainer_mueller",
            max_chars=30,
            help="3–30 Zeichen. Nur a–z, A–Z, 0–9, _ und - erlaubt. Leer lassen, um den Benutzernamen zu entfernen.",
        )
        bn_c2.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "💾 Speichern", type="primary", use_container_width=True
        )
        if submitted:
            nb = new_bn.strip()
            if nb and len(nb) < 3:
                st.error("❌ Benutzername muss mindestens 3 Zeichen lang sein.")
            elif nb and not _BN_RE.match(nb):
                st.error("❌ Nur Buchstaben (a–z, A–Z), Ziffern, _ und - erlaubt.")
            else:
                ok, err = benutzer_benutzername_setzen(uid, nb or None)
                if ok:
                    if nb:
                        st.success(f"✅ Benutzername «{nb}» gespeichert — du kannst dich ab sofort damit anmelden.")
                    else:
                        st.success("✅ Benutzername entfernt.")
                    st.rerun()
                else:
                    st.error(f"❌ {err}")
