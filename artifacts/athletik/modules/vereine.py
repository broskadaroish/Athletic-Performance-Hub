"""Vereinsverwaltung (SaaS) — vollständige Verwaltung von Vereinen.
Nur für Superadmin zugänglich."""

import datetime
import streamlit as st
from database import (
    vereine_laden, verein_speichern, verein_by_id,
    verein_aktualisieren, verein_logo_speichern,
    verein_aktivieren, verein_statistiken,
    benutzer_laden,
)

_LIZENZTYPEN = ["Test (30 Tage)", "Basis", "Standard", "Premium", "Enterprise"]

_LIZ_COLORS = {
    "Enterprise":    "#d29922",
    "Premium":       "#58a6ff",
    "Standard":      "#3fb950",
    "Basis":         "#6e7681",
    "Test (30 Tage)":"#f85149",
}

_DEFAULT_PRIMAER   = "#1f6feb"
_DEFAULT_SEKUNDAER = "#58a6ff"


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _pct(val, mx):
    if not mx or mx <= 0:
        return 0
    return min(int(val / mx * 100), 100)


def _bar_color(pct):
    if pct >= 100:
        return "#f85149"
    if pct >= 80:
        return "#d29922"
    return "#1f6feb"


def _progress_html(label, val, mx):
    pct   = _pct(val, mx)
    color = _bar_color(pct)
    return (
        f'<div style="margin-bottom:6px">'
        f'<div style="display:flex;justify-content:space-between;font-size:10px;'
        f'color:#8b949e;margin-bottom:3px"><span>{label}</span>'
        f'<span style="color:{"#f85149" if pct>=100 else "#e6edf3"};font-weight:600">'
        f'{val} / {mx}</span></div>'
        f'<div style="background:#21262d;border-radius:4px;height:5px">'
        f'<div style="width:{pct}%;background:{color};border-radius:4px;height:5px">'
        f'</div></div></div>'
    )


def _lizenz_badge_html(lt):
    c = _LIZ_COLORS.get(lt, "#6e7681")
    return (
        f'<span style="background:{c}22;color:{c};font-size:10px;font-weight:700;'
        f'padding:2px 8px;border-radius:10px;border:1px solid {c}44">{lt or "Basis"}</span>'
    )


def _aktiv_badge_html(aktiv):
    if aktiv:
        return ('<span style="background:#23863633;color:#3fb950;font-size:10px;font-weight:700;'
                'padding:2px 8px;border-radius:10px;border:1px solid #23863655">AKTIV</span>')
    return ('<span style="background:#6e768122;color:#6e7681;font-size:10px;font-weight:700;'
            'padding:2px 8px;border-radius:10px;border:1px solid #6e768144">INAKTIV</span>')


def _lizenz_ablauf_html(lizenz_bis):
    if not lizenz_bis:
        return '<span style="font-size:10px;color:#6e7681">Kein Ablaufdatum</span>'
    try:
        bis   = datetime.date.fromisoformat(str(lizenz_bis))
        heute = datetime.date.today()
        tage  = (bis - heute).days
        if tage < 0:
            farbe = "#f85149"
            text  = f"⚠ Abgelaufen seit {abs(tage)} Tagen"
        elif tage <= 30:
            farbe = "#d29922"
            text  = f"⏳ Läuft ab in {tage} Tagen ({bis.strftime('%d.%m.%Y')})"
        else:
            farbe = "#3fb950"
            text  = f"✓ Gültig bis {bis.strftime('%d.%m.%Y')}"
        return f'<span style="font-size:10px;color:{farbe}">{text}</span>'
    except Exception:
        return f'<span style="font-size:10px;color:#8b949e">{lizenz_bis}</span>'


def _logo_widget(v: dict, width: int = 52):
    primaer = v.get("farbe_primaer") or _DEFAULT_PRIMAER
    if v.get("logo_blob"):
        try:
            st.image(bytes(v["logo_blob"]), width=width)
            return
        except Exception:
            pass
    st.markdown(
        f'<div style="width:{width}px;height:{width}px;border-radius:10px;'
        f'background:{primaer}22;display:flex;align-items:center;'
        f'justify-content:center;font-size:{width//2}px;border:1px solid #30363d">🏟</div>',
        unsafe_allow_html=True,
    )


# ── Hauptseite ────────────────────────────────────────────────────────────────

