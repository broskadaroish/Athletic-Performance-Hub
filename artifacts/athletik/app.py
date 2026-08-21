"""
Athletic Performance Hub
────────────────────────────────────────
Main Streamlit entry point.  All pages live in this single file to keep
imports simple; shared logic is delegated to the module layer.
"""

# ─── Branding & Version ───────────────────────────────────────────────────────
APP_NAME      = "Athletic Performance Hub"
APP_VERSION   = "1.0.0"
APP_DEVELOPER = "Broska Daroish"
APP_EMAIL     = "support@aphsystem.de"
APP_PHONE     = "01741682671"
APP_COPYRIGHT = "\u00a9 2026 Broska Daroish. Alle Rechte vorbehalten."

import os
import streamlit as st
from datetime import date, datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ─── Produktions-Setup (einmalig beim Modulimport) ────────────────────────────
import config          # Env-Vars zentralisiert, ensure_dirs() läuft beim Import
import logging_config  # Logging konfigurieren + rotierende Logdatei in Produktion
_log = logging_config.logger

from theme import APP_CSS, C, PLOTLY_LAYOUT as _PL_BASE
from mobile import (
    inject_mobile_player_selector,
    handle_mobile_nav_params,
    render_mobile_nav,
    inject_mobile_player_header,
    inject_mobile_mehr_overlay,
    inject_scroll_to_top_if_needed,
    detect_screen_width,
    inject_mobile_sidebar_opener,
)
from help_ui import sicherheitshinweis_box, show_test_info, show_field_help, field_info_col, norm_badge, show_trainer_checkliste
from modules.legal_page import page_impressum, page_datenschutz, page_agb
from config import PRIVACY_POLICY_VERSION, TERMS_VERSION
from ui_components import (
    kpi_card, score_kpi, risk_kpi,
    player_banner, section_header, deficit_row, strength_row,
    test_status_card, empty_state,
    score_badge_html, risk_badge_html,
    anthro_karte,
    render_observation_selector,
)

from database import (
    init_db,
    spieler_speichern, spieler_laden, spieler_by_id, spieler_loeschen, spieler_aktualisieren,
    spieler_trainer_zuweisen,
    spieler_import_dubletten_laden, spieler_import_kapazitaet_laden, spieler_importieren,
    berechne_alter, alter_am_datum, altersklasse_vorschlag, parse_datum_safe,
    verletzung_speichern, verletzungen_laden, verletzung_loeschen,
    anthropometrie_speichern, anthropometrie_letzter, anthropometrie_history, anthropometrie_loeschen_letzten,
    fms_speichern, fms_letzter, fms_history, fms_history_full,
    y_balance_speichern, y_balance_letzter, y_balance_history, y_balance_history_full,
    trainingsplan_loeschen, trainingsplan_eintrag_speichern, trainingsplan_laden,
    plan_version_erstellen, plan_version_archivieren_aktiv, plan_version_aktivieren,
    plan_version_verwerfen, plan_aktive_version,
    plan_aktive_version_id, plan_versionen_laden, plan_laden_nach_version,
    plan_eintrag_loeschen, plan_eintrag_aktualisieren, plan_eintraege_position_tauschen,
    plan_notizen_speichern, plan_trainingszeit_setzen, plan_duplizieren,
    plan_eintrag_verteilen, plan_warmup_speichern,
    sprint_speichern, sprint_letzter, sprint_history,
    sprung_speichern, sprung_letzter, sprung_history,
    agilitaet_speichern, agilitaet_letzter, agilitaet_history,
    ausdauer_speichern, ausdauer_letzter, ausdauer_history,
    kraft_speichern, kraft_letzter, kraft_history,
    einwilligung_speichern, einwilligung_letzter, einwilligung_alle,
    zustimmung_registrierung_speichern,
    db_komplett_zuruecksetzen,
    backup_status_laden, db_backup_erstellen, spieler_mandant_pruefen,
    checkliste_custom_laden, checkliste_custom_speichern,
    logo_laden, logo_speichern, logo_loeschen,
    beobachtung_speichern,
    beobachtungen_alle_fuer_spieler,
    spiro_protokoll_alle, spiro_protokoll_speichern,
    spiro_test_speichern, spiro_test_letzter, spiro_test_alle,
    spiro_stufen_speichern, spiro_stufen_laden,
    spiro_nachbelastung_speichern, spiro_nachbelastung_laden,
    spiro_test_loeschen,
    benutzer_laden, benutzer_speichern, benutzer_aktivieren, benutzer_by_id,
    benutzer_passwort, benutzer_aktualisieren, benutzer_profil_aktualisieren,
    benutzer_foto_speichern, trainer_statistiken, benutzer_loeschen,
    vereine_laden, verein_speichern, verein_aktivieren,
    verein_by_id, verein_aktualisieren, verein_logo_speichern, verein_statistiken,
    spieler_null_zuweisen, spieler_ohne_verein_zaehlen,
    zuweisung_log_laden,
    benachrichtigungen_laden, benachrichtigungen_alle_gelesen,
    _pw_verify,
)
from auth import login, hash_password
from modules.benutzerverwaltung import page_benutzerverwaltung
from modules.vereine import page_vereine
from modules.trainerportal import page_trainerportal, page_mein_profil
from modules.saas_dashboard import page_saas_dashboard
from modules.lizenz_page import page_lizenz_vereinsadmin, page_lizenz_superadmin
from modules.kundenverwaltung import page_kundenverwaltung
from modules.mein_vertrag import page_mein_vertrag
from testprotokoll_pdf import (
    generate_testprotokoll, TEST_NAMEN, TEST_REIHENFOLGE,
)
from safety_texts import (
    ZWECKBESTIMMUNG_VERSION,
    ZWECKBESTIMMUNG_TITEL,
    ZWECKBESTIMMUNG_TEXT_DISPLAY,
    AMPEL_GRUEN, AMPEL_GELB, AMPEL_ROT, AMPEL_FUSSZEILE,
    TRAININGSPLAN_HINWEIS,
    PHV_HINWEIS,
    FMS_HINWEIS,
    BESCHWERDEN_HINWEIS,
    ABBRUCH_HINWEIS,
    PDF_FUSSZEILE,
    KURZ_HINWEIS,
    EMAIL_NACHRICHT_VORLAGE,
)
from anthropometrie import (
    bmi_berechnen, bmi_kategorie, phv_offset_berechnen,
    reifestatus_text, reifestatus_farbe, wachstum_berechnen,
    koerperfett_jp7, koerperfett_jp11,
)
from sprint import SprintErgebnis
from sprung import SprungErgebnis
from agilitaet import AgilitaetErgebnis, bewertung as agil_bewertung, bewertung_farbe as agil_farbe
from ausdauer import AusdauerErgebnis, trainingsbereiche, bewertung_farbe as aus_farbe

# ─── Konstanten ───────────────────────────────────────────────────────────────

POSITIONEN = [
    "Torwart", "Innenverteidiger", "Außenverteidiger (rechts)",
    "Außenverteidiger (links)", "Defensives Mittelfeld", "Zentrales Mittelfeld",
    "Offensives Mittelfeld", "Rechtes Mittelfeld", "Linkes Mittelfeld",
    "Rechter Flügel", "Linker Flügel", "Hängende Spitze", "Mittelstürmer",
]
ALTERSKLASSEN = [
    "U7 (Bambini)", "U8/U9 (F-Jugend)", "U10/U11 (E-Jugend)",
    "U12/U13 (D-Jugend)", "U14/U15 (C-Jugend)", "U16/U17 (B-Jugend)",
    "U18/U19 (A-Jugend)", "Senioren", "Ü-Mannschaft",
]
LEISTUNGSNIVEAUS  = ["Breitensport", "Leistungssport", "Regionalkader", "Landeskader", "Bundeskader", "Profi"]
TRAININGSSTATUS   = [
    "Uneingeschränktes Mannschaftstraining",
    "Angepasstes Mannschaftstraining",
    "Individuelles Training",
    "Trainingspause",
    "Externe Abklärung empfohlen",
    "Externe Freigabe dokumentiert",
]
VERLETZUNGSARTEN  = ["Muskel", "Sehne / Band", "Knochen / Knorpel", "Prellung / Kontusion", "Sonstiges"]
KOERPERTEILE      = ["Sprunggelenk", "Knie", "Oberschenkel", "Leiste", "Hüfte", "Lendenwirbel", "Schulter", "Sonstiges"]
SCHWEREGRADE      = ["Leicht (1–7 Tage)", "Mittel (8–28 Tage)", "Schwer (> 28 Tage)"]
from training import init_training_bibliothek, empfehlung_bereiche, uebungen_fuer_bereiche
from fms import FMSResult
from y_balance import YBalanceResult
from kraft import KraftErgebnis as _KraftErgebnis, epley_1rm as _epley_1rm
from analytics import (
    risiko_score, risiko_label, athletik_score, athletik_sub_scores,
    defizite_ermitteln, trainingsbereich_scores_ermitteln, schwerpunkt_sammeln, testdaten_uebersicht,
    ist_unauffaellig, ERHALTUNGS_SCHWERPUNKT, ERHALTUNGS_BEGRUENDUNG,
)
from periodisierung import (zyklus_erstellen, zyklus_laden, trainingsplan_multi_erstellen,
                             defizit_tabelle, _alter_zu_plangruppe, _PLANGRUPPEN_CONFIG, _POOL,
                             _equip_expanded, _equip_verfuegbar, _UEBUNG_EQUIPMENT,
                             _ALTERS_ERSATZ, verletzung_aktive_bereiche,
                             schaetze_tag_dauer_min, _ZEITBUDGET_CONFIG,
                             empfohlene_athletik_einheiten, empfohlene_athletik_tage,
                              _WOCHENTAGE_WP, _ausdauer_pool_fuer_plangruppe,
                               _pause_und_ausfuehrung, katalog_uebungen_fuer_bereich)
from trainingsphilosophie import (
    PHILOSOPHIEN, empfehle_philosophie, philosophie_erklaerung,
)
from database import philosophie_speichern as _philosophie_speichern
from database import philosophie_laden    as _philosophie_laden
from i18n import t, SPRACHEN, get_lang, set_lang
from pdf_report import generate_report, generate_vergleich_pdf, generate_trainingsplan_pdf
from warmup import (
    WARMUP_BEREICH, WARMUP_OPTIONEN, APH_STANDARD, FIFA_KOMPLETT,
    FIFA_INDIVIDUELL, KEIN_WARMUP, FIFA_TEILE,
    warmup_meta_lesen, warmup_details,
)
from saison import (fussballklasse_info as _fki, testreferenz_caption as _tcap,
                    saisonwechsel_laden as _sw_laden, saisonwechsel_speichern as _sw_speichern,
                    saison_label as _saison_label,
                    jugendklasse_aus_fussballklasse as _jugendklasse)
from pdf_anleitung import generate_anleitung_pdf, ALL_TEST_IDS, TEST_LABELS
from export import kader_excel_bytes, spieler_excel_bytes
from field_eval import alter_zu_altersgruppe, asymmetrie_badge_html, fms_asymmetrie_badge_html
from spieler_import import (
    IMPORT_FIELDS,
    auto_mapping as spieler_import_auto_mapping,
    build_preview as spieler_import_build_preview,
    import_candidates as spieler_import_candidates,
    read_upload as spieler_import_read_upload,
    revalidate_preview as spieler_import_revalidate_preview,
    upload_fingerprint as spieler_import_fingerprint,
    validate_mapping as spieler_import_validate_mapping,
)


# ─── Anleitung-Download-Button (wiederverwendbar auf jeder Testseite) ─────────

@st.cache_data(show_spinner=False, ttl=300)
def _generate_anleitung_cached(test_id: str, vereinsname: str, saison: str,
                               logo_bytes: bytes | None = None) -> bytes:
    """Generiert ein Einzel-Test-PDF (gecacht nach test_id + Vereinsinfos + Logo)."""
    return generate_anleitung_pdf(
        [test_id],
        mit_deckblatt=False,
        vereinsname=vereinsname,
        saison=saison,
        logo_bytes=logo_bytes,
    )


def _anleitung_download_button(test_id: str) -> None:
    """Zeigt einen kleinen PDF-Download-Button für die Testanleitung dieser Seite."""
    vn = st.session_state.get("cfg_vereinsname", "")
    sn = st.session_state.get("cfg_saison", "")
    try:
        pdf_bytes = _generate_anleitung_cached(test_id, vn, sn, logo_bytes=logo_laden())
    except Exception:
        return
    test_name = TEST_LABELS.get(test_id, test_id)
    fname = f"Anleitung_{test_name.replace(' ', '_')}.pdf"
    _, btn_col = st.columns([5, 1])
    with btn_col:
        st.download_button(
            label="📄 Anleitung",
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
            key=f"dl_anleitung_{test_id}",
            use_container_width=True,
            help=f"Testanleitung '{test_name}' als PDF herunterladen",
        )

# ─── Bootstrap ────────────────────────────────────────────────────────────────
init_db()
init_training_bibliothek()

# ─── Hintergrund-Scheduler: tägliche Lizenz-Ablauf-Prüfung ───────────────────
try:
    from lizenz_scheduler import start_lizenz_scheduler
    start_lizenz_scheduler()
except Exception as _sched_err:
    _log.warning("Lizenz-Scheduler konnte nicht gestartet werden: %s", _sched_err)

# ─── Startup: Zweckbestimmung bestätigen ──────────────────────────────────────
def _zweck_bestaetigt() -> bool:
    """True wenn die Zweckbestimmung dieser Version bereits bestätigt wurde."""
    if st.session_state.get("zweck_bestaetigt"):
        return True
    letzter = einwilligung_letzter()
    if letzter and letzter.get("version") == ZWECKBESTIMMUNG_VERSION:
        st.session_state["zweck_bestaetigt"] = True
        return True
    return False

# ─── Page config ──────────────────────────────────────────────────────────────
from PIL import Image as _PILImage
_APP_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "app_logo.png")
if not os.path.exists(_APP_ICON_PATH):
    _APP_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico")
if not os.path.exists(_APP_ICON_PATH):
    _APP_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
_app_icon_img = _PILImage.open(_APP_ICON_PATH) if os.path.exists(_APP_ICON_PATH) else "⚽"

st.set_page_config(
    page_title="Athletic Performance Hub",
    page_icon=_app_icon_img,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject central design system ────────────────────────────────────────────
st.markdown(APP_CSS, unsafe_allow_html=True)

# ─── Cookie-Controller (Session-Persistenz über Browser-Reload) ──────────────
try:
    from streamlit_cookies_controller import CookieController as _CookieController
    _cookie_ctrl = _CookieController(key="ath_sess_ctrl")
    _COOKIES_OK = True
except Exception:
    _cookie_ctrl = None
    _COOKIES_OK = False

_SESSION_IDLE_SEC = int(os.environ.get("SESSION_IDLE_TIMEOUT", "3600"))   # 1 Stunde
_SESSION_MAX_SEC  = int(os.environ.get("SESSION_MAX_LIFETIME", "86400"))  # 24 Stunden


def _app_base_url() -> str:
    """Ermittelt die Basis-URL der App für E-Mail-Links (Verifikation, Passwort-Reset)."""
    custom = os.environ.get("APP_BASE_URL", "")
    if custom:
        return custom.rstrip("/")
    dev = os.environ.get("REPLIT_DEV_DOMAIN", "")
    if dev:
        return f"https://{dev}/athletik/app"
    return "http://localhost:8082/app"


# ─── URL-Parameter lesen (E-Mail-Verifikation, Passwort-Reset) ────────────────
_qp_verify   = st.query_params.get("verify")
_qp_reset    = st.query_params.get("reset")
_qp_checkout = st.query_params.get("checkout")  # "success" | "cancel" nach Stripe-Rückkehr

# ─── Rechtliche Seiten ohne Login erreichbar (Impressum, Datenschutz, AGB) ────
# Gesetzt durch Buttons auf der Login-Seite. key: _legal_show ∈ {impressum|datenschutz|agb}
_legal_show_key = st.session_state.pop("_legal_show", None)
if _legal_show_key in ("impressum", "datenschutz", "agb"):
    if st.button("← Zurück zur Anmeldung", key="legal_back_btn"):
        st.rerun()
    st.markdown(
        '<hr style="border-color:#21262d;margin:8px 0 16px">',
        unsafe_allow_html=True,
    )
    if _legal_show_key == "impressum":
        page_impressum()
    elif _legal_show_key == "datenschutz":
        page_datenschutz()
    elif _legal_show_key == "agb":
        page_agb()
    st.stop()

# ─── Screen-Breite frühestmöglich ermitteln (auch auf der Login-Seite) ────────
# Hintergrund: render_mobile_nav() ruft _inject_screen_width_detect() intern auf.
# Wenn das erst NACH dem Login-Gate passiert, löst der erste Aufruf in der
# Haupt-App ein location.replace(?_sw=...) aus — das löscht die frisch erstellte
# Session und der Nutzer muss effektiv zweimal anmelden.
# Indem wir detect_screen_width() hier aufrufen (noch auf der Login-Seite),
# ist die Breite bereits bekannt wenn der Nutzer sich anmeldet → kein Reload nach Login.
detect_screen_width()

# ─── ?_sw= Legacy-Kompatibilität (wird von _inject_screen_width_detect konsumiert) ──
#
# _inject_screen_width_detect() liest und löscht ?_sw= bereits als erste Aktion
# (Step 2 in seinem Docstring).  Dieser Block hier dient nur noch als Fallback,
# falls der Param durch eine externe Quelle gesetzt wurde und detect_screen_width()
# ihn noch nicht konsumiert hat.  Im Normalfall ist _sw_early leer.
#
# KEIN location.replace() mehr: _inject_screen_width_detect() verwendet seit dem
# letzten Hotfix ausschließlich history.replaceState() (kein Browser-Reload) +
# st.rerun() (Streamlit-interner WebSocket-Rerun, kein Seitenaufruf).
_sw_early = st.query_params.get("_sw", "")
if _sw_early and "_screen_width" not in st.session_state:
    try:
        st.session_state["_screen_width"] = int(_sw_early)
    except (ValueError, TypeError):
        st.session_state["_screen_width"] = 768
    try:
        del st.query_params["_sw"]
    except Exception:
        pass

# ─── Login-Gate: Benutzer muss angemeldet sein ────────────────────────────────
if "user" not in st.session_state:

    # 1. Cookie-basierte Session-Wiederherstellung (nach Browser-Reload / externer Navigation)
    #
    # Hintergrund: CookieController ist eine React-Komponente. Nach einem normalen
    # Seiten-Reload benötigt sie 1 Rerun bis der Cookie-Wert verfügbar ist.
    # Nach einer top-level Navigation von einer externen Seite (Stripe Checkout,
    # E-Mail-Links etc.) baut Streamlit eine neue WebSocket-Verbindung auf — die
    # React-Komponente braucht dabei oft 2–4 Render-Zyklen bis sie den Browser-
    # Cookie zurückmeldet.
    #
    # Lösung: bis zu _COOKIE_MAX_WAIT Reruns abwarten, erst dann Login zeigen.
    # Die URL-Parameter (?checkout=success etc.) bleiben im Browser erhalten und
    # werden nach erfolgreichem Restore im eingeloggten Bereich korrekt verarbeitet.
    # Kein Token in URL — ausschließlich Cookie-basierte Authentifizierung.
    _COOKIE_MAX_WAIT = 8  # Maximale Wartezyklen bevor Login-Seite angezeigt wird
    # 8 × 0.35s = 2.8s: genug für langsame mobile Verbindungen bei Browser-Resume

    if _cookie_ctrl and not _qp_verify and not _qp_reset:
        try:
            _stored_sid = _cookie_ctrl.get("ath_sid")
            if _stored_sid:
                from database import session_validieren as _sv
                _restored = _sv(_stored_sid, idle_sek=_SESSION_IDLE_SEC)
                if _restored:
                    st.session_state["user"]           = _restored
                    st.session_state["_session_token"] = _stored_sid
                    # Zähler zurücksetzen: nächste externe Navigation beginnt bei 0
                    st.session_state.pop("_cookie_load_attempts", None)
                    st.rerun()
                # Cookie ist da, Session aber ungültig/abgelaufen → sofort Login.
                # Kein weiteres Warten nötig: der Cookie ist lesbar, die Session
                # ist einfach abgelaufen oder wurde serverseitig invalidiert.
            else:
                # Cookie noch nicht verfügbar — auf CookieController warten.
                _attempts = st.session_state.get("_cookie_load_attempts", 0)
                if _attempts < _COOKIE_MAX_WAIT:
                    st.session_state["_cookie_load_attempts"] = _attempts + 1
                    st.markdown(
                        '<div style="min-height:80vh;display:flex;align-items:center;'
                        'justify-content:center">'
                        '<div style="color:#8b949e;font-size:14px;text-align:center">'
                        '<div style="font-size:28px;margin-bottom:12px">⚙️</div>'
                        'Sitzung wird geprüft …</div></div>',
                        unsafe_allow_html=True,
                    )
                    import time
                    time.sleep(0.35)
                    st.rerun()
                # Nach _COOKIE_MAX_WAIT Versuchen kein Cookie → Login-Seite anzeigen.
                # _cookie_load_attempts bleibt im session_state, wird beim nächsten
                # Page-Load (neue Streamlit-Session) automatisch zurückgesetzt.
        except Exception:
            pass

    # ── Rerun-Schutz: Testszenarien-Checkliste ───────────────────────────────
    #
    # Die folgenden Szenarien beschreiben das erwartete Verhalten des
    # Session-Restore-Mechanismus. Zur manuellen Verifikation nach Änderungen:
    #
    # A) Normaler Browser-Reload mit gültigem ath_sid-Cookie:
    #    → CookieController liefert Cookie nach 1–2 Reruns.
    #    → session_validieren() gibt user-dict zurück → session_state["user"] gesetzt.
    #    → Nutzer sieht die App ohne Login-Aufforderung.
    #    → _cookie_load_attempts wird auf 0 zurückgesetzt.
    #
    # B) Rückkehr von Stripe Checkout (?checkout=success) mit gültigem Cookie:
    #    → Neue WebSocket-Verbindung → 2–4 Reruns bis Cookie lesbar.
    #    → Ladeanimation ("Sitzung wird geprüft …") erscheint bis zu 4× kurz.
    #    → Nach Restore: _qp_checkout="success" noch im Browser → Banner gesetzt.
    #    → Kein erneuter Login erforderlich.
    #
    # C) Erster Aufruf ohne Cookie (kein ath_sid im Browser):
    #    → _cookie_ctrl.get("ath_sid") → None für jeden Zyklus.
    #    → Ladeanimation läuft _COOKIE_MAX_WAIT (=4) Mal, dann Login-Seite.
    #    → _cookie_load_attempts wächst bis 4, danach kein weiterer Increment
    #      (Bedingung _attempts < _COOKIE_MAX_WAIT ist False → kein st.stop() mehr).
    #
    # D) Ungültiger oder abgelaufener ath_sid-Cookie:
    #    → _cookie_ctrl.get("ath_sid") liefert Token-String.
    #    → session_validieren() gibt None zurück (abgelaufen/invalidiert/version-mismatch).
    #    → Kein Warte-Zyklus, kein Increment — sofort Login-Seite.
    #
    # E) ?checkout=success ohne gültigen ath_sid-Cookie:
    #    → if "user" not in st.session_state → Login-Gate aktiv.
    #    → st.stop() am Ende des Login-Blocks (Zeile ~1157) verhindert Ausführung
    #      der Checkout-Verarbeitungslogik (Zeile ~1261).
    #    → Nutzer sieht Login-Seite; Param wird nicht als Authentifizierung gewertet.
    #
    # F) Gültige Session, aber session_token_version stimmt nicht überein
    #    (Passwort wurde nach Session-Erstellung geändert):
    #    → session_validieren() erkennt Version-Mismatch → Session deaktiviert → None.
    #    → Szenario D greift → sofort Login-Seite.
    #    → Alternativ: per-Rerun-Check (session_token_aktiv) nach Login-Gate invalidiert
    #      den session_state → __logout_ok__ gesetzt → Login mit Hinweismeldung.
    #
    # ── Rerun-Loop-Schutz ────────────────────────────────────────────────────
    # _cookie_load_attempts wird nur inkrementiert wenn _attempts < _COOKIE_MAX_WAIT.
    # Nach Erreichen des Limits keine st.stop() mehr → Login-Seite wird angezeigt.
    # Der Zähler verbleibt im session_state (wächst nicht weiter) und wird beim
    # nächsten echten Page-Load (neue Streamlit-Session) automatisch zurückgesetzt.

    # ── Zentrierter Container ─────────────────────────────────────────────────
    _lc1, _lc2, _lc3 = st.columns([1, 2, 1])
    with _lc2:
        _aph_logo_path = os.path.join(os.path.dirname(__file__), "assets", "aph_logo.png")
        if os.path.exists(_aph_logo_path):
            _li1, _li2, _li3 = st.columns([1, 2, 1])
            _li2.image(_aph_logo_path, width=120)
        st.markdown(
            '<h2 style="color:#e6edf3;text-align:center;margin:16px 0 4px;font-size:18px;'
            'letter-spacing:0.5px">ATHLETIC PERFORMANCE HUB</h2>'
            '<p style="color:#c9a84c;text-align:center;font-size:11px;font-weight:600;'
            'letter-spacing:2px;margin-bottom:24px">TESTS · ANALYSE · TRAINING</p>',
            unsafe_allow_html=True,
        )

        # Logout-Bestätigungsmeldung (gesetzt vom Logout-Button)
        if st.session_state.pop("__logout_ok__", False):
            if st.session_state.pop("__pw_changed__", False):
                st.success("✅ Passwort erfolgreich geändert. Bitte melde dich erneut an.")
            else:
                st.success("✅ Sie wurden erfolgreich abgemeldet.")

        # 2. E-Mail-Verifikation via URL-Parameter (?verify=TOKEN)
        if _qp_verify:
            from database import email_token_validieren as _etv
            _vbid = _etv(_qp_verify)
            if _vbid:
                st.success("✅ **E-Mail-Adresse erfolgreich bestätigt!** Du kannst dich jetzt anmelden.")
            else:
                st.error("❌ Der Bestätigungslink ist ungültig oder abgelaufen. Bitte fordere einen neuen an.")
            st.query_params.clear()
            if st.button("🔐 Zur Anmeldung", key="to_login_btn"):
                st.rerun()
            st.stop()

        # 3. Passwort-Reset via URL-Parameter (?reset=TOKEN)
        if _qp_reset:
            from database import pw_reset_token_validieren as _prtv, pw_reset_anwenden as _pra
            _reset_bid = _prtv(_qp_reset)
            if not _reset_bid:
                # §5: ungültiger/abgelaufener Token
                st.error("Dieser Link ist ungültig oder abgelaufen.")
                st.query_params.clear()
                if st.button("Neuen Passwort-Link anfordern", key="rp_new_request"):
                    st.rerun()
            else:
                st.markdown("### Neues Passwort vergeben")
                _rp1 = st.text_input("Neues Passwort",       type="password", key="rp_new1")
                _rp2 = st.text_input("Passwort bestätigen",  type="password", key="rp_new2")
                if st.button("Passwort ändern", type="primary",
                             use_container_width=True, key="rp_save"):
                    if len(_rp1) < 6:
                        st.error("Das Passwort muss mindestens 6 Zeichen lang sein.")
                    elif _rp1 != _rp2:
                        st.error("Die Passwörter stimmen nicht überein.")
                    else:
                        if _pra(_qp_reset, _rp1):
                            # §5: Erfolgsmeldung + [Zur Anmeldung]-Button
                            st.success("Dein Passwort wurde erfolgreich geändert.")
                            st.query_params.clear()
                            if st.button("Zur Anmeldung", type="primary", key="rp_to_login"):
                                st.rerun()
                        else:
                            st.error("Dieser Link ist ungültig oder abgelaufen.")
            st.stop()

        # 4. Erste Einrichtung — noch kein Benutzer vorhanden
        _alle_benutzer_login = benutzer_laden()
        if not _alle_benutzer_login:
            st.info("🚀 **Erste Einrichtung** — Lege den ersten Superadmin an.")
            _setup_email = st.text_input("E-Mail / Benutzername", key="setup_email")
            _setup_pw1   = st.text_input("Passwort",              key="setup_pw1", type="password")
            _setup_pw2   = st.text_input("Passwort bestätigen",   key="setup_pw2", type="password")
            if st.button("✅ Superadmin anlegen", type="primary",
                         use_container_width=True, key="setup_btn"):
                if not _setup_email.strip():
                    st.error("E-Mail fehlt.")
                elif len(_setup_pw1) < 4:
                    st.error("Passwort muss mindestens 4 Zeichen haben.")
                elif _setup_pw1 != _setup_pw2:
                    st.error("Passwörter stimmen nicht überein.")
                else:
                    _vid = verein_speichern("Standard-Verein")
                    _aid = benutzer_speichern(_vid, "Super", "Admin",
                                             _setup_email.strip(), _setup_pw1, "Superadmin",
                                             email_verifiziert=1)
                    _n = spieler_null_zuweisen(_vid, _aid)
                    if _n:
                        st.info(f"ℹ️ {_n} bestehende Spieler wurden dem Standard-Verein zugewiesen.")
                    st.success("✅ Superadmin angelegt — bitte jetzt anmelden.")
                    st.rerun()

        else:
            # 5. Login / Registrierung / Passwort vergessen / Benutzername vergessen
            _login_tab, _reg_tab, _trainer_tab = st.tabs([
                "🔐 Anmelden",
                "🏟️ Verein registrieren",
                "👤 Trainer registrieren",
            ])

            # ── Anmelden (mit Inline-Subviews für Passwort-/Benutzername-Vergessen) ──
            with _login_tab:
                # Sekundäre Buttons optisch dezenter machen
                st.markdown("""
                <style>
                button[kind="secondary"].login-secondary {
                    background: transparent !important;
                    border: 1px solid #30363d !important;
                    color: #8b949e !important;
                    font-size: 12px !important;
                }
                </style>
                """, unsafe_allow_html=True)

                _lsv = st.session_state.get("_login_subview", None)

                # ── Subview: Benutzername vergessen ───────────────────────────
                if _lsv == "benutzername":
                    st.markdown("#### 👤 Benutzername vergessen")
                    st.caption("Gib deine hinterlegte E-Mail-Adresse ein. "
                               "Falls ein Konto existiert, senden wir dir deinen Benutzernamen.")
                    _bn_input = st.text_input("E-Mail-Adresse", key="bn_input_inline",
                                              placeholder="trainer@verein.de")
                    _bn_c1, _bn_c2 = st.columns([1, 1])
                    if _bn_c1.button("← Zurück zur Anmeldung", key="bn_back_btn",
                                     use_container_width=True):
                        st.session_state["_login_subview"] = None
                        st.rerun()
                    if _bn_c2.button("👤 Benutzername anfordern", key="bn_send_inline",
                                     type="primary", use_container_width=True):
                        # Immer gleiche Meldung — kein Info-Leakage
                        st.info("Falls ein passendes Konto existiert, "
                                "erhältst du eine E-Mail mit deinem Benutzernamen.")
                        if _bn_input.strip():
                            import logging as _log_bn
                            _log_bn_inst = _log_bn.getLogger("athletik.email")
                            try:
                                from database import benutzername_reminder_laden as _brl
                                _log_bn_inst.info("Benutzername-Reminder angefordert für: %s",
                                                  _bn_input.strip()[:3] + "***")
                                _br = _brl(_bn_input.strip())
                                if _br:
                                    _br_uname, _br_name, _br_email = _br
                                    from email_service import send_username_reminder as _sur
                                    _log_bn_inst.info("Sende Benutzername-Reminder an verifizierte Adresse")
                                    _sur(_br_email, _br_name, _br_uname,
                                         os.environ.get("APP_BASE_URL", "https://aphsystem.de"))
                                    _log_bn_inst.info("Benutzername-Reminder erfolgreich gesendet")
                                else:
                                    _log_bn_inst.info("Benutzername-Reminder: kein passendes Konto gefunden")
                            except Exception as _e_bn:
                                _log_bn_inst.error(
                                    "Benutzername-Reminder fehlgeschlagen (%s) — "
                                    "SMTP_PASSWORD wird nicht geloggt.",
                                    type(_e_bn).__name__,
                                )

                # ── Subview: Passwort vergessen ───────────────────────────────
                elif _lsv == "passwort":
                    st.markdown("#### 🔑 Passwort vergessen")
                    st.caption("Gib deine E-Mail-Adresse oder deinen Benutzernamen ein. "
                               "Falls ein Konto existiert, senden wir dir einen Reset-Link.")
                    _pw_input = st.text_input("E-Mail-Adresse oder Benutzername",
                                              key="pw_input_inline",
                                              placeholder="trainer@verein.de")
                    _pw_c1, _pw_c2 = st.columns([1, 1])
                    if _pw_c1.button("← Zurück zur Anmeldung", key="pw_back_btn",
                                     use_container_width=True):
                        st.session_state["_login_subview"] = None
                        st.rerun()
                    if _pw_c2.button("🔑 Reset-Link anfordern", key="pw_send_inline",
                                     type="primary", use_container_width=True):
                        # Immer gleiche Meldung — kein Info-Leakage
                        st.info("Falls ein passendes Konto existiert, "
                                "haben wir eine E-Mail mit weiteren Anweisungen gesendet.")
                        if _pw_input.strip():
                            import logging as _log_pw
                            _log_pw_inst = _log_pw.getLogger("athletik.email")
                            try:
                                from database import pw_reset_token_erzeugen as _prte
                                _log_pw_inst.info("Passwort-Reset angefordert")
                                _rt = _prte(_pw_input.strip())
                                if _rt:
                                    _rt_token, _rt_name, _rt_email = _rt
                                    _log_pw_inst.info("Reset-Token erzeugt — sende E-Mail")
                                    from email_service import send_password_reset as _spr
                                    _spr(_rt_email, _rt_name, _rt_token, _app_base_url())
                                    _log_pw_inst.info("Passwort-Reset E-Mail erfolgreich gesendet")
                                else:
                                    _log_pw_inst.info("Passwort-Reset: kein passendes Konto gefunden")
                            except Exception as _e_pw:
                                _log_pw_inst.error(
                                    "Passwort-Reset E-Mail fehlgeschlagen (%s) — "
                                    "SMTP_PASSWORD wird nicht geloggt.",
                                    type(_e_pw).__name__,
                                )

                # ── Hauptformular: Login ──────────────────────────────────────
                else:
                    st.markdown(
                        '<div style="text-align:center;padding:8px 0 18px">'
                        '<h3 style="color:#e6edf3;font-size:20px;font-weight:700;margin:0 0 4px">'
                        'Willkommen zurück</h3>'
                        '<p style="color:#8b949e;font-size:13px;margin:0">'
                        'Melde dich an und öffne deinen APH-Bereich.</p>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    _login_email    = st.text_input(
                        "E-Mail oder Benutzername", key="login_email",
                        placeholder="trainer@verein.de"
                    )
                    _login_passwort = st.text_input("Passwort", key="login_pw", type="password")

                    # Sekundäre Links — dezent, unter den Feldern, vor dem Anmelden-Button
                    _sl1, _sl2 = st.columns(2)
                    if _sl1.button("👤 Benutzername vergessen?", key="goto_bn_btn",
                                   use_container_width=True):
                        st.session_state["_login_subview"] = "benutzername"
                        st.rerun()
                    if _sl2.button("🔑 Passwort vergessen?", key="goto_pw_btn",
                                   use_container_width=True):
                        st.session_state["_login_subview"] = "passwort"
                        st.rerun()

                    if st.button("🔐 ANMELDEN", type="primary",
                                 use_container_width=True, key="login_btn"):
                        try:
                            _client_ip = str(st.context.ip_address) if st.context.ip_address else None
                        except Exception:
                            _client_ip = None
                        _user_obj = login(_login_email.strip(), _login_passwort, ip=_client_ip)
                        if isinstance(_user_obj, dict) and _user_obj.get("gesperrt"):
                            _min_rest = max(1, round(_user_obj["verbleibend_sek"] / 60))
                            st.error(
                                f"🔒 Konto vorübergehend gesperrt — zu viele Fehlversuche. "
                                f"Bitte in ca. **{_min_rest} Minute(n)** erneut versuchen."
                            )
                        elif isinstance(_user_obj, dict) and _user_obj.get("wartend_auf_freischaltung"):
                            st.info(
                                "✅ Deine E-Mail-Adresse wurde bereits bestätigt.\n\n"
                                "Dein Zugang wartet noch auf die **Freischaltung durch den Administrator**. "
                                "Du erhältst eine E-Mail, sobald dein Konto freigeschaltet wurde."
                            )
                        elif isinstance(_user_obj, dict) and _user_obj.get("lizenz_gekuendigt"):
                            st.error(
                                "🚫 Dein Vertrag wurde beendet und dein Zugang ist nicht mehr aktiv.\n\n"
                                "Bei Fragen zur Reaktivierung kontaktiere uns unter "
                                "**support@aphsystem.de**."
                            )
                        elif isinstance(_user_obj, dict) and _user_obj.get("konto_deaktiviert"):
                            import os as _os_kd
                            _support  = _os_kd.environ.get("SUPPORT_EMAIL", "support@aphsystem.de")
                            _kd_rolle = (_user_obj.get("rolle") or "").lower()
                            if _kd_rolle in ("vereinsadmin", "verein"):
                                _kd_text = "Dein Vereinskonto wurde deaktiviert."
                            elif _kd_rolle in ("trainer", "einzeltrainer"):
                                _kd_text = "Dein Trainerkonto wurde deaktiviert."
                            else:
                                _kd_text = "Dein Konto wurde deaktiviert."
                            st.error(
                                f"⛔ {_kd_text} "
                                f"Bitte kontaktiere den APH-Support unter **{_support}**."
                            )
                        elif isinstance(_user_obj, dict) and _user_obj.get("email_nicht_verifiziert"):
                            _ev_bid   = _user_obj["benutzer_id"]
                            _ev_email = _user_obj["email"]
                            st.warning(
                                "📧 **Bitte bestätige zuerst deine E-Mail-Adresse.** "
                                "Wir haben dir beim Registrieren eine Bestätigungs-E-Mail geschickt."
                            )
                            if st.button("📧 Bestätigungs-E-Mail erneut senden",
                                         key="resend_verify_btn"):
                                from database import (
                                    email_token_erzeugen as _ete,
                                    email_token_resend_erlaubt as _etra,
                                    benutzer_by_id as _bbi,
                                )
                                if _etra(_ev_bid):
                                    _ntoken = _ete(_ev_bid)
                                    _bu = _bbi(_ev_bid) or {}
                                    try:
                                        from email_service import send_verification_email as _sve
                                        _sve(_ev_email, _bu.get("vorname") or "Benutzer",
                                             _ntoken, _app_base_url())
                                        st.success("✅ Bestätigungs-E-Mail erneut gesendet.")
                                    except Exception as _ee:
                                        st.warning(f"E-Mail konnte nicht gesendet werden: {_ee}")
                                else:
                                    st.info("Bitte warte mindestens 5 Minuten vor der nächsten Anforderung.")
                        elif _user_obj:
                            st.session_state["user"] = _user_obj
                            try:
                                from database import session_erstellen as _se
                                _new_sid = _se(
                                    _user_obj["id"],
                                    idle_sek=_SESSION_IDLE_SEC,
                                    max_sek=_SESSION_MAX_SEC,
                                    # Race-Schutz: Passwort wurde zwischen Verifikation
                                    # und Session-Erstellung geändert → ValueError
                                    expected_token_version=_user_obj.get(
                                        "session_token_version", 0
                                    ),
                                )
                                st.session_state["_session_token"] = _new_sid
                                if _cookie_ctrl:
                                    try:
                                        _cookie_ctrl.set("ath_sid", _new_sid,
                                                        max_age=_SESSION_MAX_SEC,
                                                        path="/",
                                                        secure=True, same_site="Lax")
                                    except TypeError:
                                        # Fallback für ältere Versionen ohne path-Parameter
                                        _cookie_ctrl.set("ath_sid", _new_sid,
                                                        max_age=_SESSION_MAX_SEC,
                                                        secure=True, same_site="Lax")
                                    # Cookie-Attribute:
                                    # path="/"        → Cookie gilt für gesamte Domain
                                    #                   (nicht nur den aktuellen Streamlit-Pfad)
                                    # secure=True     → nur über HTTPS übertragen
                                    # same_site="Lax" → Cookie wird bei top-level GET-Redirects
                                    #                   von externen Seiten mitgesendet (z. B.
                                    #                   Rückkehr von Stripe Checkout), aber NICHT
                                    #                   bei eingebetteten cross-site Requests
                                    #                   (CSRF-Schutz bleibt erhalten)
                            except ValueError:
                                # Passwort wurde während des Logins geändert —
                                # Anmeldung verweigern
                                st.error(
                                    "❌ Anmeldung fehlgeschlagen: Das Passwort wurde "
                                    "gerade geändert. Bitte erneut anmelden."
                                )
                                st.stop()
                            except Exception:
                                pass
                            st.rerun()
                        else:
                            st.error("❌ E-Mail/Benutzername oder Passwort falsch.")

            # ── Verein registrieren ───────────────────────────────────────────
            with _reg_tab:
                from license import LIZENZ_TYPEN as _REG_VLT
                _VEREIN_PAKETE = ["VEREIN_BASIC", "VEREIN_PRO"]

                # ── 1 · Paket wählen ──────────────────────────────────────────
                st.markdown(
                    '<div style="margin:8px 0 10px;padding:0 0 6px;border-bottom:1px solid #21262d">'
                    '<span style="color:#e6edf3;font-size:14px;font-weight:700">1 · Paket wählen</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div style="background:#0f2417;border:1px solid #2ea043;'
                    'border-radius:8px;padding:10px 14px;margin-bottom:12px;'
                    'font-size:13px;color:#3fb950;font-weight:600">'
                    '🎁 30 Tage kostenlos testen'
                    '<span style="color:#8b949e;font-weight:400;font-size:12px">'
                    ' — Heute keine Zahlung fällig</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                # Paket-Karten mit Auswahlzustand
                _cur_v_paket = st.session_state.get("reg_v_paket", _VEREIN_PAKETE[0])
                _rvc1, _rvc2 = st.columns(2)
                for _rpk, _rpc in zip(_VEREIN_PAKETE, [_rvc1, _rvc2]):
                    _rtd = _REG_VLT[_rpk]
                    _rms = "unbegrenzt" if _rtd["max_spieler"] is None else f"max. {_rtd['max_spieler']}"
                    _is_sel = (_rpk == _cur_v_paket)
                    _sel_border = "#f85149" if _is_sel else "#30363d"
                    _sel_bg     = "#1c1112" if _is_sel else "#161b22"
                    _sel_badge  = (
                        '<div style="display:inline-block;background:#f85149;color:#fff;'
                        'font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;'
                        'margin-bottom:4px">✓ Ausgewählt</div><br>' if _is_sel else ""
                    )
                    _rpc.markdown(
                        f'<div style="background:{_sel_bg};border:2px solid {_sel_border};'
                        f'border-radius:10px;padding:12px 14px;font-size:12px;line-height:1.8">'
                        f'{_sel_badge}'
                        f'<strong style="color:#e6edf3;font-size:13px">{_rtd["label"]}</strong><br>'
                        f'<span style="color:#3fb950;font-weight:600">{_rtd["preis_monat"]:.2f}\u202f€/Mo</span>'
                        f'<span style="color:#8b949e;font-size:11px">\u2002·\u2002{_rtd["preis_jahr"]:.0f}\u202f€/Jahr</span><br>'
                        f'<span style="color:#8b949e;font-size:11px">👥 max. {_rtd["max_trainer"]} Trainer'
                        f'\u2002·\u2002{_rms} Spieler</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                _r_paket = st.radio(
                    "Paket",
                    _VEREIN_PAKETE,
                    format_func=lambda k: _REG_VLT[k]["label"],
                    key="reg_v_paket",
                    horizontal=True,
                    label_visibility="collapsed",
                )
                _r_vsel = _REG_VLT[_r_paket]
                _r_intervall = st.radio(
                    "Abrechnungsintervall *",
                    ["monat", "jahr"],
                    format_func=lambda x, _td=_r_vsel: (
                        f"Monatlich — {_td['preis_monat']:.2f}\u202f€/Monat"
                        if x == "monat"
                        else f"Jährlich — {_td['preis_jahr']:.0f}\u202f€/Jahr"
                             f"  ✓ günstiger als 12 Monatszahlungen"
                    ),
                    key="reg_v_intervall",
                )

                # ── 2 · Zugangsdaten ──────────────────────────────────────────
                st.markdown(
                    '<div style="margin:14px 0 10px;padding:0 0 6px;border-bottom:1px solid #21262d">'
                    '<span style="color:#e6edf3;font-size:14px;font-weight:700">2 · Zugangsdaten</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                _r_verein   = st.text_input("Vereinsname *",                key="reg_verein",
                                            placeholder="FC Musterstadt")
                _rr1, _rr2  = st.columns(2)
                _r_vorname  = _rr1.text_input("Vorname Ansprechpartner *",  key="reg_vorname")
                _r_nachname = _rr2.text_input("Nachname Ansprechpartner *", key="reg_nachname")
                _r_email    = st.text_input("E-Mail-Adresse *",             key="reg_email",
                                            placeholder="admin@verein.de")
                _r_uname    = st.text_input("Benutzername *",               key="reg_benutzername",
                                            placeholder="mein_benutzername")
                _rp1, _rp2  = st.columns(2)
                _r_pw1      = _rp1.text_input("Passwort *",                 key="reg_pw1", type="password")
                _r_pw2      = _rp2.text_input("Passwort bestätigen *",      key="reg_pw2", type="password")

                # ── 3 · Rechnungsdaten ────────────────────────────────────────
                st.markdown(
                    '<div style="margin:14px 0 10px;padding:0 0 6px;border-bottom:1px solid #21262d">'
                    '<span style="color:#e6edf3;font-size:14px;font-weight:700">3 · Rechnungsdaten</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                with st.expander("📄 Rechnungsadresse (Pflichtangabe)", expanded=True):
                    _rb1, _rb2 = st.columns(2)
                    _r_ra_firma    = _rb1.text_input("Firma/Verein (optional)",  key="reg_ra_firma")
                    _r_ra_tel      = _rb2.text_input("Telefon (optional)",       key="reg_ra_tel")
                    _rb3, _rb4 = st.columns(2)
                    _r_ra_vorname  = _rb3.text_input("Vorname *",                key="reg_ra_vorname")
                    _r_ra_nachname = _rb4.text_input("Nachname *",               key="reg_ra_nachname")
                    _rb5, _rb6 = st.columns([3, 1])
                    _r_ra_strasse  = _rb5.text_input("Straße *",                 key="reg_ra_strasse")
                    _r_ra_hnr      = _rb6.text_input("Nr. *",                    key="reg_ra_hnr")
                    _rb7, _rb8 = st.columns([1, 2])
                    _r_ra_plz      = _rb7.text_input("PLZ *",                    key="reg_ra_plz")
                    _r_ra_ort      = _rb8.text_input("Ort *",                    key="reg_ra_ort")
                    _rb9, _rb10 = st.columns(2)
                    _r_ra_land     = _rb9.text_input("Land *",                   key="reg_ra_land",
                                                     value="Deutschland")
                    _r_ra_remail   = _rb10.text_input("Rechnungs-E-Mail *",      key="reg_ra_remail",
                                                      placeholder="rechnung@verein.de")
                    _r_ra_ustid    = st.text_input("Umsatzsteuer-ID (optional)", key="reg_ra_ustid")

                # ── 4 · Rechtliches ───────────────────────────────────────────
                st.markdown(
                    '<div style="margin:14px 0 10px;padding:0 0 6px;border-bottom:1px solid #21262d">'
                    '<span style="color:#e6edf3;font-size:14px;font-weight:700">4 · Rechtliches</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div style="background:#161b22;border:1px solid #30363d;'
                    'border-radius:8px;padding:12px 14px;margin:4px 0 12px">',
                    unsafe_allow_html=True,
                )
                _rds_c1, _rds_c2 = st.columns([6, 1])
                _r_datenschutz = _rds_c1.checkbox(
                    "Ich habe die Datenschutzerklärung gelesen und akzeptiere sie.",
                    key="reg_v_datenschutz",
                )
                if _rds_c2.button("📖 Lesen", key="reg_v_open_ds",
                                  help="Datenschutzerklärung öffnen"):
                    st.session_state["_legal_show"] = "datenschutz"
                    st.rerun()
                _ragb_c1, _ragb_c2 = st.columns([6, 1])
                _r_agb = _ragb_c1.checkbox(
                    "Ich habe die AGB / Nutzungsbedingungen gelesen und akzeptiere sie.",
                    key="reg_v_agb",
                )
                if _ragb_c2.button("📖 Lesen", key="reg_v_open_agb",
                                   help="AGB / Nutzungsbedingungen öffnen"):
                    st.session_state["_legal_show"] = "agb"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

                st.caption("Heute keine Zahlung. Anschließend gemäß gewähltem Tarif.")
                if st.button("🚀 30 TAGE KOSTENLOS STARTEN", type="primary",
                             use_container_width=True, key="reg_btn"):
                    _rerr = []
                    if not _r_datenschutz or not _r_agb:
                        _rerr.append(
                            "Bitte akzeptiere die Datenschutzerklärung und die "
                            "AGB / Nutzungsbedingungen, um die Registrierung abzuschließen."
                        )
                    if not _r_verein.strip():            _rerr.append("Vereinsname fehlt.")
                    if not _r_vorname.strip() or not _r_nachname.strip():
                        _rerr.append("Vor- und Nachname des Ansprechpartners fehlen.")
                    if not _r_email.strip() or "@" not in _r_email:
                        _rerr.append("Bitte gültige E-Mail-Adresse eingeben.")
                    if not _r_uname.strip():             _rerr.append("Benutzername fehlt.")
                    if len(_r_pw1) < 6:                  _rerr.append("Passwort mind. 6 Zeichen.")
                    elif _r_pw1 != _r_pw2:               _rerr.append("Passwörter stimmen nicht überein.")
                    if not _r_ra_vorname.strip() or not _r_ra_nachname.strip():
                        _rerr.append("Rechnungsadresse: Vor-/Nachname fehlen.")
                    if not _r_ra_strasse.strip() or not _r_ra_hnr.strip():
                        _rerr.append("Rechnungsadresse: Straße und Hausnummer fehlen.")
                    if not _r_ra_plz.strip() or not _r_ra_ort.strip():
                        _rerr.append("Rechnungsadresse: PLZ und Ort fehlen.")
                    if not _r_ra_land.strip():           _rerr.append("Rechnungsadresse: Land fehlt.")
                    if not _r_ra_remail.strip() or "@" not in _r_ra_remail:
                        _rerr.append("Rechnungsadresse: Rechnungs-E-Mail fehlt oder ungültig.")
                    if _rerr:
                        for _e in _rerr: st.error(_e)
                    if _r_paket not in _VEREIN_PAKETE:
                        _rerr.append(f"Ungültiges Paket: {_r_paket!r}.")
                    if _r_intervall not in ("monat", "jahr"):
                        _rerr.append("Ungültiges Abrechnungsintervall.")
                    if _rerr:
                        for _e in _rerr: st.error(_e)
                    else:
                        try:
                            from database import verein_registrieren, rechnungsadresse_speichern as _ras
                            _vid, _bid = verein_registrieren(
                                _r_verein.strip(), _r_vorname.strip(),
                                _r_nachname.strip(), _r_email.strip(), _r_pw1,
                                benutzername=_r_uname.strip(),
                                lizenztyp=_r_paket,
                                abo_intervall=_r_intervall,
                            )
                            _ras(_bid,
                                 firma=_r_ra_firma.strip() or None,
                                 vorname=_r_ra_vorname.strip(),
                                 nachname=_r_ra_nachname.strip(),
                                 strasse=_r_ra_strasse.strip(),
                                 hausnummer=_r_ra_hnr.strip(),
                                 plz=_r_ra_plz.strip(),
                                 ort=_r_ra_ort.strip(),
                                 land=_r_ra_land.strip(),
                                 rechnung_email=_r_ra_remail.strip(),
                                 telefon=_r_ra_tel.strip() or None,
                                 ust_id=_r_ra_ustid.strip() or None)
                            zustimmung_registrierung_speichern(
                                _bid, PRIVACY_POLICY_VERSION, TERMS_VERSION
                            )
                            from database import email_token_erzeugen as _ete
                            _vtoken = _ete(_bid)
                            _reg_email_ok = False
                            try:
                                from email_service import send_verification_email as _sve
                                _sve(_r_email.strip(), _r_vorname.strip(),
                                     _vtoken, _app_base_url())
                                _reg_email_ok = True
                            except Exception as _smtp_err:
                                import logging as _log_reg
                                _log_reg.getLogger("athletik.email").error(
                                    "Verein-Reg: Bestätigungs-E-Mail konnte nicht gesendet werden "
                                    "(%s). SMTP-Passwort wird nicht geloggt.",
                                    type(_smtp_err).__name__,
                                )
                                st.session_state["_reg_pending_bid"]   = _bid
                                st.session_state["_reg_pending_email"] = _r_email.strip()
                            if _reg_email_ok:
                                st.success(
                                    "✅ Verein erfolgreich registriert! "
                                    "Bitte bestätige deine E-Mail-Adresse — "
                                    "wir haben dir eine Bestätigungs-E-Mail gesendet."
                                )
                            else:
                                st.warning(
                                    "✅ Dein Konto wurde erstellt, aber die Bestätigungs-E-Mail "
                                    "konnte momentan nicht versendet werden. "
                                    "Bitte versuche, die Bestätigungs-E-Mail erneut anzufordern."
                                )
                                if st.button("📧 Bestätigungs-E-Mail erneut senden",
                                             key="reg_resend_verein_btn"):
                                    _rpb = st.session_state.get("_reg_pending_bid")
                                    _rpe = st.session_state.get("_reg_pending_email","")
                                    if _rpb:
                                        from database import (
                                            email_token_erzeugen as _ete2,
                                            email_token_resend_erlaubt as _etra2,
                                            benutzer_by_id as _bbi2,
                                        )
                                        if _etra2(_rpb):
                                            _nt2 = _ete2(_rpb)
                                            _bu2 = _bbi2(_rpb) or {}
                                            try:
                                                from email_service import send_verification_email as _sve2
                                                _sve2(_rpe, _bu2.get("vorname","Benutzer"),
                                                      _nt2, _app_base_url())
                                                st.success("✅ Bestätigungs-E-Mail gesendet.")
                                            except Exception as _e2:
                                                st.warning(f"E-Mail konnte nicht gesendet werden: {type(_e2).__name__}")
                        except ValueError as _ve:
                            st.error(str(_ve))
                        except Exception as _ex:
                            st.error(f"Fehler bei der Registrierung: {_ex}")

            # ── Trainer registrieren ──────────────────────────────────────────
            with _trainer_tab:
                # ── Registrierungsmodus wählen ────────────────────────────────────────
                _trainer_modus = st.radio(
                    "Wie möchtest du APH nutzen?",
                    ["eigenstaendig", "beitreten"],
                    format_func=lambda x: (
                        "🎯 Als eigener Trainer registrieren"
                        if x == "eigenstaendig"
                        else "🤝 Einem Verein beitreten"
                    ),
                    key="trainer_modus",
                    horizontal=True,
                )
                st.divider()

                # ── Option B: Einem Verein beitreten ─────────────────────────────────
                if _trainer_modus == "beitreten":
                    st.markdown(
                        '<div style="background:#0d1e2d;border:1px solid #1f6feb;'                        'border-radius:8px;padding:10px 14px;margin-bottom:12px;'                        'font-size:13px;color:#58a6ff;font-weight:600">'                        '🤝 Mit Beitrittscode einem bestehenden Verein beitreten</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        "Den Beitrittscode erhältst du von deinem Vereinsadmin. "
                        "Nach der Registrierung muss dein Konto freigegeben werden."
                    )
                    st.markdown("---")
                    _bj_code = st.text_input(
                        "Trainer-Beitrittscode *",
                        key="bj_code",
                        placeholder="z. B. ABC123",
                        help="Den Code erhältst du von deinem Vereinsadmin.",
                    )
                    _bj_c1, _bj_c2 = st.columns(2)
                    _bj_vorname  = _bj_c1.text_input("Vorname *",    key="bj_vorname")
                    _bj_nachname = _bj_c2.text_input("Nachname *",   key="bj_nachname")
                    _bj_email    = st.text_input(
                        "E-Mail-Adresse *", key="bj_email",
                        placeholder="trainer@verein.de",
                    )
                    _bj_uname    = st.text_input(
                        "Benutzername *", key="bj_benutzername",
                        placeholder="mein_benutzername",
                    )
                    _bj_p1, _bj_p2 = st.columns(2)
                    _bj_pw1 = _bj_p1.text_input("Passwort *", key="bj_pw1", type="password")
                    _bj_pw2 = _bj_p2.text_input("Passwort bestätigen *", key="bj_pw2", type="password")
                    st.markdown(
                        '<div style="background:#161b22;border:1px solid #30363d;'                        'border-radius:8px;padding:12px 14px;margin:8px 0 12px">',
                        unsafe_allow_html=True,
                    )
                    _bj_ds_c1, _bj_ds_c2 = st.columns([6, 1])
                    _bj_datenschutz = _bj_ds_c1.checkbox(
                        "Ich habe die Datenschutzerklärung gelesen und akzeptiere sie.",
                        key="bj_datenschutz",
                    )
                    if _bj_ds_c2.button("📖 Lesen", key="bj_open_ds"):
                        st.session_state["_legal_show"] = "datenschutz"
                        st.rerun()
                    _bj_agb_c1, _bj_agb_c2 = st.columns([6, 1])
                    _bj_agb = _bj_agb_c1.checkbox(
                        "Ich habe die AGB / Nutzungsbedingungen gelesen und akzeptiere sie.",
                        key="bj_agb",
                    )
                    if _bj_agb_c2.button("📖 Lesen", key="bj_open_agb"):
                        st.session_state["_legal_show"] = "agb"
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    if st.button("🤝 Verein beitreten", type="primary",
                                 use_container_width=True, key="bj_submit_btn"):
                        _bj_errs = []
                        if not _bj_code.strip():
                            _bj_errs.append("Beitrittscode fehlt.")
                        if not _bj_vorname.strip() or not _bj_nachname.strip():
                            _bj_errs.append("Vor- und Nachname fehlen.")
                        if not _bj_email.strip() or "@" not in _bj_email:
                            _bj_errs.append("Bitte gültige E-Mail-Adresse eingeben.")
                        if not _bj_uname.strip():
                            _bj_errs.append("Benutzername fehlt.")
                        if len(_bj_pw1) < 6:
                            _bj_errs.append("Passwort muss mindestens 6 Zeichen haben.")
                        elif _bj_pw1 != _bj_pw2:
                            _bj_errs.append("Passwörter stimmen nicht überein.")
                        if not _bj_datenschutz or not _bj_agb:
                            _bj_errs.append(
                                "Bitte akzeptiere die Datenschutzerklärung und die AGB."
                            )
                        if _bj_errs:
                            for _be in _bj_errs:
                                st.error(_be)
                        else:
                            try:
                                from database import (
                                    verein_by_registriercode as _vbrc,
                                    trainer_verein_beitreten as _tvb,
                                    email_token_erzeugen as _ete_bj,
                                )
                                # E-Mail-Existenz-Check: Hinweis statt Fehlermeldung
                                from database import (
                                    benutzer_email_existiert as _bee,
                                )
                                if _bee(_bj_email.strip()):
                                    st.info(
                                        "ℹ️ **Ein Konto mit dieser E-Mail-Adresse existiert bereits.** "
                                        "Bitte melde dich zuerst an. Mehrere Vereinsmitgliedschaften "
                                        "können nach dem Login in deinem Profil unter "
                                        "**Meine Vereine** verwaltet werden.",
                                        icon="ℹ️",
                                    )
                                    st.stop()
                                _bj_verein = _vbrc(_bj_code.strip())
                                if _bj_verein is None:
                                    st.error("❌ Der Beitrittscode ist ungültig.")
                                else:
                                    _bj_bid = _tvb(
                                        _bj_verein["id"],
                                        _bj_vorname.strip(),
                                        _bj_nachname.strip(),
                                        _bj_email.strip(),
                                        _bj_pw1,
                                        benutzername=_bj_uname.strip(),
                                    )
                                    zustimmung_registrierung_speichern(
                                        _bj_bid, PRIVACY_POLICY_VERSION, TERMS_VERSION
                                    )
                                    _bj_email_ok = False
                                    try:
                                        _bj_tok = _ete_bj(_bj_bid)
                                        from email_service import (
                                            send_verification_email as _sve_bj,
                                        )
                                        _sve_bj(
                                            _bj_email.strip(),
                                            _bj_vorname.strip(),
                                            _bj_tok,
                                            _app_base_url(),
                                        )
                                        _bj_email_ok = True
                                    except Exception as _bj_smtp_e:
                                        import logging as _log_bj
                                        _log_bj.getLogger("athletik.email").error(
                                            "Beitritt-Reg: Verifizierungs-E-Mail "
                                            "fehlgeschlagen (%s).",
                                            type(_bj_smtp_e).__name__,
                                        )
                                    st.success(
                                        f"✅ Registrierung bei "
                                        f"**{_bj_verein['name']}** erfolgreich! "
                                        "Dein Konto wird vom Vereinsadmin freigeschaltet."
                                        + (" Bitte bestätige deine E-Mail-Adresse."
                                           if _bj_email_ok else "")
                                    )
                            except ValueError as _bj_ve:
                                st.error(f"❌ {_bj_ve}")
                            except Exception as _bj_ex:
                                st.error(f"Fehler bei der Registrierung: {_bj_ex}")

                # ── Option A: Eigener Trainer (bestehender Flow) ──────────────────────
                if _trainer_modus == "eigenstaendig":

                    from license import LIZENZ_TYPEN as _REG_TLT
                    _TRAINER_PAKETE = ["TRAINER_BASIC", "TRAINER_PRO"]

                    # ── 1 · Paket wählen ──────────────────────────────────────────
                    st.markdown(
                        '<div style="margin:8px 0 10px;padding:0 0 6px;border-bottom:1px solid #21262d">'
                        '<span style="color:#e6edf3;font-size:14px;font-weight:700">1 · Paket wählen</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        '<div style="background:#0f2417;border:1px solid #2ea043;'
                        'border-radius:8px;padding:10px 14px;margin-bottom:12px;'
                        'font-size:13px;color:#3fb950;font-weight:600">'
                        '🎁 30 Tage kostenlos testen'
                        '<span style="color:#8b949e;font-weight:400;font-size:12px">'
                        ' — Heute keine Zahlung fällig</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    # Paket-Karten mit Auswahlzustand
                    _cur_t_paket = st.session_state.get("reg_t_paket", _TRAINER_PAKETE[0])
                    _ttc1, _ttc2 = st.columns(2)
                    for _tpk, _tpc in zip(_TRAINER_PAKETE, [_ttc1, _ttc2]):
                        _ttd = _REG_TLT[_tpk]
                        _tms = "unbegrenzt" if _ttd["max_spieler"] is None else f"max. {_ttd['max_spieler']}"
                        _t_is_sel = (_tpk == _cur_t_paket)
                        _t_sel_border = "#f85149" if _t_is_sel else "#30363d"
                        _t_sel_bg     = "#1c1112" if _t_is_sel else "#161b22"
                        _t_sel_badge  = (
                            '<div style="display:inline-block;background:#f85149;color:#fff;'
                            'font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;'
                            'margin-bottom:4px">✓ Ausgewählt</div><br>' if _t_is_sel else ""
                        )
                        _tpc.markdown(
                            f'<div style="background:{_t_sel_bg};border:2px solid {_t_sel_border};'
                            f'border-radius:10px;padding:12px 14px;font-size:12px;line-height:1.8">'
                            f'{_t_sel_badge}'
                            f'<strong style="color:#e6edf3;font-size:13px">{_ttd["label"]}</strong><br>'
                            f'<span style="color:#3fb950;font-weight:600">{_ttd["preis_monat"]:.2f}\u202f€/Mo</span>'
                            f'<span style="color:#8b949e;font-size:11px">\u2002·\u2002{_ttd["preis_jahr"]:.0f}\u202f€/Jahr</span><br>'
                            f'<span style="color:#8b949e;font-size:11px">👤 {_ttd["max_trainer"]} Trainer'
                            f'\u2002·\u2002{_tms} Spieler</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    _t_paket = st.radio(
                        "Paket",
                        _TRAINER_PAKETE,
                        format_func=lambda k: _REG_TLT[k]["label"],
                        key="reg_t_paket",
                        horizontal=True,
                        label_visibility="collapsed",
                    )
                    _t_tsel = _REG_TLT[_t_paket]
                    _t_intervall = st.radio(
                        "Abrechnungsintervall *",
                        ["monat", "jahr"],
                        format_func=lambda x, _td=_t_tsel: (
                            f"Monatlich — {_td['preis_monat']:.2f}\u202f€/Monat"
                            if x == "monat"
                            else f"Jährlich — {_td['preis_jahr']:.0f}\u202f€/Jahr"
                                 f"  ✓ günstiger als 12 Monatszahlungen"
                        ),
                        key="reg_t_intervall",
                    )

                    # ── 2 · Zugangsdaten ──────────────────────────────────────────
                    st.markdown(
                        '<div style="margin:14px 0 10px;padding:0 0 6px;border-bottom:1px solid #21262d">'
                        '<span style="color:#e6edf3;font-size:14px;font-weight:700">2 · Zugangsdaten</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    _tt1, _tt2 = st.columns(2)
                    _t_vorname  = _tt1.text_input("Vorname *",      key="trainer_vorname")
                    _t_nachname = _tt2.text_input("Nachname *",     key="trainer_nachname")
                    _t_email    = st.text_input("E-Mail-Adresse *", key="trainer_email",
                                                placeholder="trainer@verein.de")
                    _t_uname    = st.text_input("Benutzername *",   key="trainer_benutzername",
                                                placeholder="mein_benutzername")
                    _tp1, _tp2 = st.columns(2)
                    _t_pw1 = _tp1.text_input("Passwort *",          key="trainer_pw1", type="password")
                    _t_pw2 = _tp2.text_input("Passwort bestätigen *", key="trainer_pw2", type="password")

                    # ── 3 · Rechnungsdaten ────────────────────────────────────────
                    st.markdown(
                        '<div style="margin:14px 0 10px;padding:0 0 6px;border-bottom:1px solid #21262d">'
                        '<span style="color:#e6edf3;font-size:14px;font-weight:700">3 · Rechnungsdaten</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    with st.expander("📄 Rechnungsadresse (Pflichtangabe)", expanded=True):
                        _tb1, _tb2 = st.columns(2)
                        _t_ra_firma    = _tb1.text_input("Firma/Verein (optional)",  key="tr_ra_firma")
                        _t_ra_tel      = _tb2.text_input("Telefon (optional)",       key="tr_ra_tel")
                        _tb3, _tb4 = st.columns(2)
                        _t_ra_vorname  = _tb3.text_input("Vorname *",                key="tr_ra_vorname")
                        _t_ra_nachname = _tb4.text_input("Nachname *",               key="tr_ra_nachname")
                        _tb5, _tb6 = st.columns([3, 1])
                        _t_ra_strasse  = _tb5.text_input("Straße *",                 key="tr_ra_strasse")
                        _t_ra_hnr      = _tb6.text_input("Nr. *",                    key="tr_ra_hnr")
                        _tb7, _tb8 = st.columns([1, 2])
                        _t_ra_plz      = _tb7.text_input("PLZ *",                    key="tr_ra_plz")
                        _t_ra_ort      = _tb8.text_input("Ort *",                    key="tr_ra_ort")
                        _tb9, _tb10 = st.columns(2)
                        _t_ra_land     = _tb9.text_input("Land *",                   key="tr_ra_land",
                                                         value="Deutschland")
                        _t_ra_remail   = _tb10.text_input("Rechnungs-E-Mail *",      key="tr_ra_remail",
                                                          placeholder="rechnung@trainer.de")
                        _t_ra_ustid    = st.text_input("Umsatzsteuer-ID (optional)", key="tr_ra_ustid")

                    # ── 4 · Rechtliches ───────────────────────────────────────────
                    st.markdown(
                        '<div style="margin:14px 0 10px;padding:0 0 6px;border-bottom:1px solid #21262d">'
                        '<span style="color:#e6edf3;font-size:14px;font-weight:700">4 · Rechtliches</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        '<div style="background:#161b22;border:1px solid #30363d;'
                        'border-radius:8px;padding:12px 14px;margin:4px 0 12px">',
                        unsafe_allow_html=True,
                    )
                    _tds_c1, _tds_c2 = st.columns([6, 1])
                    _t_datenschutz = _tds_c1.checkbox(
                        "Ich habe die Datenschutzerklärung gelesen und akzeptiere sie.",
                        key="reg_t_datenschutz",
                    )
                    if _tds_c2.button("📖 Lesen", key="reg_t_open_ds",
                                      help="Datenschutzerklärung öffnen"):
                        st.session_state["_legal_show"] = "datenschutz"
                        st.rerun()
                    _tagb_c1, _tagb_c2 = st.columns([6, 1])
                    _t_agb = _tagb_c1.checkbox(
                        "Ich habe die AGB / Nutzungsbedingungen gelesen und akzeptiere sie.",
                        key="reg_t_agb",
                    )
                    if _tagb_c2.button("📖 Lesen", key="reg_t_open_agb",
                                       help="AGB / Nutzungsbedingungen öffnen"):
                        st.session_state["_legal_show"] = "agb"
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.caption("Heute keine Zahlung. Anschließend gemäß gewähltem Tarif.")
                    if st.button("🚀 30 TAGE KOSTENLOS STARTEN", type="primary",
                                 use_container_width=True, key="trainer_reg_btn"):
                        _terr = []
                        if not _t_datenschutz or not _t_agb:
                            _terr.append(
                                "Bitte akzeptiere die Datenschutzerklärung und die "
                                "AGB / Nutzungsbedingungen, um die Registrierung abzuschließen."
                            )
                        if not _t_vorname.strip() or not _t_nachname.strip():
                            _terr.append("Vor- und Nachname fehlen.")
                        if not _t_email.strip() or "@" not in _t_email:
                            _terr.append("Bitte gültige E-Mail-Adresse eingeben.")
                        if not _t_uname.strip():             _terr.append("Benutzername fehlt.")
                        if len(_t_pw1) < 6:                  _terr.append("Passwort mind. 6 Zeichen.")
                        elif _t_pw1 != _t_pw2:               _terr.append("Passwörter stimmen nicht überein.")
                        if not _t_ra_vorname.strip() or not _t_ra_nachname.strip():
                            _terr.append("Rechnungsadresse: Vor-/Nachname fehlen.")
                        if not _t_ra_strasse.strip() or not _t_ra_hnr.strip():
                            _terr.append("Rechnungsadresse: Straße und Hausnummer fehlen.")
                        if not _t_ra_plz.strip() or not _t_ra_ort.strip():
                            _terr.append("Rechnungsadresse: PLZ und Ort fehlen.")
                        if not _t_ra_land.strip():           _terr.append("Rechnungsadresse: Land fehlt.")
                        if not _t_ra_remail.strip() or "@" not in _t_ra_remail:
                            _terr.append("Rechnungsadresse: Rechnungs-E-Mail fehlt oder ungültig.")
                        if _t_paket not in _TRAINER_PAKETE:
                            _terr.append(f"Ungültiges Paket: {_t_paket!r}.")
                        if _t_intervall not in ("monat", "jahr"):
                            _terr.append("Ungültiges Abrechnungsintervall.")
                        if _terr:
                            for _e in _terr: st.error(_e)
                        else:
                            try:
                                from database import trainer_registrieren, rechnungsadresse_speichern as _ras
                                _tbid = trainer_registrieren(
                                    _t_vorname.strip(), _t_nachname.strip(),
                                    _t_email.strip(), _t_pw1,
                                    benutzername=_t_uname.strip(),
                                    lizenztyp=_t_paket,
                                    abo_intervall=_t_intervall,
                                )
                                _ras(_tbid,
                                     firma=_t_ra_firma.strip() or None,
                                     vorname=_t_ra_vorname.strip(),
                                     nachname=_t_ra_nachname.strip(),
                                     strasse=_t_ra_strasse.strip(),
                                     hausnummer=_t_ra_hnr.strip(),
                                     plz=_t_ra_plz.strip(),
                                     ort=_t_ra_ort.strip(),
                                     land=_t_ra_land.strip(),
                                     rechnung_email=_t_ra_remail.strip(),
                                     telefon=_t_ra_tel.strip() or None,
                                     ust_id=_t_ra_ustid.strip() or None)
                                zustimmung_registrierung_speichern(
                                    _tbid, PRIVACY_POLICY_VERSION, TERMS_VERSION
                                )
                                from database import email_token_erzeugen as _ete
                                _tvtoken = _ete(_tbid)
                                _treg_email_ok = False
                                try:
                                    from email_service import send_verification_email as _sve
                                    _sve(_t_email.strip(), _t_vorname.strip(),
                                         _tvtoken, _app_base_url())
                                    _treg_email_ok = True
                                except Exception as _tsmtp_err:
                                    import logging as _log_treg
                                    _log_treg.getLogger("athletik.email").error(
                                        "Trainer-Reg: Bestätigungs-E-Mail konnte nicht gesendet werden "
                                        "(%s). SMTP-Passwort wird nicht geloggt.",
                                        type(_tsmtp_err).__name__,
                                    )
                                    st.session_state["_reg_pending_bid"]   = _tbid
                                    st.session_state["_reg_pending_email"] = _t_email.strip()
                                if _treg_email_ok:
                                    st.success(
                                        "✅ Registrierung erfolgreich! "
                                        "Bitte bestätige deine E-Mail-Adresse — "
                                        "wir haben dir eine Bestätigungs-E-Mail gesendet. "
                                        "Danach schaltet ein Administrator dein Konto frei."
                                    )
                                else:
                                    st.warning(
                                        "✅ Dein Konto wurde erstellt, aber die Bestätigungs-E-Mail "
                                        "konnte momentan nicht versendet werden. "
                                        "Bitte versuche, die Bestätigungs-E-Mail erneut anzufordern."
                                    )
                                    if st.button("📧 Bestätigungs-E-Mail erneut senden",
                                                 key="reg_resend_trainer_btn"):
                                        _rpbt = st.session_state.get("_reg_pending_bid")
                                        _rpet = st.session_state.get("_reg_pending_email","")
                                        if _rpbt:
                                            from database import (
                                                email_token_erzeugen as _ete3,
                                                email_token_resend_erlaubt as _etra3,
                                                benutzer_by_id as _bbi3,
                                            )
                                            if _etra3(_rpbt):
                                                _nt3 = _ete3(_rpbt)
                                                _bu3 = _bbi3(_rpbt) or {}
                                                try:
                                                    from email_service import send_verification_email as _sve3
                                                    _sve3(_rpet, _bu3.get("vorname","Benutzer"),
                                                          _nt3, _app_base_url())
                                                    st.success("✅ Bestätigungs-E-Mail gesendet.")
                                                except Exception as _e3:
                                                    st.warning(f"E-Mail konnte nicht gesendet werden: {type(_e3).__name__}")
                            except ValueError as _ve:
                                st.error(str(_ve))
                            except Exception as _ex:
                                st.error(f"Fehler bei der Registrierung: {_ex}")

    # ── Rechtliche Links (ohne Anmeldung erreichbar) ──────────────────────────
    st.markdown(
        '<div style="margin-top:28px;padding-top:14px;border-top:1px solid #21262d;'
        'text-align:center;font-size:10px;color:#8b949e">Rechtliches</div>',
        unsafe_allow_html=True,
    )
    _ll1, _ll2, _ll3 = st.columns(3)
    if _ll1.button("📋 Impressum", key="login_legal_impressum", use_container_width=True):
        st.session_state["_legal_show"] = "impressum"
        st.rerun()
    if _ll2.button("🔒 Datenschutz", key="login_legal_datenschutz", use_container_width=True):
        st.session_state["_legal_show"] = "datenschutz"
        st.rerun()
    if _ll3.button("📄 AGB", key="login_legal_agb", use_container_width=True):
        st.session_state["_legal_show"] = "agb"
        st.rerun()

    st.stop()

# ─── Per-Rerun Session-Token-Validierung (fängt nach Passwortänderung invalide ──
# Sessions ab, auch wenn user bereits in st.session_state ist)              ─────
_rerun_token = st.session_state.get("_session_token")
if _rerun_token:
    from database import session_token_aktiv as _sta
    if not _sta(_rerun_token):
        # Session wurde serverseitig invalidiert (z. B. nach Passwortänderung).
        # Cookie und Session-State löschen → Nutzer zur Anmeldung führen.
        if _cookie_ctrl:
            try:
                _cookie_ctrl.remove("ath_sid")
            except Exception:
                pass
        # __pw_changed__ bewahren damit die Login-Seite die korrekte Meldung zeigt
        _inv_preserve = {"__logout_ok__", "__pw_changed__"}
        _inv_keys = [k for k in st.session_state.keys() if k not in _inv_preserve]
        for _ik in _inv_keys:
            del st.session_state[_ik]
        st.session_state["__logout_ok__"] = True
        st.rerun()

# ─── Session-Timeout: inaktive Sitzungen automatisch abmelden ────────────────
from session_timeout import check_session_timeout, touch_session
check_session_timeout()

# ─── Throttled DB-Touch: letzte_aktivitaet alle 5 Minuten aktualisieren ──────
#
# WARUM: session_validieren() — die einzige Funktion, die letzte_aktivitaet
# aktualisiert — wird nur im Login-Gate aufgerufen (wenn "user" nicht im
# session_state ist). Bei aktiver WebSocket-Session läuft per-Rerun nur
# session_token_aktiv(), das letzte_aktivitaet NICHT aktualisiert.
#
# FOLGE OHNE FIX: Ein Nutzer, der >60 Minuten ohne Browser-Reload arbeitet,
# hat eine DB-Session mit idle-abgelaufener letzte_aktivitaet. Beim nächsten
# Reconnect (Display-Lock, App-Wechsel) → session_validieren() findet
# idle_sek überschritten → None → Login-Formular, obwohl Nutzer aktiv war.
#
# FIX: Throttled DB-Touch alle 5 Minuten bei authentifizierten Reruns.
# Nur wenn _session_token bekannt ist und letzte DB-Berührung > 5 Minuten zurückliegt.
_DB_TOUCH_INTERVAL_SEC = 300  # 5 Minuten
if _rerun_token:
    import time as _time_mod
    _last_db_touch = st.session_state.get("_last_db_touch_ts", 0.0)
    _now_ts = _time_mod.time()
    if (_now_ts - _last_db_touch) > _DB_TOUCH_INTERVAL_SEC:
        from database import session_aktivitaet_aktualisieren as _saa
        _saa(_rerun_token)
        st.session_state["_last_db_touch_ts"] = _now_ts

# ─── Lizenz-Gate: Abgelaufene oder gesperrte Lizenzen blockieren ─────────────
from license import enforce_license_gate
enforce_license_gate()

# ─── Mehrfachmandanten-Auswahl ────────────────────────────────────────────────
# Trainern, die mehreren Vereinen angehören, wird nach dem Login eine
# Auswahlseite gezeigt. Superadmins und Vereinsadmins überspringen diesen Schritt.
# Einmal gewählt, wird die Auswahl im session_state gespeichert.
# Ein "Mandant wechseln"-Link in der Sidebar setzt _mandant_gewaehlt zurück.
_ma_user = st.session_state.get("user", {})
if (
    _ma_user.get("rolle") == "Trainer"
    and not st.session_state.get("_mandant_gewaehlt")
):
    try:
        from database import trainer_mandanten_fuer_benutzer as _tmfb_ma
        _ma_mandanten = _tmfb_ma(_ma_user["id"])
        # Nur echte Vereine (keine technischen Mandanten) zählen
        _ma_echte = [m for m in _ma_mandanten if not m.get("ist_technischer_mandant")]
        if len(_ma_echte) > 1:
            # Auswahlscreen: Trainer wählt seinen aktiven Mandanten
            st.markdown(
                '<div style="max-width:580px;margin:60px auto">'
                '<h2 style="color:#e6edf3;margin-bottom:4px">🏢 Mandant auswählen</h2>'
                '<p style="color:#8b949e;font-size:13px;margin-bottom:24px">'
                'Du bist mehreren Vereinen zugeordnet. '
                'Wähle aus, für welchen Verein du jetzt arbeiten möchtest.</p>',
                unsafe_allow_html=True,
            )
            for _mopt in _ma_echte:
                _ma_col1, _ma_col2 = st.columns([4, 1])
                _ma_col1.markdown(
                    f'<div style="padding:8px 0">'
                    f'<span style="font-size:15px;font-weight:700;color:#e6edf3">'
                    f'🏢 {_mopt["verein_name"]}</span><br>'
                    f'<span style="font-size:11px;color:#8b949e">'
                    f'Rolle: {_mopt["rolle_im_verein"]} · '
                    f'Mitglied seit: {_mopt["beigetreten_am"] or "—"}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if _ma_col2.button(
                    "✅ Auswählen",
                    key=f"_ma_sel_{_mopt['verein_id']}",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state["user"]["verein_id"] = _mopt["verein_id"]
                    st.session_state["user"]["verein_name"] = _mopt["verein_name"]
                    st.session_state["_mandant_gewaehlt"] = True
                    st.session_state["_aktiver_mandant_id"] = _mopt["verein_id"]
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()
        elif len(_ma_echte) == 1:
            # Nur ein echter Mandant → direkt setzen, kein Auswahlscreen
            st.session_state["user"]["verein_id"] = _ma_echte[0]["verein_id"]
            st.session_state["user"]["verein_name"] = _ma_echte[0]["verein_name"]
            st.session_state["_aktiver_mandant_id"] = _ma_echte[0]["verein_id"]
        st.session_state["_mandant_gewaehlt"] = True
    except Exception:
        # Fehler in der Mandantenabfrage darf Login/App nicht blockieren
        st.session_state["_mandant_gewaehlt"] = True

# ─── Startup-Gate: Zweckbestimmung muss bestätigt werden ─────────────────────
if not _zweck_bestaetigt():
    st.markdown(
        f'<div style="max-width:700px;margin:40px auto;padding:36px 40px;'
        f'background:#161b22;border:2px solid #d29922;border-radius:12px">'
        f'<div style="font-size:28px;text-align:center;margin-bottom:8px">⚠️</div>'
        f'<h2 style="color:#e6edf3;text-align:center;margin-bottom:4px">'
        f'Zweckbestimmung und Anwendungshinweise</h2>'
        f'<p style="color:#8b949e;text-align:center;font-size:12px;margin-bottom:24px">'
        f'Version {ZWECKBESTIMMUNG_VERSION} — Bitte vor der ersten Nutzung bestätigen</p>',
        unsafe_allow_html=True,
    )
    for absatz in ZWECKBESTIMMUNG_TEXT_DISPLAY.split("\n\n"):
        st.markdown(absatz)
    st.markdown(
        '<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;'
        'padding:14px 16px;margin-top:20px;color:#f0a030;font-size:13px">'
        '⚠️ Diese Anwendung ist eine sportliche Trainings- und Dokumentationshilfe. '
        'Sie ersetzt keine ärztliche Untersuchung und erteilt keine Sportfreigabe.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")
    benutzer_name = st.text_input(
        "Ihr Name (Trainer / Nutzer)",
        placeholder="z. B. Thomas Müller",
        key="zweck_benutzer",
    )
    bestaetigt = st.checkbox(
        "Ich habe die Zweckbestimmung und Anwendungshinweise gelesen und verstanden.",
        key="zweck_checkbox",
    )
    if st.button("✅ Bestätigen und App starten", type="primary",
                 disabled=not bestaetigt, use_container_width=True):
        name = benutzer_name.strip() or "Trainer"
        einwilligung_speichern(ZWECKBESTIMMUNG_VERSION, name)
        st.session_state["zweck_bestaetigt"] = True
        st.rerun()
    st.stop()

# ─── Splash Screen (einmal pro Sitzung) ──────────────────────────────────────
if "splash_done" not in st.session_state:
    st.session_state["splash_done"] = True
    import time as _time
    _APH_LOGO_PATH = os.path.join(os.path.dirname(__file__), "assets", "aph_logo.png")
    _sc1, _sc2, _sc3 = st.columns([1, 2, 1])
    with _sc2:
        # Logo — aph_logo.png (neues APH-Branding)
        if os.path.exists(_APH_LOGO_PATH):
            _ic1, _ic2, _ic3 = st.columns([1, 2, 1])
            _ic2.image(_APH_LOGO_PATH, width=110)
        st.markdown(
            f'<div style="text-align:center;padding:12px 0 20px">'
            f'<div style="font-size:72px;line-height:1">'
            f'{"" if os.path.exists(_APH_LOGO_PATH) else "⚽"}</div>'
            f'<h1 style="color:#e6edf3;font-size:22px;font-weight:800;'
            f'letter-spacing:3px;text-transform:uppercase;margin:16px 0 6px;line-height:1.3">'
            f'Athletic Performance Hub</h1>'
            f'<div style="color:#58a6ff;font-size:11px;font-weight:700;'
            f'letter-spacing:3px;margin-bottom:14px">TEST · ANALYSE · TRAINING</div>'
            f'<div style="color:#8b949e;font-size:11px;margin-bottom:4px">'
            f'Version {APP_VERSION}</div>'
            f'<div style="color:#30363d;font-size:11px;margin-top:32px">'
            f'APH wird geladen …</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    _time.sleep(1.2)
    st.rerun()

# ─── Stripe Checkout: Query-Params + Neu-Registrierungs-Prompt ───────────────
#
# 1. Stripe leitet nach Checkout-Abschluss zurück mit ?checkout=success/cancel.
#    Wir konvertieren das in einen session_state-Banner und leeren den Param.
# 2. Neu-registrierte Nutzer ohne stripe_customer_id sehen einen Checkout-Prompt.
#    Price ID und Tarif werden ausschließlich server-seitig aus der DB bestimmt.
#    Kein Price-ID-Input aus dem Frontend.

if _qp_checkout in ("success", "cancel"):
    st.session_state[f"_checkout_{_qp_checkout}_banner"] = True
    st.query_params.clear()
    st.rerun()

if st.session_state.pop("_checkout_success_banner", False):
    st.success(
        "✅ **Zahlungsmethode erfolgreich hinterlegt!** "
        "30 Tage kostenlos testen. "
        "Die erste Abbuchung erfolgt erst nach Ende der Testphase."
    )

if st.session_state.pop("_checkout_cancel_banner", False):
    st.info(
        "ℹ️ Checkout abgebrochen — dein Konto bleibt bestehen. "
        "Du kannst die Zahlungsmethode jederzeit unter "
        "**Einstellungen → Lizenz & Abonnement** hinterlegen."
    )

# ── Checkout-Prompt für Neu-Registrierungen ────────────────────────────────
_chk_u    = st.session_state.get("user", {})
_chk_role = _chk_u.get("rolle", "")
_chk_vid  = _chk_u.get("verein_id")

if (
    _chk_role not in ("Superadmin",)
    and _chk_vid
    and not st.session_state.get("_checkout_banner_dismissed")
):
    try:
        from stripe_service import stripe_verfuegbar as _sv_chk
        if _sv_chk():
            from database import lizenz_info_laden as _lil_chk, stripe_ids_setzen as _sis_chk
            _chk_info = _lil_chk(_chk_vid)
            if _chk_info and not _chk_info.get("stripe_customer_id"):
                _chk_ltyp = (_chk_info.get("lizenztyp") or "VEREIN_BASIC").strip()
                _chk_intv = (_chk_info.get("abo_intervall") or "monat").strip()
                from stripe_service import get_price_id as _gpi_chk
                _chk_pid = _gpi_chk(_chk_ltyp, _chk_intv)
                if _chk_pid:
                    _intv_label = "Monatlich" if _chk_intv == "monat" else "Jährlich"
                    st.markdown(
                        f'<div style="background:#0f2417;border:1px solid #2ea043;'
                        f'border-radius:8px;padding:14px 18px;margin-bottom:16px">'
                        f'<div style="color:#3fb950;font-weight:700;font-size:14px;'
                        f'margin-bottom:4px">🎁 30 Tage kostenlos testen</div>'
                        f'<div style="color:#8b949e;font-size:12px">'
                        f'Paket: <b style="color:#e6edf3">{_chk_ltyp}</b> · '
                        f'<b style="color:#e6edf3">{_intv_label}</b> — '
                        f'heute keine Zahlung fällig. '
                        f'Hinterlege jetzt deine Zahlungsmethode für die automatische '
                        f'Abbuchung nach der Testphase.</div></div>',
                        unsafe_allow_html=True,
                    )
                    _chk_c1, _chk_c2 = st.columns([3, 1])
                    with _chk_c1:
                        _do_checkout = st.button(
                            "💳 Jetzt Zahlungsmethode hinterlegen (kostenlos)",
                            type="primary",
                            use_container_width=True,
                            key="checkout_prompt_start",
                        )
                    with _chk_c2:
                        _skip_checkout = st.button(
                            "Später",
                            use_container_width=True,
                            key="checkout_prompt_skip",
                        )
                    if _skip_checkout:
                        st.session_state["_checkout_banner_dismissed"] = True
                        st.rerun()
                    if _do_checkout:
                        try:
                            from stripe_service import (
                                customer_erstellen as _ce_chk,
                                checkout_session_erstellen as _cse_chk,
                            )
                            # Stripe-Kunden anlegen — ausschließlich server-seitige Daten
                            _new_customer_id = _ce_chk(
                                email=_chk_u.get("email", ""),
                                name=(
                                    f"{_chk_u.get('vorname', '').strip()} "
                                    f"{_chk_u.get('nachname', '').strip()}"
                                ).strip() or _chk_u.get("email", ""),
                                verein_id=_chk_vid,
                            )
                            _sis_chk(_chk_vid, customer_id=_new_customer_id)
                            # Checkout-Session erstellen mit 30-Tage-Trial
                            _chk_url = _cse_chk(
                                customer_id=_new_customer_id,
                                price_id=_chk_pid,
                                verein_id=_chk_vid,
                                success_url=f"{_app_base_url()}?checkout=success",
                                cancel_url=f"{_app_base_url()}?checkout=cancel",
                                testphase_tage=30,
                                lizenztyp=_chk_ltyp,
                                abo_intervall=_chk_intv,
                            )
                            st.markdown(
                                f'<meta http-equiv="refresh" content="0; url={_chk_url}">'
                                f'<p style="color:#8b949e;font-size:12px">'
                                f'Weiterleitung zu Stripe… '
                                f'<a href="{_chk_url}" style="color:#58a6ff">'
                                f'Hier klicken</a></p>',
                                unsafe_allow_html=True,
                            )
                            st.stop()
                        except Exception as _chk_ex:
                            st.error(f"Checkout konnte nicht gestartet werden: {_chk_ex}")
    except Exception:
        pass  # Stripe nicht verfügbar oder konfigurationsfehler — kein Prompt zeigen

# ─── Payment-Failure-Banner: Zahlung fehlgeschlagen ──────────────────────────
# Zeige einen gelben Warnhinweis wenn der Zahlungsstatus 'fehlgeschlagen' ist.
# Kein Feature-Lock — Warnung reicht (Grace Period).
_pf_user = st.session_state.get("user", {})
_pf_role = _pf_user.get("rolle", "")
_pf_vid  = _pf_user.get("verein_id")

if _pf_role not in ("Superadmin",) and _pf_vid:
    try:
        from database import lizenz_info_laden as _lil_pf
        _pf_info = _lil_pf(_pf_vid) or {}
        if (_pf_info.get("zahlungsstatus") or "") == "fehlgeschlagen":
            _pf_col1, _pf_col2 = st.columns([5, 1])
            with _pf_col1:
                st.warning(
                    "⚠️ **Zahlung fehlgeschlagen.** Bitte aktualisiere deine Zahlungsmethode, "
                    "um eine Unterbrechung deines Zugangs zu vermeiden."
                )
            with _pf_col2:
                if st.button("📋 Mein Vertrag", key="_pf_goto_vertrag",
                             use_container_width=True):
                    st.session_state["_nav_goto"] = "📋  Mein Vertrag"
                    st.rerun()
    except Exception:
        pass

# ─── Helpers ──────────────────────────────────────────────────────────────────

# Delegate badge helpers to ui_components (keep aliases for existing page code)
def _risk_badge(level: str) -> str:
    return risk_badge_html(level)

def _score_badge(score: int) -> str:
    return score_badge_html(score)

def _progress_html(value: int, max_val: int, color: str = "#1f6feb") -> str:
    pct = min(value / max_val * 100, 100)
    return f'<div class="prog-wrap"><div class="prog-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'

def _save_ok(msg: str) -> None:
    """Erfolgsmeldung (grün) nach st.rerun() als Toast anzeigen."""
    st.session_state["__save_ok__"] = msg
    _audit("OK", msg)

def _save_err(msg: str) -> None:
    """Fehlermeldung (rot) nach st.rerun() als Toast anzeigen."""
    st.session_state["__save_err__"] = msg
    _audit("ERROR", msg)

def _save_warn(msg: str) -> None:
    """Warnmeldung (gelb) nach st.rerun() als Toast anzeigen."""
    st.session_state["__save_warn__"] = msg
    _audit("WARN", msg)

def _save_info(msg: str) -> None:
    """Info-Meldung (blau) nach st.rerun() als Toast anzeigen."""
    st.session_state["__save_info__"] = msg

def _audit(level: str, msg: str, detail: str = "") -> None:
    """Interne Protokollierung aller wichtigen Aktionen (Zeitpunkt, Benutzer, Aktion, Ergebnis)."""
    try:
        user = st.session_state.get("user") or {}
        uid  = user.get("id", "–")
        mail = user.get("email", user.get("name", "–"))
        import logging as _logging
        _log_fb = _logging.getLogger("athletik.feedback")
        _log_fb.info("[%s] user=%s(%s) | %s%s", level, uid, mail, msg,
                     f" | {detail}" if detail else "")
    except Exception:
        pass

def _check_save_ok() -> None:
    """
    Zeigt alle gespeicherten Feedback-Meldungen als auto-verschwindende Toasts.
    Einheitlich: ✅ Erfolg · ❌ Fehler · ⚠️ Warnung · ℹ️ Info
    """
    if msg := st.session_state.pop("__save_ok__",   None):
        st.toast(f"✅ {msg}", icon=None)
    if msg := st.session_state.pop("__save_err__",  None):
        st.toast(f"❌ {msg}", icon=None)
    if msg := st.session_state.pop("__save_warn__", None):
        st.toast(f"⚠️ {msg}", icon=None)
    if msg := st.session_state.pop("__save_info__", None):
        st.toast(f"ℹ️ {msg}", icon=None)

_check_feedback = _check_save_ok  # einheitlicher Alias für neuen Code

def _confirm_loeschen(key: str, was: str = "diesen Datensatz",
                      btn_label: str | None = None) -> bool:
    """
    Zweistufige Bestätigungsabfrage vor kritischen Lösch-Aktionen (Spec §5 Sicherheitsabfrage).
    Gibt True zurück, wenn der Benutzer die Löschung explizit bestätigt hat.

    Verwendung:
        if _confirm_loeschen("verletzung_del", was="diesen Verletzungseintrag"):
            verletzung_loeschen(vid)
            _save_ok("Eintrag gelöscht.")
            st.rerun()
    """
    _pend = f"__del_pend_{key}__"
    if not st.session_state.get(_pend):
        _lbl = btn_label or f"🗑️ {was.capitalize()} löschen"
        if st.button(_lbl, key=key, type="secondary"):
            st.session_state[_pend] = True
            st.rerun()
        return False
    # Bestätigungs-UI
    st.warning(
        f"⚠️ **Möchtest du {was} wirklich löschen?**  \n"
        "Diese Aktion kann nicht rückgängig gemacht werden."
    )
    _c1, _c2 = st.columns(2)
    if _c1.button("✅ Ja, endgültig löschen", key=f"{key}_yes", type="primary"):
        st.session_state.pop(_pend, None)
        return True
    if _c2.button("❌ Abbrechen", key=f"{key}_no"):
        st.session_state.pop(_pend, None)
        st.rerun()
    return False

def _reset_keys(*keys: str) -> None:
    """Löscht Formularfelder aus dem Session-State → werden beim nächsten Render auf Default zurückgesetzt."""
    for k in keys:
        st.session_state.pop(k, None)

def _akt_user() -> dict:
    """Gibt den eingeloggten Benutzer-Dict zurück (nach Login-Gate immer vorhanden)."""
    return st.session_state.get("user") or {"id": None, "rolle": "Superadmin", "verein_id": None}


def _validate_geburtsdatum(datum_str: str):
    """Prüft Datum TT.MM.JJJJ — gibt (True, None) oder (False, Fehlermeldung) zurück."""
    from datetime import datetime as _dt, date as _d
    s = datum_str.strip()
    if not s:
        return False, "Bitte ein Geburtsdatum eingeben."
    parts = s.split(".")
    if len(parts) != 3:
        return False, f"Format TT.MM.JJJJ erwartet (z. B. 15.03.2008), eingegeben: »{s}«"
    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return False, f"Datum enthält ungültige Zeichen: »{s}«"
    if not (1 <= month <= 12):
        return False, f"Monat {month} ist ungültig — erlaubt: 1–12."
    if not (1 <= day <= 31):
        return False, f"Tag {day} ist ungültig — erlaubt: 1–31."
    if not (1900 <= year <= 2100):
        return False, f"Jahr {year} ist ungültig — erlaubt: 1900–2100."
    try:
        _dt(year, month, day)
    except ValueError:
        return False, f"Das Datum {day}.{month}.{year} existiert nicht (z. B. 31.02 gibt es nicht)."
    return True, None

def _color_for_score(score: int, max_val: int = 100) -> str:
    pct = score / max_val
    if pct >= 0.75: return C["green"]
    if pct >= 0.5:  return C["yellow"]
    return C["red"]


def _datum_filter(df: "pd.DataFrame", key: str) -> "pd.DataFrame":
    """Rendert einen optionalen Datum-Bereichsfilter über einer Verlaufstabelle.
    Erwartet eine Spalte 'Datum' im DataFrame. Gibt den gefilterten DataFrame zurück."""
    if df is None or df.empty or "Datum" not in df.columns:
        return df
    daten = df["Datum"].tolist()
    if len(daten) < 2:
        return df
    _fc1, _fc2 = st.columns(2)
    _von = _fc1.selectbox("📅 Zeitraum von", ["Alle"] + daten,
                           key=f"dfilter_von_{key}", label_visibility="visible")
    _bis = _fc2.selectbox("bis", ["Alle"] + list(reversed(daten)),
                           key=f"dfilter_bis_{key}", label_visibility="visible")
    if _von != "Alle" or _bis != "Alle":
        try:
            _von_idx = daten.index(_von) if _von != "Alle" else 0
            _bis_idx = daten.index(_bis) if _bis != "Alle" else len(daten) - 1
            if _von_idx > _bis_idx:
                _von_idx, _bis_idx = _bis_idx, _von_idx
            df = df.iloc[_von_idx:_bis_idx + 1].reset_index(drop=True)
            st.caption(f"🔍 {len(df)} von {len(daten)} Einträgen angezeigt.")
        except Exception:
            pass
    return df


def _pb_trend_cards(df: "pd.DataFrame", metrics: list, key: str = "") -> None:
    """Zeigt Persönliche-Bestleistung-Kacheln + Trend-Pfeil für Verlauf-Tabs.
    metrics: list of (col_name, label, unit, lower_is_better)
    lower_is_better: True für Zeitmessungen (Sprint, Agilität), False für Scores/Distanzen.
    """
    valid = []
    for col_name, label, unit, lib in metrics:
        if col_name not in df.columns:
            continue
        series = pd.to_numeric(df[col_name], errors="coerce").dropna()
        series = series[series > 0]
        if series.empty:
            continue
        valid.append((col_name, label, unit, lib, series))
    if not valid:
        return

    st.markdown(
        '<p style="font-size:10px;color:#8b949e;letter-spacing:.8px;margin:6px 0 4px 0">'
        '🏆 PERSÖNLICHE BESTLEISTUNGEN</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(valid))
    for col_out, (col_name, label, unit, lower_is_better, series) in zip(cols, valid):
        pb_val = series.min() if lower_is_better else series.max()
        pb_idx = series.idxmin() if lower_is_better else series.idxmax()
        pb_date = str(df.loc[pb_idx, "Datum"]) if "Datum" in df.columns else ""

        trend_html = ""
        if len(series) >= 2:
            last_v, prev_v = float(series.iloc[-1]), float(series.iloc[-2])
            diff = last_v - prev_v
            if lower_is_better:
                t_str = (f"↓ {abs(diff):.2f} {unit} verbessert" if diff < -0.001
                         else f"↑ {diff:.2f} {unit} schlechter" if diff > 0.001 else "→ unverändert")
                t_clr = "#3fb950" if diff < -0.001 else "#f85149" if diff > 0.001 else "#8b949e"
            else:
                t_str = (f"↑ {diff:.2f} {unit} verbessert" if diff > 0.001
                         else f"↓ {abs(diff):.2f} {unit} schlechter" if diff < -0.001 else "→ unverändert")
                t_clr = "#3fb950" if diff > 0.001 else "#f85149" if diff < -0.001 else "#8b949e"
            trend_html = (
                f'<div style="font-size:10px;color:{t_clr};margin-top:3px">{t_str}</div>'
            )

        if unit == "s":
            pb_str = f"{pb_val:.2f}"
        elif unit in ("%", "cm", "kg", "m", "ml/kg/min"):
            pb_str = f"{pb_val:.1f}"
        else:
            pb_str = f"{int(round(pb_val))}"

        col_out.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;'
            f'padding:10px 14px;margin-bottom:8px">'
            f'<div style="font-size:9px;color:#8b949e;letter-spacing:.8px">{label}</div>'
            f'<div style="font-size:20px;font-weight:800;color:#e6edf3;line-height:1.2">'
            f'{pb_str}&thinsp;<span style="font-size:11px;color:#8b949e">{unit}</span></div>'
            f'<div style="font-size:9px;color:#6e7681">{pb_date}</div>'
            + trend_html + '</div>',
            unsafe_allow_html=True,
        )


# ─── Task #257: History-Edit/Delete Helpers ───────────────────────────────────

def _history_mandant_ok(spieler_id: int) -> bool:
    """Prüft Mandantenzugehörigkeit des Spielers für den aktiven Benutzer."""
    u = _akt_user()
    return spieler_mandant_pruefen(spieler_id, u.get("id"), u.get("rolle", ""), u.get("verein_id"))


def _datum_zu_date(datum_str: str | None) -> "date":
    """Konvertiert gespeichertes Datum (DD.MM.YYYY oder YYYY-MM-DD) in date-Objekt."""
    if not datum_str:
        return date.today()
    d = parse_datum_safe(datum_str)
    if d:
        return d
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%Y (%H:%M)"):
        try:
            return datetime.strptime(datum_str.split(" (")[0], fmt).date()
        except Exception:
            pass
    return date.today()


def _edit_select_box(records: list[dict], module_key: str) -> dict | None:
    """Zeigt eine Selectbox mit Datum + ID für einen History-Datensatz. Gibt den gewählten Record zurück."""
    if not records:
        st.info("Keine Einträge zum Bearbeiten vorhanden.")
        return None
    options = [f"{r.get('datum','?')} [ID {r.get('id','?')}]" for r in records]
    idx = st.selectbox("Eintrag auswählen", range(len(options)),
                       format_func=lambda i: options[i],
                       key=f"hist_edit_sel_{module_key}")
    return records[idx]


# ─── Anthropometrie ───────────────────────────────────────────────────────────

def _render_anthro_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für Anthropometrie-Verlauf."""
    from database import anthropometrie_history_edit, anthropometrie_update, anthropometrie_loeschen
    records = anthropometrie_history_edit(spieler_id)
    if not records:
        st.info("Noch keine Messungen vorhanden.")
        return

    rec = _edit_select_box(records, f"anthro_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]

    with st.form(f"anthro_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**Messung bearbeiten — ID {rid}**")
        datum_val = _datum_zu_date(rec.get("datum"))
        d_col, g_col, gew_col = st.columns(3)
        new_datum  = d_col.date_input("Datum", value=datum_val, key=f"ae_datum_{rid}")
        new_groesse = g_col.number_input("Größe (cm)", 0.0, 250.0,
                                          float(rec.get("groesse") or 0), 0.1, key=f"ae_gr_{rid}")
        new_gewicht = gew_col.number_input("Gewicht (kg)", 0.0, 200.0,
                                            float(rec.get("gewicht") or 0), 0.1, key=f"ae_gw_{rid}")
        c1, c2, c3 = st.columns(3)
        new_sh  = c1.number_input("Sitzhöhe (cm)",    0.0, 150.0, float(rec.get("sitzhoehe") or 0),    0.1, key=f"ae_sh_{rid}")
        new_bl  = c2.number_input("Beinlänge (cm)",   0.0, 130.0, float(rec.get("beinlaenge") or 0),   0.1, key=f"ae_bl_{rid}")
        new_arm = c3.number_input("Armspannweite (cm)", 0.0, 250.0, float(rec.get("armspannweite") or 0), 0.1, key=f"ae_arm_{rid}")
        c4, c5 = st.columns(2)
        new_kf  = c4.number_input("Körperfett (%)",  0.0, 60.0, float(rec.get("koerperfett") or 0),   0.1, key=f"ae_kf_{rid}")
        new_mm  = c5.number_input("Muskelmasse (kg)", 0.0, 100.0, float(rec.get("muskelmasse") or 0),  0.1, key=f"ae_mm_{rid}")
        c6, c7 = st.columns(2)
        new_bl_r = c6.number_input("Beinlänge R (cm)", 0.0, 130.0, float(rec.get("beinlaenge_r") or 0), 0.1, key=f"ae_blr_{rid}")
        new_bl_l = c7.number_input("Beinlänge L (cm)", 0.0, 130.0, float(rec.get("beinlaenge_l") or 0), 0.1, key=f"ae_bll_{rid}")

        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert — Spieler gehört nicht zu Ihrem Mandanten.")
                return
            from anthropometrie import bmi_berechnen, bmi_kategorie, phv_offset_berechnen, reifestatus_text
            sp_r = spieler_by_id(spieler_id)
            alter_r = alter_am_datum(
                sp_r.get("geburtsdatum", "") if sp_r else "",
                new_datum.strftime("%d.%m.%Y"),
            ) or 0
            geschl_r = sp_r.get("geschlecht", "Männlich") if sp_r else "Männlich"
            new_bmi = bmi_berechnen(new_gewicht, new_groesse) if new_groesse > 0 and new_gewicht > 0 else None
            new_bmi_kat = bmi_kategorie(new_bmi) if new_bmi else None
            new_phv = phv_offset_berechnen(alter_r, new_groesse, new_gewicht, new_sh, new_bl, geschl_r)
            new_reife = reifestatus_text(new_phv)
            ok = anthropometrie_update(
                rid, spieler_id, new_datum.strftime("%d.%m.%Y"),
                new_groesse or None, new_gewicht or None,
                new_sh or None, new_bl or None, new_arm or None,
                new_kf or None, new_mm or None,
                new_bmi, new_bmi_kat, new_phv, new_reife,
                new_bl_r or None, new_bl_l or None,
                rec.get("koerperfett_methode"),
            )
            if ok:
                _save_ok("Anthropometrie-Messung aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen.")

    st.markdown("---")
    if _confirm_loeschen(f"anthro_hist_del_{spieler_id}_{rid}",
                          was=f"Messung vom {rec.get('datum','?')} (ID {rid})",
                          btn_label="🗑️ Eintrag löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert.")
            return
        if anthropometrie_loeschen(rid, spieler_id):
            _save_ok("Messung gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


# ─── FMS ──────────────────────────────────────────────────────────────────────

def _render_fms_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für FMS-Verlauf."""
    from database import fms_history_edit, fms_update, fms_loeschen
    records = fms_history_edit(spieler_id)
    if not records:
        st.info("Noch keine FMS-Tests vorhanden.")
        return

    rec = _edit_select_box(records, f"fms_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]

    _FMS_FELDER = [
        ("Deep Squat",   "deep_squat",    f"fe_ds_{rid}"),
        ("Hurdle L",     "hurdle_links",  f"fe_hl_{rid}"),
        ("Hurdle R",     "hurdle_rechts", f"fe_hr_{rid}"),
        ("Inline L",     "inline_links",  f"fe_il_{rid}"),
        ("Inline R",     "inline_rechts", f"fe_ir_{rid}"),
        ("Shoulder L",   "shoulder_links",f"fe_sl_{rid}"),
        ("Shoulder R",   "shoulder_rechts",f"fe_sr_{rid}"),
        ("ASLR L",       "aslr_links",    f"fe_al_{rid}"),
        ("ASLR R",       "aslr_rechts",   f"fe_ar_{rid}"),
        ("Trunk",        "trunk",         f"fe_tr_{rid}"),
        ("Rotary L",     "rotary_links",  f"fe_rl_{rid}"),
        ("Rotary R",     "rotary_rechts", f"fe_rr_{rid}"),
    ]

    with st.form(f"fms_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**FMS bearbeiten — ID {rid}**")
        datum_val = _datum_zu_date(rec.get("datum"))
        new_datum = st.date_input("Datum", value=datum_val, key=f"fe_datum_{rid}")
        cols = st.columns(4)
        vals = {}
        for i, (lbl, fld, key) in enumerate(_FMS_FELDER):
            vals[fld] = cols[i % 4].number_input(lbl, 0, 3, int(rec.get(fld) or 0), key=key)
        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert."); return
            sp_r = spieler_by_id(spieler_id)
            alter_r = alter_am_datum(
                sp_r.get("geburtsdatum", "") if sp_r else "",
                new_datum.strftime("%d.%m.%Y"),
            )
            ok = fms_update(
                rid, spieler_id, new_datum.strftime("%d.%m.%Y"),
                vals["deep_squat"], vals["hurdle_links"], vals["hurdle_rechts"],
                vals["inline_links"], vals["inline_rechts"],
                vals["shoulder_links"], vals["shoulder_rechts"],
                vals["aslr_links"], vals["aslr_rechts"],
                vals["trunk"], vals["rotary_links"], vals["rotary_rechts"],
                alter=alter_r,
            )
            if ok:
                _save_ok("FMS-Test aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen.")

    st.markdown("---")
    if _confirm_loeschen(f"fms_hist_del_{spieler_id}_{rid}",
                          was=f"FMS-Test vom {rec.get('datum','?')} (ID {rid})",
                          btn_label="🗑️ FMS-Test löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert."); return
        if fms_loeschen(rid, spieler_id):
            _save_ok("FMS-Test gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


# ─── Y-Balance ────────────────────────────────────────────────────────────────

def _render_ybalance_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für Y-Balance-Verlauf."""
    from database import (
        y_balance_history_edit, y_balance_update, y_balance_loeschen,
        anthropometrie_history_edit, anthropometrie_beinlaengen_zum_testdatum,
    )
    records = y_balance_history_edit(spieler_id)
    if not records:
        st.info("Noch keine Y-Balance-Tests vorhanden.")
        return

    rec = _edit_select_box(records, f"yb_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]
    historische_anthro = anthropometrie_history_edit(spieler_id)

    with st.form(f"yb_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**Y-Balance bearbeiten — ID {rid}**")
        datum_val = _datum_zu_date(rec.get("datum"))
        new_datum = st.date_input("Datum", value=datum_val, key=f"yb_datum_{rid}")
        st.caption("Messwerte (cm) — Composite-Scores werden neu berechnet.")
        c1, c2 = st.columns(2)
        ant_r = c1.number_input("Anterior Rechts (cm)", 0.0, 200.0, float(rec.get("anterior_rechts") or 0), 0.1, key=f"yb_ar_{rid}")
        ant_l = c2.number_input("Anterior Links (cm)",  0.0, 200.0, float(rec.get("anterior_links")  or 0), 0.1, key=f"yb_al_{rid}")
        pm_r  = c1.number_input("Posteromedial Rechts (cm)", 0.0, 200.0, float(rec.get("posteromedial_rechts") or 0), 0.1, key=f"yb_pmr_{rid}")
        pm_l  = c2.number_input("Posteromedial Links (cm)",  0.0, 200.0, float(rec.get("posteromedial_links")  or 0), 0.1, key=f"yb_pml_{rid}")
        pl_r  = c1.number_input("Posterolateral Rechts (cm)", 0.0, 200.0, float(rec.get("posterolateral_rechts") or 0), 0.1, key=f"yb_plr_{rid}")
        pl_l  = c2.number_input("Posterolateral Links (cm)",  0.0, 200.0, float(rec.get("posterolateral_links")  or 0), 0.1, key=f"yb_pll_{rid}")
        _beinlaengen_basis = anthropometrie_beinlaengen_zum_testdatum(
            historische_anthro, datum_val.strftime("%d.%m.%Y"),
        )
        if _beinlaengen_basis:
            st.caption(
                "Beinlängen für den Composite-Score: "
                f"R {_beinlaengen_basis['beinlaenge_r']:.1f} cm · "
                f"L {_beinlaengen_basis['beinlaenge_l']:.1f} cm "
                f"(Anthropometrie vom {_beinlaengen_basis['datum']})."
            )
        else:
            st.error(
                "Keine dokumentierte Beinlänge am oder vor diesem Testdatum. "
                "Der Y-Balance-Test kann nicht sicher neu berechnet werden."
            )
        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert."); return
            sp_r = spieler_by_id(spieler_id)
            _datum_text = new_datum.strftime("%d.%m.%Y")
            _beinlaengen_basis = anthropometrie_beinlaengen_zum_testdatum(
                historische_anthro, _datum_text,
            )
            if not _beinlaengen_basis:
                st.error(
                    "❌ Keine dokumentierte Beinlänge am oder vor dem gewählten Testdatum. "
                    "Der Eintrag wurde nicht verändert."
                )
                return
            alter_r = alter_am_datum(
                sp_r.get("geburtsdatum", "") if sp_r else "", _datum_text,
            )
            ok = y_balance_update(
                rid, spieler_id, _datum_text,
                ant_r, ant_l, pm_r, pm_l, pl_r, pl_l,
                _beinlaengen_basis["beinlaenge_r"],
                _beinlaengen_basis["beinlaenge_l"],
                alter=alter_r,
            )
            if ok:
                _save_ok("Y-Balance-Test aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen.")

    st.markdown("---")
    if _confirm_loeschen(f"yb_hist_del_{spieler_id}_{rid}",
                          was=f"Y-Balance-Test vom {rec.get('datum','?')} (ID {rid})",
                          btn_label="🗑️ Y-Balance löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert."); return
        if y_balance_loeschen(rid, spieler_id):
            _save_ok("Y-Balance-Test gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


# ─── Sprint ───────────────────────────────────────────────────────────────────

def _render_sprint_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für Sprint-Verlauf."""
    from database import sprint_history_edit, sprint_update, sprint_loeschen
    records = sprint_history_edit(spieler_id)
    if not records:
        st.info("Noch keine Sprint-Tests vorhanden.")
        return

    rec = _edit_select_box(records, f"spr_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]

    with st.form(f"sprint_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**Sprint bearbeiten — ID {rid}**")
        st.caption("Zeiten in Sekunden (0 = nicht gemessen). Bester Versuch + abgeleitete Werte werden neu berechnet.")
        datum_val = _datum_zu_date(rec.get("datum"))
        new_datum = st.date_input("Datum", value=datum_val, key=f"se_datum_{rid}")
        st.caption("Versuch 1 | Versuch 2 | Versuch 3 (Sekunden, 0 = nicht gemessen)")
        cols_5 = st.columns(4)
        cols_5[0].markdown("**5 m**")
        v1_5  = cols_5[1].number_input("V1", 0.0, 20.0, float(rec.get("v1_5m")  or 0), 0.01, format="%.2f", key=f"se_5v1_{rid}", label_visibility="collapsed")
        v2_5  = cols_5[2].number_input("V2", 0.0, 20.0, float(rec.get("v2_5m")  or 0), 0.01, format="%.2f", key=f"se_5v2_{rid}", label_visibility="collapsed")
        v3_5  = cols_5[3].number_input("V3", 0.0, 20.0, float(rec.get("v3_5m")  or 0), 0.01, format="%.2f", key=f"se_5v3_{rid}", label_visibility="collapsed")
        cols_10 = st.columns(4)
        cols_10[0].markdown("**10 m**")
        v1_10 = cols_10[1].number_input("V1",0.0,20.0,float(rec.get("v1_10m") or 0),0.01,format="%.2f",key=f"se_10v1_{rid}",label_visibility="collapsed")
        v2_10 = cols_10[2].number_input("V2",0.0,20.0,float(rec.get("v2_10m") or 0),0.01,format="%.2f",key=f"se_10v2_{rid}",label_visibility="collapsed")
        v3_10 = cols_10[3].number_input("V3",0.0,20.0,float(rec.get("v3_10m") or 0),0.01,format="%.2f",key=f"se_10v3_{rid}",label_visibility="collapsed")
        cols_20 = st.columns(4)
        cols_20[0].markdown("**20 m**")
        v1_20 = cols_20[1].number_input("V1",0.0,20.0,float(rec.get("v1_20m") or 0),0.01,format="%.2f",key=f"se_20v1_{rid}",label_visibility="collapsed")
        v2_20 = cols_20[2].number_input("V2",0.0,20.0,float(rec.get("v2_20m") or 0),0.01,format="%.2f",key=f"se_20v2_{rid}",label_visibility="collapsed")
        v3_20 = cols_20[3].number_input("V3",0.0,20.0,float(rec.get("v3_20m") or 0),0.01,format="%.2f",key=f"se_20v3_{rid}",label_visibility="collapsed")
        cols_30 = st.columns(4)
        cols_30[0].markdown("**30 m**")
        v1_30 = cols_30[1].number_input("V1",0.0,20.0,float(rec.get("v1_30m") or 0),0.01,format="%.2f",key=f"se_30v1_{rid}",label_visibility="collapsed")
        v2_30 = cols_30[2].number_input("V2",0.0,20.0,float(rec.get("v2_30m") or 0),0.01,format="%.2f",key=f"se_30v2_{rid}",label_visibility="collapsed")
        v3_30 = cols_30[3].number_input("V3",0.0,20.0,float(rec.get("v3_30m") or 0),0.01,format="%.2f",key=f"se_30v3_{rid}",label_visibility="collapsed")
        cols_40 = st.columns(4)
        cols_40[0].markdown("**40 m**")
        v1_40 = cols_40[1].number_input("V1",0.0,20.0,float(rec.get("v1_40m") or 0),0.01,format="%.2f",key=f"se_40v1_{rid}",label_visibility="collapsed")
        v2_40 = cols_40[2].number_input("V2",0.0,20.0,float(rec.get("v2_40m") or 0),0.01,format="%.2f",key=f"se_40v2_{rid}",label_visibility="collapsed")
        v3_40 = cols_40[3].number_input("V3",0.0,20.0,float(rec.get("v3_40m") or 0),0.01,format="%.2f",key=f"se_40v3_{rid}",label_visibility="collapsed")
        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert."); return
            sp_r = spieler_by_id(spieler_id)
            _geschl = sp_r.get("geschlecht","Männlich") if sp_r else "Männlich"
            _niveau = sp_r.get("leistungsniveau","Leistungssport") if sp_r else "Leistungssport"
            _alter  = alter_am_datum(
                sp_r.get("geburtsdatum", "") if sp_r else "",
                new_datum.strftime("%d.%m.%Y"),
            )
            ok = sprint_update(
                rid, spieler_id, new_datum.strftime("%d.%m.%Y"),
                v1_5 or None, v2_5 or None, v3_5 or None,
                v1_10 or None, v2_10 or None, v3_10 or None,
                v1_20 or None, v2_20 or None, v3_20 or None,
                v1_30 or None, v2_30 or None, v3_30 or None,
                geschlecht=_geschl, niveau=_niveau, alter=_alter,
                v1_40=v1_40 or None, v2_40=v2_40 or None, v3_40=v3_40 or None,
            )
            if ok:
                _save_ok("Sprint-Test aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen.")

    st.markdown("---")
    if _confirm_loeschen(f"spr_hist_del_{spieler_id}_{rid}",
                          was=f"Sprint-Test vom {rec.get('datum','?')} (ID {rid})",
                          btn_label="🗑️ Sprint-Test löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert."); return
        if sprint_loeschen(rid, spieler_id):
            _save_ok("Sprint-Test gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


# ─── Sprung ───────────────────────────────────────────────────────────────────

def _render_sprung_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für Sprung-Verlauf."""
    from database import sprung_history_edit, sprung_update, sprung_loeschen, testverlauf_datum_kollision
    records = sprung_history_edit(spieler_id)
    if not records:
        st.info("Noch keine Sprung-Tests vorhanden.")
        return

    rec = _edit_select_box(records, f"spg_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]

    with st.form(f"sprung_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**Sprung bearbeiten — ID {rid}**")
        st.caption("Bestleistungswerte (cm / s). Abgeleitete Werte werden neu berechnet.")
        datum_val = _datum_zu_date(rec.get("datum"))
        new_datum = st.date_input("Datum", value=datum_val, key=f"spge_datum_{rid}")
        c1, c2 = st.columns(2)
        cmj_b = c1.number_input("CMJ beidbeinig (cm)", 0.0, 120.0, float(rec.get("cmj_beid") or 0), 0.1, key=f"spge_cb_{rid}")
        cmj_r = c1.number_input("CMJ einbeinig rechts (cm)", 0.0, 100.0, float(rec.get("cmj_rechts") or 0), 0.1, key=f"spge_cr_{rid}")
        cmj_l = c1.number_input("CMJ einbeinig links (cm)", 0.0, 100.0, float(rec.get("cmj_links") or 0), 0.1, key=f"spge_cl_{rid}")
        squat = c1.number_input("Squat Jump (cm)", 0.0, 120.0, float(rec.get("squat_jump") or 0), 0.1, key=f"spge_sq_{rid}")
        dj_h  = c2.number_input("Drop Jump Höhe (cm)", 0.0, 100.0, float(rec.get("drop_jump_hoehe") or 0), 0.1, key=f"spge_dh_{rid}")
        dj_kz = c2.number_input("Drop Jump KZ (s)", 0.0, 2.0, float(rec.get("drop_jump_kz") or 0), 0.01, format="%.3f", key=f"spge_dk_{rid}")
        swj   = c2.number_input("Standweitsprung (cm)", 0.0, 400.0, float(rec.get("standweit") or 0), 1.0, key=f"spge_sw_{rid}")
        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert."); return
            _datum_text = new_datum.strftime("%d.%m.%Y")
            if testverlauf_datum_kollision("sprung", rid, spieler_id, _datum_text):
                st.error("❌ Für dieses Datum existiert bereits ein anderer Sprung-Test. Bitte Datum anpassen.")
                return
            sp_r = spieler_by_id(spieler_id)
            _geschl = sp_r.get("geschlecht","Männlich") if sp_r else "Männlich"
            _niveau = sp_r.get("leistungsniveau","Leistungssport") if sp_r else "Leistungssport"
            _alter  = alter_am_datum(
                sp_r.get("geburtsdatum", "") if sp_r else "", _datum_text,
            )
            ok = sprung_update(
                rid, spieler_id, _datum_text,
                cmj_b or None, cmj_r or None, cmj_l or None,
                squat or None, dj_h or None, dj_kz or None, swj or None,
                geschlecht=_geschl, niveau=_niveau, alter=_alter,
                v1_cmj_beid=rec.get("v1_cmj_beid"), v2_cmj_beid=rec.get("v2_cmj_beid"), v3_cmj_beid=rec.get("v3_cmj_beid"),
                v1_cmj_r=rec.get("v1_cmj_r"), v2_cmj_r=rec.get("v2_cmj_r"), v3_cmj_r=rec.get("v3_cmj_r"),
                v1_cmj_l=rec.get("v1_cmj_l"), v2_cmj_l=rec.get("v2_cmj_l"), v3_cmj_l=rec.get("v3_cmj_l"),
                v1_squat=rec.get("v1_squat"), v2_squat=rec.get("v2_squat"), v3_squat=rec.get("v3_squat"),
                v1_dj_h=rec.get("v1_dj_h"), v2_dj_h=rec.get("v2_dj_h"), v3_dj_h=rec.get("v3_dj_h"),
                v1_dj_kz=rec.get("v1_dj_kz"), v2_dj_kz=rec.get("v2_dj_kz"), v3_dj_kz=rec.get("v3_dj_kz"),
                v1_swj=rec.get("v1_swj"), v2_swj=rec.get("v2_swj"), v3_swj=rec.get("v3_swj"),
            )
            if ok:
                _save_ok("Sprung-Test aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen.")

    st.markdown("---")
    if _confirm_loeschen(f"spg_hist_del_{spieler_id}_{rid}",
                          was=f"Sprung-Test vom {rec.get('datum','?')} (ID {rid})",
                          btn_label="🗑️ Sprung-Test löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert."); return
        if sprung_loeschen(rid, spieler_id):
            _save_ok("Sprung-Test gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


# ─── Agilität ─────────────────────────────────────────────────────────────────

def _render_agilitaet_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für Agilität-Verlauf."""
    from database import agilitaet_history_edit, agilitaet_update, agilitaet_loeschen, testverlauf_datum_kollision
    records = agilitaet_history_edit(spieler_id)
    if not records:
        st.info("Noch keine Agilität-Tests vorhanden.")
        return

    rec = _edit_select_box(records, f"agil_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]

    with st.form(f"agil_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**Agilität bearbeiten — ID {rid}**")
        st.caption("Bestzeiten in Sekunden (0 = nicht gemessen). Abgeleitete Werte werden neu berechnet.")
        datum_val = _datum_zu_date(rec.get("datum"))
        new_datum = st.date_input("Datum", value=datum_val, key=f"ae2_datum_{rid}")
        c1, c2 = st.columns(2)
        t505_r  = c1.number_input("505-Test rechts (s)", 0.0, 20.0, float(rec.get("t505_r")  or 0), 0.01, format="%.2f", key=f"ae2_505r_{rid}")
        t505_l  = c1.number_input("505-Test links (s)",  0.0, 20.0, float(rec.get("t505_l")  or 0), 0.01, format="%.2f", key=f"ae2_505l_{rid}")
        t5_10_5 = c1.number_input("5-10-5 Shuttle (s)", 0.0, 20.0, float(rec.get("t5_10_5") or 0), 0.01, format="%.2f", key=f"ae2_5105_{rid}")
        t_test  = c2.number_input("T-Test (s)",          0.0, 30.0, float(rec.get("t_test")  or 0), 0.01, format="%.2f", key=f"ae2_tt_{rid}")
        illinois= c2.number_input("Illinois (s)",        0.0, 30.0, float(rec.get("illinois") or 0), 0.01, format="%.2f", key=f"ae2_ill_{rid}")
        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert."); return
            _datum_text = new_datum.strftime("%d.%m.%Y")
            if testverlauf_datum_kollision("agilitaet", rid, spieler_id, _datum_text):
                st.error("❌ Für dieses Datum existiert bereits ein anderer Agilität-Test. Bitte Datum anpassen.")
                return
            sp_r = spieler_by_id(spieler_id)
            _geschl = sp_r.get("geschlecht","Männlich") if sp_r else "Männlich"
            _niveau = sp_r.get("leistungsniveau","Leistungssport") if sp_r else "Leistungssport"
            _alter  = alter_am_datum(
                sp_r.get("geburtsdatum", "") if sp_r else "", _datum_text,
            )
            ok = agilitaet_update(
                rid, spieler_id, _datum_text,
                t505_r or None, t505_l or None, t5_10_5 or None, t_test or None, illinois or None,
                geschlecht=_geschl, niveau=_niveau, alter=_alter,
                v1_t505_r=rec.get("v1_t505_r"), v2_t505_r=rec.get("v2_t505_r"), v3_t505_r=rec.get("v3_t505_r"),
                v1_t505_l=rec.get("v1_t505_l"), v2_t505_l=rec.get("v2_t505_l"), v3_t505_l=rec.get("v3_t505_l"),
                v1_t5_10_5=rec.get("v1_t5_10_5"), v2_t5_10_5=rec.get("v2_t5_10_5"), v3_t5_10_5=rec.get("v3_t5_10_5"),
                v1_t_test=rec.get("v1_t_test"), v2_t_test=rec.get("v2_t_test"), v3_t_test=rec.get("v3_t_test"),
                v1_illinois=rec.get("v1_illinois"), v2_illinois=rec.get("v2_illinois"), v3_illinois=rec.get("v3_illinois"),
                modified_t_test=rec.get("modified_t_test") or None,
                pro_agility=rec.get("pro_agility") or None,
                arrowhead_r=rec.get("arrowhead_r") or None,
                arrowhead_l=rec.get("arrowhead_l") or None,
                zigzag=rec.get("zigzag") or None,
                balsom=rec.get("balsom") or None,
                 v1_modified_t_test=rec.get("v1_modified_t_test"), v2_modified_t_test=rec.get("v2_modified_t_test"), v3_modified_t_test=rec.get("v3_modified_t_test"),
                 v1_pro_agility=rec.get("v1_pro_agility"), v2_pro_agility=rec.get("v2_pro_agility"), v3_pro_agility=rec.get("v3_pro_agility"),
                 v1_arrowhead_r=rec.get("v1_arrowhead_r"), v2_arrowhead_r=rec.get("v2_arrowhead_r"), v3_arrowhead_r=rec.get("v3_arrowhead_r"),
                 v1_arrowhead_l=rec.get("v1_arrowhead_l"), v2_arrowhead_l=rec.get("v2_arrowhead_l"), v3_arrowhead_l=rec.get("v3_arrowhead_l"),
                 v1_zigzag=rec.get("v1_zigzag"), v2_zigzag=rec.get("v2_zigzag"), v3_zigzag=rec.get("v3_zigzag"),
                 v1_balsom=rec.get("v1_balsom"), v2_balsom=rec.get("v2_balsom"), v3_balsom=rec.get("v3_balsom"),
            )
            if ok:
                _save_ok("Agilität-Test aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen.")

    st.markdown("---")
    if _confirm_loeschen(f"agil_hist_del_{spieler_id}_{rid}",
                          was=f"Agilität-Test vom {rec.get('datum','?')} (ID {rid})",
                          btn_label="🗑️ Agilität-Test löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert."); return
        if agilitaet_loeschen(rid, spieler_id):
            _save_ok("Agilität-Test gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


# ─── Ausdauer ─────────────────────────────────────────────────────────────────

def _render_ausdauer_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für Ausdauer-Verlauf (Yo-Yo)."""
    from database import ausdauer_history_edit, ausdauer_update, ausdauer_loeschen
    records = ausdauer_history_edit(spieler_id)
    if not records:
        st.info("Noch keine Ausdauer-Tests vorhanden.")
        return

    rec = _edit_select_box(records, f"aus_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]

    with st.form(f"aus_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**Ausdauer bearbeiten — ID {rid}**")
        datum_val = _datum_zu_date(rec.get("datum"))
        new_datum = st.date_input("Datum", value=datum_val, key=f"ause_datum_{rid}")
        c1, c2, c3 = st.columns(3)
        _typ_idx = 0 if rec.get("test_typ","IR1") == "IR1" else 1
        new_typ  = c1.selectbox("Test-Typ", ["IR1","IR2"], index=_typ_idx, key=f"ause_typ_{rid}")
        new_dist = c2.number_input("Distanz (m)", 0, 10000, int(rec.get("distanz_m") or 0), 40, key=f"ause_dist_{rid}")
        new_hf   = c3.number_input("HF max (bpm)", 0, 230, int(rec.get("hf_max") or 0), 1, key=f"ause_hf_{rid}")
        c4, c5 = st.columns(2)
        _rpe_opts = list(range(6,21))
        _rpe_def = int(rec.get("rpe") or 15)
        _rpe_idx = _rpe_opts.index(_rpe_def) if _rpe_def in _rpe_opts else 9
        new_rpe  = c4.selectbox("RPE (Borg 6–20)", _rpe_opts, index=_rpe_idx, key=f"ause_rpe_{rid}")
        c5.caption(
            "Die Yo-Yo-Altersgruppe wird beim Speichern aus dem gewählten "
            "Testdatum und der Fußballklasse abgeleitet."
        )
        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert."); return
            sp_r = spieler_by_id(spieler_id)
            _geschl = sp_r.get("geschlecht","Männlich") if sp_r else "Männlich"
            _datum_text = new_datum.strftime("%d.%m.%Y")
            _alter_td = alter_am_datum(
                sp_r.get("geburtsdatum", "") if sp_r else "", _datum_text,
            )
            _fk_td = _fk_aus_datum(
                sp_r.get("geburtsdatum", "") if sp_r else "", stichtag=new_datum,
            ) if sp_r and sp_r.get("geburtsdatum") else None
            _altersgruppe_td = _fk_zu_yoyo(_fk_td, _alter_td)
            ok = ausdauer_update(
                rid, spieler_id, _datum_text,
                new_typ, float(new_dist), new_hf or None, new_rpe or None,
                altersgruppe=_altersgruppe_td, geschlecht=_geschl,
            )
            if ok:
                _save_ok("Ausdauer-Test aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen.")

    st.markdown("---")
    if _confirm_loeschen(f"aus_hist_del_{spieler_id}_{rid}",
                          was=f"Ausdauer-Test vom {rec.get('datum','?')} (ID {rid})",
                          btn_label="🗑️ Ausdauer-Test löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert."); return
        if ausdauer_loeschen(rid, spieler_id):
            _save_ok("Ausdauer-Test gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


# ─── Kraft ────────────────────────────────────────────────────────────────────

def _render_kraft_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für Kraft-Verlauf."""
    from database import kraft_history_edit, kraft_update, kraft_loeschen
    from kraft import lateral_asymmetrie, rumpf_ratio, relative_kraft_berechnen, epley_1rm as _ep1rm
    records = kraft_history_edit(spieler_id)
    if not records:
        st.info("Noch keine Kraft-Tests vorhanden.")
        return

    rec = _edit_select_box(records, f"kr_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]

    with st.form(f"kraft_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**Kraft bearbeiten — ID {rid}**")
        datum_val = _datum_zu_date(rec.get("datum"))
        new_datum = st.date_input("Datum", value=datum_val, key=f"kre_datum_{rid}")
        c1, c2 = st.columns(2)
        new_kgew   = c1.number_input("Körpergewicht (kg)", 0.0, 200.0, float(rec.get("koerpergewicht") or 75.0), 0.5, key=f"kre_kgew_{rid}")
        new_d1rm   = c2.number_input("Direktes 1RM (kg)",  0.0, 300.0, float(rec.get("direktes_1rm") or 0), 2.5, key=f"kre_d1rm_{rid}")
        new_g1rm   = c1.number_input("Geschätztes 1RM (kg)", 0.0, 300.0, float(rec.get("geschaetztes_1rm") or 0), 2.5, key=f"kre_g1rm_{rid}")
        st.caption("Rumpfkraftausdauer (Sekunden)")
        r1, r2, r3, r4 = st.columns(4)
        new_vent_v1 = r1.number_input("Ventral V1 (s)", 0.0, 600.0, float(rec.get("ventral_sekunden") or 0), 1.0, key=f"kre_vv1_{rid}")
        new_vent_v2 = r2.number_input("Ventral V2 (s)", 0.0, 600.0, float(rec.get("ventral_versuch2") or 0), 1.0, key=f"kre_vv2_{rid}")
        new_lat_r   = r3.number_input("Lateral R (s)", 0.0, 600.0, float(rec.get("lateral_rechts_sekunden") or 0), 1.0, key=f"kre_lr_{rid}")
        new_lat_l   = r4.number_input("Lateral L (s)", 0.0, 600.0, float(rec.get("lateral_links_sekunden") or 0), 1.0, key=f"kre_ll_{rid}")
        new_dorsal  = st.number_input("Dorsal (s)", 0.0, 600.0, float(rec.get("dorsal_sekunden") or 0), 1.0, key=f"kre_dors_{rid}")
        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert."); return
            # Abgeleitete Werte berechnen
            _kgew = new_kgew if new_kgew > 0 else None
            _rel_d = relative_kraft_berechnen(new_d1rm or None, new_kgew) if new_d1rm else None
            _rel_g = relative_kraft_berechnen(new_g1rm or None, new_kgew) if new_g1rm else None
            _vent_best = max([v for v in [new_vent_v1 or 0, new_vent_v2 or 0] if v > 0], default=None)
            _lat_diff = abs((new_lat_r or 0) - (new_lat_l or 0)) if new_lat_r and new_lat_l else None
            _lat_asym = lateral_asymmetrie(new_lat_r or None, new_lat_l or None)
            _rumpf_ges = sum([v for v in [_vent_best or 0, new_lat_r or 0, new_lat_l or 0, new_dorsal or 0] if v > 0]) or None
            _r_vd = rumpf_ratio(_vent_best, new_dorsal or None)
            _r_rd = rumpf_ratio(new_lat_r or None, new_dorsal or None)
            _r_ld = rumpf_ratio(new_lat_l or None, new_dorsal or None)
            ok = kraft_update(
                rid, spieler_id, new_datum.strftime("%d.%m.%Y"),
                _kgew, new_d1rm or None, new_g1rm or None,
                _rel_d, _rel_g, int(rec.get("sicherheit_bestaetigt") or 0),
                new_vent_v1 or None, new_vent_v2 or None,
                new_lat_r or None, new_lat_l or None, new_dorsal or None,
                _rumpf_ges, _lat_diff, _lat_asym,
                _r_vd, _r_rd, _r_ld,
                abbruchgrund=rec.get("abbruchgrund"),
                bemerkung=rec.get("bemerkung"),
                ventral_variante=rec.get("ventral_variante"),
                lateral_rechts_variante=rec.get("lateral_rechts_variante"),
                lateral_links_variante=rec.get("lateral_links_variante"),
                dorsal_variante=rec.get("dorsal_variante"),
            )
            if ok:
                _save_ok("Kraft-Test aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen.")

    st.markdown("---")
    if _confirm_loeschen(f"kr_hist_del_{spieler_id}_{rid}",
                          was=f"Kraft-Test vom {rec.get('datum','?')} (ID {rid})",
                          btn_label="🗑️ Kraft-Test löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert."); return
        if kraft_loeschen(rid, spieler_id):
            _save_ok("Kraft-Test gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


# ─── Spiroergometrie ──────────────────────────────────────────────────────────

def _render_spiro_edit(spieler_id: int) -> None:
    """Edit/Delete-Bereich für Spiro-Verlauf inklusive Stufen und Nachbelastung."""
    from database import (
        spiro_history_edit, spiro_test_update_mit_einzelmesspunkten,
        spiro_test_loeschen_sicher, spiro_stufen_laden, spiro_nachbelastung_laden,
        spiro_stufe_loeschen, spiro_nachbelastung_loeschen,
    )
    from spiro import GERAETEARTEN, SCHWELLENMETHODEN
    records = spiro_history_edit(spieler_id)
    if not records:
        st.info("Noch keine Spiro-Tests vorhanden.")
        return

    rec = _edit_select_box(records, f"spiro_{spieler_id}")
    if rec is None:
        return
    rid = rec["id"]

    st.caption("ℹ️ Datum, Kennwerte, Belastungsstufen und Nachbelastungswerte können hier gemeinsam korrigiert werden.")

    with st.form(f"spiro_edit_form_{spieler_id}_{rid}"):
        st.markdown(f"**Spiro bearbeiten — ID {rid}**")
        datum_val = _datum_zu_date(rec.get("datum"))
        new_datum = st.date_input("Datum", value=datum_val, key=f"sp_e_datum_{rid}")
        _gd_idx = GERAETEARTEN.index(rec.get("geraeteart","Laufband")) if rec.get("geraeteart") in GERAETEARTEN else 0
        new_geraet = st.selectbox("Geräteart", GERAETEARTEN, index=_gd_idx, key=f"sp_e_gd_{rid}")
        c1, c2 = st.columns(2)
        new_testort = c1.text_input("Testort", value=rec.get("testort") or "", key=f"sp_e_to_{rid}")
        new_tester  = c2.text_input("Tester", value=rec.get("tester") or "", key=f"sp_e_tr_{rid}")
        new_kgew = c1.number_input("Körpergewicht (kg)", 0.0, 200.0, float(rec.get("koerpergewicht") or 0), 0.5, key=f"sp_e_kg_{rid}")
        st.markdown("##### Ergebniskennwerte")
        rc1, rc2, rc3 = st.columns(3)
        new_vmax   = rc1.number_input("V max (km/h)", 0.0, 40.0, float(rec.get("maximale_geschwindigkeit") or 0), 0.1, key=f"sp_e_vm_{rid}")
        new_hfmax  = rc2.number_input("HF max (bpm)",  0.0, 250.0, float(rec.get("maximale_herzfrequenz") or 0), 1.0, key=f"sp_e_hfm_{rid}")
        new_rpe    = rc3.number_input("RPE max", 0, 20, int(rec.get("rpe_max") or 0), 1, key=f"sp_e_rpe_{rid}")
        rc4, rc5 = st.columns(2)
        new_vo2pk  = rc4.number_input("VO₂ peak (ml/kg/min)", 0.0, 100.0, float(rec.get("vo2_peak") or 0), 0.1, key=f"sp_e_vo2pk_{rid}")
        new_vo2max = rc5.number_input("VO₂max (ml/kg/min)",   0.0, 100.0, float(rec.get("vo2_max") or 0),   0.1, key=f"sp_e_vo2mx_{rid}")
        st.markdown("##### Schwellenwerte")
        sc1, sc2, sc3 = st.columns(3)
        new_vt1v  = sc1.number_input("VT1 Geschw. (km/h)", 0.0, 30.0, float(rec.get("vt1_geschwindigkeit") or 0), 0.1, key=f"sp_e_vt1v_{rid}")
        new_vt1hf = sc2.number_input("VT1 HF (bpm)", 0.0, 250.0, float(rec.get("vt1_herzfrequenz") or 0), 1.0, key=f"sp_e_vt1h_{rid}")
        new_vt2v  = sc3.number_input("VT2 Geschw. (km/h)", 0.0, 30.0, float(rec.get("vt2_geschwindigkeit") or 0), 0.1, key=f"sp_e_vt2v_{rid}")
        sc4, sc5 = st.columns(2)
        new_vt2hf = sc4.number_input("VT2 HF (bpm)", 0.0, 250.0, float(rec.get("vt2_herzfrequenz") or 0), 1.0, key=f"sp_e_vt2h_{rid}")
        _sm_opts = ["—"] + SCHWELLENMETHODEN
        _sm_def  = rec.get("laktatschwelle_methode") or "—"
        _sm_idx  = _sm_opts.index(_sm_def) if _sm_def in _sm_opts else 0
        new_schw_meth = sc5.selectbox("Schwellenmethode", _sm_opts, index=_sm_idx, key=f"sp_e_sm_{rid}")
        sc6, sc7, sc8 = st.columns(3)
        new_schw_v  = sc6.number_input("Schwelle Geschw. (km/h)", 0.0, 30.0, float(rec.get("schwelle_geschwindigkeit") or 0), 0.1, key=f"sp_e_sv_{rid}")
        new_schw_hf = sc7.number_input("Schwelle HF (bpm)", 0.0, 250.0, float(rec.get("schwelle_herzfrequenz") or 0), 1.0, key=f"sp_e_shf_{rid}")
        new_schw_lak = sc8.number_input("Schwelle Laktat (mmol/l)", 0.0, 20.0, float(rec.get("schwelle_laktat") or 0), 0.1, key=f"sp_e_slak_{rid}")
        new_bemerkung = st.text_area("Bemerkung", value=rec.get("bemerkung") or "", key=f"sp_e_bem_{rid}", height=60)

        st.markdown("##### Belastungsstufen")
        st.caption("Fehlende Messwerte leer lassen. Jeder gespeicherte Messpunkt wird per eigener ID aktualisiert; andere Stufen bleiben unverändert.")
        stufen_felder = [
            ("Stufe", "stufennummer"), ("Geschw. (km/h)", "geschwindigkeit_kmh"),
            ("Steigung (%)", "steigung_prozent"), ("Dauer (s)", "dauer_sekunden"),
            ("Strecke (m)", "strecke_meter"), ("HF Ende (bpm)", "herzfrequenz_bpm"),
            ("HF Ø (bpm)", "hf_durchschnitt"), ("VO₂ rel. (ml/kg/min)", "vo2_relativ"),
            ("VO₂ abs. (l/min)", "vo2_absolut"), ("VCO₂ (l/min)", "vco2"),
            ("VE (l/min)", "ve"), ("RER", "rer"), ("Atemfreq. (/min)", "atemfrequenz"),
            ("O₂-Puls", "sauerstoffpuls"), ("Laktat (mmol/l)", "laktat_mmol_l"),
            ("RPE (0–10)", "rpe"), ("✓ vollst.", "stufe_vollstaendig"),
            ("Probe ✓", "blutprobe_gueltig"), ("Bemerkung", "bemerkung"),
        ]
        stufen_bool_felder = {"stufe_vollstaendig", "blutprobe_gueltig"}
        stufen_vorbelegt = []
        for s in spiro_stufen_laden(rid):
            row = {"Messpunkt-ID": s["id"]}
            for label, feld in stufen_felder:
                wert = s.get(feld)
                row[label] = bool(wert) if feld in stufen_bool_felder else wert
            stufen_vorbelegt.append(row)
        stufen_df = pd.DataFrame(
            stufen_vorbelegt,
            columns=["Messpunkt-ID"] + [label for label, _ in stufen_felder],
        )
        stufen_cfg = {
            "Messpunkt-ID": st.column_config.NumberColumn("Messpunkt-ID", disabled=True),
            "Stufe": st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
            "Geschw. (km/h)": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            "Steigung (%)": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            "Dauer (s)": st.column_config.NumberColumn(min_value=0, step=1),
            "Strecke (m)": st.column_config.NumberColumn(min_value=0, step=1),
            "HF Ende (bpm)": st.column_config.NumberColumn(min_value=0, max_value=250, step=1),
            "HF Ø (bpm)": st.column_config.NumberColumn(min_value=0, max_value=250, step=1),
            "VO₂ rel. (ml/kg/min)": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            "VO₂ abs. (l/min)": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
            "VCO₂ (l/min)": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
            "VE (l/min)": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            "RER": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
            "Atemfreq. (/min)": st.column_config.NumberColumn(min_value=0, step=1),
            "O₂-Puls": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            "Laktat (mmol/l)": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            "RPE (0–10)": st.column_config.NumberColumn(min_value=0, max_value=10, step=1),
            "✓ vollst.": st.column_config.CheckboxColumn(default=True),
            "Probe ✓": st.column_config.CheckboxColumn(default=True),
        }
        edited_stufen = st.data_editor(
            stufen_df, num_rows="fixed", use_container_width=True,
            key=f"sp_e_stufen_{rid}", column_config=stufen_cfg, disabled=["Messpunkt-ID"],
        )

        st.markdown("##### Nachbelastungswerte")
        nb_felder = [
            ("Zeit (min)", "zeitpunkt_minuten"), ("HF (bpm)", "herzfrequenz_bpm"),
            ("Laktat (mmol/l)", "laktat_mmol_l"), ("Bemerkung", "bemerkung"),
        ]
        nb_vorbelegt = [
            {"Messpunkt-ID": e["id"], **{label: e.get(feld) for label, feld in nb_felder}}
            for e in spiro_nachbelastung_laden(rid)
        ]
        nb_df = pd.DataFrame(
            nb_vorbelegt,
            columns=["Messpunkt-ID"] + [label for label, _ in nb_felder],
        )
        edited_nb = st.data_editor(
            nb_df, num_rows="fixed", use_container_width=True, key=f"sp_e_nb_{rid}",
            column_config={
                "Messpunkt-ID": st.column_config.NumberColumn("Messpunkt-ID", disabled=True),
                "Zeit (min)": st.column_config.NumberColumn(min_value=0, step=1),
                "HF (bpm)": st.column_config.NumberColumn(min_value=0, max_value=250, step=1),
                "Laktat (mmol/l)": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            },
            disabled=["Messpunkt-ID"],
        )
        submitted = st.form_submit_button("💾 Speichern", type="primary")
        if submitted:
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert."); return
            def _wert(row, label):
                value = row.get(label)
                return None if value is None or pd.isna(value) else value

            neue_stufen = []
            for _, row in edited_stufen.iterrows():
                stufen_id = _wert(row, "Messpunkt-ID")
                if stufen_id is None:
                    neue_stufen = []
                    break
                stufen_werte = {
                    feld: (
                        bool(row.get(label, True)) if feld in stufen_bool_felder
                        else _wert(row, label)
                    )
                    for label, feld in stufen_felder
                }
                neue_stufen.append({"id": int(stufen_id), **stufen_werte})
            neue_nachbelastung = []
            for _, row in edited_nb.iterrows():
                nachbelastung_id = _wert(row, "Messpunkt-ID")
                if nachbelastung_id is None:
                    neue_nachbelastung = []
                    break
                nachbelastung_werte = {
                    feld: _wert(row, label) for label, feld in nb_felder
                }
                neue_nachbelastung.append({"id": int(nachbelastung_id), **nachbelastung_werte})
            _testtyp = rec.get("testtyp","spiro_laufband")
            akt_user = _akt_user()
            ok = spiro_test_update_mit_einzelmesspunkten(
                rid, spieler_id, new_datum.strftime("%Y-%m-%d"), _testtyp,
                neue_stufen, neue_nachbelastung,
                benutzer_id=akt_user.get("id"), rolle=akt_user.get("rolle"),
                verein_id=akt_user.get("verein_id"),
                geraeteart=new_geraet,
                protokoll_id=rec.get("protokoll_id"),
                testort=new_testort or None,
                tester=new_tester or None,
                mit_spiro=int(rec.get("mit_spiro") or 0),
                mit_laktat=int(rec.get("mit_laktat") or 0),
                raumtemperatur=rec.get("raumtemperatur"),
                letzte_mahlzeit=rec.get("letzte_mahlzeit"),
                letzte_intensive_einheit=rec.get("letzte_intensive_einheit"),
                akute_beschwerden=rec.get("akute_beschwerden"),
                koerpergewicht=new_kgew or None,
                maximale_geschwindigkeit=new_vmax or None,
                maximale_herzfrequenz=new_hfmax or None,
                vo2_peak=new_vo2pk or None,
                vo2_max=new_vo2max or None,
                geschaetzte_vo2max=rec.get("geschaetzte_vo2max"),
                vt1_geschwindigkeit=new_vt1v or None,
                vt1_herzfrequenz=new_vt1hf or None,
                vt2_geschwindigkeit=new_vt2v or None,
                vt2_herzfrequenz=new_vt2hf or None,
                laktatschwelle_methode=new_schw_meth if new_schw_meth != "—" else None,
                schwelle_geschwindigkeit=new_schw_v or None,
                schwelle_herzfrequenz=new_schw_hf or None,
                schwelle_laktat=new_schw_lak or None,
                ruhelaktat=rec.get("ruhelaktat"),
                laktat_blutentnahmeort=rec.get("laktat_blutentnahmeort"),
                laktat_messgeraet=rec.get("laktat_messgeraet"),
                rpe_max=new_rpe or None,
                abbruchgrund=rec.get("abbruchgrund"),
                bemerkung=new_bemerkung or None,
            )
            if ok:
                _save_ok("Spiro-Test und gespeicherte Messpunkte aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Aktualisierung fehlgeschlagen oder Zugriff verweigert.")

    st.markdown("##### Einzelne Messpunkte löschen")
    st.caption("Das Löschen betrifft immer nur den gewählten Messpunkt. Haupttest und übrige Messwerte bleiben erhalten.")
    for stufe in spiro_stufen_laden(rid):
        stufen_id = stufe["id"]
        if _confirm_loeschen(
            f"spiro_stage_del_{rid}_{stufen_id}",
            was=f"Belastungsstufe {stufe.get('stufennummer', '?')} (Messpunkt-ID {stufen_id})",
            btn_label=f"🗑️ Stufe {stufe.get('stufennummer', '?')} löschen",
        ):
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert.")
                return
            akt_user = _akt_user()
            if spiro_stufe_loeschen(
                stufen_id, rid, spieler_id,
                benutzer_id=akt_user.get("id"), rolle=akt_user.get("rolle"),
                verein_id=akt_user.get("verein_id"),
            ):
                _save_ok("Belastungsstufe gelöscht. Stufenbasierte Kennwerte wurden aktualisiert.")
                st.rerun()
            else:
                st.error("❌ Löschen fehlgeschlagen oder Zugriff verweigert.")

    for nachbelastung in spiro_nachbelastung_laden(rid):
        nachbelastung_id = nachbelastung["id"]
        if _confirm_loeschen(
            f"spiro_after_del_{rid}_{nachbelastung_id}",
            was=f"Nachbelastungswert bei {nachbelastung.get('zeitpunkt_minuten', '?')} min (Messpunkt-ID {nachbelastung_id})",
            btn_label=f"🗑️ Nachbelastung {nachbelastung.get('zeitpunkt_minuten', '?')} min löschen",
        ):
            if not _history_mandant_ok(spieler_id):
                st.error("❌ Zugriff verweigert.")
                return
            akt_user = _akt_user()
            if spiro_nachbelastung_loeschen(
                nachbelastung_id, rid, spieler_id,
                benutzer_id=akt_user.get("id"), rolle=akt_user.get("rolle"),
                verein_id=akt_user.get("verein_id"),
            ):
                _save_ok("Nachbelastungswert gelöscht.")
                st.rerun()
            else:
                st.error("❌ Löschen fehlgeschlagen oder Zugriff verweigert.")

    st.markdown("---")
    if _confirm_loeschen(f"spiro_hist_del_{spieler_id}_{rid}",
                          was=f"Stufentest vom {rec.get('datum','?')} (ID {rid}) inkl. Stufen und Nachbelastung",
                          btn_label="🗑️ Stufentest löschen"):
        if not _history_mandant_ok(spieler_id):
            st.error("❌ Zugriff verweigert."); return
        if spiro_test_loeschen_sicher(rid, spieler_id):
            _save_ok("Stufentest gelöscht.")
            st.rerun()
        else:
            st.error("❌ Löschen fehlgeschlagen.")


def _player_selector(key_suffix="") -> dict | None:
    """Returns the globally selected player (no per-page dropdown rendered).
    The selector lives in the sidebar; all pages share the same active player."""
    spieler = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
    if not spieler:
        st.warning("👤 Noch keine Spieler angelegt. Gehe zu **Spieler → Verwaltung** um den ersten Spieler anzulegen.")
        return None
    pid = st.session_state.get("global_player_id")
    if pid:
        match = next((p for p in spieler if p["id"] == pid), None)
        if match:
            return match
    # Fallback to first player; also store in session state
    st.session_state["global_player_id"] = spieler[0]["id"]
    return spieler[0]


def _spieler_suchname(spieler: dict) -> str:
    """Stable display name for the shared active-player search."""
    return (
        spieler.get("name")
        or f"{spieler.get('vorname', '')} {spieler.get('nachname', '')}".strip()
        or f"Spieler #{spieler.get('id', '—')}"
    )


def _spieler_suchtreffer(spieler_liste: list[dict], suchtext: str) -> list[dict]:
    """Case-insensitive partial search over first name, last name and full name."""
    query = (suchtext or "").strip().casefold()
    if not query:
        return spieler_liste
    treffer = []
    for spieler in spieler_liste:
        vorname = str(spieler.get("vorname") or "")
        nachname = str(spieler.get("nachname") or "")
        name = _spieler_suchname(spieler)
        suchfelder = (vorname, nachname, name, f"{vorname} {nachname}")
        if any(query in feld.casefold() for feld in suchfelder if feld):
            treffer.append(spieler)
    return treffer


def _aktiven_spieler_suchbereich(
    spieler_liste: list[dict],
    bereich: str,
    *,
    titel: str = "Spieler suchen …",
) -> dict | None:
    """Shared, confirmed active-player search for sidebar and main pages.

    Only ``global_player_id`` is written. The player list is always supplied by
    the caller's existing permission-aware ``spieler_laden`` call.
    """
    if not spieler_liste:
        return None

    query_key = f"_aktiver_spieler_suche_{bereich}"
    choice_key = f"_aktiver_spieler_treffer_{bereich}"
    notice_key = f"_aktiver_spieler_hinweis_{bereich}"

    suchtext = st.text_input(
        titel,
        key=query_key,
        placeholder="Vorname, Nachname oder vollständiger Name",
        label_visibility="collapsed" if bereich == "sidebar" else "visible",
    )
    treffer = _spieler_suchtreffer(spieler_liste, suchtext)
    if not treffer:
        st.caption("Kein passender Spieler gefunden.")
        return None

    current_id = st.session_state.get("global_player_id")
    current_index = next(
        (i for i, spieler in enumerate(treffer) if spieler.get("id") == current_id),
        0,
    )
    auswahl = st.selectbox(
        "Treffer",
        treffer,
        index=current_index,
        format_func=_spieler_suchname,
        key=choice_key,
        label_visibility="collapsed" if bereich == "sidebar" else "visible",
    )
    if st.button(
        "Auswahl bestätigen",
        key=f"_aktiver_spieler_bestaetigen_{bereich}",
        use_container_width=True,
        type="primary" if bereich != "sidebar" else "secondary",
    ):
        st.session_state["global_player_id"] = auswahl["id"]
        st.session_state[f"_aktiver_spieler_suche_offen_{bereich}"] = False
        st.session_state[notice_key] = _spieler_suchname(auswahl)
        st.rerun()

    hinweis = st.session_state.pop(notice_key, None)
    if hinweis:
        st.success(f"✅ {hinweis} ist jetzt der aktive Spieler.")
    return auswahl


def _inline_spielerwechsel(bereich: str) -> None:
    """Renders the shared in-place active-player switcher for one main page."""
    offen_key = f"_aktiver_spieler_suche_offen_{bereich}"
    hinweis_key = f"_aktiver_spieler_hinweis_{bereich}"
    if st.button(
        "👤 Spieler wechseln",
        key=f"{bereich}_spieler_wechsel",
        use_container_width=False,
    ):
        st.session_state[offen_key] = not st.session_state.get(offen_key, False)
        st.rerun()

    hinweis = st.session_state.pop(hinweis_key, None)
    if hinweis:
        st.success(f"✅ {hinweis} ist jetzt der aktive Spieler.")

    if st.session_state.get(offen_key):
        berechtigte_spieler = spieler_laden(
            _akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"]
        )
        _aktiven_spieler_suchbereich(berechtigte_spieler, bereich)


# ─── Plotly theme helper ───────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    font=dict(color="#e6edf3", family="Inter, Segoe UI, system-ui"),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#30363d"),
    margin=dict(l=40, r=20, t=40, b=40),
)

_AXIS_BASE = dict(gridcolor="#21262d", linecolor="#30363d", zerolinecolor="#30363d")


def _pl(**overrides) -> dict:
    """Erstellt ein Plotly-Layout ohne doppelte Schlüsselkonflikte."""
    layout = {k: v for k, v in PLOTLY_LAYOUT.items()
              if k not in overrides and k not in ("xaxis", "yaxis")}
    layout["xaxis"] = {**_AXIS_BASE, **overrides.pop("xaxis", {})}
    layout["yaxis"] = {**_AXIS_BASE, **overrides.pop("yaxis", {})}
    layout.update(overrides)
    return layout


# ══════════════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    """Mannschaft-Seite: Kachelansicht, Filter, Trainingsgruppen, Warnmeldungen."""
    from datetime import timedelta as _td, datetime as _dt

    st.markdown(
        section_header("👥 Mannschaft", "Kaderübersicht, Trainingsgruppen und Warnmeldungen"),
        unsafe_allow_html=True,
    )

    all_players = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
    if not all_players:
        st.markdown(
            empty_state("👥", "Noch keine Spieler angelegt",
                        "Gehe zur Spielerverwaltung, um Spieler hinzuzufügen."),
            unsafe_allow_html=True,
        )
        return

    # ── Enrich all player data (one pass) ─────────────────────────────────────
    player_data = []
    for p in all_players:
        pid    = p["id"]
        fms    = fms_letzter(pid)
        y      = y_balance_letzter(pid)
        sprint = sprint_letzter(pid)
        sprung = sprung_letzter(pid)
        agil   = agilitaet_letzter(pid)
        aus    = ausdauer_letzter(pid)
        anthro = anthropometrie_letzter(pid)
        spiro  = spiro_test_letzter(pid)
        verlet = verletzungen_laden(pid)
        rs     = risiko_score(fms, y, verlet)
        _, level = risiko_label(rs)
        spiro  = spiro_test_letzter(pid)
        sc     = athletik_score(fms, y, sprint, sprung, agil, aus, spiro_row=spiro)
        defizite = defizite_ermitteln(fms, y, sprint, sprung, agil, aus, anthro,
                                      spiro_row=spiro,
                                      geschlecht=p.get("geschlecht", "Männlich"))
        # last test date across all modules
        dates = [d["datum"] for d in [fms, y, sprint, sprung, agil, aus]
                 if d and d.get("datum")]
        last_test_date = max(dates) if dates else None
        player_data.append({
            "p": p, "fms": fms, "y": y, "sprint": sprint, "sprung": sprung,
            "agil": agil, "aus": aus, "anthro": anthro, "spiro": spiro,
            "verlet": verlet, "rs": rs, "level": level, "sc": sc,
            "defizite": defizite, "last_test_date": last_test_date,
        })

    total     = len(player_data)
    scores    = [d["sc"] for d in player_data]
    high_risk = sum(1 for d in player_data if d["level"] == "hoch")
    med_risk  = sum(1 for d in player_data if d["level"] == "mittel")
    avg_score = round(sum(scores) / len(scores)) if scores else 0

    # ── KPI strip ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spieler gesamt", total)
    c2.metric("🔴 Handlungsbedarf Hoch", high_risk)
    c3.metric("🟡 Handlungsbedarf", med_risk)
    c4.metric("Ø Athletik Score", f"{avg_score}/100")

    # ── KPI-Filter aus dem Dashboard (Direktlinks) ───────────────────────────
    _kpi_filter = st.session_state.get("kpi_filter")
    if _kpi_filter:
        _FILTER_LABELS = {
            # Dieselben 5 Module wie dashboard_trainer_ohne_test():
            # fms_test, sprint_test, y_balance_test, agilitaet_test, ausdauer_test
            # Sprungtest wird bewusst NICHT berücksichtigt.
            "faellig":  ("📋", "Spieler ohne Test > 30 Tage (FMS, Sprint, Y-Balance, Agilität, Ausdauer)",
                         lambda d: all(
                             (not x or not x.get("datum") or
                              (lambda _d: _d is None or (date.today() - _d).days > 30)(
                                  parse_datum_safe(x["datum"])))
                             for x in [d["fms"], d["sprint"], d["y"], d["agil"], d["aus"]]
                         )),
            "verletzt": ("🩺", "Spieler mit Verletzung in den letzten 14 Tagen",
                         lambda d: any(
                             (lambda s: s is not None and (date.today() - s).days <= 14)(
                                 parse_datum_safe(v.get("datum"))
                             )
                             for v in (d["verlet"] or [])
                         )),
            "risiko":   ("⚠", "Spieler mit erhöhtem Verletzungsrisiko (mittel/hoch)",
                         lambda d: d["level"] in ("hoch", "mittel")),
        }
        if _kpi_filter in _FILTER_LABELS:
            _fi, _fl, _ff = _FILTER_LABELS[_kpi_filter]
            _banner_cols = st.columns([9, 1])
            with _banner_cols[0]:
                st.info(f"{_fi} **Aktiver Filter:** {_fl}")
            with _banner_cols[1]:
                if st.button("✕ Filter entfernen", key="kpi_filter_clear",
                             use_container_width=True):
                    del st.session_state["kpi_filter"]
                    st.rerun()
            player_data = [d for d in player_data if _ff(d)]
            if not player_data:
                st.warning("Keine Spieler für diesen Filter gefunden.")

    st.markdown("---")

    # ── Helper: render color ───────────────────────────────────────────────────
    _RISK_COLOR  = {"hoch": C["red"], "mittel": C["yellow"], "gering": C["green"]}
    _RISK_ICON   = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}
    _RISK_LABEL  = {"hoch": "Handlungsbedarf hoch", "mittel": "Handlungsbedarf", "gering": "Unauffällig"}

    def _score_color(s: int) -> str:
        return C["green"] if s >= 75 else C["yellow"] if s >= 50 else C["red"]

    def _fmt_date(d: str | None) -> str:
        if not d:
            return "Kein Test"
        _pd = parse_datum_safe(d)
        return _pd.strftime("%d.%m.%Y") if _pd else str(d)

    def _days_since(d: str | None) -> int | None:
        if not d:
            return None
        _pd = parse_datum_safe(d)
        return (date.today() - _pd).days if _pd else None

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_kacheln, tab_gruppen, tab_warn, tab_tabelle = st.tabs([
        "🃏 Spielerkacheln", "🏋️ Trainingsgruppen", "⚠️ Warnmeldungen", "📊 Kader-Tabelle"
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — SPIELERKACHELN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_kacheln:
        # Filter bar
        f1, f2, f3, f4 = st.columns(4)
        alle_pos  = sorted({d["p"].get("hauptposition") or d["p"].get("position") or ""
                            for d in player_data
                            if d["p"].get("hauptposition") or d["p"].get("position")})
        alle_mann = sorted({d["p"].get("mannschaft") or "" for d in player_data
                            if d["p"].get("mannschaft")})
        alle_ak   = sorted({d["p"].get("altersklasse") or "" for d in player_data
                            if d["p"].get("altersklasse")})
        alle_stat = sorted({d["p"].get("trainingsstatus") or "" for d in player_data
                            if d["p"].get("trainingsstatus")})

        filt_pos  = f1.selectbox("Position",       ["Alle"] + alle_pos,  key="dash_pos",  label_visibility="visible")
        filt_mann = f2.selectbox("Mannschaft",      ["Alle"] + alle_mann, key="dash_mann", label_visibility="visible")
        filt_ak   = f3.selectbox("Altersklasse",    ["Alle"] + alle_ak,   key="dash_ak",   label_visibility="visible")
        filt_stat = f4.selectbox("Trainingsstatus", ["Alle"] + alle_stat, key="dash_stat", label_visibility="visible")

        filtered = player_data
        if filt_pos  != "Alle":
            filtered = [d for d in filtered
                        if (d["p"].get("hauptposition") or d["p"].get("position")) == filt_pos]
        if filt_mann != "Alle":
            filtered = [d for d in filtered if d["p"].get("mannschaft") == filt_mann]
        if filt_ak   != "Alle":
            filtered = [d for d in filtered if d["p"].get("altersklasse") == filt_ak]
        if filt_stat != "Alle":
            filtered = [d for d in filtered if d["p"].get("trainingsstatus") == filt_stat]

        st.caption(f"{len(filtered)} von {total} Spielern")

        if not filtered:
            st.info("Keine Spieler für die gewählten Filter.")
        else:
            cols = st.columns(3, gap="medium")
            for i, d in enumerate(filtered):
                p      = d["p"]
                level  = d["level"]
                rc     = _RISK_COLOR[level]
                sc_col = _score_color(d["sc"])
                pos    = p.get("hauptposition") or p.get("position") or "—"
                team   = p.get("mannschaft") or "—"

                # Key metrics (compact)
                metrics = []
                if d["fms"] and d["fms"].get("score"):
                    metrics.append(f"FMS {d['fms']['score']}/21")
                _spr_ov = d.get("sprint")
                if _spr_ov:
                    for _ovdist, _ovlbl in [
                        ("beste_30m","30m"),("beste_20m","20m"),
                        ("beste_10m","10m"),("beste_40m","40m"),("beste_5m","5m"),
                    ]:
                        _ovv = _spr_ov.get(_ovdist) or 0
                        if _ovv > 0:
                            metrics.append(f"{_ovlbl} {_ovv:.2f}s")
                            break
                if d["sprung"] and d["sprung"].get("cmj_beid"):
                    metrics.append(f"CMJ {d['sprung']['cmj_beid']:.0f}cm")
                metrics_str = " · ".join(metrics) if metrics else "Noch keine Testdaten"

                with cols[i % 3]:
                    st.markdown(
                        f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
                        f'border-top:3px solid {rc};border-radius:12px;'
                        f'padding:14px 16px 10px;margin-bottom:4px">'
                        f'<div style="font-size:16px;font-weight:700;color:{C["text"]}">{p["name"]}</div>'
                        f'<div style="font-size:11px;color:{C["muted"]};margin-bottom:8px">'
                        f'{pos} · {team}</div>'
                        f'<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:6px">'
                        f'<span style="font-size:28px;font-weight:800;color:{sc_col}">{d["sc"]}</span>'
                        f'<span style="font-size:11px;color:{C["muted"]}">/ 100 Athletik-Score</span>'
                        f'</div>'
                        f'<div style="font-size:11px;color:{rc};font-weight:600;margin-bottom:6px">'
                        f'{_RISK_ICON[level]} {_RISK_LABEL[level]}</div>'
                        f'<div style="font-size:10px;color:{C["muted"]}">'
                        f'{metrics_str}</div>'
                        f'<div style="font-size:10px;color:{C["muted"]};margin-top:4px">'
                        f'🗓 {_fmt_date(d["last_test_date"])}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("Zum Profil →", key=f"kachel_profil_{p['id']}",
                                 use_container_width=True):
                        st.session_state["global_player_id"] = p["id"]
                        st.session_state["_nav_goto"]         = "👤  Spieler"
                        st.session_state["nav_sub_spieler"]   = "🏃 Profil & Diagnostik"
                        st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — TRAININGSGRUPPEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_gruppen:
        st.markdown(
            f'<div style="font-size:13px;color:{C["muted"]};margin-bottom:16px">'
            f'Automatischer Vorschlag basierend auf kritischen Defiziten aus der Testanalyse. '
            f'Spieler werden dem Bereich mit dem dringlichsten Förderbedarf zugeordnet.</div>',
            unsafe_allow_html=True,
        )

        # Map defizit modul → group
        _MODUL_GRUPPE = {
            "Sprint":         "⚡ Gruppe Schnelligkeit",
            "Agilität":       "⚡ Gruppe Schnelligkeit",
            "Sprung":         "🦘 Gruppe Sprungkraft",
            "FMS":            "🔒 Gruppe Stabilität & Bewegungskontrolle",
            "Y-Balance":      "🔒 Gruppe Stabilität & Bewegungskontrolle",
            "Ausdauer":       "🫁 Gruppe Ausdauerkapazität",
        }
        _GRUPPE_INFO = {
            "⚡ Gruppe Schnelligkeit":              "Sprint, Beschleunigung, Richtungswechsel",
            "🦘 Gruppe Sprungkraft":                "Explosivkraft, Reaktivkraft, Beinachsenstabilität",
            "🔒 Gruppe Stabilität & Bewegungskontrolle": "FMS-Defizite, Y-Balance-Asymmetrien, Core-Stabilität",
            "🫁 Gruppe Ausdauerkapazität":          "Aerobe Basis, intermittierende Ausdauer",
            "✅ Kein spezifischer Förderbedarf":    "Keine kritischen Defizite — allgemeines Athletiktraining",
        }
        _GRUPPE_ORDER = [
            "⚡ Gruppe Schnelligkeit",
            "🦘 Gruppe Sprungkraft",
            "🔒 Gruppe Stabilität & Bewegungskontrolle",
            "🫁 Gruppe Ausdauerkapazität",
            "✅ Kein spezifischer Förderbedarf",
        ]

        gruppen: dict[str, list] = {g: [] for g in _GRUPPE_ORDER}

        for d in player_data:
            # Find primary critical deficit, then warnung
            primary_group = None
            for level_filter in ("kritisch", "warnung"):
                for defizit in d["defizite"]:
                    if defizit["level"] == level_filter:
                        modul = defizit.get("modul", "")
                        if modul in _MODUL_GRUPPE:
                            primary_group = _MODUL_GRUPPE[modul]
                            break
                if primary_group:
                    break
            if not primary_group:
                primary_group = "✅ Kein spezifischer Förderbedarf"
            gruppen[primary_group].append(d)

        for gruppe_name in _GRUPPE_ORDER:
            mitglieder = gruppen[gruppe_name]
            if not mitglieder:
                continue
            info = _GRUPPE_INFO[gruppe_name]
            with st.expander(
                f"{gruppe_name} — {len(mitglieder)} Spieler",
                expanded=gruppe_name != "✅ Kein spezifischer Förderbedarf",
            ):
                st.caption(f"Trainingsschwerpunkt: {info}")
                cols = st.columns(min(len(mitglieder), 4))
                for j, d in enumerate(mitglieder):
                    p = d["p"]
                    rc = _RISK_COLOR[d["level"]]
                    # Show primary deficit text
                    prim_def = next(
                        (df["text"] for df in d["defizite"] if df.get("modul") in _MODUL_GRUPPE
                         and _MODUL_GRUPPE[df["modul"]] == gruppe_name),
                        None
                    )
                    with cols[j % 4]:
                        st.markdown(
                            f'<div style="background:{C["surface2"]};border:1px solid {C["border"]};'
                            f'border-left:3px solid {rc};border-radius:8px;padding:10px 12px;'
                            f'margin-bottom:6px">'
                            f'<div style="font-size:13px;font-weight:600;color:{C["text"]}">'
                            f'{p["name"]}</div>'
                            f'<div style="font-size:10px;color:{C["muted"]}">'
                            f'{p.get("hauptposition") or p.get("position") or "—"}</div>'
                            f'<div style="font-size:10px;color:{rc};margin-top:4px">'
                            f'{_RISK_ICON[d["level"]]} Score {d["sc"]}/100</div>'
                            + (f'<div style="font-size:9px;color:{C["muted"]};margin-top:4px;'
                               f'line-height:1.3">{prim_def}</div>' if prim_def else "")
                            + f'</div>',
                            unsafe_allow_html=True,
                        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — WARNMELDUNGEN
    # ══════════════════════════════════════════════════════════════════════════
    with tab_warn:
        RETEST_TAGE = 56  # 8 Wochen

        warns_risiko     = [d for d in player_data if d["level"] == "hoch"]
        warns_retest     = [d for d in player_data
                            if (_days_since(d["last_test_date"]) or 999) > RETEST_TAGE]
        warns_wachstum   = []
        warns_eingeschr  = []
        warns_bmi        = []   # Anthropometrie: BMI auffällig

        for d in player_data:
            # Growth spurt: PHV-related reifestatus
            if d["anthro"]:
                reife = str(d["anthro"].get("reifestatus") or "").lower()
                phv   = d["anthro"].get("phv_offset")
                if ("vor phv" in reife or "wachstum" in reife
                        or (phv is not None and -1.5 <= float(phv) <= 1.0)):
                    warns_wachstum.append(d)
            # Restricted training status
            ts = str(d["p"].get("trainingsstatus") or "")
            if "Pause" in ts or "Abklärung" in ts or "Eingeschränkt" in ts or "Angepasst" in ts:
                warns_eingeschr.append(d)
            # BMI-Auffälligkeit
            if d["anthro"]:
                bmi = d["anthro"].get("bmi")
                if bmi:
                    bmi_f = float(bmi)
                    if bmi_f >= 25 or (0 < bmi_f < 18.5):
                        warns_bmi.append(d)
        def _warn_block(title: str, icon: str, color: str, items: list,
                        detail_fn) -> None:
            if not items:
                st.markdown(
                    f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
                    f'border-radius:8px;padding:10px 14px;margin-bottom:10px;'
                    f'display:flex;gap:10px;align-items:center">'
                    f'<span style="font-size:18px">{icon}</span>'
                    f'<div><div style="font-size:13px;font-weight:600;color:{C["muted"]}">'
                    f'{title}</div>'
                    f'<div style="font-size:11px;color:{C["muted"]}">Keine Auffälligkeiten</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                return
            with st.expander(f"{icon} {title} — {len(items)} Spieler", expanded=True):
                for d in items:
                    p   = d["p"]
                    det = detail_fn(d)
                    st.markdown(
                        f'<div style="background:{C["surface2"]};border-left:3px solid {color};'
                        f'border-radius:6px;padding:8px 12px;margin-bottom:6px">'
                        f'<div style="font-size:13px;font-weight:600;color:{C["text"]}">'
                        f'{p["name"]}</div>'
                        f'<div style="font-size:11px;color:{C["muted"]}">'
                        f'{p.get("hauptposition") or p.get("position") or "—"} · '
                        f'{p.get("mannschaft") or "—"}</div>'
                        f'<div style="font-size:11px;color:{color};margin-top:4px">{det}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        _warn_block(
            "Hoher Risikoscore",
            "🔴", C["red"], warns_risiko,
            lambda d: f"Risikoscore {d['rs']} — FMS/Y-Balance oder Verletzungshistorie kritisch"
        )
        _warn_block(
            f"Fälliger Retest (>{RETEST_TAGE} Tage)",
            "📅", C["yellow"], warns_retest,
            lambda d: (f"Letzter Test: {_fmt_date(d['last_test_date'])} "
                       f"({_days_since(d['last_test_date']) or '?'} Tage)")
        )
        _warn_block(
            "Körperzusammensetzung auffällig (BMI)",
            "⚖️", C["yellow"], warns_bmi,
            lambda d: (
                f"BMI {float(d['anthro']['bmi']):.1f} — "
                + ("Übergewicht" if float(d['anthro']['bmi']) >= 25 else "Untergewicht")
                + (f" · {d['anthro'].get('bmi_kategorie') or ''}")
            )
        )
        _warn_block(
            "Wachstumsschub-Fenster",
            "🌱", C["blue"], warns_wachstum,
            lambda d: (f"Reifestatus: {d['anthro'].get('reifestatus') or '—'} · "
                       f"PHV-Offset: {d['anthro'].get('phv_offset') or '—'} Jahre"
                       if d["anthro"] else "PHV-Daten vorhanden")
        )
        _warn_block(
            "Eingeschränkter Trainingsstatus",
            "🚫", C["muted"], warns_eingeschr,
            lambda d: d["p"].get("trainingsstatus") or "—"
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — KADER-TABELLE (bestehende Ansicht)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_tabelle:
        col_left, col_right = st.columns([1, 2])
        with col_left:
            st.markdown("##### Athletik-Status Verteilung")
            low_risk = total - high_risk - med_risk
            fig_pie = go.Figure(go.Pie(
                labels=["Handlungsbedarf Hoch", "Handlungsbedarf", "Unauffällig"],
                values=[high_risk, med_risk, low_risk],
                hole=0.55,
                marker_colors=["#f85149", "#d29922", "#3fb950"],
                textfont=dict(color="#e6edf3"),
            ))
            fig_pie.update_layout(**PLOTLY_LAYOUT, height=240, showlegend=True,
                                  legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_right:
            st.markdown("##### Athletik Scores — Kader")
            names  = [d["p"]["name"] for d in player_data]
            cols_c = [_color_for_score(d["sc"]) for d in player_data]
            fig_bar = go.Figure(go.Bar(
                x=names, y=scores,
                marker_color=cols_c,
                text=scores, textposition="outside",
                textfont=dict(color="#e6edf3"),
            ))
            fig_bar.update_layout(**_pl(height=240, yaxis=dict(range=[0, 105])))
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        # ── Suche & Filter ────────────────────────────────────────────────────
        _kt_c1, _kt_c2, _kt_c3 = st.columns([3, 2, 2])
        _kt_suche = _kt_c1.text_input("🔍 Spieler suchen", placeholder="Name …",
                                       key="kt_suche", label_visibility="collapsed")
        _kt_risiko = _kt_c2.selectbox("Risikolevel", ["Alle", "🔴 Hoch", "🟡 Mittel", "🟢 Gering"],
                                       key="kt_risiko")
        _alle_kt_mann = sorted({d["p"].get("mannschaft") or "" for d in player_data if d["p"].get("mannschaft")})
        _kt_mann = _kt_c3.selectbox("Mannschaft", ["Alle"] + _alle_kt_mann, key="kt_mann2")

        rows = []
        for d in player_data:
            p, fms, y, sprint, sprung, agil, aus = (
                d["p"], d["fms"], d["y"], d["sprint"], d["sprung"], d["agil"], d["aus"]
            )
            # Suche & Filter anwenden
            if _kt_suche.strip() and _kt_suche.lower() not in p["name"].lower():
                continue
            _rl = d["level"]
            if _kt_risiko == "🔴 Hoch"   and _rl != "hoch":   continue
            if _kt_risiko == "🟡 Mittel" and _rl != "mittel": continue
            if _kt_risiko == "🟢 Gering" and _rl != "gering": continue
            if _kt_mann != "Alle" and p.get("mannschaft") != _kt_mann: continue

            icon = _RISK_ICON[_rl]
            rows.append({
                "Name":           p["name"],
                "Position":       p.get("hauptposition") or p.get("position") or "—",
                "Mannschaft":     p.get("mannschaft") or "—",
                "Altersklasse":   p.get("altersklasse") or "—",
                "Athletik Score": d["sc"],
                "FMS Score":      fms["score"] if fms else None,
                "Y-Balance Ø":    round((y["composite_rechts"] + y["composite_links"]) / 2, 1)
                                  if y else None,
                "Sprint (s)": (
                    next(
                        (sprint.get(k) for k in (
                            "beste_30m","beste_20m","beste_10m","beste_40m","beste_5m"
                        ) if (sprint.get(k) or 0) > 0),
                        None,
                    ) if sprint else None
                ),
                "CMJ (cm)":       sprung["cmj_beid"] if sprung and sprung.get("cmj_beid") else None,
                "VO₂max (Yo-Yo)": aus["vo2max"] if aus and aus.get("vo2max") else None,
                "VO₂ (Spiro)": (
                    f"{float(d['spiro']['vo2_peak']):.1f} (direkt)"
                    if d.get("spiro") and d["spiro"].get("vo2_peak") else
                    f"{float(d['spiro']['vo2_max']):.1f} (direkt)"
                    if d.get("spiro") and d["spiro"].get("vo2_max") else
                    f"{float(d['spiro']['geschaetzte_vo2max']):.1f} (geschätzt)"
                    if d.get("spiro") and d["spiro"].get("geschaetzte_vo2max") else None
                ),
                "BMI":            (
                    float(d["anthro"]["bmi"]) if d.get("anthro") and d["anthro"].get("bmi")
                    else None
                ),
                "Risiko":         f"{icon} {_rl.capitalize()}",
            })
        _df_kt = pd.DataFrame(rows)
        if not _df_kt.empty:
            st.dataframe(
                _df_kt,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Athletik Score": st.column_config.ProgressColumn(
                        "Athletik Score", min_value=0, max_value=100, format="%d"),
                    "FMS Score":        st.column_config.NumberColumn("FMS Score", format="%d / 21"),
                    "Y-Balance Ø":      st.column_config.NumberColumn("Y-Balance Ø", format="%.1f %%"),
                    "Sprint 10m (s)":   st.column_config.NumberColumn("Sprint 10m (s)", format="%.2f s"),
                    "CMJ (cm)":         st.column_config.NumberColumn("CMJ (cm)", format="%.0f cm"),
                    "VO₂max (Yo-Yo)":   st.column_config.NumberColumn("VO₂max Yo-Yo", format="%.1f"),
                    "VO₂ (Spiro)":      st.column_config.TextColumn("VO₂ Spiro"),
                    "BMI":              st.column_config.NumberColumn("BMI", format="%.1f"),
                },
            )
            st.caption(f"{len(rows)} von {total} Spielern angezeigt.")
        else:
            st.info("Keine Spieler für die gewählten Filter.")

        st.markdown("---")
        st.markdown("### 📥 Kader-Export")
        col_exp, _ = st.columns([1, 3])
        with col_exp:
            with st.spinner("Excel wird vorbereitet …"):
                excel_data = kader_excel_bytes()
            filename = f"Kader_Export_{date.today().strftime('%Y-%m-%d')}.xlsx"
            st.download_button(
                label="⬇️ Kader-Export (Excel)",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Exportiert alle Spieler-Stammdaten, letzte Testwerte und die gesamte Verletzungshistorie als Excel-Datei (2 Tabellenblätter).",
            )


# ──────────────────────────────────────────────────────────────────────────────

def _render_inline_edit_form(sp: dict) -> None:
    """Inline-Bearbeitungsformular für einen Spieler direkt in der Spielerliste."""
    _sid = sp["id"]
    _vn_def = sp.get("vorname") or (sp["name"].split()[0] if " " in sp["name"] else sp["name"])
    _nn_def = sp.get("nachname") or (" ".join(sp["name"].split()[1:]) if " " in sp["name"] else "")

    st.markdown(
        '<div style="background:#161b22;border:1px solid #388bfd44;'
        'border-left:3px solid #388bfd;border-radius:8px;padding:16px 20px;margin:6px 0 14px 0">',
        unsafe_allow_html=True,
    )
    st.markdown(f"##### ✏️ {sp['name']} bearbeiten")

    st.markdown("**👤 Persönliche Daten**")
    _c1, _c2 = st.columns(2)
    _e_vn    = _c1.text_input("Vorname *",                    value=_vn_def,                     key=f"il_vn_{_sid}")
    _e_nn    = _c2.text_input("Nachname *",                   value=_nn_def,                     key=f"il_nn_{_sid}")
    _e_geb   = _c1.text_input("Geburtsdatum (TT.MM.JJJJ) *", value=sp.get("geburtsdatum") or "", key=f"il_geb_{_sid}")
    _gi      = ["Männlich", "Weiblich", "Divers"].index(sp.get("geschlecht", "Männlich")) \
               if sp.get("geschlecht") in ["Männlich", "Weiblich", "Divers"] else 0
    _e_gesch = _c2.selectbox("Geschlecht", ["Männlich", "Weiblich", "Divers"],
                              index=_gi, key=f"il_gesch_{_sid}")
    _e_alter = berechne_alter(_e_geb)
    _e_ak_vs = altersklasse_vorschlag(_e_geb)
    if _e_alter:
        _e_fki   = _fki(_e_geb)
        _e_fk    = _e_fki.get("fussballklasse") or "?"
        _e_jk    = _jugendklasse(_e_fk)
        _e_sl    = _e_fki.get("saison", "")
        _c1.markdown(
            f"<small style='color:#3fb950'>"
            f"Alter: **{_e_alter} Jahre** · Fußballklasse: **{_e_fk}** (Saison {_e_sl})"
            f"<br>Jugendklasse: **{_e_jk}** · Altersklassen-Vorschlag: {_e_ak_vs}</small>",
            unsafe_allow_html=True,
        )
    _aki  = ALTERSKLASSEN.index(sp.get("altersklasse")) \
            if sp.get("altersklasse") in ALTERSKLASSEN else 7
    _e_ak = _c2.selectbox("Altersklasse", ALTERSKLASSEN, index=_aki, key=f"il_ak_{_sid}")

    st.markdown("**🏟️ Sportliche Daten**")
    _p1, _p2 = st.columns(2)
    _cur_hpos = sp.get("hauptposition") or sp.get("position") or POSITIONEN[0]
    _hpi    = POSITIONEN.index(_cur_hpos) if _cur_hpos in POSITIONEN else 0
    _e_hpos = _p1.selectbox("Hauptposition *", POSITIONEN, index=_hpi, key=f"il_hpos_{_sid}")
    _npl    = ["—"] + POSITIONEN
    _cur_npos = sp.get("nebenposition") or "—"
    _npi    = _npl.index(_cur_npos) if _cur_npos in _npl else 0
    _e_npos = _p2.selectbox("Nebenposition", _npl, index=_npi, key=f"il_npos_{_sid}")
    _sbi    = ["Rechts", "Links", "Beidfüßig"].index(sp.get("spielbein", "Rechts")) \
              if sp.get("spielbein") in ["Rechts", "Links", "Beidfüßig"] else 0
    _e_sb   = _p1.selectbox("Spielbein", ["Rechts", "Links", "Beidfüßig"], index=_sbi, key=f"il_sb_{_sid}")
    _lvi    = LEISTUNGSNIVEAUS.index(sp.get("leistungsniveau", LEISTUNGSNIVEAUS[0])) \
              if sp.get("leistungsniveau") in LEISTUNGSNIVEAUS else 0
    _e_lvl  = _p2.selectbox("Leistungsniveau", LEISTUNGSNIVEAUS, index=_lvi, key=f"il_lvl_{_sid}")

    st.markdown("**🏃 Teamdaten**")
    _t1, _t2 = st.columns(2)
    _e_mann = _t1.text_input("Mannschaft / Verein", value=sp.get("mannschaft") or "", key=f"il_mann_{_sid}")
    _tsi    = TRAININGSSTATUS.index(sp.get("trainingsstatus", TRAININGSSTATUS[0])) \
              if sp.get("trainingsstatus") in TRAININGSSTATUS else 0
    _e_ts   = _t2.selectbox("Trainingsstatus", TRAININGSSTATUS, index=_tsi, key=f"il_ts_{_sid}")

    # ── Trainer-Zuweisung (nur Superadmin und Vereinsadmin) ───────────────────
    _rolle = _akt_user()["rolle"]
    _new_trainer_id = None  # Sentinel: keine Änderung
    _new_verein_id  = None
    _zuweisung_changed = False

    if _rolle in ("Superadmin", "Vereinsadmin"):
        st.markdown("**🔗 Trainer-Zuweisung**")
        _za1, _za2 = st.columns(2)

        # Vereine laden
        _alle_vereine = vereine_laden()
        if _rolle == "Vereinsadmin":
            # Vereinsadmin sieht nur seinen eigenen Verein
            _va_vid = _akt_user()["verein_id"]
            _alle_vereine = [v for v in _alle_vereine if v["id"] == _va_vid]

        _verein_opts   = ["— kein Verein —"] + [v["name"] for v in _alle_vereine]
        _verein_ids    = [None] + [v["id"] for v in _alle_vereine]
        _cur_vid       = sp.get("verein_id")
        _verein_idx    = _verein_ids.index(_cur_vid) if _cur_vid in _verein_ids else 0
        _e_verein_name = _za1.selectbox("Verein", _verein_opts, index=_verein_idx, key=f"il_verein_{_sid}")
        _e_verein_id   = _verein_ids[_verein_opts.index(_e_verein_name)]

        # Trainer laden — über trainer_mandanten_fuer_verein() um Mehrfachmandanten zu erfassen.
        # Für Vereinsadmin: nur Trainer des eigenen Vereins; für Superadmin: alle aktiven Trainer
        # im gewählten Verein. benutzer.verein_id ist kein Autorisierungsfeld mehr.
        _alle_benutzer = benutzer_laden()
        if _e_verein_id is not None:
            try:
                _tm_v = trainer_mandanten_fuer_verein(_e_verein_id)
                _tm_bids = {t["benutzer_id"] for t in _tm_v}
            except Exception:
                _tm_bids = None  # Fallback auf Legacy
            if _tm_bids is not None:
                _trainer_pool = [
                    b for b in _alle_benutzer
                    if b.get("rolle") == "Trainer" and b["id"] in _tm_bids
                ]
            else:
                _trainer_pool = [
                    b for b in _alle_benutzer
                    if b.get("rolle") == "Trainer" and b.get("verein_id") == _e_verein_id
                ]
        else:
            _trainer_pool = [b for b in _alle_benutzer if b.get("rolle") == "Trainer"]

        _trainer_opts  = ["— kein Trainer —"] + [
            f"{b['vorname']} {b['nachname']}".strip() for b in _trainer_pool
        ]
        _trainer_ids   = [None] + [b["id"] for b in _trainer_pool]
        _cur_tid       = sp.get("trainer_id")
        _trainer_idx   = _trainer_ids.index(_cur_tid) if _cur_tid in _trainer_ids else 0
        _e_trainer_name = _za2.selectbox("Zuständiger Trainer", _trainer_opts,
                                          index=_trainer_idx, key=f"il_trainer_{_sid}")
        _e_trainer_id  = _trainer_ids[_trainer_opts.index(_e_trainer_name)]

        _new_trainer_id    = _e_trainer_id
        _new_verein_id     = _e_verein_id
        _zuweisung_changed = True

    _ba, _bb = st.columns([3, 1])
    if _ba.button("💾 Speichern", key=f"il_save_{_sid}", type="primary", use_container_width=True):
        if not _e_vn.strip() or not _e_nn.strip():
            st.error("❌ Bitte Vor- und Nachnamen eingeben.")
        else:
            _gok, _gerr = _validate_geburtsdatum(_e_geb)
            if not _gok:
                st.error(f"❌ Ungültiges Geburtsdatum: {_gerr}")
            else:
                _kwargs = {}
                if _zuweisung_changed:
                    _kwargs["trainer_id"] = _new_trainer_id
                    _kwargs["verein_id"]  = _new_verein_id
                spieler_aktualisieren(
                    _sid,
                    _e_vn.strip(), _e_nn.strip(), _e_geb.strip(),
                    _e_gesch, _e_hpos,
                    _e_npos if _e_npos != "—" else "",
                    _e_ak, _e_sb, _e_lvl,
                    _e_mann.strip(), _e_ts,
                    ausfuehrender_id=_akt_user().get("id"),
                    **_kwargs,
                )
                st.session_state.pop("inline_edit_id", None)
                _save_ok(f"**{_e_vn} {_e_nn}** wurde aktualisiert.")
                st.rerun()
    if _bb.button("✖️ Abbrechen", key=f"il_cancel_{_sid}", use_container_width=True):
        st.session_state.pop("inline_edit_id", None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _page_spieler_import():
    """Rendert den bestätigungsbasierten, mandantensicheren Kaderimport."""
    st.markdown("### Kader importieren")
    st.caption(
        "Unterstützt CSV und XLSX. Es werden ausschließlich Spielerstammdaten "
        "übernommen – keine IDs, Rollen, Trainer- oder Vereinszuordnungen aus der Datei."
    )

    user = _akt_user()
    ziel_verein_id = user.get("verein_id")
    ziel_name = user.get("verein_name") or ""
    if user.get("rolle") == "Superadmin":
        _vereine = [v for v in vereine_laden() if v.get("aktiv")]
        if not _vereine:
            st.error("Es ist kein aktiver Mandant für den Import vorhanden.")
            return
        _verein_options = {f"{v.get('name') or 'Unbenannter Verein'}": v for v in _vereine}
        _selected_verein = st.selectbox(
            "Zielmandant",
            list(_verein_options),
            help="Der Zielmandant wird serverseitig geprüft und niemals aus der Datei übernommen.",
            key="spieler_import_superadmin_verein",
        )
        _ziel = _verein_options[_selected_verein]
        ziel_verein_id, ziel_name = _ziel.get("id"), _ziel.get("name") or ""

    if not ziel_verein_id:
        st.warning("Für den Import muss zuerst ein aktiver Mandant ausgewählt werden.")
        return

    st.info(f"🏢 Importziel: **{ziel_name or 'Aktiver Mandant'}**")
    upload = st.file_uploader(
        "CSV- oder Excel-Datei auswählen",
        type=["csv", "xlsx"],
        key="spieler_import_upload",
        help="Maximal 10 MB, 1.000 Datenzeilen und 40 Spalten. Die Originaldatei wird nicht gespeichert.",
    )
    st.download_button(
        "⬇️ CSV-Vorlage herunterladen",
        data=(
            "Vorname;Nachname;Geburtsdatum;Geschlecht;Hauptposition;Mannschaft\n"
            "Max;Mustermann;15.03.2008;Männlich;Zentrales Mittelfeld;U19\n"
        ).encode("utf-8-sig"),
        file_name="spielerimport_vorlage.csv",
        mime="text/csv",
        key="spieler_import_vorlage",
    )
    if upload is None:
        st.info("Lade eine Datei hoch, um die Spalten zuzuordnen und die Vorschau zu prüfen.")
        return

    try:
        upload_bytes = upload.getvalue()
        fingerprint = spieler_import_fingerprint(upload_bytes)
        headers, source_rows = spieler_import_read_upload(upload_bytes, upload.name)
    except ValueError as exc:
        st.error(f"❌ {exc}")
        return

    if st.session_state.get("spieler_import_done_fingerprint") != fingerprint:
        st.session_state.pop("spieler_import_done_result", None)
    elif st.session_state.get("spieler_import_done_result"):
        result = st.session_state["spieler_import_done_result"]
        st.success(
            f"Import abgeschlossen — **{result['angelegt']}** neu angelegt, "
            f"**{result['uebersprungen']}** übersprungen, "
            f"**{result['limit_blockiert']}** wegen Paketlimit nicht angelegt."
        )
        st.caption("Für einen weiteren Import wähle bitte eine andere Datei aus.")
        return

    if not source_rows:
        st.warning("Die Datei enthält keine Datenzeilen.")
        return

    st.markdown("#### 1. Spalten zuordnen")
    st.caption(f"{len(source_rows)} Datenzeilen erkannt. Pflichtfelder sind mit * markiert.")
    automatic_mapping = spieler_import_auto_mapping(headers)
    _no_mapping = "— Nicht übernehmen —"
    _map_columns = st.columns(2)
    mapping: dict[str, str | None] = {}
    for index, (field, label) in enumerate(IMPORT_FIELDS.items()):
        options = [_no_mapping] + headers
        proposed = automatic_mapping.get(field)
        default_index = options.index(proposed) if proposed in options else 0
        selected = _map_columns[index % 2].selectbox(
            label,
            options,
            index=default_index,
            key=f"spieler_import_map_{fingerprint}_{field}",
        )
        mapping[field] = None if selected == _no_mapping else selected

    mapping_errors = spieler_import_validate_mapping(headers, mapping)
    if mapping_errors:
        for error in mapping_errors:
            st.error(f"❌ {error}")
        return

    mapping_signature = f"{fingerprint}|{ziel_verein_id}|{tuple(mapping.items())}"
    existing_keys = spieler_import_dubletten_laden(int(ziel_verein_id))
    if st.session_state.get("spieler_import_signature") != mapping_signature:
        st.session_state["spieler_import_preview"] = spieler_import_build_preview(
            source_rows,
            mapping,
            existing_keys,
            positionen=POSITIONEN,
            leistungsniveaus=LEISTUNGSNIVEAUS,
            trainingsstatus=TRAININGSSTATUS,
        )
        st.session_state["spieler_import_signature"] = mapping_signature
        st.session_state.pop("spieler_import_done_fingerprint", None)
        st.session_state.pop("spieler_import_done_result", None)

    preview = st.session_state.get("spieler_import_preview") or []
    if not preview:
        st.warning("Für diese Zuordnung sind keine Vorschauzeilen vorhanden.")
        return

    st.markdown("#### 2. Vorschau prüfen")
    _filter = st.radio(
        "Status filtern",
        ["Alle", "🟢 Bereit", "🟡 Hinweis", "🔴 Fehler"],
        horizontal=True,
        key=f"spieler_import_filter_{mapping_signature}",
    )
    displayed = [row for row in preview if _filter == "Alle" or row.get("status") == _filter]
    if not displayed:
        st.info("Für diesen Status gibt es keine Zeilen.")
    else:
        editor_columns = [
            "_zeile", "Importieren", "status", "hinweis", "vorname", "nachname",
            "geburtsdatum", "altersklasse", "geschlecht", "hauptposition",
            "nebenposition", "spielbein", "leistungsniveau", "mannschaft",
            "trainingsstatus",
        ]
        editor_df = pd.DataFrame(displayed).reindex(columns=editor_columns)
        edited_df = st.data_editor(
            editor_df,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            key=f"spieler_import_editor_{mapping_signature}",
            disabled=["_zeile", "status", "hinweis", "altersklasse"],
            column_config={
                "_zeile": st.column_config.NumberColumn("Zeile", format="%d"),
                "Importieren": st.column_config.CheckboxColumn("Importieren"),
                "status": st.column_config.TextColumn("Prüfung"),
                "hinweis": st.column_config.TextColumn("Hinweis", width="large"),
                "vorname": st.column_config.TextColumn("Vorname *", required=True),
                "nachname": st.column_config.TextColumn("Nachname *", required=True),
                "geburtsdatum": st.column_config.TextColumn("Geburtsdatum *", help="TT.MM.JJJJ"),
                "altersklasse": st.column_config.TextColumn("Altersklasse (automatisch)"),
                "geschlecht": st.column_config.SelectboxColumn("Geschlecht", options=["Männlich", "Weiblich", "Divers"]),
                "hauptposition": st.column_config.SelectboxColumn("Hauptposition", options=POSITIONEN),
                "nebenposition": st.column_config.SelectboxColumn("Nebenposition", options=[""] + POSITIONEN),
                "spielbein": st.column_config.SelectboxColumn("Spielbein", options=["Rechts", "Links", "Beidfüßig"]),
                "leistungsniveau": st.column_config.SelectboxColumn("Leistungsniveau", options=LEISTUNGSNIVEAUS),
                "mannschaft": st.column_config.TextColumn("Mannschaft"),
                "trainingsstatus": st.column_config.SelectboxColumn("Trainingsstatus", options=TRAININGSSTATUS),
            },
        )
        by_row = {int(row["_zeile"]): dict(row) for row in preview}
        for edited in edited_df.to_dict("records"):
            row_number = int(edited["_zeile"])
            if row_number not in by_row:
                continue
            for field in ("Importieren", *IMPORT_FIELDS):
                if field in edited:
                    by_row[row_number][field] = edited[field]
        preview = spieler_import_revalidate_preview(
            [by_row[int(row["_zeile"])] for row in preview],
            existing_keys,
            positionen=POSITIONEN,
            leistungsniveaus=LEISTUNGSNIVEAUS,
            trainingsstatus=TRAININGSSTATUS,
        )
        st.session_state["spieler_import_preview"] = preview

    _status_counts = {
        "bereit": sum(row.get("status") == "🟢 Bereit" for row in preview),
        "hinweis": sum(row.get("status") == "🟡 Hinweis" for row in preview),
        "fehler": sum(row.get("status") == "🔴 Fehler" for row in preview),
    }
    _metric_cols = st.columns(3)
    _metric_cols[0].metric("Bereit", _status_counts["bereit"])
    _metric_cols[1].metric("Mit Hinweis", _status_counts["hinweis"])
    _metric_cols[2].metric("Fehler", _status_counts["fehler"])

    st.markdown("#### 3. Zeilen gemeinsam bearbeiten")
    _row_numbers = [int(row["_zeile"]) for row in preview]
    _bulk_rows = st.multiselect(
        "Zeilen auswählen",
        _row_numbers,
        format_func=lambda value: f"Zeile {value}",
        key=f"spieler_import_bulk_rows_{mapping_signature}",
    )
    _bulk_c1, _bulk_c2, _bulk_c3, _bulk_c4 = st.columns([2, 2, 2, 1])
    _bulk_mannschaft = _bulk_c1.text_input("Mannschaft setzen", key=f"spieler_import_bulk_team_{mapping_signature}")
    _bulk_geschlecht = _bulk_c2.selectbox(
        "Geschlecht setzen",
        ["Nicht ändern", "Männlich", "Weiblich", "Divers"],
        key=f"spieler_import_bulk_gender_{mapping_signature}",
    )
    _bulk_position = _bulk_c3.selectbox(
        "Hauptposition setzen",
        ["Nicht ändern"] + POSITIONEN,
        key=f"spieler_import_bulk_position_{mapping_signature}",
    )
    if _bulk_c4.button("Übernehmen", key=f"spieler_import_bulk_apply_{mapping_signature}", use_container_width=True):
        if not _bulk_rows:
            st.warning("Bitte zuerst mindestens eine Zeile auswählen.")
        else:
            selected_rows = set(_bulk_rows)
            for row in preview:
                if int(row["_zeile"]) not in selected_rows:
                    continue
                if _bulk_mannschaft.strip():
                    row["mannschaft"] = _bulk_mannschaft.strip()
                if _bulk_geschlecht != "Nicht ändern":
                    row["geschlecht"] = _bulk_geschlecht
                if _bulk_position != "Nicht ändern":
                    row["hauptposition"] = _bulk_position
            st.session_state["spieler_import_preview"] = spieler_import_revalidate_preview(
                preview,
                existing_keys,
                positionen=POSITIONEN,
                leistungsniveaus=LEISTUNGSNIVEAUS,
                trainingsstatus=TRAININGSSTATUS,
            )
            st.rerun()

    _remove_rows = st.multiselect(
        "Einzelne Zeilen aus der Vorschau entfernen",
        _row_numbers,
        format_func=lambda value: f"Zeile {value}",
        key=f"spieler_import_remove_rows_{mapping_signature}",
    )
    if st.button("🗑️ Aus Vorschau entfernen", key=f"spieler_import_remove_{mapping_signature}"):
        if not _remove_rows:
            st.warning("Bitte wähle mindestens eine Zeile aus.")
        else:
            remove_set = set(_remove_rows)
            st.session_state["spieler_import_preview"] = [
                row for row in preview if int(row["_zeile"]) not in remove_set
            ]
            st.rerun()

    st.markdown("#### 4. Import bestätigen")
    capacity = spieler_import_kapazitaet_laden(int(ziel_verein_id))
    _is_duplicate = lambda row: "wird übersprungen" in str(row.get("hinweis", ""))
    _new_rows = [
        row for row in preview
        if row.get("Importieren") and row.get("status") != "🔴 Fehler" and not _is_duplicate(row)
    ]
    if capacity["limit"] is None:
        st.info(f"📦 Paketlimit: unbegrenzt · aktuell {capacity['belegt']} Spieler")
        over_limit = False
    else:
        st.info(
            f"📦 Paketlimit: {capacity['belegt']} von {capacity['limit']} Spielern belegt · "
            f"{capacity['verbleibend']} Plätze frei"
        )
        over_limit = len(_new_rows) > int(capacity["verbleibend"] or 0)
        if over_limit:
            st.error(
                f"Für die ausgewählten neuen Spieler werden {len(_new_rows)} Plätze benötigt, "
                f"aber nur {capacity['verbleibend']} sind frei. Entferne oder deaktiviere Zeilen."
            )

    confirmation = st.checkbox(
        f"Ich bestätige den Import von maximal {len(_new_rows)} neuen Spielern in „{ziel_name or 'den aktiven Mandanten'}“.",
        key=f"spieler_import_confirm_{mapping_signature}",
    )
    candidates = spieler_import_candidates(preview)
    if st.button(
        "✅ Geprüfte Spieler endgültig anlegen",
        type="primary",
        use_container_width=True,
        disabled=not confirmation or not candidates or over_limit,
        key=f"spieler_import_commit_{mapping_signature}",
    ):
        try:
            result = spieler_importieren(
                candidates,
                benutzer_id=user.get("id"),
                rolle=user.get("rolle") or "Trainer",
                verein_id=int(ziel_verein_id),
            )
        except PermissionError:
            st.error("❌ Der Zielmandant ist nicht mehr berechtigt. Bitte wähle den Mandanten neu aus.")
        except ValueError as exc:
            st.error(f"❌ Import wurde nicht durchgeführt: {exc}")
        else:
            st.session_state["spieler_import_done_fingerprint"] = fingerprint
            st.session_state["spieler_import_done_result"] = result
            st.success(
                f"✅ {result['angelegt']} Spieler neu angelegt · "
                f"{result['uebersprungen']} übersprungen · "
                f"{result['limit_blockiert']} wegen Paketlimit nicht angelegt."
            )


def page_spieler():
    st.markdown("# 👤 Spielerverwaltung")
    tab_add, tab_import, tab_list = st.tabs(["➕ Neu anlegen", "📥 Importieren", "📋 Alle Spieler"])

    # ── Tab 1: Neuen Spieler anlegen ──────────────────────────────────────────
    with tab_add:
        st.markdown("### Spieler hinzufügen")

        st.markdown("#### 👤 Persönliche Daten")
        # Zeile 1: Vorname | Nachname  (separate columns-Deklaration → korrekte Reihenfolge auch auf Mobilgeräten)
        _r1c1, _r1c2 = st.columns(2)
        vorname  = _r1c1.text_input("Vorname *",  key="neu_vn")
        nachname = _r1c2.text_input("Nachname *", key="neu_nn")

        # Zeile 2: Geburtsdatum | Geschlecht
        _r2c1, _r2c2 = st.columns(2)
        geburtsdatum = _r2c1.text_input("Geburtsdatum (TT.MM.JJJJ) *",
                                        placeholder="15.03.2008", key="neu_geb")
        geschlecht   = _r2c2.selectbox("Geschlecht", ["Männlich", "Weiblich", "Divers"], key="neu_gesch")

        # Zeile 3: Alter-Anzeige | Altersklasse
        alter        = berechne_alter(geburtsdatum)
        ak_vorschlag = altersklasse_vorschlag(geburtsdatum)
        _r3c1, _r3c2 = st.columns(2)
        if alter:
            _fk_neu = _fki(geburtsdatum)
            _fk_txt = _fk_neu["fussballklasse"] or "?"
            _fk_sl  = _fk_neu["saison"]
            _jk_txt = _jugendklasse(_fk_txt)
            _r3c1.markdown(
                f"<small style='color:#3fb950'>"
                f"Alter: **{alter} Jahre** · Fußballklasse: **{_fk_txt}** (Saison {_fk_sl})"
                f"<br>Jugendklasse: **{_jk_txt}** · Altersklassen-Vorschlag: {ak_vorschlag}</small>",
                unsafe_allow_html=True,
            )
        altersklasse = _r3c2.selectbox("Altersklasse", ALTERSKLASSEN,
                                       index=ALTERSKLASSEN.index(ak_vorschlag) if ak_vorschlag in ALTERSKLASSEN else 7,
                                       key="neu_ak")

        st.markdown("#### 🏟️ Sportliche Daten")
        p1, p2 = st.columns(2)
        hauptposition   = p1.selectbox("Hauptposition *", POSITIONEN,              key="neu_hpos")
        nebenposition   = p2.selectbox("Nebenposition",   ["—"] + POSITIONEN,      key="neu_npos")
        spielbein       = p1.selectbox("Spielbein",       ["Rechts", "Links", "Beidfüßig"], key="neu_sb")
        leistungsniveau = p2.selectbox("Leistungsniveau", LEISTUNGSNIVEAUS,        key="neu_lvl")

        st.markdown("#### 🏃 Teamdaten")
        t1, t2 = st.columns(2)
        mannschaft      = t1.text_input("Mannschaft / Verein", key="neu_mann")
        trainingsstatus = t2.selectbox("Trainingsstatus", TRAININGSSTATUS,         key="neu_ts")

        st.markdown("---")
        _check_save_ok()
        if st.button("💾 Spieler speichern", key="neu_save", type="primary", use_container_width=True):
            if not vorname.strip() or not nachname.strip():
                st.error("❌ Bitte Vor- und Nachnamen eingeben.")
            else:
                _geb_ok, _geb_err = _validate_geburtsdatum(geburtsdatum)
                if not _geb_ok:
                    st.error(f"❌ Ungültiges Geburtsdatum: {_geb_err}")
                else:
                    spieler_speichern(
                        vorname.strip(), nachname.strip(), geburtsdatum.strip(),
                        geschlecht, hauptposition,
                        nebenposition if nebenposition != "—" else "",
                        altersklasse, spielbein, leistungsniveau,
                        mannschaft.strip(), trainingsstatus,
                        trainer_id=_akt_user()["id"],
                        verein_id=_akt_user()["verein_id"],
                    )
                    _save_ok(f"Spieler **{vorname} {nachname}** wurde gespeichert.")
                    st.rerun()

    with tab_import:
        _page_spieler_import()

    # ── Tab 2: Alle Spieler — direkt in der Tabelle bearbeiten ──────────────────
    with tab_list:
        _sp_list = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
        if not _sp_list:
            st.info("Noch keine Spieler vorhanden.")
            return

        # ── Suche & Filter ────────────────────────────────────────────────────
        _sc1, _sc2, _sc3, _sc4 = st.columns([2, 1.5, 1.5, 1.5])
        suche  = _sc1.text_input("🔍 Suchen", placeholder="Name oder Mannschaft …",
                                 key="spieler_suche", label_visibility="collapsed")
        _alle_mann = ["Alle Mannschaften"] + sorted(
            {p.get("mannschaft") or "" for p in _sp_list if p.get("mannschaft")})
        _alle_ak   = ["Alle Klassen"] + ALTERSKLASSEN
        _alle_pos  = ["Alle Positionen"] + POSITIONEN
        f_mann = _sc2.selectbox("Mannschaft",   _alle_mann, key="f_mann", label_visibility="collapsed")
        f_ak   = _sc3.selectbox("Altersklasse", _alle_ak,   key="f_ak",   label_visibility="collapsed")
        f_pos  = _sc4.selectbox("Position",     _alle_pos,  key="f_pos",  label_visibility="collapsed")

        gefiltert = _sp_list
        if suche.strip():
            _s = suche.lower()
            gefiltert = [p for p in gefiltert if
                         _s in p["name"].lower() or
                         _s in (p.get("mannschaft") or "").lower() or
                         _s in (p.get("hauptposition") or p.get("position") or "").lower()]
        if f_mann != "Alle Mannschaften":
            gefiltert = [p for p in gefiltert if p.get("mannschaft") == f_mann]
        if f_ak != "Alle Klassen":
            gefiltert = [p for p in gefiltert if p.get("altersklasse") == f_ak]
        if f_pos != "Alle Positionen":
            gefiltert = [p for p in gefiltert if
                         p.get("hauptposition") == f_pos or p.get("position") == f_pos]

        if not gefiltert:
            st.info("Keine Spieler gefunden.")
        else:
            # ── DataFrame aufbauen ────────────────────────────────────────────
            def _vn(p):
                return p.get("vorname") or (p["name"].split()[0] if p.get("name") else "")
            def _nn(p):
                parts = p["name"].split() if p.get("name") else []
                return p.get("nachname") or (" ".join(parts[1:]) if len(parts) > 1 else "")

            _df_spieler = pd.DataFrame([{
                "_id":             p["id"],
                "Vorname":         _vn(p),
                "Nachname":        _nn(p),
                "Geburtsdatum":    p.get("geburtsdatum") or "",
                "Geschlecht":      p.get("geschlecht") or "Männlich",
                "Hauptposition":   p.get("hauptposition") or p.get("position") or POSITIONEN[0],
                "Nebenposition":   p.get("nebenposition") or "—",
                "Altersklasse":    p.get("altersklasse") or ALTERSKLASSEN[7],
                "Spielbein":       p.get("spielbein") or "Rechts",
                "Leistungsniveau": p.get("leistungsniveau") or LEISTUNGSNIVEAUS[0],
                "Mannschaft":      p.get("mannschaft") or "",
                "Trainingsstatus": p.get("trainingsstatus") or TRAININGSSTATUS[0],
            } for p in gefiltert])

            _edited = st.data_editor(
                _df_spieler,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key="spieler_data_editor",
                column_config={
                    "_id":             None,
                    "Vorname":         st.column_config.TextColumn("Vorname", required=True),
                    "Nachname":        st.column_config.TextColumn("Nachname", required=True),
                    "Geburtsdatum":    st.column_config.TextColumn("Geburtsdatum", help="Format: TT.MM.JJJJ"),
                    "Geschlecht":      st.column_config.SelectboxColumn("Geschlecht",
                                           options=["Männlich", "Weiblich", "Divers"]),
                    "Hauptposition":   st.column_config.SelectboxColumn("Hauptposition",
                                           options=POSITIONEN, required=True),
                    "Nebenposition":   st.column_config.SelectboxColumn("Nebenposition",
                                           options=["—"] + POSITIONEN),
                    "Altersklasse":    st.column_config.SelectboxColumn("Altersklasse",
                                           options=ALTERSKLASSEN, required=True),
                    "Spielbein":       st.column_config.SelectboxColumn("Spielbein",
                                           options=["Rechts", "Links", "Beidfüßig"]),
                    "Leistungsniveau": st.column_config.SelectboxColumn("Leistungsniveau",
                                           options=LEISTUNGSNIVEAUS),
                    "Mannschaft":      st.column_config.TextColumn("Mannschaft"),
                    "Trainingsstatus": st.column_config.SelectboxColumn("Trainingsstatus",
                                           options=TRAININGSSTATUS),
                },
                disabled=["_id"],
            )

            # ── Speichern ─────────────────────────────────────────────────────
            _editor_state = st.session_state.get("spieler_data_editor") or {}
            _edited_rows  = _editor_state.get("edited_rows") or {}
            _n_changes    = len(_edited_rows)

            _sa, _sb = st.columns([4, 1])
            if _n_changes:
                _sa.caption(f"✏️ {_n_changes} Zeile(n) geändert — bitte speichern.")
            else:
                _sa.caption(f"{len(gefiltert)} von {len(_sp_list)} Spieler "
                            "· Zelle anklicken zum Bearbeiten")

            if _sb.button("💾 Speichern", type="primary", use_container_width=True,
                          disabled=(_n_changes == 0), key="spl_save_btn"):
                _saved = 0
                for _ridx in _edited_rows:
                    _row  = _edited.iloc[int(_ridx)]
                    _geb  = str(_row["Geburtsdatum"]).strip() if _row["Geburtsdatum"] else ""
                    _ok, _err = _validate_geburtsdatum(_geb)
                    if not _ok:
                        st.error(f"❌ Zeile {int(_ridx)+1}: {_err}")
                        continue
                    _npos = str(_row["Nebenposition"])
                    spieler_aktualisieren(
                        int(_row["_id"]),
                        str(_row["Vorname"]).strip(),
                        str(_row["Nachname"]).strip(),
                        _geb,
                        str(_row["Geschlecht"]),
                        str(_row["Hauptposition"]),
                        _npos if _npos != "—" else "",
                        str(_row["Altersklasse"]),
                        str(_row["Spielbein"]),
                        str(_row["Leistungsniveau"]),
                        str(_row["Mannschaft"]).strip(),
                        str(_row["Trainingsstatus"]),
                    )
                    _saved += 1
                if _saved:
                    _save_ok(f"{_saved} Spieler aktualisiert.")
                    st.rerun()

        # ── Trainer-Zuweisung (nur Superadmin / Vereinsadmin) ────────────────
        _rolle = _akt_user()["rolle"]
        if _rolle in ("Superadmin", "Vereinsadmin") and gefiltert:
            st.markdown("---")
            with st.expander("🔗 Trainer-Zuweisung ändern"):
                st.caption(
                    "Hier kann der zuständige Trainer und der Verein eines Spielers "
                    "geändert werden, ohne den Spieler neu anlegen zu müssen."
                )

                # Spieler-Auswahl (über ID, nicht Name – eindeutig)
                _za_opts = {f"{p['name']} (ID {p['id']})": p for p in gefiltert}
                _za_key  = st.selectbox(
                    "Spieler auswählen",
                    list(_za_opts.keys()),
                    key="za_spieler_select",
                )
                _za_sp = _za_opts[_za_key]

                # Spieler-ID als Teil aller Widget-Keys → State-Reset bei Spielerwechsel
                _za_sid = _za_sp["id"]
                _va_vid = _akt_user()["verein_id"]

                # Vereine laden
                _za_alle_vereine = vereine_laden()
                if _rolle == "Vereinsadmin":
                    # Vereinsadmin ist auf seinen eigenen Verein beschränkt
                    _za_alle_vereine = [v for v in _za_alle_vereine if v["id"] == _va_vid]

                _za_v_opts = ["— kein Verein —"] + [v["name"] for v in _za_alle_vereine]
                _za_v_ids  = [None] + [v["id"] for v in _za_alle_vereine]
                _za_cur_vid = _za_sp.get("verein_id")
                # Vereinsadmin: Verein auf eigene ID festsetzen (nicht änderbar)
                if _rolle == "Vereinsadmin":
                    _za_verein_idx = _za_v_ids.index(_va_vid) if _va_vid in _za_v_ids else 0
                else:
                    _za_verein_idx = _za_v_ids.index(_za_cur_vid) if _za_cur_vid in _za_v_ids else 0

                _zac1, _zac2 = st.columns(2)
                _za_verein_name = _zac1.selectbox(
                    "Verein",
                    _za_v_opts,
                    index=_za_verein_idx,
                    key=f"za_verein_sel_{_za_sid}",   # spieler-spezifisch!
                    disabled=(_rolle == "Vereinsadmin"),
                )
                _za_sel_vid = _za_v_ids[_za_v_opts.index(_za_verein_name)]

                # Trainer aus dem gewählten Verein — über trainer_mandanten_fuer_verein()
                # damit Mehrfachmandanten-Trainer im zweiten Verein sichtbar sind.
                _za_alle_benutzer = benutzer_laden()
                if _za_sel_vid is not None:
                    try:
                        _za_tm_v = trainer_mandanten_fuer_verein(_za_sel_vid)
                        _za_tm_bids = {t["benutzer_id"] for t in _za_tm_v}
                    except Exception:
                        _za_tm_bids = None
                    if _za_tm_bids is not None:
                        _za_trainer_pool = [
                            b for b in _za_alle_benutzer
                            if b.get("rolle") == "Trainer"
                            and b.get("aktiv", 1)
                            and b["id"] in _za_tm_bids
                        ]
                    else:
                        _za_trainer_pool = [
                            b for b in _za_alle_benutzer
                            if b.get("rolle") == "Trainer"
                            and b.get("aktiv", 1)
                            and b.get("verein_id") == _za_sel_vid
                        ]
                else:
                    _za_trainer_pool  = [
                        b for b in _za_alle_benutzer
                        if b.get("rolle") == "Trainer" and b.get("aktiv", 1)
                    ]
                _za_t_opts = ["— kein Trainer —"] + [
                    f"{b['vorname']} {b['nachname']} (ID {b['id']})".strip()
                    for b in _za_trainer_pool
                ]
                _za_t_ids  = [None] + [b["id"] for b in _za_trainer_pool]
                _za_cur_tid = _za_sp.get("trainer_id")
                _za_trainer_idx = _za_t_ids.index(_za_cur_tid) if _za_cur_tid in _za_t_ids else 0

                _za_trainer_name = _zac2.selectbox(
                    "Zuständiger Trainer",
                    _za_t_opts,
                    index=_za_trainer_idx,
                    key=f"za_trainer_sel_{_za_sid}",  # spieler-spezifisch!
                )
                _za_sel_tid = _za_t_ids[_za_t_opts.index(_za_trainer_name)]

                if st.button("💾 Zuweisung speichern", key="za_save_btn", type="primary"):
                    try:
                        # aufrufender_verein_id → serverseitige Erzwingung für Vereinsadmin
                        spieler_trainer_zuweisen(
                            _za_sid,
                            trainer_id=_za_sel_tid,
                            verein_id=_za_sel_vid,
                            aufrufender_verein_id=_va_vid if _rolle == "Vereinsadmin" else None,
                            ausfuehrender_id=_akt_user().get("id"),
                        )
                        _save_ok(
                            f"**{_za_sp['name']}**: Trainer-Zuweisung wurde aktualisiert."
                        )
                        st.rerun()
                    except ValueError as _za_err:
                        st.error(f"❌ Zuweisung nicht möglich: {_za_err}")

        # ── Spieler löschen ───────────────────────────────────────────────────
        st.markdown("---")
        with st.expander("🗑️ Spieler löschen"):
            namen_lst = [p["name"] for p in gefiltert] if gefiltert else []
            loeschen_auswahl = st.multiselect(
                "Spieler auswählen (Mehrfachauswahl möglich)",
                namen_lst, key="multi_del",
            )
            if loeschen_auswahl:
                n_del = len(loeschen_auswahl)
                st.warning(
                    f"⚠️ {'Dieser Spieler wird' if n_del == 1 else f'Diese {n_del} Spieler werden'} "
                    "zusammen mit allen Testdaten unwiderruflich gelöscht."
                )
                _btn_label = (f"🗑️ {loeschen_auswahl[0]} endgültig löschen"
                              if n_del == 1 else f"🗑️ {n_del} Spieler endgültig löschen")
                if st.button(_btn_label, type="primary", key="multi_del_btn"):
                    ids_loeschen = [p["id"] for p in _sp_list if p["name"] in loeschen_auswahl]
                    for pid in ids_loeschen:
                        spieler_loeschen(pid)
                    if n_del == 1:
                        _save_ok(f"**{loeschen_auswahl[0]}** wurde gelöscht.")
                    else:
                        _save_ok(f"{n_del} Spieler wurden gelöscht.")
                    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────

def _duplikat_check(key_pfx: str, datum_str: str, hist: list) -> str:
    """Prüft ob für diesen Spieler bereits ein Test am gleichen Datum existiert.

    Returns: 'speichern' | 'zweiter' | 'abbrechen'
    """
    if not hist:
        return "speichern"
    existing = any(
        (r.get("datum") if isinstance(r, dict) else (r[0] if r else "")) == datum_str
        for r in hist
    )
    if not existing:
        return "speichern"
    wahl = st.radio(
        "⚠️ Für diesen Spieler existiert bereits ein Test an diesem Datum.",
        ["Bestehenden Test überschreiben", "Als zweiten Test speichern", "Abbrechen"],
        key=f"_dup_{key_pfx}",
        horizontal=True,
    )
    if "zweiten" in wahl:
        return "zweiter"
    if "Abbrechen" in wahl:
        return "abbrechen"
    return "speichern"


# ──────────────────────────────────────────────────────────────────────────────
# GLOBALER ZURÜCK-BUTTON — zentrale Helper-Funktion (§7 des Auftrags)
# ──────────────────────────────────────────────────────────────────────────────

def _back_button(
    label: str,
    target_section: str,
    target_sub_diagnostik: str = "",
    target_sub_spieler: str = "",
    key: str = "back_btn",
) -> None:
    """Rendert ← Zurück-Button mit APH-internem Routing.
    Kein Browser-history.back(). Setzt Session-State-Pending-Keys + rerun().
    Spielerauswahl / Testdaten bleiben erhalten.
    """
    # Mobile-freundliche Darstellung via CSS
    st.markdown(
        '<style>'
        '.aph-back button {'
        '  background:transparent!important;'
        '  border:1px solid #30363d!important;'
        '  color:#8b949e!important;'
        '  font-size:13px!important;'
        '  padding:6px 16px!important;'
        '  border-radius:6px!important;'
        '  margin-bottom:10px!important;'
        '  min-height:38px!important;'
        '  cursor:pointer!important;'
        '}'
        '.aph-back button:hover {'
        '  border-color:#58a6ff!important;'
        '  color:#58a6ff!important;'
        '}'
        '</style>',
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown('<div class="aph-back">', unsafe_allow_html=True)
        if st.button(label, key=key):
            st.session_state["_nav_goto"] = target_section
            if target_sub_diagnostik:
                st.session_state["_nav_sub_diagnostik_goto"] = target_sub_diagnostik
            if target_sub_spieler:
                st.session_state["_nav_sub_spieler_goto"] = target_sub_spieler
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────

def page_fms():
    st.markdown("# 📝 FMS — Functional Movement Screen")
    _back_button("← Zurück zu Tests", "🔬  Diagnostik", target_sub_diagnostik="🏠 Übersicht", key="back_fms")
    st.markdown("Sieben Bewegungsmuster werden bilateral getestet. Maximalpunktzahl: **21 Punkte**.")

    sicherheitshinweis_box()
    show_trainer_checkliste("fms")
    show_test_info("fms")
    _anleitung_download_button("fms")

    auswahl = _player_selector("fms")
    if not auswahl:
        return

    spieler_id = auswahl["id"]
    _fms_sp = spieler_by_id(spieler_id)
    _fms_alter = berechne_alter(_fms_sp.get("geburtsdatum", "") if _fms_sp else None)
    _fms_geschl = _fms_sp.get("geschlecht", "Männlich") if _fms_sp else "Männlich"

    tab_neu, tab_letzter, tab_verlauf = st.tabs(["📋 Neuer Test", "📂 Letzter Test", "📈 Verlauf"])

    # ── Tab 1: Neuer Test ─────────────────────────────────────────────────────
    with tab_neu:
        st.markdown("---")
        st.markdown("### Testergebnisse eingeben")
        st.caption("Bewertung: 3 = korrekt | 2 = mit Kompensation | 1 = nicht möglich | 0 = Schmerzen. ℹ️ Tooltip an jedem Feld für Details.")

        _fh = lambda fid: show_field_help("fms", fid)

        def _fms_row(nr, label, key_l, key_r, fid):
            lbl_col, info_col = st.columns([8, 1])
            lbl_col.markdown(f"**{nr} · {label}**")
            field_info_col(info_col, "fms", fid)
            _cl, _cr = st.columns(2)
            l_val = _cl.number_input("Links",  0, 3, key=key_l, help=_fh(fid))
            r_val = _cr.number_input("Rechts", 0, 3, key=key_r, help=_fh(fid))
            norm_badge(l_val, "fms", fid, _cl)
            norm_badge(r_val, "fms", fid, _cr)
            asym_html = fms_asymmetrie_badge_html(l_val, r_val)
            if asym_html:
                st.markdown(asym_html, unsafe_allow_html=True)
            return l_val, r_val

        ds_lbl, ds_info = st.columns([8, 1])
        ds_lbl.markdown("**1 · Deep Squat** — ein Score (kein L/R)")
        field_info_col(ds_info, "fms", "deep_squat")
        _c1, _gap = st.columns([2, 4])
        deep = _c1.number_input("Punkte", 0, 3, key="ds", help=_fh("deep_squat"))
        norm_badge(deep, "fms", "deep_squat", _c1)

        st.markdown("---")
        st.markdown("*Bilateral: niedrigerer Seitenwert zählt für den Gesamtscore*")
        hurdle_l, hurdle_r     = _fms_row(2, "Hurdle Step",       "hl",  "hr",  "hurdle_step")
        inline_l, inline_r     = _fms_row(3, "Inline Lunge",      "il",  "ir",  "inline_lunge")
        shoulder_l, shoulder_r = _fms_row(4, "Shoulder Mobility", "shl", "shr", "shoulder")
        aslr_l, aslr_r         = _fms_row(5, "ASLR",              "al",  "ar",  "aslr")

        st.markdown("---")
        ts_lbl, ts_info = st.columns([8, 1])
        ts_lbl.markdown("**6 · Trunk Stability Push-up** — ein Score (kein L/R)")
        field_info_col(ts_info, "fms", "trunk_stability")
        _c6, _gap6 = st.columns([2, 4])
        trunk = _c6.number_input("Punkte", 0, 3, key="ts", help=_fh("trunk_stability"))
        norm_badge(trunk, "fms", "trunk_stability", _c6)

        st.markdown("---")
        st.markdown("*Bilateral: niedrigerer Seitenwert zählt für den Gesamtscore*")
        rotary_l, rotary_r     = _fms_row(7, "Rotary Stability",  "rl",  "rr",  "rotary_stability")

        st.markdown("---")
        obs_fms = render_observation_selector("fms", spieler_id, date.today().strftime("%d.%m.%Y"), "fms", standalone=False)
        _dup_fms = _duplikat_check("fms", str(date.today()), fms_history(spieler_id))

        if st.button("✅ FMS speichern & auswerten", use_container_width=True, type="primary"):
            if _dup_fms == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            import json as _j, datetime as _dtm
            _datum_fms = str(date.today())
            if _dup_fms == "zweiter":
                _datum_fms += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
            result = FMSResult(
                deep_squat=deep, hurdle_l=hurdle_l, hurdle_r=hurdle_r,
                inline_l=inline_l, inline_r=inline_r,
                shoulder_l=shoulder_l, shoulder_r=shoulder_r,
                aslr_l=aslr_l, aslr_r=aslr_r, trunk=trunk,
                rotary_l=rotary_l, rotary_r=rotary_r,
                alter=_fms_alter,
            )
            fms_speichern(
                spieler_id, _datum_fms,
                deep, hurdle_l, hurdle_r, inline_l, inline_r,
                shoulder_l, shoulder_r, aslr_l, aslr_r, trunk, rotary_l, rotary_r,
                result.score, result.bewertung, result.asymmetrie, result.schwerpunkt,
            )
            if obs_fms["beob_ids"] or obs_fms.get("freitext"):
                beobachtung_speichern(
                    spieler_id, "fms", _datum_fms,
                    _j.dumps(obs_fms["beob_ids"], ensure_ascii=False),
                    obs_fms["seite"], obs_fms["auspraegung"],
                    obs_fms["freitext"], obs_fms["text_generiert"],
                )
            _save_ok("FMS Test gespeichert!")
            _reset_keys("ds", "ts", "hl", "hr", "il", "ir", "shl", "shr", "al", "ar", "rl", "rr")
            st.markdown("---")
            st.markdown("### Ergebnis")
            m1, m2, m3 = st.columns(3)
            m1.metric("Gesamtscore", f"{result.score} / 21")
            m2.metric("Bewertung", result.bewertung)
            m3.metric("Risikostufe", result.risiko_level.capitalize())
            st.caption(f"📊 {_tcap(_fms_alter, _fms_sp.get('geburtsdatum', '') if _fms_sp else '')}")
            # ── Kurze Beurteilung ──────────────────────────────────────
            from fms import fms_bewertung_kurz as _fms_bkurz
            _fms_bw_clr = {"Ausgezeichnet": "#3fb950", "Gut": "#3fb950",
                           "Beobachten": "#d29922", "Aktionsbedarf": "#f85149"}
            _fms_bc = _fms_bw_clr.get(result.bewertung, "#8b949e")
            st.markdown(
                f'<div style="background:#161b22;border-left:4px solid {_fms_bc};'
                f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0">'
                f'<span style="color:{_fms_bc};font-weight:700">{result.bewertung}</span>'
                f'<span style="color:#8b949e;font-size:12px;margin-left:10px">{result.score}/21 Punkte</span><br>'
                f'<small style="color:#c9d1d9">{_fms_bkurz(result.score)}</small></div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### Pattern-Scores")
            for name, val in result.pattern_scores.items():
                col = _color_for_score(val, 3)
                st.markdown(f"**{name}** — {val}/3 {_progress_html(val, 3, col)}", unsafe_allow_html=True)
            st.info(f"**Trainingsschwerpunkt:** {result.schwerpunkt}")
            if result.asymmetrie != "Keine Asymmetrie":
                st.warning(f"⚠️ {result.asymmetrie}")

    # ── Tab 2: Letzter Test — alle 13 Einzelbewertungen ──────────────────────
    with tab_letzter:
        last = fms_letzter(spieler_id)
        if not last:
            st.info("Noch kein FMS-Test gespeichert.")
        else:
            lm1, lm2, lm3 = st.columns(3)
            lm1.metric("Gesamtscore", f"{last.get('score', 0)} / 21")
            lm2.metric("Bewertung",   last.get("bewertung", "—"))
            lm3.metric("Datum",       last.get("datum", "—"))
            # ── Kurze Beurteilung ──────────────────────────────────────────────
            from fms import fms_bewertung_kurz as _fms_bkurz2
            _fms_bw_clr2 = {"Ausgezeichnet": "#3fb950", "Gut": "#3fb950",
                             "Beobachten": "#d29922", "Aktionsbedarf": "#f85149"}
            _fms_bc2 = _fms_bw_clr2.get(last.get("bewertung", ""), "#8b949e")
            st.markdown(
                f'<div style="background:#161b22;border-left:4px solid {_fms_bc2};'
                f'border-radius:0 8px 8px 0;padding:10px 16px;margin:8px 0">'
                f'<span style="color:{_fms_bc2};font-weight:700">{last.get("bewertung","—")}</span>'
                f'<span style="color:#8b949e;font-size:12px;margin-left:10px">{last.get("score",0)}/21 Punkte</span><br>'
                f'<small style="color:#c9d1d9">{_fms_bkurz2(last.get("score"))}</small></div>',
                unsafe_allow_html=True,
            )
            st.markdown("---")
            st.markdown("#### Einzelbewertungen")
            _SC = {3: "#3fb950", 2: "#d29922", 1: "#f0883e", 0: "#f85149"}
            _FMS_EINZEL = [
                ("1 · Deep Squat",          last.get("deep_squat"),    None),
                ("2 · Hurdle Step",          last.get("hurdle_links"),  last.get("hurdle_rechts")),
                ("3 · Inline Lunge",         last.get("inline_links"),  last.get("inline_rechts")),
                ("4 · Shoulder Mobility",    last.get("shoulder_links"),last.get("shoulder_rechts")),
                ("5 · ASLR",                 last.get("aslr_links"),    last.get("aslr_rechts")),
                ("6 · Trunk Stability",      last.get("trunk"),         None),
                ("7 · Rotary Stability",     last.get("rotary_links"),  last.get("rotary_rechts")),
            ]
            for tname, lv, rv in _FMS_EINZEL:
                ca, cb, cc, cd = st.columns([3, 1, 1, 1])
                ca.markdown(f"**{tname}**")
                if rv is None:
                    v = int(lv or 0)
                    cb.markdown(f'<span style="color:{_SC.get(v,"#8b949e")};font-weight:700;font-size:1.15em">{v}</span> / 3', unsafe_allow_html=True)
                else:
                    lval = int(lv or 0); rval = int(rv or 0)
                    cb.markdown(f'L: <span style="color:{_SC.get(lval,"#8b949e")};font-weight:700">{lval}</span>/3', unsafe_allow_html=True)
                    cc.markdown(f'R: <span style="color:{_SC.get(rval,"#8b949e")};font-weight:700">{rval}</span>/3', unsafe_allow_html=True)
                    if lval != rval:
                        cd.markdown("⚠️ Asymm.")
            st.markdown("---")
            st.write("**Asymmetrie:**", last.get("asymmetrie") or "—")
            st.write("**Trainingsschwerpunkt:**", last.get("schwerpunkt") or "—")

    # ── Tab 3: Verlauf ────────────────────────────────────────────────────────
    with tab_verlauf:
        hist_full = fms_history_full(spieler_id)
        if not hist_full:
            st.info("Noch keine FMS-Tests vorhanden.")
        else:
            df_fms = pd.DataFrame([{
                "Datum":       r["datum"],
                "Deep Squat":  int(r.get("deep_squat") or 0),
                "Hurdle L":    int(r.get("hurdle_links") or 0),
                "Hurdle R":    int(r.get("hurdle_rechts") or 0),
                "Inline L":    int(r.get("inline_links") or 0),
                "Inline R":    int(r.get("inline_rechts") or 0),
                "Shoulder L":  int(r.get("shoulder_links") or 0),
                "Shoulder R":  int(r.get("shoulder_rechts") or 0),
                "ASLR L":      int(r.get("aslr_links") or 0),
                "ASLR R":      int(r.get("aslr_rechts") or 0),
                "Trunk":       int(r.get("trunk") or 0),
                "Rotary L":    int(r.get("rotary_links") or 0),
                "Rotary R":    int(r.get("rotary_rechts") or 0),
                "Gesamtscore": int(r.get("score") or 0),
                "Bewertung":   r.get("bewertung") or "—",
            } for r in hist_full])

            # ── Persönliche Bestleistung ─────────────────────────────────────
            _pb_trend_cards(df_fms, [
                ("Gesamtscore", "FMS Gesamtscore", "Punkte", False),
            ])

            # Gesamtscore-Kurve
            fig_score = go.Figure()
            fig_score.add_trace(go.Scatter(
                x=df_fms["Datum"], y=df_fms["Gesamtscore"],
                mode="lines+markers+text", text=df_fms["Gesamtscore"],
                textposition="top center",
                line=dict(color="#3b82f6", width=3), marker=dict(size=9),
            ))
            fig_score.add_hline(y=14, line_dash="dash", line_color="#d29922",
                                annotation_text="Schwellenwert 14")
            fig_score.update_layout(**_pl(height=280, title="FMS Gesamtscore",
                                          yaxis=dict(range=[0, 22], title="Score (0–21)")))
            st.plotly_chart(fig_score, use_container_width=True)

            # Einzelwerte-Verlauf
            with st.expander("📊 Einzelwerte-Verlauf anzeigen"):
                _ecolors = ["#3b82f6","#3fb950","#56d364","#d29922","#e3b341",
                            "#f85149","#ff7b72","#58a6ff","#79c0ff","#a371f7","#f0883e","#ffa657"]
                _ecols   = ["Deep Squat","Hurdle L","Hurdle R","Inline L","Inline R",
                            "Shoulder L","Shoulder R","ASLR L","ASLR R","Trunk","Rotary L","Rotary R"]
                fig_e = go.Figure()
                for col_n, clr in zip(_ecols, _ecolors):
                    fig_e.add_trace(go.Scatter(
                        x=df_fms["Datum"], y=df_fms[col_n],
                        mode="lines+markers", name=col_n,
                        line=dict(color=clr, width=2),
                    ))
                fig_e.update_layout(**_pl(height=350, title="FMS Einzelbewertungen"))
                st.plotly_chart(fig_e, use_container_width=True)

            # Zwei Testtermine vergleichen
            daten = df_fms["Datum"].tolist()
            if len(daten) >= 2:
                with st.expander("⚖️ Zwei Testtermine vergleichen"):
                    vc1, vc2 = st.columns(2)
                    d_alt = vc1.selectbox("Älterer Termin", daten, index=0, key="fms_vgl_alt")
                    d_neu = vc2.selectbox("Neuerer Termin", daten, index=len(daten)-1, key="fms_vgl_neu")
                    if d_alt != d_neu:
                        r_alt = df_fms[df_fms["Datum"] == d_alt].iloc[0]
                        r_neu = df_fms[df_fms["Datum"] == d_neu].iloc[0]
                        _vcols = ["Deep Squat","Hurdle L","Hurdle R","Inline L","Inline R",
                                  "Shoulder L","Shoulder R","ASLR L","ASLR R","Trunk","Rotary L","Rotary R","Gesamtscore"]
                        vgl_rows = []
                        for c in _vcols:
                            v1 = int(r_alt[c]); v2 = int(r_neu[c]); delta = v2 - v1
                            vgl_rows.append({"Merkmal": c, d_alt: v1, d_neu: v2,
                                             "Δ": f"+{delta}" if delta > 0 else str(delta)})
                        st.dataframe(pd.DataFrame(vgl_rows), use_container_width=True, hide_index=True)
                    else:
                        st.info("Bitte zwei verschiedene Testtermine auswählen.")

            # Volltabelle
            st.markdown("---")
            st.markdown("##### Alle Tests")
            show_cols = ["Datum","Deep Squat","Hurdle L","Hurdle R","Inline L","Inline R",
                         "Shoulder L","Shoulder R","ASLR L","ASLR R","Trunk","Rotary L","Rotary R","Gesamtscore","Bewertung"]
            _df_fms_show = _datum_filter(df_fms[show_cols].copy(), "fms_voll")
            st.dataframe(
                _df_fms_show,
                use_container_width=True, hide_index=True,
                column_config={
                    "Gesamtscore": st.column_config.NumberColumn("Gesamtscore", format="%d / 21"),
                    **{c: st.column_config.NumberColumn(c, format="%d") for c in
                       ["Deep Squat","Hurdle L","Hurdle R","Inline L","Inline R",
                        "Shoulder L","Shoulder R","ASLR L","ASLR R","Trunk","Rotary L","Rotary R"]},
                },
            )
            # ── Bearbeiten / Löschen ──────────────────────────────────────────
            st.markdown("---")
            with st.expander("✏️ Eintrag bearbeiten / löschen"):
                _render_fms_edit(spieler_id)


# ──────────────────────────────────────────────────────────────────────────────

def page_ybalance():
    st.markdown("# 📏 Y-Balance Test")
    _back_button("← Zurück zu Tests", "🔬  Diagnostik", target_sub_diagnostik="🏠 Übersicht", key="back_yb")
    st.markdown("Composite Score = (A + PM + PL) / (3 × Beinlänge) × 100.  Schwellenwert: **≥ 89 %**.")

    sicherheitshinweis_box()
    show_trainer_checkliste("y_balance")
    show_test_info("y_balance")
    _anleitung_download_button("y_balance")

    auswahl = _player_selector("yb")
    if not auswahl:
        return

    spieler_id = auswahl["id"]
    _yb_sp = spieler_by_id(spieler_id)
    _yb_alter = berechne_alter(_yb_sp.get("geburtsdatum", "") if _yb_sp else None)
    _yb_geschl = _yb_sp.get("geschlecht", "Männlich") if _yb_sp else "Männlich"

    tab_neu, tab_letzter, tab_verlauf = st.tabs(["📋 Neuer Test", "📂 Letzter Test", "📈 Verlauf"])

    # ── Tab 1: Neuer Test ─────────────────────────────────────────────────────
    with tab_neu:
        st.markdown("---")
        _fh = lambda fid: show_field_help("y_balance", fid)
        col1, col2 = st.columns(2)
        br_h, br_i = col1.columns([5, 1]); br_h.markdown("**Beinlänge Rechts (cm) \\***"); field_info_col(br_i, "y_balance", "beinlaenge")
        bein_r = col1.number_input("Beinlänge Rechts (cm) *", min_value=1.0, value=90.0, step=0.5,
                                    label_visibility="collapsed", help=_fh("beinlaenge"))
        bl_h, bl_i = col2.columns([5, 1]); bl_h.markdown("**Beinlänge Links (cm) \\***"); field_info_col(bl_i, "y_balance", "beinlaenge")
        bein_l = col2.number_input("Beinlänge Links (cm) *",  min_value=1.0, value=90.0, step=0.5,
                                    label_visibility="collapsed", help=_fh("beinlaenge"))

        st.markdown("#### Reichweiten (cm)")
        ch1, ch2 = st.columns(2)
        ch1.markdown("**Rechte Seite**")
        ch2.markdown("**Linke Seite**")
        ar_h, ar_i = ch1.columns([5, 1]); ar_h.markdown("**Anterior R (cm)**"); field_info_col(ar_i, "y_balance", "anterior")
        ant_r  = ch1.number_input("Anterior R",       0.0, 200.0, 0.0, step=0.5, key="antr", label_visibility="collapsed", help=_fh("anterior"))
        al_h, al_i = ch2.columns([5, 1]); al_h.markdown("**Anterior L (cm)**"); field_info_col(al_i, "y_balance", "anterior")
        ant_l  = ch2.number_input("Anterior L",       0.0, 200.0, 0.0, step=0.5, key="antl", label_visibility="collapsed", help=_fh("anterior"))
        pmr_h, pmr_i = ch1.columns([5, 1]); pmr_h.markdown("**Posteromedial R (cm)**"); field_info_col(pmr_i, "y_balance", "posteromedial")
        pm_r   = ch1.number_input("Posteromedial R",  0.0, 200.0, 0.0, step=0.5, key="pmr",  label_visibility="collapsed", help=_fh("posteromedial"))
        pml_h, pml_i = ch2.columns([5, 1]); pml_h.markdown("**Posteromedial L (cm)**"); field_info_col(pml_i, "y_balance", "posteromedial")
        pm_l   = ch2.number_input("Posteromedial L",  0.0, 200.0, 0.0, step=0.5, key="pml",  label_visibility="collapsed", help=_fh("posteromedial"))
        plr_h, plr_i = ch1.columns([5, 1]); plr_h.markdown("**Posterolateral R (cm)**"); field_info_col(plr_i, "y_balance", "posterolateral")
        pl_r   = ch1.number_input("Posterolateral R", 0.0, 200.0, 0.0, step=0.5, key="plr",  label_visibility="collapsed", help=_fh("posterolateral"))
        pll_h, pll_i = ch2.columns([5, 1]); pll_h.markdown("**Posterolateral L (cm)**"); field_info_col(pll_i, "y_balance", "posterolateral")
        pl_l   = ch2.number_input("Posterolateral L", 0.0, 200.0, 0.0, step=0.5, key="pll",  label_visibility="collapsed", help=_fh("posterolateral"))

        st.markdown("---")
        obs_yb = render_observation_selector("y_balance", spieler_id, date.today().strftime("%d.%m.%Y"), "yb", standalone=False)
        _dup_yb = _duplikat_check("yb", str(date.today()), y_balance_history(spieler_id))

        _yb_warns = []
        if bein_r > 0:
            for _val, _lbl in [(ant_r, "Anterior R"), (pm_r, "Posteromedial R"), (pl_r, "Posterolateral R")]:
                if _val > bein_r * 1.3:
                    _yb_warns.append(f"{_lbl} ({_val:.1f} cm > 130 % Beinlänge R)")
        if bein_l > 0:
            for _val, _lbl in [(ant_l, "Anterior L"), (pm_l, "Posteromedial L"), (pl_l, "Posterolateral L")]:
                if _val > bein_l * 1.3:
                    _yb_warns.append(f"{_lbl} ({_val:.1f} cm > 130 % Beinlänge L)")
        if bein_r > 0 and bein_l > 0 and abs(bein_r - bein_l) > 5:
            _yb_warns.append(f"Beinlängendifferenz R/L: {abs(bein_r - bein_l):.1f} cm — bitte prüfen")
        if _yb_warns:
            st.warning("⚠️ Ungewöhnliche Werte — bitte Eingaben prüfen (Speichern trotzdem möglich):\n"
                       + "\n".join(f"• {w}" for w in _yb_warns))

        if st.button("💾 Y-Balance berechnen & speichern", type="primary", use_container_width=True):
            if _dup_yb == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            import json as _j, datetime as _dtm
            _datum_yb = str(date.today())
            if _dup_yb == "zweiter":
                _datum_yb += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
            res = YBalanceResult(
                anterior_r=ant_r, anterior_l=ant_l,
                posteromedial_r=pm_r, posteromedial_l=pm_l,
                posterolateral_r=pl_r, posterolateral_l=pl_l,
                beinlaenge_r=bein_r, beinlaenge_l=bein_l,
                alter=_yb_alter,
            )
            y_balance_speichern(
                spieler_id, _datum_yb,
                ant_r, ant_l, pm_r, pm_l, pl_r, pl_l,
                res.diff_anterior, res.diff_posteromedial, res.diff_posterolateral,
                res.composite_r, res.composite_l,
                res.asymmetrie_text, res.schwerpunkt,
            )
            if obs_yb["beob_ids"] or obs_yb.get("freitext"):
                beobachtung_speichern(
                    spieler_id, "y_balance", _datum_yb,
                    _j.dumps(obs_yb["beob_ids"], ensure_ascii=False),
                    obs_yb["seite"], obs_yb["auspraegung"],
                    obs_yb["freitext"], obs_yb["text_generiert"],
                )
            _save_ok(f"Y-Balance Test gespeichert! — Composite R: {res.composite_r} % | L: {res.composite_l} %")
            _reset_keys("antr", "antl", "pmr", "pml", "plr", "pll")
            st.rerun()

    # ── Tab 2: Letzter Test — alle Einzelwerte ───────────────────────────────
    with tab_letzter:
        last = y_balance_letzter(spieler_id)
        if not last:
            st.info("Noch kein Y-Balance-Test gespeichert.")
        else:
            lm1, lm2, lm3 = st.columns(3)
            lm1.metric("Composite Rechts", f"{last.get('composite_rechts','—')} %")
            lm2.metric("Composite Links",  f"{last.get('composite_links','—')} %")
            lm3.metric("Datum", last.get("datum","—"))
            st.markdown("---")
            st.markdown("#### Reichweiten")
            rc1, rc2 = st.columns(2)
            rc1.markdown("**Rechts**")
            rc2.markdown("**Links**")
            for _lbl, _rk, _lk in [
                ("Anterior",      "anterior_rechts",      "anterior_links"),
                ("Posteromedial", "posteromedial_rechts", "posteromedial_links"),
                ("Posterolateral","posterolateral_rechts","posterolateral_links"),
            ]:
                rc1.markdown(f"**{_lbl}:** {last.get(_rk,'—')} cm")
                rc2.markdown(f"**{_lbl}:** {last.get(_lk,'—')} cm")
            st.markdown("---")
            st.markdown("#### Seitendifferenzen")
            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Δ Anterior",      f"{last.get('diff_anterior','—')} cm")
            dc2.metric("Δ Posteromedial", f"{last.get('diff_posteromedial','—')} cm")
            dc3.metric("Δ Posterolateral",f"{last.get('diff_posterolateral','—')} cm")
            st.markdown("---")
            st.write("**Asymmetrie:**",          last.get("asymmetrie") or "—")
            st.write("**Trainingsschwerpunkt:**", last.get("schwerpunkt") or "—")

    # ── Tab 3: Verlauf ────────────────────────────────────────────────────────
    with tab_verlauf:
        hist_yb = y_balance_history_full(spieler_id)
        if not hist_yb:
            st.info("Noch keine Y-Balance-Tests vorhanden.")
        else:
            df_yb = pd.DataFrame([{
                "Datum":           r["datum"],
                "Composite R (%)": round(float(r.get("composite_rechts") or 0), 1),
                "Composite L (%)": round(float(r.get("composite_links")  or 0), 1),
                "Ant R":           float(r.get("anterior_rechts")       or 0),
                "Ant L":           float(r.get("anterior_links")        or 0),
                "PM R":            float(r.get("posteromedial_rechts")  or 0),
                "PM L":            float(r.get("posteromedial_links")   or 0),
                "PL R":            float(r.get("posterolateral_rechts") or 0),
                "PL L":            float(r.get("posterolateral_links")  or 0),
                "Asymmetrie":      r.get("asymmetrie") or "—",
                "Schwerpunkt":     r.get("schwerpunkt") or "—",
            } for r in hist_yb])

            # ── Persönliche Bestleistung ─────────────────────────────────────
            _pb_trend_cards(df_yb, [
                ("Composite R (%)", "Composite Rechts", "%", False),
                ("Composite L (%)", "Composite Links",  "%", False),
            ])

            # Composite-Score-Kurve
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(x=df_yb["Datum"], y=df_yb["Composite R (%)"],
                mode="lines+markers", name="Composite Rechts", line=dict(color="#3b82f6", width=3)))
            fig_comp.add_trace(go.Scatter(x=df_yb["Datum"], y=df_yb["Composite L (%)"],
                mode="lines+markers", name="Composite Links",  line=dict(color="#f85149", width=3)))
            fig_comp.add_hline(y=89, line_dash="dash", line_color="#d29922",
                               annotation_text="Schwellenwert 89 %")
            fig_comp.update_layout(**_pl(height=280, title="Y-Balance Composite Scores",
                                         yaxis=dict(title="Composite Score (%)")))
            st.plotly_chart(fig_comp, use_container_width=True)

            # Einzelrichtungen
            with st.expander("📊 Einzelrichtungen-Verlauf anzeigen"):
                fig_dir = go.Figure()
                for col_n, clr in [
                    ("Ant R","#3b82f6"),("Ant L","#79c0ff"),
                    ("PM R","#3fb950"),("PM L","#56d364"),
                    ("PL R","#f85149"),("PL L","#ffa657"),
                ]:
                    fig_dir.add_trace(go.Scatter(x=df_yb["Datum"], y=df_yb[col_n],
                        mode="lines+markers", name=col_n, line=dict(color=clr, width=2)))
                fig_dir.update_layout(**_pl(height=320, title="Reichweiten pro Richtung (cm)",
                                             yaxis=dict(title="Reichweite (cm)")))
                st.plotly_chart(fig_dir, use_container_width=True)

            # Asymmetrie-Verlauf über Zeit
            _asym_num = pd.to_numeric(df_yb["Asymmetrie"], errors="coerce")
            _asym_df  = df_yb[_asym_num > 0].copy()
            if not _asym_df.empty:
                _asym_vals = pd.to_numeric(_asym_df["Asymmetrie"], errors="coerce")
                fig_asym = go.Figure()
                fig_asym.add_trace(go.Bar(
                    x=_asym_df["Datum"], y=_asym_vals,
                    marker_color=["#f85149" if v > 10 else "#3fb950" for v in _asym_vals],
                    text=_asym_vals.round(1), textposition="outside",
                ))
                fig_asym.add_hline(y=10, line_dash="dash", line_color="#d29922",
                                   annotation_text="Grenzwert 10 %")
                fig_asym.update_layout(**_pl(height=240,
                                             title="Y-Balance Asymmetrie Rechts vs. Links (%)",
                                             yaxis=dict(title="Asymmetrie (%)")))
                st.plotly_chart(fig_asym, use_container_width=True)

            # Zwei Testtermine vergleichen
            daten_yb = df_yb["Datum"].tolist()
            if len(daten_yb) >= 2:
                with st.expander("⚖️ Zwei Testtermine vergleichen"):
                    yvc1, yvc2 = st.columns(2)
                    yd_alt = yvc1.selectbox("Älterer Termin", daten_yb, index=0, key="yb_vgl_alt")
                    yd_neu = yvc2.selectbox("Neuerer Termin", daten_yb, index=len(daten_yb)-1, key="yb_vgl_neu")
                    if yd_alt != yd_neu:
                        yr_alt = df_yb[df_yb["Datum"] == yd_alt].iloc[0]
                        yr_neu = df_yb[df_yb["Datum"] == yd_neu].iloc[0]
                        _yvcols = ["Composite R (%)","Composite L (%)","Ant R","Ant L","PM R","PM L","PL R","PL L"]
                        yvgl = []
                        for c in _yvcols:
                            v1 = yr_alt[c]; v2 = yr_neu[c]; d = round(v2-v1, 1)
                            yvgl.append({"Merkmal":c, yd_alt: v1, yd_neu: v2, "Δ": f"+{d}" if d > 0 else str(d)})
                        st.dataframe(pd.DataFrame(yvgl), use_container_width=True, hide_index=True)
                    else:
                        st.info("Bitte zwei verschiedene Testtermine auswählen.")

            # Volltabelle
            st.markdown("---")
            st.markdown("##### Alle Tests")
            _df_yb_show = df_yb[["Datum","Composite R (%)","Composite L (%)","Ant R","Ant L",
                                   "PM R","PM L","PL R","PL L","Asymmetrie","Schwerpunkt"]].copy()
            _df_yb_show = _datum_filter(_df_yb_show, "yb_voll")
            st.dataframe(
                _df_yb_show,
                use_container_width=True, hide_index=True,
                column_config={
                    "Composite R (%)": st.column_config.NumberColumn("Composite R (%)", format="%.1f %%"),
                    "Composite L (%)": st.column_config.NumberColumn("Composite L (%)", format="%.1f %%"),
                    "Asymmetrie":      st.column_config.NumberColumn("Asymmetrie", format="%.1f %%"),
                    **{c: st.column_config.NumberColumn(c, format="%.1f cm")
                       for c in ["Ant R","Ant L","PM R","PM L","PL R","PL L"]},
                },
            )
            # ── Bearbeiten / Löschen ──────────────────────────────────────────
            st.markdown("---")
            with st.expander("✏️ Eintrag bearbeiten / löschen"):
                _render_ybalance_edit(spieler_id)


# ──────────────────────────────────────────────────────────────────────────────

def page_spieler_profil():
    st.markdown("# 🏃 Spielerprofil & Diagnostik")
    _back_button("← Zurück zur Spielerübersicht", "👤  Spieler",
                 target_sub_spieler="👥 Verwaltung", key="back_profil")

    auswahl = _player_selector("profil")
    if not auswahl:
        return

    sid    = auswahl["id"]
    fms    = fms_letzter(sid)
    y      = y_balance_letzter(sid)
    sprint = sprint_letzter(sid)
    sprung = sprung_letzter(sid)
    agil   = agilitaet_letzter(sid)
    aus    = ausdauer_letzter(sid)
    kraft  = kraft_letzter(sid)
    anthro      = anthropometrie_letzter(sid)
    anthro_hist = anthropometrie_history(sid)
    verlet = verletzungen_laden(sid)
    rs     = risiko_score(fms, y, verlet)
    label, level = risiko_label(rs)
    _spiro_p = spiro_test_letzter(sid)
    ascore   = athletik_score(fms, y, sprint, sprung, agil, aus, spiro_row=_spiro_p)
    defizite = defizite_ermitteln(fms, y, sprint, sprung, agil, aus, anthro, kraft_row=kraft, spiro_row=_spiro_p,
                                  geschlecht=auswahl.get("geschlecht", "Männlich"))
    schwerpunkt = schwerpunkt_sammeln(fms, y, sprint, sprung, agil, aus,
                                      kraft_row=kraft_letzter(sid), spiro_row=_spiro_p)
    alter = berechne_alter(auswahl.get("geburtsdatum"))

    # ── Header ────────────────────────────────────────────────────────────
    h1, h2, h3 = st.columns([2, 1, 1])
    with h1:
        st.markdown(f"## {auswahl['name']}")
        haupt = auswahl.get("hauptposition") or auswahl.get("position") or "—"
        neben = auswahl.get("nebenposition") or ""
        pos_str = f"{haupt}" + (f" / {neben}" if neben else "")
        info_zeile = (
            f"🎂 {alter} Jahre  ·  "
            f"⚽ {pos_str}  ·  "
            f"🏟️ {auswahl.get('mannschaft') or '—'}  ·  "
            f"🦵 Spielbein: {auswahl.get('spielbein') or '—'}"
        )
        st.markdown(f"<small style='color:#8b949e'>{info_zeile}</small>", unsafe_allow_html=True)
        # ── Fußballklasse (dynamisch berechnet — jahrgangsbasiert) ─────────────
        _fk_info = _fki(auswahl.get("geburtsdatum", ""))
        _fk_str  = _fk_info["fussballklasse"] or "—"
        _jg_str  = str(_fk_info["jahrgang"]) if _fk_info["jahrgang"] else "—"
        _sl_str  = _fk_info["saison"]
        _tref_str = f"Testreferenz: {__import__('age_norms').alter_zu_normgruppe(alter)}" if alter else "—"
        st.markdown(
            f"<small style='color:#58a6ff'>"
            f"⚽ Fußballklasse: <b>{_fk_str}</b>  ·  "
            f"Jahrgang: {_jg_str}  ·  Saison: {_sl_str}  ·  {_tref_str}"
            f"</small>",
            unsafe_allow_html=True,
        )
        niv = auswahl.get("leistungsniveau") or "—"
        status = auswahl.get("trainingsstatus") or "Volltraining"
        status_color = (
            "#f85149" if any(x in status.lower() for x in ["pause", "abklärung", "abklaerung"])
            else "#d29922" if any(x in status.lower() for x in ["angepasst", "individuell", "freigabe"])
            else "#3fb950"
        )
        st.markdown(
            f"<small style='color:#8b949e'>{niv}  ·  "
            f"<span style='color:{status_color};font-weight:600'>{status}</span></small>",
            unsafe_allow_html=True,
        )
    with h2:
        st.markdown("**Athletik Score**")
        st.markdown(_score_badge(ascore), unsafe_allow_html=True)
    with h3:
        st.markdown("**Athletik-Status**")
        st.markdown(_risk_badge(level), unsafe_allow_html=True)

    # ── Schnellaktionen ────────────────────────────────────────────────────
    _btn_a, _btn_b, _ = st.columns([2, 2, 3])
    with _btn_a:
        if st.button("⚖️ Mit anderem Spieler vergleichen",
                     key="profil_goto_vergleich",
                     use_container_width=True):
            st.session_state["vergl_preset_pid"] = sid
            st.session_state["_nav_goto"] = "⚖️  Vergleich"
            st.rerun()
    with _btn_b:
        # Kein Cache — damit Änderungen (neue Tests, neue Verletzungen) sofort
        # im Export sichtbar sind und keine veralteten Daten ausgeliefert werden.
        _xlsx = spieler_excel_bytes(sid)
        _name_safe = auswahl["name"].replace(" ", "_")
        st.download_button(
            label="⬇️ Spieler exportieren (Excel)",
            data=_xlsx,
            file_name=f"Spieler_{_name_safe}_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="profil_xlsx_dl",
        )

    # ── Radar-Chart im Header (wenn ≥ 3 Module vorhanden) ─────────────────
    sub_scores_header = athletik_sub_scores(fms, y, sprint, sprung, agil, aus,
                                            spiro_row=_spiro_p)
    if len(sub_scores_header) >= 3:
        label_map_h = {
            "FMS": "FMS", "Y-Balance": "Y-Balance", "Sprint": "Sprint",
            "Sprungkraft": "Sprungkraft", "Agilitaet": "Agilität", "Ausdauer": "Ausdauer",
            "Spiro": "Spiro",
        }
        cats_h  = [label_map_h.get(k, k) for k in sub_scores_header.keys()]
        vals_h  = list(sub_scores_header.values())
        cats_hc = cats_h + [cats_h[0]]
        vals_hc = vals_h + [vals_h[0]]
        fig_hdr = go.Figure()
        fig_hdr.add_trace(go.Scatterpolar(
            r=vals_hc, theta=cats_hc,
            fill="toself", name="Profil",
            line=dict(color="#3b82f6", width=2),
            fillcolor="rgba(59,130,246,0.18)",
            marker=dict(size=7, color="#58a6ff"),
        ))
        fig_hdr.update_layout(
            polar=dict(
                bgcolor="#161b22",
                radialaxis=dict(visible=True, range=[0, 100],
                               color="#8b949e", gridcolor="#30363d",
                               tickfont=dict(size=8)),
                angularaxis=dict(color="#e6edf3", gridcolor="#30363d",
                                 tickfont=dict(size=10)),
            ),
            **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis", "margin")},
            height=280, showlegend=False, margin=dict(l=40, r=40, t=20, b=20),
        )
        _, rc = st.columns([3, 2])
        with rc:
            st.plotly_chart(fig_hdr, use_container_width=True)

    st.markdown("---")

    # ── Key metrics ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("FMS Score",      f"{fms['score']}/21" if fms else "Kein Test")
    m2.metric("FMS Bewertung",  fms["bewertung"] if fms else "—")
    if y:
        avg_y = (y["composite_rechts"] + y["composite_links"]) / 2
        m3.metric("Y-Balance Ø",    f"{avg_y:.1f} %")
        m4.metric("Y-Balance Asym.", y["asymmetrie"][:25])
    else:
        m3.metric("Y-Balance",  "Kein Test")
        m4.metric("Y-Balance",  "—")

    st.markdown("---")

    # ── Anthropometrie-Karte ───────────────────────────────────────────────
    ak_col, ak_btn_col = st.columns([5, 1])
    with ak_col:
        st.markdown(anthro_karte(anthro), unsafe_allow_html=True)
    with ak_btn_col:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("📐 Messen →", key="profil_goto_anthro", use_container_width=True):
            st.session_state["_nav_goto"]                  = "🔬  Diagnostik"
            st.session_state["_nav_sub_diagnostik_goto"]   = "📐 Anthropometrie"
            st.rerun()

    # ── Anthropometrie-Verlauf (nur bei ≥ 2 Messungen) ────────────────────
    if len(anthro_hist) >= 2:
        df_ah = pd.DataFrame(anthro_hist)
        # Metric selector (compact, inline)
        metrik_opt = {"Größe (cm)": "groesse", "Gewicht (kg)": "gewicht", "BMI": "bmi"}
        metrik_label = st.radio(
            "Verlauf anzeigen",
            list(metrik_opt.keys()),
            horizontal=True,
            key="profil_anthro_metrik",
            label_visibility="collapsed",
        )
        metrik_col  = metrik_opt[metrik_label]
        metrik_farbe = {"groesse": "#3b82f6", "gewicht": "#3fb950", "bmi": "#d29922"}[metrik_col]
        metrik_einheit = {"groesse": "cm", "gewicht": "kg", "bmi": ""}[metrik_col]

        fig_ah = go.Figure()
        fig_ah.add_trace(go.Scatter(
            x=df_ah["datum"],
            y=df_ah[metrik_col],
            mode="lines+markers+text",
            text=[f"{v:.1f}{metrik_einheit}" if v else "" for v in df_ah[metrik_col]],
            textposition="top center",
            textfont=dict(size=10, color=metrik_farbe),
            line=dict(color=metrik_farbe, width=2),
            marker=dict(size=7, color=metrik_farbe),
            name=metrik_label,
        ))
        fig_ah.update_layout(**_pl(
            height=220,
            margin=dict(l=40, r=20, t=12, b=36),
            showlegend=False,
            xaxis=dict(title=None, tickfont=dict(size=10)),
            yaxis=dict(title=metrik_label, tickfont=dict(size=10)),
        ))
        st.plotly_chart(fig_ah, use_container_width=True)

    # ── Stufentest-Kachel: nur protokollspezifische V2-Aussage ──────────────
    if _spiro_p:
        from spiro import spiro_bewertung_v2 as _spiro_bewertung_v2
        _spiro_alter_p = alter_am_datum(auswahl.get("geburtsdatum", ""), _spiro_p.get("datum", "")) or alter
        _spiro_rating_p = _spiro_bewertung_v2(
            _spiro_p,
            alter_testtag=_spiro_alter_p,
            geschlecht=auswahl.get("geschlecht", "Männlich"),
            stufen=spiro_stufen_laden(_spiro_p["id"]),
        )["text"]
    else:
        _spiro_rating_p = None

    _sp_col, _ = st.columns([2, 1])
    with _sp_col:
        st.markdown(
            test_status_card(
                "Stufentest", "🔬",
                _spiro_p["datum"] if _spiro_p else None,
                _spiro_rating_p,
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Tabs: Defizite / Verletzungshistorie / PDF ─────────────────────────
    tab_def, tab_verletz, tab_pdf = st.tabs(["🎯 Defizite & Empfehlungen", "🩹 Verletzungshistorie", "📄 PDF Report"])

    with tab_def:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 🎯 Erkannte Defizite")
            if not defizite:
                st.success("✅ Keine auffälligen Defizite erkannt.")
            else:
                for d in defizite:
                    css   = "tag-crit" if d["level"] == "kritisch" else "tag-warn"
                    modul = d.get("modul", "")
                    modul_badge = (
                        f'<span style="font-size:10px;color:#8b949e;background:#21262d;'
                        f'border-radius:4px;padding:1px 6px;margin-left:6px">{modul}</span>'
                        if modul else ""
                    )
                    st.markdown(
                        f'<div class="card"><span class="{css}">{d["bereich"]}</span>'
                        f'{modul_badge}'
                        f'<br><small style="color:#8b949e">{d["text"]}</small></div>',
                        unsafe_allow_html=True,
                    )
        with col_r:
            st.markdown("### 🏋️ Trainingsempfehlungen")
            # Erhaltungstraining wenn Tests vorliegen aber keine Defizite erkannt
            _sw_empf = schwerpunkt
            _erh_aktiv = False
            if not schwerpunkt.strip():
                if ist_unauffaellig(fms, y, sprint, sprung, agil, aus, spiro_row=_spiro_p):
                    _sw_empf = ERHALTUNGS_SCHWERPUNKT
                    _erh_aktiv = True
            bereiche = empfehlung_bereiche(_sw_empf)
            if not bereiche:
                st.info("Noch keine Testdaten erfasst — Diagnostik durchführen, um Trainingsempfehlungen zu erhalten.")
            else:
                if _erh_aktiv:
                    st.success("✅ **Unauffällige Diagnostik** — Erhaltungs- und Leistungssteigerungsplan aktiv", icon=None)
                    st.markdown(
                        f'<div style="background:#0d1117;border-left:3px solid #3fb950;padding:10px 14px;'
                        f'border-radius:6px;margin-bottom:10px;font-size:12px;color:#8b949e">'
                        f'{ERHALTUNGS_BEGRUENDUNG}</div>',
                        unsafe_allow_html=True,
                    )
                for bereich, uebungen in uebungen_fuer_bereiche(bereiche).items():
                    with st.expander(f"**{bereich}** — {len(uebungen)} Übungen"):
                        for u in uebungen:
                            st.markdown(
                                f"**{u['uebung']}**  \n"
                                f"Problem: {u['problem']} · {u['saetze']} Sätze · "
                                f"{u['wiederholungen']} · {u['haeufigkeit']}"
                            )

    with tab_verletz:
        st.markdown("### 🩹 Verletzungshistorie")

        # Neue Verletzung eintragen
        with st.expander("➕ Neue Verletzung eintragen"):
            va1, va2 = st.columns(2)
            v_datum      = va1.text_input("Datum (TT.MM.JJJJ)", value=date.today().strftime("%d.%m.%Y"), key="v_dat")
            v_art        = va2.selectbox("Verletzungsart", VERLETZUNGSARTEN, key="v_art")
            v_koerper    = va1.selectbox("Körperteil", KOERPERTEILE, key="v_koerper")
            v_schwere    = va2.selectbox("Schweregrad", SCHWEREGRADE, key="v_schwere")
            v_ausfall    = va1.number_input("Ausfalltage (geschätzt)", 0, 365, 0, key="v_ausfall")
            v_notizen    = st.text_area("Notizen / Anmerkungen", key="v_notizen", height=80)
            if st.button("💾 Verletzung speichern", key="v_save", type="primary", use_container_width=True):
                verletzung_speichern(sid, v_datum, v_art, v_koerper, v_schwere, int(v_ausfall), v_notizen)
                _save_ok("Verletzung gespeichert.")
                st.rerun()

        # Verletzungsliste
        verletzungen = verletzungen_laden(sid)
        if not verletzungen:
            st.info("Noch keine Verletzungen eingetragen.")
        else:
            gesamt_ausfall = sum(v.get("ausfall_tage") or 0 for v in verletzungen)
            va, vb = st.columns(2)
            va.metric("Einträge gesamt", len(verletzungen))
            vb.metric("Ausfalltage gesamt", gesamt_ausfall)
            st.markdown("---")
            for v in verletzungen:
                schwere_color = (
                    "#f85149" if "schwer" in (v.get("schwere") or "").lower()
                    else "#d29922" if "mittel" in (v.get("schwere") or "").lower()
                    else "#3fb950"
                )
                st.markdown(
                    f'<div class="card">'
                    f'<div style="display:flex;justify-content:space-between">'
                    f'<span style="font-weight:700;color:#e6edf3">{v.get("koerperteil","—")} — {v.get("art","—")}</span>'
                    f'<span style="color:#8b949e;font-size:13px">{v.get("datum","")}</span>'
                    f'</div>'
                    f'<span style="color:{schwere_color};font-size:12px;font-weight:600">{v.get("schwere","—")}</span>'
                    f'  ·  <span style="color:#8b949e;font-size:12px">{v.get("ausfall_tage",0)} Ausfalltage</span>'
                    + (f'<br><small style="color:#8b949e">{v["notizen"]}</small>' if v.get("notizen") else "")
                    + f'</div>',
                    unsafe_allow_html=True,
                )
            with st.expander("🗑️ Verletzungseintrag löschen"):
                del_v = st.selectbox(
                    "Eintrag wählen", verletzungen,
                    format_func=lambda x: f"{x.get('datum','')} — {x.get('koerperteil','')} ({x.get('art','')})",
                    key="del_v",
                )
                if _confirm_loeschen("del_v_btn", was="diesen Verletzungseintrag",
                                     btn_label="🗑️ Eintrag löschen"):
                    verletzung_loeschen(del_v["id"])
                    _save_ok("Verletzungseintrag gelöscht.")
                    st.rerun()

    with tab_pdf:
        st.markdown("### 📄 PDF Report")

        # Daten laden
        plan_rows        = zyklus_laden(sid)
        anthro_row       = anthropometrie_letzter(sid)
        sprint_row       = sprint_letzter(sid)
        sprung_row       = sprung_letzter(sid)
        agil_row         = agilitaet_letzter(sid)
        aus_row          = ausdauer_letzter(sid)
        verletzungen_pdf = verletzungen_laden(sid)
        kraft_pdf        = kraft_letzter(sid)
        beob_pdf         = beobachtungen_alle_fuer_spieler(sid)
        spiro_pdf        = spiro_test_letzter(sid)

        # ── Modulauswahl ──────────────────────────────────────────────────────
        st.markdown("#### 📋 Module auswählen")
        st.caption(
            "Wähle, welche Abschnitte im PDF erscheinen sollen. "
            "Grau = noch keine Daten vorhanden."
        )

        # (label, session_key, hat_daten, daten_objekt)
        _MODULE_CFG = [
            ("📐 Anthropometrie",         "pdf_m_anthro",   bool(anthro_row),       anthro_row),
            ("📝 FMS",                    "pdf_m_fms",      bool(fms),              fms),
            ("📏 Y-Balance",              "pdf_m_ybal",     bool(y),                y),
            ("⚡ Sprint",                 "pdf_m_sprint",   bool(sprint_row),       sprint_row),
            ("🦘 Sprung / CMJ",           "pdf_m_sprung",   bool(sprung_row),       sprung_row),
            ("🔀 Agilität",               "pdf_m_agil",     bool(agil_row),         agil_row),
            ("🫁 Ausdauer (Yo-Yo)",       "pdf_m_ausdauer", bool(aus_row),          aus_row),
            ("💪 Kraftdiagnostik",        "pdf_m_kraft",    bool(kraft_pdf),        kraft_pdf),
            ("🫀 Spiroergometrie",        "pdf_m_spiro",    bool(spiro_pdf),        spiro_pdf),
            ("🩹 Verletzungshistorie",    "pdf_m_verletz",  bool(verletzungen_pdf), verletzungen_pdf),
            ("⚠️ Defizite & Empfehlungen","pdf_m_defizite", bool(defizite),         defizite),
            ("📅 Trainingsplan",          "pdf_m_plan",     bool(plan_rows),        plan_rows),
            ("🗒️ Trainerbeobachtungen",   "pdf_m_beob",     bool(beob_pdf),         beob_pdf),
        ]

        # Schnellauswahl-Buttons
        _qa1, _qa2, _qa3 = st.columns(3)
        if _qa1.button("✅ Alle aktivieren",  key="pdf_m_alle_an",  use_container_width=True):
            for _, _k, _hd, _ in _MODULE_CFG:
                if _hd:
                    st.session_state[_k] = True
        if _qa2.button("⬜ Alle deaktivieren", key="pdf_m_alle_aus", use_container_width=True):
            for _, _k, _hd, _ in _MODULE_CFG:
                if _hd:
                    st.session_state[_k] = False
        if _qa3.button("🔬 Nur Testergebnisse", key="pdf_m_nur_tests", use_container_width=True):
            _test_keys = {"pdf_m_anthro","pdf_m_fms","pdf_m_ybal","pdf_m_sprint",
                          "pdf_m_sprung","pdf_m_agil","pdf_m_ausdauer","pdf_m_kraft","pdf_m_spiro"}
            for _, _k, _hd, _ in _MODULE_CFG:
                if _hd:
                    st.session_state[_k] = _k in _test_keys

        st.markdown("")
        _mc1, _mc2, _mc3 = st.columns(3)
        _col_cycle = [_mc1, _mc2, _mc3]
        _selection = {}

        for _i, (_lbl, _key, _hat_daten, _daten) in enumerate(_MODULE_CFG):
            _col = _col_cycle[_i % 3]
            with _col:
                if _hat_daten:
                    _selection[_key] = st.checkbox(
                        _lbl,
                        value=st.session_state.get(_key, True),
                        key=_key,
                    )
                else:
                    st.checkbox(
                        _lbl,
                        value=False,
                        disabled=True,
                        key=f"{_key}_dis",
                        help="Noch keine Daten vorhanden",
                    )
                    _selection[_key] = False

        _n_aktiv = sum(1 for v in _selection.values() if v)

        st.markdown("---")

        # Vorschau-Banner
        _vorh_labels = [_lbl for (_lbl, _key, _hat, _) in _MODULE_CFG if _selection.get(_key)]
        if _vorh_labels:
            st.markdown(
                f'<div style="background:#0d1117;border:1px solid #238636;'
                f'border-radius:8px;padding:10px 14px;margin-bottom:12px">'
                f'<div style="font-size:10px;color:#3fb950;letter-spacing:1px;margin-bottom:6px">'
                f'PDF ENTHÄLT — {_n_aktiv} MODULE</div>'
                f'<div style="color:#c9d1d9;font-size:12px">'
                + "  ·  ".join(_vorh_labels)
                + '</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning("⚠️ Kein Modul ausgewählt — bitte mindestens eines aktivieren.")

        if _n_aktiv > 0 and st.button(
            f"📥 PDF Report generieren  ({_n_aktiv} Module)",
            key="pdf_gen", type="primary", use_container_width=True,
        ):
            def _m(key, daten):
                return daten if _selection.get(key) else None

            _verein_pdf = verein_by_id(_akt_user().get("verein_id") or 0) or {}
            _spiro_pdf_row = _m("pdf_m_spiro", spiro_pdf)
            _spiro_bewertung_pdf = None
            if _spiro_pdf_row:
                from spiro import spiro_bewertung_v2 as _spiro_bewertung_v2
                _spiro_bewertung_pdf = _spiro_bewertung_v2(
                    _spiro_pdf_row,
                    alter_testtag=alter_am_datum(
                        auswahl.get("geburtsdatum", ""), _spiro_pdf_row.get("datum", "")
                    ) or alter,
                    geschlecht=auswahl.get("geschlecht", "Männlich"),
                    stufen=spiro_stufen_laden(_spiro_pdf_row["id"]),
                )
            pdf_bytes = generate_report(
                spieler=auswahl,
                fms_row=       _m("pdf_m_fms",      fms),
                y_row=         _m("pdf_m_ybal",     y),
                anthro_row=    _m("pdf_m_anthro",   anthro_row),
                sprint_row=    _m("pdf_m_sprint",   sprint_row),
                sprung_row=    _m("pdf_m_sprung",   sprung_row),
                agil_row=      _m("pdf_m_agil",     agil_row),
                aus_row=       _m("pdf_m_ausdauer", aus_row),
                kraft_row=     _m("pdf_m_kraft",    kraft_pdf),
                spiro_row=     _spiro_pdf_row,
                spiro_bewertung=_spiro_bewertung_pdf,
                verletzungen=  _m("pdf_m_verletz",  verletzungen_pdf) or [],
                athletik_score=ascore,
                risiko_label=label,
                defizite=      _m("pdf_m_defizite", defizite) or [],
                plan_rows=     _m("pdf_m_plan",     plan_rows) or [],
                beobachtungen= _m("pdf_m_beob",     beob_pdf) or [],
                vereinsname=st.session_state.get("cfg_vereinsname", ""),
                saison=st.session_state.get("cfg_saison", ""),
                logo_bytes=logo_laden(),
                trainer_name=st.session_state.get("cfg_trainer_name", ""),
                farbe_primaer=_verein_pdf.get("farbe_primaer"),
            )
            st.session_state["pdf_bytes_cache"] = pdf_bytes
            st.download_button(
                label="⬇️ PDF herunterladen",
                data=pdf_bytes,
                file_name=f"athletik_report_{auswahl['name'].replace(' ','_')}_{date.today()}.pdf",
                mime="application/pdf",
                key="pdf_dl",
            )
            _save_ok(f"PDF erstellt mit {_n_aktiv} Modulen.")

        st.markdown("---")
        st.markdown("### 📧 E-Mail vorbereiten")
        st.caption(
            "Erstelle eine vorbereitete E-Mail mit dem Pflichthinweis aus den "
            "Anwendungshinweisen. Die E-Mail wird in deinem Standard-Mail-Programm geöffnet."
        )
        ec1, ec2 = st.columns(2)
        email_empfaenger = ec1.text_input(
            "Empfänger-Adresse", placeholder="spieler@beispiel.de", key="email_to"
        )
        email_trainername = ec2.text_input(
            "Absender / Trainername", key="email_trainer",
            value=st.session_state.get("cfg_vereinsname", ""),
            placeholder="Dein Name oder Vereinsname"
        )
        spieler_name = auswahl.get("name", "Spieler")
        email_betreff = f"Athletik Testprotokoll – {spieler_name} – {date.today().strftime('%d.%m.%Y')}"
        email_text = EMAIL_NACHRICHT_VORLAGE.format(
            trainername=email_trainername.strip() or "Trainer"
        )
        email_text_edit = email_text
        with st.expander("📋 E-Mail-Text Vorschau / bearbeiten"):
            email_text_edit = st.text_area(
                "E-Mail-Text (bearbeitbar)", value=email_text,
                height=160, key="email_text_edit",
                label_visibility="collapsed"
            )

        import urllib.parse
        mailto_body  = urllib.parse.quote(email_text_edit)
        mailto_subj  = urllib.parse.quote(email_betreff)
        mailto_link  = f"mailto:{email_empfaenger}?subject={mailto_subj}&body={mailto_body}"
        st.link_button(
            "📨 E-Mail-Programm öffnen",
            url=mailto_link,
            use_container_width=True,
        )
        st.info(
            "💡 Der Pflichthinweis ist im E-Mail-Text enthalten. "
            "Hänge den heruntergeladenen PDF-Report manuell als Anhang an."
        )


# ──────────────────────────────────────────────────────────────────────────────

def page_trainingsplan():
    st.markdown("# 📅 Trainingsplan")
    _inline_spielerwechsel("training")

    auswahl = _player_selector("plan")
    if not auswahl:
        return

    sid     = auswahl["id"]
    fms     = fms_letzter(sid)
    y       = y_balance_letzter(sid)
    sprint  = sprint_letzter(sid)
    sprung  = sprung_letzter(sid)
    agil    = agilitaet_letzter(sid)
    aus     = ausdauer_letzter(sid)
    kraft   = kraft_letzter(sid)
    spiro   = spiro_test_letzter(sid)

    # ── SCHRITT 3: Datenstatus + Defiziterkennung (NO_DATA ≠ DEFIZIT) ────────
    _tests_vorhanden  = any([fms, y, sprint, sprung, agil, aus, kraft, spiro])
    defizite_valide   = defizite_ermitteln(fms, y, sprint, sprung, agil, aus, kraft_row=kraft, spiro_row=spiro,
                                            geschlecht=auswahl.get("geschlecht", "Männlich"))
    _anzahl_defizite  = len(defizite_valide)   # nur echte, datenbasierte Defizite zählen

    schwerpunkt = trainingsbereich_scores_ermitteln(
        fms, y, sprint, sprung, agil, aus, kraft_row=kraft, spiro_row=spiro,
        geschlecht=auswahl.get("geschlecht", "Männlich"),
    )

    # Planmodus bestimmen: Basis / Erhaltung / Diagnostik
    _tp_unauffaellig = _tests_vorhanden and not schwerpunkt
    if not _tests_vorhanden:
        _plan_modus = "Basis"       # Fall A: kein Test → kein Defizit, Basis-Modus
    elif _tp_unauffaellig:
        _plan_modus = "Erhaltung"   # Tests vorhanden, keine Auffälligkeiten
        schwerpunkt = ERHALTUNGS_SCHWERPUNKT
    else:
        _plan_modus = "Diagnostik"  # echte Defizite erkannt

    _schwerpunkt_historie = (
        ", ".join(
            f"{bereich} (Priorität {prioritaet})"
            for bereich, prioritaet in sorted(schwerpunkt.items(), key=lambda item: -item[1])
        )
        if isinstance(schwerpunkt, dict) else str(schwerpunkt or "")
    )

    tab_auto, tab_manual, tab_view = st.tabs(["🤖 Automatisch generieren", "✍️ Manuell hinzufügen", "📋 Plan anzeigen"])

    with tab_auto:
        st.markdown("### Individuellen Trainingsplan aus Diagnostikdaten")

        # ── Modus-Banner ──────────────────────────────────────────────────────
        if _plan_modus == "Basis":
            # Fall A: kein Test vorhanden — Basis-Modus, keine Defizite
            st.markdown(
                f'<div style="background:#0d1117;border:1px solid #30363d;border-radius:10px;'
                f'padding:14px 18px;margin-bottom:16px">'
                f'<div style="font-size:14px;font-weight:700;color:#8b949e;margin-bottom:4px">'
                f'📋 Trainingsmodus: <strong style="color:#e6edf3">Basis-Modus</strong></div>'
                f'<div style="font-size:12px;color:#8b949e">'
                f'Keine ausreichenden Diagnosedaten vorhanden. '
                f'Der Plan wird alters- und leistungsorientiert ohne diagnostischen Schwerpunkt erstellt. '
                f'Alle Trainingsbereiche sind <em>allgemeine Athletikbausteine</em>, keine erkannten Defizite.'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        elif _plan_modus == "Erhaltung":
            st.markdown(
                f'<div style="background:#0d2415;border:1px solid #3fb950;border-radius:10px;'
                f'padding:14px 18px;margin-bottom:16px">'
                f'<div style="font-size:14px;font-weight:700;color:#3fb950;margin-bottom:4px">'
                f'✅ Trainingsmodus: Leistung erhalten und weiterentwickeln</div>'
                f'<div style="font-size:12px;color:#8b949e">{ERHALTUNGS_BEGRUENDUNG}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            # Diagnostik-Modus: echte Defizite
            _prio_clr = {3: "#f85149", 2: "#d29922", 1: "#3fb950"}
            _prio_lbl = {3: "🔴 Hauptschwerpunkt", 2: "🟡 Schwerpunkt", 1: "🟢 Nebenschwerpunkt"}
            if _anzahl_defizite == 1:
                _diag_modus_info = (
                    "Genau <strong>1 Defizit</strong> erkannt — dieser Bereich ist Hauptschwerpunkt "
                    "(ca. 60–70 %). Ergänzende Athletik bleibt erhalten."
                )
            elif _anzahl_defizite == 2:
                _diag_modus_info = (
                    "<strong>2 Defizite</strong> erkannt — beide als gleichgewichtete diagnostische "
                    "Schwerpunkte (je ca. 35 %). Allgemeiner Erhalt: ca. 30 %."
                )
            else:
                _diag_modus_info = (
                    f"<strong>{_anzahl_defizite} Defizite</strong> erkannt — die wichtigsten 2–3 "
                    "werden priorisiert, weitere als Nebenschwerpunkte geführt."
                )
            st.markdown(
                f'<div style="background:#1a0000;border:1px solid #f85149;border-radius:10px;'
                f'padding:14px 18px;margin-bottom:16px">'
                f'<div style="font-size:14px;font-weight:700;color:#f85149;margin-bottom:4px">'
                f'🔬 Trainingsmodus: Diagnostik-Modus</div>'
                f'<div style="font-size:12px;color:#8b949e">{_diag_modus_info}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Defizit-Anzeige (nur bei Diagnostik-Modus aus echten Daten) ──────
        if _plan_modus == "Diagnostik" and defizite_valide:
            st.markdown("#### 🔍 Erkannte Defizite (datenbasiert)")
            _d_cols = st.columns(min(_anzahl_defizite, 4))
            _prio_clr_map = {3: "#f85149", 2: "#d29922", 1: "#3fb950"}
            _prio_lbl_map = {3: "Hauptschwerpunkt", 2: "Schwerpunkt", 1: "Nebenschwerpunkt"}
            for i, d in enumerate(defizite_valide):
                col = _d_cols[i % len(_d_cols)]
                _clr = _prio_clr_map.get(d.get("prioritaet", 2), "#8b949e")
                _lbl = _prio_lbl_map.get(d.get("prioritaet", 2), "Schwerpunkt")
                _src = d.get("modul") or "—"
                _dat = d.get("datum") or ""
                col.markdown(
                    f'<div style="background:#161b22;border:2px solid {_clr};border-radius:8px;'
                    f'padding:10px 14px;margin-bottom:8px;text-align:center">'
                    f'<div style="font-size:10px;color:{_clr};font-weight:700">{_lbl}</div>'
                    f'<div style="font-weight:700;color:#e6edf3;font-size:13px;margin:3px 0">{d["bereich"]}</div>'
                    f'<div style="color:#8b949e;font-size:10px">Quelle: {_src}</div>'
                    f'{"<div style=color:#6e7681;font-size:10px>" + _dat + "</div>" if _dat else ""}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            # Begründungen anzeigen
            with st.expander("ℹ️ Warum wird das trainiert?"):
                for d in defizite_valide:
                    st.markdown(
                        f"**{d['bereich']}** *(Quelle: {d.get('modul','—')})*  \n"
                        f"{d['text']}"
                    )
        elif _plan_modus == "Erhaltung":
            st.markdown("#### 🎯 Trainingsschwerpunkte (Erhaltung)")

        # ── Datenbasis-Transparenz ────────────────────────────────────────────
        _datenbasis = testdaten_uebersicht(fms, y, sprint, sprung, agil, aus, spiro_row=spiro)
        with st.expander("📊 Datenbasis — welche Tests wurden berücksichtigt?"):
            _db_cols = st.columns(len(_datenbasis))
            for col, (test_name, (status, datum)) in zip(_db_cols, _datenbasis.items()):
                if status == "NO_DATA":
                    col.markdown(
                        f'<div style="text-align:center;padding:6px">'
                        f'<div style="font-size:11px;color:#8b949e">{test_name}</div>'
                        f'<div style="font-size:10px;color:#30363d">Noch kein Test</div>'
                        f'</div>', unsafe_allow_html=True
                    )
                else:
                    col.markdown(
                        f'<div style="text-align:center;padding:6px">'
                        f'<div style="font-size:11px;color:#3fb950;font-weight:700">{test_name}</div>'
                        f'<div style="font-size:10px;color:#8b949e">{datum or "✓"}</div>'
                        f'</div>', unsafe_allow_html=True
                    )

        st.markdown("---")

        # ── Trainingsphilosophie — Empfehlung + Auswahl ───────────────────────
        st.markdown("#### 🧠 Trainingsphilosophie")

        # Diagnostik-Score für Empfehlungs-Engine
        _diag_score: float | None = None
        try:
            _ascore_val = athletik_score(fms, y, sprint, sprung, agil, aus)
            _diag_score = float(_ascore_val) if _ascore_val is not None else None
        except Exception:
            pass

        _ph_empfehlung, _ph_conf = empfehle_philosophie(
            alter            = _tp_alter if "_tp_alter" in dir() else berechne_alter(auswahl.get("geburtsdatum")),
            plangruppe       = _tp_pg    if "_tp_pg" in dir()    else None,
            fms_score        = float(fms.score) if fms and hasattr(fms, "score") else None,
            saison_phase     = st.session_state.get("saison_phase_sel", "Normal"),
            verletzung_aktiv = bool(verletzung_aktive_bereiche(verletzungen_laden(sid))),
            diagnostik_score = _diag_score,
        )
        _ph_erklaerung = philosophie_erklaerung(
            _ph_empfehlung,
            alter         = berechne_alter(auswahl.get("geburtsdatum")),
            fms_score     = float(fms.score) if fms and hasattr(fms, "score") else None,
            saison_phase  = st.session_state.get("saison_phase_sel", "Normal"),
            verletzung_aktiv = bool(verletzung_aktive_bereiche(verletzungen_laden(sid))),
            diagnostik_score = _diag_score,
            confidence    = _ph_conf,
        )

        # Gespeicherte Philosophie laden (persistiert per Spieler)
        _ph_gespeichert = _philosophie_laden(sid)
        _ph_default_idx = list(PHILOSOPHIEN.keys()).index(_ph_empfehlung) if _ph_empfehlung in PHILOSOPHIEN else 0
        if _ph_gespeichert and _ph_gespeichert in PHILOSOPHIEN:
            _ph_default_idx = list(PHILOSOPHIEN.keys()).index(_ph_gespeichert)

        # Empfehlungskarte
        _ph_emp_label = PHILOSOPHIEN.get(_ph_empfehlung, {}).get("label", _ph_empfehlung)
        _ph_conf_pct  = int(_ph_conf * 100)
        _ph_conf_clr  = "#3fb950" if _ph_conf >= 0.8 else "#d29922" if _ph_conf >= 0.6 else "#8b949e"
        st.markdown(
            f'<div style="background:#0d1117;border:1px solid {_ph_conf_clr};border-radius:10px;'
            f'padding:12px 16px;margin-bottom:12px">'
            f'<span style="color:{_ph_conf_clr};font-weight:700;font-size:13px">🤖 Empfehlung: {_ph_emp_label}</span>'
            f'<span style="background:{_ph_conf_clr}22;color:{_ph_conf_clr};border-radius:4px;'
            f'padding:2px 8px;font-size:11px;margin-left:8px">{_ph_conf_pct} % Übereinstimmung</span><br>'
            f'<span style="color:#8b949e;font-size:12px;margin-top:4px;display:block">'
            f'{PHILOSOPHIEN.get(_ph_empfehlung, {}).get("beschreibung", "")}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Auswahl-Selectbox (Trainer kann übernehmen oder ändern)
        _ph_keys   = list(PHILOSOPHIEN.keys())
        _ph_labels = [PHILOSOPHIEN[k]["label"] for k in _ph_keys]
        _ph_sel_idx = st.selectbox(
            "Trainingsphilosophie auswählen",
            range(len(_ph_keys)),
            index=_ph_default_idx,
            format_func=lambda i: _ph_labels[i],
            key="philosophie_sel",
            help="Die Empfehlung basiert auf Alter, FMS, Diagnostik, Saisonphase und Verletzungshistorie. "
                 "Der Trainer kann jederzeit eine andere Philosophie wählen.",
        )
        selected_philosophie_key = _ph_keys[_ph_sel_idx]
        _ph_sel     = PHILOSOPHIEN[selected_philosophie_key]
        _ph_prog    = _ph_sel.get("progression", "moderat")
        _ph_energie = _ph_sel.get("energiesystem_fokus", "Gemischt")
        _ph_methoden = ", ".join(_ph_sel.get("trainingsmethoden", [])[:4])
        st.caption(
            f"📈 Progression: **{_ph_prog}** · Energiesystem: **{_ph_energie}** · "
            f"Methoden: {_ph_methoden}"
        )

        st.markdown("---")
        st.markdown("#### ⚙️ Planparameter")

        # ── Planungsmodus (Spec §2) ────────────────────────────────────────────
        _planungsmodus = st.radio(
            "**Planungsmodus**",
            ["Standard", "Mit Vereinsbelastung / Wochenplanung"],
            horizontal=True,
            key="planungsmodus_sel",
            help=(
                "**Standard**: Planerstellung wie bisher — Tests, Alter, Defizite und "
                "Schwerpunkte werden berücksichtigt, keine Angaben zu Vereinstraining oder Spieltagen nötig.\n\n"
                "**Mit Vereinsbelastung**: APH berücksichtigt die Gesamtwochenbelastung und "
                "empfiehlt passende Athletikeinheiten und Trainingstage."
            ),
        )
        _vb_modus = _planungsmodus == "Mit Vereinsbelastung / Wochenplanung"

        _pc1, _pc2 = st.columns(2)
        plan_laenge = _pc1.selectbox(
            "Planlänge",
            [4, 6, 8],
            format_func=lambda x: f"{x} Wochen",
            index=1,
            key="plan_laenge",
        )

        # ── Saisonperiode ─────────────────────────────────────────────────────
        _SAISON_OPTIONEN = {
            "Normal":       ("🔄 Normal",        "Defizit-getriebene 4-Phasen-Progression"),
            "Vorbereitung": ("📈 Vorbereitung",   "Volles Volumen & Intensität — Fitness aufbauen"),
            "Saison":       ("⚽ Saison",         "Erhaltungstraining — weniger Volumen, +Fußball"),
            "Nachsaison":   ("🔁 Nachsaison",     "Regeneration — nur Stabilisation, max. 4 Wochen"),
        }
        saison_phase = _pc2.selectbox(
            "Saisonperiode",
            list(_SAISON_OPTIONEN.keys()),
            format_func=lambda k: _SAISON_OPTIONEN[k][0],
            key="saison_phase_sel",
        )
        _sp_beschr = _SAISON_OPTIONEN[saison_phase][1]
        st.caption(f"**{_SAISON_OPTIONEN[saison_phase][0]}** — {_sp_beschr}")

        # §4 Equipment-Auswahl — verfügbares Equipment bestimmt Übungsauswahl
        _EQUIPMENT_ALLE = [
            "Körpergewicht", "Miniband", "Powerband", "Freie Gewichte",
            "Kurzhanteln", "Langhanteln", "Kettlebell", "Medizinball",
            "Maschine", "Schlitten", "Ball",
        ]
        verfuegbares_equipment = st.multiselect(
            "Verfügbares Equipment",
            _EQUIPMENT_ALLE,
            default=["Körpergewicht", "Miniband", "Freie Gewichte", "Ball"],
            key="equip_sel",
            help="Übungen mit nicht verfügbarem Equipment werden automatisch durch gleichwertige Alternativen ersetzt (Spec §4).",
        )

        # ── Aktive Verletzungen erkennen und anzeigen ─────────────────────────
        _alle_verletzungen = verletzungen_laden(sid)
        _aktive_bereiche   = verletzung_aktive_bereiche(_alle_verletzungen)
        if _aktive_bereiche:
            st.warning(
                "⚠️ **Aktive Verletzung erkannt** — folgende Bereiche werden im Plan ausgeschlossen:\n\n"
                + ", ".join(sorted(_aktive_bereiche)),
                icon=None,
            )

        # Altersgruppe ermitteln und anzeigen
        _tp_alter = berechne_alter(auswahl.get("geburtsdatum"))
        _tp_pg    = _alter_zu_plangruppe(_tp_alter)
        _tp_cfg   = _PLANGRUPPEN_CONFIG[_tp_pg]
        _tp_fki   = _fki(auswahl.get("geburtsdatum", ""))
        _tp_fk    = _tp_fki.get("fussballklasse") or "—"
        _tp_jk    = _jugendklasse(_tp_fk)
        _tp_sl    = _tp_fki.get("saison", "")
        _pg_farben = {
            "U7": "#3fb950", "U8": "#3fb950",
            "U10": "#3fb950", "U14": "#3fb950", "U18": "#d29922",
            "Senior": "#58a6ff", "Ü40": "#d29922", "Ü55": "#f85149",
        }
        _pg_clr = _pg_farben.get(_tp_pg, "#8b949e")
        _tp_alter_str = f" / {int(_tp_alter)} Jahre" if _tp_alter else ""
        st.markdown(
            f'<div style="background:#161b22;border:2px solid {_pg_clr};border-radius:8px;'
            f'padding:10px 16px;margin-bottom:12px">'
            f'<span style="font-size:13px;color:{_pg_clr};font-weight:700">'
            f'🎯 Trainingsstufe: {_tp_pg}{_tp_alter_str}</span>'
            f'<span style="color:#8b949e;font-size:12px;margin-left:10px">— {_tp_cfg["label"]}</span><br>'
            f'<small style="color:#8b949e">'
            f'Fußballklasse: {_tp_fk} (Saison {_tp_sl}) · Jugendklasse: {_tp_jk} · '
            f'Quelle: Faigenbaum & Myer (2010) · Lloyd et al. (2014) · NSCA Youth RT Position Statement'
            f'</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Trainingszeit pro Einheit (Spec §7) ──────────────────────────────
        _ZEIT_OPT = {20:"20 Min", 30:"30 Min", 45:"45 Min",
                     60:"60 Min", 75:"75 Min", 90:"90 Min", 0:"Benutzerdefiniert"}
        _tz_c1, _tz_c2 = st.columns([3, 2])
        _tz_sel = _tz_c1.selectbox(
            "Trainingszeit pro Einheit",
            list(_ZEIT_OPT.keys()), index=3,
            format_func=lambda k: _ZEIT_OPT[k], key="trainingszeit_sel",
        )
        if _tz_sel == 0:
            trainingszeit_min = int(_tz_c2.number_input(
                "Minuten (individuell)", min_value=10, max_value=180,
                value=60, step=5, key="trainingszeit_custom",
            ))
        else:
            trainingszeit_min = _tz_sel
        # Zeitbudget-Vorschau
        _zb_key = max(k for k in _ZEITBUDGET_CONFIG if k <= trainingszeit_min)
        _zb_prev = _ZEITBUDGET_CONFIG[_zb_key]
        st.caption(
            f"⏱️ Zeitbudget: max. **{_zb_prev['max_ueb_tag']} Übungen/Tag** · "
            f"max. **{_zb_prev['satz_cap']} Sätze** · "
            f"Warm-Up ~{_zb_prev['warmup_min']} min"
        )

        # ── Vereinsbelastung / Wochenplanung (Spec §4–§13) ───────────────────
        if _vb_modus:
            st.markdown("---")
            st.markdown("#### 🏟️ Vereinsbelastung & Wochenplanung")

            _vb_col1, _vb_col2 = st.columns(2)
            _vb_verein_anzahl_raw = _vb_col1.selectbox(
                "Vereinstraining pro Woche",
                [0, 1, 2, 3, 4, 5, "6+"],
                index=2,
                key="vb_verein_anzahl",
                help="Wie oft trainiert der Spieler pro Woche im Verein?",
            )
            _vb_verein_anzahl_int = 6 if str(_vb_verein_anzahl_raw) == "6+" else int(_vb_verein_anzahl_raw)

            _vb_verein_tage = _vb_col2.multiselect(
                "Vereinstrainingstage",
                _WOCHENTAGE_WP,
                default=["Dienstag", "Donnerstag"],
                key="vb_verein_tage",
                help="An welchen Tagen findet das Vereinstraining normalerweise statt?",
            )
            if _vb_verein_anzahl_int > 0 and len(_vb_verein_tage) != _vb_verein_anzahl_int:
                st.caption(
                    f"ℹ️ Vereinstraining/Woche ({_vb_verein_anzahl_int}) ≠ "
                    f"Anzahl gewählter Tage ({len(_vb_verein_tage)})."
                )

            _vb_col3, _vb_col4 = st.columns(2)
            _SPIEL_OPTIONEN = ["Kein Spiel", "1 Spiel", "2 Spiele", "Turnier / mehrere Spiele", "wechselnd"]
            _vb_spielbelastung = _vb_col3.selectbox(
                "Spiel-/Turnierbelastung pro Woche",
                _SPIEL_OPTIONEN,
                index=1,
                key="vb_spielbelastung",
            )
            _vb_spiel_tage: list[str] = []
            if _vb_spielbelastung != "Kein Spiel":
                _vb_spiel_tage = _vb_col4.multiselect(
                    "Typischer Spiel-/Turniertag",
                    _WOCHENTAGE_WP + ["Wechselnd"],
                    default=["Samstag"],
                    key="vb_spiel_tage",
                )

            # ── APH-Empfehlung (Spec §9) ──────────────────────────────────
            _spiel_tage_clean = [t for t in _vb_spiel_tage if t != "Wechselnd"]
            _vb_empf_anzahl, _vb_empf_begr = empfohlene_athletik_einheiten(
                alter=_tp_alter,
                verein_anzahl=_vb_verein_anzahl_int,
                spielbelastung=_vb_spielbelastung,
                saison_phase=saison_phase,
                hat_defizite=_anzahl_defizite > 0,
                trainingszeit_min=trainingszeit_min,
            )
            _vb_empf_tage = empfohlene_athletik_tage(
                anzahl=_vb_empf_anzahl,
                verein_tage=_vb_verein_tage,
                spiel_tage=_spiel_tage_clean,
                alter=_tp_alter,
                schwerpunkt_text=schwerpunkt,
            )
            st.markdown(
                f'<div style="background:#0d2a1a;border:1px solid #3fb950;border-radius:10px;'
                f'padding:14px 18px;margin-bottom:14px">'
                f'<div style="color:#3fb950;font-weight:700;font-size:14px;margin-bottom:6px">'
                f'🤖 APH-Empfehlung</div>'
                f'<div style="color:#c9d1d9;font-size:14px">'
                f'<b>{_vb_empf_anzahl} Athletikeinheit(en) pro Woche</b></div>'
                f'<div style="color:#8b949e;font-size:12px;margin-top:4px">Empfohlene Tage: '
                f'<b>{", ".join(_vb_empf_tage) if _vb_empf_tage else "—"}</b></div>'
                f'<div style="color:#8b949e;font-size:12px;margin-top:6px;font-style:italic">'
                f'{_vb_empf_begr}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Trainer-Override: Anzahl (Spec §10, §11)
            _vb_override_anzahl = st.checkbox(
                "Anzahl der Athletikeinheiten manuell festlegen",
                key="vb_override_anzahl_cb",
            )
            if _vb_override_anzahl:
                _vb_gewaehlte_anzahl = st.selectbox(
                    "Gewünschte Athletikeinheiten pro Woche",
                    [0, 1, 2, 3, 4],
                    index=min(_vb_empf_anzahl, 4),
                    key="vb_gewaehlte_anzahl_sel",
                )
                if _vb_gewaehlte_anzahl > _vb_empf_anzahl + 1:
                    st.warning(
                        "⚠️ Die gewählte Anzahl zusätzlicher Athletikeinheiten ist bei der "
                        "aktuellen Fußballbelastung relativ hoch. "
                        "Bitte Gesamtbelastung und Regeneration berücksichtigen."
                    )
            else:
                _vb_gewaehlte_anzahl = _vb_empf_anzahl

            # Trainer-Override: Tage (Spec §26, §27)
            _vb_override_tage = st.checkbox(
                "Athletiktage manuell wählen",
                key="vb_override_tage_cb",
            )
            if _vb_override_tage:
                _vb_gewaehlte_tage = st.multiselect(
                    "Athletiktrainingstage",
                    _WOCHENTAGE_WP,
                    default=_vb_empf_tage,
                    key="vb_gewaehlte_tage_sel",
                )
                # Konfliktwarnungen (Spec §27, §28)
                _vb_konflikte = []
                for _vb_t in _vb_gewaehlte_tage:
                    if _vb_t in _vb_verein_tage:
                        _vb_konflikte.append(
                            f"Athletik und Vereinstraining am gleichen Tag ({_vb_t})"
                        )
                    if _vb_t in _WOCHENTAGE_WP:
                        _vb_ti = _WOCHENTAGE_WP.index(_vb_t)
                        for _st in _spiel_tage_clean:
                            if _st in _WOCHENTAGE_WP:
                                _sti = _WOCHENTAGE_WP.index(_st)
                                if (_sti - _vb_ti) % 7 == 1:
                                    _vb_konflikte.append(
                                        f"Athletikeinheit am {_vb_t} direkt vor Spieltag ({_st}) "
                                        "— bei intensiven Inhalten Regeneration beachten"
                                    )
                for _k in set(_vb_konflikte):
                    st.caption(f"ℹ️ {_k}")
            else:
                _vb_gewaehlte_tage = empfohlene_athletik_tage(
                    anzahl=_vb_gewaehlte_anzahl,
                    verein_tage=_vb_verein_tage,
                    spiel_tage=_spiel_tage_clean,
                    alter=_tp_alter,
                    schwerpunkt_text=schwerpunkt,
                )

            _vb_trainer_override = _vb_override_anzahl or _vb_override_tage

            import json as _json_vb
            _wochenplanung_json = _json_vb.dumps({
                "planungsmodus": "vereinsbelastung",
                "verein_training_anzahl": _vb_verein_anzahl_int,
                "verein_trainingstage": _vb_verein_tage,
                "spielbelastung": _vb_spielbelastung,
                "spieltag": _vb_spiel_tage,
                "empfohlene_athletik_anzahl": _vb_empf_anzahl,
                "gewaehlte_athletik_anzahl": _vb_gewaehlte_anzahl,
                "empfohlene_athletik_tage": _vb_empf_tage,
                "gewaehlte_athletik_tage": _vb_gewaehlte_tage,
                "trainer_override": _vb_trainer_override,
                "aph_begruendung": _vb_empf_begr,
            }, ensure_ascii=False)
        else:
            _wochenplanung_json = None

        st.markdown("---")

        # ── Schutz vor ungewolltem Überschreiben (Spec §4) ───────────────────
        _aktive_v_auto = plan_aktive_version(sid)
        _confirm_key   = f"plan_create_confirm_{sid}"
        if _aktive_v_auto and not st.session_state.get(_confirm_key):
            st.warning(
                f"⚠️ Für diesen Spieler besteht bereits ein aktiver Trainingsplan "
                f"(Version {_aktive_v_auto['version_nr']}, erstellt am {_aktive_v_auto['datum']}, "
                f"Modus: {_aktive_v_auto['modus']})."
            )
            _ga, _gb = st.columns(2)
            _ga.button("📋 Bestehenden Plan weiter bearbeiten", use_container_width=True,
                       key="plan_behalten_btn")
            if _gb.button("🔄 Neuen Plan erstellen (alter wird archiviert)",
                          use_container_width=True, type="primary", key="plan_neu_btn"):
                st.session_state[_confirm_key] = True
                st.rerun()
        else:
            if st.button("⚡ Trainingsplan erstellen", use_container_width=True,
                         key="auto_gen_btn", type="primary"):
                # VB-Modus: gewaehlte_athletik_anzahl an Generator übergeben —
                # begrenzt tatsächlich erzeugte APH-Einheiten pro Woche.
                _gen_vb_anzahl: int | None = None
                if _wochenplanung_json:
                    try:
                        import json as _json_gen
                        _wp_gen = _json_gen.loads(_wochenplanung_json)
                        if _wp_gen.get("planungsmodus") == "vereinsbelastung":
                            _gen_vb_anzahl = int(_wp_gen.get("gewaehlte_athletik_anzahl") or 2)
                    except Exception:
                        _gen_vb_anzahl = None

                _new_pid: int | None = None
                try:
                    _new_pid = plan_version_erstellen(
                        sid, str(date.today()),
                        erstellt_von=st.session_state.get("username", ""),
                        modus=_plan_modus,
                        schwerpunkt=_schwerpunkt_historie[:500],
                        trainingszeit_min=trainingszeit_min,
                        wochenplanung_json=_wochenplanung_json,
                        status="ENTWURF",
                    )
                    n = trainingsplan_multi_erstellen(
                        sid, schwerpunkt,
                        wochen=plan_laenge,
                        alter=_tp_alter,
                        verletzung_bereiche=_aktive_bereiche,
                        saison_phase=saison_phase,
                        verfuegbares_equipment=verfuegbares_equipment,
                        philosophie_key=selected_philosophie_key,
                        trainingszeit_min=trainingszeit_min,
                        plan_id=_new_pid,
                        vb_anzahl=_gen_vb_anzahl,
                    )
                    if n <= 0:
                        raise RuntimeError("Der Plan enthält keine passenden Übungen.")
                    if not plan_version_aktivieren(sid, _new_pid):
                        raise RuntimeError("Die erzeugte Planversion konnte nicht aktiviert werden.")
                except Exception as _plan_error:
                    if _new_pid is not None:
                        plan_version_verwerfen(sid, _new_pid)
                    _log.exception("Automatische Planerstellung fehlgeschlagen")
                    st.error(f"Trainingsplan konnte nicht erstellt werden: {_plan_error}")
                else:
                    _philosophie_speichern(sid, selected_philosophie_key)
                    st.session_state.pop(_confirm_key, None)
                    _phase_hinweis   = f" ({saison_phase})" if saison_phase != "Normal" else ""
                    _verletz_hinweis = f" · {len(_aktive_bereiche)} Bereich(e) ausgeschlossen" if _aktive_bereiche else ""
                    _equip_hinweis   = f" · {', '.join(verfuegbares_equipment[:3])}{'…' if len(verfuegbares_equipment)>3 else ''}" if verfuegbares_equipment else ""
                    _save_ok(f"Trainingsplan erstellt — {n} Übungen, {plan_laenge} Wochen, {trainingszeit_min} min/Einheit ({_tp_pg}){_phase_hinweis}{_verletz_hinweis}.")
                    st.rerun()

    with tab_manual:
        st.markdown("### Übung manuell hinzufügen")
        st.caption("Alle Angaben werden in der aktiven Planversion gespeichert. Katalogübungen übernehmen passende Standardwerte, die der Trainer jederzeit anpassen kann.")
        mc1, mc2 = st.columns(2)
        bereich = mc1.selectbox("Bereich", ["Sprunggelenk","Knie","Hüfte","Rumpf","Oberschenkel",
                                             "Schnelligkeit","Explosivität","Agilität","Ausdauer","Fußball"],
                                key="manual_bereich")

        # Equipment-Filter für Manuell-Tab
        _EQUIPMENT_ALLE_MANUAL = [
            "Körpergewicht", "Miniband", "Powerband", "Freie Gewichte",
            "Kurzhanteln", "Langhanteln", "Kettlebell", "Medizinball",
            "Maschine", "Schlitten", "Ball",
        ]
        _manual_equip_default = list(st.session_state.get("equip_sel", []))
        _manual_equip = mc2.multiselect(
            "Equipment-Filter",
            _EQUIPMENT_ALLE_MANUAL,
            default=_manual_equip_default,
            key="manual_equip_filter",
            help="Nur Übungen anzeigen, die mit dem gewählten Equipment durchführbar sind. "
                 "Leer lassen = alle Übungen zeigen.",
        )

        # Zentraler Katalog: gleiche Pool-/Equipment-Logik wie Austausch und Editor.
        _m_alter = berechne_alter(auswahl.get("geburtsdatum"))
        _m_pg    = _alter_zu_plangruppe(_m_alter)
        _katalog = katalog_uebungen_fuer_bereich(bereich, _m_pg, _manual_equip)
        _EIGENE_OPT = "✏️ Eigene Übung eingeben..."
        _katalog_opts = _katalog + [_EIGENE_OPT]

        _ub_sel = st.selectbox("Übungsname", _katalog_opts,
                               key=f"manual_ub_{bereich}",
                               help="Alle Übungen aus dem Katalog für diesen Bereich "
                                    "gefiltert nach Equipment. Ganz unten: eigene Übung frei eingeben.")
        if _ub_sel == _EIGENE_OPT:
            uebung = st.text_input("Eigene Übung eingeben", key="manual_ub_custom",
                                   placeholder="z. B. Reverse Lunge mit Rotation")
        else:
            uebung = _ub_sel

        # Technisch vorhandene Standardwerte für Katalogübungen sichtbar machen.
        _manual_pool_key = "stabilisation"
        if _ub_sel != _EIGENE_OPT:
            if bereich == "Ausdauer":
                for _pk in ["stabilisation", "kraft", "power"]:
                    if any(_u == uebung for _u, *_ in _ausdauer_pool_fuer_plangruppe(_m_pg, _pk, 99)):
                        _manual_pool_key = _pk
                        break
            else:
                for _pk in ["stabilisation", "kraft", "power"]:
                    if any(_u == uebung for _u, *_ in _POOL.get(bereich, {}).get(_pk, [])):
                        _manual_pool_key = _pk
                        break
        _default_pause, _default_ausf = _pause_und_ausfuehrung(
            bereich, _manual_pool_key, False, _m_pg
        )
        if _ub_sel == _EIGENE_OPT:
            _default_ausf = ""
        _known_equipment = sorted(_UEBUNG_EQUIPMENT.get(uebung, frozenset({"Körpergewicht"})))
        _default_equipment = _known_equipment[0] if _known_equipment else "Körpergewicht"

        _mf1, _mf2, _mf3 = st.columns(3)
        saetze      = _mf1.text_input("Sätze", "3", key="manual_saetze")
        wdh         = _mf2.text_input("Wiederholungen", "10", key="manual_wdh")
        haeufigkeit = _mf3.text_input("Häufigkeit", "2×/Woche", key="manual_haeuf")
        _mf4, _mf5, _mf6 = st.columns(3)
        pause_sekunden = int(_mf4.number_input(
            "Pause (s)", min_value=0, max_value=600, value=int(_default_pause),
            key=f"manual_pause_{bereich}_{_ub_sel}",
        ))
        rpe = int(_mf5.number_input(
            "RPE / Intensität", min_value=1, max_value=10, value=7,
            key=f"manual_rpe_{bereich}_{_ub_sel}",
        ))
        _manual_equipment_index = (_EQUIPMENT_ALLE_MANUAL.index(_default_equipment)
                                   if _default_equipment in _EQUIPMENT_ALLE_MANUAL else 0)
        equipment = _mf6.selectbox(
            "Equipment", _EQUIPMENT_ALLE_MANUAL, index=_manual_equipment_index,
            key=f"manual_equipment_{bereich}_{_ub_sel}",
        )
        ausfuehrung = st.text_area(
            "Ausführung / Traineranweisung",
            value=_default_ausf,
            height=90,
            key=f"manual_ausfuehrung_{bereich}_{_ub_sel}",
            placeholder="Bei eigener Übung: sichere, konkrete Ausführung beschreiben.",
        )

        _aktive_vid_manual = plan_aktive_version_id(sid)
        _manual_existing = plan_laden_nach_version(_aktive_vid_manual) if _aktive_vid_manual else []
        _manual_wochen = sorted({int(r["woche"]) for r in _manual_existing}) or list(range(1, 13))
        _manual_tage = sorted({int(r["tag"]) for r in _manual_existing}) or [1]
        _mf7, _mf8 = st.columns(2)
        woche = _mf7.selectbox(
            "Woche", _manual_wochen,
            index=0, format_func=lambda w: f"Woche {w}", key="manual_woche",
        )
        tag = _mf8.selectbox(
            "Trainingstag", _manual_tage,
            index=0, format_func=lambda t: f"Tag {t}", key="manual_tag",
        )
        if st.button("➕ Übung speichern", type="primary", use_container_width=True):
            if not uebung or not str(uebung).strip():
                st.error("Bitte einen Übungsnamen eingeben.")
                return
            if not _aktive_vid_manual:
                _aktive_vid_manual = plan_version_erstellen(
                    sid, str(date.today()),
                    erstellt_von=st.session_state.get("username", ""),
                    modus="Manuell", trainingszeit_min=60,
                )
            trainingsplan_eintrag_speichern(
                sid, str(date.today()), woche,
                bereich, uebung, saetze, wdh, haeufigkeit,
                tag=int(tag), pause_sekunden=pause_sekunden, ausfuehrung=ausfuehrung,
                rpe=rpe, equipment=equipment,
                plan_id=_aktive_vid_manual,
            )
            _save_ok("Übung zum Trainingsplan hinzugefügt.")
            st.rerun()

    with tab_view:
        # ── Aktive Version laden ──────────────────────────────────────────────
        _av = plan_aktive_version(sid)
        if not _av:
            st.info("Noch kein Trainingsplan vorhanden. Bitte zuerst automatisch generieren oder manuell Übungen hinzufügen.")
            return
        _vid = _av["id"]
        plan = plan_laden_nach_version(_vid)
        if not plan:
            st.info("Der aktive Plan enthält noch keine Übungen. Bitte über '🤖 Automatisch generieren' oder '✍️ Manuell hinzufügen' Übungen ergänzen.")
            return
        _hauptteil_plan = [row for row in plan if row.get("bereich") != WARMUP_BEREICH]

        # ── Versions-Banner ───────────────────────────────────────────────────
        _v_modus_clr = {"Basis":"#8b949e","Erhaltung":"#3fb950","Diagnostik":"#f85149"}.get(_av["modus"],"#8b949e")
        st.markdown(
            f'<div style="background:#161b22;border:1px solid {_v_modus_clr};border-radius:8px;'
            f'padding:9px 14px;margin-bottom:10px;display:flex;gap:16px;align-items:center;flex-wrap:wrap">'
            f'<span style="color:{_v_modus_clr};font-weight:700;font-size:13px">'
            f'📋 Version {_av["version_nr"]} — {_av["modus"]}-Modus</span>'
            f'<span style="color:#8b949e;font-size:12px">Erstellt {_av["datum"]}</span>'
            f'<span style="color:#8b949e;font-size:12px">· ⏱️ {_av["trainingszeit_min"]} min/Einheit</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Neue Diagnosedaten (Spec §22) — 3 Optionen ───────────────────────
        try:
            _td = [
                fms.get("datum") or fms.get("erstellt_am")     if fms   else None,
                y.get("datum")   or y.get("erstellt_am")       if y     else None,
                sprint.get("datum") or sprint.get("erstellt_am") if sprint else None,
                sprung.get("datum") or sprung.get("erstellt_am") if sprung else None,
                agil.get("datum")   or agil.get("erstellt_am")   if agil  else None,
                aus.get("datum")    or aus.get("erstellt_am")    if aus   else None,
                spiro.get("datum")  or spiro.get("erstellt_am")  if spiro else None,
            ]
            _newest_diag = max((d for d in _td if d), default=None)
            if _newest_diag and _newest_diag > _av["datum"]:
                st.warning(
                    f"📊 **Neue Diagnosedaten verfügbar** (letzter Test: {_newest_diag}). "
                    f"Der bestehende Plan (V{_av['version_nr']}, {_av['datum']}) wurde nicht verändert."
                )
                _diag_c1, _diag_c2, _diag_c3 = st.columns(3)
                _diag_c1.button("✅ Bestehenden Plan behalten", use_container_width=True,
                                key="diag_keep_btn")
                if _diag_c2.button("🔀 Plan anpassen", use_container_width=True,
                                   key="diag_adjust_btn"):
                    plan_version_archivieren_aktiv(sid)
                    _adj_pid = plan_duplizieren(sid, _vid, str(date.today()),
                                               st.session_state.get("username",""))
                    _save_ok(f"Plan als neue Version dupliziert — bitte jetzt anpassen.")
                    st.rerun()
                if _diag_c3.button("🆕 Neuen Plan erstellen", use_container_width=True,
                                   key="diag_new_btn"):
                    st.session_state[f"plan_create_confirm_{sid}"] = True
                    st.rerun()
        except Exception:
            pass

        # ── KPI-Zeile ─────────────────────────────────────────────────────────
        _total_wochen   = max(r["woche"] for r in plan)
        _total_uebungen = len(set(r["uebung"] for r in _hauptteil_plan))
        _total_bereiche = len(set(r["bereich"] for r in _hauptteil_plan))
        _total_tags     = max(r["tag"] for r in plan)
        _ci1, _ci2, _ci3, _ci4 = st.columns(4)
        _ci1.metric("Wochen", _total_wochen)
        _ci2.metric("Übungen", _total_uebungen)
        _ci3.metric("Bereiche", _total_bereiche)
        _ci4.metric("Einheiten/Woche", _total_tags)

        # ── Wochenansicht (Spec §21) — nur wenn Vereinsbelastungs-Modus gespeichert ──
        _av_wp_json = _av.get("wochenplanung_json")
        if _av_wp_json:
            try:
                import json as _json_tv
                _wp = _json_tv.loads(_av_wp_json)
                if _wp.get("planungsmodus") == "vereinsbelastung":
                    with st.expander("📅 Wochenansicht", expanded=False):
                        _wp_verein_tage = _wp.get("verein_trainingstage", [])
                        _wp_spiel_tage  = [t for t in _wp.get("spieltag", []) if t != "Wechselnd"]
                        _wp_ath_tage    = _wp.get("gewaehlte_athletik_tage", [])
                        _wp_spielbel    = _wp.get("spielbelastung", "")
                        st.caption(
                            f"🏟️ Vereinstraining: **{', '.join(_wp_verein_tage) or '—'}** · "
                            f"🏆 Spiel: **{', '.join(_wp_spiel_tage) or '—'}** · "
                            f"🏋️ Athletik: **{', '.join(_wp_ath_tage) or '—'}**"
                        )
                        _TAGE_ALLE_WV = ["Montag","Dienstag","Mittwoch","Donnerstag",
                                          "Freitag","Samstag","Sonntag"]
                        # Schwerpunkte aus Plan je Athletik-Tag sammeln
                        _ath_bereiche: list[str] = []
                        for _row in plan:
                            _rb = _row.get("bereich","")
                            if _rb and _rb not in _ath_bereiche:
                                _ath_bereiche.append(_rb)
                        _sp_str = " + ".join(_ath_bereiche[:3]) if _ath_bereiche else "Athletik"
                        _zeit_min = _av.get("trainingszeit_min", 60)
                        _total_w_wp = max((r["woche"] for r in plan), default=1)

                        for _wn in range(1, _total_w_wp + 1):
                            st.markdown(f"**— Woche {_wn} —**")
                            for _tag in _TAGE_ALLE_WV:
                                _ist_verein = _tag in _wp_verein_tage
                                _ist_spiel  = _tag in _wp_spiel_tage
                                _ist_ath    = _tag in _wp_ath_tage
                                if _ist_verein and _ist_ath:
                                    _lbl = "🏟️+🏋️ Vereinstraining + Athletik"
                                    _clr = "#e3b341"
                                elif _ist_verein:
                                    _lbl = "🏟️ Vereinstraining"
                                    _clr = "#58a6ff"
                                elif _ist_spiel:
                                    _lbl = ("🏆 Turnier / Spiel"
                                            if _wp_spielbel == "Turnier / mehrere Spiele"
                                            else "🏆 Spiel")
                                    _clr = "#f85149"
                                elif _ist_ath:
                                    _lbl = f"🏋️ APH Athletik · {_sp_str} · {_zeit_min} min"
                                    _clr = "#3fb950"
                                else:
                                    _lbl = "〇 Regeneration / frei"
                                    _clr = "#444d56"
                                st.markdown(
                                    f'<div style="display:flex;gap:10px;align-items:center;'
                                    f'padding:4px 0;border-bottom:1px solid #21262d">'
                                    f'<span style="color:#8b949e;font-size:12px;min-width:80px">'
                                    f'{_tag}</span>'
                                    f'<span style="color:{_clr};font-size:13px">{_lbl}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                            st.markdown("")
            except Exception:
                pass

        # ── PDF-Druck-Button ──────────────────────────────────────────────────
        _tv_alter   = berechne_alter(auswahl.get("geburtsdatum"))
        _tv_pg      = _alter_zu_plangruppe(_tv_alter)
        _tv_cfg     = _PLANGRUPPEN_CONFIG[_tv_pg]
        _tv_fki     = _fki(auswahl.get("geburtsdatum", ""))
        _tv_fk      = _tv_fki.get("fussballklasse") or "—"
        _tv_jk      = _jugendklasse(_tv_fk)
        _tv_sl      = _tv_fki.get("saison", "")
        _tv_pg_farben = {
            "U7": "#3fb950", "U8": "#3fb950",
            "U10": "#3fb950", "U14": "#3fb950", "U18": "#d29922",
            "Senior": "#58a6ff", "Ü40": "#d29922", "Ü55": "#f85149",
        }
        _tv_pg_clr  = _tv_pg_farben.get(_tv_pg, "#8b949e")
        _tv_alt_str = f" / {int(_tv_alter)} Jahre" if _tv_alter else ""
        # Legacy-APH-Fallback für PDF und Planansicht. Die konkrete Auswahl je
        # Tag wird weiterhin ausschließlich durch warmup_meta_lesen/details
        # aufgelöst.
        _zeit_soll = _av["trainingszeit_min"]
        _wu_min = _ZEITBUDGET_CONFIG.get(
            max(k for k in _ZEITBUDGET_CONFIG if k <= _zeit_soll),
            {"warmup_min": 10},
        )["warmup_min"]
        st.markdown(
            f'<div style="background:#161b22;border:2px solid {_tv_pg_clr};border-radius:8px;'
            f'padding:10px 16px;margin-bottom:12px">'
            f'<span style="font-size:13px;color:{_tv_pg_clr};font-weight:700">'
            f'🎯 Trainingsstufe: {_tv_pg}{_tv_alt_str}</span>'
            f'<span style="color:#8b949e;font-size:12px;margin-left:10px">— {_tv_cfg["label"]}</span><br>'
            f'<small style="color:#8b949e">'
            f'Fußballklasse: {_tv_fk} (Saison {_tv_sl}) · Jugendklasse: {_tv_jk}'
            f'</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.button("📄 PDF drucken", key="tp_pdf_btn", use_container_width=False):
            with st.spinner("Trainingsplan-PDF wird erstellt …"):
                try:
                    _tv_vereinsname = st.session_state.get("cfg_vereinsname", "")
                    # Aktive Version nutzen statt trainingsplan_laden() —
                    # stellt sicher dass das PDF exakt die angezeigte Version enthält
                    _tv_plan_raw = plan_laden_nach_version(_vid)
                    # Normalisiere zu dict-Liste mit einheitlichen Spaltennamen
                    _tv_plan_dicts = []
                    for _row in (_tv_plan_raw or []):
                        if isinstance(_row, (list, tuple)):
                            _keys = ["bereich","uebung","saetze","wiederholungen",
                                     "haeufigkeit","woche","tag","pause_sekunden","ausfuehrung"]
                            _tv_plan_dicts.append(dict(zip(_keys, list(_row) + [""]*9)))
                        else:
                            _tv_plan_dicts.append(_row)
                    _tv_pdf_bytes = generate_trainingsplan_pdf(
                        spieler             = auswahl,
                        plan_rows           = _tv_plan_dicts,
                        plangruppe          = _tv_pg,
                        plangruppen_config  = _tv_cfg,
                        alters_ersatz       = _ALTERS_ERSATZ,
                        vereinsname         = _tv_vereinsname,
                        version_nr          = _av.get("version_nr"),
                        plan_datum          = _av.get("datum", ""),
                        wochenplanung_json  = _av.get("wochenplanung_json"),
                        legacy_warmup_min   = _wu_min,
                    )
                    _tv_vorname  = (auswahl.get("vorname") or "").strip()
                    _tv_nachname = (auswahl.get("nachname") or auswahl.get("name") or "Spieler").strip()
                    _tv_filename = f"Trainingsplan_{_tv_vorname}_{_tv_nachname}_{_tv_pg}.pdf".replace(" ","_")
                    st.download_button(
                        label     = "⬇️ PDF herunterladen",
                        data      = _tv_pdf_bytes,
                        file_name = _tv_filename,
                        mime      = "application/pdf",
                        key       = "tp_pdf_download",
                    )
                    _save_ok(f"Trainingsplan-PDF erstellt — {len(_tv_pdf_bytes) // 1024} KB · Trainingsstufe: {_tv_pg}")
                except Exception as _tv_exc:
                    _save_err(f"PDF konnte nicht erstellt werden: {_tv_exc}")

        # ── Plan-Aktionen ─────────────────────────────────────────────────────
        st.markdown("---")
        _pac1, _pac2 = st.columns(2)
        if _pac1.button("📎 Plan duplizieren", key="dup_plan_btn", use_container_width=True,
                        help="Erstellt eine Kopie als neue Version. Original bleibt archiviert."):
            _dup_id = plan_duplizieren(sid, _vid, str(date.today()),
                                      st.session_state.get("username", ""))
            _save_ok("Plan dupliziert — neue Version ist jetzt aktiv.")
            st.rerun()
        if _pac2.button("🗂️ Als neue Version speichern", key="new_ver_btn", use_container_width=True,
                        help="Archiviert die aktuelle Version und startet eine neue mit denselben Übungen."):
            _nver_id = plan_duplizieren(sid, _vid, str(date.today()),
                                       st.session_state.get("username", ""))
            _save_ok("Neue Version erstellt — der bisherige Stand ist archiviert.")
            st.rerun()

        st.markdown("---")

        # ── Shared Konstanten ─────────────────────────────────────────────────
        _farbe_bereich = {
            "Hüfte": "#3b82f6", "Knie": "#3fb950", "Rumpf": "#d29922",
            "Sprunggelenk": "#a371f7", "Oberschenkel": "#f85149",
            "Schnelligkeit": "#58a6ff", "Explosivität": "#e3b341",
            "Agilität": "#56d364", "Fußball": "#ff7b72",
        }
        # _tag_namen: Im Vereinsbelastungs-Modus gewaehlte_athletik_tage verwenden,
        # sonst die bisherige Standardzuordnung (Spec §21, Nachbesserung).
        _tag_namen = {1:"Tag 1 — Montag", 2:"Tag 2 — Mittwoch", 3:"Tag 3 — Freitag",
                      4:"Tag 4 — Samstag", 0:"Alle Tage"}
        try:
            if _av_wp_json:
                import json as _json_tn
                _wp_tn = _json_tn.loads(_av_wp_json)
                _ath_tage_tn = _wp_tn.get("gewaehlte_athletik_tage") or []
                if _ath_tage_tn:
                    _tag_namen = {0: "Alle Tage"}
                    for _ti, _tw in enumerate(_ath_tage_tn, start=1):
                        _tag_namen[_ti] = f"Tag {_ti} — {_tw}"
        except Exception:
            pass  # Fallback: Standard-Zuordnung bleibt
        _BEREICHE_ALL = ["Sprunggelenk","Knie","Hüfte","Rumpf","Oberschenkel",
                         "Schnelligkeit","Explosivität","Agilität","Ausdauer","Fußball"]
        # ── Übungsplan mit interaktiver Bearbeitung ───────────────────────────
        alle_wochen = sorted(set(r["woche"] for r in plan))
        for woche_nr in alle_wochen:
            _is_deload = (woche_nr % 4 == 0)
            _woche_label = f"Woche {int(woche_nr)}" + (" — 🔄 Deload" if _is_deload else "")
            sub_w = [r for r in plan if r["woche"] == woche_nr]

            with st.expander(_woche_label, expanded=(woche_nr <= 2)):
                if _is_deload:
                    st.info("⬇️ **Deload-Woche:** Reduziertes Volumen und Intensität zur Regeneration. Technikfokus.")

                for tag_nr in sorted(set(r["tag"] for r in sub_w)):
                    _tag_label = _tag_namen.get(int(tag_nr), f"Tag {int(tag_nr)}")
                    sub_t = [r for r in sub_w if r["tag"] == tag_nr]
                    _warmup_row = next(
                        (row for row in sub_t if row.get("bereich") == WARMUP_BEREICH),
                        None,
                    )
                    _hauptteil_tag = [row for row in sub_t if row.get("bereich") != WARMUP_BEREICH]
                    _warmup_meta = warmup_meta_lesen(_warmup_row)
                    _warmup_aph_dauer = _warmup_meta.get("aph_dauer_min") or _wu_min
                    _warmup_info = warmup_details(
                        _warmup_meta["art"], _warmup_meta["level"], _warmup_meta["teile"],
                        aph_dauer_min=_warmup_aph_dauer,
                    )

                    # ── Dauer-Schätzung + Plausibilitätsprüfung ───────────────
                    _est_main = schaetze_tag_dauer_min(_hauptteil_tag)
                    _est_total = round(_est_main + _warmup_info["dauer_min"] + 5, 1)  # +5 min Cool-Down
                    _diff = round(_est_total - _zeit_soll, 1)
                    _dur_clr = "#3fb950" if abs(_diff) <= 5 else "#d29922" if abs(_diff) <= 15 else "#f85149"
                    _dur_icon = "✅" if abs(_diff) <= 5 else "⚠️" if abs(_diff) <= 15 else "🔴"

                    st.markdown(
                        f'<div style="background:#161b22;border-left:4px solid #1f6feb;'
                        f'border-radius:0 8px 8px 0;padding:8px 14px;margin:12px 0 4px;'
                        f'display:flex;justify-content:space-between;align-items:center">'
                        f'<span style="color:#58a6ff;font-weight:700;font-size:14px">🗓️ {_tag_label}</span>'
                        f'<span style="color:{_dur_clr};font-size:12px">'
                        f'{_dur_icon} ~{_est_total:.0f} min (Ziel: {_zeit_soll} min'
                        f'{f", +{_diff:.0f}" if _diff>5 else f", {_diff:.0f}" if _diff<-5 else ""}'
                        f')</span></div>',
                        unsafe_allow_html=True,
                    )
                    if _diff > 10:
                        st.caption(f"💡 Hinweis: Geplante Einheit überschreitet Trainingsziel um ca. {_diff:.0f} Minuten.")
                    elif _diff < -15:
                        st.caption(f"💡 Hinweis: Es sind noch ca. {-_diff:.0f} Minuten verfügbar.")

                    # ── Warm-Up Block: gespeicherte Auswahl oder Legacy-Fallback ──
                    _warmup_legacy = _warmup_meta.get("legacy", False)
                    _warmup_title = _warmup_info["titel"]
                    with st.expander(
                        f"🔥 Warm-up: {_warmup_title} (~{_warmup_info['dauer_min']} min)",
                        expanded=False,
                    ):
                        if _warmup_legacy:
                            st.caption("Legacy-Plan: APH Standard-Warm-up wird angezeigt, bis eine Auswahl gespeichert wird.")
                        if _warmup_info["hinweis"]:
                            st.caption(_warmup_info["hinweis"])
                        if _warmup_info["zeilen"]:
                            st.dataframe(
                                pd.DataFrame([
                                    {
                                        "Teil": row["teil"],
                                        "Übung": row["uebung"],
                                        "Volumen": row["volumen"],
                                        "Hinweis": row["hinweis"],
                                    }
                                    for row in _warmup_info["zeilen"]
                                ]),
                                use_container_width=True, hide_index=True,
                            )
                        else:
                            st.info("Für diesen Trainingstag ist kein Warm-up eingeplant.")

                        st.markdown("##### Warm-up auswählen")
                        _wu_current_art = _warmup_meta["art"]
                        _wu_art_index = (WARMUP_OPTIONEN.index(_wu_current_art)
                                         if _wu_current_art in WARMUP_OPTIONEN else 0)
                        _wu_art = st.radio(
                            "Programm",
                            WARMUP_OPTIONEN,
                            index=_wu_art_index,
                            horizontal=True,
                            key=f"warmup_art_{woche_nr}_{tag_nr}",
                        )
                        _wu_level = _warmup_meta["level"]
                        _wu_teile = list(_warmup_meta["teile"])
                        if _wu_art in (FIFA_KOMPLETT, FIFA_INDIVIDUELL):
                            _wu_level = st.selectbox(
                                "FIFA 11+ · Teil 2 Level",
                                [1, 2, 3],
                                index=max(0, min(2, int(_wu_level) - 1)),
                                key=f"warmup_level_{woche_nr}_{tag_nr}",
                                help="Das Level wird ausschließlich durch den Trainer gewählt.",
                            )
                            if _wu_art == FIFA_INDIVIDUELL:
                                st.caption("Nur „FIFA 11+ komplett“ enthält alle drei Teile.")
                                _wu_teile = st.multiselect(
                                    "FIFA-11+-Teile",
                                    FIFA_TEILE,
                                    default=_wu_teile,
                                    key=f"warmup_parts_{woche_nr}_{tag_nr}",
                                )
                            else:
                                _wu_teile = list(FIFA_TEILE)

                        _wu_scope = st.radio(
                            "Anwenden auf",
                            ["Nur diesen Woche-/Tag-Block", "Auf weitere Wochen / Trainingstage"],
                            horizontal=True,
                            key=f"warmup_scope_{woche_nr}_{tag_nr}",
                        )
                        _wu_target_weeks = [int(woche_nr)]
                        _wu_target_tage = [int(tag_nr)]
                        if _wu_scope == "Auf weitere Wochen / Trainingstage":
                            _wu_quick_options = ["Benutzerdefiniert", "Nur aktuelle Woche", "Alle Wochen"]
                            if len(alle_wochen) >= 4:
                                _wu_quick_options.append("Wochen 1–4")
                            if len(alle_wochen) >= 6:
                                _wu_quick_options.append("Wochen 1–6")
                            if len(alle_wochen) >= 8:
                                _wu_quick_options.append("Wochen 1–8")
                            _wu_quick = st.selectbox(
                                "Schnellwahl Wochen",
                                _wu_quick_options,
                                key=f"warmup_quick_{woche_nr}_{tag_nr}",
                            )
                            if _wu_quick == "Nur aktuelle Woche":
                                _wu_target_weeks = [int(woche_nr)]
                            elif _wu_quick == "Alle Wochen":
                                _wu_target_weeks = list(alle_wochen)
                            elif _wu_quick.startswith("Wochen 1–"):
                                _wu_limit = int(_wu_quick.rsplit("–", 1)[1])
                                _wu_target_weeks = [w for w in alle_wochen if int(w) <= _wu_limit]
                            else:
                                _wu_target_weeks = st.multiselect(
                                    "Planwochen",
                                    alle_wochen,
                                    default=[int(woche_nr)],
                                    format_func=lambda w: f"Woche {w}",
                                    key=f"warmup_weeks_{woche_nr}_{tag_nr}",
                                )
                            _wu_target_tage = st.multiselect(
                                "Trainingstage",
                                sorted({int(row["tag"]) for row in plan}),
                                default=[int(tag_nr)],
                                format_func=lambda t: _tag_namen.get(t, f"Tag {t}"),
                                key=f"warmup_days_{woche_nr}_{tag_nr}",
                            )

                        if st.button(
                            "💾 Warm-up speichern",
                            key=f"warmup_save_{woche_nr}_{tag_nr}",
                            use_container_width=True,
                        ):
                            if _wu_art == FIFA_INDIVIDUELL and not _wu_teile:
                                st.error("Für FIFA 11+ individuell bitte mindestens einen Teil auswählen.")
                            elif not _wu_target_weeks or not _wu_target_tage:
                                st.error("Bitte mindestens eine Planwoche und einen Trainingstag auswählen.")
                            else:
                                _saved = 0
                                for _wu_week in _wu_target_weeks:
                                    for _wu_day in _wu_target_tage:
                                        if plan_warmup_speichern(
                                            sid, _vid, int(_wu_week), int(_wu_day),
                                            _wu_art, int(_wu_level), list(_wu_teile),
                                            aph_dauer_min=_wu_min,
                                        ):
                                            _saved += 1
                                _save_ok(f"Warm-up für {_saved} Woche-/Tag-Block{'' if _saved == 1 else 's'} gespeichert.")
                                st.rerun()

                    # ── Hauptteil: Bereiche + per-Übung Editing ───────────────
                    for breich in sorted(set(r["bereich"] for r in _hauptteil_tag)):
                        _clr = _farbe_bereich.get(breich, "#8b949e")
                        st.markdown(
                            f'<div style="font-size:12px;font-weight:700;color:{_clr};'
                            f'margin:10px 0 4px;border-left:3px solid {_clr};padding-left:8px">'
                            f'{breich}</div>',
                            unsafe_allow_html=True,
                        )
                        entries_b = [r for r in _hauptteil_tag if r["bereich"] == breich]

                        for idx_e, entry in enumerate(entries_b):
                            eid        = entry["id"]
                            _edit_key  = f"tv_edit_{eid}"
                            _del_key   = f"tv_del_{eid}"
                            _swap_key  = f"tv_swap_{eid}"
                            _dist_key  = f"tv_distribute_{eid}"

                            # ── Lösch-Bestätigung ──────────────────────────────
                            if st.session_state.get(_del_key):
                                st.warning(
                                    f"🗑️ Übung **'{entry['uebung']}'** aus diesem Trainingsplan entfernen? "
                                    f"*(Die Übung bleibt in der Trainingsbibliothek.)*"
                                )
                                _dc1, _dc2 = st.columns(2)
                                if _dc1.button("✅ Ja, entfernen", key=f"del_yes_{eid}",
                                               type="primary", use_container_width=True):
                                    plan_eintrag_loeschen(eid)
                                    st.session_state.pop(_del_key, None)
                                    st.rerun()
                                if _dc2.button("✕ Abbrechen", key=f"del_no_{eid}",
                                               use_container_width=True):
                                    st.session_state.pop(_del_key, None)
                                    st.rerun()

                            # ── Bearbeitungsformular ───────────────────────────
                            elif st.session_state.get(_edit_key):
                                _EIGENE_EDIT = "✏️ Eigene Übung eingeben..."
                                _e_bereich_key = f"edit_bereich_{eid}"
                                _e_uebung_key = f"edit_uebung_{eid}"
                                _e_custom_key = f"edit_uebung_custom_{eid}"
                                if _e_bereich_key not in st.session_state:
                                    st.session_state[_e_bereich_key] = (
                                        breich if breich in _BEREICHE_ALL else _BEREICHE_ALL[0]
                                    )
                                if _e_custom_key not in st.session_state:
                                    st.session_state[_e_custom_key] = str(entry["uebung"])

                                # Außerhalb des Forms, damit ein Bereichswechsel den
                                # Katalog sofort aktualisiert und noch nichts speichert.
                                _ef1, _ef2 = st.columns(2)
                                _e_bereich = _ef1.selectbox(
                                    "Bereich",
                                    _BEREICHE_ALL,
                                    key=_e_bereich_key,
                                )
                                _e_katalog = katalog_uebungen_fuer_bereich(_e_bereich, _tv_pg)
                                _e_optionen = _e_katalog + [_EIGENE_EDIT]
                                if _e_uebung_key not in st.session_state:
                                    st.session_state[_e_uebung_key] = (
                                        entry["uebung"]
                                        if entry["uebung"] in _e_katalog
                                        else _EIGENE_EDIT
                                    )
                                elif st.session_state[_e_uebung_key] not in _e_optionen:
                                    st.session_state[_e_uebung_key] = _EIGENE_EDIT
                                _e_auswahl = _ef2.selectbox(
                                    "Übungsname",
                                    _e_optionen,
                                    key=_e_uebung_key,
                                    help="Katalogübungen passen sich dem gewählten Bereich an.",
                                )
                                if _e_auswahl == _EIGENE_EDIT:
                                    _e_uebung = st.text_input(
                                        "Eigene Übung eingeben",
                                        key=_e_custom_key,
                                        placeholder="z. B. Reverse Lunge mit Rotation",
                                    )
                                else:
                                    _e_uebung = _e_auswahl

                                with st.form(f"form_edit_{eid}", border=True):
                                    _ef3, _ef4, _ef5 = st.columns(3)
                                    _e_saetze = _ef3.text_input("Sätze", value=str(entry["saetze"]))
                                    _e_wdh    = _ef4.text_input("Wdh. / Dauer", value=str(entry["wiederholungen"]))
                                    _e_haeuf  = _ef5.text_input("Häufigkeit", value=str(entry["haeufigkeit"]))
                                    _ef6, _ef7, _ef8 = st.columns(3)
                                    _e_pause  = _ef6.number_input("Pause (s)", min_value=0, max_value=600,
                                                                   value=int(entry["pause_sekunden"]))
                                    _e_rpe    = _ef7.number_input("RPE", min_value=1, max_value=10,
                                                                   value=int(entry["rpe"]))
                                    _e_equip  = _ef8.text_input("Equipment", value=str(entry["equipment"]))
                                    _e_ausfuehrung = st.text_area(
                                        "Ausführung / Traineranweisung",
                                        value=str(entry.get("ausfuehrung") or ""),
                                        height=80,
                                        help="Die konkrete Ausführung gilt nur für diesen Plan-Eintrag.",
                                    )
                                    _ef9, _ef10 = st.columns(2)
                                    _e_woche = _ef9.selectbox(
                                        "Woche",
                                        alle_wochen,
                                        index=alle_wochen.index(entry["woche"]) if entry["woche"] in alle_wochen else 0,
                                        format_func=lambda w: f"Woche {w}",
                                    )
                                    _e_tag = _ef10.selectbox(
                                        "Trainingstag",
                                        sorted({int(row["tag"]) for row in plan}),
                                        index=sorted({int(row["tag"]) for row in plan}).index(int(entry["tag"])),
                                        format_func=lambda t: _tag_namen.get(t, f"Tag {t}"),
                                    )
                                    _e_notiz  = st.text_area("Notiz (Plan-spezifisch)", value=entry.get("notiz",""),
                                                             height=60,
                                                             help="Diese Notiz gilt nur für diesen Plan — die Bibliotheksübung bleibt unverändert.")
                                    _fe_save, _fe_cancel = st.columns(2)
                                    if _fe_save.form_submit_button("💾 Speichern", type="primary",
                                                                    use_container_width=True):
                                        plan_eintrag_aktualisieren(
                                            eid,
                                            uebung=_e_uebung, bereich=_e_bereich,
                                            saetze=_e_saetze, wiederholungen=_e_wdh,
                                            haeufigkeit=_e_haeuf,
                                            pause_sekunden=int(_e_pause),
                                            ausfuehrung=_e_ausfuehrung,
                                            rpe=int(_e_rpe), equipment=_e_equip,
                                            woche=int(_e_woche), tag=int(_e_tag),
                                            notiz=_e_notiz,
                                        )
                                        st.session_state.pop(_edit_key, None)
                                        for _e_state_key in (_e_bereich_key, _e_uebung_key, _e_custom_key):
                                            st.session_state.pop(_e_state_key, None)
                                        _save_ok(f"Übung '{_e_uebung}' aktualisiert.")
                                        st.rerun()
                                    if _fe_cancel.form_submit_button("✕ Abbrechen",
                                                                      use_container_width=True):
                                        st.session_state.pop(_edit_key, None)
                                        for _e_state_key in (_e_bereich_key, _e_uebung_key, _e_custom_key):
                                            st.session_state.pop(_e_state_key, None)
                                        st.rerun()

                            # ── Übung einplanen / verteilen ─────────────────────
                            elif st.session_state.get(_dist_key):
                                st.markdown(f"**📅 Übung einplanen / verteilen** — *{entry['uebung']}*")
                                with st.form(f"form_distribute_{eid}", border=True):
                                    _dist_mode = st.radio(
                                        "Aktion",
                                        ["Auf ausgewählte Tage / Wochen kopieren", "An einen anderen Tag / eine andere Woche verschieben"],
                                        help="Kopieren ist der Standard: Der ursprüngliche Eintrag bleibt unverändert.",
                                    )
                                    _quick_options = ["Benutzerdefiniert", "Nur aktuelle Woche", "Alle Wochen"]
                                    if len(alle_wochen) >= 4:
                                        _quick_options.append("Wochen 1–4")
                                    if len(alle_wochen) >= 6:
                                        _quick_options.append("Wochen 1–6")
                                    if len(alle_wochen) >= 8:
                                        _quick_options.append("Wochen 1–8")
                                    _dist_quick = st.selectbox("Schnellwahl Wochen", _quick_options)
                                    if _dist_quick == "Nur aktuelle Woche":
                                        _dist_weeks = [int(entry["woche"])]
                                    elif _dist_quick == "Alle Wochen":
                                        _dist_weeks = list(alle_wochen)
                                    elif _dist_quick.startswith("Wochen 1–"):
                                        _dist_cap = int(_dist_quick.rsplit("–", 1)[1])
                                        _dist_weeks = [w for w in alle_wochen if int(w) <= _dist_cap]
                                    else:
                                        _dist_weeks = st.multiselect(
                                            "Planwochen",
                                            alle_wochen,
                                            default=[int(entry["woche"])],
                                            format_func=lambda w: f"Woche {w}",
                                        )
                                    _dist_days = st.multiselect(
                                        "Trainingstage",
                                        sorted({int(row["tag"]) for row in plan}),
                                        default=[int(entry["tag"])],
                                        format_func=lambda t: _tag_namen.get(t, f"Tag {t}"),
                                    )
                                    _distribution_count = len(_dist_weeks) * len(_dist_days)
                                    if _dist_mode.startswith("Auf ausgewählte") and _distribution_count >= 8:
                                        st.warning(
                                            "⚠️ Diese Übung wird für viele Trainingseinheiten eingeplant. "
                                            "Bitte Belastung und Regeneration prüfen."
                                        )
                                    _dist_save, _dist_cancel = st.columns(2)
                                    if _dist_save.form_submit_button("📅 Anwenden", type="primary", use_container_width=True):
                                        if not _dist_weeks or not _dist_days:
                                            st.error("Bitte mindestens eine Woche und einen Trainingstag auswählen.")
                                        elif _dist_mode.startswith("An einen"):
                                            if len(_dist_weeks) != 1 or len(_dist_days) != 1:
                                                st.error("Verschieben ist bewusst nur auf genau einen Woche-/Tag-Block möglich. Für mehrere Ziele bitte kopieren.")
                                            else:
                                                plan_eintrag_aktualisieren(
                                                    eid, woche=int(_dist_weeks[0]), tag=int(_dist_days[0])
                                                )
                                                st.session_state.pop(_dist_key, None)
                                                _save_ok("Übung verschoben.")
                                                st.rerun()
                                        else:
                                            _result = plan_eintrag_verteilen(
                                                sid, _vid, eid, list(_dist_weeks), list(_dist_days)
                                            )
                                            st.session_state.pop(_dist_key, None)
                                            if _result["erstellt"]:
                                                _freq_note = f" · Häufigkeit: {_result['haeufigkeit']}" if _result["haeufigkeit"] else ""
                                                _skip_note = f" · {_result['duplikate']} Duplikat(e) übersprungen" if _result["duplikate"] else ""
                                                _save_ok(f"{_result['erstellt']} Kopie(n) eingeplant{_freq_note}{_skip_note}.")
                                            elif _result["duplikate"]:
                                                st.warning("Alle ausgewählten Kombinationen enthalten diese Übung bereits. Keine Duplikate erzeugt.")
                                            else:
                                                st.info("Der ursprüngliche Eintrag liegt bereits im ausgewählten Woche-/Tag-Block.")
                                            st.rerun()
                                    if _dist_cancel.form_submit_button("✕ Abbrechen", use_container_width=True):
                                        st.session_state.pop(_dist_key, None)
                                        st.rerun()

                            # ── Übung austauschen ──────────────────────────────
                            elif st.session_state.get(_swap_key):
                                st.markdown(f"**↕️ Übung austauschen** — aktuell: *{entry['uebung']}*")
                                _sw_b_sel = st.selectbox("Bereich für Alternative",
                                                         _BEREICHE_ALL,
                                                         index=_BEREICHE_ALL.index(breich) if breich in _BEREICHE_ALL else 0,
                                                         key=f"swap_bereich_{eid}")
                                _EQUIPMENT_ALLE_SWAP = [
                                    "Körpergewicht", "Miniband", "Powerband", "Freie Gewichte",
                                    "Kurzhanteln", "Langhanteln", "Kettlebell", "Medizinball",
                                    "Maschine", "Schlitten", "Ball",
                                ]
                                _swap_equip = st.multiselect(
                                    "Equipment-Filter (optional)",
                                    _EQUIPMENT_ALLE_SWAP,
                                    default=list(st.session_state.get("equip_sel", [])),
                                    key=f"swap_equip_{eid}",
                                    help="Nur Übungen mit passendem Equipment anzeigen. Leer = alle.",
                                )
                                _sw_pool = katalog_uebungen_fuer_bereich(
                                    _sw_b_sel, _tv_pg, _swap_equip
                                )
                                _EIGENE_SW = "✏️ Eigene Übung eingeben…"
                                _sw_sel = st.selectbox(
                                    "Alternative auswählen", _sw_pool + [_EIGENE_SW],
                                    key=f"swap_sel_{eid}",
                                    help="Ähnliche Übungen aus dem gleichen Bereich stehen oben.",
                                )
                                if _sw_sel == _EIGENE_SW:
                                    _sw_custom = st.text_input("Eigene Übung eingeben",
                                                               key=f"swap_custom_{eid}")
                                    _sw_uebung = _sw_custom
                                else:
                                    _sw_uebung = _sw_sel
                                _sw_c1, _sw_c2 = st.columns(2)
                                if _sw_c1.button("✅ Übernehmen", key=f"swap_ok_{eid}",
                                                 type="primary", use_container_width=True):
                                    if _sw_uebung:
                                        plan_eintrag_aktualisieren(eid, uebung=_sw_uebung,
                                                                   bereich=_sw_b_sel)
                                        st.session_state.pop(_swap_key, None)
                                        _save_ok(f"Übung ausgetauscht: '{entry['uebung']}' → '{_sw_uebung}'")
                                        st.rerun()
                                if _sw_c2.button("✕ Abbrechen", key=f"swap_cancel_{eid}",
                                                 use_container_width=True):
                                    st.session_state.pop(_swap_key, None)
                                    st.rerun()

                            # ── Normalansicht mit Aktions-Buttons ─────────────
                            else:
                                _rpe_v    = int(entry.get("rpe", 7))
                                _rpe_icon = "🟢" if _rpe_v<=5 else "🟡" if _rpe_v<=7 else "🔴"
                                _abgehakt = bool(entry.get("abgehakt", 0))
                                _rc1, _rc2, _rc3 = st.columns([1, 5, 4])

                                # Abgehakt-Checkbox
                                _new_ahk = _rc1.checkbox("", value=_abgehakt,
                                                          key=f"ahk_{eid}",
                                                          help="Durchgeführt")
                                if _new_ahk != _abgehakt:
                                    plan_eintrag_aktualisieren(eid, abgehakt=int(_new_ahk))
                                    st.rerun()

                                _uebung_anzeige = ("~~" + entry["uebung"] + "~~"
                                                   if _abgehakt else entry["uebung"])
                                _rc2.markdown(
                                    f"**{_uebung_anzeige}**  \n"
                                    f"<span style='color:#8b949e;font-size:11px'>"
                                    f"{entry['saetze']} Sätze · {entry['wiederholungen']} · "
                                    f"Pause {entry['pause_sekunden']}s · RPE {_rpe_v} {_rpe_icon} · "
                                    f"{entry['equipment']}</span>"
                                    + (f"<br><span style='color:#58a6ff;font-size:11px'>💬 {entry['notiz']}</span>"
                                       if entry.get("notiz") else ""),
                                    unsafe_allow_html=True,
                                )

                                with _rc3:
                                    _bc1, _bc2, _bc3, _bc4, _bc5, _bc6 = st.columns(6)
                                    if _bc1.button("✏️", key=f"edit_btn_{eid}", help="Bearbeiten"):
                                        st.session_state[_edit_key] = True
                                        st.rerun()
                                    if _bc2.button("🗑️", key=f"del_btn_{eid}", help="Löschen"):
                                        st.session_state[_del_key] = True
                                        st.rerun()
                                    if _bc3.button("↕️", key=f"swap_btn_{eid}", help="Austauschen"):
                                        st.session_state[_swap_key] = True
                                        st.rerun()
                                    if _bc4.button("📅", key=f"dist_btn_{eid}", help="Übung einplanen / verteilen"):
                                        st.session_state[_dist_key] = True
                                        st.rerun()
                                    # Reihenfolge: Hoch/Runter
                                    _prev_entry = entries_b[idx_e-1] if idx_e > 0 else None
                                    _next_entry = entries_b[idx_e+1] if idx_e < len(entries_b)-1 else None
                                    if _bc5.button("⬆", key=f"up_btn_{eid}", help="Nach oben",
                                                   disabled=_prev_entry is None):
                                        if _prev_entry:
                                            plan_eintraege_position_tauschen(eid, _prev_entry["id"])
                                            st.rerun()
                                    if _bc6.button("⬇", key=f"dn_btn_{eid}", help="Nach unten",
                                                   disabled=_next_entry is None):
                                        if _next_entry:
                                            plan_eintraege_position_tauschen(eid, _next_entry["id"])
                                            st.rerun()

                    # ── Übung aus Bibliothek hinzufügen (pro Tag) ─────────────
                    with st.expander(f"➕ Übung zu {_tag_label} hinzufügen", expanded=False):
                        _add_c1, _add_c2 = st.columns(2)
                        _add_bereich = _add_c1.selectbox("Bereich", _BEREICHE_ALL,
                                                         key=f"add_b_{woche_nr}_{tag_nr}")
                        _add_pool: list[str] = []
                        for _pk in ["stabilisation","kraft","power"]:
                            for _u, *_ in _POOL.get(_add_bereich,{}).get(_pk,[]):
                                if _u not in _add_pool:
                                    _add_pool.append(_u)
                        _EIGENE_ADD = "✏️ Eigene Übung eingeben…"
                        _add_ub_sel = _add_c2.selectbox("Übung", _add_pool + [_EIGENE_ADD],
                                                         key=f"add_ub_{woche_nr}_{tag_nr}")
                        if _add_ub_sel == _EIGENE_ADD:
                            _add_uebung = st.text_input("Eigene Übung", placeholder="z. B. Lateral Band Walk",
                                                        key=f"add_custom_{woche_nr}_{tag_nr}")
                        else:
                            _add_uebung = _add_ub_sel
                        _add_d1, _add_d2, _add_d3 = st.columns(3)
                        _add_saetze = _add_d1.text_input("Sätze", "3", key=f"add_s_{woche_nr}_{tag_nr}")
                        _add_wdh    = _add_d2.text_input("Wdh.", "10", key=f"add_w_{woche_nr}_{tag_nr}")
                        _add_haeuf  = _add_d3.text_input("Häufigkeit", "2×/Woche",
                                                          key=f"add_h_{woche_nr}_{tag_nr}")
                        if st.button("➕ Hinzufügen", key=f"add_btn_{woche_nr}_{tag_nr}",
                                     use_container_width=True, type="primary"):
                            if _add_uebung:
                                trainingsplan_eintrag_speichern(
                                    sid, str(date.today()), woche_nr,
                                    _add_bereich, _add_uebung, _add_saetze, _add_wdh, _add_haeuf,
                                    tag=tag_nr, plan_id=_vid,
                                )
                                _save_ok(f"Übung '{_add_uebung}' zu {_tag_label} hinzugefügt.")
                                st.rerun()

                    # ── Cool-Down ─────────────────────────────────────────────
                    st.caption(
                        "🧘 **Cool-Down (5 min):** Stretching der trainierten Muskelgruppen — "
                        "Hüftbeuger, Oberschenkel, Rumpf."
                    )

        # ── Trainer-Notizen ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📝 Trainer-Notizen")
        _notizen_val = _av.get("notizen","")
        _notizen_new = st.text_area("Notizen zu diesem Trainingsplan", value=_notizen_val,
                                    height=120, key="plan_notizen_ta",
                                    placeholder="Trainingsziele, Beobachtungen, besondere Hinweise…")
        _ns1, _ns2 = st.columns(2)
        if _ns1.button("💾 Notizen speichern", key="save_notizen_btn", use_container_width=True):
            plan_notizen_speichern(_vid, _notizen_new)
            _save_ok("Notizen gespeichert.")
            st.rerun()
        if _ns2.button("✕ Verwerfen", key="discard_notizen_btn", use_container_width=True):
            st.rerun()

        # ── Plan-Historie (Spec §6) ───────────────────────────────────────────
        _versionen = plan_versionen_laden(sid)
        _archiviert = [v for v in _versionen if v["status"] == "ARCHIVIERT"]
        if _archiviert:
            st.markdown("---")
            with st.expander(f"🗂️ Frühere Trainingspläne ({len(_archiviert)} archiviert)", expanded=False):
                for _av_hist in _archiviert:
                    _hist_plan = plan_laden_nach_version(_av_hist["id"])
                    _hist_n    = len(_hist_plan)
                    _hist_w    = max((r["woche"] for r in _hist_plan), default=0)
                    _h_c1, _h_c2 = st.columns([3, 2])
                    _h_c1.markdown(
                        f"**Plan #{_av_hist['version_nr']:03d}** — {_av_hist['datum']}  \n"
                        f"<span style='color:#8b949e;font-size:11px'>"
                        f"{_av_hist['modus']}-Modus · {_hist_n} Übungen · {_hist_w} Wochen · "
                        f"{_av_hist['trainingszeit_min']} min/Einheit</span>",
                        unsafe_allow_html=True,
                    )
                    if _h_c2.button("📋 Anzeigen / Als Basis nutzen",
                                    key=f"hist_dup_{_av_hist['id']}",
                                    use_container_width=True):
                        plan_duplizieren(sid, _av_hist["id"], str(date.today()),
                                        st.session_state.get("username",""))
                        _save_ok(f"Plan #{_av_hist['version_nr']:03d} wurde als neue aktive Version dupliziert.")
                        st.rerun()
                    if _av_hist.get("notizen"):
                        st.caption(f"📝 {_av_hist['notizen'][:120]}…" if len(_av_hist["notizen"])>120
                                   else f"📝 {_av_hist['notizen']}")
                    st.markdown('<hr style="border-color:#30363d;margin:6px 0">', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────

def page_periodisierung():
    st.markdown("# 🔄 Periodisierungsplan")
    st.markdown("Regelbasierter Athletik-Zyklus: Defizit-gewichtet · Multi-Fokus pro Woche · Progressive Belastungssteuerung")
    _inline_spielerwechsel("training")

    auswahl = _player_selector("perio")
    if not auswahl:
        return

    sid    = auswahl["id"]
    fms    = fms_letzter(sid)
    y      = y_balance_letzter(sid)
    sprint = sprint_letzter(sid)
    sprung = sprung_letzter(sid)
    agil   = agilitaet_letzter(sid)
    aus    = ausdauer_letzter(sid)
    kraft  = kraft_letzter(sid)
    _spiro_perio = spiro_test_letzter(sid)
    schwerpunkt  = trainingsbereich_scores_ermitteln(
        fms, y, sprint, sprung, agil, aus, kraft_row=kraft,
        spiro_row=_spiro_perio, geschlecht=auswahl.get("geschlecht", "Männlich"),
    )

    # Erhaltungstraining-Modus: Tests vorhanden, keine Defizite → ERHALTUNGS_SCHWERPUNKT
    _perio_tests_vorhanden = any([fms, y, sprint, sprung, agil, aus, kraft, _spiro_perio])
    if _perio_tests_vorhanden and not schwerpunkt:
        schwerpunkt = ERHALTUNGS_SCHWERPUNKT
        st.markdown(
            f'<div style="background:#0d2415;border:1px solid #3fb950;border-radius:10px;'
            f'padding:12px 16px;margin-bottom:16px">'
            f'<span style="color:#3fb950;font-weight:700">✅ Unauffällige Diagnostik</span>'
            f'<span style="color:#8b949e;font-size:12px;margin-left:8px">— Trainingsmodus: Leistung erhalten und weiterentwickeln</span></div>',
            unsafe_allow_html=True,
        )

    # ── Deficit summary ───────────────────────────────────────────────────────
    defizite = defizit_tabelle(schwerpunkt)
    if defizite:
        st.markdown("#### 🔍 Defizit-Analyse")
        _d_cols = st.columns(min(len(defizite), 4))
        _farben = {"🔴 Primär": "#f85149", "🟡 Sekundär": "#d29922", "🟢 Tertiär": "#3fb950"}
        for i, d in enumerate(defizite):
            _clr = _farben.get(d["Priorität"], "#8b949e")
            _d_cols[i % len(_d_cols)].markdown(
                f'<div style="background:#161b22;border:2px solid {_clr};border-radius:8px;'
                f'padding:8px 12px;margin-bottom:6px;text-align:center">'
                f'<div style="font-size:16px">{d["Priorität"].split()[0]}</div>'
                f'<div style="font-weight:700;color:#e6edf3;font-size:13px">{d["Bereich"]}</div>'
                f'<div style="color:{_clr};font-size:11px">{d["Volumen/Woche"]}/Woche</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("ℹ️ Keine Testdaten — Standard-Basisplan wird erstellt.")

    st.markdown("---")
    col_info, col_gen = st.columns([3, 2])
    with col_info:
        wochen_auswahl = st.selectbox(
            "Planlänge",
            [4, 8, 12],
            index=2,
            format_func=lambda x: f"{x} Wochen",
            key="perio_wochen",
        )
        if wochen_auswahl == 4:
            st.markdown("**Phase 1** (W1–4): Stabilisation & Bewegungsqualität")
        elif wochen_auswahl == 8:
            st.markdown("**Phase 1** (W1–4): Stabilisation  \n**Phase 2** (W5–8): Kraftaufbau")
        else:
            st.markdown(
                "**Phase 1** (W1–4): Stabilisation  \n"
                "**Phase 2** (W5–8): Kraftaufbau  \n"
                "**Phase 3** (W9–12): Fußballspezifisch"
            )
        st.caption("Jede 4. Woche = Deload · Jede Woche = mehrere Trainingsschwerpunkte")
    # Altersgruppe ermitteln
    _pz_alter = berechne_alter(auswahl.get("geburtsdatum"))
    _pz_pg    = _alter_zu_plangruppe(_pz_alter)
    _pz_cfg   = _PLANGRUPPEN_CONFIG[_pz_pg]
    _pg_farben2 = {
        "U7": "#3fb950", "U8": "#3fb950",
        "U10": "#3fb950", "U14": "#3fb950", "U18": "#d29922",
        "Senior": "#58a6ff", "Ü40": "#d29922", "Ü55": "#f85149",
    }
    _pg_clr2 = _pg_farben2.get(_pz_pg, "#8b949e")

    with col_info:
        st.markdown(
            f'<div style="background:#161b22;border:2px solid {_pg_clr2};border-radius:8px;'
            f'padding:8px 14px;margin-top:8px">'
            f'<span style="color:{_pg_clr2};font-weight:700;font-size:13px">🎯 {_pz_pg}</span>'
            f'<span style="color:#8b949e;font-size:11px;margin-left:8px">{_pz_cfg["label"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Zyklus erstellen / neu generieren", use_container_width=True, key="perio_gen"):
            zyklus_erstellen(sid, schwerpunkt, wochen=wochen_auswahl, alter=_pz_alter)
            _save_ok(f"{wochen_auswahl}-Wochen-Zyklus generiert! ({_pz_pg})")
            st.rerun()

    plan = zyklus_laden(sid)
    if not plan:
        st.info("Noch kein Periodisierungsplan vorhanden. Klicke auf **Zyklus erstellen**.")
        return

    df = pd.DataFrame(plan)
    df.columns = ["Woche", "Phase", "Ziel", "Bereich", "Übung", "Intensität", "Volumen", "Häufigkeit"]

    # Statistik-Header
    _pi1, _pi2, _pi3, _pi4 = st.columns(4)
    _pi1.metric("Wochen", int(df["Woche"].max()))
    _pi2.metric("Übungen gesamt", len(df))
    _pi3.metric("Bereiche", df["Bereich"].nunique())
    _pi4.metric("Phasen", df["Phase"].str.split("(").str[0].str.strip().nunique())
    st.markdown("---")

    # Phase colour map — match on prefix (new format includes week type in parens)
    _phase_defs = [
        ("Phase 1 — Stabilisation",    "#1f6feb"),
        ("Phase 2 — Kraftaufbau",       "#3fb950"),
        ("Phase 3 — Fußballspezifisch", "#d29922"),
        # Short plans (4/8 wk) may use generic phase names
        ("Stabilisation",               "#1f6feb"),
        ("Kraftaufbau",                 "#3fb950"),
    ]
    _seen_phases: set = set()

    _farbe_bereich = {
        "Hüfte": "#3b82f6", "Knie": "#3fb950", "Rumpf": "#d29922",
        "Sprunggelenk": "#a371f7", "Oberschenkel": "#f85149",
        "Schnelligkeit": "#58a6ff", "Explosivität": "#e3b341",
        "Agilität": "#56d364", "Fußball": "#ff7b72",
    }

    # Group by leading phase name (strip the "(Woche-Typ)" suffix)
    df["_PhaseGroup"] = df["Phase"].str.extract(r"^(Phase \d+ — [^(]+|[^(]+)", expand=False).str.strip()

    for phase_prefix, color in _phase_defs:
        sub = df[df["_PhaseGroup"].str.startswith(phase_prefix)]
        if sub.empty or phase_prefix in _seen_phases:
            continue
        _seen_phases.add(phase_prefix)
        weeks = sorted(sub["Woche"].unique())
        _ziel = sub.iloc[0]["Ziel"]
        st.markdown(
            f'<div style="border-left:4px solid {color};padding-left:12px;margin:20px 0 8px">'
            f'<h4 style="color:{color};margin:0 0 2px">{phase_prefix}</h4>'
            f'<small style="color:#8b949e">Wochen {weeks[0]}–{weeks[-1]} · {_ziel}</small></div>',
            unsafe_allow_html=True,
        )
        for woche_nr in weeks:
            _is_deload = (woche_nr % 4 == 0)
            _woche_typ = sub[sub["Woche"] == woche_nr]["Phase"].iloc[0]
            _typ_label = _woche_typ.split("(")[-1].rstrip(")") if "(" in _woche_typ else ""
            _exp_label = f"Woche {woche_nr}" + (f" — {_typ_label}" if _typ_label else "")
            w_sub = sub[sub["Woche"] == woche_nr]
            with st.expander(_exp_label, expanded=(woche_nr == weeks[0])):
                if _is_deload:
                    st.caption("⬇️ Deload-Woche: reduziertes Volumen zur aktiven Regeneration")
                for breich in sorted(w_sub["Bereich"].unique()):
                    _clr = _farbe_bereich.get(breich, "#8b949e")
                    st.markdown(
                        f'<div style="font-size:12px;font-weight:700;color:{_clr};'
                        f'border-left:3px solid {_clr};padding-left:8px;margin:6px 0 2px">{breich}</div>',
                        unsafe_allow_html=True,
                    )
                    _b_sub = w_sub[w_sub["Bereich"] == breich][["Übung", "Intensität", "Volumen", "Häufigkeit"]]
                    st.dataframe(_b_sub, use_container_width=True, hide_index=True)

    # Download plan CSV
    _csv_df = df.drop(columns=["_PhaseGroup"])
    csv = _csv_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Plan als CSV herunterladen", csv,
        f"periodisierung_{auswahl['name'].replace(' ', '_')}.csv", "text/csv",
    )


# ──────────────────────────────────────────────────────────────────────────────

def page_fortschritt():
    st.markdown("# 📈 Fortschrittsverfolgung")
    _inline_spielerwechsel("entwicklung")

    auswahl = _player_selector("prog")
    if not auswahl:
        return

    sid = auswahl["id"]
    st.markdown(f"### {auswahl['name']} — historische Testergebnisse")

    fms_hist    = fms_history(sid)
    yb_hist     = y_balance_history(sid)
    sprint_hist = sprint_history(sid)
    sprung_hist = sprung_history(sid)
    agil_hist   = agilitaet_history(sid)
    aus_hist    = ausdauer_history(sid)
    kraft_hist  = kraft_history(sid)
    anthro_hist = anthropometrie_history(sid)

    tab_profil, tab_beweg, tab_speed, tab_auskoerp = st.tabs([
        "🕸️ Athletisches Profil",
        "🦵 Beweglichkeit",
        "⚡ Speed & Kraft",
        "🫁 Ausdauer & Körper",
    ])

    # ── Athletisches Profil — Radar-Chart ────────────────────────────────────
    with tab_profil:
        fms_now    = fms_letzter(sid)
        y_now      = y_balance_letzter(sid)
        sprint_now = sprint_letzter(sid)
        sprung_now = sprung_letzter(sid)
        agil_now   = agilitaet_letzter(sid)
        aus_now    = ausdauer_letzter(sid)
        spiro_now  = spiro_test_letzter(sid)
        sub = athletik_sub_scores(fms_now, y_now, sprint_now, sprung_now, agil_now, aus_now,
                                   spiro_row=spiro_now)

        if len(sub) < 2:
            st.info("Mindestens 2 Testmodule müssen vorliegen, um das Radar-Chart zu zeichnen.")
        else:
            # Label-Mapping für Anzeige
            label_map = {
                "FMS": "FMS",
                "Y-Balance": "Y-Balance",
                "Sprint": "Sprint",
                "Sprungkraft": "Sprungkraft",
                "Agilitaet": "Agilität",
                "Ausdauer": "Ausdauer",
                "Spiro": "Spiro",
            }
            cats   = [label_map.get(k, k) for k in sub.keys()]
            vals   = list(sub.values())
            # Radar geschlossen
            cats_closed = cats + [cats[0]]
            vals_closed = vals + [vals[0]]

            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(
                r=vals_closed, theta=cats_closed,
                fill="toself", name="Aktuell",
                line=dict(color="#3b82f6", width=2),
                fillcolor="rgba(59,130,246,0.15)",
                marker=dict(size=8, color="#58a6ff"),
            ))
            # Referenzlinie 70 (Teamziel)
            ref_cats = cats + [cats[0]]
            ref_vals = [70] * len(ref_cats)
            fig_r.add_trace(go.Scatterpolar(
                r=ref_vals, theta=ref_cats,
                mode="lines", name="Teamziel 70",
                line=dict(color="#d29922", width=1, dash="dash"),
            ))
            fig_r.update_layout(
                polar=dict(
                    bgcolor="#161b22",
                    radialaxis=dict(visible=True, range=[0, 100],
                                   color="#8b949e", gridcolor="#30363d",
                                   tickfont=dict(size=9)),
                    angularaxis=dict(color="#e6edf3", gridcolor="#30363d"),
                ),
                **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
                height=420, showlegend=True,
                legend=dict(orientation="h", y=-0.1),
                title=dict(text="Athletisches Profil (normiert 0–100)", font=dict(color="#e6edf3")),
            )
            col_rad, col_tbl = st.columns([3, 2])
            with col_rad:
                st.plotly_chart(fig_r, use_container_width=True)
            with col_tbl:
                st.markdown("### Modulscores")
                for k, v in sub.items():
                    label = label_map.get(k, k)
                    bar_color = "#3fb950" if v >= 75 else "#d29922" if v >= 50 else "#f85149"
                    st.markdown(
                        f"**{label}** — {v}/100 "
                        f"<span style='display:inline-block;width:{v}px;max-width:100px;"
                        f"height:8px;background:{bar_color};border-radius:4px;vertical-align:middle'></span>",
                        unsafe_allow_html=True,
                    )

    # ── Beweglichkeit: FMS + Y-Balance ──────────────────────────────────────────
    with tab_beweg:
        _beweg_sel = st.radio(
            "Modul auswählen", ["📝 FMS", "📏 Y-Balance"],
            horizontal=True, key="fort_beweg_radio", label_visibility="collapsed",
        )
        if _beweg_sel == "📝 FMS":
            if not fms_hist:
                st.info("Noch keine FMS Tests vorhanden.")
            else:
                df = pd.DataFrame(fms_hist)
                df.columns = ["Datum", "Score", "Bewertung", "Asymmetrie", "Schwerpunkt"]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["Datum"], y=df["Score"],
                    mode="lines+markers+text",
                    text=df["Score"], textposition="top center",
                    line=dict(color="#3b82f6", width=3),
                    marker=dict(size=9, color="#58a6ff"),
                    name="FMS Score",
                ))
                fig.add_hline(y=14, line_dash="dash", line_color="#d29922",
                              annotation_text="Beobachten ≤14", annotation_position="top right")
                fig.add_hline(y=12, line_dash="dash", line_color="#f85149",
                              annotation_text="Aktionsbedarf ≤12", annotation_position="top right")
                fig.update_layout(**_pl(height=340, title="FMS Score Verlauf", yaxis=dict(range=[0, 22])))
                st.plotly_chart(fig, use_container_width=True)
                _df_fms_f = _datum_filter(df.copy(), "fort_fms")
                st.dataframe(_df_fms_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "Score": st.column_config.NumberColumn("Score", format="%d / 21"),
                             })
        else:
            if not yb_hist:
                st.info("Noch keine Y-Balance Tests vorhanden.")
            else:
                df = pd.DataFrame(yb_hist)
                df.columns = ["Datum", "Composite R", "Composite L", "Asymmetrie", "Schwerpunkt"]
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=df["Datum"], y=df["Composite R"],
                    mode="lines+markers", name="Rechts",
                    line=dict(color="#3b82f6", width=3), marker=dict(size=9),
                ))
                fig2.add_trace(go.Scatter(
                    x=df["Datum"], y=df["Composite L"],
                    mode="lines+markers", name="Links",
                    line=dict(color="#f85149", width=3), marker=dict(size=9),
                ))
                fig2.add_hline(y=89, line_dash="dash", line_color="#d29922",
                               annotation_text="Normwert 89 %", annotation_position="top right")
                fig2.update_layout(**_pl(height=340, title="Y-Balance Composite Score Verlauf",
                                        yaxis=dict(range=[70, 115])))
                st.plotly_chart(fig2, use_container_width=True)
                _df_yb_f = _datum_filter(df.copy(), "fort_yb")
                st.dataframe(_df_yb_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "Composite R": st.column_config.NumberColumn("Composite R (%)", format="%.1f %%"),
                                 "Composite L": st.column_config.NumberColumn("Composite L (%)", format="%.1f %%"),
                                 "Asymmetrie":  st.column_config.NumberColumn("Asymmetrie", format="%.1f %%"),
                             })

    # ── Speed & Kraft: Sprint + Sprung + Agilität + Kraft ─────────────────────
    with tab_speed:
        _speed_sel = st.radio(
            "Modul auswählen", ["⚡ Sprint", "🦘 Sprung", "🔀 Agilität", "💪 Kraft"],
            horizontal=True, key="fort_speed_radio", label_visibility="collapsed",
        )
        if _speed_sel == "⚡ Sprint":
            if not sprint_hist:
                st.info("Noch keine Sprint-Tests vorhanden.")
            else:
                df = pd.DataFrame(sprint_hist)
                df.columns = ["Datum", "5m", "10m", "20m", "30m", "40m", "Beschl.-Index", "Bewertung 10m"]
                fig3 = go.Figure()
                for col, color in [("10m", "#3b82f6"), ("30m", "#3fb950")]:
                    if col in df.columns and df[col].notna().any():
                        fig3.add_trace(go.Scatter(
                            x=df["Datum"], y=df[col],
                            mode="lines+markers", name=f"Sprint {col}",
                            line=dict(color=color, width=3), marker=dict(size=9),
                        ))
                fig3.update_layout(**_pl(height=320, title="Sprintzeiten Verlauf",
                                        yaxis=dict(title="Zeit (s)")))
                st.plotly_chart(fig3, use_container_width=True)
                _df_sp_f = _datum_filter(df.copy(), "fort_sprint")
                st.dataframe(_df_sp_f, use_container_width=True, hide_index=True,
                             column_config={c: st.column_config.NumberColumn(c, format="%.2f s")
                                            for c in ["5m","10m","20m","30m"]})
        elif _speed_sel == "🦘 Sprung":
            if not sprung_hist:
                st.info("Noch keine Sprung-Tests vorhanden.")
            else:
                df = pd.DataFrame(sprung_hist)
                df.columns = ["Datum", "CMJ beid.", "Squat Jump", "Drop Jump", "RSI",
                              "Standweit", "CMJ Asymm.", "Bewertung CMJ"]
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter(
                    x=df["Datum"], y=df["CMJ beid."],
                    mode="lines+markers+text",
                    text=df["CMJ beid."], textposition="top center",
                    line=dict(color="#3b82f6", width=3), marker=dict(size=9),
                    name="CMJ beidbeinig (cm)",
                ))
                fig4.add_hline(y=33, line_dash="dash", line_color="#d29922",
                               annotation_text="Norm Leistungssport 33 cm",
                               annotation_position="top right")
                fig4.update_layout(**_pl(height=320, title="CMJ Sprunghöhe Verlauf",
                                        yaxis=dict(title="Höhe (cm)")))
                st.plotly_chart(fig4, use_container_width=True)
                _df_sprung_f = _datum_filter(df.copy(), "fort_sprung")
                st.dataframe(_df_sprung_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "CMJ beid.":  st.column_config.NumberColumn("CMJ beid. (cm)", format="%.1f cm"),
                                 "Squat Jump": st.column_config.NumberColumn("Squat Jump (cm)", format="%.1f cm"),
                                 "Drop Jump":  st.column_config.NumberColumn("Drop Jump (cm)", format="%.1f cm"),
                                 "CMJ Asymm.": st.column_config.NumberColumn("CMJ Asymm. (%)", format="%.1f %%"),
                             })
        elif _speed_sel == "🔀 Agilität":
            if not agil_hist:
                st.info("Noch keine Agilitäts-Tests vorhanden.")
            else:
                df = pd.DataFrame(agil_hist).rename(columns={
                    "datum": "Datum", "t505_r": "505 R (s)", "t505_l": "505 L (s)",
                    "asym_505": "Asymm. 505 (%)", "t5_10_5": "5-10-5 (s)",
                    "t_test": "T-Test (s)", "illinois": "Illinois (s)",
                    "bew_t_test": "Bewertung T-Test", "modified_t_test": "Mod. T-Test (s)",
                    "pro_agility": "Pro Agility (s)", "arrowhead_r": "Arrowhead R (s)",
                    "arrowhead_l": "Arrowhead L (s)", "zigzag": "Zigzag (s)", "balsom": "Balsom (s)",
                })
                fig5 = go.Figure()
                for col, color in [("T-Test (s)", "#3b82f6"), ("Illinois (s)", "#3fb950")]:
                    if col in df.columns and df[col].notna().any():
                        fig5.add_trace(go.Scatter(
                            x=df["Datum"], y=df[col],
                            mode="lines+markers", name=col,
                            line=dict(color=color, width=3), marker=dict(size=9),
                        ))
                fig5.update_layout(**_pl(height=320, title="Agilitätszeiten Verlauf",
                                        yaxis=dict(title="Zeit (s)")))
                st.plotly_chart(fig5, use_container_width=True)
                _df_agil_f = _datum_filter(df.copy(), "fort_agil")
                st.dataframe(_df_agil_f, use_container_width=True, hide_index=True,
                             column_config={c: st.column_config.NumberColumn(c, format="%.2f s")
                                            for c in ["505 R (s)","505 L (s)","5-10-5 (s)","T-Test (s)","Illinois (s)"]})
        else:  # Kraft
            if not kraft_hist:
                st.info("Noch keine Krafttests vorhanden.")
            else:
                df_k = pd.DataFrame(kraft_hist)
                figk1 = go.Figure()
                if "direktes_1rm" in df_k.columns:
                    figk1.add_trace(go.Scatter(
                        x=df_k["datum"], y=df_k["direktes_1rm"],
                        mode="lines+markers", name="Direktes 1RM (kg)",
                        line=dict(color="#3fb950", width=3), marker=dict(size=9),
                    ))
                if "geschaetztes_1rm" in df_k.columns:
                    figk1.add_trace(go.Scatter(
                        x=df_k["datum"], y=df_k["geschaetztes_1rm"],
                        mode="lines+markers", name="Epley 1RM (kg)",
                        line=dict(color="#3b82f6", width=2, dash="dash"), marker=dict(size=7),
                    ))
                figk1.update_layout(**_pl(height=300, title="Bankdrücken 1RM Verlauf (kg)",
                                         yaxis=dict(title="kg")))
                st.plotly_chart(figk1, use_container_width=True)
                if "rumpf_gesamt_sekunden" in df_k.columns:
                    figk2 = go.Figure()
                    for col_k, lbl_k, clr_k in [
                        ("ventral_sekunden",        "Ventral (Plank)", "#3fb950"),
                        ("lateral_rechts_sekunden", "Lateral rechts",  "#3b82f6"),
                        ("lateral_links_sekunden",  "Lateral links",   "#d29922"),
                        ("dorsal_sekunden",          "Dorsal",          "#9e6a03"),
                        ("rumpf_gesamt_sekunden",    "Gesamtzeit",      "#f85149"),
                    ]:
                        if col_k in df_k.columns:
                            figk2.add_trace(go.Scatter(
                                x=df_k["datum"], y=df_k[col_k],
                                mode="lines+markers", name=lbl_k,
                                line=dict(color=clr_k, width=2), marker=dict(size=7),
                            ))
                    figk2.update_layout(**_pl(height=300, title="Rumpfkraftausdauer Verlauf (s)",
                                             yaxis=dict(title="Sekunden")))
                    st.plotly_chart(figk2, use_container_width=True)
                _df_kraft_ren = df_k.rename(columns={
                    "datum": "Datum", "direktes_1rm": "1RM direkt (kg)",
                    "geschaetztes_1rm": "1RM Epley (kg)",
                    "relative_kraft_direkt": "Rel. K. direkt",
                    "relative_kraft_geschaetzt": "Rel. K. Epley",
                    "ventral_sekunden": "Ventral (s)",
                    "lateral_rechts_sekunden": "Lat. R (s)",
                    "lateral_links_sekunden": "Lat. L (s)",
                    "dorsal_sekunden": "Dorsal (s)",
                    "rumpf_gesamt_sekunden": "Rumpf ges. (s)",
                    "lateral_asymmetrie_prozent": "Lat. Asym (%)",
                })
                _df_kraft_f = _datum_filter(_df_kraft_ren, "fort_kraft")
                st.dataframe(_df_kraft_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "1RM direkt (kg)": st.column_config.NumberColumn("1RM direkt (kg)", format="%.1f kg"),
                                 "1RM Epley (kg)":  st.column_config.NumberColumn("1RM Epley (kg)", format="%.1f kg"),
                                 "Lat. Asym (%)":   st.column_config.NumberColumn("Lat. Asym (%)", format="%.1f %%"),
                             })

    # ── Ausdauer & Körper: Ausdauer + Anthropometrie ───────────────────────────
    with tab_auskoerp:
        _ausd_sel = st.radio(
            "Modul auswählen", ["🫁 Ausdauer", "⚖️ Anthropometrie"],
            horizontal=True, key="fort_ausd_radio", label_visibility="collapsed",
        )
        if _ausd_sel == "🫁 Ausdauer":
            if not aus_hist:
                st.info("Noch keine Ausdauer-Tests vorhanden.")
            else:
                df = pd.DataFrame(aus_hist)
                df.columns = ["Datum", "Test-Typ", "Distanz (m)", "VO₂max", "Bewertung", "HF max", "RPE"]
                fig6 = go.Figure()
                if "VO₂max" in df.columns and df["VO₂max"].notna().any():
                    fig6.add_trace(go.Scatter(
                        x=df["Datum"], y=df["VO₂max"],
                        mode="lines+markers+text",
                        text=df["VO₂max"], textposition="top center",
                        line=dict(color="#3b82f6", width=3), marker=dict(size=9),
                        name="VO₂max (ml/kg/min)",
                    ))
                fig6.add_hline(y=50, line_dash="dash", line_color="#d29922",
                               annotation_text="Zielwert ≥ 50 ml/kg/min",
                               annotation_position="top right")
                fig6.update_layout(**_pl(height=320, title="VO₂max Verlauf",
                                        yaxis=dict(title="VO₂max (ml/kg/min)")))
                st.plotly_chart(fig6, use_container_width=True)
                _df_aus_f = _datum_filter(df.copy(), "fort_ausdauer")
                st.dataframe(_df_aus_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "VO₂max":      st.column_config.NumberColumn("VO₂max", format="%.1f ml/kg/min"),
                                 "Distanz (m)": st.column_config.NumberColumn("Distanz (m)", format="%d m"),
                             })
        else:
            if not anthro_hist:
                st.info("Noch keine Anthropometrie-Messungen vorhanden.")
            else:
                df = pd.DataFrame(anthro_hist)
                df.columns = ["Datum", "Größe (cm)", "Gewicht (kg)", "Körperfett (%)", "Muskelmasse (kg)",
                              "BMI", "BMI-Kat.", "Sitzhöhe (cm)", "Beinlänge (cm)", "Armspann (cm)",
                              "PHV-Offset", "Reifestatus", "Beinlänge R", "Beinlänge L", "KF-Methode"]
                fig7 = go.Figure()
                fig7.add_trace(go.Scatter(
                    x=df["Datum"], y=df["Gewicht (kg)"],
                    mode="lines+markers", name="Gewicht (kg)",
                    line=dict(color="#3b82f6", width=3), marker=dict(size=9),
                ))
                fig7.add_trace(go.Scatter(
                    x=df["Datum"], y=df["Muskelmasse (kg)"],
                    mode="lines+markers", name="Muskelmasse (kg)",
                    line=dict(color="#3fb950", width=3), marker=dict(size=9),
                ))
                fig7.update_layout(**_pl(height=320, title="Körperzusammensetzung Verlauf",
                                        yaxis=dict(title="kg")))
                st.plotly_chart(fig7, use_container_width=True)
                fig8 = go.Figure()
                fig8.add_trace(go.Scatter(
                    x=df["Datum"], y=df["BMI"],
                    mode="lines+markers", name="BMI",
                    line=dict(color="#d29922", width=3), marker=dict(size=9),
                ))
                fig8.add_hline(y=25, line_dash="dash", line_color="#f85149",
                               annotation_text="Übergewicht ≥ 25", annotation_position="top right")
                fig8.update_layout(**_pl(height=260, title="BMI Verlauf"))
                st.plotly_chart(fig8, use_container_width=True)
                _df_anthro_show = df[["Datum", "Größe (cm)", "Gewicht (kg)", "Körperfett (%)",
                                       "Muskelmasse (kg)", "BMI", "BMI-Kat.", "PHV-Offset", "Reifestatus"]].copy()
                _df_anthro_f = _datum_filter(_df_anthro_show, "fort_anthro")
                st.dataframe(_df_anthro_f, use_container_width=True, hide_index=True,
                             column_config={
                                 "Größe (cm)":      st.column_config.NumberColumn("Größe (cm)", format="%.0f cm"),
                                 "Gewicht (kg)":    st.column_config.NumberColumn("Gewicht (kg)", format="%.1f kg"),
                                 "Körperfett (%)":  st.column_config.NumberColumn("Körperfett (%)", format="%.1f %%"),
                                 "Muskelmasse (kg)":st.column_config.NumberColumn("Muskelmasse (kg)", format="%.1f kg"),
                                 "BMI":             st.column_config.NumberColumn("BMI", format="%.1f"),
                             })

# ──────────────────────────────────────────────────────────────────────────────

def page_anthropometrie():
    st.markdown("# 📐 Anthropometrie")
    _back_button("← Zurück zu Tests", "🔬  Diagnostik", target_sub_diagnostik="🏠 Übersicht", key="back_anthro")
    st.markdown("Körpermessungen, BMI und Wachstumsverlauf — Grundlage für belastungsgerechtes Training.")

    sicherheitshinweis_box()
    show_trainer_checkliste("anthropometrie")
    show_test_info("anthropometrie")
    _anleitung_download_button("anthropometrie")

    auswahl = _player_selector("anthro")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    alter  = berechne_alter(sp.get("geburtsdatum", "")) if sp else 0.0
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    altersgruppe_norm = alter_zu_altersgruppe(alter)

    history = anthropometrie_history(sid)
    letzter = anthropometrie_letzter(sid)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_neu, tab_verlauf = st.tabs(["📋 Neue Messung", "📈 Verlauf"])

    with tab_neu:
        st.markdown("### Körpermessung eingeben")
        _check_save_ok()
        _fh = lambda fid: show_field_help("anthropometrie", fid)
        _APP_DIR = os.path.dirname(os.path.abspath(__file__))

        datum = st.date_input("Datum", value=date.today(), key="anthro_datum")

        # ── Körperfett-Methode — zuerst und volle Breite ──────────────────────
        st.markdown("#### 📏 Körperfett-Messung")
        kf_methode = st.radio(
            "Methode wählen",
            ["Manuell", "7-Hautfalten (JP)", "11-Hautfalten (JP)", "Körperanalysewaage"],
            key="anthro_kf_methode", horizontal=True, label_visibility="collapsed",
        )
        _kf_default = float(letzter["koerperfett"]) if letzter and letzter.get("koerperfett") else 0.0
        koerperfett = 0.0

        if kf_methode in ("Manuell", "Körperanalysewaage"):
            _kf_note = "Gerätewert direkt eingeben (BIA-Waage, DEXA o. ä.)" if kf_methode == "Körperanalysewaage" else "Bekannten Prozentwert direkt eingeben"
            st.caption(_kf_note)
            _kfrc1, _kfrc2 = st.columns([2, 5])
            koerperfett = _kfrc1.number_input(
                "Körperfett (%)", 0.0, 50.0, _kf_default, step=0.1, key="anthro_kf_man"
            )
            if koerperfett > 0:
                norm_badge(koerperfett, "anthropometrie", "koerperfett", _kfrc1, altersgruppe=altersgruppe_norm)

        elif kf_methode == "7-Hautfalten (JP)":
            _svg7 = os.path.join(_APP_DIR, "assets", "tests", "anthropometrie", "hautfalten_7.svg")
            _img7_col, _inp7_col = st.columns([5, 11])
            with _img7_col:
                if os.path.exists(_svg7):
                    st.image(_svg7, use_container_width=True)
                else:
                    st.caption("📍 Brust · Abdomen · Suprailiakal · Oberschenkel · Trizeps · Subskapular · Mittelachse")
            with _inp7_col:
                st.caption("**Jackson & Pollock (1978)** — alle Werte in mm, rechte Körperseite, entspannte Muskulatur")
                _h7r1, _h7r2, _h7r3, _h7r4 = st.columns(4)
                _h7r5, _h7r6, _h7r7, _h7res  = st.columns(4)
                s_brust  = _h7r1.number_input("Brust (mm)",        0.0, 80.0, 0.0, step=0.5, key="hf7_br")
                s_mittel = _h7r2.number_input("Mittelachse (mm)",  0.0, 60.0, 0.0, step=0.5, key="hf7_mi")
                s_tri    = _h7r3.number_input("Trizeps (mm)",      0.0, 60.0, 0.0, step=0.5, key="hf7_tr")
                s_sub    = _h7r4.number_input("Subskapular (mm)",  0.0, 60.0, 0.0, step=0.5, key="hf7_su")
                s_abd    = _h7r5.number_input("Abdomen (mm)",      0.0, 80.0, 0.0, step=0.5, key="hf7_ab")
                s_sup    = _h7r6.number_input("Suprailiakal (mm)", 0.0, 60.0, 0.0, step=0.5, key="hf7_sp")
                s_ober   = _h7r7.number_input("Oberschenkel (mm)", 0.0, 60.0, 0.0, step=0.5, key="hf7_ob")
                _all7 = [s_brust, s_mittel, s_tri, s_sub, s_abd, s_sup, s_ober]
                if all(v > 0 for v in _all7) and alter and alter > 0:
                    koerperfett = koerperfett_jp7(*_all7, float(alter), geschl)
                    _h7res.metric("Körperfett (JP7)", f"{koerperfett} %")
                    norm_badge(koerperfett, "anthropometrie", "koerperfett", _h7res, altersgruppe=altersgruppe_norm)
                else:
                    st.info("ℹ️ Alle 7 Werte > 0 eingeben — Körperfett wird automatisch berechnet.")

        elif kf_methode == "11-Hautfalten (JP)":
            _svg11 = os.path.join(_APP_DIR, "assets", "tests", "anthropometrie", "hautfalten_11.svg")
            _img11_col, _inp11_col = st.columns([5, 11])
            with _img11_col:
                if os.path.exists(_svg11):
                    st.image(_svg11, use_container_width=True)
                else:
                    st.caption("📍 7-Punkt + Bizeps · Wadeninnenseite · unt. Rücken · Pektoral")
            with _inp11_col:
                st.caption("**Pařízkova (1977)** — 11 Messpunkte, rechte Körperseite, Werte in mm")
                _h11a, _h11b, _h11c, _h11d   = st.columns(4)
                _h11e, _h11f, _h11g, _h11h   = st.columns(4)
                _h11i, _h11j, _h11k, _h11res = st.columns(4)
                s11_br  = _h11a.number_input("Brust",        0.0, 80.0, 0.0, step=0.5, key="hf11_br")
                s11_mi  = _h11b.number_input("Mittelachse",  0.0, 60.0, 0.0, step=0.5, key="hf11_mi")
                s11_tr  = _h11c.number_input("Trizeps",      0.0, 60.0, 0.0, step=0.5, key="hf11_tr")
                s11_su  = _h11d.number_input("Subskapular",  0.0, 60.0, 0.0, step=0.5, key="hf11_su")
                s11_ab  = _h11e.number_input("Abdomen",      0.0, 80.0, 0.0, step=0.5, key="hf11_ab")
                s11_sp  = _h11f.number_input("Suprailiakal", 0.0, 60.0, 0.0, step=0.5, key="hf11_sp")
                s11_ob  = _h11g.number_input("Oberschenkel", 0.0, 60.0, 0.0, step=0.5, key="hf11_ob")
                s11_biz = _h11h.number_input("Bizeps",       0.0, 60.0, 0.0, step=0.5, key="hf11_bz")
                s11_wa  = _h11i.number_input("Wade innen",   0.0, 40.0, 0.0, step=0.5, key="hf11_wa")
                s11_rk  = _h11j.number_input("Unt. Rücken",  0.0, 60.0, 0.0, step=0.5, key="hf11_rk")
                s11_pk  = _h11k.number_input("Pektoral",     0.0, 60.0, 0.0, step=0.5, key="hf11_pk")
                _all11 = [s11_br, s11_mi, s11_tr, s11_su, s11_ab, s11_sp, s11_ob, s11_biz, s11_wa, s11_rk, s11_pk]
                if all(v > 0 for v in _all11) and alter and alter > 0:
                    koerperfett = koerperfett_jp11(*_all11, float(alter), geschl)
                    _h11res.metric("Körperfett (JP11)", f"{koerperfett} %")
                    norm_badge(koerperfett, "anthropometrie", "koerperfett", _h11res, altersgruppe=altersgruppe_norm)
                else:
                    st.info("ℹ️ Alle 11 Werte > 0 eingeben — Körperfett wird automatisch berechnet.")

        # ── Körpermessungen ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📐 Körpermessungen")
        c1, c2 = st.columns(2)
        g_h, g_i = c1.columns([5, 1]); g_h.markdown("**Körpergröße (cm)**"); field_info_col(g_i, "anthropometrie", "groesse")
        groesse      = c1.number_input("Körpergröße (cm)", 100.0, 220.0,
                                        float(letzter["groesse"]) if letzter else 175.0,
                                        step=0.5, key="anthro_groesse", label_visibility="collapsed", help=_fh("groesse"))
        gw_h, gw_i = c1.columns([5, 1]); gw_h.markdown("**Körpergewicht (kg)**"); field_info_col(gw_i, "anthropometrie", "gewicht")
        gewicht      = c1.number_input("Körpergewicht (kg)", 15.0, 150.0,
                                        float(letzter["gewicht"]) if letzter else 70.0,
                                        step=0.5, key="anthro_gewicht", label_visibility="collapsed", help=_fh("gewicht"))
        mm_h, mm_i = c1.columns([5, 1]); mm_h.markdown("**Muskelmasse (kg)**"); field_info_col(mm_i, "anthropometrie", "muskelmasse")
        muskelmasse  = c1.number_input("Muskelmasse (kg)", 0.0, 100.0,
                                        float(letzter["muskelmasse"]) if letzter else 0.0,
                                        step=0.5, key="anthro_mm", label_visibility="collapsed", help=_fh("muskelmasse"))
        sh_h, sh_i = c2.columns([5, 1]); sh_h.markdown("**Sitzhöhe (cm) — optional für PHV**"); field_info_col(sh_i, "anthropometrie", "sitzhoehe")
        sitzhoehe    = c2.number_input("Sitzhöhe (cm) — optional für PHV", 0.0, 120.0,
                                        float(letzter["sitzhoehe"]) if letzter else 0.0,
                                        step=0.5, key="anthro_sh", label_visibility="collapsed", help=_fh("sitzhoehe"))
        _def_bl_r = float(letzter.get("beinlaenge_r") or letzter.get("beinlaenge") or 0) if letzter else 0.0
        _def_bl_l = float(letzter.get("beinlaenge_l") or letzter.get("beinlaenge") or 0) if letzter else 0.0
        blr_h, blr_i = c2.columns([5, 1]); blr_h.markdown("**Beinlänge rechts (cm)**"); field_info_col(blr_i, "anthropometrie", "beinlaenge")
        beinlaenge_r = c2.number_input("Beinlänge rechts (cm)", 0.0, 120.0, _def_bl_r,
                                        step=0.5, key="anthro_bl_r", label_visibility="collapsed", help=_fh("beinlaenge"))
        bll_h, bll_i = c2.columns([5, 1]); bll_h.markdown("**Beinlänge links (cm)**"); field_info_col(bll_i, "anthropometrie", "beinlaenge")
        beinlaenge_l = c2.number_input("Beinlänge links (cm)", 0.0, 120.0, _def_bl_l,
                                        step=0.5, key="anthro_bl_l", label_visibility="collapsed", help=_fh("beinlaenge"))
        beinlaenge = (beinlaenge_r + beinlaenge_l) / 2.0 if beinlaenge_r > 0 and beinlaenge_l > 0 else max(beinlaenge_r, beinlaenge_l)
        if beinlaenge_r > 0 and beinlaenge_l > 0:
            _diff_bl = abs(beinlaenge_r - beinlaenge_l)
            if _diff_bl >= 0.5:
                c2.warning(f"⚠️ Beinlängendifferenz {_diff_bl:.1f} cm — Ärztliche Untersuchung empfohlen.")
        as_h, as_i = c2.columns([5, 1]); as_h.markdown("**Armspannweite (cm)**"); field_info_col(as_i, "anthropometrie", "armspann")
        armspann     = c2.number_input("Armspannweite (cm)", 0.0, 250.0,
                                        float(letzter["armspannweite"]) if letzter else 0.0,
                                        step=0.5, key="anthro_arm", label_visibility="collapsed", help=_fh("armspann"))

        bmi     = bmi_berechnen(gewicht, groesse)
        bmi_kat = bmi_kategorie(bmi)
        phv     = phv_offset_berechnen(alter, groesse, gewicht, sitzhoehe, beinlaenge, geschl) if alter else None
        reife   = reifestatus_text(phv)
        farbe   = reifestatus_farbe(phv)

        # ── Plausibilitätsprüfungen ──────────────────────────────────────────
        if datum > date.today():
            st.warning("⚠️ Datum liegt in der Zukunft — bitte prüfen.")
        if sitzhoehe > 0 and sitzhoehe >= groesse:
            st.warning("⚠️ Sitzhöhe ≥ Körpergröße — Eingaben prüfen.")
        if beinlaenge > 0 and beinlaenge >= groesse:
            st.warning("⚠️ Beinlänge ≥ Körpergröße — Eingaben prüfen.")
        if armspann > 0 and (armspann < groesse * 0.75 or armspann > groesse * 1.25):
            st.warning(
                f"⚠️ Armspannweite ({armspann:.0f} cm) liegt deutlich außerhalb der "
                f"Körpergröße ({groesse:.0f} cm) — Eingaben prüfen."
            )
        if alter and alter < 18 and bmi > 0:
            st.info(
                "ℹ️ Hinweis: BMI-Normbereiche für Erwachsene (≥ 18 J.) gelten nicht direkt "
                "für Kinder und Jugendliche — bitte altersabhängige Normkurven verwenden."
            )

        # Vorschau
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("BMI", f"{bmi}", bmi_kat)
        m2.metric("Körperfett", f"{koerperfett} %")
        if phv is not None:
            m3.metric("PHV-Offset", f"{phv:+.1f} Jahre")
        st.markdown(
            f'<div style="background:#161b22;border:1px solid {farbe};border-radius:8px;padding:10px 14px;margin:8px 0">'
            f'<span style="color:{farbe};font-weight:600">⚠️ Reifestatus (Schätzung): </span>'
            f'<span style="color:#e6edf3">{reife}</span><br>'
            f'<small style="color:#8b949e">Hinweis: Diese Schätzung (Mirwald-Formel) ersetzt keine ärztliche Untersuchung.</small>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Trainerbeobachtungen ────────────────────────────────────────────
        st.markdown("---")
        obs_anthro = render_observation_selector("anthropometrie", sid, datum.strftime("%d.%m.%Y"), "anthro", standalone=False)

        col_sv, col_del = st.columns([3, 1])
        with col_sv:
            if st.button("💾 Messung speichern", use_container_width=True, key="anthro_save", type="primary"):
                import json as _j
                anthropometrie_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    groesse, gewicht, sitzhoehe, beinlaenge, armspann,
                    koerperfett, muskelmasse,
                    bmi, bmi_kat, phv, reife,
                    beinlaenge_r=beinlaenge_r, beinlaenge_l=beinlaenge_l,
                    koerperfett_methode=kf_methode,
                )
                if obs_anthro["beob_ids"] or obs_anthro.get("freitext"):
                    beobachtung_speichern(
                        sid, "anthropometrie", datum.strftime("%d.%m.%Y"),
                        _j.dumps(obs_anthro["beob_ids"], ensure_ascii=False),
                        obs_anthro["seite"], obs_anthro["auspraegung"],
                        obs_anthro["freitext"], obs_anthro["text_generiert"],
                    )
                _save_ok("Messung gespeichert!")
                _reset_keys(
                    "anthro_groesse", "anthro_gewicht", "anthro_mm", "anthro_sh",
                    "anthro_bl_r", "anthro_bl_l", "anthro_arm", "anthro_kf_man", "anthro_kf_methode",
                )
                st.rerun()
        with col_del:
            if letzter and _confirm_loeschen("anthro_del", was="die letzte Messung",
                                              btn_label="🗑️ Letzte löschen"):
                anthropometrie_loeschen_letzten(sid)
                _save_ok("Letzte Messung gelöscht.")
                st.rerun()

    with tab_verlauf:
        if not history:
            st.info("Noch keine Messungen vorhanden.")
            return

        df = pd.DataFrame(history)
        df.columns = ["Datum", "Größe", "Gewicht", "Körperfett", "Muskelmasse",
                      "BMI", "BMI-Kat.", "Sitzhöhe", "Beinlänge", "Armspann",
                      "PHV-Offset", "Reifestatus", "Beinlänge R", "Beinlänge L",
                      "KF-Methode"]

        # Wachstum/Monat
        wachstum = wachstum_berechnen(history)
        if wachstum is not None and wachstum > 0:
            st.info(f"📏 Durchschnittliches Wachstum: **{wachstum} cm/Monat**")

        c_g, c_w = st.columns(2)
        with c_g:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["Datum"], y=df["Größe"],
                                     mode="lines+markers+text", text=df["Größe"].round(1),
                                     textposition="top center",
                                     line=dict(color="#3b82f6", width=3),
                                     marker=dict(size=8), name="Größe (cm)"))
            fig.update_layout(**_pl(height=280, title="Körpergröße", yaxis=dict(title="cm")))
            st.plotly_chart(fig, use_container_width=True)

        with c_w:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df["Datum"], y=df["Gewicht"],
                                      mode="lines+markers+text", text=df["Gewicht"].round(1),
                                      textposition="top center",
                                      line=dict(color="#3fb950", width=3),
                                      marker=dict(size=8), name="Gewicht (kg)"))
            fig2.update_layout(**_pl(height=280, title="Körpergewicht", yaxis=dict(title="kg")))
            st.plotly_chart(fig2, use_container_width=True)

        c_kf, c_bmi = st.columns(2)
        with c_kf:
            fig3 = go.Figure()
            _kf_hover = df.apply(
                lambda r: f"{r['Körperfett']:.1f} %<br>Methode: {r['KF-Methode'] or '—'}",
                axis=1,
            )
            fig3.add_trace(go.Scatter(x=df["Datum"], y=df["Körperfett"],
                                      mode="lines+markers+text", text=df["Körperfett"].round(1),
                                      textposition="top center",
                                      hovertext=_kf_hover, hoverinfo="x+text",
                                      line=dict(color="#d29922", width=3),
                                      marker=dict(size=8), name="Körperfett (%)"))
            fig3.update_layout(**_pl(height=280, title="Körperfett", yaxis=dict(title="%")))
            st.plotly_chart(fig3, use_container_width=True)

        with c_bmi:
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(x=df["Datum"], y=df["BMI"],
                                  marker_color="#58a6ff", text=df["BMI"].round(1),
                                  textposition="outside", name="BMI"))
            fig4.add_hline(y=18.5, line_dash="dash", line_color="#3fb950",
                           annotation_text="Untergrenze 18.5")
            fig4.add_hline(y=25.0, line_dash="dash", line_color="#d29922",
                           annotation_text="Übergewicht 25")
            fig4.update_layout(**_pl(height=280, title="BMI-Verlauf", yaxis=dict(title="BMI (kg/m²)")))
            st.plotly_chart(fig4, use_container_width=True)

        st.dataframe(df[["Datum", "Größe", "Gewicht", "BMI", "BMI-Kat.", "Körperfett",
                          "KF-Methode", "Muskelmasse", "PHV-Offset", "Reifestatus"]],
                     use_container_width=True, hide_index=True)

        # ── Zwei Termine vergleichen ──────────────────────────────────────────
        if len(df) >= 2:
            with st.expander("🔍 Zwei Termine vergleichen"):
                datums_an = df["Datum"].tolist()
                anc1, anc2 = st.columns(2)
                and1 = anc1.selectbox("Termin 1", datums_an, index=0, key="anth_cmp_d1")
                and2 = anc2.selectbox("Termin 2", datums_an, index=len(datums_an)-1, key="anth_cmp_d2")
                anr1 = df[df["Datum"] == and1].iloc[0]
                anr2 = df[df["Datum"] == and2].iloc[0]
                compare_cols_an = ["Größe", "Gewicht", "Körperfett", "Muskelmasse", "BMI"]
                rows_an = []
                for can in compare_cols_an:
                    v1an = float(anr1.get(can, 0) or 0)
                    v2an = float(anr2.get(can, 0) or 0)
                    if v1an > 0 or v2an > 0:
                        diff_an = round(v2an - v1an, 2) if v1an > 0 and v2an > 0 else "—"
                        rows_an.append({
                            "Messung": can,
                            and1: f"{v1an:.1f}" if v1an else "—",
                            and2: f"{v2an:.1f}" if v2an else "—",
                            "Differenz": f"{diff_an:+.2f}" if isinstance(diff_an, float) else diff_an,
                        })
                if rows_an:
                    st.dataframe(pd.DataFrame(rows_an), use_container_width=True, hide_index=True)

        # ── Bearbeiten / Löschen ──────────────────────────────────────────────
        st.markdown("---")
        with st.expander("✏️ Messung bearbeiten / löschen"):
            _render_anthro_edit(sid)


# ──────────────────────────────────────────────────────────────────────────────

def _sprint_eingabe(distanz_label: str, key_prefix: str, letzter_row, col,
                    field_id: str = "", altersgruppe: str = "Senior"):
    """Hilfsfunktion: 3-Versuch-Eingabe für eine Sprint-Distanz mit Info-Button."""
    hdr, info_btn = col.columns([5, 1])
    hdr.markdown(f"**{distanz_label}**")
    if field_id:
        field_info_col(info_btn, "sprint", field_id)
    c1, c2, c3 = col.columns(3)
    help_txt = show_field_help("sprint", field_id) if field_id else ""
    v1 = c1.number_input("V1", 0.0, 20.0, 0.0, step=0.01, format="%.2f",
                          key=f"{key_prefix}_v1", label_visibility="collapsed",
                          help=f"Versuch 1 — {distanz_label}  \n{help_txt}" if help_txt else f"Versuch 1 — {distanz_label}")
    v2 = c2.number_input("V2", 0.0, 20.0, 0.0, step=0.01, format="%.2f",
                          key=f"{key_prefix}_v2", label_visibility="collapsed",
                          help=f"Versuch 2 — {distanz_label}")
    v3 = c3.number_input("V3", 0.0, 20.0, 0.0, step=0.01, format="%.2f",
                          key=f"{key_prefix}_v3", label_visibility="collapsed",
                          help=f"Versuch 3 — {distanz_label}")
    bester = min((v for v in [v1, v2, v3] if v > 0), default=None)
    if bester:
        col.markdown(f'<small style="color:#8b949e">Bester Versuch: <b style="color:#58a6ff">{bester:.2f} s</b></small>', unsafe_allow_html=True)
        if field_id:
            norm_badge(bester, "sprint", field_id, col, altersgruppe=altersgruppe)
    return v1, v2, v3, bester


# ─── Sprint-Analyse Hilfsfunktionen ──────────────────────────────────────────

def _sprint_leistungsbereiche_ui(sprint_row: dict, alter_j=None) -> None:
    """Zeigt Sprint-Leistungsbereiche aus validen Testdaten (NO_DATA → keine Anzeige)."""
    b10  = sprint_row.get("beste_10m") or 0
    b20  = sprint_row.get("beste_20m") or 0
    b30  = sprint_row.get("beste_30m") or 0
    b40  = sprint_row.get("beste_40m") or 0
    bew10 = sprint_row.get("bewertung_10m") or ""
    bew30 = sprint_row.get("bewertung_30m") or ""

    bereiche = []
    if b10 > 0:
        _fc = "#da3633" if "Verbesserung" in bew10 else ("#d29922" if "Mittel" in bew10 else "#238636" if bew10 else "#58a6ff")
        bereiche.append(("Beschleunigung 0–10 m", f"{b10:.2f} s", bew10 or "Gemessen", _fc))
    if b10 > 0 and b20 > 0:
        bereiche.append(("Beschleunigung 10–20 m", f"{round(b20-b10,2):.2f} s", "Segment", "#58a6ff"))
    if b20 > 0 and b30 > 0:
        bereiche.append(("Übergang 20–30 m", f"{round(b30-b20,2):.2f} s", "Segment", "#58a6ff"))
    if b30 > 0:
        _fc30 = "#da3633" if "Verbesserung" in bew30 else ("#d29922" if "Mittel" in bew30 else "#238636" if bew30 else "#58a6ff")
        bereiche.append(("Maximalgeschwindigkeit (30 m)", f"{b30:.2f} s", bew30 or "Gemessen", _fc30))
    if b30 > 0 and b40 > 0:
        bereiche.append(("Speed Maintenance 30–40 m", f"{round(b40-b30,2):.2f} s", "Segment", "#8b949e"))

    if not bereiche:
        st.caption("Keine validen Sprint-Daten für Leistungsbereichsanalyse verfügbar.")
        return

    cols = st.columns(len(bereiche))
    for col, (lbl, zeit, bew, farbe) in zip(cols, bereiche):
        col.markdown(
            f"<div style='background:#161b22;border:1px solid #30363d;border-radius:8px;"
            f"padding:10px 8px;text-align:center'>"
            f"<div style='font-size:9px;color:#8b949e;margin-bottom:4px;line-height:1.3'>{lbl}</div>"
            f"<div style='font-size:20px;font-weight:700;color:#e6edf3'>{zeit}</div>"
            f"<div style='font-size:10px;color:{farbe};margin-top:4px'>{bew}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def _sprint_muskulatur_info_ui() -> None:
    """Zeigt die 7 wissenschaftlich relevanten Muskelgruppen (Spec §3)."""
    _MUSKELN = [
        ("Psoas major",    "Hüftbeugung · Beinvorführung · Schwungbeinphase",                   "R²=0,499 ★"),
        ("Gluteus medius", "Beckenstabilität · Hüftstabilität · einbeinige Kontrolle",           "R²=0,451 ★"),
        ("Gluteus maximus","Explosive Hüftstreckung · Kraftübertragung · Beschleunigung",        "R²=0,365"),
        ("Piriformis",     "Hüftstabilität · Kontrolle der Hüftposition",                        "R²=0,303"),
        ("Rectus femoris", "Hüftbeugung · Kniestreckung",                                        "R²=0,321"),
        ("Adduktoren",     "Stabilisierung · Kraftübertragung · Hüftkontrolle",                 "—"),
        ("Hamstrings",     "Hüftstreckung · Kniekontrolle · Schwungbein-/Stützphase",           "R²=0,269"),
    ]
    for i in range(0, len(_MUSKELN), 4):
        gruppe = _MUSKELN[i:i+4]
        cols = st.columns(len(gruppe))
        for col, (name, funktion, r2) in zip(cols, gruppe):
            col.markdown(
                f"<div style='background:#161b22;border:1px solid #30363d;border-radius:8px;"
                f"padding:12px;height:100%'>"
                f"<div style='font-size:12px;font-weight:700;color:#58a6ff;margin-bottom:6px'>{name}</div>"
                f"<div style='font-size:11px;color:#8b949e;line-height:1.5'>{funktion}</div>"
                f"<div style='font-size:10px;color:#6e7681;margin-top:6px'>{r2}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.caption("★ Stärkster Zusammenhang mit Sprintgeschwindigkeit in der Referenzstudie.")


def page_sprint():
    st.markdown("# ⚡ Sprint-Diagnostik")
    _back_button("← Zurück zu Tests", "🔬  Diagnostik", target_sub_diagnostik="🏠 Übersicht", key="back_sprint")
    st.markdown("Lineare Beschleunigung und Maximalgeschwindigkeit — 5 m bis 40 m, je 3 Versuche.")

    # ── Sicherheitshinweis & Testanleitung ────────────────────────────────────
    sicherheitshinweis_box()
    show_trainer_checkliste("sprint")
    show_test_info("sprint")
    _anleitung_download_button("sprint")

    auswahl = _player_selector("sprint")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"
    alter_sprint = berechne_alter(sp.get("geburtsdatum", "")) if sp else None
    altersgruppe = alter_zu_altersgruppe(alter_sprint or 0)

    letzter = sprint_letzter(sid)
    hist    = sprint_history(sid)

    tab_neu, tab_verlauf, tab_analyse = st.tabs(["📋 Neuer Test", "📈 Verlauf", "🔬 Sprint-Analyse"])

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="sprint_datum")
        # Alter am gewählten Testdatum — nicht heutiges Alter (Spec §3)
        alter_sprint_td = alter_am_datum(
            sp.get("geburtsdatum", "") if sp else "", datum.strftime("%d.%m.%Y")
        ) or alter_sprint
        if datum > date.today():
            st.warning("⚠️ Testdatum liegt in der Zukunft — bitte prüfen.")

        _ALLE_DIST = ["5 m", "10 m", "20 m", "30 m", "40 m"]
        aktive_dist = st.multiselect(
            "Distanzen für diese Sitzung auswählen",
            _ALLE_DIST, default=[], key="sprint_aktive_distanzen",
            help="Nur tatsächlich gemessene Sprintdistanzen auswählen.",
        )
        if not aktive_dist:
            st.info("Wähle mindestens eine Sprintdistanz für diese Sitzung aus.")

        st.markdown("#### Zeiten eingeben (Sekunden) — Versuch 1 / 2 / 3")
        st.caption("0.00 = Versuch nicht durchgeführt. ℹ️-Button neben jeder Distanz für Eingabehilfe.")

        c_l, c_r = st.columns(2)
        # Initialisierung auf None — nur ausgewählte Distanzen rendern
        v1_5  = v2_5  = v3_5  = b5  = None
        v1_10 = v2_10 = v3_10 = b10 = None
        v1_20 = v2_20 = v3_20 = b20 = None
        v1_30 = v2_30 = v3_30 = b30 = None
        v1_40 = v2_40 = v3_40 = b40 = None

        if "5 m"  in aktive_dist:
            v1_5,  v2_5,  v3_5,  b5  = _sprint_eingabe("5 m",  "s5",  letzter, c_l, "sprint_5m",  altersgruppe)
        if "10 m" in aktive_dist:
            v1_10, v2_10, v3_10, b10 = _sprint_eingabe("10 m", "s10", letzter, c_l, "sprint_10m", altersgruppe)
        if "20 m" in aktive_dist:
            v1_20, v2_20, v3_20, b20 = _sprint_eingabe("20 m", "s20", letzter, c_r, "sprint_20m", altersgruppe)
        if "30 m" in aktive_dist:
            v1_30, v2_30, v3_30, b30 = _sprint_eingabe("30 m", "s30", letzter, c_r, "sprint_30m", altersgruppe)
        if "40 m" in aktive_dist:
            v1_40, v2_40, v3_40, b40 = _sprint_eingabe("40 m", "s40", letzter, c_r, "sprint_40m", altersgruppe)

        from sprint import (beschleunigungsindex, bewertung_sprint, bewertung_farbe,
                            SprintErgebnis as _SE)
        res = _SE(beste_5m=b5, beste_10m=b10, beste_20m=b20, beste_30m=b30,
                  geschlecht=geschl, niveau=niveau, alter=alter_sprint_td)

        if any([b5, b10, b20, b30, b40]):
            st.markdown("---")
            m1, m2, m3, m4, m5 = st.columns(5)
            if b10: m1.metric("10 m", f"{b10:.2f} s", res.bewertung_10m)
            if b20: m2.metric("20 m", f"{b20:.2f} s")
            if b30: m3.metric("30 m", f"{b30:.2f} s", res.bewertung_30m)
            if b40: m4.metric("40 m", f"{b40:.2f} s")
            if res.beschl_index: m5.metric("Beschl.-Index", f"{res.beschl_index:.3f}")
            st.caption(f"📊 {_tcap(alter_sprint_td, sp.get('geburtsdatum', '') if sp else '')}")

            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite:
                    st.markdown(f"- {d}")

        # Plausibilitätsprüfung Sprint-Zeiten
        if b5 and b10 and b10 < b5:
            st.warning("⚠️ Plausibilitätsprüfung: Die 10-m-Zeit ist kleiner als die 5-m-Zeit — bitte Eingaben prüfen.")
        if b10 and b20 and b20 < b10:
            st.warning("⚠️ Plausibilitätsprüfung: Die 20-m-Zeit ist kleiner als die 10-m-Zeit — bitte Eingaben prüfen.")
        if b20 and b30 and b30 < b20:
            st.warning("⚠️ Plausibilitätsprüfung: Die 30-m-Zeit ist kleiner als die 20-m-Zeit — bitte Eingaben prüfen.")
        if b30 and b40 and b40 < b30:
            st.warning("⚠️ Plausibilitätsprüfung: Die 40-m-Zeit ist kleiner als die 30-m-Zeit — bitte Eingaben prüfen.")

        # ── Trainerbeobachtungen ────────────────────────────────────────────
        st.markdown("---")
        obs_sprint = render_observation_selector("sprint", sid, datum.strftime("%d.%m.%Y"), "sprint", standalone=False)
        _dup_spr = _duplikat_check("sprint", datum.strftime("%d.%m.%Y"), hist)

        if st.button("💾 Test speichern", use_container_width=True, key="sprint_save", type="primary"):
            if _dup_spr == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            if not any([b5, b10, b20, b30, b40]):
                st.error("Bitte mindestens eine Distanz eingeben.")
            else:
                from sprint import beschleunigungsindex, bewertung_sprint
                import json, datetime as _dtm
                _datum_spr = datum.strftime("%d.%m.%Y")
                if _dup_spr == "zweiter":
                    _datum_spr += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
                sprint_speichern(
                    sid, _datum_spr,
                    v1_5, v2_5, v3_5, b5 or 0,
                    v1_10, v2_10, v3_10, b10 or 0,
                    v1_20, v2_20, v3_20, b20 or 0,
                    v1_30, v2_30, v3_30, b30 or 0,
                    res.beschl_index or 0,
                    res.bewertung_10m, res.bewertung_30m,
                    json.dumps(res.defizite, ensure_ascii=False),
                    v1_40=v1_40, v2_40=v2_40, v3_40=v3_40, b40=b40,
                )
                if obs_sprint["beob_ids"] or obs_sprint.get("freitext"):
                    beobachtung_speichern(
                        sid, "sprint", _datum_spr,
                        json.dumps(obs_sprint["beob_ids"], ensure_ascii=False),
                        obs_sprint["seite"], obs_sprint["auspraegung"],
                        obs_sprint["freitext"], obs_sprint["text_generiert"],
                    )
                _save_ok("Sprint-Test gespeichert!")
                _reset_keys(*[f"{p}_{v}" for p in ["s5", "s10", "s20", "s30", "s40"]
                               for v in ["v1", "v2", "v3"]])
                _reset_keys("sprint_aktive_distanzen")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Sprint-Tests vorhanden.")
            return

        df = pd.DataFrame(hist)
        df.columns = ["Datum", "5 m", "10 m", "20 m", "30 m", "40 m", "Beschl.-Index", "Bew. 10 m"]

        # ── Persönliche Bestleistung ──────────────────────────────────────────
        _pb_trend_cards(df, [
            ("5 m",  "Sprint 5 m",  "s", True),
            ("10 m", "Sprint 10 m", "s", True),
            ("20 m", "Sprint 20 m", "s", True),
            ("30 m", "Sprint 30 m", "s", True),
            ("40 m", "Sprint 40 m", "s", True),
        ])

        # ── Letzter Test ────────────────────────────────────────────────────
        if letzter:
            with st.expander("📋 Letzter gespeicherter Test", expanded=True):
                lt = letzter
                l1, l2, l3, l4, l5, l6 = st.columns(6)
                def _sm(col, label, val):
                    if val and val > 0:
                        col.metric(label, f"{val:.2f} s")
                _sm(l1, "5 m",  lt.get("beste_5m"))
                _sm(l2, "10 m", lt.get("beste_10m"))
                _sm(l3, "20 m", lt.get("beste_20m"))
                _sm(l4, "30 m", lt.get("beste_30m"))
                _sm(l5, "40 m", lt.get("beste_40m"))
                if lt.get("beschl_index"):
                    l6.metric("Beschl.-Index", f"{lt['beschl_index']:.3f}")
                if lt.get("bewertung_10m"):
                    st.caption(f"Bewertung 10 m: **{lt['bewertung_10m']}** | Datum: {lt.get('datum','—')}")
                # Testreferenz basierend auf Alter AM TESTTAG (Spec §6)
                _lt_alter_td = alter_am_datum(
                    sp.get("geburtsdatum","") if sp else "", lt.get("datum","")
                ) if sp and lt.get("datum") else alter_sprint
                if _lt_alter_td is not None:
                    st.caption(f"📊 Testreferenz am Testtag: {_tcap(_lt_alter_td, sp.get('geburtsdatum','') if sp else '')}")

        # ── Verlaufschart ────────────────────────────────────────────────────
        fig = go.Figure()
        for col_name, color in [("10 m", "#3b82f6"), ("20 m", "#3fb950"),
                                  ("30 m", "#d29922"), ("40 m", "#a371f7"), ("5 m", "#f85149")]:
            sub = df[df[col_name] > 0] if col_name in df.columns else pd.DataFrame()
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_name],
                                     mode="lines+markers", name=col_name,
                                     line=dict(color=color, width=2),
                                     marker=dict(size=7)))
        fig.update_layout(**_pl(height=340, title="Sprintzeiten-Verlauf",
                                yaxis=dict(autorange="reversed",
                                           title="Zeit (s) — niedriger = besser")))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Zwei Termine vergleichen ─────────────────────────────────────────
        if len(df) >= 2:
            with st.expander("🔍 Zwei Termine vergleichen"):
                datums = df["Datum"].tolist()
                cd1, cd2 = st.columns(2)
                d1 = cd1.selectbox("Termin 1", datums, index=0, key="spr_cmp_d1")
                d2 = cd2.selectbox("Termin 2", datums, index=len(datums)-1, key="spr_cmp_d2")
                r1 = df[df["Datum"] == d1].iloc[0]
                r2 = df[df["Datum"] == d2].iloc[0]
                compare_cols = ["5 m", "10 m", "20 m", "30 m", "40 m", "Beschl.-Index"]
                rows_cmp = []
                for c in compare_cols:
                    v1_c = r1.get(c, 0) or 0
                    v2_c = r2.get(c, 0) or 0
                    if v1_c > 0 or v2_c > 0:
                        diff = round(v2_c - v1_c, 3) if v1_c > 0 and v2_c > 0 else "—"
                        rows_cmp.append({"Messung": c, d1: f"{v1_c:.2f}" if v1_c else "—",
                                         d2: f"{v2_c:.2f}" if v2_c else "—",
                                         "Differenz": f"{diff:+.3f}" if isinstance(diff, float) else diff})
                if rows_cmp:
                    st.dataframe(pd.DataFrame(rows_cmp), use_container_width=True, hide_index=True)
                    st.caption("Differenz: negativ = schneller, positiv = langsamer")

        # ── Bearbeiten / Löschen ──────────────────────────────────────────────
        st.markdown("---")
        with st.expander("✏️ Eintrag bearbeiten / löschen"):
            _render_sprint_edit(sid)

    # ── Sprint-Analyse Tab (Spec §3, §4, §6, §22, §23, §24, §34) ────────────
    with tab_analyse:
        # Wissenschaftlicher Hinweis — IMMER sichtbar, nie versteckt (Spec §4)
        st.info(
            "**Wissenschaftlicher Hinweis:** Die dargestellten Studienergebnisse zeigen "
            "statistische Zusammenhänge zwischen Muskelvolumen und Sprintgeschwindigkeit. "
            "Sie erlauben keine direkte Diagnose einzelner Muskelschwächen und bedeuten "
            "nicht, dass Muskelgröße allein Sprintleistung verursacht."
        )

        if not letzter:
            st.info("Noch keine Sprint-Tests vorhanden. Bitte zuerst einen Sprint-Test durchführen.")
        else:
            # ── Leistungsbereiche (Spec §6, §34) ─────────────────────────────
            st.markdown("### Sprint-Leistungsbereiche")
            _sprint_leistungsbereiche_ui(letzter, alter_sprint)
            st.caption(f"Letzter Test: **{letzter.get('datum', '—')}**  — nur VALID_DATA wird bewertet.")

            st.markdown("---")

            # ── Mögliche Trainingsschwerpunkte — Mehrquellen-Analyse ────────
            _fms_sa = fms_letzter(sid)
            _yb_sa  = y_balance_letzter(sid)
            from analytics import sprint_trainingsschwerpunkte_ermitteln as _ste6
            _schwerpunkte = _ste6(letzter, _fms_sa, _yb_sa)

            if _schwerpunkte:
                st.markdown("### Mögliche Trainingsschwerpunkte")
                st.caption(
                    "Formulierungen als *mögliche Trainingsbereiche* — keine Muskeldiagnosen aus "
                    "Sprintzeiten allein (Spec §35). Mehrere Testquellen erhöhen die Priorität (Spec §21)."
                )
                _PRIO_FARBE = {3: "#da3633", 2: "#d29922", 1: "#238636"}
                _PRIO_LABEL = {3: "Deutliche Auffälligkeit", 2: "Relevante Auffälligkeit", 1: "Leichte Auffälligkeit"}
                for _sp in _schwerpunkte:
                    _pf = _PRIO_FARBE.get(_sp["prioritaet"], "#58a6ff")
                    _prio_lbl = _PRIO_LABEL.get(_sp["prioritaet"], "—")
                    st.markdown(
                        f"<div style='background:#161b22;border-left:3px solid {_pf};"
                        f"border:1px solid {_pf};border-radius:8px;padding:14px;margin-bottom:8px'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;"
                        f"margin-bottom:6px'>"
                        f"<span style='font-size:14px;font-weight:700;color:#e6edf3'>{_sp['bereich']}</span>"
                        f"<span style='font-size:10px;color:{_pf};background:#21262d;padding:2px 8px;"
                        f"border-radius:10px'>{_prio_lbl}</span></div>"
                        f"<div style='font-size:12px;color:#8b949e;line-height:1.5'>{_sp['beschreibung']}</div>"
                        f"<div style='font-size:10px;color:#6e7681;margin-top:8px'>"
                        f"📊 Grundlage: {', '.join(_sp['quellen'])}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # Warum wird das trainiert? (Spec §23)
                with st.expander("❓ Warum wird das trainiert?"):
                    _bereiche_txt = ", ".join(sp["bereich"] for sp in _schwerpunkte)
                    _quellen_alle = sorted({q for sp in _schwerpunkte for q in sp["quellen"]})
                    st.markdown(
                        f"**Schwerpunkt:** {_bereiche_txt}\n\n"
                        f"**Grundlage:** {', '.join(_quellen_alle)}\n\n"
                        "**Begründung:** Die vorhandenen Sprint- und Bewegungstests zeigen "
                        "Auffälligkeiten in Bereichen, die für eine effiziente Kraftübertragung "
                        "beim Sprint funktionell relevant sein können. Diese Empfehlungen "
                        "beziehen sich auf Trainingsbereiche — keine medizinischen Diagnosen "
                        "oder Muskelbehauptungen aus Sprintzeiten."
                    )

            elif letzter.get("bewertung_10m") or letzter.get("bewertung_30m"):
                st.success(
                    "✅ Aktuelle Sprintwerte zeigen keine relevanten Auffälligkeiten. "
                    "Weiter auf Leistungserhalt und -entwicklung fokussieren."
                )
            else:
                st.info(
                    "Keine ausreichende Bewertungsgrundlage — bitte vollständigen "
                    "Sprint-Test mit 10-m- und 30-m-Zeit durchführen."
                )

            st.markdown("---")

            # ── Wissenschaftlich relevante Muskulatur (Spec §3) ─────────────
            st.markdown("### Wissenschaftlich relevante Muskulatur für Sprintleistung")
            _sprint_muskulatur_info_ui()

            # Wissenschaftlicher Hintergrund (Spec §24)
            with st.expander("📚 Wissenschaftlicher Hintergrund"):
                st.markdown(
                    "Untersuchungen bei College-Footballspielern zeigten deutliche Zusammenhänge "
                    "zwischen maximaler Sprintgeschwindigkeit und insbesondere dem Muskelvolumen "
                    "des **Psoas major** (R²=0,499), **Gluteus medius** (R²=0,451) und "
                    "**Gluteus maximus** (R²=0,365). Eine Kombination aus Psoas major, Gluteus medius "
                    "und Piriformis erklärte dabei ca. **57–59 % der Varianz** der maximalen "
                    "Sprintgeschwindigkeit.\n\n"
                    "**Wichtige Einschränkung:** Diese Ergebnisse zeigen statistische Zusammenhänge "
                    "und bedeuten nicht, dass Muskelgröße allein die Sprintgeschwindigkeit bestimmt. "
                    "Sprintleistung ist **multifaktoriell** — Technik, Explosivkraft, neuromuskuläre "
                    "Ansteuerung, Koordination, Mobilität, Ermüdung und weitere Faktoren spielen "
                    "eine wesentliche Rolle. Aus Sprintzeiten kann *nicht* auf einzelne "
                    "Muskelschwächen geschlossen werden.\n\n"
                    "*Quelle: Studie an 66 College-Footballspielern — Zusammenhang zwischen "
                    "Muskelvolumen unterer Extremität und maximaler Sprintgeschwindigkeit.*"
                )


# ──────────────────────────────────────────────────────────────────────────────

def page_sprung():
    st.markdown("# 🦘 Sprung-Diagnostik")
    _back_button("← Zurück zu Tests", "🔬  Diagnostik", target_sub_diagnostik="🏠 Übersicht", key="back_sprung")
    st.markdown("Explosivkraft, Reaktivkraft und Seitenasymmetrie — CMJ, Squat Jump, Drop Jump, Standweitsprung.")

    sicherheitshinweis_box()
    show_trainer_checkliste("jump")
    show_test_info("jump")
    _anleitung_download_button("jump")

    auswahl = _player_selector("sprung")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"
    alter_sprung = berechne_alter(sp.get("geburtsdatum", "")) if sp else None
    altersgruppe = alter_zu_altersgruppe(alter_sprung or 0)

    letzter = sprung_letzter(sid)
    hist    = sprung_history(sid)

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    def _v3_sprung(label, key_pfx, max_val, step=0.5, col=None, field_id=""):
        """3-Versuch-Eingabe (Höhe cm oder Zeit s) — Bestwert = max()."""
        ct = col if col else st
        lbl_c, info_c = ct.columns([5, 1])
        lbl_c.markdown(f"**{label}**")
        if field_id:
            field_info_col(info_c, "jump", field_id)
        vc1, vc2, vc3, vbest = ct.columns(4)
        vc1.caption("V1"); vc2.caption("V2"); vc3.caption("V3"); vbest.caption("Bestwert")
        v1 = vc1.number_input(key_pfx+"v1", 0.0, max_val, 0.0, step=step,
                               key=f"{key_pfx}_v1", label_visibility="collapsed")
        v2 = vc2.number_input(key_pfx+"v2", 0.0, max_val, 0.0, step=step,
                               key=f"{key_pfx}_v2", label_visibility="collapsed")
        v3 = vc3.number_input(key_pfx+"v3", 0.0, max_val, 0.0, step=step,
                               key=f"{key_pfx}_v3", label_visibility="collapsed")
        vals = [v for v in [v1, v2, v3] if v > 0]
        best = max(vals) if vals else None
        if best:
            vbest.metric("✓", f"{best:.1f}")
            if field_id:
                norm_badge(best, "jump", field_id, ct, altersgruppe=altersgruppe)
        return (v1 or None), (v2 or None), (v3 or None), best

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="sprung_datum")
        # Alter am gewählten Testdatum — nicht heutiges Alter (Spec §3)
        alter_sprung_td = alter_am_datum(
            sp.get("geburtsdatum", "") if sp else "", datum.strftime("%d.%m.%Y")
        ) or alter_sprung
        if datum > date.today():
            st.warning("⚠️ Testdatum liegt in der Zukunft — bitte prüfen.")
        _ALLE_SPRUNG = [
            "CMJ beidbeinig", "CMJ einbeinig rechts", "CMJ einbeinig links",
            "Squat Jump", "Drop Jump — Höhe", "Drop Jump — KZ", "Standweitsprung",
        ]
        aktive_sprung = st.multiselect(
            "Tests für diese Sitzung auswählen",
            _ALLE_SPRUNG, default=[], key="sprung_aktive_tests",
        )
        if not aktive_sprung:
            st.info("Wähle mindestens einen Sprungtest für diese Sitzung aus.")

        st.markdown("#### Sprünge — je 3 Versuche | Bestwert = max(V1, V2, V3)")
        st.caption("0.00 = Versuch nicht durchgeführt")

        c1, c2 = st.columns(2)

        # Initialisierung aller Variablen auf None — nur ausgewählte Tests rendern
        v1_cb = v2_cb = v3_cb = b_cmj_beid = None
        v1_cr = v2_cr = v3_cr = b_cmj_r    = None
        v1_cl = v2_cl = v3_cl = b_cmj_l    = None
        v1_sq = v2_sq = v3_sq = b_squat    = None
        v1_dh = v2_dh = v3_dh = b_dj_h    = None
        v1_dk = v2_dk = v3_dk = b_dj_kz   = None
        v1_sw = v2_sw = v3_sw = b_swj      = None

        if "CMJ beidbeinig" in aktive_sprung:
            v1_cb, v2_cb, v3_cb, b_cmj_beid = _v3_sprung("CMJ beidbeinig (cm)", "cmj_beid_", 100.0, col=c1, field_id="cmj_beid")
        if "CMJ einbeinig rechts" in aktive_sprung:
            v1_cr, v2_cr, v3_cr, b_cmj_r = _v3_sprung("CMJ einbeinig rechts (cm)", "cmj_r_", 80.0, col=c1, field_id="cmj_r")
        if "CMJ einbeinig links" in aktive_sprung:
            v1_cl, v2_cl, v3_cl, b_cmj_l = _v3_sprung("CMJ einbeinig links (cm)",  "cmj_l_", 80.0, col=c1, field_id="cmj_l")
        if b_cmj_r and b_cmj_l:
            c1.markdown(asymmetrie_badge_html(b_cmj_r, b_cmj_l, niedriger_besser=False), unsafe_allow_html=True)
        if "Squat Jump" in aktive_sprung:
            v1_sq, v2_sq, v3_sq, b_squat = _v3_sprung("Squat Jump (cm)", "squat_", 100.0, col=c1, field_id="squat_jump")
        if "Drop Jump — Höhe" in aktive_sprung:
            v1_dh, v2_dh, v3_dh, b_dj_h = _v3_sprung("Drop Jump — Höhe (cm)", "dj_h_", 80.0, col=c2, field_id="dj_hoehe")
        if "Drop Jump — KZ" in aktive_sprung:
            v1_dk, v2_dk, v3_dk, b_dj_kz = _v3_sprung("Drop Jump — KZ (s)", "dj_kz_", 2.0, step=0.01, col=c2, field_id="dj_kontakt")
        if "Standweitsprung" in aktive_sprung:
            v1_sw, v2_sw, v3_sw, b_swj = _v3_sprung("Standweitsprung (cm)", "swj_", 400.0, step=1.0, col=c2, field_id="standweit")

        from sprung import SprungErgebnis as _SpE
        res = _SpE(cmj_beid=b_cmj_beid, cmj_rechts=b_cmj_r, cmj_links=b_cmj_l,
                   squat_jump=b_squat, drop_jump_hoehe=b_dj_h, drop_jump_kz=b_dj_kz,
                   standweit=b_swj, geschlecht=geschl, niveau=niveau, alter=alter_sprung_td)

        if any([b_cmj_beid, b_cmj_r, b_cmj_l, b_squat, b_dj_h, b_swj]):
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if b_cmj_beid: m1.metric("CMJ", f"{b_cmj_beid:.1f} cm", res.bewertung_cmj)
            if b_squat:    m2.metric("Squat Jump", f"{b_squat:.1f} cm")
            if res.rsi:    m3.metric("RSI", f"{res.rsi:.2f}", "gut" if res.rsi >= 1.5 else "niedrig")
            if res.cmj_asymmetrie:
                color_txt = "⚠️ auffällig" if res.cmj_asymmetrie > 10 else "✅ ok"
                m4.metric("Asymmetrie", f"{res.cmj_asymmetrie:.1f} %", color_txt)
            st.caption(f"📊 {_tcap(alter_sprung_td, sp.get('geburtsdatum', '') if sp else '')}")
            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite: st.markdown(f"- {d}")

        # ── Plausibilitätsprüfung ──────────────────────────────────────────
        _sprung_warns = []
        if b_cmj_beid and b_cmj_beid > 80:
            _sprung_warns.append(f"CMJ beidbeinig {b_cmj_beid:.1f} cm (> 80 cm = absoluter Weltklasse-Wert)")
        if b_cmj_r and b_cmj_r > 70:
            _sprung_warns.append(f"CMJ rechts {b_cmj_r:.1f} cm (> 70 cm — bitte prüfen)")
        if b_cmj_l and b_cmj_l > 70:
            _sprung_warns.append(f"CMJ links {b_cmj_l:.1f} cm (> 70 cm — bitte prüfen)")
        if b_swj and b_swj > 330:
            _sprung_warns.append(f"Standweitsprung {b_swj:.0f} cm (> 330 cm = außergewöhnlich)")
        if _sprung_warns:
            st.warning(
                "⚠️ Ungewöhnliche Werte — bitte Eingaben prüfen (Speichern trotzdem möglich):\n"
                + "\n".join(f"• {w}" for w in _sprung_warns)
            )

        st.markdown("---")
        obs_sprung = render_observation_selector("sprung", sid, datum.strftime("%d.%m.%Y"), "sprung", standalone=False)
        _dup_spg = _duplikat_check("sprung", datum.strftime("%d.%m.%Y"), hist)

        if st.button("💾 Test speichern", use_container_width=True, key="sprung_save", type="primary"):
            if _dup_spg == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            if not any([b_cmj_beid, b_cmj_r, b_cmj_l, b_squat, b_dj_h, b_swj]):
                st.error("Bitte mindestens einen Testwert eingeben.")
            else:
                import json, datetime as _dtm
                _datum_spg = datum.strftime("%d.%m.%Y")
                if _dup_spg == "zweiter":
                    _datum_spg += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
                sprung_speichern(
                    sid, _datum_spg,
                    b_cmj_beid or 0, b_cmj_r or 0, b_cmj_l or 0,
                    res.cmj_asymmetrie or 0,
                    b_squat or 0, b_dj_h or 0, b_dj_kz or 0,
                    res.rsi or 0, b_swj or 0,
                    res.bewertung_cmj,
                    json.dumps(res.defizite, ensure_ascii=False),
                    v1_cmj_beid=v1_cb, v2_cmj_beid=v2_cb, v3_cmj_beid=v3_cb,
                    v1_cmj_r=v1_cr,    v2_cmj_r=v2_cr,    v3_cmj_r=v3_cr,
                    v1_cmj_l=v1_cl,    v2_cmj_l=v2_cl,    v3_cmj_l=v3_cl,
                    v1_squat=v1_sq,    v2_squat=v2_sq,    v3_squat=v3_sq,
                    v1_dj_h=v1_dh,     v2_dj_h=v2_dh,     v3_dj_h=v3_dh,
                    v1_dj_kz=v1_dk,    v2_dj_kz=v2_dk,    v3_dj_kz=v3_dk,
                    v1_swj=v1_sw,      v2_swj=v2_sw,       v3_swj=v3_sw,
                )
                if obs_sprung["beob_ids"] or obs_sprung.get("freitext"):
                    beobachtung_speichern(
                        sid, "sprung", _datum_spg,
                        json.dumps(obs_sprung["beob_ids"], ensure_ascii=False),
                        obs_sprung["seite"], obs_sprung["auspraegung"],
                        obs_sprung["freitext"], obs_sprung["text_generiert"],
                    )
                _save_ok("Sprung-Test gespeichert!")
                _reset_keys(*[f"{p}_v{n}" for p in [
                    "cmj_beid_", "cmj_r_", "cmj_l_", "squat_", "dj_h_", "dj_kz_", "swj_",
                ] for n in [1, 2, 3]])
                _reset_keys("sprung_aktive_tests")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Sprung-Tests vorhanden.")
            return

        df = pd.DataFrame(hist)
        df.columns = ["Datum", "CMJ", "Squat Jump", "Drop Jump H.", "RSI",
                      "Standweit", "Asymmetrie %", "Bewertung CMJ"]

        # ── Persönliche Bestleistung ──────────────────────────────────────────
        _pb_trend_cards(df, [
            ("CMJ",        "CMJ Sprunghöhe",  "cm",  False),
            ("Squat Jump", "Squat Jump",       "cm",  False),
            ("RSI",        "Reactive Strength Index", "",   False),
            ("Standweit",  "Standweitsprung",  "cm",  False),
        ])

        c_cmj, c_asym = st.columns(2)
        with c_cmj:
            fig = go.Figure()
            for col_name, color in [("CMJ", "#3b82f6"), ("Squat Jump", "#3fb950")]:
                sub = df[df[col_name] > 0]
                if sub.empty: continue
                fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_name],
                                         mode="lines+markers", name=col_name,
                                         line=dict(color=color, width=2), marker=dict(size=7)))
            fig.update_layout(**_pl(height=280, title="CMJ & Squat Jump (cm)", yaxis=dict(title="cm")))
            st.plotly_chart(fig, use_container_width=True)
        with c_asym:
            sub_a = df[df["Asymmetrie %"] > 0]
            if not sub_a.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=sub_a["Datum"], y=sub_a["Asymmetrie %"],
                                      marker_color=["#f85149" if v > 10 else "#3fb950" for v in sub_a["Asymmetrie %"]],
                                      text=sub_a["Asymmetrie %"].round(1), textposition="outside"))
                fig2.add_hline(y=10, line_dash="dash", line_color="#d29922", annotation_text="Grenzwert 10 %")
                fig2.update_layout(**_pl(height=280, title="CMJ-Asymmetrie links/rechts"))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Keine einbeinigen CMJ-Werte vorhanden.")

        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Zwei Termine vergleichen ──────────────────────────────────────────
        if len(df) >= 2:
            with st.expander("🔍 Zwei Termine vergleichen"):
                datums_sp = df["Datum"].tolist()
                spc1, spc2 = st.columns(2)
                spd1 = spc1.selectbox("Termin 1", datums_sp, index=0, key="spg_cmp_d1")
                spd2 = spc2.selectbox("Termin 2", datums_sp, index=len(datums_sp)-1, key="spg_cmp_d2")
                spr1 = df[df["Datum"] == spd1].iloc[0]
                spr2 = df[df["Datum"] == spd2].iloc[0]
                compare_cols_sp = ["CMJ", "Squat Jump", "Drop Jump H.", "RSI", "Standweit", "Asymmetrie %"]
                rows_sp = []
                for csp in compare_cols_sp:
                    v1sp = float(spr1.get(csp, 0) or 0)
                    v2sp = float(spr2.get(csp, 0) or 0)
                    if v1sp > 0 or v2sp > 0:
                        diff_sp = round(v2sp - v1sp, 2) if v1sp > 0 and v2sp > 0 else "—"
                        rows_sp.append({
                            "Messung": csp,
                            spd1: f"{v1sp:.2f}" if v1sp else "—",
                            spd2: f"{v2sp:.2f}" if v2sp else "—",
                            "Differenz": f"{diff_sp:+.2f}" if isinstance(diff_sp, float) else diff_sp,
                        })
                if rows_sp:
                    st.dataframe(pd.DataFrame(rows_sp), use_container_width=True, hide_index=True)
                    st.caption("Differenz: positiv = höher/weiter, negativ = niedriger/kürzer")

        # ── Bearbeiten / Löschen ──────────────────────────────────────────────
        st.markdown("---")
        with st.expander("✏️ Eintrag bearbeiten / löschen"):
            _render_sprung_edit(sid)


# ──────────────────────────────────────────────────────────────────────────────

def _zeit_eingabe(label: str, key: str, col, letzter=None, letzter_key=None,
                  test_id: str = "", field_id: str = "", altersgruppe: str = "Senior"):
    """Hilfsfunktion: Zeiteingabe mit optionalem ℹ️-Button."""
    if field_id and test_id:
        hdr, info_btn = col.columns([5, 1])
        hdr.markdown(f"**{label}**")
        field_info_col(info_btn, test_id, field_id)
    else:
        col.markdown(f"**{label}**")
    default = float(letzter[letzter_key]) if (letzter and letzter_key and letzter.get(letzter_key)) else 0.0
    help_txt = show_field_help(test_id, field_id) if (test_id and field_id) else None
    v = col.number_input(label, 0.0, 30.0, default, step=0.01, format="%.2f",
                         key=key, label_visibility="collapsed", help=help_txt)
    if v > 0 and test_id and field_id:
        norm_badge(v, test_id, field_id, col, altersgruppe=altersgruppe)
    return v if v > 0 else None


def page_agilitaet():
    st.markdown("# 🔀 Agilität & Richtungswechsel")
    _back_button("← Zurück zu Tests", "🔬  Diagnostik", target_sub_diagnostik="🏠 Übersicht", key="back_agil")
    st.markdown("505-Test, 5-10-5 Shuttle, T-Test, Illinois Agility Run — Richtungswechsel-Fähigkeit und Abbremsstärke.")

    sicherheitshinweis_box()
    show_trainer_checkliste("agility")
    show_test_info("agility")
    _anleitung_download_button("agility")

    auswahl = _player_selector("agil")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    niveau = sp.get("leistungsniveau", "Leistungssport") if sp else "Leistungssport"
    alter_agil = berechne_alter(sp.get("geburtsdatum", "")) if sp else None
    altersgruppe = alter_zu_altersgruppe(alter_agil or 0)

    letzter = agilitaet_letzter(sid)
    hist    = agilitaet_history(sid)

    tab_neu, tab_verlauf, tab_info = st.tabs(["📋 Neuer Test", "📈 Verlauf", "ℹ️ Testbeschreibung"])

    def _v3_agil(label, key_pfx, col, field_id="", max_val=30.0):
        """3-Versuch-Eingabe (Zeiten s) — Bestzeit = min()."""
        if field_id:
            hdr, info = col.columns([5, 1])
            hdr.markdown(f"**{label}**")
            field_info_col(info, "agility", field_id)
        else:
            col.markdown(f"**{label}**")
        vc1, vc2, vc3, vbest = col.columns(4)
        vc1.caption("V1"); vc2.caption("V2"); vc3.caption("V3"); vbest.caption("Bestzeit")
        v1 = vc1.number_input(key_pfx+"v1", 0.0, max_val, 0.0, step=0.01, format="%.2f",
                               key=f"{key_pfx}_v1", label_visibility="collapsed")
        v2 = vc2.number_input(key_pfx+"v2", 0.0, max_val, 0.0, step=0.01, format="%.2f",
                               key=f"{key_pfx}_v2", label_visibility="collapsed")
        v3 = vc3.number_input(key_pfx+"v3", 0.0, max_val, 0.0, step=0.01, format="%.2f",
                               key=f"{key_pfx}_v3", label_visibility="collapsed")
        vals = [v for v in [v1, v2, v3] if v > 0]
        best = min(vals) if vals else None
        if best:
            vbest.metric("s", f"{best:.2f}")
            if field_id:
                norm_badge(best, "agility", field_id, col, altersgruppe=altersgruppe)
        return (v1 or None), (v2 or None), (v3 or None), best

    _ALLE_AGIL = ["505-Test R/L", "5-10-5 Shuttle", "T-Test", "Illinois Agility",
                  "Modified T-Test", "Pro Agility Shuttle", "Arrowhead R/L", "Zig-Zag", "Balsom"]

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="agil_datum")
        # Alter am gewählten Testdatum — nicht heutiges Alter (Spec §3)
        alter_agil_td = alter_am_datum(
            sp.get("geburtsdatum", "") if sp else "", datum.strftime("%d.%m.%Y")
        ) or alter_agil
        if datum > date.today():
            st.warning("⚠️ Testdatum liegt in der Zukunft — bitte prüfen.")

        aktive_agil = st.multiselect(
            "Tests für diese Sitzung aktivieren",
            _ALLE_AGIL, default=[], key="agil_aktive_tests",
        )
        if not aktive_agil:
            st.info("Wähle mindestens einen Test für diese Sitzung aus.")

        st.markdown("#### Zeiten — je 3 Versuche | Bestzeit = min(V1, V2, V3)")
        st.caption("0.00 = Versuch nicht durchgeführt")
        c1, c2 = st.columns(2)

        # ── Standardtests (mit Normbewertung) ─────────────────────────────
        v1_505r=v2_505r=v3_505r=t505_r = None
        v1_505l=v2_505l=v3_505l=t505_l = None
        v1_510=v2_510=v3_510=t5_10_5 = None
        v1_tt=v2_tt=v3_tt=t_test = None
        v1_ill=v2_ill=v3_ill=illinois = None

        if "505-Test R/L" in aktive_agil:
            v1_505r, v2_505r, v3_505r, t505_r = _v3_agil("505-Test rechts (s)", "a505r_", c1, field_id="t505_r")
            v1_505l, v2_505l, v3_505l, t505_l = _v3_agil("505-Test links (s)",  "a505l_", c1, field_id="t505_l")
            if t505_r and t505_l:
                c1.markdown(asymmetrie_badge_html(t505_r, t505_l, niedriger_besser=True), unsafe_allow_html=True)
        if "5-10-5 Shuttle" in aktive_agil:
            v1_510, v2_510, v3_510, t5_10_5 = _v3_agil("5-10-5 Shuttle (s)", "a5105_", c2, field_id="t5_10_5")
        if "T-Test" in aktive_agil:
            v1_tt, v2_tt, v3_tt, t_test = _v3_agil("T-Test (s)", "att_", c2, field_id="t_test")
        if "Illinois Agility" in aktive_agil:
            v1_ill, v2_ill, v3_ill, illinois = _v3_agil("Illinois Agility (s)", "aill_", c1, field_id="illinois")

        # ── Weitere Tests (ohne automatische Normbewertung) ───────────────
        v1_mtt=v2_mtt=v3_mtt=modified_t_test = None
        v1_pa=v2_pa=v3_pa=pro_agility = None
        v1_arr_r=v2_arr_r=v3_arr_r=arrowhead_r = None
        v1_arr_l=v2_arr_l=v3_arr_l=arrowhead_l = None
        v1_zz=v2_zz=v3_zz=zigzag = None
        v1_bal=v2_bal=v3_bal=balsom_t = None

        weitere_aktiv = [t for t in ["Modified T-Test","Pro Agility Shuttle","Arrowhead R/L","Zig-Zag","Balsom"]
                         if t in aktive_agil]
        if weitere_aktiv:
            st.markdown("---")
            st.markdown("##### Weitere Tests (Bestzeit erfassen)")
        if "Modified T-Test" in aktive_agil:
            v1_mtt, v2_mtt, v3_mtt, modified_t_test = _v3_agil("Modified T-Test (s)", "amtt_", c2, field_id="modified_t_test")
        if "Pro Agility Shuttle" in aktive_agil:
            v1_pa, v2_pa, v3_pa, pro_agility = _v3_agil("Pro Agility Shuttle (s)", "apa_", c1, field_id="pro_agility")
        if "Arrowhead R/L" in aktive_agil:
            v1_arr_r, v2_arr_r, v3_arr_r, arrowhead_r = _v3_agil("Arrowhead rechts (s)", "aarrr_", c2, field_id="arrowhead_r")
            v1_arr_l, v2_arr_l, v3_arr_l, arrowhead_l = _v3_agil("Arrowhead links (s)",  "adarrl_", c2, field_id="arrowhead_l")
            if arrowhead_r and arrowhead_l:
                c2.markdown(asymmetrie_badge_html(arrowhead_r, arrowhead_l, niedriger_besser=True), unsafe_allow_html=True)
        if "Zig-Zag" in aktive_agil:
            v1_zz, v2_zz, v3_zz, zigzag = _v3_agil("Zig-Zag Agility (s)", "azz_", c1, field_id="zigzag")
        if "Balsom" in aktive_agil:
            v1_bal, v2_bal, v3_bal, balsom_t = _v3_agil("Balsom Agility Test (s)", "abal_", c2, field_id="balsom")

        from agilitaet import AgilitaetErgebnis as _AE
        res = _AE(t505_r=t505_r, t505_l=t505_l, t5_10_5=t5_10_5,
                  t_test=t_test, illinois=illinois,
                  geschlecht=geschl, niveau=niveau, alter=alter_agil_td)

        alle_werte = [t505_r, t505_l, t5_10_5, t_test, illinois,
                      modified_t_test, pro_agility, arrowhead_r, arrowhead_l, zigzag, balsom_t]

        if any(alle_werte):
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if t505_r:   m1.metric("505 rechts", f"{t505_r:.2f} s",   res.bew_505)
            if t505_l:   m2.metric("505 links",  f"{t505_l:.2f} s")
            if t_test:   m3.metric("T-Test",     f"{t_test:.2f} s",   res.bew_t_test)
            if illinois: m4.metric("Illinois",   f"{illinois:.2f} s", res.bew_illinois)
            st.caption(f"📊 {_tcap(alter_agil_td, sp.get('geburtsdatum', '') if sp else '')}")
            if res.asym_505:
                color = "#f85149" if res.asym_505 > 10 else "#3fb950"
                sign  = "⚠️ auffällig" if res.asym_505 > 10 else "✅ symmetrisch"
                st.markdown(
                    f'<div style="background:#161b22;border:1px solid {color};border-radius:8px;'
                    f'padding:10px 14px;margin:8px 0">'
                    f'<span style="color:{color};font-weight:600">505-Asymmetrie: {res.asym_505:.1f} % — {sign}</span>'
                    f'<br><small style="color:#8b949e">Grenzwert: 10 % (klinisch relevant)</small></div>',
                    unsafe_allow_html=True,
                )
            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite: st.markdown(f"- {d}")

        st.markdown("---")
        obs_agil = render_observation_selector("agilitaet", sid, datum.strftime("%d.%m.%Y"), "agil", standalone=False)
        _dup_agil = _duplikat_check("agil", datum.strftime("%d.%m.%Y"), hist)

        if st.button("💾 Test speichern", use_container_width=True, key="agil_save", type="primary"):
            if _dup_agil == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            if not any(alle_werte):
                st.error("Bitte mindestens einen Testwert eingeben.")
            else:
                import json, datetime as _dtm
                _datum_agil = datum.strftime("%d.%m.%Y")
                if _dup_agil == "zweiter":
                    _datum_agil += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
                agilitaet_speichern(
                    sid, _datum_agil,
                    t505_r or 0, t505_l or 0, res.asym_505 or 0,
                    t5_10_5 or 0, t_test or 0, illinois or 0,
                    res.bew_505, res.bew_t_test, res.bew_illinois,
                    json.dumps(res.defizite, ensure_ascii=False),
                    v1_t505_r=v1_505r, v2_t505_r=v2_505r, v3_t505_r=v3_505r,
                    v1_t505_l=v1_505l, v2_t505_l=v2_505l, v3_t505_l=v3_505l,
                    v1_t5_10_5=v1_510, v2_t5_10_5=v2_510, v3_t5_10_5=v3_510,
                    v1_t_test=v1_tt,   v2_t_test=v2_tt,   v3_t_test=v3_tt,
                    v1_illinois=v1_ill, v2_illinois=v2_ill, v3_illinois=v3_ill,
                    modified_t_test=modified_t_test, pro_agility=pro_agility,
                    arrowhead_r=arrowhead_r, arrowhead_l=arrowhead_l,
                    zigzag=zigzag, balsom=balsom_t,
                    v1_modified_t_test=v1_mtt, v2_modified_t_test=v2_mtt, v3_modified_t_test=v3_mtt,
                    v1_pro_agility=v1_pa, v2_pro_agility=v2_pa, v3_pro_agility=v3_pa,
                    v1_arrowhead_r=v1_arr_r, v2_arrowhead_r=v2_arr_r, v3_arrowhead_r=v3_arr_r,
                    v1_arrowhead_l=v1_arr_l, v2_arrowhead_l=v2_arr_l, v3_arrowhead_l=v3_arr_l,
                    v1_zigzag=v1_zz, v2_zigzag=v2_zz, v3_zigzag=v3_zz,
                    v1_balsom=v1_bal, v2_balsom=v2_bal, v3_balsom=v3_bal,
                )
                if obs_agil["beob_ids"] or obs_agil.get("freitext"):
                    beobachtung_speichern(
                        sid, "agilitaet", _datum_agil,
                        json.dumps(obs_agil["beob_ids"], ensure_ascii=False),
                        obs_agil["seite"], obs_agil["auspraegung"],
                        obs_agil["freitext"], obs_agil["text_generiert"],
                    )
                _save_ok("Agilität-Test gespeichert!")
                _reset_keys(*[f"{p}_v{n}" for p in [
                    "a505r_", "a505l_", "a5105_", "att_", "aill_",
                    "amtt_", "apa_", "aarrr_", "adarrl_", "azz_", "abal_",
                ] for n in [1, 2, 3]])
                _reset_keys("agil_aktive_tests")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Agilität-Tests vorhanden.")
        else:
            df = pd.DataFrame(hist)
            df.columns = ["Datum", "505 R", "505 L", "Asymmetrie %",
                          "5-10-5", "T-Test", "Illinois", "Bew. T-Test",
                          "Mod. T-Test", "Pro Agility", "Arrowhead R", "Arrowhead L",
                          "Zig-Zag", "Balsom"]

            # ── Persönliche Bestleistung ──────────────────────────────────────
            _pb_trend_cards(df, [
                ("505 R",    "505-Test rechts", "s", True),
                ("505 L",    "505-Test links",  "s", True),
                ("T-Test",   "T-Test",          "s", True),
                ("Illinois", "Illinois Agility","s", True),
                ("5-10-5",   "5-10-5 Shuttle",  "s", True),
            ])

            # Letzter Test
            if letzter:
                with st.expander("📋 Letzter gespeicherter Test", expanded=True):
                    la = letzter
                    _agil_zeiten = [
                        ("505 R", la.get("t505_r")), ("505 L", la.get("t505_l")),
                        ("5-10-5", la.get("t5_10_5")), ("T-Test", la.get("t_test")),
                        ("Illinois", la.get("illinois")),
                        ("Mod. T-Test", la.get("modified_t_test")),
                        ("Pro Agility", la.get("pro_agility")),
                        ("Arrow. R", la.get("arrowhead_r")),
                        ("Arrow. L", la.get("arrowhead_l")),
                        ("Zig-Zag", la.get("zigzag")),
                        ("Balsom", la.get("balsom")),
                    ]
                    vorh = [(lbl, v) for lbl, v in _agil_zeiten if v and float(v) > 0]
                    if vorh:
                        cols_la = st.columns(min(len(vorh), 6))
                        for i, (lbl, v) in enumerate(vorh[:6]):
                            cols_la[i].metric(lbl, f"{float(v):.2f} s")
                        if len(vorh) > 6:
                            cols_la2 = st.columns(len(vorh) - 6)
                            for i, (lbl, v) in enumerate(vorh[6:]):
                                cols_la2[i].metric(lbl, f"{float(v):.2f} s")
                    st.caption(f"Datum: {la.get('datum','—')}")

            fig = go.Figure()
            for col_name, clr in [("T-Test","#3b82f6"),("Illinois","#3fb950"),
                                   ("5-10-5","#d29922"),("505 R","#f85149"),("505 L","#a371f7"),
                                   ("Mod. T-Test","#79c0ff"),("Pro Agility","#56d364"),
                                   ("Arrowhead R","#ffa657"),("Arrowhead L","#ff7b72"),
                                   ("Zig-Zag","#bc8cff"),("Balsom","#e3b341")]:
                if col_name not in df.columns: continue
                sub = df[df[col_name] > 0]
                if sub.empty: continue
                fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_name],
                                         mode="lines+markers", name=col_name,
                                         line=dict(color=clr, width=2), marker=dict(size=7)))
            fig.update_layout(**_pl(height=350, title="Agilitätszeiten-Verlauf (s)",
                                    yaxis=dict(autorange="reversed", title="Zeit (s)")))
            st.plotly_chart(fig, use_container_width=True)

            sub_a = df[df["Asymmetrie %"] > 0]
            if not sub_a.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=sub_a["Datum"], y=sub_a["Asymmetrie %"],
                    marker_color=["#f85149" if v > 10 else "#3fb950" for v in sub_a["Asymmetrie %"]],
                    text=sub_a["Asymmetrie %"].round(1), textposition="outside",
                ))
                fig2.add_hline(y=10, line_dash="dash", line_color="#d29922", annotation_text="Grenzwert 10 %")
                fig2.update_layout(**_pl(height=240, title="505-Asymmetrie R vs. L (%)"))
                st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

            if len(df) >= 2:
                with st.expander("🔍 Zwei Termine vergleichen"):
                    datums_a = df["Datum"].tolist()
                    ac1, ac2 = st.columns(2)
                    ad1 = ac1.selectbox("Termin 1", datums_a, index=0, key="agil_cmp_d1")
                    ad2 = ac2.selectbox("Termin 2", datums_a, index=len(datums_a)-1, key="agil_cmp_d2")
                    ar1 = df[df["Datum"] == ad1].iloc[0]
                    ar2 = df[df["Datum"] == ad2].iloc[0]
                    cmp_cols_a = ["505 R","505 L","5-10-5","T-Test","Illinois",
                                  "Mod. T-Test","Pro Agility","Arrowhead R","Arrowhead L","Zig-Zag","Balsom"]
                    rows_a = []
                    for ca in cmp_cols_a:
                        if ca not in df.columns: continue
                        v1a = ar1.get(ca, 0) or 0
                        v2a = ar2.get(ca, 0) or 0
                        if v1a > 0 or v2a > 0:
                            diff_a = round(v2a - v1a, 3) if v1a > 0 and v2a > 0 else "—"
                            rows_a.append({"Test": ca, ad1: f"{v1a:.2f}" if v1a else "—",
                                           ad2: f"{v2a:.2f}" if v2a else "—",
                                           "Differenz": f"{diff_a:+.3f}" if isinstance(diff_a, float) else diff_a})
                    if rows_a:
                        st.dataframe(pd.DataFrame(rows_a), use_container_width=True, hide_index=True)
                        st.caption("Differenz: negativ = schneller, positiv = langsamer")

            # ── Bearbeiten / Löschen ──────────────────────────────────────────
            st.markdown("---")
            with st.expander("✏️ Eintrag bearbeiten / löschen"):
                _render_agilitaet_edit(sid)

    with tab_info:
        # ── Standardtests mit Normbewertung ──────────────────────────────────
        st.markdown("#### Standardtests — mit automatischer Normbewertung ✅")
        _agil_info_std = [
            ("assets/tests/agility/test_505.svg",    "505-Test R/L",
             "10 m anlaufen → 180° Wendung → 5 m Sprint\nGetrennt für rechts und links. Asymmetrie > 10 % = trainingsrelevant."),
            ("assets/tests/agility/shuttle_5_10_5.svg", "5-10-5 Shuttle",
             "5 m links → 10 m rechts → 5 m zurück zur Mitte\nShuttle-Beschleunigung und Abbremsfähigkeit."),
            ("assets/tests/agility/t_test.svg",      "T-Test",
             "9,14 m vor → je 4,57 m seitwärts → rückwärts\nMehrdirektionale Agilität: vorwärts, lateral, rückwärts."),
            ("assets/tests/agility/illinois.svg",    "Illinois Agility",
             "10 m Slalomkurs mit 8 Kegeln\nGesamtagilität und Richtungswechselgeschwindigkeit."),
        ]
        cols_std = st.columns(4)
        for i, (svg, name, desc) in enumerate(_agil_info_std):
            with cols_std[i]:
                st.markdown(f"**{name}**")
                try:
                    st.image(svg, width="stretch")
                except Exception:
                    st.caption("(Skizze nicht verfügbar)")
                st.caption(desc)

        st.markdown("---")
        st.markdown("#### Weitere Tests — Bestzeit erfassen")
        _agil_info_neu = [
            ("assets/tests/agility/modified_t_test.svg", "Modified T-Test",
             "Kürzere T-Test-Variante\nStart → A (9,15 m) → B links → C rechts → A → Start"),
            ("assets/tests/agility/pro_agility.svg",     "Pro Agility Shuttle",
             "NFL-Combine-Standard (5-10-5)\n5 yd links → 10 yd rechts → 5 yd zurück"),
            ("assets/tests/agility/arrowhead.svg",       "Arrowhead R/L",
             "Pfeilförmiges Muster, bilateral\nStart → Spitze → Kegel rechts/links → Start"),
            ("assets/tests/agility/zigzag.svg",          "Zig-Zag Agility",
             "4–5 Kegel im Zickzack\nca. 20–25 m, Kurskontrolle"),
            ("assets/tests/agility/balsom.svg",          "Balsom Agility Test",
             "4×4 m Rechteck + Mittelpunkt\n3 Läufe à 25 s, Richtungswechsel zählen"),
        ]
        cols_neu = st.columns(5)
        for i, (svg, name, desc) in enumerate(_agil_info_neu):
            with cols_neu[i]:
                st.markdown(f"**{name}**")
                try:
                    st.image(svg, width="stretch")
                except Exception:
                    st.caption("(Skizze nicht verfügbar)")
                st.caption(desc)


# ──────────────────────────────────────────────────────────────────────────────

ALTERSGRUPPEN_YO = ["U8/U9", "U10/U11", "U12/U13", "U13/U14", "U15/U16", "U17/U18", "Senioren"]


# ──────────────────────────────────────────────────────────────────────────────
# SPIROERGOMETRIE-STUFENTEST (innerhalb Ausdauerbereich)
# ──────────────────────────────────────────────────────────────────────────────

def _page_spiro():
    """Spiroergometrie-Stufentest — Eingabe, Auswertung, Verlauf & Vergleich."""
    from spiro import (
        interpoliere_bei_laktat as _ibl,
        kurvenverschiebung_bewerten as _kvb,
        protokolle_vergleichbar as _pv,
        schwellenvergleich_tabelle as _svt,
        trainingsbereiche_aus_schwellen as _tbs,
        spiro_bewertung_v2 as _spiro_bewertung_v2,
        BRUCE_STUFEN, GERAETEARTEN, SCHWELLENMETHODEN,
    )

    st.markdown(
        '<div style="background:#1a2233;border:1px solid #3b82f6;border-radius:8px;'
        'padding:12px 16px;margin-bottom:14px;font-size:13px;color:#cdd9e5">'
        'ℹ️ <b>Hinweis:</b> Diese App führt keine Spiroergometrie durch. Sie dient zur '
        'strukturierten Erfassung, Auswertung und Verlaufskontrolle von Ergebnissen '
        'fachgerecht durchgeführter Tests. Sportliche Auswertung — kein Ersatz für eine ärztliche Untersuchung.'
        '</div>',
        unsafe_allow_html=True,
    )

    auswahl = _player_selector("spiro")
    if not auswahl:
        return
    sid = auswahl["id"]

    alle_tests      = spiro_test_alle(sid)
    alle_protokolle = spiro_protokoll_alle()

    tab_neu, tab_ausw, tab_vgl = st.tabs([
        "📋 Neuer Test", "📊 Auswertung", "📈 Verlauf & Vergleich"
    ])

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 1 — NEUER TEST
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_neu:
        # ── Protokoll ─────────────────────────────────────────────────────────
        st.markdown("### Testprotokoll")
        prot_optionen = ["— Kein Protokoll —"] + [
            f"{p['name']} ({p.get('geraeteart','?')}, "
            f"Start {p.get('startgeschwindigkeit','?')} km/h, "
            f"+{p.get('steigerung','?')} km/h, "
            f"{p.get('stufendauer','?')} min)"
            for p in alle_protokolle
        ]
        prot_wahl = st.selectbox("Protokoll auswählen", prot_optionen, key="spiro_prot_wahl")
        prot_id   = None
        if prot_wahl != "— Kein Protokoll —" and alle_protokolle:
            prot_idx = prot_optionen.index(prot_wahl) - 1
            prot_id  = alle_protokolle[prot_idx]["id"] if 0 <= prot_idx < len(alle_protokolle) else None

        with st.expander("➕ Neues Protokoll erstellen / speichern"):
            pn_name = st.text_input("Protokollname *", key="prot_name",
                                    placeholder="z.B. IAT-Laufband-Standard 3 min")
            pc1, pc2 = st.columns(2)
            pn_geraet    = pc1.selectbox("Geräteart", GERAETEARTEN, key="prot_geraet")
            pn_start     = pc1.number_input("Startgeschwindigkeit (km/h)", 2.0, 20.0, 8.0, 0.5, key="prot_start")
            pn_steigerung= pc2.number_input("Steigerung pro Stufe (km/h)",  0.5,  4.0, 2.0, 0.5, key="prot_steig")
            pn_dauer     = pc2.number_input("Stufendauer (min)",             1.0, 10.0, 3.0, 0.5, key="prot_dauer")
            pn_steigung  = pc1.number_input("Laufbandsteigung (%)",          0.0, 15.0, 1.0, 0.5, key="prot_steigung")
            pn_pause     = pc2.number_input("Pausendauer Blutabnahme (s)",     0,  120,  30,   5, key="prot_pause")
            if st.button("💾 Protokoll speichern", key="prot_save", type="primary", use_container_width=True):
                if not pn_name.strip():
                    st.error("Protokollname ist erforderlich.")
                else:
                    spiro_protokoll_speichern(
                        pn_name.strip(), pn_geraet, pn_start, pn_steigerung,
                        pn_dauer, pn_steigung, pn_pause / 60,
                    )
                    st.success("✅ Protokoll gespeichert.")
                    st.rerun()

        st.markdown("---")

        # ── Testmetadaten ─────────────────────────────────────────────────────
        st.markdown("### Testdaten")
        d1, d2 = st.columns(2)
        # Datum nach erfolgreichem Speichern erhalten (spiro_saved_datum wird beim Speichern gesetzt)
        if "spiro_saved_datum" in st.session_state and "spiro_datum" not in st.session_state:
            st.session_state["spiro_datum"] = st.session_state.pop("spiro_saved_datum")
        elif "spiro_saved_datum" in st.session_state:
            st.session_state.pop("spiro_saved_datum", None)
        datum_spiro = d1.date_input("Testdatum *", value=date.today(), key="spiro_datum")
        if datum_spiro > date.today():
            d1.warning("⚠️ Datum in der Zukunft.")
        geraeteart_spiro = d2.selectbox("Geräteart *", GERAETEARTEN, key="spiro_geraet")
        d3, d4 = st.columns(2)
        testort_spiro = d3.text_input("Testort", key="spiro_testort")
        tester_spiro  = d4.text_input("Tester / Trainer", key="spiro_tester")

        st.markdown("**Testumfang (Mehrfachauswahl möglich)**")
        tm1, tm2 = st.columns(2)
        mit_spiro_cb  = tm1.checkbox("Mit Atemgasanalyse (Spirometrie)", key="spiro_mit_spiro")
        mit_laktat_cb = tm2.checkbox("Mit kapillarer Laktatmessung",     key="spiro_mit_laktat")

        with st.expander("Optionale Testbedingungen"):
            oc1, oc2 = st.columns(2)
            raumtemp_spiro = oc1.number_input("Raumtemperatur (°C)", -10.0, 45.0, 20.0, 0.5, key="spiro_temp")
            kgew_default   = float((anthropometrie_letzter(sid) or {}).get("gewicht") or 75.0)
            kgew_spiro     = oc2.number_input("Körpergewicht (kg)", 20.0, 200.0, kgew_default, 0.5, key="spiro_kgew")
            mahlzeit_spiro = oc1.text_input("Letzte Mahlzeit (wann, was)", key="spiro_mahlzeit")
            einheit_spiro  = oc2.text_input("Letzte intensive Einheit (wann)", key="spiro_letzte_einheit")
            beschw_spiro   = st.text_area("Akute Beschwerden", key="spiro_beschw", height=55)

        # Laktat-Sicherheitshinweis
        ruhelaktat_spiro = None
        blut_ort_spiro   = None
        geraet_spiro     = None
        if mit_laktat_cb:
            st.warning(
                "⚠️ **Sicherheitshinweis Laktatmessung:** Kapillare Blutentnahmen dürfen nur von "
                "entsprechend eingewiesenen Personen unter Einhaltung der geltenden Hygiene-, "
                "Arbeitsschutz- und Entsorgungsvorgaben durchgeführt werden. "
                "Diese App ist kein Ersatz für eine fachliche Einweisung."
            )
            ll1, ll2 = st.columns(2)
            ruhelaktat_spiro = ll1.number_input(
                "Ruhe-Laktat (mmol/l) — leer lassen wenn nicht gemessen",
                0.0, 20.0, 0.0, 0.1, key="spiro_ruhelaktat",
            )
            blut_ort_spiro = ll2.selectbox(
                "Blutentnahmeort", ["Ohrläppchen", "Fingerbeere", "Anderes"], key="spiro_blut_ort"
            )
            geraet_spiro = ll1.text_input("Messgerät / Chargennummer", key="spiro_laktat_geraet")

        st.markdown("---")

        # ── Stufentabelle (dynamisch via st.data_editor) ──────────────────────
        st.markdown("### Belastungsstufen")
        st.caption(
            "Stufen manuell eintragen oder bei ausgewähltem Protokoll automatisch befüllen. "
            "Fehlende Messwerte **leer lassen** — nicht 0 eintragen."
        )

        # Spalten je nach Testumfang
        base_stufen_cols = [
            "Stufe", "Geschw. (km/h)", "Steigung (%)", "Dauer (s)", "HF Ende (bpm)", "RPE (0–10)",
            "✓ vollst.", "Bemerkung",
        ]
        base_stufen_keys = [
            "stufennummer", "geschwindigkeit_kmh", "steigung_prozent",
            "dauer_sekunden", "herzfrequenz_bpm", "rpe", "stufe_vollstaendig", "bemerkung",
        ]
        if mit_laktat_cb:
            base_stufen_cols += ["Laktat (mmol/l)", "Probe ✓"]
            base_stufen_keys += ["laktat_mmol_l", "blutprobe_gueltig"]
        if mit_spiro_cb:
            base_stufen_cols += ["VO₂ rel. (ml/kg/min)", "VO₂ abs. (l/min)", "RER"]
            base_stufen_keys += ["vo2_relativ", "vo2_absolut", "rer"]

        # Auto-Befüllung aus Protokoll
        if st.button("🔄 Stufen aus Protokoll befüllen", key="spiro_fill_prot",
                     disabled=(prot_id is None)):
            p_data = next((p for p in alle_protokolle if p["id"] == prot_id), None)
            if p_data:
                n_max = int(p_data.get("max_stufen") or 10)
                _ist_bruce_fill = (
                    p_data.get("geraeteart") == "Laufband"
                    and "bruce" in str(p_data.get("name") or "").lower()
                )
                if _ist_bruce_fill:
                    n_max = min(n_max, len(BRUCE_STUFEN))
                if not _ist_bruce_fill and (
                    not p_data.get("startgeschwindigkeit") or not p_data.get("steigerung")
                ):
                    st.warning("⚠️ Für dieses Protokoll fehlen Startgeschwindigkeit oder Steigerung.")
                    n_max = 0
                rows = []
                for i in range(n_max):
                    if _ist_bruce_fill and i < len(BRUCE_STUFEN):
                        v_kmh, _steigung, _dauer_s = BRUCE_STUFEN[i]
                    else:
                        v_kmh = round(p_data["startgeschwindigkeit"] + i * p_data["steigerung"], 1)
                        _steigung = p_data.get("steigung", 0)
                        _dauer_s = float(p_data.get("stufendauer") or 0) * 60
                    row   = dict(zip(base_stufen_cols,
                                    [i+1, v_kmh, _steigung, _dauer_s,
                                     None, None, True, ""] +
                                    ([None, True] if mit_laktat_cb else []) +
                                    ([None, None, None] if mit_spiro_cb else [])))
                    rows.append(row)
                st.session_state[f"spiro_editor_{sid}_data"] = rows

        # data_editor
        existing_rows = st.session_state.get(f"spiro_editor_{sid}_data", [])
        df_init = (pd.DataFrame(existing_rows, columns=base_stufen_cols)
                   if existing_rows else pd.DataFrame(columns=base_stufen_cols))

        col_cfg = {
            "Stufe":            st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
            "Geschw. (km/h)":   st.column_config.NumberColumn(min_value=0, step=0.5, format="%.1f"),
            "Steigung (%)":     st.column_config.NumberColumn(min_value=0, step=0.5, format="%.1f"),
            "Dauer (s)":        st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
            "HF Ende (bpm)":    st.column_config.NumberColumn(min_value=0, max_value=250, step=1),
            "RPE (0–10)":       st.column_config.NumberColumn(min_value=0, max_value=10,  step=1),
            "✓ vollst.":        st.column_config.CheckboxColumn(default=True),
            "Laktat (mmol/l)":  st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f",
                                    help="Leer lassen wenn nicht gemessen — nicht 0 eintragen"),
            "Probe ✓":          st.column_config.CheckboxColumn(default=True),
            "VO₂ rel. (ml/kg/min)": st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
            "VO₂ abs. (l/min)": st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
            "RER":              st.column_config.NumberColumn(min_value=0, step=0.01, format="%.2f"),
        }
        edited_stufen = st.data_editor(
            df_init,
            num_rows="dynamic",
            use_container_width=True,
            key=f"spiro_stufen_editor_{sid}",
            column_config={k: v for k, v in col_cfg.items() if k in base_stufen_cols},
        )

        # Plausibilitätsprüfung
        if not edited_stufen.empty:
            df_check = edited_stufen.dropna(subset=["Stufe"])
            if df_check["Stufe"].duplicated().any():
                st.warning("⚠️ Doppelte Stufennummern erkannt.")
            hf_vals = df_check.get("HF Ende (bpm)", pd.Series()).dropna()
            if len(hf_vals) and ((hf_vals <= 0).any() or (hf_vals > 250).any()):
                st.warning("⚠️ Herzfrequenz außerhalb des Bereichs 1–250 bpm.")
            if mit_laktat_cb and "Laktat (mmol/l)" in df_check.columns:
                lak = df_check["Laktat (mmol/l)"].dropna()
                if (lak < 0).any():
                    st.warning("⚠️ Negativer Laktatwert erkannt.")
                if (lak == 0).any():
                    st.warning("⚠️ Laktat = 0 mmol/l: Bitte leer lassen wenn nicht gemessen.")

        # Nachbelastung
        edited_nb = None
        if mit_laktat_cb or mit_spiro_cb:
            st.markdown("---")
            st.markdown("### Nachbelastungswerte (optional)")
            nb_df = pd.DataFrame(
                [{"Zeit (min)": t, "HF (bpm)": None, "Laktat (mmol/l)": None, "Bemerkung": ""}
                 for t in [1, 3, 5]],
            )
            edited_nb = st.data_editor(
                nb_df, num_rows="dynamic", use_container_width=True, key=f"spiro_nb_{sid}",
                column_config={
                    "Zeit (min)":       st.column_config.NumberColumn(min_value=0, step=1),
                    "HF (bpm)":         st.column_config.NumberColumn(min_value=0, max_value=250, step=1),
                    "Laktat (mmol/l)":  st.column_config.NumberColumn(min_value=0, step=0.1, format="%.1f"),
                },
            )

        # Atemgas-Kennwerte
        vo2_peak_v = vo2_max_v = hf_max_spiro = None
        vt1_v_s = vt1_h_s = vt2_v_s = vt2_h_s = None
        if mit_spiro_cb:
            st.markdown("---")
            st.markdown("### Atemgas-Kennwerte (Spiro-Zusammenfassung)")
            st.caption("Direkt gemessene Werte aus dem Spiroergometrie-Gerät — kein VO₂max ohne Ausbelastungsnachweis.")
            sg1, sg2, sg3 = st.columns(3)
            vo2_peak_v   = sg1.number_input("VO₂peak (ml/kg/min)", 0.0, 100.0, 0.0, 0.1, key="spiro_vo2peak")
            vo2_max_v    = sg2.number_input("VO₂max — nur wenn Kriterien erfüllt", 0.0, 100.0, 0.0, 0.1, key="spiro_vo2max")
            hf_max_spiro = sg3.number_input("HF max (bpm)", 0, 250, 0, 1, key="spiro_hf_max")
            sg4, sg5 = st.columns(2)
            vt1_v_s = sg4.number_input("VT1 Geschwindigkeit (km/h)", 0.0, 30.0, 0.0, 0.1, key="spiro_vt1_v")
            vt1_h_s = sg5.number_input("VT1 Herzfrequenz (bpm)",     0, 250, 0, 1, key="spiro_vt1_hf")
            vt2_v_s = sg4.number_input("VT2 Geschwindigkeit (km/h)", 0.0, 30.0, 0.0, 0.1, key="spiro_vt2_v")
            vt2_h_s = sg5.number_input("VT2 Herzfrequenz (bpm)",     0, 250, 0, 1, key="spiro_vt2_hf")
            st.info("ℹ️ VO₂max gilt nur bei dokumentierten Ausbelastungskriterien (RER ≥ 1,10, plateau, HF max). Ohne Nachweis: VO₂peak verwenden.")

        # Maximale Werte & Schwelle
        st.markdown("---")
        st.markdown("### Maximale Testwerte")
        mv1, mv2 = st.columns(2)
        v_max_spiro = mv1.number_input("Maximale Geschwindigkeit (km/h)", 0.0, 40.0, 0.0, 0.1, key="spiro_v_max")
        rpe_max_s   = mv2.number_input("RPE max (0–10)", 0, 10, 10, 1, key="spiro_rpe_max")
        abbruch_s   = st.text_input("Abbruchgrund (falls nicht vollständig absolviert)", key="spiro_abbruch")

        # ── Auto-Schwellenberechnung (aus Laktat-Kurve) ──────────────────────
        if mit_laktat_cb and not edited_stufen.empty:
            _auto_stufen = []
            for _, _row in edited_stufen.dropna(subset=["Stufe"]).iterrows():
                _auto_stufen.append({
                    "geschwindigkeit_kmh": _row.get("Geschw. (km/h)"),
                    "laktat_mmol_l":       _row.get("Laktat (mmol/l)"),
                    "herzfrequenz_bpm":    _row.get("HF Ende (bpm)"),
                    "blutprobe_gueltig":   _row.get("Probe ✓", True),
                })
            _hat_laktat = any(
                s["laktat_mmol_l"] is not None and not (isinstance(s["laktat_mmol_l"], float) and pd.isna(s["laktat_mmol_l"]))
                for s in _auto_stufen
            )
            if _hat_laktat:
                ac1, ac2 = st.columns([3, 1])
                ac1.caption("💡 Laktat-Daten vorhanden — Schwellenwerte können automatisch berechnet werden (2 mmol/l oder 4 mmol/l Interpolation).")
                _calc_ziel = ac2.selectbox("Ziel-Laktat", ["2 mmol/l", "4 mmol/l"], key="spiro_calc_ziel")
                if st.button("🔢 Schwellen automatisch berechnen", key="spiro_auto_calc"):
                    _lak_ziel = 2.0 if "2" in _calc_ziel else 4.0
                    _res_v = _ibl(_auto_stufen, _lak_ziel)
                    if _res_v:
                        st.session_state["spiro_schw_v"]    = float(_res_v["x_wert"])
                        st.session_state["spiro_schwmeth"]  = f"Fixer Wert {int(_lak_ziel)} mmol/l"
                        # Schwellen-HF per linearer Interpolation auf geschw ermitteln
                        _res_hf = _ibl(
                            [{"geschwindigkeit_kmh": s["geschwindigkeit_kmh"],
                              "laktat_mmol_l": s["herzfrequenz_bpm"],
                              "blutprobe_gueltig": True}
                             for s in _auto_stufen if s.get("herzfrequenz_bpm") and s.get("geschwindigkeit_kmh")],
                            _res_v["x_wert"],
                        )
                        if _res_hf:
                            st.session_state["spiro_schw_hf"] = float(_res_hf["x_wert"])
                        st.session_state["spiro_schw_lak"] = _lak_ziel
                        st.success(f"✅ Schwelle bei {_lak_ziel} mmol/l → {_res_v['x_wert']:.1f} km/h berechnet. Werte in Expander übernommen.")
                    else:
                        st.warning(f"⚠️ Interpolation bei {_lak_ziel} mmol/l nicht möglich — Laktat-Wert liegt außerhalb des gemessenen Bereichs.")

        with st.expander("Schwellenwert eintragen / überschreiben"):
            schw_meth = st.selectbox("Schwellenmethode", ["—"] + SCHWELLENMETHODEN, key="spiro_schwmeth")
            sw1, sw2, sw3 = st.columns(3)
            schw_v   = sw1.number_input("Schwelle Geschwindigkeit (km/h)", 0.0, 30.0, step=0.1, format="%.1f", key="spiro_schw_v")
            schw_hf  = sw2.number_input("Schwelle Herzfrequenz (bpm)",     0, 250, step=1, key="spiro_schw_hf")
            schw_lak = sw3.number_input("Schwelle Laktat (mmol/l)",        0.0, 20.0, step=0.1, format="%.1f", key="spiro_schw_lak")
            st.caption("✏️ Berechnete Werte können hier manuell angepasst oder überschrieben werden.")

        bemerkung_s = st.text_area("Bemerkungen", key="spiro_bemerkung", height=65)

        # ── Speichern ─────────────────────────────────────────────────────────
        st.markdown("---")
        if st.button("💾 Stufentest speichern", use_container_width=True, key="spiro_save", type="primary"):
            df_valid = edited_stufen.dropna(subset=["Stufe"]) if not edited_stufen.empty else pd.DataFrame()
            if df_valid.empty:
                st.error("Bitte mindestens eine Belastungsstufe eintragen.")
            else:
                # HF max automatisch aus Stufen wenn nicht manuell
                hf_max_eff = hf_max_spiro or None
                if not hf_max_eff and "HF Ende (bpm)" in df_valid.columns:
                    hf_series = df_valid["HF Ende (bpm)"].dropna()
                    if not hf_series.empty:
                        hf_max_eff = float(hf_series.max())
                v_max_eff = v_max_spiro or None
                if not v_max_eff and "Geschw. (km/h)" in df_valid.columns:
                    v_series = df_valid["Geschw. (km/h)"].dropna()
                    if not v_series.empty:
                        v_max_eff = float(v_series.max())

                testtyp_s = (
                    "spiro_laufband" if "Laufband" in geraeteart_spiro
                    else "spiro_feld" if "Feld" in geraeteart_spiro
                    else "spiro_fahrrad_optional"
                )
                test_id = spiro_test_speichern(
                    spieler_id=sid,
                    datum=datum_spiro.strftime("%Y-%m-%d"),
                    testtyp=testtyp_s,
                    geraeteart=geraeteart_spiro,
                    protokoll_id=prot_id,
                    testort=testort_spiro or None,
                    tester=tester_spiro or None,
                    mit_spiro=1 if mit_spiro_cb else 0,
                    mit_laktat=1 if mit_laktat_cb else 0,
                    raumtemperatur=raumtemp_spiro if raumtemp_spiro != 20.0 else None,
                    letzte_mahlzeit=mahlzeit_spiro or None,
                    letzte_intensive_einheit=einheit_spiro or None,
                    akute_beschwerden=beschw_spiro or None,
                    koerpergewicht=kgew_spiro if kgew_spiro != 75.0 else None,
                    maximale_geschwindigkeit=v_max_eff,
                    maximale_herzfrequenz=hf_max_eff,
                    vo2_peak=vo2_peak_v or None,
                    vo2_max=vo2_max_v or None,
                    vt1_geschwindigkeit=vt1_v_s or None,
                    vt1_herzfrequenz=vt1_h_s or None,
                    vt2_geschwindigkeit=vt2_v_s or None,
                    vt2_herzfrequenz=vt2_h_s or None,
                    laktatschwelle_methode=schw_meth if schw_meth != "—" else None,
                    schwelle_geschwindigkeit=schw_v or None,
                    schwelle_herzfrequenz=schw_hf or None,
                    schwelle_laktat=schw_lak or None,
                    ruhelaktat=ruhelaktat_spiro if (ruhelaktat_spiro and ruhelaktat_spiro > 0) else None,
                    laktat_blutentnahmeort=blut_ort_spiro,
                    laktat_messgeraet=geraet_spiro or None,
                    rpe_max=rpe_max_s or None,
                    abbruchgrund=abbruch_s or None,
                    bemerkung=bemerkung_s or None,
                )
                # Stufen speichern
                stufen_liste = []
                for _, row in df_valid.iterrows():
                    stufe_dict = {}
                    for col_name, key_name in zip(base_stufen_cols, base_stufen_keys):
                        val = row.get(col_name)
                        if val is None or (isinstance(val, float) and pd.isna(val)):
                            stufe_dict[key_name] = None
                        else:
                            stufe_dict[key_name] = val
                    # Laktat 0 → None (keine Messung)
                    if stufe_dict.get("laktat_mmol_l") == 0:
                        stufe_dict["laktat_mmol_l"] = None
                    stufen_liste.append(stufe_dict)
                spiro_stufen_speichern(test_id, stufen_liste)
                # Nachbelastung speichern
                if edited_nb is not None and not edited_nb.empty:
                    nb_liste = []
                    for _, nb_row in edited_nb.iterrows():
                        t_min = nb_row.get("Zeit (min)")
                        if t_min is None or (isinstance(t_min, float) and pd.isna(t_min)):
                            continue
                        nb_liste.append({
                            "zeitpunkt_minuten": t_min,
                            "herzfrequenz_bpm": None if (nb_row.get("HF (bpm)") is None or pd.isna(nb_row.get("HF (bpm)", float("nan")))) else nb_row["HF (bpm)"],
                            "laktat_mmol_l":    None if (nb_row.get("Laktat (mmol/l)") is None or pd.isna(nb_row.get("Laktat (mmol/l)", float("nan")))) else nb_row["Laktat (mmol/l)"],
                            "bemerkung":        nb_row.get("Bemerkung") or None,
                        })
                    spiro_nachbelastung_speichern(test_id, nb_liste)
                # Datum und Tester erhalten, alles andere zurücksetzen
                _saved_date = datum_spiro
                _clear_keys = [
                    "spiro_mit_spiro", "spiro_mit_laktat",
                    "spiro_vo2peak", "spiro_vo2max", "spiro_hf_max",
                    "spiro_vt1_v", "spiro_vt1_hf", "spiro_vt2_v", "spiro_vt2_hf",
                    "spiro_schw_v", "spiro_schw_hf", "spiro_schw_lak", "spiro_schwmeth",
                    "spiro_v_max", "spiro_rpe_max", "spiro_abbruch", "spiro_bemerkung",
                    "spiro_ruhelaktat", "spiro_mahlzeit", "spiro_letzte_einheit",
                    "spiro_beschw", "spiro_temp", "spiro_kgew",
                    f"spiro_editor_{sid}_data", f"spiro_stufen_editor_{sid}",
                    f"spiro_nb_{sid}",
                ]
                for _k in _clear_keys:
                    st.session_state.pop(_k, None)
                # Datum für nächsten Test vorbelegen
                st.session_state["spiro_saved_datum"] = _saved_date
                _save_ok(f"Stufentest vom {datum_spiro.strftime('%d.%m.%Y')} gespeichert!")
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 2 — AUSWERTUNG
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_ausw:
        if not alle_tests:
            st.info("Noch keine Stufentests für diesen Spieler vorhanden.")
        else:
            test_labels_a = [
                f"{t['datum']} | {t.get('geraeteart','?')}"
                f"{' | Laktat' if t.get('mit_laktat') else ''}"
                f"{' | Spiro' if t.get('mit_spiro') else ''}"
                f"{(' | ' + t['protokoll_name']) if t.get('protokoll_name') else ''}"
                for t in alle_tests
            ]
            ausw_idx = st.selectbox("Test auswählen", range(len(test_labels_a)),
                                     format_func=lambda i: test_labels_a[i], key="spiro_ausw_idx")
            test_a  = alle_tests[ausw_idx]
            stufen_a = spiro_stufen_laden(test_a["id"])
            nb_a     = spiro_nachbelastung_laden(test_a["id"])
            _spiro_alter_a = alter_am_datum(auswahl.get("geburtsdatum", ""), test_a.get("datum", ""))
            _spiro_v2_a = _spiro_bewertung_v2(
                test_a,
                alter_testtag=_spiro_alter_a,
                geschlecht=auswahl.get("geschlecht", "Männlich"),
                stufen=stufen_a,
            )

            # Kennzahlen-Header
            aw1, aw2, aw3, aw4 = st.columns(4)
            if test_a.get("maximale_geschwindigkeit"):
                aw1.metric("V max", f"{test_a['maximale_geschwindigkeit']:.1f} km/h")
            if test_a.get("maximale_herzfrequenz"):
                aw2.metric("HF max", f"{test_a['maximale_herzfrequenz']:.0f} bpm")
            vo2_lbl = "VO₂peak" if test_a.get("vo2_peak") else ("VO₂max" if test_a.get("vo2_max") else None)
            vo2_val = test_a.get("vo2_peak") or test_a.get("vo2_max")
            if vo2_lbl and vo2_val:
                aw3.metric(f"{vo2_lbl} (gemessen)", f"{vo2_val:.1f} ml/kg/min")
            elif test_a.get("geschaetzte_vo2max"):
                aw3.metric("VO₂max (geschätzt)", f"{test_a['geschaetzte_vo2max']:.1f} ml/kg/min")
            if test_a.get("schwelle_geschwindigkeit"):
                meth_s = (test_a.get("laktatschwelle_methode") or "Schwelle")[:14]
                aw4.metric(f"V bei {meth_s}", f"{test_a['schwelle_geschwindigkeit']:.1f} km/h")
            if _spiro_v2_a["status"] == "bruce_referenzvergleich":
                st.info(f"ℹ️ {_spiro_v2_a['text']}")
            else:
                st.caption(f"ℹ️ {_spiro_v2_a['text']}")

            if stufen_a:
                df_st_a = pd.DataFrame(stufen_a)
                lak_rows = df_st_a[df_st_a["laktat_mmol_l"].notna()].copy() if "laktat_mmol_l" in df_st_a.columns else pd.DataFrame()

                # Laktat-Leistungskurve
                if not lak_rows.empty and "geschwindigkeit_kmh" in lak_rows.columns:
                    fig_lak = go.Figure()
                    fig_lak.add_trace(go.Scatter(
                        x=lak_rows["geschwindigkeit_kmh"], y=lak_rows["laktat_mmol_l"],
                        mode="lines+markers+text", name="Laktat (mmol/l)",
                        text=lak_rows["laktat_mmol_l"].round(1), textposition="top center",
                        line=dict(color="#f85149", width=3), marker=dict(size=10),
                    ))
                    for zl_c, clr_c in [(2.0, "#d29922"), (4.0, "#f85149")]:
                        r_z = _ibl(stufen_a, zl_c)
                        if r_z:
                            fig_lak.add_vline(
                                x=r_z["x_wert"], line_dash="dash", line_color=clr_c,
                                annotation_text=f"{zl_c:.0f} mmol/l → {r_z['x_wert']:.1f} km/h (interp.)",
                                annotation_position="top right",
                            )
                    if test_a.get("schwelle_geschwindigkeit"):
                        fig_lak.add_vline(
                            x=test_a["schwelle_geschwindigkeit"], line_dash="dot",
                            line_color="#3fb950",
                            annotation_text=f"Schwelle: {(test_a.get('laktatschwelle_methode') or '')[:18]}",
                        )
                    fig_lak.update_layout(**_pl(
                        height=320,
                        title="Laktat-Leistungskurve (tatsächliche Messpunkte)",
                        xaxis=dict(title="Geschwindigkeit (km/h)"),
                        yaxis=dict(title="Laktat (mmol/l)"),
                    ))
                    st.plotly_chart(fig_lak, use_container_width=True)
                    st.caption(
                        "📌 Verbunden sind nur tatsächlich gemessene Werte. "
                        "Interpolierte Schwellenwerte (gestrichelt) werden nicht extrapoliert."
                    )

                # HF-Leistungskurve
                hf_rows = df_st_a[df_st_a["herzfrequenz_bpm"].notna()].copy() if "herzfrequenz_bpm" in df_st_a.columns else pd.DataFrame()
                if not hf_rows.empty and "geschwindigkeit_kmh" in hf_rows.columns:
                    fig_hf = go.Figure()
                    fig_hf.add_trace(go.Scatter(
                        x=hf_rows["geschwindigkeit_kmh"], y=hf_rows["herzfrequenz_bpm"],
                        mode="lines+markers", name="Herzfrequenz (bpm)",
                        line=dict(color="#3b82f6", width=3), marker=dict(size=9),
                    ))
                    for vt_key, vt_col, vt_lbl in [("vt1_geschwindigkeit","#d29922","VT1"),("vt2_geschwindigkeit","#f85149","VT2")]:
                        if test_a.get(vt_key):
                            fig_hf.add_vline(x=test_a[vt_key], line_dash="dash",
                                             line_color=vt_col, annotation_text=vt_lbl)
                    fig_hf.update_layout(**_pl(
                        height=260,
                        title="Herzfrequenz-Leistungskurve",
                        xaxis=dict(title="Geschwindigkeit (km/h)"),
                        yaxis=dict(title="HF (bpm)"),
                    ))
                    st.plotly_chart(fig_hf, use_container_width=True)

                # Stufentabelle
                st.markdown("#### Stufentabelle")
                show_st_cols = [c for c in [
                    "stufennummer", "geschwindigkeit_kmh", "herzfrequenz_bpm",
                    "laktat_mmol_l", "rpe", "stufe_vollstaendig",
                    "vo2_relativ", "rer",
                ] if c in df_st_a.columns]
                st.dataframe(
                    df_st_a[show_st_cols].rename(columns={
                        "stufennummer": "Stufe", "geschwindigkeit_kmh": "km/h",
                        "herzfrequenz_bpm": "HF (bpm)", "laktat_mmol_l": "Laktat (mmol/l)",
                        "rpe": "RPE", "stufe_vollstaendig": "vollst.",
                        "vo2_relativ": "VO₂ rel.", "rer": "RER",
                    }),
                    use_container_width=True, hide_index=True,
                )

            if nb_a:
                st.markdown("#### Nachbelastungswerte")
                df_nb_a = pd.DataFrame(nb_a)[["zeitpunkt_minuten","herzfrequenz_bpm","laktat_mmol_l","bemerkung"]]
                df_nb_a.columns = ["Zeit (min)", "HF (bpm)", "Laktat (mmol/l)", "Bemerkung"]
                st.dataframe(df_nb_a, use_container_width=True, hide_index=True)

            # Trainingsbereiche aus Schwellen
            if (test_a.get("vt1_herzfrequenz") and test_a.get("vt2_herzfrequenz")) \
               or test_a.get("schwelle_herzfrequenz"):
                grundlage_tb = (
                    f"{test_a.get('laktatschwelle_methode') or 'VT-Schwellen'} "
                    f"aus Stufentest vom {test_a.get('datum','')}"
                )
                bereiche_tb = _tbs(
                    vt1_hf=test_a.get("vt1_herzfrequenz"),
                    vt2_hf=test_a.get("vt2_herzfrequenz"),
                    schwelle_hf=test_a.get("schwelle_herzfrequenz"),
                    hf_max=test_a.get("maximale_herzfrequenz"),
                    grundlage_text=grundlage_tb,
                )
                if bereiche_tb:
                    st.markdown("#### Individuelle Trainingsbereiche")
                    st.caption(f"Grundlage: {grundlage_tb}")
                    st.dataframe(
                        pd.DataFrame(bereiche_tb)[["Bereich","HF-Bereich","Intensität"]],
                        use_container_width=True, hide_index=True,
                    )
                    st.caption("Keine Verwendung der 220-minus-Alter-Formel — Basis sind gemessene Schwellenwerte.")

            # Fußball-Einordnung
            st.markdown("---")
            st.info(
                "🏟️ **Fußballbezogene Einordnung:** Der laufbasierte Stufentest beschreibt die "
                "aerobe und submaximale Ausdauerleistungsfähigkeit unter standardisierten Bedingungen. "
                "Geschwindigkeit, Herzfrequenz, Atemgaswerte und Laktat können für die individuelle "
                "Trainingssteuerung verwendet werden. Ein Labortest bildet nicht alle Anforderungen "
                "des Fußballspiels ab."
            )

            st.markdown("---")
            if _confirm_loeschen("spiro_del", was="diesen Stufentest",
                                  btn_label="🗑️ Diesen Test löschen"):
                spiro_test_loeschen(test_a["id"])
                _save_ok("Stufentest gelöscht.")
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 3 — VERLAUF & VERGLEICH
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_vgl:
        if not alle_tests:
            st.info("Noch keine Stufentests vorhanden.")
        else:
            # Übersichtstabelle
            st.markdown("### Alle Stufentests")
            ov_cols = ["datum","geraeteart","maximale_geschwindigkeit","maximale_herzfrequenz",
                        "vo2_peak","vo2_max","schwelle_geschwindigkeit","laktatschwelle_methode","protokoll_name"]
            df_ov = pd.DataFrame(alle_tests)[[c for c in ov_cols if c in pd.DataFrame(alle_tests).columns]]
            df_ov = df_ov.rename(columns={
                "datum":"Datum","geraeteart":"Gerät","maximale_geschwindigkeit":"V max (km/h)",
                "maximale_herzfrequenz":"HF max","vo2_peak":"VO₂peak","vo2_max":"VO₂max",
                "schwelle_geschwindigkeit":"V Schwelle","laktatschwelle_methode":"Methode",
                "protokoll_name":"Protokoll",
            })
            st.dataframe(df_ov, use_container_width=True, hide_index=True)

            # ── Bearbeiten / Löschen ──────────────────────────────────────────
            st.markdown("---")
            with st.expander("✏️ Test bearbeiten / löschen"):
                _render_spiro_edit(sid)

            if len(alle_tests) < 2:
                st.info("Mindestens 2 Tests für den Vergleich erforderlich.")
                return

            st.markdown("---")
            st.markdown("### Laktatkurven vergleichen")
            vl1, vl2 = st.columns(2)
            vgl_labels = [
                f"{t['datum']} — {t.get('geraeteart','?')}"
                f"{(' | ' + t['protokoll_name']) if t.get('protokoll_name') else ''}"
                for t in alle_tests
            ]
            idx_t1 = vl1.selectbox("Test 1 (Referenz)", range(len(vgl_labels)),
                                    format_func=lambda i: vgl_labels[i], key="vgl_t1")
            idx_t2 = vl2.selectbox("Test 2 (Vergleich)", range(len(vgl_labels)),
                                    format_func=lambda i: vgl_labels[i],
                                    index=min(1, len(alle_tests) - 1), key="vgl_t2")

            if idx_t1 == idx_t2:
                st.warning("Bitte zwei verschiedene Tests auswählen.")
            else:
                t_ref  = alle_tests[idx_t1]
                t_new  = alle_tests[idx_t2]
                st_ref = spiro_stufen_laden(t_ref["id"])
                st_new = spiro_stufen_laden(t_new["id"])

                # Protokollkompatibilität prüfen
                p_ref = next((p for p in alle_protokolle if p["id"] == t_ref.get("protokoll_id")), {})
                p_new = next((p for p in alle_protokolle if p["id"] == t_new.get("protokoll_id")), {})
                if t_ref.get("protokoll_id") and t_new.get("protokoll_id"):
                    vgl_ok, vgl_abw = _pv(p_ref, p_new)
                    if not vgl_ok:
                        st.warning(
                            "⚠️ **Protokolle unterscheiden sich — direkter Vergleich eingeschränkt:**\n\n"
                            + "  \n".join(f"• {a}" for a in vgl_abw)
                        )
                    else:
                        st.success("✅ Gleiche Protokollparameter — direkter Vergleich möglich.")
                elif t_ref.get("geraeteart") != t_new.get("geraeteart"):
                    st.warning(
                        "⚠️ Verschiedene Gerätearten — direkter Vergleich eingeschränkt. "
                        f"({t_ref.get('geraeteart','?')} vs. {t_new.get('geraeteart','?')})"
                    )
                else:
                    st.info("ℹ️ Kein vollständiges Protokoll hinterlegt — Vergleichbarkeit nicht automatisch prüfbar.")

                # Overlay Laktatkurven
                lak_ref = [r for r in st_ref if r.get("laktat_mmol_l") and r.get("geschwindigkeit_kmh")]
                lak_new = [r for r in st_new if r.get("laktat_mmol_l") and r.get("geschwindigkeit_kmh")]

                if lak_ref and lak_new:
                    fig_ov_lak = go.Figure()
                    for rows_v, lbl_v, clr_v in [(lak_ref, t_ref["datum"], "#3b82f6"), (lak_new, t_new["datum"], "#f85149")]:
                        fig_ov_lak.add_trace(go.Scatter(
                            x=[r["geschwindigkeit_kmh"] for r in rows_v],
                            y=[r["laktat_mmol_l"]       for r in rows_v],
                            mode="lines+markers", name=lbl_v,
                            line=dict(color=clr_v, width=3), marker=dict(size=9),
                        ))
                    fig_ov_lak.update_layout(**_pl(
                        height=340,
                        title="Laktatkurven-Overlay — gleiche Achsenskalierung",
                        xaxis=dict(title="Geschwindigkeit (km/h)"),
                        yaxis=dict(title="Laktat (mmol/l)"),
                    ))
                    st.plotly_chart(fig_ov_lak, use_container_width=True)

                    # Schwellenvergleich
                    zeilen_sv = _svt(st_ref, st_new, t_ref["datum"], t_new["datum"])
                    if zeilen_sv:
                        st.markdown("#### Vergleich bei festen Laktatwerten")
                        st.caption("Interpolierte Werte: als '(interp.)' markiert. Keine Extrapolation außerhalb der Messung.")
                        st.dataframe(pd.DataFrame(zeilen_sv), use_container_width=True, hide_index=True)

                    # Kurvenverschiebung
                    st.markdown("#### Kurvenverschiebung — neutrale Bewertung")
                    for zl_v in [2.0, 4.0]:
                        r_ref_z = _ibl(st_ref, zl_v)
                        r_new_z = _ibl(st_new, zl_v)
                        stufe_v, text_v = _kvb(
                            r_ref_z["x_wert"] if r_ref_z else None,
                            r_new_z["x_wert"] if r_new_z else None,
                            zl_v,
                        )
                        clr_v = {
                            "wahrscheinlich verbessert": "#3fb950",
                            "weitgehend unverändert":    "#d29922",
                            "möglicherweise vermindert": "#f85149",
                            "nicht sicher vergleichbar": "#8b949e",
                        }.get(stufe_v, "#8b949e")
                        st.markdown(
                            f'<div style="background:#161b22;border-left:3px solid {clr_v};'
                            f'padding:10px 14px;margin:6px 0;border-radius:4px">'
                            f'<b style="color:{clr_v}">{stufe_v}</b><br>'
                            f'<span style="font-size:13px;color:#cdd9e5">{text_v}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    st.caption(
                        "⚠️ Eine Kurvenverschiebung beweist keine eindeutige Verbesserung oder Verschlechterung. "
                        "Tagesform, Vorbelastung, Regeneration, Ernährung, Temperatur, Testbedingungen, "
                        "Ausbelastungsgrad, RPE und Herzfrequenz müssen bei der Interpretation berücksichtigt werden."
                    )
                else:
                    st.info("Für mindestens einen der gewählten Tests sind keine Laktatwerte verfügbar.")

                # HF-Overlay
                hf_ref = [r for r in st_ref if r.get("herzfrequenz_bpm") and r.get("geschwindigkeit_kmh")]
                hf_new = [r for r in st_new if r.get("herzfrequenz_bpm") and r.get("geschwindigkeit_kmh")]
                if hf_ref and hf_new:
                    fig_ov_hf = go.Figure()
                    for rows_h, lbl_h, clr_h in [(hf_ref, t_ref["datum"], "#3b82f6"), (hf_new, t_new["datum"], "#f85149")]:
                        fig_ov_hf.add_trace(go.Scatter(
                            x=[r["geschwindigkeit_kmh"] for r in rows_h],
                            y=[r["herzfrequenz_bpm"]    for r in rows_h],
                            mode="lines+markers", name=lbl_h,
                            line=dict(color=clr_h, width=3), marker=dict(size=9),
                        ))
                    fig_ov_hf.update_layout(**_pl(
                        height=260,
                        title="Herzfrequenz-Leistungskurven — Vergleich",
                        xaxis=dict(title="Geschwindigkeit (km/h)"),
                        yaxis=dict(title="HF (bpm)"),
                    ))
                    st.plotly_chart(fig_ov_hf, use_container_width=True)
RPE_LABELS = {
    6: "6 — Gar keine Anstrengung", 7: "7", 8: "8", 9: "9",
    10: "10 — Sehr leicht", 11: "11 — Leicht", 12: "12",
    13: "13 — Etwas anstrengend", 14: "14",
    15: "15 — Anstrengend", 16: "16", 17: "17 — Sehr anstrengend",
    18: "18", 19: "19 — Extrem anstrengend", 20: "20 — Maximale Anstrengung",
}


def page_ausdauer():
    st.markdown("# 🫁 Ausdauer-Diagnostik")
    _back_button("← Zurück zu Tests", "🔬  Diagnostik", target_sub_diagnostik="🏠 Übersicht", key="back_aus")

    # ── Bereichsselektor ──────────────────────────────────────────────────────
    bereich = st.radio(
        "Ausdauertest",
        ["🏃 Yo-Yo Intermittent Recovery Test", "🔬 Spiroergometrie-Stufentest"],
        horizontal=True,
        key="aus_bereich_wahl",
        label_visibility="collapsed",
    )
    st.markdown("---")

    if bereich == "🔬 Spiroergometrie-Stufentest":
        _page_spiro()
        return

    # ── Yo-Yo (unveränderter Code) ────────────────────────────────────────────
    st.markdown("## 🏃 Yo-Yo Intermittent Recovery Test")
    st.markdown("Yo-Yo Intermittent Recovery Test Level 1 (IR1) und Level 2 (IR2) — Standardtest im Fußball.")

    sicherheitshinweis_box()
    show_trainer_checkliste("yoyo")
    show_test_info("yoyo")
    _anleitung_download_button("yoyo")

    auswahl = _player_selector("aus")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    alter  = berechne_alter(sp.get("geburtsdatum","")) if sp else 0
    ag_norm = alter_zu_altersgruppe(alter or 0)   # für field_eval-Normbadge

    letzter = ausdauer_letzter(sid)
    hist    = ausdauer_history(sid)

    # ── Zentrale Yo-Yo-Gruppenableitung via Fußball-Altersklasse ─────────────
    # Ersetzt die frühere lokale alter_zu_gruppe()-Funktion.
    # Bug dort: Alter 9 → "U8/U9" statt "U10/U11"; "U13/U14" fehlte komplett.
    from ausdauer import fussballklasse_zu_yoyo_gruppe as _fk_zu_yoyo
    from saison  import fussballklasse_aus_datum       as _fk_aus_datum

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    with tab_neu:
        c1, c2 = st.columns(2)
        datum       = c1.date_input("Testdatum", value=date.today(), key="aus_datum")
        # Alter am gewählten Testdatum (Spec §3)
        _alter_aus_td = alter_am_datum(
            sp.get("geburtsdatum", "") if sp else "", datum.strftime("%d.%m.%Y")
        ) or alter
        # Fußballklasse am Testtag → Yo-Yo-Normgruppe (FK ist primäre Quelle)
        _gbd_aus   = sp.get("geburtsdatum", "") if sp else ""
        _fk_am_td  = _fk_aus_datum(_gbd_aus, stichtag=datum) if _gbd_aus else None
        _yoyo_def  = _fk_zu_yoyo(_fk_am_td, _alter_aus_td)
        _yoyo_idx  = (ALTERSGRUPPEN_YO.index(_yoyo_def)
                      if _yoyo_def in ALTERSGRUPPEN_YO else len(ALTERSGRUPPEN_YO) - 1)

        test_typ    = c1.selectbox("Test-Level", ["IR1", "IR2"], key="aus_typ")
        altersgruppe = c2.selectbox("Altersgruppe", ALTERSGRUPPEN_YO,
                                     index=_yoyo_idx,
                                     key="aus_ag")
        # Info: FK ≠ Testreferenz ist bewusst (Spec §2)
        if _gbd_aus:
            c2.caption(
                f"**Fußballklasse:** {_fk_am_td or '—'} · "
                f"**Testreferenz:** {_yoyo_def} · "
                f"**Alter am Testtag:** {int(_alter_aus_td or 0)} J."
            )

        st.markdown("#### Testergebnis")
        _fh = lambda fid: show_field_help("yoyo", fid)
        c3, c4, c5 = st.columns(3)
        dist_h, dist_i = c3.columns([5, 1]); dist_h.markdown("**Erzielte Distanz (m)**"); field_info_col(dist_i, "yoyo", "distanz")
        distanz_m = c3.number_input("Erzielte Distanz (m)", 0, 5000,
                                     int(letzter["distanz_m"]) if letzter else 0,
                                     step=40, key="aus_dist", label_visibility="collapsed", help=_fh("distanz"))
        if distanz_m > 0: norm_badge(distanz_m, "yoyo", "distanz", c3, altersgruppe=ag_norm)
        hf_h, hf_i = c4.columns([5, 1]); hf_h.markdown("**HF max (bpm)**"); field_info_col(hf_i, "yoyo", "hf_max")
        hf_max    = c4.number_input("HF max (bpm)", 0, 230,
                                     int(letzter["hf_max"]) if letzter and letzter.get("hf_max") else 0,
                                     step=1, key="aus_hf", label_visibility="collapsed", help=_fh("hf_max"))
        rpe_h, rpe_i = c5.columns([5, 1]); rpe_h.markdown("**RPE (Borg 6–20)**"); field_info_col(rpe_i, "yoyo", "rpe")
        rpe_val   = c5.selectbox("RPE (Borg 6–20)", list(range(6, 21)),
                                  index=9, key="aus_rpe",
                                  format_func=lambda x: RPE_LABELS.get(x, str(x)),
                                  help=_fh("rpe"), label_visibility="collapsed")

        from ausdauer import AusdauerErgebnis as _AE, trainingsbereiche, bewertung_ir1
        res = _AE(test_typ=test_typ, distanz_m=distanz_m,
                  hf_max=hf_max or None, rpe=rpe_val,
                  geschlecht=geschl, altersgruppe=altersgruppe)

        if distanz_m > 0:
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Distanz", f"{distanz_m} m")
            if res.vo2max:
                m2.metric("VO₂max (Schätzung ⚠️)", f"{res.vo2max} ml/kg/min")
            bew_color = aus_farbe(res.bewertung)
            m3.markdown(
                f'<div style="background:#161b22;border:1px solid {bew_color};border-radius:8px;'
                f'padding:8px 12px;text-align:center">'
                f'<div style="color:{bew_color};font-weight:700;font-size:18px">{res.bewertung}</div>'
                f'<div style="color:#8b949e;font-size:11px">Bewertung {altersgruppe}</div></div>',
                unsafe_allow_html=True,
            )

            st.caption("⚠️ Die VO₂max-Schätzung basiert auf der Bangsbo-Formel und ist kein Laborwert.")
            if test_typ == "IR2":
                st.info(
                    "ℹ️ Für den Yo-Yo IR2 wird keine automatische VO₂max-Schätzung berechnet — "
                    "der Bangsbo-Koeffizient gilt ausschließlich für den IR1."
                )

            if res.vo2max:
                st.markdown("#### Trainingsbereiche")
                tb = trainingsbereiche(res.vo2max)
                st.dataframe(pd.DataFrame(tb), use_container_width=True, hide_index=True)

            if res.defizite:
                st.markdown("**🔴 Identifizierte Defizite:**")
                for d in res.defizite:
                    st.markdown(f"- {d}")

        # ── Trainerbeobachtungen ────────────────────────────────────────────
        st.markdown("---")
        obs_aus = render_observation_selector("ausdauer", sid, datum.strftime("%d.%m.%Y"), "aus", standalone=False)
        _dup_aus = _duplikat_check("aus", datum.strftime("%d.%m.%Y"), hist)

        if st.button("💾 Test speichern", use_container_width=True, key="aus_save", type="primary"):
            if _dup_aus == "abbrechen":
                st.info("Kein Test gespeichert."); st.stop()
            if distanz_m <= 0:
                st.error("Bitte Distanz eingeben.")
            else:
                import json, datetime as _dtm
                _datum_aus = datum.strftime("%d.%m.%Y")
                if _dup_aus == "zweiter":
                    _datum_aus += " (" + _dtm.datetime.now().strftime("%H:%M") + ")"
                ausdauer_speichern(
                    sid, _datum_aus,
                    test_typ, distanz_m,
                    hf_max or 0, rpe_val,
                    res.vo2max or 0, res.bewertung,
                    altersgruppe,
                    json.dumps(res.defizite, ensure_ascii=False),
                )
                if obs_aus["beob_ids"] or obs_aus.get("freitext"):
                    beobachtung_speichern(
                        sid, "ausdauer", _datum_aus,
                        json.dumps(obs_aus["beob_ids"], ensure_ascii=False),
                        obs_aus["seite"], obs_aus["auspraegung"],
                        obs_aus["freitext"], obs_aus["text_generiert"],
                    )
                _save_ok("Ausdauer-Test gespeichert!")
                _reset_keys("aus_dist", "aus_hf", "aus_rpe")
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Ausdauer-Tests vorhanden.")
            return

        df = pd.DataFrame(hist)
        df.columns = ["Datum", "Test", "Distanz (m)", "VO₂max", "Bewertung", "HF max", "RPE"]

        # ── Persönliche Bestleistung ──────────────────────────────────────────
        _pb_trend_cards(df, [
            ("Distanz (m)", "Yo-Yo Distanz", "m",         False),
            ("VO₂max",      "VO₂max (Schätzg.)", "ml/kg/min", False),
        ])

        c_d, c_v = st.columns(2)
        with c_d:
            fig = go.Figure()
            for typ, color in [("IR1", "#3b82f6"), ("IR2", "#3fb950")]:
                sub = df[df["Test"] == typ]
                if sub.empty: continue
                fig.add_trace(go.Scatter(
                    x=sub["Datum"], y=sub["Distanz (m)"],
                    mode="lines+markers+text", name=f"Yo-Yo {typ}",
                    text=sub["Distanz (m)"], textposition="top center",
                    line=dict(color=color, width=3), marker=dict(size=8),
                ))
            fig.update_layout(**_pl(height=300, title="Yo-Yo Distanz-Verlauf (m)"))
            st.plotly_chart(fig, use_container_width=True)

        with c_v:
            sub_v = df[df["VO₂max"] > 0]
            if not sub_v.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=sub_v["Datum"], y=sub_v["VO₂max"],
                    mode="lines+markers+text", name="VO₂max (Schätzung)",
                    text=sub_v["VO₂max"].round(1), textposition="top center",
                    line=dict(color="#d29922", width=3), marker=dict(size=8),
                ))
                fig2.add_hline(y=50, line_dash="dash", line_color="#3fb950",
                               annotation_text="Zielwert 50 ml/kg/min")
                fig2.update_layout(**_pl(height=300, title="VO₂max-Schätzung ⚠️"))
                st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Zwei Termine vergleichen ──────────────────────────────────────────
        if len(df) >= 2:
            with st.expander("🔍 Zwei Termine vergleichen"):
                datums_au = df["Datum"].tolist()
                auc1, auc2 = st.columns(2)
                aud1 = auc1.selectbox("Termin 1", datums_au, index=0, key="aus_cmp_d1")
                aud2 = auc2.selectbox("Termin 2", datums_au, index=len(datums_au)-1, key="aus_cmp_d2")
                aur1 = df[df["Datum"] == aud1].iloc[0]
                aur2 = df[df["Datum"] == aud2].iloc[0]
                compare_cols_au = ["Distanz (m)", "VO₂max", "HF max", "RPE"]
                rows_au = []
                for cau in compare_cols_au:
                    v1au = float(aur1.get(cau, 0) or 0)
                    v2au = float(aur2.get(cau, 0) or 0)
                    if v1au > 0 or v2au > 0:
                        diff_au = round(v2au - v1au, 1) if v1au > 0 and v2au > 0 else "—"
                        rows_au.append({
                            "Messung": cau,
                            aud1: f"{v1au:.0f}" if v1au else "—",
                            aud2: f"{v2au:.0f}" if v2au else "—",
                            "Differenz": f"{diff_au:+.1f}" if isinstance(diff_au, float) else diff_au,
                        })
                if rows_au:
                    st.dataframe(pd.DataFrame(rows_au), use_container_width=True, hide_index=True)
                    st.caption("Differenz: positiv = besser (mehr Distanz / höherer VO₂max)")

        # ── Bearbeiten / Löschen ──────────────────────────────────────────────
        st.markdown("---")
        with st.expander("✏️ Eintrag bearbeiten / löschen"):
            _render_ausdauer_edit(sid)


# ──────────────────────────────────────────────────────────────────────────────

def page_kraft():
    st.markdown("# 💪 Kraftdiagnostik")
    _back_button("← Zurück zu Tests", "🔬  Diagnostik", target_sub_diagnostik="🏠 Übersicht", key="back_kraft")
    st.markdown(
        "Bankdrücken 1RM (direkt oder Epley-Schätzung) und Rumpfkraftausdauer — "
        "interne Orientierungswerte für die Trainingssteuerung. "
        "Kein Test ersetzt eine ärztliche Einschätzung oder Sportfreigabe."
    )

    sicherheitshinweis_box()
    show_trainer_checkliste("kraft")
    show_test_info("kraft")

    auswahl = _player_selector("kraft")
    if not auswahl:
        return

    sid    = auswahl["id"]
    sp     = spieler_by_id(sid)
    geschl = sp.get("geschlecht", "Männlich") if sp else "Männlich"
    alter  = berechne_alter(sp.get("geburtsdatum")) if sp else None
    kgew   = anthropometrie_letzter(sid)
    hist   = kraft_history(sid)

    tab_neu, tab_verlauf = st.tabs(["📋 Neuer Test", "📈 Verlauf"])

    with tab_neu:
        datum = st.date_input("Testdatum", value=date.today(), key="kraft_datum")
        # Alter am gewählten Testdatum — nicht heutiges Alter (Spec §3)
        alter_td = alter_am_datum(
            sp.get("geburtsdatum", "") if sp else "", datum.strftime("%d.%m.%Y")
        ) or alter
        if datum > date.today():
            st.warning("⚠️ Testdatum liegt in der Zukunft — bitte prüfen.")

        koerpergewicht_default = float(kgew["gewicht"]) if kgew and kgew.get("gewicht") else 75.0
        koerpergewicht = st.number_input(
            "Körpergewicht (kg) — für Berechnung der relativen Kraft",
            15.0, 150.0, koerpergewicht_default, step=0.5, key="kraft_kgew"
        )

        st.markdown("---")
        # ── Bankdrücken ────────────────────────────────────────────────────
        bd_head, bd_info = st.columns([6, 1])
        bd_head.markdown("### 🏋️ Bankdrücken — 1-Wiederholungsmaximum (1RM)")
        field_info_col(bd_info, "kraft", "direktes_1rm")
        st.caption(
            "Interner Orientierungswert für die Trainingssteuerung. "
            "Direkte 1RM-Tests nur mit Sicherung und ausreichendem Aufwärmen."
        )
        bd_methode = st.radio(
            "Testmethode",
            ["Submaximaltest (Epley-Schätzung) — empfohlen", "Direkter 1RM-Test"],
            key="kraft_bd_methode",
        )

        direktes_1rm  = None
        epley_gewicht = None
        epley_wdh     = None
        sicherheit_ok = False

        if "Direkt" in bd_methode:
            st.warning(
                "⚠️ **Sicherheitshinweis — Direkter 1RM-Test**\n\n"
                "• Mindestens 2 Trainer/Spotters als Sicherung\n"
                "• Ausreichendes Aufwärmen abgeschlossen (progressive Laststeigerung)\n"
                "• Technikbeherrschung und Testprotokoll erklärt\n"
                "• Sofortabbruch bei technischen Mängeln oder Schmerzen"
            )
            c1, c2, c3 = st.columns(3)
            ok1 = c1.checkbox("✅ Sicherung durch mind. 2 Trainer", key="kraft_sek1")
            ok2 = c2.checkbox("✅ Aufwärmphase abgeschlossen", key="kraft_sek2")
            ok3 = c3.checkbox("✅ Technik & Protokoll besprochen", key="kraft_sek3")
            sicherheit_ok = ok1 and ok2 and ok3
            if not sicherheit_ok:
                st.info("Alle drei Sicherheitspunkte müssen bestätigt sein.")
            else:
                st.success("✅ Sicherheitsprotokoll vollständig — Test kann durchgeführt werden.")
            direktes_1rm = st.number_input(
                "Direktes 1RM (kg)", 0.0, 300.0, 0.0, step=2.5, key="kraft_d1rm",
                disabled=(not sicherheit_ok)
            ) or None
            if direktes_1rm and direktes_1rm > 200:
                st.warning(f"⚠️ {direktes_1rm:.0f} kg ist ein außergewöhnlicher 1RM-Wert — bitte Eingabe prüfen.")
        else:
            st.caption("Eingabe: Gewicht und Wiederholungsanzahl aus dem Submaximaltest (empfohlen 2–10 WH).")
            c1, c2 = st.columns(2)
            epley_gewicht = c1.number_input("Testgewicht (kg)", 0.0, 300.0, 0.0, step=2.5, key="kraft_e_gew") or None
            epley_wdh_raw = c2.number_input("Wiederholungen", 1, 15, 5, key="kraft_e_wdh")
            epley_wdh = int(epley_wdh_raw)
            if epley_wdh > 10:
                st.warning("⚠️ Die Epley-Formel ist für > 10 Wiederholungen weniger genau.")
            if epley_gewicht:
                est = _epley_1rm(epley_gewicht, epley_wdh)
                if est:
                    rel = round(est / koerpergewicht, 2) if koerpergewicht > 0 else None
                    c1, c2 = st.columns(2)
                    c1.metric("Geschätztes 1RM (Epley)", f"{est:.1f} kg")
                    if rel: c2.metric("Relative Kraft", f"{rel:.2f} ×KGW")
            sicherheit_ok = True

        from kraft import KraftErgebnis as _KE
        kraft_res = _KE(
            koerpergewicht=koerpergewicht,
            direktes_1rm=direktes_1rm,
            epley_gewicht=epley_gewicht,
            epley_wiederholungen=epley_wdh,
            sicherheit_bestaetigt=sicherheit_ok,
        )
        if kraft_res.hat_bankdruecken_daten:
            from kraft import beurteilung_relative_kraft as _bwrk
            m1, m2, m3 = st.columns(3)
            if direktes_1rm:              m1.metric("Direkt 1RM", f"{direktes_1rm:.1f} kg")
            if kraft_res.geschaetztes_1rm: m2.metric("Epley-Schätzung", f"{kraft_res.geschaetztes_1rm:.1f} kg")
            rel = kraft_res.relative_kraft_direkt or kraft_res.relative_kraft_geschaetzt
            if rel:
                m3.metric("Relative Kraft", f"{rel:.2f} ×KGW")
                _stufe_rk, _empf_rk = _bwrk(rel, alter=alter_td, geschlecht=geschl)
                _clr_rk = {"Sehr gut": "#3fb950", "Gut": "#3fb950",
                           "Durchschnittlich": "#d29922",
                           "Unterdurchschnittlich": "#f85149", "Kritisch": "#f85149"}.get(_stufe_rk, "#8b949e")
                st.markdown(
                    f'<div style="background:#161b22;border:1px solid {_clr_rk};border-radius:8px;'
                    f'padding:10px 14px;margin:6px 0">'
                    f'<span style="color:{_clr_rk};font-weight:700">Bankdrücken Rel. Kraft: {_stufe_rk}</span>'
                    f'<span style="color:#8b949e;font-size:12px;margin-left:12px">{rel:.2f} ×KGW</span><br>'
                    f'<small style="color:#8b949e">{_empf_rk}</small>'
                    f'<br><small style="color:#8b949e;font-size:11px">📊 {_tcap(alter_td, sp.get("geburtsdatum","") if sp else "")}</small></div>',
                    unsafe_allow_html=True,
                )

        # ── Rumpfkraftausdauer ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🧱 Rumpfkraftausdauer — Haltedauer (Sekunden)")
        st.caption("Ventral: 2 Versuche (Bestwert = länger). Lateral R/L und Dorsal: je 1 Versuch.")

        rc1, rc2 = st.columns(2)
        vh_head, vh_info = rc1.columns([5, 1])
        vh_head.markdown("**Ventral (Plank) — 2 Versuche**")
        field_info_col(vh_info, "kraft", "ventral_sekunden")
        rv1_c, rv2_c = rc1.columns(2)
        ventral_v1 = rv1_c.number_input("V1 (s)", 0.0, 600.0, 0.0, step=1.0, key="kraft_vent_v1") or None
        ventral_v2 = rv2_c.number_input("V2 (s)", 0.0, 600.0, 0.0, step=1.0, key="kraft_vent_v2") or None
        ventr_best = max([v for v in [ventral_v1, ventral_v2] if v], default=None)
        if ventr_best: rc1.success(f"Bestwert ventral: **{ventr_best:.0f} s**")

        lh_head, lh_info = rc2.columns([5, 1])
        lh_head.markdown("**Lateral (Seitstütz) — R/L**")
        field_info_col(lh_info, "kraft", "lateral_rechts")
        lateral_r = rc2.number_input("Lateral rechts (s)", 0.0, 600.0, 0.0, step=1.0, key="kraft_lat_r") or None
        lateral_l = rc2.number_input("Lateral links (s)",  0.0, 600.0, 0.0, step=1.0, key="kraft_lat_l") or None
        dh_head, dh_info = rc1.columns([5, 1])
        dh_head.markdown("**Dorsal (Biering-Sørensen)**")
        field_info_col(dh_info, "kraft", "dorsal_sekunden")
        dorsal    = rc1.number_input("Dorsal (s)",         0.0, 600.0, 0.0, step=1.0, key="kraft_dors") or None

        rumpf_res = _KE(
            koerpergewicht=koerpergewicht,
            direktes_1rm=direktes_1rm, epley_gewicht=epley_gewicht,
            epley_wiederholungen=epley_wdh, sicherheit_bestaetigt=sicherheit_ok,
            ventral_sekunden=ventral_v1, ventral_versuch2=ventral_v2,
            lateral_rechts_sekunden=lateral_r, lateral_links_sekunden=lateral_l,
            dorsal_sekunden=dorsal,
        )

        if rumpf_res.hat_rumpfkraft_daten:
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            if rumpf_res.ventral_bestwert: m1.metric("Ventral", f"{rumpf_res.ventral_bestwert:.0f} s")
            if lateral_r:                  m2.metric("Lateral R", f"{lateral_r:.0f} s")
            if lateral_l:                  m3.metric("Lateral L", f"{lateral_l:.0f} s")
            if dorsal:                     m4.metric("Dorsal", f"{dorsal:.0f} s")
            if rumpf_res.lateral_asymmetrie_pct is not None:
                color = "#f85149" if rumpf_res.lateral_asymmetrie_pct > 10 else "#3fb950"
                hint  = "⚠️ auffällig" if rumpf_res.lateral_asymmetrie_pct > 10 else "✅ symmetrisch"
                st.markdown(
                    f'<div style="background:#161b22;border:1px solid {color};border-radius:8px;'
                    f'padding:10px 14px;margin:8px 0">'
                    f'<span style="color:{color};font-weight:600">Lateral-Asymmetrie: '
                    f'{rumpf_res.lateral_asymmetrie_pct:.1f} % — {hint}</span>'
                    f'<br><small style="color:#8b949e">Grenzwert: 10 % Seitendifferenz</small></div>',
                    unsafe_allow_html=True,
                )
            # ── Rumpfkraftausdauer Beurteilung ──────────────────────────────
            from kraft import beurteilung_ventral_plank as _bwvp, beurteilung_dorsal as _bwdors, beurteilung_lateral as _bwlat
            _rk_bwcols = [x for x in [
                ("Ventral (Plank)", rumpf_res.ventral_bestwert, _bwvp),
                ("Lateral R",       lateral_r,                  _bwlat),
                ("Lateral L",       lateral_l,                  _bwlat),
                ("Dorsal",          dorsal,                     _bwdors),
            ] if x[1]]
            if _rk_bwcols:
                _bc = st.columns(len(_rk_bwcols))
                _bw_clr_map = {"Sehr gut": "#3fb950", "Gut": "#3fb950",
                               "Durchschnittlich": "#d29922",
                               "Unterdurchschnittlich": "#f85149", "Kritisch": "#f85149"}
                for _i, (_lbl, _val, _fn) in enumerate(_rk_bwcols):
                    _st2, _em2 = _fn(_val)
                    _c2 = _bw_clr_map.get(_st2, "#8b949e")
                    _bc[_i].markdown(
                        f'<div style="background:#161b22;border:1px solid {_c2};border-radius:8px;'
                        f'padding:10px 14px;text-align:center">'
                        f'<div style="color:{_c2};font-weight:700;font-size:13px">{_lbl}: {_st2}</div>'
                        f'<div style="color:#e6edf3;font-size:22px;font-weight:700">{_val:.0f} s</div>'
                        f'<small style="color:#8b949e">{_em2}</small></div>',
                        unsafe_allow_html=True,
                    )
            if rumpf_res.hinweise:
                st.markdown("**🔵 Trainingshinweise:**")
                for h in rumpf_res.hinweise:
                    st.markdown(f"- {h}")

        st.markdown("---")
        bemerkung = st.text_area("Trainernotiz (optional)", height=70, key="kraft_bemerkung") or None
        obs_kraft = render_observation_selector("kraft", sid, datum.strftime("%d.%m.%Y"), "kraft", standalone=False)

        save_disabled = ("Direkt" in bd_methode) and (not sicherheit_ok)
        if st.button("💾 Test speichern", use_container_width=True, key="kraft_save", type="primary",
                     disabled=save_disabled):
            if not rumpf_res.hat_daten:
                st.error("Bitte mindestens einen Messwert eingeben.")
            else:
                import json
                lat_diff  = round(abs(lateral_r - lateral_l), 1) if lateral_r and lateral_l else None
                rumpf_ges = None
                vals_r = [v for v in [rumpf_res.ventral_bestwert, lateral_r, lateral_l, dorsal] if v]
                if vals_r: rumpf_ges = round(sum(vals_r), 1)
                kraft_speichern(
                    sid, datum.strftime("%d.%m.%Y"),
                    koerpergewicht, rumpf_res.direktes_1rm, rumpf_res.geschaetztes_1rm,
                    rumpf_res.relative_kraft_direkt, rumpf_res.relative_kraft_geschaetzt,
                    1 if sicherheit_ok else 0,
                    ventral_v1, ventral_v2, lateral_r, lateral_l, dorsal,
                    rumpf_ges, lat_diff, rumpf_res.lateral_asymmetrie_pct,
                    rumpf_res.ratio_ventral_dorsal, rumpf_res.ratio_lateral_r_dorsal,
                    rumpf_res.ratio_lateral_l_dorsal, bemerkung=bemerkung,
                )
                if obs_kraft["beob_ids"] or obs_kraft.get("freitext"):
                    beobachtung_speichern(
                        sid, "kraft", datum.strftime("%d.%m.%Y"),
                        json.dumps(obs_kraft["beob_ids"], ensure_ascii=False),
                        obs_kraft["seite"], obs_kraft["auspraegung"],
                        obs_kraft["freitext"], obs_kraft["text_generiert"],
                    )
                _save_ok("Kraft-Test gespeichert!")
                _reset_keys(
                    "kraft_kgew", "kraft_bd_methode", "kraft_sek1", "kraft_sek2", "kraft_sek3",
                    "kraft_d1rm", "kraft_e_gew", "kraft_e_wdh",
                    "kraft_vent_v1", "kraft_vent_v2", "kraft_lat_r", "kraft_lat_l",
                    "kraft_dors", "kraft_bemerkung",
                )
                st.rerun()

    with tab_verlauf:
        if not hist:
            st.info("Noch keine Kraft-Tests vorhanden.")
            return
        df = pd.DataFrame(hist)
        df.columns = [
            "Datum", "Direkt 1RM", "Epley 1RM",
            "Rel. Kraft D", "Rel. Kraft E",
            "Ventral (s)", "Lateral R (s)", "Lateral L (s)",
            "Dorsal (s)", "Lat.-Asym. %", "V/D-Ratio",
        ]

        # ── Persönliche Bestleistung ──────────────────────────────────────────
        _pb_trend_cards(df, [
            ("Direkt 1RM",    "Bankdrücken 1RM (direkt)", "kg", False),
            ("Epley 1RM",     "Bankdrücken 1RM (Epley)",  "kg", False),
            ("Ventral (s)",   "Planke ventral",           "s",  False),
            ("Dorsal (s)",    "Planke dorsal",            "s",  False),
        ])

        # ── Letzter Test ──────────────────────────────────────────────────────
        with st.expander("📋 Letzter gespeicherter Test", expanded=True):
            lr = df.iloc[-1]
            ka1, ka2, ka3, ka4, ka5, ka6 = st.columns(6)
            def _km(col, label, val, fmt="%.1f", suffix=""):
                if val and float(val) > 0:
                    col.metric(label, f"{float(val):{fmt.replace('%','')}} {suffix}".strip())
            _km(ka1, "Direkt 1RM",  lr.get("Direkt 1RM"), fmt="%.1f", suffix="kg")
            _km(ka2, "Epley 1RM",   lr.get("Epley 1RM"),  fmt="%.1f", suffix="kg")
            _km(ka3, "Ventral",     lr.get("Ventral (s)"),   fmt="%.0f", suffix="s")
            _km(ka4, "Lateral R",   lr.get("Lateral R (s)"), fmt="%.0f", suffix="s")
            _km(ka5, "Lateral L",   lr.get("Lateral L (s)"), fmt="%.0f", suffix="s")
            _km(ka6, "Dorsal",      lr.get("Dorsal (s)"),    fmt="%.0f", suffix="s")
            if lr.get("Lat.-Asym. %") and float(lr["Lat.-Asym. %"]) > 0:
                color = "#f85149" if float(lr["Lat.-Asym. %"]) > 10 else "#3fb950"
                st.markdown(
                    f'<small style="color:{color}">Lateral-Asymmetrie: '
                    f'<b>{float(lr["Lat.-Asym. %"]):.1f} %</b> | Datum: {lr["Datum"]}</small>',
                    unsafe_allow_html=True,
                )

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            for col_n, clr in [("Direkt 1RM", "#3b82f6"), ("Epley 1RM", "#3fb950")]:
                sub = df[df[col_n] > 0] if col_n in df.columns else pd.DataFrame()
                if sub.empty: continue
                fig.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_n], mode="lines+markers",
                                         name=col_n, line=dict(color=clr, width=2), marker=dict(size=7)))
            fig.update_layout(**_pl(height=280, title="Bankdrücken 1RM-Verlauf (kg)", yaxis=dict(title="kg")))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = go.Figure()
            for col_n, clr in [("Ventral (s)", "#3b82f6"), ("Lateral R (s)", "#3fb950"),
                                ("Lateral L (s)", "#d29922"), ("Dorsal (s)", "#a371f7")]:
                sub = df[df[col_n] > 0] if col_n in df.columns else pd.DataFrame()
                if sub.empty: continue
                fig2.add_trace(go.Scatter(x=sub["Datum"], y=sub[col_n], mode="lines+markers",
                                          name=col_n, line=dict(color=clr, width=2), marker=dict(size=7)))
            fig2.update_layout(**_pl(height=280, title="Rumpfkraftausdauer-Verlauf (s)", yaxis=dict(title="s")))
            st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Zwei Termine vergleichen ──────────────────────────────────────────
        if len(df) >= 2:
            with st.expander("🔍 Zwei Termine vergleichen"):
                datums_k = df["Datum"].tolist()
                kc1, kc2 = st.columns(2)
                kd1 = kc1.selectbox("Termin 1", datums_k, index=0, key="kr_cmp_d1")
                kd2 = kc2.selectbox("Termin 2", datums_k, index=len(datums_k)-1, key="kr_cmp_d2")
                kr1 = df[df["Datum"] == kd1].iloc[0]
                kr2 = df[df["Datum"] == kd2].iloc[0]
                compare_cols_k = ["Direkt 1RM", "Epley 1RM", "Rel. Kraft D", "Rel. Kraft E",
                                   "Ventral (s)", "Lateral R (s)", "Lateral L (s)", "Dorsal (s)", "Lat.-Asym. %"]
                rows_k = []
                for ck in compare_cols_k:
                    v1k = kr1.get(ck, 0) or 0
                    v2k = kr2.get(ck, 0) or 0
                    if v1k > 0 or v2k > 0:
                        diff_k = round(v2k - v1k, 2) if v1k > 0 and v2k > 0 else "—"
                        rows_k.append({"Messung": ck, kd1: f"{v1k:.2f}" if v1k else "—",
                                       kd2: f"{v2k:.2f}" if v2k else "—",
                                       "Differenz": f"{diff_k:+.2f}" if isinstance(diff_k, float) else diff_k})
                if rows_k:
                    st.dataframe(pd.DataFrame(rows_k), use_container_width=True, hide_index=True)

        # ── Bearbeiten / Löschen ──────────────────────────────────────────────
        st.markdown("---")
        with st.expander("✏️ Eintrag bearbeiten / löschen"):
            _render_kraft_edit(sid)


# ══════════════════════════════════════════════════════════════════════════════
# NEW PAGES (Phase 1)
# ══════════════════════════════════════════════════════════════════════════════

def page_startseite():
    """Home — personalisierte Übersicht für den aktiven Spieler."""
    spieler_liste = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
    if not spieler_liste:
        st.markdown(empty_state("⚽", "Willkommen bei Athletik Diagnostik",
                                "Lege unter Spieler → Verwaltung deinen ersten Spieler an."),
                    unsafe_allow_html=True)
        return

    auswahl = _player_selector()
    if not auswahl:
        return

    sid    = auswahl["id"]
    fms    = fms_letzter(sid)
    y      = y_balance_letzter(sid)
    sprint = sprint_letzter(sid)
    sprung = sprung_letzter(sid)
    agil   = agilitaet_letzter(sid)
    aus    = ausdauer_letzter(sid)
    kraft  = kraft_letzter(sid)
    anthro = anthropometrie_letzter(sid)
    verlet = verletzungen_laden(sid)

    rs              = risiko_score(fms, y, verlet)
    _, level        = risiko_label(rs)
    _spiro_s = spiro_test_letzter(sid)
    ascore          = athletik_score(fms, y, sprint, sprung, agil, aus, spiro_row=_spiro_s)
    defizite = defizite_ermitteln(fms, y, sprint, sprung, agil, aus, anthro, spiro_row=_spiro_s,
                                  geschlecht=auswahl.get("geschlecht", "Männlich"))
    alter    = berechne_alter(auswahl.get("geburtsdatum"))

    # ── Greeting ──────────────────────────────────────────────────────────────
    hour = datetime.now().hour
    greeting = "Guten Morgen" if hour < 12 else "Guten Tag" if hour < 18 else "Guten Abend"
    st.markdown(f"## {greeting}, Coach")

    # ── Player banner ─────────────────────────────────────────────────────────
    st.markdown(player_banner(auswahl, alter), unsafe_allow_html=True)

    # ── KPI row ───────────────────────────────────────────────────────────────
    score_color = C["green"] if ascore >= 75 else C["yellow"] if ascore >= 50 else C["red"]
    risk_colors = {"hoch": C["red"], "mittel": C["yellow"], "gering": C["green"]}
    risk_icons  = {"hoch": "🔴", "mittel": "🟡", "gering": "🟢"}
    risk_labels = {"hoch": "HANDLUNGSBEDARF HOCH", "mittel": "HANDLUNGSBEDARF", "gering": "UNAUFFÄLLIG"}

    # Last test date across all modules
    dates = []
    for row in [fms, y, sprint, sprung, agil, aus, anthro]:
        if row and row.get("datum"):
            dates.append(str(row["datum"]))
    letzter_test = max(dates) if dates else None

    # F-07: Hinweis wenn noch keine Testdaten vorhanden
    hat_tests = any([fms, y, sprint, sprung, agil, aus])
    if not hat_tests:
        st.info("ℹ️ Noch nicht genug Testdaten für einen vollständigen Athletik-Score. Führe mindestens einen Test durch.")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        score_display = (
            f'{ascore}<span style="font-size:16px;font-weight:400;color:{C["muted"]}">/100</span>'
            if hat_tests else
            f'<span style="font-size:20px;color:{C["muted"]}">—</span>'
        )
        st.markdown(kpi_card("Athletik Score", score_display, color=score_color if hat_tests else C["muted"]),
                    unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("Athletik-Status",
                             f'{risk_icons[level]} {risk_labels[level]}',
                             color=risk_colors[level]), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Letzter Test", letzter_test or "Kein Test",
                             subtitle="Datum"), unsafe_allow_html=True)
    with k4:
        verlet_count = len(verlet) if verlet else 0
        ausfall_ges  = sum(v.get("ausfall_tage") or 0 for v in (verlet or []))
        st.markdown(kpi_card("Verletzungshistorie",
                             str(verlet_count),
                             subtitle=f"{ausfall_ges} Ausfalltage gesamt"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Defizite & Stärken ────────────────────────────────────────────────────
    col_def, col_str = st.columns(2)

    with col_def:
        st.markdown(f'<div style="font-size:13px;font-weight:600;letter-spacing:1px;color:{C["muted"]};margin-bottom:8px">TOP DEFIZITE</div>', unsafe_allow_html=True)
        if not defizite:
            st.markdown(f'<div style="color:{C["green"]};font-size:14px;padding:10px 0">✅ Keine auffälligen Defizite erkannt.</div>', unsafe_allow_html=True)
        else:
            for d in defizite[:5]:
                st.markdown(deficit_row(d), unsafe_allow_html=True)
            if len(defizite) > 5:
                st.caption(f"+ {len(defizite)-5} weitere Defizite — Details im Spielerprofil")

    with col_str:
        st.markdown(f'<div style="font-size:13px;font-weight:600;letter-spacing:1px;color:{C["muted"]};margin-bottom:8px">STÄRKEN</div>', unsafe_allow_html=True)
        strengths = []
        if fms and fms["score"] >= 17:
            strengths.append(("FMS Bewegungsqualität", f'Score {fms["score"]}/21'))
        if y:
            avg_y = (y["composite_rechts"] + y["composite_links"]) / 2
            if avg_y >= 92:
                strengths.append(("Y-Balance", f'Ø {avg_y:.1f} %'))
        if sprint and sprint.get("bewertung_10m") in ("Sehr gut (Profi-Niveau)", "Gut (Leistungssport)"):
            strengths.append(("Sprint", sprint["bewertung_10m"]))
        if sprung and sprung.get("bewertung_cmj") in ("Sehr gut (Profi-Niveau)", "Gut (Leistungssport)"):
            strengths.append(("Explosivkraft", sprung["bewertung_cmj"]))
        if agil and agil.get("bew_t_test") in ("Sehr gut (Profi-Niveau)", "Gut (Leistungssport)"):
            strengths.append(("Agilität", agil["bew_t_test"]))
        if aus and aus.get("bewertung") == "Gut":
            strengths.append(("Ausdauer", f'VO₂max ~{aus["vo2max"]} ml/kg/min' if aus.get("vo2max") else "Gut"))
        if not strengths:
            st.markdown(f'<div style="color:{C["muted"]};font-size:14px;padding:10px 0">Noch keine Tests mit Stärken vorhanden.</div>', unsafe_allow_html=True)
        for bereich, detail in strengths[:5]:
            st.markdown(strength_row(bereich, detail), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Test-Übersicht ────────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:13px;font-weight:600;letter-spacing:1px;color:{C["muted"]};margin-bottom:10px">TESTMODULE — AKTUELLER STATUS</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    # Kraft-Beurteilungstext für Startseite-Karte
    from kraft import beurteilung_relative_kraft as _bwrk_s
    _rel_ks = (kraft.get("relative_kraft_direkt") or kraft.get("relative_kraft_geschaetzt")) if kraft else None
    if _rel_ks:
        _kraft_rating_s = _bwrk_s(_rel_ks, alter=alter, geschlecht=auswahl.get("geschlecht", "Männlich"))[0]
    elif kraft and kraft.get("ventral_sekunden"):
        _kraft_rating_s = "Ventral: %.0f s" % kraft["ventral_sekunden"]
    else:
        _kraft_rating_s = None

    # Y-Balance: Asymmetrie-Text als Rating (Farblogik in test_status_card reagiert auf "auffällig" / "Asymmetrie")
    _yb_rating_s = str(y["asymmetrie"]) if y and y.get("asymmetrie") else None

    # Anthropometrie-Beurteilung für Startseite (Ampelfarben)
    _anthro_kat = (anthro.get("bmi_kategorie") or "").strip() if anthro else ""
    _anthro_kat_l = _anthro_kat.lower()
    if "normalgewicht" in _anthro_kat_l:
        _anthro_rating_s = f"Unauffällig — {_anthro_kat}"
    elif "untergewicht" in _anthro_kat_l:
        _anthro_rating_s = f"Beobachten — {_anthro_kat}"
    elif "übergewicht" in _anthro_kat_l or "ubergewicht" in _anthro_kat_l:
        _anthro_rating_s = f"Handlungsbedarf — {_anthro_kat}"
    elif "adipositas" in _anthro_kat_l:
        _anthro_rating_s = f"Aktionsbedarf — {_anthro_kat}"
    elif anthro and anthro.get("bmi"):
        _anthro_rating_s = f"BMI {anthro['bmi']:.1f}"
    else:
        _anthro_rating_s = None

    # Stufentest-Beurteilung für Startseite — ausschließlich protokollspezifisch.
    from spiro import spiro_bewertung_v2 as _spiro_bewertung_v2
    _geschl_s = auswahl.get("geschlecht", "Männlich")
    _spiro_rating_s = _spiro_bewertung_v2(
        _spiro_s,
        alter_testtag=alter_am_datum(auswahl.get("geburtsdatum", ""), _spiro_s.get("datum", "")) or alter,
        geschlecht=_geschl_s,
        stufen=spiro_stufen_laden(_spiro_s["id"]),
    )["text"] if _spiro_s else None

    cards = [
        ("Anthropometrie", "📐", anthro, _anthro_rating_s,    anthro["datum"] if anthro else None),
        ("FMS", "📝", fms,
         (fms["bewertung"] + " — " + __import__("fms").fms_bewertung_kurz(fms["score"])[:55] + "…")
          if fms else None,
         fms["datum"] if fms else None),
        ("Y-Balance", "📏", y,      _yb_rating_s,           y["datum"] if y else None),
        ("Sprint",    "⚡", sprint, sprint["bewertung_10m"] if sprint else None, sprint["datum"] if sprint else None),
        ("Sprung",    "🦘", sprung, sprung["bewertung_cmj"] if sprung else None, sprung["datum"] if sprung else None),
        ("Agilität",  "🔀", agil,   agil["bew_t_test"]      if agil   else None, agil["datum"]   if agil   else None),
        ("Ausdauer",  "🫁", aus,    aus["bewertung"]        if aus    else None, aus["datum"]    if aus    else None),
        ("Kraft",     "💪", kraft,  _kraft_rating_s,         kraft["datum"] if kraft else None),
        ("Stufentest","🔬", _spiro_s, _spiro_rating_s,      _spiro_s["datum"] if _spiro_s else None),
    ]
    for i, (name, icon, row, rating, dt) in enumerate(cards):
        col = [c1, c2, c3][i % 3]
        with col:
            st.markdown(test_status_card(name, icon, dt, rating), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick actions ─────────────────────────────────────────────────────────
    st.markdown(f'<div style="font-size:13px;font-weight:600;letter-spacing:1px;color:{C["muted"]};margin-bottom:10px">SCHNELLZUGRIFF</div>', unsafe_allow_html=True)
    qa1, qa2, qa3, qa4 = st.columns(4)
    if qa1.button("👤 Spielerprofil", use_container_width=True):
        st.session_state["_nav_goto"] = "👤  Spieler"
        st.session_state["nav_sub_spieler"] = "🏃 Profil & Diagnostik"
        st.rerun()
    if qa2.button("🔬 Test starten", use_container_width=True):
        st.session_state["_nav_goto"] = "🔬  Diagnostik"
        st.rerun()
    if qa3.button("📅 Trainingsplan", use_container_width=True):
        st.session_state["_nav_goto"] = "📅  Training"
        st.rerun()
    if qa4.button("📈 Verlauf", use_container_width=True):
        st.session_state["_nav_goto"] = "📈  Entwicklung"
        st.rerun()


def page_zweckbestimmung():
    """Zweckbestimmung und Hinweise — erneut abrufbar aus den Einstellungen."""
    st.markdown("# 📋 Zweckbestimmung und Anwendungshinweise")
    st.markdown(
        f'<div style="background:#1c2128;border:1px solid #d29922;border-radius:8px;'
        f'padding:16px 20px;margin-bottom:20px">'
        f'<span style="color:#d29922;font-size:12px;font-weight:600;letter-spacing:1px">'
        f'VERSION {ZWECKBESTIMMUNG_VERSION}</span></div>',
        unsafe_allow_html=True,
    )

    for absatz in ZWECKBESTIMMUNG_TEXT_DISPLAY.split("\n\n"):
        st.markdown(absatz)

    st.markdown("---")
    st.markdown("### 🟢 🟡 🔴 Bedeutung der Ampelfarben")
    st.markdown(
        f'<div style="background:#0d1117;border-left:4px solid #3fb950;'
        f'border-radius:6px;padding:12px 16px;margin:8px 0">'
        f'<b style="color:#3fb950">Grün</b><br>'
        f'<span style="color:#8b949e">{AMPEL_GRUEN}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="background:#0d1117;border-left:4px solid #d29922;'
        f'border-radius:6px;padding:12px 16px;margin:8px 0">'
        f'<b style="color:#d29922">Gelb</b><br>'
        f'<span style="color:#8b949e">{AMPEL_GELB}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="background:#0d1117;border-left:4px solid #f85149;'
        f'border-radius:6px;padding:12px 16px;margin:8px 0">'
        f'<b style="color:#f85149">Rot</b><br>'
        f'<span style="color:#8b949e">{AMPEL_ROT}</span></div>',
        unsafe_allow_html=True,
    )
    st.caption(f"ℹ️ {AMPEL_FUSSZEILE}")

    st.markdown("---")
    st.markdown("### 🏋️ Trainingsplan-Hinweis")
    st.info(TRAININGSPLAN_HINWEIS)

    st.markdown("### 📐 Wachstum / Anthropometrie")
    st.info(PHV_HINWEIS)

    st.markdown("### 📝 FMS / Y-Balance")
    st.info(FMS_HINWEIS)

    st.markdown("---")
    st.markdown("### 📜 Bestätigungsprotokoll")
    alle = einwilligung_alle()
    if alle:
        df_einw = pd.DataFrame(alle)[["datum", "version", "benutzer"]]
        df_einw.columns = ["Datum", "Version", "Bestätigt von"]
        st.dataframe(df_einw, use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Bestätigung gespeichert.")

    st.markdown("---")
    st.markdown("### 🔄 Zweckbestimmung erneut bestätigen")
    benutzer_neu = st.text_input("Name", key="zweck_renew_name", placeholder="Trainer / Nutzer")
    if st.button("✅ Erneut bestätigen und speichern", key="zweck_renew_btn"):
        einwilligung_speichern(ZWECKBESTIMMUNG_VERSION, benutzer_neu.strip() or "Trainer")
        st.success("✅ Zweckbestimmung erneut bestätigt und gespeichert.")
        st.rerun()


def page_einstellungen():
    """Einstellungen — App-Konfiguration."""
    st.markdown(section_header("⚙️ Einstellungen", "App-Konfiguration und Datenverwaltung"),
                unsafe_allow_html=True)

    with st.expander("⚙️ Allgemein", expanded=True):
        st.markdown("### Vereinsinformationen")
        c1, c2 = st.columns(2)
        vereinsname = c1.text_input("Vereinsname", value=st.session_state.get("cfg_vereinsname", ""), key="cfg_vname")
        saison      = c2.text_input("Aktuelle Saison", value=st.session_state.get("cfg_saison", "2025/26"), key="cfg_saison")
        if st.button("💾 Speichern", key="cfg_save", type="primary"):
            # cfg_saison wird automatisch via Widget-Key gesetzt — kein manuelles Setzen
            st.session_state["cfg_vereinsname"] = vereinsname
            st.toast("✅ Einstellungen gespeichert (Session).", icon=None)

        # ── Saisonwechsel ──────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### ⚽ Saisonwechsel")
        st.caption(
            "Das Datum des Saisonwechsels bestimmt die automatisch berechnete "
            "Fußball-Altersklasse (z. B. U11) — keine jährliche manuelle Pflege nötig. "
            "Standard: 1. Juli."
        )
        _sw_t, _sw_m = _sw_laden()
        _swc1, _swc2, _swc3 = st.columns([1, 1, 2])
        _sw_tag_neu   = _swc1.number_input("Tag",   min_value=1, max_value=31,
                                           value=int(_sw_t), step=1, key="sw_tag_inp")
        _sw_monat_neu = _swc2.number_input("Monat", min_value=1, max_value=12,
                                           value=int(_sw_m), step=1, key="sw_monat_inp")
        _swc3.markdown(
            f"<br><small style='color:#58a6ff'>Aktuelle Saison: "
            f"<b>{_saison_label(int(_sw_tag_neu), int(_sw_monat_neu))}</b></small>",
            unsafe_allow_html=True,
        )
        if st.button("💾 Saisonwechsel speichern", key="sw_save"):
            _sw_speichern(int(_sw_tag_neu), int(_sw_monat_neu))
            st.toast("✅ Saisonwechsel gespeichert.", icon=None)
            st.rerun()

        st.markdown("---")
        st.markdown("### 🏷️ Vereinslogo")
        st.caption(
            "Das Logo wird in allen generierten PDFs (Anleitungen, Profile, Protokolle) "
            "automatisch eingebunden — einmal hochladen, dauerhaft gespeichert."
        )
        _gespeichertes_logo = logo_laden()
        _col_logo, _col_logo_btn = st.columns([3, 1])
        with _col_logo:
            _neue_logo_datei = st.file_uploader(
                "Logo hochladen (PNG, JPG — max. 10 MB)",
                type=["png", "jpg", "jpeg"],
                key="cfg_logo_upload",
                label_visibility="collapsed",
            )
        with _col_logo_btn:
            if _gespeichertes_logo:
                if st.button("🗑️ Logo löschen", key="cfg_logo_del",
                             use_container_width=True):
                    logo_loeschen()
                    _save_ok("Vereinslogo gelöscht.")
                    st.rerun()
        if _neue_logo_datei is not None:
            _logo_raw = _neue_logo_datei.getvalue()
            from utils.file_magic import validate_image
            _ok, _err = validate_image(_logo_raw, max_mb=config.MAX_LOGO_MB)
            if not _ok:
                st.error(f"❌ {_err}")
                _log.warning("Abgelehnter Logo-Upload: %s", _err)
            else:
                from utils.file_magic import optimize_image as _opt_img_logo
                logo_speichern(_opt_img_logo(_logo_raw))
                _save_ok("Vereinslogo gespeichert.")
                st.rerun()
        if _gespeichertes_logo:
            import io as _io
            try:
                st.image(_io.BytesIO(_gespeichertes_logo), width=160,
                         caption=f"Gespeichertes Logo ({len(_gespeichertes_logo)//1024} KB)")
            except Exception:
                st.info("Logo gespeichert (Vorschau nicht verfügbar).")
        else:
            st.info("Noch kein Vereinslogo gespeichert.")

        # ── Trainer-Beitrittscode (nur für Vereinsadmin) ──────────────────────
        if _akt_user().get("rolle") in ("Vereinsadmin", "Superadmin"):
            st.markdown("---")
            st.markdown("### 🔑 Trainer-Beitrittscode")
            st.caption(
                "Teile diesen Code mit Trainern, damit sie sich selbst registrieren können. "
                "Nach der Registrierung musst du das Konto unter **Benutzerverwaltung** freischalten."
            )
            from database import registrier_code_laden, registrier_code_regenerieren
            _aktueller_code = registrier_code_laden(_akt_user()["verein_id"])
            _c_code, _c_btn = st.columns([3, 1])
            with _c_code:
                st.code(_aktueller_code or "—", language=None)
            with _c_btn:
                if st.button("🔄 Neu generieren", key="regen_code",
                             use_container_width=True,
                             help="Ungültig macht den alten Code — alle neuen Trainer brauchen den neuen Code."):
                    _neuer = registrier_code_regenerieren(_akt_user()["verein_id"])
                    st.success(f"Neuer Code: **{_neuer}**")
                    st.rerun()

        st.markdown("---")
        st.markdown("### Kader-Übersicht")
        alle = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
        st.metric("Spieler gesamt", len(alle))
        if alle:
            mannschaften = list({p.get("mannschaft") or "Keine" for p in alle})
            st.markdown(f"**Mannschaften:** {', '.join(sorted(mannschaften))}")

    with st.expander("📋 Zweckbestimmung"):
        page_zweckbestimmung()

    with st.expander("✅ Checklisten"):
        from help_ui import _DEFAULT_CHECKLISTE, _TEST_CHECKLISTE

        chk_view_tab, chk_edit_tab = st.tabs(
            ["👁️ Alle Checklisten ansehen", "✏️ Eigene Punkte ergänzen"]
        )

        with chk_view_tab:
            st.markdown("### 📋 Standard-Checkliste (gilt für alle Tests)")
            st.caption(
                "Diese Punkte erscheinen vor jedem Test. "
                "Basierend auf NSCA-Richtlinien und DFB-Trainerempfehlungen."
            )
            for icon, text in _DEFAULT_CHECKLISTE:
                st.markdown(
                    f'<div style="display:flex;gap:10px;padding:5px 0;'
                    f'border-bottom:1px solid #21262d">'
                    f'<span style="font-size:16px;min-width:22px">{icon}</span>'
                    f'<span style="color:#e6edf3;font-size:13px">{text}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("### 🔬 Testspezifische Checklisten")

            _CHK_TEST_MAP = {
                "sprint": ("⚡ Sprint", "sprint"),
                "jump":   ("🦘 Sprung / CMJ / Drop Jump", "jump"),
                "agility":("🔀 Agilität", "agility"),
                "yoyo":   ("🫁 Yo-Yo Ausdauer", "yoyo"),
                "fms":    ("📝 FMS", "fms"),
                "y_balance":("📏 Y-Balance", "y_balance"),
                "anthropometrie": ("📐 Anthropometrie", "anthropometrie"),
                "kraft":  ("💪 Kraft", "kraft"),
            }
            for tid, (label, chk_key) in _CHK_TEST_MAP.items():
                items = _TEST_CHECKLISTE.get(chk_key, [])
                if not items:
                    continue
                with st.expander(f"📋 {label}  ({len(items)} Punkte)", expanded=False):
                    for icon, text in items:
                        st.markdown(
                            f'<div style="display:flex;gap:10px;padding:4px 0;'
                            f'border-bottom:1px solid #21262d">'
                            f'<span style="font-size:15px;min-width:22px">{icon}</span>'
                            f'<span style="color:#c9d1d9;font-size:12px">{text}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    # Eigene Punkte aus DB anzeigen
                    custom = checkliste_custom_laden(tid)
                    if custom:
                        st.markdown(
                            f'<div style="margin-top:8px;font-size:10px;color:#58a6ff;'
                            f'letter-spacing:1px">EIGENE PUNKTE</div>',
                            unsafe_allow_html=True,
                        )
                        for line in custom.splitlines():
                            if line.strip():
                                st.markdown(
                                    f'<div style="display:flex;gap:10px;padding:4px 0">'
                                    f'<span>📌</span>'
                                    f'<span style="color:#c9d1d9;font-size:12px">{line.strip()}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

        with chk_edit_tab:
            st.markdown("### ✏️ Eigene Checklistenpunkte pro Test")
            st.caption(
                "Ergänze testspezifische Routineschritte, die nach den Standardpunkten "
                "in der Trainer-Checkliste erscheinen. Ein Punkt pro Zeile."
            )
            st.markdown("---")
            for tid in ALL_TEST_IDS:
                label = TEST_LABELS[tid]
                aktuell = checkliste_custom_laden(tid)
                n_std = len(_DEFAULT_CHECKLISTE) + len(_TEST_CHECKLISTE.get(tid, []))
                badge = f"{n_std} Standard"
                with st.expander(f"📋 {label}  —  {badge}-Punkte", expanded=False):
                    neuer_text = st.text_area(
                        "Eigene Punkte (eine Zeile = ein Punkt)",
                        value=aktuell,
                        height=130,
                        placeholder=(
                            "z. B.\nVideoaufnahme starten\n"
                            "Trikot-Nummer notiert\nEltern informiert"
                        ),
                        key=f"chk_custom_{tid}",
                        label_visibility="collapsed",
                    )
                    col_save, col_reset = st.columns([2, 1])
                    if col_save.button("💾 Speichern", key=f"chk_save_{tid}",
                                       use_container_width=True):
                        checkliste_custom_speichern(tid, neuer_text)
                        st.success("✅ Gespeichert.")
                    if col_reset.button("🗑️ Löschen", key=f"chk_del_{tid}",
                                        use_container_width=True):
                        checkliste_custom_speichern(tid, "")
                        st.rerun()

    with st.expander("🌐 Sprache / Language"):
        st.markdown("### 🌐 Sprache / Language")
        st.caption(
            "Wähle die Anzeigesprache für die Navigation und Benutzeroberfläche. "
            "Die fachlichen Testinhalte bleiben in der jeweiligen Originalsprache."
        )
        st.markdown("---")

        aktuell_lang = get_lang()
        lang_options  = list(SPRACHEN.keys())
        lang_labels   = list(SPRACHEN.values())
        try:
            lang_idx = lang_options.index(aktuell_lang)
        except ValueError:
            lang_idx = 0

        neue_sprache_label = st.radio(
            "Sprache / Language",
            lang_labels,
            index=lang_idx,
            key="lang_radio_sel",
            label_visibility="collapsed",
        )
        # Index rückrechnen
        neue_sprache_code = lang_options[lang_labels.index(neue_sprache_label)]

        if st.button("✅ Sprache übernehmen / Apply Language", type="primary",
                     use_container_width=True):
            set_lang(neue_sprache_code)
            st.success(
                f"✅ Sprache gesetzt: {SPRACHEN[neue_sprache_code]}"
                if neue_sprache_code == "de"
                else f"✅ Language set: {SPRACHEN[neue_sprache_code]}"
            )
            st.rerun()

        st.markdown("---")
        st.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;'
            f'border-radius:8px;padding:14px 16px">'
            f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;margin-bottom:8px">VORSCHAU / PREVIEW</div>'
            f'<div style="color:#e6edf3;font-size:13px">'
            f'<b>Navigation:</b> {t("nav_startseite")} &nbsp;·&nbsp; '
            f'{t("nav_spieler")} &nbsp;·&nbsp; {t("nav_diagnostik")}<br>'
            f'<b>Buttons:</b> {t("speichern")} &nbsp;·&nbsp; {t("loeschen")} &nbsp;·&nbsp; {t("generieren")}<br>'
            f'<b>Felder:</b> {t("vorname")} &nbsp;·&nbsp; {t("nachname")} &nbsp;·&nbsp; {t("geburtsdatum")}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    with st.expander("🔑 Passwort ändern"):
        st.markdown("### 🔑 Passwort ändern")
        st.caption(
            "Gib dein aktuelles Passwort zur Bestätigung ein, dann das neue Passwort zweimal."
        )
        st.markdown("---")
        _pw_alt    = st.text_input("Aktuelles Passwort",       key="pw_change_alt",  type="password")
        _pw_neu1   = st.text_input("Neues Passwort",           key="pw_change_neu1", type="password")
        _pw_neu2   = st.text_input("Neues Passwort bestätigen", key="pw_change_neu2", type="password")
        if st.button("🔑 Passwort ändern", key="pw_change_btn", type="primary"):
            _u = _akt_user()
            _u_db = benutzer_by_id(_u["id"])
            if not _pw_alt:
                st.error("❌ Bitte das aktuelle Passwort eingeben.")
            elif _u_db is None or not _pw_verify(_pw_alt, _u_db.get("passwort_hash") or ""):
                st.error("❌ Das aktuelle Passwort ist falsch.")
            elif len(_pw_neu1) < 4:
                st.error("❌ Das neue Passwort muss mindestens 4 Zeichen haben.")
            elif _pw_neu1 != _pw_neu2:
                st.error("❌ Die neuen Passwörter stimmen nicht überein.")
            else:
                benutzer_passwort(_u["id"], _pw_neu1)
                # Alle Sessions wurden in benutzer_passwort() bereits serverseitig
                # ungültig gemacht. Jetzt auch die lokale Session + Cookie löschen
                # und den Benutzer zur Login-Seite weiterleiten.
                if _cookie_ctrl:
                    try:
                        _cookie_ctrl.remove("ath_sid")
                    except Exception:
                        pass
                _pw_keys_del = [k for k in st.session_state.keys()
                                if k != "__logout_ok__"]
                for _pwk in _pw_keys_del:
                    del st.session_state[_pwk]
                st.session_state["__logout_ok__"] = True
                st.session_state["__pw_changed__"] = True
                st.rerun()

    with st.expander("🔒 Datenschutz & Datenverwaltung"):
        st.markdown("### 🔒 Datenschutz & Datenverwaltung")

        st.info(
            "**Was wird gespeichert?** Name, Geburtsdatum, Positions- und "
            "Vereinsangaben sowie alle eingegebenen Testergebnisse und "
            "Verletzungseinträge.\n\n"
            "**Wo?** Ausschließlich lokal in der Datei `athletik.db` auf diesem "
            "Gerät. Es erfolgt keine Übertragung an externe Server oder Cloud-Dienste.\n\n"
            "**Wie lange?** Bis zur manuellen Löschung — es gibt keine automatische "
            "Löschfrist. Erstelle regelmäßig Sicherungskopien der Datenbankdatei."
        )

        st.markdown("---")
        st.markdown("### 🗑️ Einzelnen Spieler vollständig löschen")
        st.caption(
            "Löscht den Spieler samt aller Testdaten, Verletzungshistorie und "
            "Trainingsplan. Diese Aktion kann nicht rückgängig gemacht werden."
        )
        alle_spieler = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
        if not alle_spieler:
            st.info("Keine Spieler vorhanden.")
        else:
            del_namen = {p["name"]: p["id"] for p in alle_spieler}
            del_auswahl_name = st.selectbox(
                "Spieler auswählen", options=list(del_namen.keys()),
                key="dsg_del_spieler"
            )
            bestaetigung = st.text_input(
                f'Zur Bestätigung den Namen **{del_auswahl_name}** eintippen:',
                key="dsg_del_confirm"
            )
            if st.button("🗑️ Spieler unwiderruflich löschen", key="dsg_del_btn",
                         type="primary"):
                if bestaetigung.strip() == del_auswahl_name:
                    spieler_loeschen(del_namen[del_auswahl_name])
                    if st.session_state.get("aktiver_spieler_id") == del_namen[del_auswahl_name]:
                        del st.session_state["aktiver_spieler_id"]
                    st.success(f"✅ Spieler **{del_auswahl_name}** und alle zugehörigen Daten gelöscht.")
                    st.rerun()
                else:
                    st.error("❌ Name stimmt nicht überein — Löschung abgebrochen.")

        st.markdown("---")
        st.markdown("### ⚠️ Gesamte Datenbank zurücksetzen")
        st.warning(
            "Löscht **alle** Spieler, Testergebnisse, Verletzungshistorien und "
            "Einwilligungseinträge. Die App-Struktur bleibt erhalten. "
            "**Diese Aktion ist endgültig und kann nicht rückgängig gemacht werden.**"
        )
        reset_check = st.checkbox(
            "Ich habe eine Sicherungskopie erstellt und bestätige den vollständigen Reset.",
            key="dsg_reset_check"
        )
        reset_confirm = st.text_input(
            "Zur Bestätigung **RESET** eintippen:", key="dsg_reset_text"
        )
        if st.button("🔥 Alle Daten löschen", key="dsg_reset_btn",
                     type="primary", disabled=not reset_check):
            if reset_confirm.strip() == "RESET":
                db_komplett_zuruecksetzen()
                for key in list(st.session_state.keys()):
                    if key.startswith("aktiver_spieler") or key == "zweck_bestaetigt":
                        del st.session_state[key]
                st.success("✅ Alle Daten wurden gelöscht. Die App ist zurückgesetzt.")
                st.rerun()
            else:
                st.error("❌ Bestätigungswort falsch — Reset abgebrochen.")

    with st.expander("💾 Export & Backup"):
        st.markdown("### Daten exportieren")
        alle = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
        if not alle:
            st.info("Keine Spieler vorhanden.")
        else:
            rows = []
            for p in alle:
                fms    = fms_letzter(p["id"])
                y      = y_balance_letzter(p["id"])
                sprint = sprint_letzter(p["id"])
                aus    = ausdauer_letzter(p["id"])
                verlet = verletzungen_laden(p["id"])
                ascore = athletik_score(fms, y, sprint, None, None, aus,
                                        spiro_row=spiro_test_letzter(p["id"]))
                rs     = risiko_score(fms, y, verlet)
                _, rlv = risiko_label(rs)
                rows.append({
                    "Name":            p["name"],
                    "Position":        p.get("position") or "—",
                    "Mannschaft":      p.get("mannschaft") or "—",
                    "Altersklasse":    p.get("altersklasse") or "—",
                    "Athletik Score":  ascore,
                    "Risiko":          rlv.capitalize(),
                    "FMS":             int(fms["score"]) if fms else None,
                    "VO₂max":          float(aus["vo2max"]) if aus and aus.get("vo2max") else None,
                })
            df_export = pd.DataFrame(rows)
            st.dataframe(df_export, use_container_width=True, hide_index=True)
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Kader-CSV herunterladen", csv,
                               f"kader_export_{date.today()}.csv", "text/csv",
                               use_container_width=True)

        st.markdown("---")
        st.markdown("### 🛡️ Datensicherheit")

        _bst = backup_status_laden()

        # ── KPI-Zeile ─────────────────────────────────────────────────────────
        _ds1, _ds2, _ds3 = st.columns(3)
        _ds1.metric(
            "Datenbank",
            "✅ Erreichbar" if _bst["db_erreichbar"] else "❌ Nicht erreichbar",
            f"{_bst['db_groesse_kb']} KB" if _bst["db_groesse_kb"] else None,
        )
        _ds2.metric(
            "Letztes Backup",
            _bst["letztes_backup_datum"] or "Noch keins",
            f"{_bst['letztes_backup_groesse_kb']} KB"
            if _bst["letztes_backup_groesse_kb"] else None,
        )
        _ds3.metric("Backups vorhanden", _bst["backup_anzahl"])

        if not _bst["db_erreichbar"]:
            st.error(
                "⚠️ Datenbank momentan nicht erreichbar. "
                "Bitte später erneut versuchen."
            )
        if not _bst["letztes_backup_datum"]:
            st.warning(
                "⚠️ Noch kein Backup vorhanden. "
                "Erstelle jetzt ein erstes Backup."
            )

        # ── Manueller Backup-Button ───────────────────────────────────────────
        if st.button(
            "📦 Jetzt Backup erstellen",
            key="dsg_backup_btn",
            help="Erstellt sofort ein konsistentes SQLite-Backup via Online-Backup-API",
        ):
            with st.spinner("Backup wird erstellt …"):
                _bk_ok, _bk_msg = db_backup_erstellen()
            if _bk_ok:
                st.success(f"✅ {_bk_msg}")
                st.rerun()
            else:
                st.error(f"❌ Backup fehlgeschlagen: {_bk_msg}")

        st.caption(
            "Backups werden täglich automatisch erstellt und in "
            "`uploads/backups/` gespeichert (30 Tage Aufbewahrung). "
            "Die Datenbankdatei ist nicht im Git-Repository enthalten."
        )

        # ── Backup-Verlauf ────────────────────────────────────────────────────
        if _bst["backups"]:
            with st.expander(
                f"📋 Backup-Verlauf ({_bst['backup_anzahl']} Datei(en))",
                expanded=False,
            ):
                for _b in _bst["backups"]:
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'padding:6px 0;border-bottom:1px solid #21262d;'
                        f'font-size:13px">'
                        f'<span style="color:#e6edf3;font-family:monospace">'
                        f'{_b["name"]}</span>'
                        f'<span style="color:#8b949e">'
                        f'{_b["datum"]} · {_b["groesse_kb"]} KB</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Eigene Dokumente hochladen / verwalten
# ══════════════════════════════════════════════════════════════════════════════

def _custom_docs_section(kategorie: str, titel: str = "Eigene Dokumente"):
    """Upload, Anzeige und Verwaltung eigener PDF-Dokumente.
    kategorie: 'anleitungen' oder 'protokolle'.
    Dateien werden in config.DOCS_DIR / kategorie gespeichert
    (persistentes Volume in Produktion).
    """
    from utils.file_magic import validate_pdf

    ordner = config.DOCS_DIR / kategorie
    ordner.mkdir(parents=True, exist_ok=True)

    st.markdown(f"---\n### 📂 {titel}")
    st.caption(
        "Eigene PDFs hochladen — z. B. externe Anleitungen, Vereinsformulare "
        "oder angepasste Protokolle. Die Dateien bleiben dauerhaft gespeichert."
    )

    # ── Upload ────────────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "PDF hochladen (Mehrfachauswahl möglich)",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"custom_upload_{kategorie}",
    )
    if uploaded:
        neu = 0
        fehler = []
        for f in uploaded:
            raw = f.getvalue()
            ok, err = validate_pdf(raw, max_mb=config.MAX_DOC_MB)
            if not ok:
                fehler.append(f"**{f.name}**: {err}")
                _log.warning("Abgelehnter PDF-Upload: %s — %s", f.name, err)
                continue
            ziel = ordner / f.name
            with open(ziel, "wb") as fh:
                fh.write(raw)
            neu += 1
        if fehler:
            for msg in fehler:
                st.error(f"❌ {msg}")
        if neu:
            _save_ok(f"{neu} Datei(en) gespeichert.")
            st.rerun()

    # ── Gespeicherte Dateien ──────────────────────────────────────────────────
    dateien = sorted(ordner.glob("*.pdf"))
    if not dateien:
        st.info("Noch keine eigenen Dokumente hochgeladen.")
        return

    st.markdown(f"**{len(dateien)} gespeicherte{'s' if len(dateien) == 1 else ''} "
                f"Dokument{'' if len(dateien) == 1 else 'e'}:**")
    for pdf_path in dateien:
        c_name, c_dl, c_del = st.columns([5, 2, 1])
        size_kb = pdf_path.stat().st_size // 1024
        c_name.markdown(
            f'<div style="padding:5px 0;color:#e6edf3;font-size:13px">'
            f'📄 {pdf_path.name}'
            f'<span style="color:#8b949e;font-size:11px;margin-left:8px">{size_kb} KB</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with open(pdf_path, "rb") as fh:
            c_dl.download_button(
                "⬇️ Download",
                data=fh.read(),
                file_name=pdf_path.name,
                mime="application/pdf",
                key=f"dl_{kategorie}_{pdf_path.stem}",
                use_container_width=True,
            )
        if c_del.button("🗑️", key=f"del_{kategorie}_{pdf_path.stem}",
                        help=f"{pdf_path.name} löschen", use_container_width=True):
            pdf_path.unlink(missing_ok=True)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DOKUMENTE (Protokoll + Anleitungen kombiniert)
# ══════════════════════════════════════════════════════════════════════════════

def page_dokumente():
    """Kombinierte Dokumente-Seite: Anleitungen und Protokoll in einer."""
    st.markdown(
        section_header("📄 Dokumente", "Testanleitungen und Druckprotokolle"),
        unsafe_allow_html=True,
    )
    _inline_spielerwechsel("dokumente")
    tab_anl, tab_proto = st.tabs(["📄 Testanleitungen", "🖨️ Druckprotokoll"])
    with tab_anl:
        page_export_pdf()
    with tab_proto:
        page_testprotokoll()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TESTANLEITUNGEN EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def page_export_pdf():
    """Testanleitungen als druckbares PDF exportieren."""
    st.markdown(
        section_header("📄 Testanleitungen exportieren",
                       "Vollständige Coaching-Anleitungen als druckbares PDF"),
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="background:{C['surface']};border:1px solid {C['border']};
                    border-radius:10px;padding:16px 20px;margin-bottom:18px">
          <div style="font-size:13px;color:{C['text']};line-height:1.7">
            Exportiere vollständige Testanleitungen für Coaches ohne App-Zugang.<br>
            Das PDF enthält: <b>Ziel, Aufbau, Durchführung, Trainerhinweis,
            Fehlerquellen, Sicherheitshinweise und Testskizzen</b>.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Testauswahl ──────────────────────────────────────────────────────────
    st.markdown("### 📋 Tests auswählen")

    col_auswahl, col_opt = st.columns([3, 1])

    with col_opt:
        alle_auswaehlen = st.checkbox("Alle Tests", value=True, key="pdf_alle")
        mit_deckblatt   = st.checkbox("Deckblatt", value=True, key="pdf_deckblatt")

    with col_auswahl:
        if alle_auswaehlen:
            selected_ids = ALL_TEST_IDS
            # Show labels as info
            muted_color = C["muted"]
            st.markdown(
                f"<div style='color:{muted_color};font-size:12px;padding:4px 0'>"
                + " &nbsp;·&nbsp; ".join(TEST_LABELS[tid] for tid in ALL_TEST_IDS)
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            options     = list(TEST_LABELS.values())
            id_by_label = {v: k for k, v in TEST_LABELS.items()}
            selected_labels = st.multiselect(
                "Tests auswählen",
                options,
                default=options[:3],
                key="pdf_test_select",
                label_visibility="collapsed",
            )
            selected_ids = [id_by_label[lbl] for lbl in selected_labels]

    # ── Einzeltest-Schnelldownload ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚡ Einzeltest-Schnelldownload")
    st.caption("Ein Test direkt als PDF — kein weiterer Klick nötig.")
    _qt_cols = st.columns(4)
    for _qi, _tid in enumerate(ALL_TEST_IDS):
        _ql = TEST_LABELS[_tid]
        if _qt_cols[_qi % 4].button(f"📄 {_ql}", key=f"qt_{_tid}", use_container_width=True):
            with st.spinner(f"{_ql} wird erstellt …"):
                try:
                    _qb = generate_anleitung_pdf(
                        [_tid],
                        mit_deckblatt=False,
                        vereinsname=st.session_state.get("cfg_vereinsname", ""),
                        saison=st.session_state.get("cfg_saison", ""),
                        logo_bytes=logo_laden(),
                    )
                    st.download_button(
                        f"⬇️ {_ql} herunterladen",
                        data=_qb,
                        file_name=f"Anleitung_{_ql.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"qt_dl_{_tid}",
                    )
                except Exception as _qe:
                    st.error(f"Fehler: {_qe}")

    # ── Vorschau der Inhalte ─────────────────────────────────────────────────
    if selected_ids:
        st.markdown("---")
        st.markdown("### 📑 Enthaltene Abschnitte")

        from test_help import TEST_HELP as _TH
        cols = st.columns(min(len(selected_ids), 3))
        for i, tid in enumerate(selected_ids):
            data = _TH[tid]
            with cols[i % len(cols)]:
                st.markdown(
                    f"""
                    <div style="background:{C['surface']};border:1px solid {C['border']};
                                border-radius:8px;padding:12px 14px;margin-bottom:10px">
                      <div style="font-weight:700;font-size:12px;color:{C['blue']};
                                  margin-bottom:4px">{data['name']}</div>
                      <div style="font-size:11px;color:{C['muted']};line-height:1.5">
                        {data['kurzbeschreibung'][:100]}…
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("---")

        # ── Vereins-Personalisierung ─────────────────────────────────────────
        st.markdown("### 🏟️ Vereins-Personalisierung")
        _vn = st.session_state.get("cfg_vereinsname", "")
        _sn = st.session_state.get("cfg_saison", "")
        if _vn or _sn:
            _info_parts = []
            if _vn:
                _info_parts.append(f"**Verein:** {_vn}")
            if _sn:
                _info_parts.append(f"**Saison:** {_sn}")
            st.success("  ·  ".join(_info_parts) + "  — wird im PDF-Header und Deckblatt verwendet.")
        else:
            st.info(
                "Kein Vereinsname oder Saison eingetragen. "
                "Unter **⚙️ Einstellungen → Allgemein** eintragen, um das PDF zu personalisieren."
            )

        # ── Logo: dauerhaft aus DB, optional überschreiben ───────────────────
        _logo_bytes: bytes | None = logo_laden()
        if _logo_bytes:
            import io as _io2
            try:
                _lcol1, _lcol2 = st.columns([1, 4])
                _lcol1.image(_io2.BytesIO(_logo_bytes), width=80)
                _lcol2.success(
                    "✅ Vereinslogo aus den Einstellungen wird automatisch verwendet. "
                    "Anderes Logo hochladen, um es für dieses PDF zu ersetzen."
                )
            except Exception:
                st.success("✅ Vereinslogo gespeichert — wird im PDF verwendet.")
        else:
            st.info(
                "Kein Logo gespeichert. Unter **⚙️ Einstellungen → Allgemein** dauerhaft hinterlegen, "
                "oder hier einmalig für dieses PDF hochladen."
            )
        _logo_override = st.file_uploader(
            "Alternatives Logo (nur für diesen Export, PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            key="pdf_logo_upload",
            label_visibility="collapsed",
        )
        if _logo_override is not None:
            _raw_override = _logo_override.getvalue()
            from utils.file_magic import validate_image as _vi, optimize_image as _opt_img_ov
            _ok_ov, _err_ov = _vi(_raw_override, max_mb=config.MAX_LOGO_MB)
            if not _ok_ov:
                st.error(f"❌ {_err_ov}")
                _logo_bytes = None
            else:
                _logo_bytes = _opt_img_ov(_raw_override)

        st.markdown("---")

        # ── Generieren ───────────────────────────────────────────────────────
        st.markdown("### 📥 PDF generieren")
        n_tests = len(selected_ids)
        st.info(
            f"**{n_tests} Test{'s' if n_tests != 1 else ''}** ausgewählt. "
            "Das PDF wird direkt im Browser zum Download angeboten."
        )

        if st.button("⚙️ PDF generieren", type="primary", use_container_width=True,
                     key="pdf_generate_btn"):
            with st.spinner("PDF wird erstellt …"):
                try:
                    pdf_bytes = generate_anleitung_pdf(
                        selected_ids,
                        mit_deckblatt=mit_deckblatt,
                        vereinsname=st.session_state.get("cfg_vereinsname", ""),
                        saison=st.session_state.get("cfg_saison", ""),
                        logo_bytes=_logo_bytes,
                    )
                    st.session_state["_pdf_bytes"]    = pdf_bytes
                    st.session_state["_pdf_ready"]    = True
                    st.session_state["_pdf_test_ids"] = selected_ids
                except Exception as exc:
                    st.error(f"Fehler beim Erstellen des PDFs: {exc}")
                    st.session_state["_pdf_ready"] = False

        if st.session_state.get("_pdf_ready") and "_pdf_bytes" in st.session_state:
            ids_in_file = st.session_state.get("_pdf_test_ids", selected_ids)
            if set(ids_in_file) == set(selected_ids):
                pdf_bytes = st.session_state["_pdf_bytes"]
                n = len(ids_in_file)
                if n == len(ALL_TEST_IDS):
                    fname = "Testanleitungen_Komplett.pdf"
                elif n == 1:
                    fname = f"Testanleitung_{TEST_LABELS[ids_in_file[0]].replace(' ', '_')}.pdf"
                else:
                    fname = f"Testanleitungen_{n}_Tests.pdf"

                st.success(f"✅ PDF fertig — {len(pdf_bytes) // 1024} KB")
                st.download_button(
                    label="📥 PDF herunterladen",
                    data=pdf_bytes,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True,
                    key="pdf_dl_btn",
                )
    else:
        st.warning("Bitte mindestens einen Test auswählen.")

    _custom_docs_section("anleitungen", "Eigene Anleitungen")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SPIELER-VERGLEICH
# ══════════════════════════════════════════════════════════════════════════════

def page_spieler_vergleich():
    st.markdown("# ⚖️ Spieler-Vergleich")
    st.markdown(
        '<p style="color:#8b949e;margin-top:-8px">Zwei Athleten direkt gegenüberstellen — '
        'Testwerte, Stärken und Defizite auf einen Blick.</p>',
        unsafe_allow_html=True,
    )
    _inline_spielerwechsel("vergleich")
    st.markdown("---")

    alle_spieler = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
    if len(alle_spieler) < 2:
        st.info("⚠️ Mindestens **zwei Spieler** werden für den Vergleich benötigt. "
                "Bitte unter **Spieler → Verwaltung** weitere Spieler anlegen.")
        return

    # ── Preset from profile page ───────────────────────────────────────────────
    if "vergl_preset_pid" in st.session_state:
        _preset_pid = st.session_state.pop("vergl_preset_pid")
        _preset_player = next((p for p in alle_spieler if p["id"] == _preset_pid), None)
        if _preset_player:
            st.session_state["vergl_sp1"] = _preset_player

    # ── Player selectors ──────────────────────────────────────────────────────
    c1, _gap, c2 = st.columns([5, 1, 5])
    with c1:
        sp1 = st.selectbox(
            "🔵 Spieler A",
            alle_spieler,
            format_func=lambda x: x["name"],
            key="vergl_sp1",
        )
    with c2:
        # Default to a different player
        sp2_default = next(
            (p for p in alle_spieler if p["id"] != sp1["id"]),
            alle_spieler[0],
        )
        sp2_idx = next(
            (i for i, p in enumerate(alle_spieler) if p["id"] == sp2_default["id"]), 0
        )
        sp2 = st.selectbox(
            "🟢 Spieler B",
            alle_spieler,
            index=sp2_idx,
            format_func=lambda x: x["name"],
            key="vergl_sp2",
        )

    if sp1["id"] == sp2["id"]:
        st.warning("⚠️ Bitte zwei **verschiedene** Spieler auswählen.")
        return

    # ── Load data ─────────────────────────────────────────────────────────────
    pid1, pid2 = sp1["id"], sp2["id"]
    fms1  = fms_letzter(pid1);        fms2  = fms_letzter(pid2)
    y1    = y_balance_letzter(pid1);  y2    = y_balance_letzter(pid2)
    spr1  = sprint_letzter(pid1);     spr2  = sprint_letzter(pid2)
    spg1  = sprung_letzter(pid1);     spg2  = sprung_letzter(pid2)
    agil1 = agilitaet_letzter(pid1);  agil2 = agilitaet_letzter(pid2)
    aus1  = ausdauer_letzter(pid1);   aus2  = ausdauer_letzter(pid2)
    spiro1 = spiro_test_letzter(pid1); spiro2 = spiro_test_letzter(pid2)

    # ── Composite scores ──────────────────────────────────────────────────────
    sc1 = athletik_score(fms1, y1, spr1, spg1, agil1, aus1, spiro_row=spiro1)
    sc2 = athletik_score(fms2, y2, spr2, spg2, agil2, aus2, spiro_row=spiro2)
    sub1 = athletik_sub_scores(fms1, y1, spr1, spg1, agil1, aus1, spiro_row=spiro1)
    sub2 = athletik_sub_scores(fms2, y2, spr2, spg2, agil2, aus2, spiro_row=spiro2)

    # ── Score banner ──────────────────────────────────────────────────────────
    def _score_color(s: int) -> str:
        if s >= 75: return C["green"]
        if s >= 50: return C["yellow"]
        return C["red"]

    b1, _bm, b2 = st.columns([5, 1, 5])
    with b1:
        col = _score_color(sc1)
        st.markdown(
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-left:4px solid #1f6feb;border-radius:10px;padding:16px 20px;text-align:center">'
            f'<div style="font-size:12px;color:{C["muted"]};letter-spacing:1px">SPIELER A</div>'
            f'<div style="font-size:22px;font-weight:800;color:{C["text"]};margin:4px 0">{sp1["name"]}</div>'
            f'<div style="font-size:11px;color:{C["muted"]}">'
            f'{sp1.get("hauptposition") or sp1.get("position") or "—"} · '
            f'{sp1.get("mannschaft") or "—"}</div>'
            f'<div style="font-size:32px;font-weight:900;color:{col};margin-top:8px">{sc1}</div>'
            f'<div style="font-size:11px;color:{C["muted"]}">Athletik-Score / 100</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with _bm:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:center;'
            'height:100%;font-size:24px;color:#30363d;padding-top:30px">VS</div>',
            unsafe_allow_html=True,
        )
    with b2:
        col = _score_color(sc2)
        st.markdown(
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-left:4px solid #3fb950;border-radius:10px;padding:16px 20px;text-align:center">'
            f'<div style="font-size:12px;color:{C["muted"]};letter-spacing:1px">SPIELER B</div>'
            f'<div style="font-size:22px;font-weight:800;color:{C["text"]};margin:4px 0">{sp2["name"]}</div>'
            f'<div style="font-size:11px;color:{C["muted"]}">'
            f'{sp2.get("hauptposition") or sp2.get("position") or "—"} · '
            f'{sp2.get("mannschaft") or "—"}</div>'
            f'<div style="font-size:32px;font-weight:900;color:{col};margin-top:8px">{sc2}</div>'
            f'<div style="font-size:11px;color:{C["muted"]}">Athletik-Score / 100</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Radar chart ───────────────────────────────────────────────────────────
    _CAT_KEYS   = ["FMS", "Y-Balance", "Sprint", "Sprungkraft", "Agilitaet", "Ausdauer"]
    _CAT_LABELS = ["FMS", "Y-Balance", "Sprint", "Sprungkraft", "Agilität", "Ausdauer"]

    v1 = [sub1.get(k, 0) for k in _CAT_KEYS]
    v2 = [sub2.get(k, 0) for k in _CAT_KEYS]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=v1 + [v1[0]],
        theta=_CAT_LABELS + [_CAT_LABELS[0]],
        fill="toself",
        fillcolor="rgba(31,111,235,0.15)",
        line=dict(color="#1f6feb", width=2),
        name=sp1["name"],
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=v2 + [v2[0]],
        theta=_CAT_LABELS + [_CAT_LABELS[0]],
        fill="toself",
        fillcolor="rgba(63,185,80,0.15)",
        line=dict(color="#3fb950", width=2),
        name=sp2["name"],
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(size=9, color=C["muted"]),
                gridcolor=C["surface2"],
                linecolor=C["border"],
            ),
            angularaxis=dict(gridcolor=C["surface2"], linecolor=C["border"]),
            bgcolor=C["bg"],
        ),
        paper_bgcolor=C["bg"],
        font=dict(color=C["text"], family="Inter, Segoe UI, system-ui"),
        legend=dict(
            bgcolor=C["surface"],
            bordercolor=C["border"],
            borderwidth=1,
            orientation="h",
            x=0.5, xanchor="center",
            y=-0.08,
        ),
        margin=dict(l=40, r=40, t=60, b=60),
        title=dict(
            text="Athletisches Profil (normiert 0–100)",
            font=dict(size=15, color=C["text"]),
            x=0.5,
        ),
        height=460,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # ── Detailed comparison table ─────────────────────────────────────────────
    st.markdown("### 📊 Testwerte im Detail")

    # Helper: render a metric cell with traffic-light color
    def _cell(label: str, val, unit: str = "", color: str | None = None) -> str:
        if val is None:
            return (
                f'<div style="padding:8px 0">'
                f'<div style="font-size:11px;color:{C["muted"]}">{label}</div>'
                f'<div style="font-size:13px;color:{C["muted"]};font-style:italic">—</div>'
                f'</div>'
            )
        c = color or C["text"]
        return (
            f'<div style="padding:8px 0">'
            f'<div style="font-size:11px;color:{C["muted"]}">{label}</div>'
            f'<div style="font-size:16px;font-weight:700;color:{c}">{val}{unit}</div>'
            f'</div>'
        )

    def _bewertung_farbe(bew: str | None) -> str:
        if not bew:
            return C["muted"]
        if "Sehr gut" in bew or bew == "Gut":
            return C["green"]
        if "Mittel" in bew:
            return C["yellow"]
        if "Verbesserung" in bew:
            return C["red"]
        return C["muted"]

    def _missing_notice(name: str) -> str:
        return (
            f'<div style="padding:12px 16px;background:{C["surface"]};border-radius:8px;'
            f'border:1px solid {C["border"]};color:{C["muted"]};font-style:italic;font-size:13px">'
            f'ℹ️ {name} hat diesen Test noch nicht absolviert.</div>'
        )

    def _section_header(icon: str, title: str):
        st.markdown(
            f'<div style="margin:24px 0 8px;padding:10px 16px;background:{C["surface2"]};'
            f'border-radius:8px;border-left:3px solid {C["border"]}">'
            f'<span style="font-weight:700;color:{C["text"]}">{icon} {title}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    def _row_card(html1: str, html2: str):
        """Render two side-by-side data cards."""
        ca, cb = st.columns(2)
        ca.markdown(
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-top:3px solid #1f6feb;border-radius:10px;padding:14px 18px">{html1}</div>',
            unsafe_allow_html=True,
        )
        cb.markdown(
            f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
            f'border-top:3px solid #3fb950;border-radius:10px;padding:14px 18px">{html2}</div>',
            unsafe_allow_html=True,
        )

    # ── Column headers ────────────────────────────────────────────────────────
    ha, hb = st.columns(2)
    ha.markdown(
        f'<div style="text-align:center;font-size:12px;color:#1f6feb;font-weight:700;'
        f'letter-spacing:1px;padding:4px 0">🔵 {sp1["name"].upper()}</div>',
        unsafe_allow_html=True,
    )
    hb.markdown(
        f'<div style="text-align:center;font-size:12px;color:#3fb950;font-weight:700;'
        f'letter-spacing:1px;padding:4px 0">🟢 {sp2["name"].upper()}</div>',
        unsafe_allow_html=True,
    )

    # ── FMS ───────────────────────────────────────────────────────────────────
    _section_header("📝", "FMS — Functional Movement Screen")
    if fms1 or fms2:
        def _fms_html(row, name):
            if not row:
                return _missing_notice(name)
            sc  = row["score"]
            col = C["green"] if sc >= 17 else (C["yellow"] if sc >= 14 else C["red"])
            asym = row.get("asymmetrie") or "—"
            asym_col = C["red"] if "Asymmetrie" in str(asym) else C["green"]
            bew = row.get("bewertung") or "—"
            return (
                _cell("Gesamtscore", f"{sc}/21", color=col)
                + _cell("Bewertung", bew, color=_bewertung_farbe(bew))
                + _cell("Asymmetrie", asym, color=asym_col)
            )
        _row_card(_fms_html(fms1, sp1["name"]), _fms_html(fms2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat den FMS-Test absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Y-Balance ─────────────────────────────────────────────────────────────
    _section_header("📏", "Y-Balance Test")
    if y1 or y2:
        def _ybal_html(row, name):
            if not row:
                return _missing_notice(name)
            cr = row.get("composite_rechts") or 0
            cl = row.get("composite_links") or 0
            avg = (cr + cl) / 2
            col = C["green"] if avg >= 94 else (C["yellow"] if avg >= 89 else C["red"])
            asym = row.get("asymmetrie") or "—"
            asym_col = C["red"] if "Asymmetrie" in str(asym) else C["green"]
            return (
                _cell("Composite Rechts", f"{cr:.1f}", "%", col)
                + _cell("Composite Links", f"{cl:.1f}", "%", col)
                + _cell("Ø Composite", f"{avg:.1f}", "%", col)
                + _cell("Asymmetrie", asym, color=asym_col)
            )
        _row_card(_ybal_html(y1, sp1["name"]), _ybal_html(y2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat den Y-Balance-Test absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Sprint ────────────────────────────────────────────────────────────────
    _section_header("⚡", "Sprint-Diagnostik")
    if spr1 or spr2:
        def _spr_html(row, name):
            if not row:
                return _missing_notice(name)
            t10 = row.get("beste_10m")
            t30 = row.get("beste_30m")
            bew10 = row.get("bewertung_10m") or "—"
            bew30 = row.get("bewertung_30m") or "—"
            # Lower is better for sprint times
            def _t_col(t, gut, mittel):
                if t is None: return C["muted"]
                return C["green"] if t <= gut else (C["yellow"] if t <= mittel else C["red"])
            return (
                _cell("10-m Zeit", f"{t10:.2f}" if t10 else "—", " s",
                      _t_col(t10, 1.80, 1.95))
                + _cell("Bewertung 10 m", bew10, color=_bewertung_farbe(bew10))
                + _cell("30-m Zeit", f"{t30:.2f}" if t30 else "—", " s",
                        _t_col(t30, 4.00, 4.30))
                + _cell("Bewertung 30 m", bew30, color=_bewertung_farbe(bew30))
            )
        _row_card(_spr_html(spr1, sp1["name"]), _spr_html(spr2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat die Sprint-Diagnostik absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Sprung ────────────────────────────────────────────────────────────────
    _section_header("🦘", "Sprung-Diagnostik")
    if spg1 or spg2:
        def _spg_html(row, name):
            if not row:
                return _missing_notice(name)
            cmj  = row.get("cmj_beid")
            asym = row.get("cmj_asymmetrie")
            rsi  = row.get("rsi")
            sw   = row.get("standweit")
            bew  = row.get("bewertung_cmj") or "—"
            cmj_col = C["green"] if (cmj and cmj >= 40) else (C["yellow"] if (cmj and cmj >= 30) else C["red"])
            asym_col = (C["red"] if (asym and float(asym) > 10) else C["green"]) if asym is not None else C["muted"]
            return (
                _cell("CMJ beidbeinig", f"{cmj:.1f}" if cmj else "—", " cm", cmj_col)
                + _cell("Bewertung CMJ", bew, color=_bewertung_farbe(bew))
                + _cell("CMJ-Asymmetrie", f"{float(asym):.1f}" if asym is not None else "—", " %", asym_col)
                + _cell("RSI", f"{float(rsi):.2f}" if rsi else "—",
                        color=(C["green"] if rsi and float(rsi) >= 1.5 else C["yellow"]) if rsi else C["muted"])
                + _cell("Standweit", f"{sw:.2f}" if sw else "—", " m")
            )
        _row_card(_spg_html(spg1, sp1["name"]), _spg_html(spg2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat die Sprung-Diagnostik absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Agilität ──────────────────────────────────────────────────────────────
    _section_header("🔀", "Agilität")
    if agil1 or agil2:
        def _agil_html(row, name):
            if not row:
                return _missing_notice(name)
            t505r = row.get("t505_r")
            t505l = row.get("t505_l")
            asym  = row.get("asym_505")
            t_test = row.get("t_test")
            bew505 = row.get("bew_505") or "—"
            bew_t  = row.get("bew_t_test") or "—"
            asym_col = (C["red"] if asym and float(asym) > 10 else C["green"]) if asym is not None else C["muted"]
            return (
                _cell("505-Test rechts", f"{t505r:.2f}" if t505r else "—", " s")
                + _cell("505-Test links", f"{t505l:.2f}" if t505l else "—", " s")
                + _cell("Asymmetrie 505", f"{float(asym):.1f}" if asym is not None else "—", " %", asym_col)
                + _cell("T-Test", f"{t_test:.2f}" if t_test else "—", " s")
                + _cell("Bewertung T-Test", bew_t, color=_bewertung_farbe(bew_t))
            )
        _row_card(_agil_html(agil1, sp1["name"]), _agil_html(agil2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat den Agilitätstest absolviert.</div>',
            unsafe_allow_html=True,
        )

    # ── Ausdauer ──────────────────────────────────────────────────────────────
    _section_header("🫁", "Ausdauer")
    if aus1 or aus2:
        def _aus_html(row, name):
            if not row:
                return _missing_notice(name)
            dist = row.get("distanz_m")
            vo2  = row.get("vo2max")
            bew  = row.get("bewertung") or "—"
            dist_col = C["green"] if dist and dist >= 1600 else (C["yellow"] if dist and dist >= 800 else C["red"])
            vo2_col  = C["green"] if vo2 and float(vo2) >= 55 else (C["yellow"] if vo2 and float(vo2) >= 45 else C["red"])
            return (
                _cell("Distanz", f"{int(dist)}" if dist else "—", " m", dist_col)
                + _cell("VO₂max", f"{float(vo2):.1f}" if vo2 else "—", " ml/kg/min", vo2_col)
                + _cell("Bewertung", bew, color=_bewertung_farbe(bew))
            )
        _row_card(_aus_html(aus1, sp1["name"]), _aus_html(aus2, sp2["name"]))
    else:
        st.markdown(
            f'<div style="color:{C["muted"]};font-style:italic;padding:8px 4px">'
            f'Keiner der beiden Spieler hat den Ausdauertest absolviert.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Missing tests summary ─────────────────────────────────────────────────
    def _fehlende_tests(name, fms, y, spr, spg, agil, aus):
        fehlend = []
        if not fms:  fehlend.append("FMS")
        if not y:    fehlend.append("Y-Balance")
        if not spr:  fehlend.append("Sprint")
        if not spg:  fehlend.append("Sprung")
        if not agil: fehlend.append("Agilität")
        if not aus:  fehlend.append("Ausdauer")
        return fehlend

    f1 = _fehlende_tests(sp1["name"], fms1, y1, spr1, spg1, agil1, aus1)
    f2 = _fehlende_tests(sp2["name"], fms2, y2, spr2, spg2, agil2, aus2)

    if f1 or f2:
        st.markdown("#### ℹ️ Ausstehende Tests")
        nc1, nc2 = st.columns(2)
        with nc1:
            if f1:
                st.warning(
                    f"**{sp1['name']}** hat folgende Tests noch nicht absolviert: "
                    + ", ".join(f1)
                )
        with nc2:
            if f2:
                st.warning(
                    f"**{sp2['name']}** hat folgende Tests noch nicht absolviert: "
                    + ", ".join(f2)
                )

    # ── PDF-Export ────────────────────────────────────────────────────────────
    st.markdown("---")
    _ex_col, _ = st.columns([3, 7])
    with _ex_col:
        @st.cache_data(show_spinner=False, ttl=300)
        def _vergleich_pdf_cached(pid1, pid2, sc1, sc2):
            return generate_vergleich_pdf(
                sp1=sp1, sp2=sp2, sc1=sc1, sc2=sc2,
                fms1=fms1, fms2=fms2,
                y1=y1, y2=y2,
                spr1=spr1, spr2=spr2,
                spg1=spg1, spg2=spg2,
                agil1=agil1, agil2=agil2,
                aus1=aus1, aus2=aus2,
            )
        pdf_bytes = _vergleich_pdf_cached(pid1, pid2, sc1, sc2)
        filename = f"vergleich_{sp1['name'].replace(' ', '_')}_{sp2['name'].replace(' ', '_')}.pdf"
        st.download_button(
            label="📄 Vergleich als PDF exportieren",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
            key="vergl_pdf_dl",
        )

    # ── Entwicklungsverlauf ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📈 Entwicklungsverlauf")
    st.markdown(
        '<p style="color:#8b949e;margin-top:-8px">'
        'Athletik-Score und Einzelmodule beider Spieler im Zeitverlauf.</p>',
        unsafe_allow_html=True,
    )

    from datetime import timedelta as _tdd
    _tf_col, _ = st.columns([2, 5])
    zeitraum = _tf_col.selectbox(
        "Zeitraum",
        ["Letzte 3 Monate", "Letzte 6 Monate", "Letzte 12 Monate", "Alles"],
        index=1,
        key="vergl_zeitraum",
    )
    _today = date.today()
    if zeitraum == "Letzte 3 Monate":
        cutoff = str(_today - _tdd(days=90))
    elif zeitraum == "Letzte 6 Monate":
        cutoff = str(_today - _tdd(days=182))
    elif zeitraum == "Letzte 12 Monate":
        cutoff = str(_today - _tdd(days=365))
    else:
        cutoff = "0000-00-00"

    def _filter(rows): return [r for r in rows if (r.get("datum") or "") >= cutoff]

    h_fms1   = _filter(fms_history(pid1));          h_fms2   = _filter(fms_history(pid2))
    h_y1     = _filter(y_balance_history(pid1));    h_y2     = _filter(y_balance_history(pid2))
    h_spr1   = _filter(sprint_history(pid1));       h_spr2   = _filter(sprint_history(pid2))
    h_spg1   = _filter(sprung_history(pid1));       h_spg2   = _filter(sprung_history(pid2))
    h_agil1  = _filter(agilitaet_history(pid1));    h_agil2  = _filter(agilitaet_history(pid2))
    h_aus1   = _filter(ausdauer_history(pid1));     h_aus2   = _filter(ausdauer_history(pid2))
    h_spiro1 = _filter(spiro_test_alle(pid1));      h_spiro2 = _filter(spiro_test_alle(pid2))

    def _score_timeline(fh, yh, sprh, spgh, agilh, aush, spiroh):
        """Berechnet Athletik-Score für jeden Testtermin (kumulativer Zustand)."""
        state = {
            "fms": None, "y": None, "sprint": None, "sprung": None,
            "agil": None, "aus": None, "spiro": None,
        }
        events = (
            [(r["datum"], "fms",    r) for r in fh]
            + [(r["datum"], "y",      r) for r in yh]
            + [(r["datum"], "sprint", r) for r in sprh]
            + [(r["datum"], "sprung", r) for r in spgh]
            + [(r["datum"], "agil",   r) for r in agilh]
            + [(r["datum"], "aus",    r) for r in aush]
            + [(r["datum"], "spiro",  r) for r in spiroh if r.get("datum")]
        )
        events.sort(key=lambda x: x[0])
        out = []
        for datum, mod, row in events:
            state[mod] = row
            sc = athletik_score(state["fms"], state["y"], state["sprint"],
                                state["sprung"], state["agil"], state["aus"],
                                spiro_row=state["spiro"])
            if sc > 0:
                out.append((datum, sc))
        return out

    tl1 = _score_timeline(h_fms1, h_y1, h_spr1, h_spg1, h_agil1, h_aus1, h_spiro1)
    tl2 = _score_timeline(h_fms2, h_y2, h_spr2, h_spg2, h_agil2, h_aus2, h_spiro2)

    # ── Gesamtscore-Chart ─────────────────────────────────────────────────────
    if tl1 or tl2:
        fig_tl = go.Figure()
        if tl1:
            _d1, _s1 = zip(*tl1)
            fig_tl.add_trace(go.Scatter(
                x=list(_d1), y=list(_s1),
                mode="lines+markers", name=sp1["name"],
                line=dict(color="#1f6feb", width=2.5),
                marker=dict(size=7, color="#1f6feb"),
            ))
        if tl2:
            _d2, _s2 = zip(*tl2)
            fig_tl.add_trace(go.Scatter(
                x=list(_d2), y=list(_s2),
                mode="lines+markers", name=sp2["name"],
                line=dict(color="#3fb950", width=2.5),
                marker=dict(size=7, color="#3fb950"),
            ))
        fig_tl.update_layout(
            title=dict(text="Athletik-Gesamtscore (0–100)",
                       font=dict(size=14, color=C["text"]), x=0.0),
            xaxis=dict(gridcolor=C["surface2"], linecolor=C["border"],
                       tickfont=dict(color=C["muted"])),
            yaxis=dict(title="Score", range=[0, 100], gridcolor=C["surface2"],
                       linecolor=C["border"], tickfont=dict(color=C["muted"])),
            paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            font=dict(color=C["text"], family="Inter, Segoe UI, system-ui"),
            legend=dict(bgcolor=C["surface"], bordercolor=C["border"], borderwidth=1,
                        orientation="h", x=0.5, xanchor="center", y=-0.18),
            margin=dict(l=40, r=20, t=50, b=70),
            height=320,
        )
        st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info(f"Noch keine Testdaten im Zeitraum «{zeitraum}» vorhanden.")

    # ── Einzelmodul-Charts (Expander) ─────────────────────────────────────────
    def _modul_chart(title: str, rows1: list, rows2: list,
                     field: str, label: str, unit: str = "",
                     invert: bool = False, ymin=None, ymax=None):
        """Hilfsfunktion: Liniendiagramm eines Rohwerts für beide Spieler."""
        pts1 = [(r["datum"], float(r[field])) for r in rows1 if r.get(field)]
        pts2 = [(r["datum"], float(r[field])) for r in rows2 if r.get(field)]
        if not pts1 and not pts2:
            return
        fig = go.Figure()
        if pts1:
            _x1, _y1 = zip(*pts1)
            fig.add_trace(go.Scatter(
                x=list(_x1), y=list(_y1),
                mode="lines+markers", name=sp1["name"],
                line=dict(color="#1f6feb", width=2),
                marker=dict(size=6),
            ))
        if pts2:
            _x2, _y2 = zip(*pts2)
            fig.add_trace(go.Scatter(
                x=list(_x2), y=list(_y2),
                mode="lines+markers", name=sp2["name"],
                line=dict(color="#3fb950", width=2),
                marker=dict(size=6),
            ))
        note = " (niedriger = besser)" if invert else ""
        fig.update_layout(
            title=dict(text=f"{title}{note}", font=dict(size=13, color=C["text"]), x=0.0),
            xaxis=dict(gridcolor=C["surface2"], linecolor=C["border"],
                       tickfont=dict(color=C["muted"], size=9)),
            yaxis=dict(title=f"{label}{unit}", autorange="reversed" if invert else True,
                       gridcolor=C["surface2"], linecolor=C["border"],
                       tickfont=dict(color=C["muted"], size=9),
                       range=[ymin, ymax] if ymin is not None else None),
            paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            font=dict(color=C["text"], family="Inter, Segoe UI, system-ui"),
            legend=dict(bgcolor=C["surface"], bordercolor=C["border"], borderwidth=1,
                        orientation="h", x=0.5, xanchor="center", y=-0.22, font=dict(size=10)),
            margin=dict(l=40, r=10, t=40, b=60),
            height=260,
        )
        return fig

    any_module_data = any([h_fms1, h_fms2, h_y1, h_y2, h_spr1, h_spr2,
                           h_spg1, h_spg2, h_agil1, h_agil2, h_aus1, h_aus2])
    if any_module_data:
        with st.expander("📊 Einzelmodule im Detail anzeigen"):
            # Row 1: FMS + Y-Balance
            mc1, mc2 = st.columns(2)
            with mc1:
                fig = _modul_chart("FMS-Score", h_fms1, h_fms2,
                                   "score", "Punkte", "/21", ymin=0, ymax=21)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_fms1 or h_fms2: st.caption("FMS — kein Wert im Zeitraum.")
            with mc2:
                # Y-Balance: compute average composite per row
                def _yb_avg(rows):
                    out = []
                    for r in rows:
                        cr = r.get("composite_rechts") or 0
                        cl = r.get("composite_links") or 0
                        if cr or cl:
                            out.append({"datum": r["datum"], "_avg": (cr + cl) / 2})
                    return out
                h_y1a = _yb_avg(h_y1); h_y2a = _yb_avg(h_y2)
                fig = _modul_chart("Y-Balance Ø Composite", h_y1a, h_y2a,
                                   "_avg", "%", ymin=70, ymax=110)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_y1 or h_y2: st.caption("Y-Balance — kein Wert im Zeitraum.")

            # Row 2: Sprint + Sprung
            mc3, mc4 = st.columns(2)
            with mc3:
                fig = _modul_chart("Sprint 10 m", h_spr1, h_spr2,
                                   "beste_10m", "Zeit", " s", invert=True)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_spr1 or h_spr2: st.caption("Sprint — kein 10-m-Wert im Zeitraum.")
            with mc4:
                fig = _modul_chart("CMJ beidbeinig", h_spg1, h_spg2,
                                   "cmj_beid", "Höhe", " cm", ymin=0)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_spg1 or h_spg2: st.caption("Sprung — kein CMJ-Wert im Zeitraum.")

            # Row 3: Agilität + Ausdauer
            mc5, mc6 = st.columns(2)
            with mc5:
                # Prefer t_test, fall back to t505_r
                def _agil_rows(rows):
                    out = []
                    for r in rows:
                        v = r.get("t_test") or r.get("t505_r")
                        if v:
                            out.append({"datum": r["datum"], "_agil": float(v)})
                    return out
                h_ag1f = _agil_rows(h_agil1); h_ag2f = _agil_rows(h_agil2)
                fig = _modul_chart("Agilität (T-Test / 505)", h_ag1f, h_ag2f,
                                   "_agil", "Zeit", " s", invert=True)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_agil1 or h_agil2: st.caption("Agilität — kein Wert im Zeitraum.")
            with mc6:
                fig = _modul_chart("Yo-Yo Distanz", h_aus1, h_aus2,
                                   "distanz_m", "Distanz", " m", ymin=0)
                if fig: st.plotly_chart(fig, use_container_width=True)
                elif h_aus1 or h_aus2: st.caption("Ausdauer — kein Wert im Zeitraum.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DIAGNOSTIK ÜBERSICHT (Kachel-Grid)
# ══════════════════════════════════════════════════════════════════════════════

def page_diagnostik_overview() -> None:
    """Diagnostik-Startscreen: Kachelübersicht aller 6 Testmodule."""
    st.markdown(
        section_header("🔬 Diagnostik", "Testübersicht — wähle ein Modul und starte direkt"),
        unsafe_allow_html=True,
    )

    _inline_spielerwechsel("diagnostik")

    sid = st.session_state.get("global_player_id")
    if not sid:
        st.markdown(
            empty_state("👤", "Kein Spieler ausgewählt",
                        "Bitte einen Spieler suchen und auswählen."),
            unsafe_allow_html=True,
        )
        return

    # ── Last results ──────────────────────────────────────────────────────────
    sp_ov    = spieler_by_id(sid)
    _alter_ov   = berechne_alter(sp_ov.get("geburtsdatum")) if sp_ov else None
    _geschl_ov  = (sp_ov.get("geschlecht") or "Männlich") if sp_ov else "Männlich"
    anthro_d = anthropometrie_letzter(sid)
    fms_d    = fms_letzter(sid)
    yb_d     = y_balance_letzter(sid)
    spr_d    = sprint_letzter(sid)
    sprg_d   = sprung_letzter(sid)
    agil_d   = agilitaet_letzter(sid)
    aus_d    = ausdauer_letzter(sid)
    kraft_d  = kraft_letzter(sid)
    spiro_d  = spiro_test_letzter(sid)

    def _rating_color(rating: str | None) -> str:
        if not rating:
            return C["muted"]
        r = rating.lower()
        if any(x in r for x in ["sehr gut", "gut", "ausgezeichnet", "unauffällig",
                                  "keine asym", "keine auffäl", "optimal", "symmetrisch", "kein akuter"]):
            return C["green"]
        if any(x in r for x in ["beobachten", "mittel", "grenzwertig", "gering", "durchschnitt"]):
            return C["yellow"]
        if any(x in r for x in ["aktionsbedarf", "handlungsbedarf", "verbesserung",
                                  "risiko", "mangelhaft", "schlecht", "asymmetrie",
                                  "auffällig", "hoch", "schwäche", "kritisch", "unterdurchschnitt"]):
            return C["red"]
        return C["muted"]

    def _fmt_date(d: str | None) -> str:
        if not d:
            return "Noch kein Test"
        _pd = parse_datum_safe(d)
        return _pd.strftime("%d.%m.%Y") if _pd else str(d)

    # ── Key metric per test ───────────────────────────────────────────────────
    def _yb_metric():
        if not yb_d:
            return None, None
        cr = yb_d.get("composite_rechts")
        cl = yb_d.get("composite_links")
        if cr and cl:
            return f"R {cr:.0f} % / L {cl:.0f} %", yb_d.get("asymmetrie")
        return None, None

    def _agil_metric():
        if not agil_d:
            return None, None
        if agil_d.get("t_test"):
            return f"T-Test: {agil_d['t_test']:.2f} s", agil_d.get("bew_t_test")
        if agil_d.get("illinois"):
            return f"Illinois: {agil_d['illinois']:.2f} s", agil_d.get("bew_illinois")
        if agil_d.get("t505_r"):
            return f"505: R {agil_d['t505_r']:.2f} s", agil_d.get("bew_505")
        return None, None

    def _anthro_metric_rating():
        if not anthro_d:
            return None, None
        bmi  = anthro_d.get("bmi")
        kf   = anthro_d.get("koerperfett")
        kat  = (anthro_d.get("bmi_kategorie") or "").strip()
        # Metric string
        parts = []
        if bmi:
            parts.append(f"BMI {bmi:.1f}")
        if kf:
            parts.append(f"KF {kf:.0f} %")
        metric = " · ".join(parts) if parts else None
        # Rating string — keywords must match _rating_color() logic
        kat_l = kat.lower()
        if "normalgewicht" in kat_l:
            rating = f"Unauffällig — {kat}"
        elif "untergewicht" in kat_l:
            rating = f"Beobachten — {kat}"
        elif "übergewicht" in kat_l or "ubergewicht" in kat_l:
            rating = f"Handlungsbedarf — {kat}"
        elif "adipositas" in kat_l:
            rating = f"Aktionsbedarf — {kat}"
        elif kat:
            rating = kat
        else:
            rating = None
        return metric, rating

    yb_metric, yb_rating     = _yb_metric()
    agil_metric, agil_rating = _agil_metric()
    def _spiro_beurteilung(spiro):
        if not spiro:
            return None
        from spiro import spiro_bewertung_v2 as _spiro_bewertung_v2
        _sp_alter = alter_am_datum(
            sp_ov.get("geburtsdatum", "") if sp_ov else "", spiro.get("datum", "")
        ) or _alter_ov
        return _spiro_bewertung_v2(
            spiro,
            alter_testtag=_sp_alter,
            geschlecht=_geschl_ov,
            stufen=spiro_stufen_laden(spiro["id"]),
        )["text"]

    anthro_metric, anthro_rating = _anthro_metric_rating()

    # Sprint-Karte: beste verfügbare Distanz anzeigen (30m > 20m > 10m > 40m > 5m)
    # 0-Werte = nicht gemessen, zählen nicht als Sprintdaten
    _spr_metric = None
    _spr_rating = None
    if spr_d:
        for _sdist, _slbl in [
            ("beste_30m", "30 m"), ("beste_20m", "20 m"), ("beste_10m", "10 m"),
            ("beste_40m", "40 m"), ("beste_5m",  " 5 m"),
        ]:
            _sv = spr_d.get(_sdist) or 0
            if _sv > 0:
                _spr_metric = f"{_slbl}: {_sv:.2f} s"
                break
        for _rk in ("bewertung_30m", "bewertung_10m"):
            _rv = str(spr_d.get(_rk) or "")
            if _rv and _rv != "—":
                _spr_rating = _rv
                break

    tiles = [
        {
            "icon": "📐", "name": "Anthropometrie",
            "desc": "Körpermessung & Körperzusammensetzung",
            "sub":  "📐 Anthropometrie",
            "metric": anthro_metric,
            "rating": anthro_rating,
            "date":   anthro_d.get("datum") if anthro_d else None,
        },
        {
            "icon": "📝", "name": "FMS",
            "desc": "Functional Movement Screen",
            "sub":  "📝 FMS",
            "metric": f"{fms_d['score']}/21" if fms_d else None,
            "rating": (
                fms_d.get("bewertung","") + " — " +
                __import__("fms").fms_bewertung_kurz(fms_d.get("score"))[:60] + "…"
                if fms_d else None
            ),
            "date":   fms_d.get("datum")     if fms_d else None,
        },
        {
            "icon": "📏", "name": "Y-Balance",
            "desc": "Dynamische Gleichgewichtskontrolle",
            "sub":  "📏 Y-Balance",
            "metric": yb_metric,
            "rating": yb_rating,
            "date":   yb_d.get("datum") if yb_d else None,
        },
        {
            "icon": "⚡", "name": "Sprint",
            "desc": "Lineare Schnelligkeit",
            "sub":  "⚡ Sprint",
            "metric": _spr_metric,
            "rating": _spr_rating,
            "date":   spr_d.get("datum") if spr_d else None,
        },
        {
            "icon": "🦘", "name": "Sprung",
            "desc": "Sprungkraft & Reaktivkraft",
            "sub":  "🦘 Sprung",
            "metric": (f"CMJ: {sprg_d['cmj_beid']:.1f} cm"
                       if sprg_d and sprg_d.get("cmj_beid") else None),
            "rating": sprg_d.get("bewertung_cmj") if sprg_d else None,
            "date":   sprg_d.get("datum")         if sprg_d else None,
        },
        {
            "icon": "🔀", "name": "Agilität",
            "desc": "Richtungswechsel & Reaktion",
            "sub":  "🔀 Agilität",
            "metric": agil_metric,
            "rating": agil_rating,
            "date":   agil_d.get("datum") if agil_d else None,
        },
        {
            "icon": "🫁", "name": "Ausdauer",
            "desc": "Aerobe Kapazität (Yo-Yo)",
            "sub":  "🫁 Ausdauer",
            "metric": (f"VO₂max: {aus_d['vo2max']:.1f} ml·kg⁻¹·min⁻¹"
                       if aus_d and aus_d.get("vo2max") else None),
            "rating": aus_d.get("bewertung") if aus_d else None,
            "date":   aus_d.get("datum")     if aus_d else None,
        },
        {
            "icon": "💪", "name": "Kraftdiagnostik",
            "desc": "Bankdrücken 1RM & Rumpfkraft",
            "sub":  "💪 Kraft",
            "metric": (
                f"1RM: {kraft_d.get('direktes_1rm') or kraft_d.get('geschaetztes_1rm'):.1f} kg"
                if kraft_d and (kraft_d.get("direktes_1rm") or kraft_d.get("geschaetztes_1rm"))
                else ("Rumpf: %.0f s" % kraft_d["rumpf_gesamt_sekunden"]
                      if kraft_d and kraft_d.get("rumpf_gesamt_sekunden") else None)
            ),
            "rating": (
                __import__("kraft").beurteilung_relative_kraft(
                    kraft_d.get("relative_kraft_direkt") or kraft_d.get("relative_kraft_geschaetzt"),
                    alter=(alter_am_datum(sp_ov.get("geburtsdatum", "") if sp_ov else "",
                                         kraft_d.get("datum", "")) or _alter_ov),
                    geschlecht=_geschl_ov
                )[0]
                if kraft_d and (kraft_d.get("relative_kraft_direkt") or kraft_d.get("relative_kraft_geschaetzt"))
                else (
                    __import__("kraft").beurteilung_ventral_plank(kraft_d.get("ventral_sekunden"))[0]
                    if kraft_d and kraft_d.get("ventral_sekunden") else None
                )
            ),
            "date": kraft_d.get("datum") if kraft_d else None,
        },
        {
            "icon": "🔬", "name": "Stufentest",
            "desc": "Spiroergometrie / Laktatstufen",
            "sub":  "🫁 Ausdauer",  # öffnet Ausdauer-Seite (Selector wählt Spiro)
            "metric": (
                f"V max: {spiro_d['maximale_geschwindigkeit']:.1f} km/h"
                if spiro_d and spiro_d.get("maximale_geschwindigkeit") else
                (f"Schwelle: {spiro_d['schwelle_geschwindigkeit']:.1f} km/h"
                 if spiro_d and spiro_d.get("schwelle_geschwindigkeit") else None)
            ),
            "rating": _spiro_beurteilung(spiro_d),
            "date":   spiro_d.get("datum") if spiro_d else None,
        },
    ]

    # ── Render grid: 3 × 3 Kacheln (9 Module) ────────────────────────────────
    rows = [tiles[0:3], tiles[3:6], tiles[6:9]]
    for row_idx, row_tiles in enumerate(rows):
        cols = st.columns(3, gap="medium")
        for j, tile in enumerate(row_tiles):
            i = row_idx * 3 + j
            with cols[j]:
                has_data    = tile["metric"] is not None
                rc          = _rating_color(tile["rating"]) if has_data else C["border"]
                dot         = (
                    f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
                    f'background:{rc};margin-right:5px;vertical-align:middle"></span>'
                )
                metric_html = (
                    f'<div style="font-size:20px;font-weight:800;color:{C["text"]};'
                    f'margin:10px 0 2px;letter-spacing:-0.5px">{tile["metric"]}</div>'
                    if has_data else
                    f'<div style="font-size:12px;color:{C["muted"]};margin:10px 0 2px;'
                    f'font-style:italic">Noch keine Daten vorhanden</div>'
                )
                rating_html = (
                    f'<div style="font-size:11px;color:{rc};font-weight:600;margin-bottom:6px">'
                    f'{dot}{tile["rating"]}</div>'
                    if has_data and tile["rating"] else
                    f'<div style="font-size:11px;color:{C["muted"]};margin-bottom:6px">—</div>'
                )
                st.markdown(
                    f'<div style="background:{C["surface"]};border:1px solid {C["border"]};'
                    f'border-top:3px solid {rc};border-radius:12px;padding:16px 18px 10px;'
                    f'margin-bottom:2px;min-height:140px">'
                    f'<div style="display:flex;align-items:center;gap:9px">'
                    f'<span style="font-size:24px;line-height:1">{tile["icon"]}</span>'
                    f'<div>'
                    f'<div style="font-size:15px;font-weight:700;color:{C["text"]}">{tile["name"]}</div>'
                    f'<div style="font-size:10px;color:{C["muted"]};letter-spacing:0.5px">'
                    f'{tile["desc"].upper()}</div>'
                    f'</div></div>'
                    f'{metric_html}'
                    f'{rating_html}'
                    f'<div style="font-size:10px;color:{C["muted"]}">🗓 {_fmt_date(tile["date"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                btn_label = "Messen →" if tile["sub"] == "📐 Anthropometrie" else "Test starten →"
                if st.button(btn_label, key=f"tile_btn_{i}", use_container_width=True):
                    st.session_state["_nav_sub_diagnostik_goto"] = tile["sub"]
                    st.rerun()
        st.write("")


# ══════════════════════════════════════════════════════════════════════════════
# TESTPROTOKOLL DRUCKEN
# ══════════════════════════════════════════════════════════════════════════════

def page_testprotokoll():
    st.markdown(
        section_header("🖨️ Testprotokoll drucken",
                       "Leere Druckbogen fuer die papierbasierte Erfassung"),
        unsafe_allow_html=True,
    )

    alle_spieler = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])

    # ── Schritt 1: Variante ────────────────────────────────────────────────────
    st.markdown("### Schritt 1 — Variante")
    variante = st.radio(
        "Druckvariante",
        ["📄 Leeres Protokoll (ohne Spieler)", "👤 Protokoll mit Spieler(n)"],
        horizontal=True,
        label_visibility="collapsed",
        key="proto_variante",
    )
    leer = variante.startswith("📄")

    # ── Schritt 2: Tests auswählen ─────────────────────────────────────────────
    st.markdown("### Schritt 2 — Tests auswählen")

    # Schnellauswahl nach Bereich
    _BEREICH_FILTER = {
        "Alle Tests": list(TEST_REIHENFOLGE),
        "Beweglichkeit & Stabilität": ["fms", "y_balance"],
        "Schnelligkeit & Kraft":       ["sprint", "jump", "agility", "kraft"],
        "Ausdauer & Körper":           ["yoyo", "anthropometrie"],
    }
    bereich_wahl = st.selectbox(
        "Schnellauswahl nach Bereich",
        list(_BEREICH_FILTER.keys()),
        key="proto_bereich_filter",
        label_visibility="visible",
    )
    vorauswahl = _BEREICH_FILTER[bereich_wahl]

    col_all, col_none = st.columns([2, 8])
    if col_all.button("Alle auswählen", key="proto_all"):
        for tid in TEST_REIHENFOLGE:
            st.session_state[f"proto_test_{tid}"] = True
    if col_none.button("Alle abwählen", key="proto_none"):
        for tid in TEST_REIHENFOLGE:
            st.session_state[f"proto_test_{tid}"] = False

    cols = st.columns(4)
    selected_tests = []
    for i, tid in enumerate(TEST_REIHENFOLGE):
        default_val = tid in vorauswahl if bereich_wahl != "Alle Tests" else True
        checked = cols[i % 4].checkbox(
            TEST_NAMEN[tid],
            value=st.session_state.get(f"proto_test_{tid}", default_val),
            key=f"proto_test_{tid}",
        )
        if checked:
            selected_tests.append(tid)

    # ── Schritt 3: Kopfdaten vorausfüllen (optional) ───────────────────────────
    st.markdown("### Schritt 3 — Kopfdaten (optional)")
    st.caption("Diese Angaben werden in den Protokoll-Header gedruckt.")
    _h1, _h2, _h3 = st.columns(3)
    proto_datum    = _h1.text_input("Testdatum",    value="", placeholder="TT.MM.JJJJ", key="proto_datum")
    proto_trainer  = _h2.text_input("Trainer",      value=st.session_state.get("cfg_trainer_name", ""), placeholder="Name des Trainers", key="proto_trainer")
    proto_ort      = _h3.text_input("Testort",      value="", placeholder="z. B. Sportplatz", key="proto_ort")

    # Trainer-Name für spätere Sessions merken
    if proto_trainer:
        st.session_state["cfg_trainer_name"] = proto_trainer

    # ── Schritt 4: Spieler (nur bei "mit Spieler") ────────────────────────────
    selected_spieler = []
    if not leer:
        st.markdown("### Schritt 4 — Spieler auswählen")

        # Mannschaft-Filter
        mannschaften = sorted({p.get("mannschaft") or "Ohne Mannschaft" for p in alle_spieler}) if alle_spieler else []
        if mannschaften:
            mann_filter = st.selectbox(
                "Nach Mannschaft filtern",
                ["Alle Mannschaften"] + mannschaften,
                key="proto_mann_filter",
            )
            if mann_filter == "Alle Mannschaften":
                spieler_fuer_auswahl = alle_spieler
            else:
                spieler_fuer_auswahl = [
                    p for p in alle_spieler
                    if (p.get("mannschaft") or "Ohne Mannschaft") == mann_filter
                ]
        else:
            spieler_fuer_auswahl = alle_spieler

        if not spieler_fuer_auswahl:
            st.warning("Keine Spieler gefunden. Bitte zuerst Spieler anlegen.")
        else:
            opts = {p["name"]: p for p in spieler_fuer_auswahl}
            # Schnell: ganze Mannschaft auswählen
            if st.button("✅ Alle angezeigten Spieler auswählen", key="proto_all_sp"):
                st.session_state["proto_spieler_sel"] = list(opts.keys())
            auswahl = st.multiselect(
                "Spieler (Mehrfachauswahl möglich)",
                list(opts.keys()),
                key="proto_spieler_sel",
            )
            selected_spieler = [opts[n] for n in auswahl]

    # ── Vorschau ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Vorschau")
    if not selected_tests:
        st.warning("Bitte mindestens einen Test auswählen.")
        return

    n_spieler = max(len(selected_spieler), 1)
    info_cols = st.columns(4)
    info_cols[0].metric("Ausgewählte Tests", len(selected_tests))
    info_cols[1].metric("Spieler / Bögen", n_spieler)
    info_cols[2].metric("Geschätzte Seiten", f"ca. {n_spieler}–{n_spieler * 3}")
    info_cols[3].metric("Testdatum", proto_datum or "handschriftlich")

    st.markdown("**Tests:**  " + "  ·  ".join([f"`{TEST_NAMEN[t]}`" for t in selected_tests]))
    if not leer and selected_spieler:
        st.markdown("**Spieler:**  " + "  ·  ".join([f"`{p['name']}`" for p in selected_spieler]))
    if proto_trainer:
        st.markdown(f"**Trainer:**  `{proto_trainer}`")
    if proto_ort:
        st.markdown(f"**Ort:**  `{proto_ort}`")

    if leer:
        st.info("📄 Leeres Protokoll — Spielerdaten werden handschriftlich eingetragen.")
    elif not selected_spieler:
        st.warning("Bitte mindestens einen Spieler auswählen, oder zur Variante 'Leeres Protokoll' wechseln.")
        return

    # ── Druck-Tipps ───────────────────────────────────────────────────────────
    with st.expander("🖨️ Druck-Tipps", expanded=False):
        st.markdown(
            "- **Papierformat:** DIN A4, Hochformat\n"
            "- **Ränder:** min. 10 mm (Systemstandard)\n"
            "- **Druckskalierung:** 100 % (nicht 'Auf Seitengröße anpassen')\n"
            "- **Farbe:** Schwarz/Weiß reicht aus\n"
            "- **Empfehlung:** Nach dem Druck laminieren für Outdoor-Einsatz"
        )

    # ── PDF generieren ─────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("📥 Testprotokoll PDF erstellen", use_container_width=True,
                 type="primary", key="proto_gen"):
        with st.spinner("PDF wird erstellt …"):
            pdf_bytes = generate_testprotokoll(
                test_ids=selected_tests,
                spieler_liste=selected_spieler if not leer else None,
                variante="leer" if leer else "spieler",
                logo_bytes=logo_laden(),
            )
        dateiname = "testprotokoll_leer.pdf" if leer else "testprotokoll_spieler.pdf"
        st.download_button(
            label="⬇️ PDF herunterladen",
            data=pdf_bytes,
            file_name=dateiname,
            mime="application/pdf",
            use_container_width=True,
            key="proto_dl",
        )
        st.success(f"✅ PDF erstellt — {len(selected_tests)} Test(s), {n_spieler} Bogen/Bögen.")

    _custom_docs_section("protokolle", "Eigene Protokolle")


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION  (7-section structure)
# ══════════════════════════════════════════════════════════════════════════════

# ── Sub-page maps per section ─────────────────────────────────────────────────
def page_ueber_software():
    """Über — Info, Impressum, Datenschutz, AGB.

    Sub-Navigation via session_state key '_ueber_sub' ∈ {info|impressum|datenschutz|agb}.
    Kann auch von der Sidebar-Footer-Navigation gesetzt werden.
    """
    from modules.legal_page import page_impressum as _pg_impressum
    from modules.legal_page import page_datenschutz as _pg_datenschutz
    from modules.legal_page import page_agb as _pg_agb

    _sub = st.session_state.get("_ueber_sub", "info")

    # ── Seiteninhalt ───────────────────────────────────────────────────────────
    if _sub == "impressum":
        if st.button("← Zurück zu Info", key="legal_back_impressum"):
            st.session_state["_ueber_sub"] = "info"
            st.rerun()
        _pg_impressum()

    elif _sub == "datenschutz":
        if st.button("← Zurück zu Info", key="legal_back_datenschutz"):
            st.session_state["_ueber_sub"] = "info"
            st.rerun()
        _pg_datenschutz()

    elif _sub == "agb":
        if st.button("← Zurück zu Info", key="legal_back_agb"):
            st.session_state["_ueber_sub"] = "info"
            st.rerun()
        _pg_agb()

    else:
        # ── INFO ──────────────────────────────────────────────────────────────
        # Große APH-Produktgrafik (responsiv, zentriert, kein Overflow)
        _brand_overview_path = os.path.join(os.path.dirname(__file__), "assets", "aph_brand_overview.png")
        if os.path.exists(_brand_overview_path):
            st.markdown(
                '<div style="text-align:center;max-width:900px;margin:0 auto 8px auto;overflow:hidden">',
                unsafe_allow_html=True,
            )
            st.image(_brand_overview_path, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            f'<div translate="no" style="text-align:center;padding:8px 0 20px">'
            f'<h1 style="color:#e6edf3;font-size:22px;font-weight:800;'
            f'letter-spacing:0.5px;margin:8px 0 4px">{APP_NAME}</h1>'
            f'<div style="color:#c9a84c;font-size:11px;font-weight:600;'
            f'letter-spacing:2px;margin-bottom:4px">TESTS · ANALYSE · TRAINING</div>'
            f'<div style="color:#58a6ff;font-size:11px;font-weight:600;'
            f'letter-spacing:2px">VERSION {APP_VERSION}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Kurzbeschreibung
        st.markdown(
            '<div style="background:#161b22;border:1px solid #30363d;border-radius:10px;'
            'padding:16px 20px;margin-bottom:14px;color:#c9d1d9;font-size:14px;line-height:1.7">'
            'Athletic Performance Hub unterstützt Trainer und Vereine bei der strukturierten '
            'Leistungsdiagnostik, Trainingsplanung und langfristigen Entwicklung von '
            'Fußballspielern.'
            '</div>',
            unsafe_allow_html=True,
        )

        # Info-Karten
        _ci1, _ci2 = st.columns(2)
        with _ci1:
            st.markdown(
                f'<div translate="no" style="background:#161b22;border:1px solid #30363d;'
                f'border-radius:10px;padding:18px 20px;margin-bottom:12px">'
                f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;margin-bottom:8px">SOFTWARE</div>'
                f'<div style="color:#e6edf3;font-weight:700;font-size:14px;margin-bottom:4px">{APP_NAME}</div>'
                f'<div style="color:#8b949e;font-size:12px">Version {APP_VERSION}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with _ci2:
            st.markdown(
                f'<div translate="no" style="background:#161b22;border:1px solid #30363d;'
                f'border-radius:10px;padding:18px 20px;margin-bottom:12px">'
                f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;margin-bottom:8px">ENTWICKELT VON</div>'
                f'<div style="color:#e6edf3;font-weight:700;font-size:14px;margin-bottom:10px">{APP_DEVELOPER}</div>'
                f'<div style="font-size:10px;color:#8b949e;letter-spacing:1px;margin-bottom:4px">SUPPORT</div>'
                f'<a href="mailto:support@aphsystem.de" style="color:#58a6ff;font-size:13px;'
                f'text-decoration:none">support@aphsystem.de</a>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Fachlicher Hinweis
        st.markdown(
            '<div style="background:#161b22;border-left:4px solid #d29922;border-radius:6px;'
            'padding:14px 18px;color:#8b949e;font-size:13px;line-height:1.7;margin-bottom:16px">'
            '<strong style="color:#d29922">Hinweis</strong><br>'
            'Athletic Performance Hub dient der sportlichen Leistungsdiagnostik und '
            'Trainingsplanung. Die dargestellten Auswertungen, Auffälligkeiten und '
            'Trainingsempfehlungen stellen keine medizinische Diagnose dar und ersetzen '
            'keine ärztliche oder physiotherapeutische Untersuchung.'
            '</div>',
            unsafe_allow_html=True,
        )

        # Support-Button
        _mailto_support = (
            "mailto:support@aphsystem.de"
            "?subject=Athletic%20Performance%20Hub%20%E2%80%93%20Supportanfrage"
        )
        st.link_button(
            "📧 Support kontaktieren",
            _mailto_support,
            use_container_width=True,
        )

        # Rechtliche Links
        st.markdown(
            '<div style="margin-top:20px;padding-top:14px;border-top:1px solid #21262d;'
            'text-align:center;font-size:10px;color:#8b949e;margin-bottom:8px">Rechtliches</div>',
            unsafe_allow_html=True,
        )
        _rl1, _rl2, _rl3 = st.columns(3)
        if _rl1.button("📋 Impressum", key="info_goto_impressum", use_container_width=True):
            st.session_state["_ueber_sub"] = "impressum"
            st.rerun()
        if _rl2.button("🔒 Datenschutz", key="info_goto_datenschutz", use_container_width=True):
            st.session_state["_ueber_sub"] = "datenschutz"
            st.rerun()
        if _rl3.button("📄 AGB", key="info_goto_agb", use_container_width=True):
            st.session_state["_ueber_sub"] = "agb"
            st.rerun()

        st.markdown("---")
        st.caption(APP_COPYRIGHT)


_SUB_SPIELER = {
    "👥 Verwaltung":          page_spieler,
    "🏃 Profil & Diagnostik": page_spieler_profil,
}
_SUB_DIAGNOSTIK = {
    "🏠 Übersicht":           page_diagnostik_overview,
    "📐 Anthropometrie":      page_anthropometrie,
    "📝 FMS":                 page_fms,
    "📏 Y-Balance":           page_ybalance,
    "⚡ Sprint":               page_sprint,
    "🦘 Sprung":               page_sprung,
    "🔀 Agilität":            page_agilitaet,
    "🫁 Ausdauer":            page_ausdauer,
    "💪 Kraft":                page_kraft,
}
_SUB_TRAINING = {
    "📅 Trainingsplan":     page_trainingsplan,
    "🔄 Periodisierung":    page_periodisierung,
}

_MAIN_SECTIONS = [
    "🏠  Startseite",
    "👤  Spieler",
    "🔬  Diagnostik",
    "📅  Training",
    "📈  Entwicklung",
    "⚖️  Vergleich",
    "👥  Mannschaft",
    "📄  Dokumente",
    "⚙️  Einstellungen",
    "👤  Mein Profil",
    "ℹ️  Über",
]
# Rollen-basierte Admin-Sektionen
_user_rolle_nav = st.session_state.get("user", {}).get("rolle", "Trainer")
if _user_rolle_nav in ("Superadmin", "Vereinsadmin"):
    _MAIN_SECTIONS = _MAIN_SECTIONS + ["🧑‍💼  Trainerportal", "🔑  Benutzerverwaltung"]
if _user_rolle_nav in ("Trainer", "Vereinsadmin"):
    _MAIN_SECTIONS = _MAIN_SECTIONS + ["📋  Mein Vertrag"]
if _user_rolle_nav == "Vereinsadmin":
    _MAIN_SECTIONS = _MAIN_SECTIONS + ["💳  Lizenz"]
if _user_rolle_nav == "Superadmin":
    _MAIN_SECTIONS = _MAIN_SECTIONS + ["🏢  Vereinsverwaltung", "💳  Lizenzverwaltung", "👥  Kundenverwaltung"]

with st.sidebar:
    # ── Logo ──────────────────────────────────────────────────────────────────
    _sb_aph_logo = os.path.join(os.path.dirname(__file__), "assets", "aph_logo.png")
    if os.path.exists(_sb_aph_logo):
        _sbl1, _sbl2, _sbl3 = st.columns([1, 3, 1])
        with _sbl2:
            st.image(_sb_aph_logo, use_container_width=True)
    st.markdown(
        f'<div style="padding:6px 0 8px;text-align:center">'
        f'<div style="font-weight:800;font-size:13px;color:{C["text"]};letter-spacing:0.5px;margin-top:4px">ATHLETIC PERFORMANCE HUB</div>'
        f'<div style="font-weight:600;font-size:10px;color:#c9a84c;letter-spacing:1.5px;margin-top:2px">TESTS · ANALYSE · TRAINING</div>'
        f'<div style="font-size:9px;color:{C["muted"]};margin-top:2px">v{APP_VERSION}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Global player search ──────────────────────────────────────────────────
    alle_spieler = spieler_laden(_akt_user()["id"], _akt_user()["rolle"], _akt_user()["verein_id"])
    if alle_spieler:
        _ids = [p["id"] for p in alle_spieler]
        if st.session_state.get("global_player_id") not in _ids:
            st.session_state["global_player_id"] = alle_spieler[0]["id"]
        st.markdown(
            '<div style="font-size:11px;font-weight:700;color:#8b949e;'
            'letter-spacing:.5px;margin:4px 0 5px">AKTIVER SPIELER</div>',
            unsafe_allow_html=True,
        )
        _aktiven_spieler_suchbereich(alle_spieler, "sidebar", titel="Spieler suchen …")
        sel_player = next(
            (p for p in alle_spieler if p["id"] == st.session_state.get("global_player_id")),
            alle_spieler[0],
        )

        # ── Kompakte Pill (immer sichtbar) ───────────────────────────────────
        _sb_pos  = sel_player.get("hauptposition") or sel_player.get("position") or "—"
        _sb_team = sel_player.get("mannschaft") or "—"
        st.markdown(
            f'<div class="player-pill">'
            f'<div class="player-pill-sub">{_sb_pos} · {_sb_team}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Vollständiges Spielerprofil (Expander) ───────────────────────────
        _sb_pid = sel_player["id"]
        with st.expander("📋 Spielerprofil", expanded=False):
            # Stammdaten
            _sb_alter = berechne_alter(sel_player.get("geburtsdatum"))
            _sb_geb   = sel_player.get("geburtsdatum") or "—"
            _sb_rows_stamm = [
                ("Alter",          f"{_sb_alter} Jahre ({_sb_geb})" if _sb_alter else _sb_geb),
                ("Geschlecht",     sel_player.get("geschlecht") or "—"),
                ("Altersklasse",   sel_player.get("altersklasse") or "—"),
                ("Nebenposition",  sel_player.get("nebenposition") or "—"),
                ("Spielbein",      sel_player.get("spielbein") or "—"),
                ("Leistungsniveau",sel_player.get("leistungsniveau") or "—"),
                ("Status",         sel_player.get("trainingsstatus") or "—"),
            ]
            st.markdown(
                "<div style='font-size:10px;font-weight:700;color:#58a6ff;"
                "letter-spacing:1px;margin:4px 0 4px'>👤 STAMMDATEN</div>",
                unsafe_allow_html=True,
            )
            for _lbl, _val in _sb_rows_stamm:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"font-size:11px;padding:2px 0;border-bottom:1px solid #21262d'>"
                    f"<span style='color:#8b949e'>{_lbl}</span>"
                    f"<span style='color:#e6edf3;text-align:right;max-width:60%'>{_val}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Anthropometrie
            _sb_anthro = anthropometrie_letzter(_sb_pid)
            st.markdown(
                "<div style='font-size:10px;font-weight:700;color:#58a6ff;"
                "letter-spacing:1px;margin:10px 0 4px'>📏 ANTHROPOMETRIE</div>",
                unsafe_allow_html=True,
            )
            if _sb_anthro:
                _sb_rows_anthro = [
                    ("Datum",         _sb_anthro.get("datum") or "—"),
                    ("Größe",         f"{_sb_anthro.get('groesse')} cm" if _sb_anthro.get("groesse") else "—"),
                    ("Gewicht",       f"{_sb_anthro.get('gewicht')} kg" if _sb_anthro.get("gewicht") else "—"),
                    ("BMI",           f"{_sb_anthro.get('bmi'):.1f} ({_sb_anthro.get('bmi_kategorie') or '—'})" if _sb_anthro.get("bmi") else "—"),
                    ("Körperfett",    f"{_sb_anthro.get('koerperfett'):.1f} %" if _sb_anthro.get("koerperfett") else "—"),
                    ("Muskelmasse",   f"{_sb_anthro.get('muskelmasse'):.1f} kg" if _sb_anthro.get("muskelmasse") else "—"),
                    ("Sitzhöhe",      f"{_sb_anthro.get('sitzhoehe')} cm" if _sb_anthro.get("sitzhoehe") else "—"),
                    ("Beinlänge",     f"{_sb_anthro.get('beinlaenge')} cm" if _sb_anthro.get("beinlaenge") else "—"),
                    ("Armspannweite", f"{_sb_anthro.get('armspannweite')} cm" if _sb_anthro.get("armspannweite") else "—"),
                    ("PHV-Offset",    f"{_sb_anthro.get('phv_offset'):+.2f}" if _sb_anthro.get("phv_offset") is not None else "—"),
                    ("Reifestatus",   _sb_anthro.get("reifestatus") or "—"),
                    ("KF-Methode",    _sb_anthro.get("koerperfett_methode") or "—"),
                ]
                for _lbl, _val in _sb_rows_anthro:
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;"
                        f"font-size:11px;padding:2px 0;border-bottom:1px solid #21262d'>"
                        f"<span style='color:#8b949e'>{_lbl}</span>"
                        f"<span style='color:#e6edf3;text-align:right;max-width:60%'>{_val}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Noch keine Anthropometrie-Daten.")

            # Letzte Testergebnisse
            st.markdown(
                "<div style='font-size:10px;font-weight:700;color:#58a6ff;"
                "letter-spacing:1px;margin:10px 0 4px'>🔬 LETZTE TESTS</div>",
                unsafe_allow_html=True,
            )
            _sb_tests = [
                ("FMS",       fms_letzter(_sb_pid),       lambda r: f"Score {r.get('score')} ({r.get('datum','')})"),
                ("Y-Balance", y_balance_letzter(_sb_pid), lambda r: f"R {r.get('composite_rechts','—')} / L {r.get('composite_links','—')} ({r.get('datum','')})"),
                ("Sprint",    sprint_letzter(_sb_pid),    lambda r: f"10m {r.get('beste_10m','—')}s / 30m {r.get('beste_30m','—')}s ({r.get('datum','')})"),
                ("Sprung",    sprung_letzter(_sb_pid),    lambda r: f"CMJ {r.get('cmj_beid','—')} cm ({r.get('datum','')})"),
                ("Agilität",  agilitaet_letzter(_sb_pid), lambda r: f"T-Test {r.get('t_test','—')}s ({r.get('datum','')})"),
                ("Ausdauer",  ausdauer_letzter(_sb_pid),  lambda r: f"VO₂max {r.get('vo2max','—')} ({r.get('datum','')})"),
                ("Kraft",     kraft_letzter(_sb_pid),     lambda r: f"1RM {r.get('direktes_1rm','—')} kg ({r.get('datum','')})"),
            ]
            _sb_has_test = False
            for _tname, _trow, _tfmt in _sb_tests:
                if _trow:
                    _sb_has_test = True
                    try:
                        _tval = _tfmt(_trow)
                    except Exception:
                        _tval = _trow.get("datum") or "—"
                    st.markdown(
                        f"<div style='font-size:11px;padding:3px 0;border-bottom:1px solid #21262d'>"
                        f"<span style='color:#8b949e;font-weight:600'>{_tname}: </span>"
                        f"<span style='color:#e6edf3'>{_tval}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            if not _sb_has_test:
                st.caption("Noch keine Testdaten vorhanden.")

            # ── Zuweisung-Verlauf (nur Superadmin-Sicht) ─────────────────────
            if _akt_user()["rolle"] == "Superadmin":
                _sb_log = zuweisung_log_laden(_sb_pid)
                st.markdown(
                    "<div style='font-size:10px;font-weight:700;color:#58a6ff;"
                    "letter-spacing:1px;margin:10px 0 4px'>🔗 ZUWEISUNG-VERLAUF</div>",
                    unsafe_allow_html=True,
                )
                if _sb_log:
                    for _le in _sb_log:
                        _le_ts   = (_le.get("zeitstempel") or "")[:16].replace("T", " ")
                        _le_by   = _le.get("ausfuehrender_name") or "—"
                        _le_atr  = _le.get("alt_trainer_name") or "—"
                        _le_ntr  = _le.get("neu_trainer_name") or "—"
                        _le_avi  = _le.get("alt_verein_name") or "—"
                        _le_nvi  = _le.get("neu_verein_name") or "—"
                        _le_txt  = []
                        if _le.get("alt_trainer_id") != _le.get("neu_trainer_id"):
                            _le_txt.append(f"Trainer: {_le_atr} → {_le_ntr}")
                        if _le.get("alt_verein_id") != _le.get("neu_verein_id"):
                            _le_txt.append(f"Verein: {_le_avi} → {_le_nvi}")
                        _le_change = " · ".join(_le_txt) if _le_txt else "Keine Änderung"
                        st.markdown(
                            f"<div style='font-size:10px;padding:3px 0;"
                            f"border-bottom:1px solid #21262d;color:#e6edf3'>"
                            f"<span style='color:#8b949e'>{_le_ts}</span>"
                            f"<span style='color:#58a6ff;margin:0 4px'>·</span>"
                            f"<span>{_le_change}</span>"
                            f"<span style='color:#8b949e;font-size:9px;float:right'>"
                            f"von {_le_by}</span></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("Noch keine Zuweisungsänderungen protokolliert.")
    else:
        st.markdown(
            f'<div style="padding:8px 0;color:{C["muted"]};font-size:12px">Kein Spieler angelegt.</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f'<hr style="border-color:{C["surface2"]};margin:10px 0">', unsafe_allow_html=True)

    # ── Benachrichtigungen (nur für Trainer-Rolle) ────────────────────────────
    _nb_user = _akt_user()
    if _nb_user.get("rolle") == "Trainer" and _nb_user.get("id"):
        _nb_ungelesen = benachrichtigungen_laden(_nb_user["id"], nur_ungelesen=True)
        if _nb_ungelesen:
            _nb_count = len(_nb_ungelesen)
            with st.expander(f"🔔 Benachrichtigungen ({_nb_count} neu)", expanded=True):
                for _nb in _nb_ungelesen:
                    _nb_ts = (_nb.get("erstellt_am") or "")[:16].replace("T", " ")
                    # Markdown-Fettdruck in den Text einbetten
                    _nb_txt = _nb.get("text") or ""
                    st.markdown(
                        f"<div style='font-size:11px;padding:6px 0;"
                        f"border-bottom:1px solid #21262d;color:#e6edf3'>"
                        f"{_nb_txt}"
                        f"<br><span style='color:#8b949e;font-size:9px'>{_nb_ts}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                if st.button("✅ Alle als gelesen markieren",
                             key="nb_alle_gelesen", use_container_width=True):
                    benachrichtigungen_alle_gelesen(_nb_user["id"])
                    st.rerun()

    # ── ?kd= Query-Param: Direkt-Link zu Kundendetail (nach Browser-Reload) ─────
    # Wenn ein Superadmin auf eine Kundenkarte klickt (<a href="?kd=VID_BID">),
    # entsteht ein vollständiger Browser-Reload. Die Streamlit-Session geht dabei
    # verloren — nav_section würde auf den Default (Startseite) fallen.
    # Deshalb: kd= hier appweit lesen, kunden_auswahl + _nav_goto setzen.
    _qp_kd_app = st.query_params.get("kd", "")
    if _qp_kd_app and not st.session_state.get("kunden_auswahl"):
        try:
            _kd_parts_app = str(_qp_kd_app).split("_", 1)
            if len(_kd_parts_app) == 2:
                _vid_app = int(_kd_parts_app[0]) or None
                _bid_app = int(_kd_parts_app[1]) or None
                if _vid_app is not None or _bid_app is not None:
                    st.session_state["kunden_auswahl"] = (_vid_app, _bid_app)
                    st.session_state["_nav_goto"] = "👥  Kundenverwaltung"
                    st.query_params.clear()
                    st.rerun()
        except (ValueError, TypeError):
            st.query_params.clear()

    # ── Mobile: handle ?nav= query param (must be before radio widget) ────────
    handle_mobile_nav_params()

    # ── Pending navigation from quick-action buttons ───────────────────────────
    # Must be applied before the widget is instantiated to avoid StreamlitAPIException
    if "_nav_goto" in st.session_state:
        st.session_state["nav_section"] = st.session_state.pop("_nav_goto")
    if "_nav_sub_diagnostik_goto" in st.session_state:
        st.session_state["nav_sub_diagnostik"] = st.session_state.pop("_nav_sub_diagnostik_goto")
    if "_nav_sub_spieler_goto" in st.session_state:
        st.session_state["nav_sub_spieler"] = st.session_state.pop("_nav_sub_spieler_goto")

    # ── Hierarchische Hauptnavigation ─────────────────────────────────────────
    _NAV_TRANS = {
        "🏠  Startseite":    {"de": "🏠  Startseite",    "en": "🏠  Dashboard",    "tr": "🏠  Ana Sayfa",    "es": "🏠  Inicio",        "fr": "🏠  Accueil",       "pt": "🏠  Início",        "ru": "🏠  Главная",       "ar": "🏠  الرئيسية"},
        "👤  Spieler":       {"de": "👤  Spieler",        "en": "👤  Players",      "tr": "👤  Oyuncular",    "es": "👤  Jugadores",     "fr": "👤  Joueurs",       "pt": "👤  Jogadores",     "ru": "👤  Игроки",        "ar": "👤  اللاعبون"},
        "🔬  Diagnostik":    {"de": "🔬  Diagnostik",     "en": "🔬  Diagnostics",  "tr": "🔬  Tanı",         "es": "🔬  Diagnóstico",   "fr": "🔬  Diagnostic",    "pt": "🔬  Diagnóstico",   "ru": "🔬  Диагностика",   "ar": "🔬  التشخيص"},
        "📅  Training":      {"de": "📅  Training",       "en": "📅  Training",     "tr": "📅  Antrenman",    "es": "📅  Entrenamiento", "fr": "📅  Entraînement",  "pt": "📅  Treino",        "ru": "📅  Тренировка",    "ar": "📅  التدريب"},
        "📈  Entwicklung":   {"de": "📈  Entwicklung",    "en": "📈  Development",  "tr": "📈  Gelişim",      "es": "📈  Desarrollo",    "fr": "📈  Développement", "pt": "📈  Desenvolvimento","ru": "📈  Развитие",       "ar": "📈  التطور"},
        "⚖️  Vergleich":     {"de": "⚖️  Vergleich",     "en": "⚖️  Comparison",   "tr": "⚖️  Karşılaştır", "es": "⚖️  Comparación",  "fr": "⚖️  Comparaison",   "pt": "⚖️  Comparação",    "ru": "⚖️  Сравнение",     "ar": "⚖️  المقارنة"},
        "👥  Mannschaft":    {"de": "👥  Mannschaft",     "en": "👥  Team",         "tr": "👥  Takım",        "es": "👥  Equipo",        "fr": "👥  Équipe",        "pt": "👥  Equipa",        "ru": "👥  Команда",        "ar": "👥  الفريق"},
        "📄  Dokumente":      {"de": "📄  Dokumente",      "en": "📄  Documents",    "tr": "📄  Belgeler",     "es": "📄  Documentos",    "fr": "📄  Documents",      "pt": "📄  Documentos",    "ru": "📄  Документы",     "ar": "📄  المستندات"},
        "⚙️  Einstellungen": {"de": "⚙️  Einstellungen", "en": "⚙️  Settings",     "tr": "⚙️  Ayarlar",     "es": "⚙️  Ajustes",      "fr": "⚙️  Paramètres",    "pt": "⚙️  Definições",    "ru": "⚙️  Настройки",     "ar": "⚙️  الإعدادات"},
        "ℹ️  Über":          {"de": "ℹ️  Über",           "en": "ℹ️  About",        "tr": "ℹ️  Hakkında",    "es": "ℹ️  Acerca de",    "fr": "ℹ️  À propos",      "pt": "ℹ️  Sobre",         "ru": "ℹ️  О программе",   "ar": "ℹ️  حول"},
    }
    _cur_lang = get_lang()
    _subnav_by_section = {
        "👤  Spieler": (_SUB_SPIELER, "nav_sub_spieler"),
        "🔬  Diagnostik": (_SUB_DIAGNOSTIK, "nav_sub_diagnostik"),
        "📅  Training": (_SUB_TRAINING, "nav_sub_training"),
    }
    section = st.session_state.get("nav_section")
    if section not in _MAIN_SECTIONS:
        section = _MAIN_SECTIONS[0]
        st.session_state["nav_section"] = section

    sub_choice = None
    for _nav_item in _MAIN_SECTIONS:
        _nav_label = _NAV_TRANS.get(_nav_item, {}).get(_cur_lang, _nav_item)
        if st.button(
            _nav_label,
            key=f"sidebar_nav_{_nav_item}",
            use_container_width=True,
            type="primary" if section == _nav_item else "secondary",
        ):
            st.session_state["nav_section"] = _nav_item
            if _nav_item in _subnav_by_section:
                _map, _key = _subnav_by_section[_nav_item]
                st.session_state[_key] = next(iter(_map))
            st.rerun()

        # Unterpunkte werden direkt nach ihrem Hauptbereich gerendert.
        if _nav_item not in _subnav_by_section or section != _nav_item:
            continue
        _map, _key = _subnav_by_section[_nav_item]
        _active_sub = st.session_state.get(_key)
        if _active_sub not in _map:
            _active_sub = next(iter(_map))
            st.session_state[_key] = _active_sub
        # Der Container dient ausschließlich der kompakten visuellen
        # Untergliederung; Zustände, Keys und Navigation bleiben unverändert.
        with st.container(key=f"sidebar_subnav_{_key}"):
            for _sub_item in _map:
                if st.button(
                    _sub_item,
                    key=f"sidebar_subnav_{_key}_{_sub_item}",
                    use_container_width=True,
                    type="primary" if _sub_item == _active_sub else "secondary",
                ):
                    st.session_state[_key] = _sub_item
                    st.rerun()
        sub_choice = _active_sub

    inject_scroll_to_top_if_needed(section)

    st.markdown(f'<hr style="border-color:{C["surface2"]};margin:10px 0">', unsafe_allow_html=True)

    # ── Kader count ───────────────────────────────────────────────────────────
    n = len(alle_spieler) if alle_spieler else 0
    st.markdown(
        f'<div style="padding:8px 12px;background:{C["surface"]};border-radius:8px;border:1px solid {C["border"]}">'
        f'<div style="font-size:10px;color:{C["muted"]};letter-spacing:1px">KADER</div>'
        f'<div style="font-size:20px;font-weight:700;color:{C["text"]}">{n} Spieler</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Mobile logout request (from ?nav=__logout__ in Mehr overlay) ─────────
    if st.session_state.pop("__mobile_logout_request__", False):
        _mob_token = st.session_state.get("_session_token")
        if _mob_token:
            try:
                from database import session_beenden as _mob_sb
                _mob_sb(_mob_token)
            except Exception:
                pass
        if _cookie_ctrl:
            try:
                _cookie_ctrl.remove("ath_sid")
            except Exception:
                pass
        _mob_del = [k for k in st.session_state.keys() if k != "__logout_ok__"]
        for _mk in _mob_del:
            del st.session_state[_mk]
        st.session_state["__logout_ok__"] = True
        st.rerun()

    # ── Benutzer-Info & Abmelden ──────────────────────────────────────────────
    _sb_user  = st.session_state.get("user", {})
    _sb_uname = (f"{_sb_user.get('vorname','')} {_sb_user.get('nachname','')}".strip()
                 or _sb_user.get("email", ""))
    _sb_rolle = _sb_user.get("rolle", "")
    # Verein nur anzeigen wenn kein technischer Mandant (persönlicher Einzeltrainer-Verein)
    _sb_verein = "" if _sb_user.get("ist_technischer_mandant") else (
        _sb_user.get("verein_name") or _sb_user.get("verein") or ""
    )
    st.markdown(
        f'<div style="margin:8px 0 4px;padding:8px 12px;background:{C["surface"]};'
        f'border-radius:8px;border:1px solid {C["border"]}">'
        f'<div style="font-size:9px;color:{C["muted"]};letter-spacing:1px">ANGEMELDET ALS</div>'
        f'<div style="font-size:12px;font-weight:600;color:{C["text"]}">{_sb_uname}</div>'
        f'<div style="font-size:10px;color:{C["muted"]}">{_sb_rolle}'
        f'{" · " + _sb_verein if _sb_verein else ""}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # Mandant-wechseln (nur für Trainer mit mehreren Mandanten)
    if (
        _sb_rolle == "Trainer"
        and st.session_state.get("_aktiver_mandant_id")
        and st.session_state.get("_mandant_gewaehlt")
    ):
        try:
            from database import trainer_mandanten_fuer_benutzer as _tmfb_sb
            _sb_mandanten = _tmfb_sb(_sb_user["id"])
            _sb_echte = [m for m in _sb_mandanten if not m.get("ist_technischer_mandant")]
            if len(_sb_echte) > 1:
                if st.button(
                    "🔀 Mandant wechseln",
                    key="mandant_wechseln_btn",
                    use_container_width=True,
                ):
                    st.session_state.pop("_mandant_gewaehlt", None)
                    st.session_state.pop("_aktiver_mandant_id", None)
                    st.rerun()
        except Exception:
            pass

    if st.button("🚪 Abmelden", key="logout_btn", use_container_width=True):
        # DB-Session beenden
        _logout_token = st.session_state.get("_session_token")
        if _logout_token:
            try:
                from database import session_beenden as _sb
                _sb(_logout_token)
            except Exception:
                pass
        # Cookie löschen
        if _cookie_ctrl:
            try:
                _cookie_ctrl.remove("ath_sid")
            except Exception:
                pass
        # Logout-Flag setzen, restliche Keys löschen
        _keys_del = [k for k in st.session_state.keys() if k != "__logout_ok__"]
        for _lk in _keys_del:
            del st.session_state[_lk]
        st.session_state["__logout_ok__"] = True
        st.rerun()

    # ── Copyright-Footer ──────────────────────────────────────────────────────
    st.markdown(
        f'<div style="padding:8px 12px 4px;border-top:1px solid {C["border"]};margin-top:8px">'
        f'<div translate="no" style="font-size:9px;color:{C["muted"]};text-align:center;line-height:1.6">'
        f'© 2026 Athletic Performance Hub<br>v{APP_VERSION}'
        f'</div></div>',
        unsafe_allow_html=True,
    )
    # Impressum/Datenschutz/AGB sind unter "ℹ️  Über" > Info erreichbar — kein Extra-Button hier.

# ── Route ─────────────────────────────────────────────────────────────────────
_check_save_ok()

# Inject floating ☰ button so mobile users can open the sidebar drawer.
# The button finds and clicks [data-testid="stSidebarCollapseButton"] button —
# Streamlit 1.60.0's real toggle (inside stSidebarHeader, inside the sidebar).
# On desktop (≥769px) it stays display:none via CSS media query.
inject_mobile_sidebar_opener()

# Helper: look up active player object for mobile player header
def _mob_player():
    _gid = st.session_state.get("global_player_id")
    return next((p for p in (alle_spieler or []) if p["id"] == _gid), None) if _gid else None


if section == "🏠  Startseite":
    page_saas_dashboard()
elif section == "👤  Spieler":
    # Mobile: inline player selector at top of Spieler page (sidebar hidden on ≤768px)
    inject_mobile_player_selector(alle_spieler, st.session_state.get("global_player_id"), section)
    _SUB_SPIELER[sub_choice]()
elif section == "🔬  Diagnostik":
    _SUB_DIAGNOSTIK[sub_choice]()
elif section == "📅  Training":
    inject_mobile_player_header(_mob_player(), section)
    _SUB_TRAINING[sub_choice]()
elif section == "📈  Entwicklung":
    inject_mobile_player_header(_mob_player(), section)
    page_fortschritt()
elif section == "⚖️  Vergleich":
    inject_mobile_player_header(_mob_player(), section)
    page_spieler_vergleich()
elif section == "👥  Mannschaft":
    page_dashboard()
elif section == "📄  Dokumente":
    inject_mobile_player_header(_mob_player(), section)
    page_dokumente()
elif section == "⚙️  Einstellungen":
    page_einstellungen()
elif section == "ℹ️  Über":
    page_ueber_software()
elif section == "👤  Mein Profil":
    page_mein_profil()
elif section == "🧑‍💼  Trainerportal":
    page_trainerportal()
elif section == "🔑  Benutzerverwaltung":
    page_benutzerverwaltung()
elif section == "🏢  Vereinsverwaltung":
    page_vereine()
elif section == "💳  Lizenz":
    page_lizenz_vereinsadmin()
elif section == "💳  Lizenzverwaltung":
    page_lizenz_superadmin()
elif section == "📋  Mein Vertrag":
    page_mein_vertrag()
elif section == "👥  Kundenverwaltung":
    page_kundenverwaltung()

# ── Screen-width detector (no-op for nav; kept for inject_mobile_player_header guard) ──
render_mobile_nav(section)

# ═══════════════════════════════════════════════════════════════════════════════
# §20 — KORREKTUR SCHRITT 7: Mobile Bottom Navigation (Abschlussbericht)
# Datum: 2026-08-12
# ═══════════════════════════════════════════════════════════════════════════════
#
# PROBLEM-ANALYSE (drei unabhängige Fehler)
# ──────────────────────────────────────────
# 1. NAV UNSICHTBAR
#    Ursache: declare_component(path="components/mobile_nav/") schlägt in
#    Replits mTLS-Proxy fehl. Streamlit versucht /_stcore/component/ zu
#    routen — dieser Pfad wird nicht durchgeleitet. Timeout-Error im
#    Browser-Log → Custom Component nie gerendert → Nav komplett weg.
#
# 2. "SÜNDIGEN" / AUTO-TRANSLATE
#    Ursache: Chromes automatische Seitenübersetzung griff, weil kein
#    lang="de" am <html>-Element gesetzt war. Streamlit's internes UI
#    enthält englische Texte → Chrome klassifiziert die Seite als englisch
#    → bietet Übersetzung an → "Abmelden" wurde zu "sündigen" übersetzt.
#
# 3. FALSCHE NAV-ITEM-LABELS (component-intern)
#    Folge aus Problem 1 — irrelevant, da component ganz entfernt.
#
# LÖSUNG
# ──────
# Vollständige Überarbeitung mobile.py. Kein declare_component mehr.
#
# Neue Architektur:
#
#   A) VISUELLE NAV
#      st.markdown → <nav class="aph-bottom-nav"> mit <button onclick>
#      (kein <a href> → kein Page-Reload → Session erhalten)
#      CSS aus theme.py: position:fixed; bottom:0; z-index:9999
#      Alle nav-interaktiven Elemente: <button type="button">
#
#   B) NAVIGATE-SIGNAL VIA HIDDEN TRIGGER-BUTTONS
#      Für jedes mögliche Navigationsziel existiert ein st.button(label="⬡N")
#      (U+2B21 White Hexagon als eindeutiges Präfix-Zeichen).
#      render_mobile_nav() rendert alle 21 Trigger in st.columns(21) am
#      Seitenende. Die onclick-Handler der visuellen Buttons suchen per JS
#      den Trigger mit passendem textContent ("⬡3" etc.) und rufen .click()
#      auf. Streamlit empfängt das Widget-Event über den WebSocket →
#      _apply_nav_signal() → st.session_state update → st.rerun().
#      Kein Seiten-Reload, keine neue Session, kein Cookie-Verlust.
#
#   C) TRIGGER-BUTTONS VERSTECKEN
#      <img src="x" onerror="..."> feuert auf jedem Rerun, wenn das
#      Element neu in den DOM eingefügt wird. Der onerror-Handler startet
#      einen MutationObserver, der jede stColumn mit ⬡-Button-Inhalt auf
#      position:absolute;top:-9999px verschiebt. Programmatisches .click()
#      auf off-screen Elemente funktioniert (kein CSS-Gate für Events).
#      Hinweis: <script>-Blöcke in st.markdown werden von React unterdrückt.
#      Nur Event-Handler-Attribute (onclick, onerror) und <style>-Blöcke
#      werden ausgeführt.
#
#   D) CHROME AUTO-TRANSLATE FIX
#      Derselbe onerror-Handler setzt:
#        document.documentElement.lang = 'de'
#        document.documentElement.setAttribute('translate', 'no')
#      Alle Nav-HTML-Elemente tragen zusätzlich translate="no" als Attribut.
#
# ÄNDERUNGEN
# ──────────
# • mobile.py       — vollständig neu geschrieben (button-trigger Architektur)
# • theme.py        — .aph-bn-item als <button>-Styles (inkl. Reset) neu;
#                     .aph-mehr-item, .aph-mehr-close, .aph-mph-switch
#                     alle als <button>-Styles angepasst;
#                     padding-bottom: 80px für .main .block-container
# • app.py          — keine Import-Änderungen nötig (render_mobile_nav war
#                     bereits korrekt importiert)
# • components/     — mobile_nav/index.html verbleibt, wird aber nicht mehr
#                     geladen (kein declare_component-Aufruf mehr)
#
# DESKTOP UNBERÜHRT
# ─────────────────
# Alle @media-Queries bleiben unverändert. Desktop-Navigation (Sidebar) ist
# nicht betroffen. Die versteckten Trigger-Buttons sind auf Desktop durch
# die MutationObserver-Logik ebenfalls off-screen, stören aber die Sidebar
# nicht (die Buttons liegen im Main-Content-Bereich).
#
# BEKANNTE EINSCHRÄNKUNGEN
# ────────────────────────
# • 21 Mini-Spalten = minimaler Layout-Overhead vor dem MutationObserver-Hide.
#   In der Praxis: kein sichtbares Flash (Observer feuert vor Paint).
# • Ein Klick auf einen Nav-Button verursacht immer 2 Reruns (1× für den
#   Trigger-Button, 1× für st.rerun() in _apply_nav_signal). Das ist die
#   minimale Anzahl für die session-state-basierte Navigation in Streamlit.
# ═══════════════════════════════════════════════════════════════════════════════
