---
name: Ausdauer Alters-Logik + Defizit
description: Yo-Yo-Normgruppen-Ableitung, altersgerechte VO₂max-Schwellen, Ausdauer als eigener Trainingsbereich
---

## Kernregeln

**FK primär für Yo-Yo-Gruppe:**
- `fussballklasse_zu_yoyo_gruppe(fk, alter)` in `ausdauer.py` — FK hat Vorrang, Alter ist Fallback
- `_FK_ZU_YOYO_GRUPPE` enthält auch A/B/C/D/E/F-Junioren und Bambini
- Generischer Fallback für unbekannte U-Klassen via Nummer-Parsing

**Alters-Fallback (U-Logik-konsistent):**
```
alter ≤ 8  → "U8/U9"
alter 9–10 → "U10/U11"   ← vorheriger Bug: 9 → "U8/U9"
alter 11–12→ "U12/U13"
alter 13   → "U13/U14"   ← vorheriger Bug: wurde übersprungen
alter 14–15→ "U15/U16"
alter 16–17→ "U17/U18"
alter 18+  → "Senioren"
```

**Why:** Das frühere `alter < 10` → "U8/U9" war falsch; U-Logik sagt alter=9 spielt in U10 → Testreferenz U10/U11.

**VO₂max altersgerecht:**
- `_yoyo_gruppe_zu_normgruppe()` konvertiert "U10/U11" → "U10" für `_VO2_NORMEN_M/W` aus `age_norms.py`
- Schwellen in `analytics.py` und `AusdauerErgebnis.defizite` nutzen die gespeicherte `altersgruppe`-Spalte — keine Geburtstag-Durchreichung nötig
- Kritisch: `vo2max < norm * 0.85`; Warnung: `vo2max < norm`

**Ausdauer ≠ Fußball in defizit_score:**
- Keywords "ausdauer/aerob/intermittier/yo-yo" → Bereich **"Ausdauer"** (eigener Pool)
- Keywords "fußball/fussball" → Bereich **"Fußball"** (Ball-spezifische Übungen)
- `_AUSDAUER_POOL`: Jugend (U7–U10, spielerisch), Mittel (U14, 15:15/30:30), Senior (GA1/GA2/RSA)
- Generator in `periodisierung.py`: `if area == "Ausdauer": _ausdauer_pool_fuer_plangruppe(plangruppe, ...)`

**How to apply:**
- Beim Speichern eines Yo-Yo-Tests: `altersgruppe`-Feld aus `fussballklasse_zu_yoyo_gruppe()` befüllen
- Bei VO₂max-Bewertung immer gespeicherte `altersgruppe` lesen, nie Alter neu berechnen
- `defizit_score()` trennt jetzt Ausdauer von Fußball → Plan erzeugt korrekte aerobe Übungen
- `AusdauerErgebnis.defizite` gibt `["Aerobe Kapazität (VO₂max...)"]`; in analytics.py liefert `d["modul"] == "Ausdauer"` (nicht `d["bereich"]`)

## Testdateien
- `tools/test_ausdauer_alterslogik.py` — 37 Tests: FK-Mapping, Alters-Fallback, Robustheit
- `tools/test_ausdauer_defizit.py` — 8 Tests: AusdauerErgebnis.defizite + defizite_ermitteln()
- `tools/test_ausdauer_trainingsplan.py` — 23 Tests: defizit_score, Pool, trainingsplan_multi_erstellen

## Bekannte Fallstricke
- `test_b1_guards.py` schlägt mit "no such table: sessions" fehl — pre-existing, nutzt eigenes Minimal-Schema ohne Sessions-Tabelle; NICHT durch diese Änderungen verursacht
- `AusdauerErgebnis.vo2max` und `.bewertung` sind Properties — nicht als Konstruktor-Argumente übergeben
- `trainingsplan_multi_erstellen` schreibt in `trainingsplan`-Tabelle (nicht `trainingsplan_eintraege`)