def page_vereine():
    user = st.session_state.get("user", {})
    if user.get("rolle") != "Superadmin":
        st.error("⛔ Nur für Superadmin zugänglich.")
        return

    if "verein_edit_id" not in st.session_state:
        st.session_state["verein_edit_id"] = None
    if "verein_neu" not in st.session_state:
        st.session_state["verein_neu"] = False

    vereine = vereine_laden()
    alle_benutzer = benutzer_laden()

    # ── Kopfzeile ─────────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([5, 1])
    with hc1:
        st.title("🏢 Vereinsverwaltung")
        st.caption(
            f"SaaS-Verwaltung · {len(vereine)} Vereine · "
            f"{sum(1 for v in vereine if v.get('aktiv'))} aktiv"
        )
    with hc2:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        if st.button("➕ Neuer Verein", type="primary",
                     use_container_width=True, key="vv_neu_top"):
            st.session_state["verein_neu"]    = True
            st.session_state["verein_edit_id"] = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Globale Metriken ──────────────────────────────────────────────────────
    gesamt_trainer = len([b for b in alle_benutzer
                          if b.get("rolle") in ("Trainer","Vereinsadmin","Superadmin")])
    gesamt_spieler = 0
    gesamt_diag    = 0
    if vereine:
        for v in vereine:
            s = verein_statistiken(v["id"])
            gesamt_spieler += s["spieler"]
            gesamt_diag    += s["diagnostiken"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Vereine gesamt",   len(vereine),
              f"{sum(1 for v in vereine if v.get('aktiv'))} aktiv")
    m2.metric("Benutzer / Trainer", gesamt_trainer)
    m3.metric("Spieler gesamt",   gesamt_spieler)
    m4.metric("Diagnostiken",     gesamt_diag)

    st.divider()

    # ── Vereins-Karten ────────────────────────────────────────────────────────
    if not vereine:
        st.info(
            "Noch keine Vereine vorhanden.  \n"
            "Klicke **➕ Neuer Verein** um den ersten Verein anzulegen."
        )
    else:
        for v in vereine:
            _verein_karte(v, verein_statistiken(v["id"]))

    # ── Formular: Neuer Verein ────────────────────────────────────────────────
    if st.session_state.get("verein_neu"):
        st.divider()
        st.subheader("➕ Neuen Verein anlegen")
        with st.form("vv_neu_form", clear_on_submit=True):
            nc1, nc2 = st.columns(2)
            n_name  = nc1.text_input("Vereinsname *", placeholder="FC Musterstadt")
            n_ansp  = nc2.text_input("Ansprechpartner")
            n_email = nc1.text_input("E-Mail")
            n_tel   = nc2.text_input("Telefon")
            n_adr   = nc1.text_input("Adresse", placeholder="Musterstraße 1, 12345 Stadt")
            n_hp    = nc2.text_input("Homepage", placeholder="https://www.verein.de")
            n_liz   = nc1.selectbox("Lizenztyp", _LIZENZTYPEN, index=1)
            n_bis_default = datetime.date.today().replace(
                year=datetime.date.today().year + 1
            )
            n_bis = nc2.date_input("Lizenz gültig bis", value=n_bis_default)
            n_mt  = nc1.number_input("Max. Trainer", min_value=1, value=5)
            n_ms  = nc2.number_input("Max. Spieler",  min_value=1, value=50)
            sb1, sb2 = st.columns(2)
            save   = sb1.form_submit_button("✅ Anlegen", type="primary",
                                            use_container_width=True)
            cancel = sb2.form_submit_button("Abbrechen", use_container_width=True)
            if save:
                if not n_name.strip():
                    st.error("Vereinsname ist erforderlich.")
                else:
                    vid = verein_speichern(n_name.strip())
                    verein_aktualisieren(
                        vid, name=n_name.strip(),
                        ansprechpartner=n_ansp.strip() or None,
                        email=n_email.strip() or None,
                        telefon=n_tel.strip() or None,
                        adresse=n_adr.strip() or None,
                        homepage=n_hp.strip() or None,
                        lizenztyp=n_liz,
                        lizenz_bis=str(n_bis),
                        max_trainer=int(n_mt),
                        max_spieler=int(n_ms),
                    )
                    st.session_state["verein_neu"] = False
                    st.success(f"✅ Verein **{n_name.strip()}** angelegt.")
                    st.rerun()
            if cancel:
                st.session_state["verein_neu"] = False
                st.rerun()

    # ── Formular: Verein bearbeiten ───────────────────────────────────────────
    edit_id = st.session_state.get("verein_edit_id")
    if edit_id:
        v = verein_by_id(edit_id)
        if v:
            st.divider()
            _verein_edit_form(v)


# ── Vereins-Karte ─────────────────────────────────────────────────────────────

