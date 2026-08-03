"""Vereinsverwaltung (SaaS) — kompakte Übersicht, Nur für Superadmin."""

import datetime
import streamlit as st
from database import (
    vereine_laden, verein_speichern, verein_by_id,
    verein_aktualisieren, verein_logo_speichern,
    verein_aktivieren, verein_statistiken, verein_loeschen,
    benutzer_laden,
)

_LIZENZTYPEN = ["Test (30 Tage)", "Basis", "Standard", "Premium", "Enterprise"]
_LIZ_COLOR   = {
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


def _lizenz_badge(lt):
    c = _LIZ_COLOR.get(lt or "Basis", "#6e7681")
    return (f'<span style="background:{c}22;color:{c};font-size:10px;font-weight:700;'
            f'padding:2px 7px;border-radius:8px;border:1px solid {c}44">{lt or "Basis"}</span>')


def _aktiv_dot(aktiv):
    return "🟢" if aktiv else "⚫"


def _ablauf_text(lizenz_bis):
    if not lizenz_bis:
        return ""
    try:
        bis   = datetime.date.fromisoformat(str(lizenz_bis))
        tage  = (bis - datetime.date.today()).days
        if tage < 0:
            return f"⚠ abgelaufen"
        if tage <= 30:
            return f"⏳ {tage} Tage"
        return bis.strftime("%d.%m.%Y")
    except Exception:
        return str(lizenz_bis)


# ── Hauptseite ────────────────────────────────────────────────────────────────

def page_vereine():
    user = st.session_state.get("user", {})
    if user.get("rolle") != "Superadmin":
        st.error("⛔ Nur für Superadmin zugänglich.")
        return

    vereine       = vereine_laden()
    alle_benutzer = benutzer_laden()
    aktiv_n       = sum(1 for v in vereine if v.get("aktiv"))

    # ── Kopfzeile ─────────────────────────────────────────────────────────────
    st.title("🏢 Vereinsverwaltung")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Vereine",         len(vereine))
    m2.metric("Davon aktiv",     aktiv_n)
    m3.metric("Benutzer gesamt", len(alle_benutzer))
    m4.metric("Inaktive",        len(vereine) - aktiv_n)

    st.divider()

    # ── Neuen Verein anlegen ──────────────────────────────────────────────────
    with st.expander("➕ Neuen Verein anlegen"):
        _neuer_verein_form()

    if vereine:
        st.markdown(
            f'<div style="font-size:11px;color:#8b949e;margin:12px 0 4px;'
            f'letter-spacing:.5px">{len(vereine)} VEREINE — KLICKEN ZUM BEARBEITEN</div>',
            unsafe_allow_html=True,
        )

    # ── Vereinsliste als aufklappbare Zeilen ──────────────────────────────────
    for v in vereine:
        stats  = verein_statistiken(v["id"])
        lt     = v.get("lizenztyp") or "Basis"
        ablauf = _ablauf_text(v.get("lizenz_bis"))
        label  = (
            f"{_aktiv_dot(v.get('aktiv', 1))}  {v['name']}   "
            f"{'·  ' + lt + '   ' if lt else ''}"
            f"{'·  ' + ablauf + '   ' if ablauf else ''}"
            f"·  {stats['trainer']} Trainer  ·  {stats['spieler']} Spieler"
        )
        with st.expander(label):
            _verein_detail(v, stats)


# ── Neuer-Verein-Formular ────────────────────────────────────────────────────

def _neuer_verein_form():
    with st.form("vv_neu", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name   = c1.text_input("Vereinsname *")
        ansp   = c2.text_input("Ansprechpartner")
        email  = c1.text_input("E-Mail")
        tel    = c2.text_input("Telefon")
        liz    = c1.selectbox("Lizenz", _LIZENZTYPEN, index=1)
        bis    = c2.date_input(
            "Lizenz gültig bis",
            value=datetime.date.today().replace(year=datetime.date.today().year + 1),
        )
        mt = c1.number_input("Max. Trainer", min_value=1, value=5)
        ms = c2.number_input("Max. Spieler",  min_value=1, value=50)
        s1, s2 = st.columns(2)
        if s1.form_submit_button("✅ Anlegen", type="primary", use_container_width=True):
            if not name.strip():
                st.error("Vereinsname ist erforderlich.")
            else:
                vid = verein_speichern(name.strip())
                verein_aktualisieren(
                    vid, name=name.strip(),
                    ansprechpartner=ansp.strip() or None,
                    email=email.strip() or None,
                    telefon=tel.strip() or None,
                    lizenztyp=liz, lizenz_bis=str(bis),
                    max_trainer=int(mt), max_spieler=int(ms),
                )
                st.success(f"✅ **{name.strip()}** angelegt.")
                st.rerun()
        s2.form_submit_button("Abbrechen", use_container_width=True)


# ── Vereinsdetail (innerhalb des Expanders) ───────────────────────────────────

def _verein_detail(v: dict, stats: dict):
    vid       = v["id"]
    primaer   = v.get("farbe_primaer")   or _DEFAULT_PRIMAER
    sekundaer = v.get("farbe_sekundaer") or _DEFAULT_SEKUNDAER
    max_t     = int(v.get("max_trainer") or 5)
    max_s     = int(v.get("max_spieler") or 50)
    lt        = v.get("lizenztyp") or "Basis"

    # Kurze Statistik-Zeile
    pct_t = _pct(stats["trainer"], max_t)
    pct_s = _pct(stats["spieler"], max_s)
    st.markdown(
        f'<div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:12px;'
        f'padding:10px 14px;background:#0d1117;border-radius:8px;border:1px solid #21262d">'
        f'<span style="font-size:13px;color:#e6edf3"><b>{stats["trainer"]}</b>'
        f' <span style="color:#8b949e;font-size:11px">/ {max_t} Trainer</span></span>'
        f'<span style="color:#30363d">|</span>'
        f'<span style="font-size:13px;color:#e6edf3"><b>{stats["spieler"]}</b>'
        f' <span style="color:#8b949e;font-size:11px">/ {max_s} Spieler</span></span>'
        f'<span style="color:#30363d">|</span>'
        f'<span style="font-size:13px;color:#e6edf3"><b>{stats["diagnostiken"]}</b>'
        f' <span style="color:#8b949e;font-size:11px">Diagnostiken</span></span>'
        f'<span style="color:#30363d">|</span>'
        + _lizenz_badge(lt)
        + f'</div>',
        unsafe_allow_html=True,
    )

    tab_stamm, tab_design, tab_lizenz, tab_del = st.tabs(
        ["📋 Stammdaten", "🎨 Logo & Farben", "🔑 Lizenz & Limits", "🗑 Löschen"]
    )

    # ── Stammdaten ─────────────────────────────────────────────────────────────
    with tab_stamm:
        with st.form(f"s_{vid}"):
            c1, c2 = st.columns(2)
            f_name = c1.text_input("Vereinsname *",    value=v.get("name",""))
            f_ansp = c2.text_input("Ansprechpartner",  value=v.get("ansprechpartner","") or "")
            f_em   = c1.text_input("E-Mail",            value=v.get("email","")    or "")
            f_tel  = c2.text_input("Telefon",           value=v.get("telefon","")  or "")
            f_adr  = c1.text_input("Adresse",           value=v.get("adresse","")  or "")
            f_hp   = c2.text_input("Homepage",          value=v.get("homepage","") or "")
            f_ak   = st.checkbox("Verein aktiv", value=bool(v.get("aktiv", 1)))
            if st.form_submit_button("💾 Speichern", type="primary",
                                      use_container_width=True):
                if not f_name.strip():
                    st.error("Vereinsname ist erforderlich.")
                else:
                    verein_aktualisieren(
                        vid, name=f_name.strip(),
                        ansprechpartner=f_ansp.strip() or None,
                        email=f_em.strip() or None,
                        telefon=f_tel.strip() or None,
                        adresse=f_adr.strip() or None,
                        homepage=f_hp.strip() or None,
                        farbe_primaer=v.get("farbe_primaer"),
                        farbe_sekundaer=v.get("farbe_sekundaer"),
                        lizenztyp=v.get("lizenztyp"),
                        lizenz_bis=v.get("lizenz_bis"),
                        max_trainer=max_t, max_spieler=max_s,
                        aktiv=1 if f_ak else 0,
                    )
                    st.success("✅ Gespeichert.")
                    st.rerun()

    # ── Logo & Farben ──────────────────────────────────────────────────────────
    with tab_design:
        lc1, lc2 = st.columns([1, 2])
        with lc1:
            if v.get("logo_blob"):
                try:
                    st.image(bytes(v["logo_blob"]), width=100)
                except Exception:
                    st.caption("Logo nicht darstellbar")
            else:
                st.markdown(
                    f'<div style="width:100px;height:100px;border-radius:10px;'
                    f'background:{primaer}22;display:flex;align-items:center;'
                    f'justify-content:center;font-size:36px;border:1px dashed #30363d">🏟</div>',
                    unsafe_allow_html=True,
                )
        with lc2:
            up = st.file_uploader("Logo hochladen (PNG, JPG, WEBP)",
                                   type=["png","jpg","jpeg","webp"],
                                   key=f"lu_{vid}")
            if up:
                verein_logo_speichern(vid, up.read())
                st.success("✅ Logo gespeichert.")
                st.rerun()
            if v.get("logo_blob"):
                if st.button("🗑 Logo entfernen", key=f"ld_{vid}"):
                    verein_logo_speichern(vid, None)
                    st.rerun()

        dc1, dc2 = st.columns(2)
        new_p = dc1.color_picker("Primärfarbe",   value=primaer,   key=f"cp_{vid}")
        new_s = dc2.color_picker("Sekundärfarbe", value=sekundaer, key=f"cs_{vid}")

        st.markdown(
            f'<div style="padding:10px 14px;border-radius:8px;background:#0d1117;'
            f'border:1px solid #30363d;margin:8px 0">'
            f'<span style="font-size:11px;color:#8b949e">VORSCHAU · </span>'
            f'<span style="font-size:14px;font-weight:700;color:{new_p}">{v["name"]}</span>'
            f'&nbsp;<span style="color:{new_s}">●</span></div>',
            unsafe_allow_html=True,
        )

        if st.button("💾 Farben speichern", key=f"fs_{vid}", type="primary"):
            verein_aktualisieren(
                vid, name=v.get("name",""),
                ansprechpartner=v.get("ansprechpartner"),
                email=v.get("email"), telefon=v.get("telefon"),
                adresse=v.get("adresse"), homepage=v.get("homepage"),
                farbe_primaer=new_p, farbe_sekundaer=new_s,
                lizenztyp=v.get("lizenztyp"), lizenz_bis=v.get("lizenz_bis"),
                max_trainer=max_t, max_spieler=max_s, aktiv=v.get("aktiv", 1),
            )
            st.success("✅ Farben gespeichert.")
            st.rerun()

    # ── Lizenz & Limits ────────────────────────────────────────────────────────
    with tab_lizenz:
        # Auslastungsbalken
        la1, la2, la3 = st.columns(3)
        la1.metric("Trainer",     f"{stats['trainer']} / {max_t}",
                   f"{pct_t}% belegt",
                   delta_color="inverse" if pct_t >= 100 else "off")
        la2.metric("Spieler",     f"{stats['spieler']} / {max_s}",
                   f"{pct_s}% belegt",
                   delta_color="inverse" if pct_s >= 100 else "off")
        la3.metric("Diagnostiken", stats["diagnostiken"])

        with st.form(f"l_{vid}"):
            lc1, lc2 = st.columns(2)
            cur_liz = v.get("lizenztyp") or "Basis"
            li_idx  = _LIZENZTYPEN.index(cur_liz) if cur_liz in _LIZENZTYPEN else 1
            f_liz   = lc1.selectbox("Lizenztyp", _LIZENZTYPEN, index=li_idx)

            cur_bis = None
            if v.get("lizenz_bis"):
                try:
                    cur_bis = datetime.date.fromisoformat(str(v["lizenz_bis"]))
                except Exception:
                    pass
            if not cur_bis:
                cur_bis = datetime.date.today().replace(year=datetime.date.today().year + 1)
            f_bis = lc2.date_input("Gültig bis", value=cur_bis)
            f_mt  = lc1.number_input("Max. Trainer", min_value=1, value=max_t)
            f_ms  = lc2.number_input("Max. Spieler",  min_value=1, value=max_s)

            if st.form_submit_button("💾 Lizenz speichern", type="primary",
                                      use_container_width=True):
                verein_aktualisieren(
                    vid, name=v.get("name",""),
                    ansprechpartner=v.get("ansprechpartner"),
                    email=v.get("email"), telefon=v.get("telefon"),
                    adresse=v.get("adresse"), homepage=v.get("homepage"),
                    farbe_primaer=v.get("farbe_primaer"),
                    farbe_sekundaer=v.get("farbe_sekundaer"),
                    lizenztyp=f_liz, lizenz_bis=str(f_bis),
                    max_trainer=int(f_mt), max_spieler=int(f_ms),
                    aktiv=v.get("aktiv", 1),
                )
                st.success("✅ Lizenz gespeichert.")
                st.rerun()

    # ── Löschen ────────────────────────────────────────────────────────────────
    with tab_del:
        if stats["spieler"] > 0 or stats["trainer"] > 0:
            st.warning(
                f"Verein hat noch **{stats['trainer']} Trainer** und "
                f"**{stats['spieler']} Spieler**. Bitte zuerst entfernen."
            )
        confirmed = st.checkbox(
            f'**{v["name"]}** unwiderruflich löschen',
            key=f"dc_{vid}",
        )
        if st.button("🗑 Verein löschen", key=f"db_{vid}",
                     disabled=not confirmed, type="secondary"):
            ok, msg = verein_loeschen(vid)
            if ok:
                st.success(f"✅ **{v['name']}** gelöscht.")
                st.rerun()
            else:
                st.error(f"❌ {msg}")
