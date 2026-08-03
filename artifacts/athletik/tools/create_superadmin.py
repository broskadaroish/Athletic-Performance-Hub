"""
Skript zum Anlegen eines Superadmins und Standard-Vereins.
Ausführen einmalig nach der Erstinstallation:

    python tools/create_superadmin.py

"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, verein_speichern, benutzer_speichern, vereine_laden, benutzer_laden

# ── Datenbank initialisieren ──────────────────────────────────────────────────
init_db()

# ── Standard-Verein anlegen falls keiner existiert ────────────────────────────
vereine = vereine_laden()
if not vereine:
    vid = verein_speichern("Standard-Verein")
    print(f"✅ Standard-Verein angelegt (ID {vid})")
else:
    vid = vereine[0]["id"]
    print(f"ℹ️  Verein vorhanden: {vereine[0]['name']} (ID {vid})")

# ── Superadmin anlegen falls noch kein Superadmin existiert ──────────────────
alle = benutzer_laden()
superadmins = [b for b in alle if b.get("rolle") == "Superadmin"]
if superadmins:
    print(f"ℹ️  Superadmin vorhanden: {superadmins[0]['email']}")
else:
    email    = input("Superadmin E-Mail (Login): ").strip() or "admin@bruce.local"
    passwort = input("Superadmin Passwort: ").strip() or "admin123"
    bid = benutzer_speichern(
        verein_id=vid,
        vorname="Super",
        nachname="Admin",
        email=email,
        passwort=passwort,
        rolle="Superadmin",
    )
    print(f"✅ Superadmin angelegt: {email} (ID {bid})")

print("\n✅ Fertig. Starte die App und melde dich an.")
