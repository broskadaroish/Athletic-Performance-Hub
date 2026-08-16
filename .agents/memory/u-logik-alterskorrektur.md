---
name: U-Logik Alterskorrektur
description: "U = unter: Alter 9 (unter 10) → U10, nicht U8. Alle drei U-Zuordnungs-Funktionen wurden angeglichen."
---

## Die Regel
**U = unter**: Ein 9-jähriger Spieler ist "unter 10" = U10. Ein 7-jähriger ist "unter 8" = U8.

Diese Definition war in drei Stellen falsch implementiert (off-by-one um 1 Jahr):

### Korrigierte Grenzen

| Funktion | Datei | Alt | Neu |
|---|---|---|---|
| `alter_zu_altersgruppe()` | field_eval.py | `alter < 10 → "U8"` | `alter < 9 → "U8"`, `alter < 11 → "U10"` |
| `_alter_zu_plangruppe()` | periodisierung.py | `a <= 9 → "U8"` | `a <= 8 → "U8"`, `a <= 11 → "U10"` |
| `altersklasse_vorschlag()` | database.py | chronol. Alter | saisonal via `fussballklasse_aus_datum()` |

### Neue Funktion
`jugendklasse_aus_fussballklasse(fk)` in `saison.py`: "U11" → "U10/U11 (E-Jugend)"

### Nicht verändert
- `age_norms.alter_zu_normgruppe()` — war bereits korrekt (`a <= 8 → U8`, `a <= 10 → U10`)
- `saison.py fussballklasse_aus_datum()` — war bereits korrekt

## Why
Der Fehler führte dazu, dass 9-jährige Spieler die U8-Testreferenz, U8-Trainingsplan und "U8/U9 (F-Jugend)" als Altersklassen-Vorschlag bekamen, obwohl sie in der Saison 2026/27 Fußballklasse U11 (E-Jugend) spielen.

## How to apply
- Bei neuen U-Grenzen immer prüfen: "Alter N" = "unter N+1" = "UN+1"
- Alle drei Funktionen (`alter_zu_altersgruppe`, `_alter_zu_plangruppe`, `altersklasse_vorschlag`) müssen dieselbe Logik haben
- U7 = Alter ≤ 6 (unter 7), U8 = Alter 7–8, U10 = Alter 9–10, U12 = Alter 11–12 usw.
- `tools/test_ulogik.py` deckt die gesamte U-Logik-Matrix ab — bei jeder Änderung pflichtmäßig ausführen
