# BLOCK B0 — VOLLSTÄNDIGE BESTANDSAUFNAHME APH
*Erstellt: 2026-08-14 | Basis: tatsächlicher Code-Stand*

---

## B0.1 SUPERADMIN

### Erkennung
- Einziger Rollenwert: exakter String `"Superadmin"` (case-sensitive, kein Enum).
- Prüfung zentral über `st.session_state["rolle"] == "Superadmin"` im UI-Layer.
- DB-seitig: `database.superadmin_emails()` → `WHERE rolle='Superadmin' AND aktiv=1` (`database.py:4128`).
- CLI-Tool: `tools/create_superadmin.py` (manueller Seed).
- Init-Check in `app.py:477–497` (startet App, sucht aktiven Superadmin).

### Vorhandene Superadmin-Seiten / -Funktionen
| Seite | Datei | Funktion |
|-------|-------|----------|
| Kundenverwaltung | `modules/kundenverwaltung.py` | `page_kundenverwaltung()` |
| Benutzerverwaltung | `modules/benutzerverwaltung.py` | `page_benutzerverwaltung()` |
| Vereinsverwaltung | `modules/vereine.py` | `page_vereine()` |
| Lizenz-Superadmin | `modules/lizenz_page.py` | `page_lizenz_superadmin()` |
| SaaS-Dashboard | `modules/saas_dashboard.py` | diverse |
| Trainerportal | `modules/trainerportal.py` | `page_trainerportal()` |
| Audit/Login-Übersicht | in `modules/kundenverwaltung.py` | `_detail_c_audit()` |
| SMTP-Test | in `app.py` | smtp-Testbereich |
| Kündigungen | `modules/mein_vertrag.py` + KV | Kündigungsliste |

### ⚠️ KRITISCH: Fehlender Schutz des letzten Superadmins

**Problem:** Es gibt KEINE Guard, die verhindert, dass der letzte aktive Superadmin gelöscht oder deaktiviert wird.

- `benutzer_loeschen(benutzer_id)` → `database.py:3751` führt direktes DELETE aus, ohne Superadmin-Rolle zu prüfen.
- `benutzer_aktivieren(id, aktiv=False)` → `database.py:3401` → reines UPDATE, kein Zählcheck.
- `page_benutzerverwaltung()` → `benutzerverwaltung.py:104–112`: kann `aktiv` für beliebige Benutzer setzen.
- Kein `COUNT(*) WHERE rolle='Superadmin' AND aktiv=1`-Guard irgendwo.

**Verlust-Szenarien:**
1. Direktes Deaktivieren über Benutzerverwaltung → kein Login mehr möglich
2. Direktes Löschen über Benutzerverwaltung → Superadmin weg
3. Verein-Löschung: blockiert wenn Benutzer zugeordnet (`database.py:2912–2927`), schützt aber nicht explizit Superadmin
4. Init-/Repair-Code (`database.py:2650–2673`) sucht nur irgendeinen Superadmin; keine Korrektur von "0 Superadmins"
5. Migration/Cleanup: kein Superadmin-Ausschluss in Bereinigungspfaden dokumentiert

**Realer Fall:** Es gab bereits einen Zustand ohne Superadmin in der Produktionsdatenbank (laut Spec). Dies bestätigt das Risiko.

**Handlungsbedarf B1:** Guard in `benutzer_loeschen()` und `benutzer_aktivieren()` — wenn `rolle='Superadmin'` und `COUNT(aktive Superadmins) <= 1`, blockieren.

---

## B0.2 KUNDENVERWALTUNG

### Vorhandene Funktionen (`modules/kundenverwaltung.py`)
| Funktion | Status |
|----------|--------|
| Kunden anzeigen (Liste + KPI-Dashboard) | ✅ |
| Suchen (Name, E-Mail, Kundennummer) | ✅ |
| Filtern (Paket, Status, Typ) | 🟡 teilweise |
| Aktivieren / Deaktivieren | ✅ |
| Sperren / Entsperren | ✅ |
| Kunden löschen | ✅ (zweistufig mit Kundennummer-Bestätigung) |
| Kundendetail | ✅ (`_kunde_detail`) |
| Vertragsdetails | ✅ (`_detail_c_lizenz`) |
| Trainerkunden | ✅ |
| Vereinskunden | ✅ |
| Technische Mandanten | ✅ (über `ist_technischer_mandant=1`) |

