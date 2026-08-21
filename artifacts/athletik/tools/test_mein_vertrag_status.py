"""Regressionen für die gemeinsame Statusquelle von Lizenzverwaltung und Vertrag."""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEST_DB = Path(tempfile.mkdtemp(prefix="aph-vertrag-status-")) / "vertrag.db"
os.environ["ATHLETIK_DB_PATH"] = str(TEST_DB)

import database
database.DB_PATH = str(TEST_DB)
database.init_db()

import streamlit as st
from license import get_lizenz_info, invalidate_lizenz_cache
from modules.lizenz_page import _sa_normalize
from modules.mein_vertrag import _laden


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS  {label}")


def neuer_verein(
    name: str,
    *,
    status: str,
    lizenz_bis: str,
    aktiv: int = 1,
    gesperrt: int = 0,
    kundennummer: str | None = None,
    kuendigungsstatus: str = "aktiv",
    ist_technischer_mandant: int = 0,
    stripe_subscription_id: str | None = None,
    cancel_at_period_end: int = 1,
) -> int:
    with database.get_conn() as conn:
        return conn.execute(
            """INSERT INTO vereine
               (name, aktiv, gesperrt, kundennummer, lizenztyp, lizenz_status,
                lizenz_bis, kuendigungsstatus, kuendigung_eingegangen,
                gekuendigt_zum, cancel_at_period_end, ist_technischer_mandant,
                stripe_subscription_id)
               VALUES (?, ?, ?, ?, 'VEREIN_PRO', ?, ?, ?, '2026-08-01', '2026-09-01', ?, ?, ?)""",
            (
                name, aktiv, gesperrt, kundennummer, status, lizenz_bis, kuendigungsstatus,
                cancel_at_period_end, ist_technischer_mandant, stripe_subscription_id,
            ),
        ).lastrowid


def vertrag_und_admin_status(verein_id: int) -> tuple[dict, str]:
    invalidate_lizenz_cache(verein_id)
    vertrag = _laden({"verein_id": verein_id, "rolle": "Vereinsadmin"})
    invalidate_lizenz_cache(verein_id)
    admin = next(row for row in _sa_normalize(database.alle_vereine_lizenz(), []) if row["_id"] == verein_id)
    return vertrag, admin["lizenz_status"]


st.session_state.clear()
zukunft = (date.today() + timedelta(days=60)).isoformat()
vergangenheit = (date.today() - timedelta(days=1)).isoformat()

# Aktive Lizenz: Mein Vertrag und Superadmin lesen dieselbe wirksame Bewertung.
aktiv_id = neuer_verein("Aktiv", status="active", lizenz_bis=zukunft, kundennummer="APH-900001")
vertrag, admin_status = vertrag_und_admin_status(aktiv_id)
check("Aktive Lizenz erscheint im Vertrag als aktiv", vertrag["lizenz_status"] == "active")
check("Aktive Lizenz stimmt mit Superadmin überein", vertrag["lizenz_status"] == admin_status)

# Reaktivierung: Flags und lokale Kündigungsdaten werden nur für reguläre Kunden zurückgesetzt.
reaktiv_id = neuer_verein(
    "Reaktivierbar", status="suspended", lizenz_bis=vergangenheit, aktiv=0, gesperrt=1,
    kundennummer="APH-900002", kuendigungsstatus="vorgemerkt",
)
database.lizenz_setzen(reaktiv_id, "VEREIN_PRO", "active", zukunft)
with database.get_conn() as conn:
    reaktiv_row = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (reaktiv_id,)).fetchone())
check(
    "Reaktivierung stellt Zugangs- und Kündigungsflags wieder her",
    reaktiv_row["aktiv"] == 1
    and reaktiv_row["gesperrt"] == 0
    and reaktiv_row["kuendigungsstatus"] == "aktiv"
    and reaktiv_row["kuendigung_eingegangen"] is None
    and reaktiv_row["gekuendigt_zum"] is None
    and reaktiv_row["cancel_at_period_end"] == 0,
)
vertrag, admin_status = vertrag_und_admin_status(reaktiv_id)
check("Reaktivierte Lizenz bleibt im Vertrag nicht gelöscht", vertrag["lizenz_status"] == "active")
check("Reaktivierte Lizenz stimmt mit Superadmin überein", vertrag["lizenz_status"] == admin_status)

# Ein technischer Mandant muss auch bei einem alten Paket-Key in beiden Ansichten
# als Trainer-Paket aufgelöst werden.
tech_id = neuer_verein(
    "Technischer Mandant", status="active", lizenz_bis=zukunft, kundennummer="APH-900005",
    ist_technischer_mandant=1,
)
with database.get_conn() as conn:
    conn.execute("UPDATE vereine SET lizenztyp='BASIC' WHERE id=?", (tech_id,))
vertrag, admin_status = vertrag_und_admin_status(tech_id)
invalidate_lizenz_cache(tech_id)
admin_row = next(row for row in _sa_normalize(database.alle_vereine_lizenz(), []) if row["_id"] == tech_id)
check("Technischer Mandant normalisiert BASIC im Vertrag als Trainer-Paket", vertrag["lizenztyp"] == "TRAINER_BASIC")
check("Technischer Mandant normalisiert BASIC im Superadmin gleich", admin_row["_paket_key"] == "TRAINER_BASIC")