def _verein_karte(v: dict, stats: dict):
    primaer   = v.get("farbe_primaer")   or _DEFAULT_PRIMAER
    lizenztyp = v.get("lizenztyp")       or "Basis"
    max_t     = int(v.get("max_trainer") or 5)
    max_s     = int(v.get("max_spieler") or 50)

    ansp    = v.get("ansprechpartner") or ""
    email   = v.get("email")           or ""
    tel     = v.get("telefon")         or ""
    hp      = v.get("homepage")        or ""
    adr     = v.get("adresse")         or ""
    kontakt = " · ".join(filter(None, [email, tel]))

    is_editing = st.session_state.get("verein_edit_id") == v["id"]

    # Karten-Rahmen via HTML
    st.markdown(
        f'<div style="background:#161b22;border:1px solid '
        f'{"#58a6ff" if is_editing else "#30363d"};border-radius:10px;'
        f'padding:16px 20px;margin-bottom:4px;border-left:4px solid {primaer}">',
        unsafe_allow_html=True,
    )

    col_logo, col_info, col_stats, col_btn = st.columns([1, 4, 4, 1])

    with col_logo:
        _logo_widget(v, width=52)

    with col_info:
        st.markdown(
            f'<div style="padding:4px 0">'
            f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px">'
            f'<span style="font-size:15px;font-weight:700;color:#e6edf3">{v["name"]}</span>'
            f'&nbsp;{_aktiv_badge_html(v.get("aktiv",1))}&nbsp;{_lizenz_badge_html(lizenztyp)}'
            f'</div>'
            + (f'<div style="font-size:12px;color:#8b949e">{ansp}</div>' if ansp else "")
            + (f'<div style="font-size:11px;color:#6e7681;margin-top:1px">{kontakt}</div>' if kontakt else "")
            + (f'<div style="font-size:10px;color:#6e7681">{adr}</div>' if adr else "")
            + (f'<div style="font-size:10px"><a href="{hp}" target="_blank" '
               f'style="color:#58a6ff">{hp}</a></div>' if hp else "")
            + f'<div style="margin-top:6px">{_lizenz_ablauf_html(v.get("lizenz_bis"))}</div>'
            + f'</div>',
            unsafe_allow_html=True,
        )

    with col_stats:
        st.markdown(
            f'<div style="padding:4px 0">'
            f'<div style="display:flex;gap:20px;margin-bottom:10px">'
            f'<div style="text-align:center">'
            f'<div style="font-size:22px;font-weight:800;color:#e6edf3">{stats["trainer"]}</div>'
            f'<div style="font-size:9px;color:#8b949e;letter-spacing:.5px">TRAINER</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:22px;font-weight:800;color:#e6edf3">{stats["spieler"]}</div>'
            f'<div style="font-size:9px;color:#8b949e;letter-spacing:.5px">SPIELER</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:22px;font-weight:800;color:#e6edf3">{stats["diagnostiken"]}</div>'
            f'<div style="font-size:9px;color:#8b949e;letter-spacing:.5px">DIAGNOSTIKEN</div></div>'
            f'</div>'
            + _progress_html("Trainer", stats["trainer"], max_t)
            + _progress_html("Spieler", stats["spieler"], max_s)
            + f'</div>',
            unsafe_allow_html=True,
        )

    with col_btn:
        st.markdown("<div style='padding-top:10px'>", unsafe_allow_html=True)
        btn_label = "✖ Schließen" if is_editing else "✏️ Bearbeiten"
        if st.button(btn_label, key=f"vv_edit_{v['id']}",
                     use_container_width=True,
                     type="secondary" if not is_editing else "secondary"):
            st.session_state["verein_edit_id"] = None if is_editing else v["id"]
            st.session_state["verein_neu"] = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="height:6px"></div>', unsafe_allow_html=True
    )


# ── Bearbeiten-Formular ───────────────────────────────────────────────────────