### Datenbeziehung
```
vereine (Kundenkonto / technischer Mandant)
  └── benutzer (verein_id → FK, nullable, kein ON DELETE)
        └── spieler (trainer_id, verein_id → FK)
```
- Einzeltrainer: `vereine.ist_technischer_mandant = 1` + `benutzer.rolle = 'Trainer'`
- Vereinskunden: `vereine.ist_technischer_mandant = 0` + ggf. `Vereinsadmin`-Benutzer
- `vereine_laden(nur_echte=True)` blendet technische Mandanten aus der Vereinsliste aus

---

## B0.3 KUNDENNUMMERN

### Erzeugung
- Format: `APH-%06d` (z. B. `APH-000007`)
- Funktionen: `kundennummer_vergeben_verein()` + `kundennummer_vergeben_benutzer()` (`database.py:4771–4797`)
- Algorithmus: `MAX(kundennummer) über beide Tabellen + 1` → **nicht atomar** (race condition bei parallelen Registrierungen möglich)
- Kein `UNIQUE`-Constraint in der DB
- Superadmins erhalten **keine** Kundennummer (`database.py:2602–2607`)
- Init-Migration vergibt fehlende Nummern nachträglich

### Semantik
| Tabelle | Nummer bedeutet |
|---------|----------------|
| `vereine.kundennummer` | **Vertragskundennummer** (Mandant/Konto) — führend |
| `benutzer.kundennummer` | Benutzeridentifikation (relevant für Einzeltrainer ohne Verein) |

### UI-Darstellung
- Kundenverwaltung zeigt primär `vereine.kundennummer`, fallback auf `benutzer.kundennummer` (`kundenverwaltung.py:169`, `_kunde_detail:617`)

### ⚠️ Risiken
- Keine DB-UNIQUE-Constraint → manuelle Eingriffe oder Bugs können Duplikate erzeugen
- MAX+1-Vergabe nicht transaktionssicher
- Doppelte Kundennummern werden nirgendwo aktiv geprüft oder gemeldet

---

## B0.4 BENUTZERVERWALTUNG

### Vorhandene Funktionen (`modules/benutzerverwaltung.py`)
| Funktion | Status |
|----------|--------|
| Benutzerliste | ✅ |
| Benutzer erstellen | ✅ |
| Name / E-Mail ändern | ✅ |
| Rolle ändern | ✅ (via Superadmin) |
| Deaktivieren / Reaktivieren | ✅ |
| Benutzer löschen | ✅ |
| Passwort setzen (Admin) | ✅ |
| Passwort-Reset-E-Mail | ✅ |
| E-Mail-Verifikation erneut senden | ✅ |
| Letzter Login | ✅ (`login_log`) |
| Login-Sperren | 🟡 (Deaktivierung, kein separates Login-Sperr-Flag) |
| Mandantenzuordnung | ✅ |

### Tatsächlich vorhandene Rollen (aus Code)
| Rolle | Beschreibung |
|-------|-------------|
| `Superadmin` | Systemadministrator, mandantenübergreifend |
| `Vereinsadmin` | Vereinsverantwortlicher (eigener Mandant) |
| `Trainer` | Standard-Trainer (DEFAULT in DB) |
| *(Spieler-Accounts gibt es als Datensatz, nicht als Login-Rolle)* | |

**Hinweis:** `Spieler` und `Eltern` existieren als Datenkonzepte, **nicht** als Login-Rollen im `benutzer`-System.

---

## B0.5 ROLLEN UND MANDANTENTRENNUNG

### UI-Layer
- Superadmin: sieht alles
- Vereinsadmin: gefiltert auf `verein_id`
- Trainer: gefiltert auf eigene Spieler (`trainer_id`)

### DB-Layer
- `spieler_mandant_pruefen()` existiert in `database.py` (SCHRITT 9 implementiert) — prüft Spieler-Zugriffsrechte
- `spieler_laden()` (`database.py:1065`) filtert korrekt nach Rolle: Superadmin → alle, Vereinsadmin → Verein, Trainer → eigene

### ⚠️ Lücken
- `benutzer_aktualisieren()` (`database.py:3392`): akzeptiert `verein_id` ohne zu prüfen, ob der aufrufende Benutzer Rechte auf diesen Mandanten hat
- Keine zentrale serverseitige Authorization-Middleware — alle Prüfungen sind in einzelnen Funktionen verstreut
- Trainer kann theoretisch via manipulierten Request `verein_id` wechseln, wenn der API-Endpunkt keine Verifizierung durchführt
- Streamlit (Single-Server) schützt über Session-State, kein echtes serverseitiges RPC-Gateway

