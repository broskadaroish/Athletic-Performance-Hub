---
name: Saison-Alterssystem
description: Drei sauber getrennte Altersebenen in APH — Fußballklasse, chronologisches Alter, Normgruppe
---

## Drei Altersebenen (Single Source of Truth)

| Ebene | Berechnung | Quelle | Verwendung |
|---|---|---|---|
| Fußball-Altersklasse | `saison.fussballklasse_berechnen(jg, stichtag, sw_tag, sw_monat)` | Geburtsjahr + Saisonwechsel | Nur UI-Anzeige |
| Chronologisches Alter | `database.berechne_alter(geburtsdatum)` | Geburtsdatum + heute | Testnormen, Belastungssteuerung |
| Normgruppe | `age_norms.alter_zu_normgruppe(alter)` | Chronologisches Alter | Sprint/Sprung/Agil-Normen |
| Plangruppe | `periodisierung._alter_zu_plangruppe(alter)` | Chronologisches Alter | Trainingsplan |

## Berechnungsregel Fußballklasse
U = Saison-Endjahr − Geburtsjahr
Saisonwechsel default: 01.07. (gespeichert in app_einstellungen: saisonwechsel_tag, saisonwechsel_monat)
Wenn heute >= Saisonwechsel: Saison = (heute.year, heute.year+1)
Wenn heute <  Saisonwechsel: Saison = (heute.year-1, heute.year)

## Beispiel (Stichtag 16.08.2026, Saisonwechsel 01.07.)
JG2016: Alter=9, Fußballklasse=U11, Normgruppe=U10, Plangruppe=U8 → alle drei verschieden

## Kernmodule
- `saison.py` (neu): aktuelle_saison, fussballklasse_berechnen, fussballklasse_aus_datum, saisonwechsel_laden/speichern, testreferenz_caption
- `age_norms.normgruppe_label()`: zeigt jetzt "Testreferenz: U10 (Alter 9–10)" statt "Referenz: U10 (Fußball)"
- `app.py`: Player-Profil-Header zeigt Fußballklasse+Saison+Jahrgang dynamisch (nicht aus gespeichertem altersklasse-Feld)
- `app.py page_einstellungen`: Saisonwechsel-Block (Tag + Monat + aktuelle Saison preview)
- Alle Testseiten (Sprint/FMS/Sprung/Agil/Kraft): Caption zeigt "Testreferenz: U10 (Alter 9–10) · Fußballklasse: U11 (Saison 2026/27)"

**Why:** Fußball-U-Klasse (jahrgangsbasiert) und wissenschaftliche Testnorm (altersbasiert) sind konzeptuell verschieden. Ein 9-Jähriger in Saison 2026/27 hat Fußballklasse U11 aber Testnorm U10.

## DB-Änderung
KEINE — app_einstellungen-Tabelle existiert bereits und wird wiederverwendet.
Schlüssel: "saisonwechsel_tag" (int), "saisonwechsel_monat" (int), Default 1/7.

## Testdatei
tools/test_saison.py — 60 PASS, 0 FAIL