def _verein_edit_form(v: dict):
    vid       = v["id"]
    primaer   = v.get("farbe_primaer")   or _DEFAULT_PRIMAER
    sekundaer = v.get("farbe_sekundaer") or _DEFAULT_SEKUNDAER

    st.markdown(
        f'<div style="background:#161b22;border:1px solid #58a6ff;border-radius:12px;'
        f'padding:20px 24px;margin-bottom:16px;border-left:4px solid {primaer}">'
        f'<h3 style="color:#e6edf3;margin:0 0 2px">✏️ {v["name"]} bearbeiten</h3>'
        f'<p style="color:#8b949e;font-size:11px;margin:0">Verein-ID {vid}</p></div>',
        unsafe_allow_html=True,
    )

    tab_stamm, tab_design, tab_lizenz = st.tabs(
        ["📋 Stammdaten", "🎨 Logo & Design", "🔑 Lizenz & Limits"]
    )

    # ── Tab 1: Stammdaten ──────────────────────────────────────────────────────
    with tab_stamm:
        with st.form(f"vv_stamm_{vid}"):
            c1, c2 = st.columns(2)
            f_name  = c1.text_input("Vereinsname *",    value=v.get("name",""))
            f_ansp  = c2.text_input("Ansprechpartner",  value=v.get("ansprechpartner","") or "")
            f_email = c1.text_input("E-Mail",            value=v.get("email","") or "")
            f_tel   = c2.text_input("Telefon",           value=v.get("telefon","") or "")
            f_adr   = c1.text_input("Adresse",           value=v.get("adresse","") or "",
                                    placeholder="Musterstraße 1, 12345 Stadt")
            f_hp    = c2.text_input("Homepage",          value=v.get("homepage","") or "",
                                    placeholder="https://www.verein.de")
            f_aktiv = st.checkbox("Verein aktiv", value=bool(v.get("aktiv", 1)))

            if st.form_submit_button("💾 Stammdaten speichern", type="primary",
                                     use_container_width=True):
                if not f_name.strip():
                    st.error("Vereinsname ist erforderlich.")
                else:
                    verein_aktualisieren(
                        vid, name=f_name.strip(),
                        ansprechpartner=f_ansp.strip() or None,
                        email=f_email.strip() or None,
                        telefon=f_tel.strip() or None,
                        adresse=f_adr.strip() or None,
                        homepage=f_hp.strip() or None,
                        farbe_primaer=v.get("farbe_primaer"),
                        farbe_sekundaer=v.get("farbe_sekundaer"),
                        lizenztyp=v.get("lizenztyp"),
                        lizenz_bis=v.get("lizenz_bis"),
                        max_trainer=int(v.get("max_trainer") or 5),
                        max_spieler=int(v.get("max_spieler") or 50),
                        aktiv=1 if f_aktiv else 0,
                    )
                    st.success("✅ Stammdaten gespeichert.")
                    st.rerun()

    # ── Tab 2: Logo & Design ───────────────────────────────────────────────────
    with tab_design:
        # Logo
        lc1, lc2 = st.columns([1, 2])
        with lc1:
            st.markdown("**Aktuelles Logo**")
            _logo_widget(v, width=110)

        with lc2:
            st.markdown("**Logo hochladen**")
            upload = st.file_uploader(
                "PNG, JPG oder WEBP · Empfohlen: quadratisch, min. 200×200 px",
                type=["png","jpg","jpeg","webp"],
                key=f"vv_logo_up_{vid}",
                label_visibility="visible",
            )
            if upload:
                verein_logo_speichern(vid, upload.read())
                st.success("✅ Logo gespeichert.")
                st.rerun()
            if v.get("logo_blob"):
                if st.button("🗑 Logo entfernen", key=f"vv_logo_del_{vid}"):
                    verein_logo_speichern(vid, None)
                    st.rerun()

        st.markdown("---")

        # Farben
        st.markdown("**Vereinsfarben**")
        st.caption("Primärfarbe: Karten-Rand und Akzente · Sekundärfarbe: Highlights")
        dc1, dc2 = st.columns(2)
        new_prim = dc1.color_picker("Primärfarbe",   value=primaer,   key=f"vv_cp_p_{vid}")
        new_sek  = dc2.color_picker("Sekundärfarbe", value=sekundaer, key=f"vv_cp_s_{vid}")

        # Vorschau
        st.markdown(
            f'<div style="margin:12px 0;padding:14px 18px;border-radius:10px;'
            f'background:#0d1117;border:1px solid #30363d">'
            f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;'
            f'margin-bottom:10px">VORSCHAU</div>'
            f'<div style="background:#161b22;border-left:4px solid {new_prim};'
            f'border-radius:6px;padding:10px 14px;display:flex;align-items:center;gap:10px">'
            f'<div style="width:28px;height:28px;border-radius:6px;background:{new_prim}"></div>'
            f'<span style="font-size:14px;font-weight:700;color:#e6edf3">{v["name"]}</span>'
            f'<span style="font-size:12px;color:{new_sek};font-weight:600">●</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if st.button("💾 Farben speichern", key=f"vv_farben_save_{vid}", type="primary"):
            verein_aktualisieren(
                vid, name=v.get("name",""),
                ansprechpartner=v.get("ansprechpartner"),
                email=v.get("email"),
                telefon=v.get("telefon"),
                adresse=v.get("adresse"),
                homepage=v.get("homepage"),
                farbe_primaer=new_prim,
                farbe_sekundaer=new_sek,
                lizenztyp=v.get("lizenztyp"),
                lizenz_bis=v.get("lizenz_bis"),
                max_trainer=int(v.get("max_trainer") or 5),
                max_spieler=int(v.get("max_spieler") or 50),
                aktiv=v.get("aktiv", 1),
            )
            st.success("✅ Farben gespeichert.")
            st.rerun()

    # ── Tab 3: Lizenz & Limits ─────────────────────────────────────────────────
    with tab_lizenz:
        stats = verein_statistiken(vid)
        max_t = int(v.get("max_trainer") or 5)
        max_s = int(v.get("max_spieler") or 50)

        # Auslastung
        st.markdown("**Aktuelle Auslastung**")
        la1, la2, la3 = st.columns(3)
        pct_t = _pct(stats["trainer"], max_t)
        pct_s = _pct(stats["spieler"], max_s)
        la1.metric("Trainer",     f'{stats["trainer"]} / {max_t}',
                   delta=f"{pct_t} % belegt",
                   delta_color="inverse" if pct_t >= 100 else "off")
        la2.metric("Spieler",     f'{stats["spieler"]} / {max_s}',
                   delta=f"{pct_s} % belegt",
                   delta_color="inverse" if pct_s >= 100 else "off")
        la3.metric("Diagnostiken", stats["diagnostiken"])

        # Lizenz-Ablauf-Hinweis
        liz_html = _lizenz_ablauf_html(v.get("lizenz_bis"))
        st.markdown(
            f'<div style="margin:8px 0;padding:10px 14px;background:#0d1117;'
            f'border-radius:8px;border:1px solid #30363d">{liz_html}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("**Lizenzeinstellungen**")

        with st.form(f"vv_lizenz_{vid}"):
            lc1, lc2 = st.columns(2)
            cur_liz = v.get("lizenztyp") or "Basis"
            liz_idx = _LIZENZTYPEN.index(cur_liz) if cur_liz in _LIZENZTYPEN else 1
            f_liz   = lc1.selectbox("Lizenztyp", _LIZENZTYPEN, index=liz_idx)

            cur_bis = None
            if v.get("lizenz_bis"):
                try:
                    cur_bis = datetime.date.fromisoformat(str(v["lizenz_bis"]))
                except Exception:
                    pass
            if cur_bis is None:
                cur_bis = datetime.date.today().replace(
                    year=datetime.date.today().year + 1
                )
            f_bis = lc2.date_input("Lizenz gültig bis", value=cur_bis)

            f_mt = lc1.number_input("Max. Trainer", min_value=1,
                                     value=max_t)
            f_ms = lc2.number_input("Max. Spieler",  min_value=1,
                                     value=max_s)

            # Lizenztypen-Legende
            st.markdown(
                '<div style="margin:10px 0;padding:12px 14px;background:#0d1117;'
                'border-radius:8px;border:1px solid #30363d">'
                '<div style="font-size:10px;color:#8b949e;letter-spacing:1px;'
                'margin-bottom:8px">LIZENZTYPEN</div>'
                '<div style="display:flex;gap:6px;flex-wrap:wrap">'
                + "".join(
                    f'<span style="background:{_LIZ_COLORS[lt]}22;color:{_LIZ_COLORS[lt]};'
                    f'font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;'
                    f'border:1px solid {_LIZ_COLORS[lt]}44">{lt}</span>'
                    for lt in _LIZENZTYPEN
                )
                + '</div></div>',
                unsafe_allow_html=True,
            )

            if st.form_submit_button("💾 Lizenz speichern", type="primary",
                                     use_container_width=True):
                verein_aktualisieren(
                    vid, name=v.get("name",""),
                    ansprechpartner=v.get("ansprechpartner"),
                    email=v.get("email"),
                    telefon=v.get("telefon"),
                    adresse=v.get("adresse"),
                    homepage=v.get("homepage"),
                    farbe_primaer=v.get("farbe_primaer"),
                    farbe_sekundaer=v.get("farbe_sekundaer"),
                    lizenztyp=f_liz,
                    lizenz_bis=str(f_bis),
                    max_trainer=int(f_mt),
                    max_spieler=int(f_ms),
                    aktiv=v.get("aktiv", 1),
                )
                st.success("✅ Lizenz gespeichert.")
                st.rerun()