---

## B0.6 LIZENZSYSTEM (`license.py`)

### Paketdefinitionen (✅ KORREKT — stimmt mit Spec überein)
| Paket | Max Trainer | Max Spieler | Monat | Jahr |
|-------|-------------|-------------|-------|------|
| TRAINER_BASIC | 1 | 20 | 9,99 € | 99 € |
| TRAINER_PRO | 1 | unbegrenzt | 14,99 € | 149 € |
| VEREIN_BASIC | 2 | 50 | 24,99 € | 249 € |
| VEREIN_PRO | 15 | unbegrenzt | 39,99 € | 399 € |

### Vorhandene Funktionen
| Funktion | Status | Datei |
|----------|--------|-------|
| `feature_erlaubt(lizenz_typ, feature)` | ✅ | `license.py:405` |
| `trainer_limit_erreicht(lizenz_typ, anz)` | ✅ | `license.py:423` |
| `spieler_limit_erreicht(lizenz_typ, anz)` | ✅ | `license.py:451` |
| Compat-Mapping (BASIC→TRAINER_BASIC etc.) | ✅ | `license.py:174–181` |
| Preise aus Env-Vars | ✅ | `license.py:116–153` |

### ⚠️ Technische Schulden
- Legacy-Bezeichnungen (`BASIC`, `PRO`, `Enterprise`, `Basis`, `Standard`, `Premium`) werden per Compat-Mapping aufgelöst
- `verein_speichern()` schreibt teils noch `"BASIC"` statt `"TRAINER_BASIC"` → inkonsistent
- Preis-IDs (Stripe) **doppelt** definiert: in `license.py` (ENV-Vars) UND in `app.py`/`stripe_service.py` über dieselben ENV-Vars — akzeptabel, da single source (ENV-Var)

---

## B0.7 VERTRAG / STRIPE

### Führende Vertragstabelle: `vereine` ✅
Alle Stripe-/Lizenz-Vertragsfelder liegen in `vereine`:

| Feld | Vorhanden | Anmerkung |
|------|-----------|-----------|
| `stripe_customer_id` | ✅ | |
| `stripe_subscription_id` | ✅ | |
| `lizenztyp` | ✅ | |
| `abo_intervall` | ✅ | |
| `lizenz_status` | ✅ | |
| `zahlungsstatus` | ✅ | |
| `testphase_bis` | ✅ | |
| `vertragsbeginn` | ✅ | nachträglich ergänzt (Phase A5) |
| `vertragsende` | ✅ | |
| `subscription_current_period_end` | ⚠️ | fehlt als persistentes Feld; `lizenz_bis` übernimmt semantisch |
| `cancel_at_period_end` | ✅ | |
| `kuendigungsstatus` | ✅ | |
| `gekuendigt_zum` | ✅ | |

### Doppelfelder in `benutzer`
Einige Lizenz-/Vertragsfelder existieren auch in `benutzer` (historisch):
- `lizenztyp`, `abo_intervall`, `lizenz_status` vermutlich in benutzer vorhanden (Legacy)
- Quelle für UI: unklar, ob immer konsistent aus `vereine` gelesen

### `stripe_events`-Tabelle
- **Nur im Express-API-Server** (`api-server/src/routes/stripe.ts:62`) — wird beim Start angelegt
- **Nicht in `database.py`** (Python-App kennt diese Tabelle nicht)
- Webhook-Idempotenz ist im API-Server implementiert ✅

---

## B0.8 PAKETLIMITS

### Serverseitige Durchsetzung
- `spieler_limit_erreicht()` und `trainer_limit_erreicht()` in `license.py` ✅
- Werden in `database.py` aufgerufen vor Spieler-/Trainer-Anlage

### ⚠️ Risiken
- **Fail-open**: bei DB-Exception gibt `spieler_limit_erreicht()` `False` zurück → Limit wird ignoriert
- **Legacy-Overrides**: `vereine.max_trainer` und `vereine.max_spieler` existieren als DB-Felder (`database.py:2893–2905`) — können zentrale Paketdefinition übersteuern; unklar ob aktiv genutzt
- **Downgrade-Schutz fehlt**: kein Check beim Paketdowngrade, ob aktuelle Nutzung das Ziellimit übersteigt

---

## B0.9 AUDIT / LOGGING