# Ablauf wird nur zentral berechnet und deshalb auf beiden Seiten gleich angezeigt.
expired_id = neuer_verein("Abgelaufen", status="active", lizenz_bis=vergangenheit, kundennummer="APH-900003")
vertrag, admin_status = vertrag_und_admin_status(expired_id)
check("Abgelaufene Lizenz wird im Vertrag als abgelaufen angezeigt", vertrag["lizenz_status"] == "expired")
check("Abgelaufene Lizenz stimmt mit Superadmin überein", vertrag["lizenz_status"] == admin_status)

# Eine laufende Kündigung bleibt ein eigener Vertragsstatus.
cancelled_id = neuer_verein(
    "Gekuendigt", status="cancelled", lizenz_bis=zukunft, kundennummer="APH-900004",
    kuendigungsstatus="vorgemerkt",
)
vertrag, admin_status = vertrag_und_admin_status(cancelled_id)
check("Gekündigte Lizenz zeigt den korrekten Lizenzstatus", vertrag["lizenz_status"] == "cancelled")
check("Gekündigte Lizenz behält ihren Kündigungsstatus", vertrag["kuendigungsstatus"] == "vorgemerkt")
check("Gekündigte Lizenz stimmt mit Superadmin überein", vertrag["lizenz_status"] == admin_status)

# Eine Stripe-Kündigung darf durch lokales Speichern nicht als widerrufen gelten.
stripe_id = neuer_verein(
    "Stripe Kündigung", status="cancelled", lizenz_bis=zukunft, kundennummer="APH-900006",
    kuendigungsstatus="vorgemerkt", stripe_subscription_id="sub_test_pending",
)
try:
    database.lizenz_setzen(stripe_id, "VEREIN_PRO", "active", zukunft)
    stripe_statuswechsel_blockiert = False
except ValueError:
    stripe_statuswechsel_blockiert = True
with database.get_conn() as conn:
    stripe_row = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (stripe_id,)).fetchone())
check(
    "Stripe-Statuswechsel bleibt ohne Stripe-Widerruf blockiert",
    stripe_statuswechsel_blockiert,
)
check(
    "Stripe-Kündigungsdaten und Status bleiben ohne Stripe-Widerruf erhalten",
    stripe_row["lizenz_status"] == "cancelled"
    and stripe_row["aktiv"] == 1
    and stripe_row["cancel_at_period_end"] == 1
    and stripe_row["kuendigungsstatus"] == "vorgemerkt"
    and stripe_row["kuendigung_eingegangen"] == "2026-08-01"
    and stripe_row["gekuendigt_zum"] == "2026-09-01",
)

# Anonymisierte Kunden dürfen nie durch eine Lizenzänderung reaktiviert werden.
deleted_id = neuer_verein(
    "Archiviert", status="geloescht", lizenz_bis=zukunft, aktiv=0, gesperrt=1,
    kundennummer="[gelöscht]",
)
vertrag, admin_status = vertrag_und_admin_status(deleted_id)
check("Anonymisierter Kunde bleibt im Vertrag gelöscht", vertrag["lizenz_status"] == "geloescht")
check("Anonymisierte Kundennummer bleibt unverändert", vertrag["kundennummer"] == "[gelöscht]")
check("Anonymisierter Kunde stimmt mit Superadmin überein", vertrag["lizenz_status"] == admin_status)
try:
    database.lizenz_setzen(deleted_id, "VEREIN_PRO", "active", zukunft)
    reaktivierung_blockiert = False
except ValueError:
    reaktivierung_blockiert = True
check("Anonymisierter Kunde wird nicht reaktiviert", reaktivierung_blockiert)

with database.get_conn() as conn:
    deleted_row = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (deleted_id,)).fetchone())
check(
    "Anonymisierte Daten bleiben nach blockierter Reaktivierung erhalten",
    deleted_row["kundennummer"] == "[gelöscht]"
    and deleted_row["lizenz_status"] == "geloescht"
    and deleted_row["aktiv"] == 0,
)

# Auch ein roher Löschstatus bleibt gelöscht, wenn die Kundennummer aus einem
# historischen Import nicht das aktuelle Anonymisierungs-Sentinel trägt.
raw_deleted_id = neuer_verein(
    "Historisch gelöscht", status="geloescht", lizenz_bis=zukunft, aktiv=0, gesperrt=1,
    kundennummer="APH-900007",
)
vertrag, admin_status = vertrag_und_admin_status(raw_deleted_id)
check("Roher Löschstatus bleibt in Mein Vertrag gelöscht", vertrag["lizenz_status"] == "geloescht")
check("Roher Löschstatus stimmt mit Superadmin überein", vertrag["lizenz_status"] == admin_status)
try:
    database.lizenz_setzen(raw_deleted_id, "VEREIN_PRO", "active", zukunft)
    raw_reaktivierung_blockiert = False
except ValueError:
    raw_reaktivierung_blockiert = True
check("Roher Löschstatus kann nicht reaktiviert werden", raw_reaktivierung_blockiert)
with database.get_conn() as conn:
    raw_deleted_row = dict(conn.execute("SELECT * FROM vereine WHERE id=?", (raw_deleted_id,)).fetchone())
check(
    "Roher Löschstatus bleibt nach Reaktivierungsversuch unverändert",
    raw_deleted_row["lizenz_status"] == "geloescht"
    and raw_deleted_row["aktiv"] == 0
    and raw_deleted_row["gesperrt"] == 1,
)

print("Gesamt: PASS")