| Tabelle | Vorhanden | Spalten | Anmerkung |
|---------|-----------|---------|-----------|
| `audit_log` | ✅ | `id, benutzer_id, aktion, details, superadmin_id, erstellt_am` | `database.py:2574–2584` |
| `lizenz_warn_log` | ✅ | Verein-FK, Warn-Typ, Datum | `database.py:463–470` — ON DELETE CASCADE! |
| `login_log` | ✅ | Login-Einträge | `database.py:470–477` |
| `rechnungen` | ✅ | Rechnungsdaten | `database.py:2623–2638` |
| `stripe_events` | ✅ (API-Server) | `event_id, event_type` | nur in Express, nicht in Python sichtbar |
| `spieler_zuweisung_log` | ✅ | Spieler-Zuweisung | |
| `benachrichtigungen` | ✅ | Push-Notifications | |

⚠️ `lizenz_warn_log` hat `ON DELETE CASCADE` auf Verein-FK → Vereinslöschung entfernt Warn-Historie

---

## B0.10 DATENBANK — Relevante Kern-Tabellen

### `benutzer`
```
id, verein_id (FK nullable), vorname, nachname, email (UNIQUE),
passwort_hash, rolle DEFAULT 'Trainer', aktiv,
kundennummer, erstellt_am,
+ Auth/Verifikations-/Login-/Profil-/Lizenz-/Vertragsmigrations-Felder
```

### `vereine`
```
id, name, aktiv, ist_technischer_mandant, kundennummer, erstellt_am,
+ Lizenz-/Stripe-/Vertrags-/Zahlungs-/Sperr-/Kündigungs-Felder (migriert)
max_trainer, max_spieler (Legacy-Overrides)
```

### `spieler`
```
id, vorname, nachname, geburtsdatum, trainer_id, verein_id,
position, fuß, aktiv, erstellt_am
```

### `sessions`
```
(in database.py nicht als CREATE TABLE gefunden → läuft über st.session_state
 + Cookie-Controller; session_erstellen() schreibt in sessions-Tabelle)
```

### `stripe_events`
```
event_id (PK), event_type, created_at
(nur in api-server/src/routes/stripe.ts, Zeile 62)
```

### Weitere relevante Tabellen
- `rechnungsadressen`, `rechnungen`, `audit_log`, `login_log`, `lizenz_warn_log`
- `spieler_zuweisung_log`, `benachrichtigungen`, `push_tokens`
- Test-Tabellen: Verletzungen, Anthropometrie, FMS, Y-Balance, Sprint, Sprung, Agilität, Ausdauer, Spiro, Kraft
- Training/Planung: `trainingsplan_versionen`, `trainingsplan_eintraege`

---

## B0.11 UI-MODULE

| Bereich | Datei | Funktion |
|---------|-------|----------|
| Superadmin Dashboard | `modules/saas_dashboard.py` | `page_saas_dashboard()` |
| Kundenverwaltung | `modules/kundenverwaltung.py` | `page_kundenverwaltung()` |
| Benutzerverwaltung | `modules/benutzerverwaltung.py` | `page_benutzerverwaltung()` |
| Vereinsverwaltung | `modules/vereine.py` | `page_vereine()` |
| Lizenzverwaltung (SA) | `modules/lizenz_page.py` | `page_lizenz_superadmin()` |
| Lizenzverwaltung (VA) | `modules/lizenz_page.py` | `page_lizenz_vereinsadmin()` |
| Mein Vertrag | `modules/mein_vertrag.py` | `page_mein_vertrag()` |
| Abonnement / Checkout | `stripe_service.py` + `app.py` | `checkout_session_erstellen()` |
| Kündigung | `modules/mein_vertrag.py` | eingebettet in Vertragsseite |
| Zahlungsprobleme | `app.py:1420+` | Payment-Failure-Banner |
| Trainerportal | `modules/trainerportal.py` | `page_trainerportal()` |

---

## B0.12 TECHNISCHE SCHULDEN / DUPLIKATE

| # | Problem | Risiko | Handlungsbedarf |
|---|---------|--------|----------------|
| 1 | **Kein Schutz letzter Superadmin** | 🔴 KRITISCH | B1.1 |
| 2 | **Vertragsdaten doppelt** in `vereine` + `benutzer` | 🟡 mittel | B2.1 |
| 3 | **Legacy-Paketnamen** (BASIC, PRO, Enterprise) parallel zu neuen | 🟡 mittel | B2/Doku |
| 4 | **Kundennummern** nicht atomar, kein UNIQUE-Index | 🟡 mittel | B2.2 |
| 5 | **`stripe_events`** nur im API-Server sichtbar | 🟡 mittel | Doku/B7 |
| 6 | **FK/Cascade-Inkonsistenz** (lizenz_warn_log CASCADE, andere nicht) | 🟡 mittel | B1.3 |
| 7 | **Fail-open** bei Limitprüfungs-Exceptions | 🟡 mittel | B5.1 |
| 8 | **Legacy-Overrides** `max_trainer/max_spieler` in vereine | 🟡 mittel | B5.1 |
| 9 | **Downgrade-Schutz fehlt** | 🟡 mittel | B5.2 |
| 10 | **`subscription_current_period_end`** nicht persistent | 🟢 gering | B2/Doku |
| 11 | **Mandantentrennung** in DB-Funktionen unvollständig | 🟡 mittel | B1.3 |

---

## B0.13 GAP-ANALYSE

| Funktion | Status | Vorhandene Datei/Funktion | Problem | Handlungsbedarf |
|----------|--------|--------------------------|---------|----------------|
| Superadmin-Erkennung | ✅ VORHANDEN | `database.py`, `app.py` | — | — |
| Superadmin-Seiten | ✅ VORHANDEN | `modules/kundenverwaltung.py` etc. | — | — |
| **Letzter-Superadmin-Schutz** | ❌ FEHLT | — | Löschen/Deaktivieren möglich | B1.1 |
| Cascade-Delete-Schutz SA | ⚠️ RISIKO | `database.py:2912` | nur Benutzer-check | B1.1 |
| Rolleneskalations-Schutz | 🟡 TEILWEISE | UI-Guards | kein serverseitiger Layer | B1.2 |
| Mandantentrennung (UI) | ✅ VORHANDEN | diverse Filter | — | — |
| Mandantentrennung (DB) | 🟡 TEILWEISE | `spieler_mandant_pruefen()` | nicht alle DB-Fns | B1.3 |
| Kundenverwaltung | ✅ VORHANDEN | `kundenverwaltung.py` | — | prüfen vs B3-Spec |
| Kundenliste mit Filtern | 🟡 TEILWEISE | `kundenverwaltung.py` | Filter unvollständig | B3.2 |
| Kundennummer-Architektur | ⚠️ RISIKO | `database.py:4771` | kein UNIQUE, nicht atomar | B2.2 |
| Vertragsquelle führend | 🟡 TEILWEISE | `vereine` weitgehend führend | Doppelfelder in benutzer | B2.1 |
| Benutzerverwaltung | ✅ VORHANDEN | `benutzerverwaltung.py` | — | gegen B4.2-Spec prüfen |
| Lizenzsystem | ✅ VORHANDEN | `license.py` | — | — |
| Paketlimits serverseitig | 🟡 TEILWEISE | `license.py` | fail-open, Legacy-Overrides | B5.1 |
| **Downgrade-Schutz** | ❌ FEHLT | — | kein Nutzungs-Check | B5.2 |
| Feature-Rechte | ✅ VORHANDEN | `feature_erlaubt()` | — | — |
| Sperren / Entsperren | ✅ VORHANDEN | `kundenverwaltung.py` | — | — |
| Trial-Verwaltung (SA sieht) | ✅ VORHANDEN | `kundenverwaltung.py` | — | — |
| Trial-Verlängerung + Stripe-Sync | ❌ FEHLT | — | nur lokale DB | B6.3 |
| Audit-Log | ✅ VORHANDEN | `audit_log`-Tabelle | — | Aktionsabdeckung prüfen |
| SA-Aktionen in Audit | 🟡 TEILWEISE | `audit_log` | nicht alle SA-Aktionen geloggt | B7.1 |
| Kunden löschen (sicher) | ✅ VORHANDEN | 2-Stufen-Bestätigung | Stripe-Abo-Check? | B7.2 |
| stripe_events (Python sichtbar) | ⚠️ RISIKO | nur API-Server | Python-App kennt Tabelle nicht | Doku |

---

## B0.14 ANGEPASSTER PLAN B1–B8

Basierend auf der Bestandsaufnahme — nur tatsächlich fehlende oder mangelhafte Funktionen implementieren:

### B1 – SUPERADMIN-SCHUTZ / ROLLEN / MANDANTENTRENNUNG
**Schwerpunkt:** Kritischer Schutz des letzten Superadmins

- **B1.1** Guard in `benutzer_loeschen()` und `benutzer_aktivieren()` in `database.py`: wenn `rolle='Superadmin'` und aktive Superadmins ≤ 1 → blockieren mit klarer Fehlermeldung
- **B1.2** Rolleneskalation: UI verhindert Trainer→Superadmin bereits; Vereinsadmin-Rechte prüfen; kein neuer Layer nötig, aber prüfen ob `benutzer_aktualisieren()` die Zielrolle validiert
- **B1.3** Mandantentrennung: `benutzer_aktualisieren()` und vergleichbare DB-Funktionen um Mandantenprüfung ergänzen; bestehende `spieler_mandant_pruefen()` als Vorbild nutzen

**Umfang:** Chirurgisch, nur 2–3 DB-Funktionen.

### B2 – KUNDEN- UND VERTRAGSDATENMODELL
**Schwerpunkt:** Architektur klären, nicht umbauen

- **B2.1** Vertragsdaten: dokumentieren welche Felder in `vereine` führend sind; Legacy-Felder in `benutzer` nicht blind löschen; ggf. Lesezugriff auf `benutzer`-Felder auf `vereine` umleiten wo sinnvoll
- **B2.2** Kundennummer: UNIQUE-Index auf `vereine.kundennummer` und `benutzer.kundennummer` hinzufügen (idempotente Migration); Vergabe-Funktion transaktionssicher machen

### B3 – SUPERADMIN DASHBOARD / KUNDENVERWALTUNG
**Schwerpunkt:** Bestehendes erweitern, nicht ersetzen

- **B3.1** SaaS-Dashboard gegen B3.1-Spec prüfen: fehlende KPIs (gesperrte Kunden, Trial-Anzahl, Kündigungen 30 Tage) ergänzen
- **B3.2** Kundenliste: fehlende Filter (Trial, gesperrt, Zahlungsstatus) ergänzen; bestehende Suchfunktion erweitern

### B4 – KUNDENDETAIL / BENUTZERVERWALTUNG
**Schwerpunkt:** Lücken schließen

- **B4.1** Kundendetail gegen B4.1-Spec prüfen: Stripe-Info-Block (Customer JA/NEIN, Subscription Status, cancel_at_period_end) mit gekürzten IDs
- **B4.2** Benutzerverwaltung: E-Mail-Verifikations-Status aus Spec vs. Bestand prüfen; `subscription_current_period_end` persistieren

### B5 – PAKETLIMITS / FEATURE-RECHTE / DOWNGRADE
**Schwerpunkt:** Downgrade-Schutz implementieren

- **B5.1** Fail-open schließen: bei Exception in Limitprüfung → fail-closed (blockieren, nicht erlauben); Legacy-Override-Felder (`max_trainer`, `max_spieler`) ignorieren oder mit Paketdefinition synchronisieren
- **B5.2** Downgrade-Schutz: vor Paketdowngrade Nutzung gegen Ziel-Limits prüfen; bei Überschreitung blockieren mit Klarmeldung (Trainer X/Y, Spieler X/Y)

### B6 – SUPPORTAKTIONEN / SPERREN / TRIAL
**Schwerpunkt:** Trial-Verlängerung

- **B6.1/B6.2** Sperren/Entsperren/Supportaktionen: bereits vorhanden, gegen Spec validieren
- **B6.3** Trial-Verlängerung: falls implementiert, Stripe-API-Sync erforderlich (nicht nur lokale DB); vorerst dokumentieren und bei Bedarf implementieren

### B7 – AUDIT / SICHERHEIT
**Schwerpunkt:** Vollständigkeit

- **B7.1** Audit-Coverage: alle Superadmin-Supportaktionen (sperren, entsperren, Trial, Deaktivierung, Rollen) müssen in `audit_log` erscheinen; fehlende Einträge ergänzen
- **B7.2** Kunden löschen: prüfen ob Stripe-Abo-Check vor Löschung existiert; falls nicht → ergänzen

### B8 – END-TO-END-TESTS
- 25-Testplan durchführen (interne Tests) + VPS-Tests dokumentieren

---

## KRITISCHE PROBLEME — ENTSCHEIDUNG

### ⚠️ KRITISCH (B1 sofort, vor allem anderen)
**Fehlender Letzter-Superadmin-Schutz.**
Es gibt bereits einen dokumentierten Produktionszwischenfall.
B1 muss zuerst implementiert werden.

### 🟡 MITTEL (kein Stopp, aber früh in B1/B2)
- Kundennummern-UNIQUE-Index: sicher idempotent, kein Datenverlustrisiko
- Vertragsdaten-Dopplung: nur Klärung/Doku, kein Umbau

**Empfehlung:** Kein Stopp. Mit B1 fortfahren.

---

*Ende B0-Bestandsaufnahme*
