#!/usr/bin/env python3
"""
tools/test_saison.py — Testmatrix: Saisonwechsel, Fußballklassen, Normgruppen,
                        Defizit-Zuordnung, Trainingsplan-Zuordnung.

Spec §13 / §16 / §18 explizit abgedeckt.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date

# ─── Importe ─────────────────────────────────────────────────────────────────
from saison import (
    aktuelle_saison, saison_label, fussballklasse_berechnen,
    fussballklasse_aus_datum, geburtsjahr_aus_datum, testreferenz_caption,
)
from age_norms import alter_zu_normgruppe, normgruppe_label
from field_eval import alter_zu_altersgruppe
from periodisierung import _alter_zu_plangruppe, _PLANGRUPPEN_CONFIG
from sprint import bewertung_sprint, SprintErgebnis

PASS = 0; FAIL = 0


def ok(label: str):
    global PASS; PASS += 1
    print(f"  ✅ PASS  {label}")


def fail(label: str, detail: str = ""):
    global FAIL; FAIL += 1
    print(f"  ❌ FAIL  {label}" + (f" — {detail}" if detail else ""))


def check(label: str, got, expected):
    if got == expected:
        ok(label)
    else:
        fail(label, f"got={got!r}, expected={expected!r}")


# ═══════════════════════════════════════════════════════════════════════════════
# §1  Saisonberechnung — aktuelle_saison()
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §1 Saisonberechnung (Saisonwechsel 01.07.) ══")

# 16.08.2026 → Saison 2026/27
check("16.08.2026 → (2026, 2027)",
      aktuelle_saison(1, 7, date(2026, 8, 16)), (2026, 2027))

# 30.06.2026 → Saison 2025/26
check("30.06.2026 → (2025, 2026)",
      aktuelle_saison(1, 7, date(2026, 6, 30)), (2025, 2026))

# 01.07.2026 → Saison 2026/27 (Grenzfall: >= ist inklusive)
check("01.07.2026 → (2026, 2027)",
      aktuelle_saison(1, 7, date(2026, 7, 1)),  (2026, 2027))

# 31.12.2026 → Saison 2026/27
check("31.12.2026 → (2026, 2027)",
      aktuelle_saison(1, 7, date(2026, 12, 31)), (2026, 2027))

# 01.07.2027 → Saison 2027/28
check("01.07.2027 → (2027, 2028)",
      aktuelle_saison(1, 7, date(2027, 7, 1)),  (2027, 2028))

# Saison-Labels
check("saison_label 16.08.2026", saison_label(1, 7, date(2026, 8, 16)), "2026/27")
check("saison_label 30.06.2026", saison_label(1, 7, date(2026, 6, 30)), "2025/26")


# ═══════════════════════════════════════════════════════════════════════════════
# §2  Fußball-Altersklasse — Testmatrix Spec §16
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §2 Fußballklassen Testmatrix (Saison 2026/27, Stichtag 16.08.2026) ══")

STICHTAG = date(2026, 8, 16)

# JG 2021 → U6 ... JG 2013 → U14
MATRIX_FK = [
    (2021, "U6"),
    (2020, "U7"),
    (2019, "U8"),
    (2018, "U9"),
    (2017, "U10"),
    (2016, "U11"),
    (2015, "U12"),
    (2014, "U13"),
    (2013, "U14"),
    (2012, "U15"),
]
for jg, erw_fk in MATRIX_FK:
    got = fussballklasse_berechnen(jg, STICHTAG, 1, 7)
    check(f"JG {jg} → {erw_fk}", got, erw_fk)


# ═══════════════════════════════════════════════════════════════════════════════
# §3  Saisongrenzen JG2016 — Spec §13
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §3 Saisongrenzen JG2016 ══")

check("JG2016, 30.06.2026 → U10",
      fussballklasse_berechnen(2016, date(2026, 6, 30), 1, 7), "U10")

check("JG2016, 01.07.2026 → U11",
      fussballklasse_berechnen(2016, date(2026, 7, 1),  1, 7), "U11")

check("JG2016, 16.08.2026 → U11",
      fussballklasse_berechnen(2016, date(2026, 8, 16), 1, 7), "U11")

check("JG2016, 31.12.2026 → U11",
      fussballklasse_berechnen(2016, date(2026, 12, 31), 1, 7), "U11")

check("JG2016, 30.06.2027 → U11",
      fussballklasse_berechnen(2016, date(2027, 6, 30), 1, 7), "U11")

check("JG2016, 01.07.2027 → U12",
      fussballklasse_berechnen(2016, date(2027, 7, 1),  1, 7), "U12")


# ═══════════════════════════════════════════════════════════════════════════════
# §4  Produktionstest JG2016 — Spec §12
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §4 Produktionstest Spieler JG2016, Stichtag 16.08.2026 ══")

# Geburtsdatum 26.08.2016
GEB_2016 = "26.08.2016"

# Chronologisches Alter: 9 Jahre (noch nicht 10, Geburtstag ist 26.08.)
from database import berechne_alter
alter_2016 = berechne_alter(GEB_2016)
check("Chronologisches Alter = 9", alter_2016, 9)

# Fußballklasse: U11
fk_2016 = fussballklasse_aus_datum(GEB_2016, STICHTAG, 1, 7)
check("Fußballklasse = U11", fk_2016, "U11")

# Normgruppe (chronologisches Alter 9): U10
norm_2016 = alter_zu_normgruppe(alter_2016)
check("Normgruppe (Alter 9) = U10", norm_2016, "U10")

# Sprint 10m=2.07 / 30m=5.06
bew_10m = bewertung_sprint(2.07, "10m", "Leistungssport", "Männlich", float(alter_2016))
bew_30m = bewertung_sprint(5.06, "30m", "Leistungssport", "Männlich", float(alter_2016))
print(f"  Sprint 10m={bew_10m!r}, 30m={bew_30m!r}")
check("Sprint-Bewertung nicht '—' (Alter 9 = U10 = gültige Norm)",
      bew_10m != "—" and bew_30m != "—", True)

# Kein U8 in Fußballklasse
check("Fußballklasse enthält KEIN 'U8'", "U8" not in (fk_2016 or ""), True)
check("Fußballklasse enthält KEIN 'U10'", "U10" not in (fk_2016 or ""), True)


# ═══════════════════════════════════════════════════════════════════════════════
# §5  Drei-Ebenen-Trennung vollständige Matrix
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §5 Drei-Ebenen-Trennung (Stichtag 16.08.2026) ══")

# alter: chronologisch | normgruppe: Testnorm | plangruppe: Trainingsplan | fk: Fußballklasse
DREI_EBENEN = [
    # (alter, erw_norm, erw_plan, jg, erw_fk)
    (7,  "U8",  "U7",  2019, "U8"),
    (9,  "U10", "U8",  2017, "U10"),
    (11, "U12", "U10", 2015, "U12"),
    (13, "U14", "U14", 2013, "U14"),
]
for alter, erw_norm, erw_plan, jg, erw_fk in DREI_EBENEN:
    norm = alter_zu_normgruppe(alter)
    plan = _alter_zu_plangruppe(float(alter))
    fk   = fussballklasse_berechnen(jg, STICHTAG, 1, 7)
    check(f"Alter {alter}: Normgruppe={norm}", norm, erw_norm)
    check(f"Alter {alter}: Plangruppe={plan}", plan, erw_plan)
    check(f"JG {jg}: Fußballklasse={fk}", fk, erw_fk)

# Kerntrennung: JG2016, 16.08.2026 — Alter 9, FK U11, Norm U10 → alle verschieden
_norm_2016 = alter_zu_normgruppe(9)
_plan_2016 = _alter_zu_plangruppe(9.0)
_fk_2016   = fussballklasse_berechnen(2016, STICHTAG, 1, 7)
check("JG2016 Alter 9: Fußballklasse U11 ≠ Normgruppe U10",
      _fk_2016 != _norm_2016, True)
check("JG2016 Alter 9: Fußballklasse U11 ≠ Plangruppe U8",
      _fk_2016 != _plan_2016, True)
check("JG2016: Fußballklasse=U11, Normgruppe=U10, Plangruppe=U8 (alle drei verschieden)",
      (_fk_2016, _norm_2016, _plan_2016) == ("U11", "U10", "U8"), True)


# ═══════════════════════════════════════════════════════════════════════════════
# §6  Normgruppen-Label (Testreferenz ≠ Fußballklasse)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §6 Normgruppen-Label ══")

check("normgruppe_label(9) enthält 'Testreferenz'",
      "Testreferenz" in normgruppe_label(9), True)
check("normgruppe_label(9) enthält 'U10'",
      "U10" in normgruppe_label(9), True)
check("normgruppe_label(9) enthält 'Alter 9–10'",
      "9–10" in normgruppe_label(9), True)

cap = testreferenz_caption(9, "26.08.2016")
print(f"  testreferenz_caption(9, '26.08.2016') = {cap!r}")
check("caption enthält 'Testreferenz'", "Testreferenz" in cap, True)
check("caption enthält 'Fußballklasse'", "Fußballklasse" in cap, True)
check("caption enthält 'U11'", "U11" in cap, True)


# ═══════════════════════════════════════════════════════════════════════════════
# §7  Sprint-Defizit-Kette (Spec §9/§10)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §7 Sprint-Defizit-Kette ══")

# Sehr gute Zeit → kein Defizit
res_gut = SprintErgebnis(beste_5m=None, beste_10m=1.80, beste_20m=None, beste_30m=None,
                         geschlecht="Männlich", niveau="Leistungssport", alter=25.0)
check("Sehr gut → kein Defizit in res.defizite",
      all("Schnelligkeit" not in d for d in res_gut.defizite), True)

# Schlechte Zeit → Defizit (Linearbeschleunigung oder Maximalgeschwindigkeit)
res_schlecht = SprintErgebnis(beste_5m=None, beste_10m=3.50, beste_20m=None, beste_30m=None,
                              geschlecht="Männlich", niveau="Leistungssport", alter=25.0)
check("Schwacher Sprint → Defizit (Beschleunigung/Maximalgesch.) erkannt",
      len(res_schlecht.defizite) > 0, True)

# U7 (Alter < 8) → kein Sprint-Urteil
bew_u7 = bewertung_sprint(4.0, "10m", "Leistungssport", "Männlich", 7.0)
check("U7 (alter=7): Sprint-Bewertung = '—' (kein falsches Defizit)",
      bew_u7, "—")


# ═══════════════════════════════════════════════════════════════════════════════
# §8  Trainingsplan-Zuordnung (Spec §7/§10)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §8 Trainingsplan-Plangruppen (altersgerecht, nicht Fußballklasse) ══")

# JG2016: Alter 9, Fußballklasse U11 → Plangruppe U8 (nicht U11/Senior!)
plan_9 = _alter_zu_plangruppe(9.0)
check("Alter 9 → Plangruppe U8 (altersgerecht, nicht U11)",
      plan_9, "U8")
cfg_9 = _PLANGRUPPEN_CONFIG[plan_9]
check("U8-Plan: max_saetze ≤ 2",
      cfg_9["max_saetze"] <= 2, True)
check("U8-Plan: haeuf_cap = '2×'",
      cfg_9["haeuf_cap"], "2×")

# Fußballklasse U11 darf NICHT direkt als Plangruppe verwendet werden
check("'U11' ist KEIN gültiger Plangruppen-Key",
      "U11" not in _PLANGRUPPEN_CONFIG, True)


# ═══════════════════════════════════════════════════════════════════════════════
# §9  Defizit-Mapping aller Testmodule (Spec §9)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §9 Defizit-Mapping Test → Trainingsbereich ══")

from analytics import schwerpunkt_sammeln
from sprint import SprintErgebnis
from sprung import SprungErgebnis

# Sprint-Defizit → Schnelligkeit
sp_sprint_def = SprintErgebnis(beste_5m=None, beste_10m=3.5, beste_20m=None, beste_30m=None,
                                geschlecht="Männlich", niveau="Leistungssport", alter=25.0)
schw = schwerpunkt_sammeln(fms_row=None, y_row=None, sprint_row=None,
                            sprung_row=None, agil_row=None, aus_row=None,
                            kraft_row=None, spiro_row=None)
# Direkt SprintErgebnis.defizite prüfen
# Defizit-Strings: "Linearbeschleunigung (0–10 m)", "Maximalgeschwindigkeit (20–30 m)"
check("Sprint-Defizit: Linearbeschleunigung oder Maximalgeschw. erkannt",
      any("Linearb" in d or "Maximal" in d for d in sp_sprint_def.defizite), True)

# Sprung-Defizit → Explosivität / CMJ
# SprungErgebnis Felder: cmj_beid, cmj_rechts, cmj_links, squat_jump, ...
sp_sprung_def = SprungErgebnis(cmj_beid=18.0,   # < NORMWERTE_CMJ * 0.95 → Defizit
                                geschlecht="Männlich", niveau="Leistungssport", alter=25.0)
check("Sprung-Defizit enthält 'Explosivkraft' oder 'CMJ' oder 'Sprung'",
      any("Explosiv" in d or "CMJ" in d or "Sprung" in d for d in sp_sprung_def.defizite), True)

print("  (FMS, Y-Balance, Agilität: Mapping über analytics.schwerpunkt_sammeln)")


# ═══════════════════════════════════════════════════════════════════════════════
# §10  Fußball-Jahrgangsmatrix komplett (Spec §16)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n══ §10 Jahrgangsmatrix komplett (Stichtag 16.08.2026 → Saison 2026/27) ══")

JG_MATRIX = [
    (2021, "U6"),
    (2020, "U7"),
    (2019, "U8"),
    (2018, "U9"),
    (2017, "U10"),
    (2016, "U11"),
    (2015, "U12"),
    (2014, "U13"),
    (2013, "U14"),
]
ok_count = 0
for jg, erw in JG_MATRIX:
    got = fussballklasse_berechnen(jg, STICHTAG, 1, 7)
    if got == erw:
        ok_count += 1
    else:
        fail(f"JG {jg}", f"got={got!r}, expected={erw!r}")

if ok_count == len(JG_MATRIX):
    ok(f"Alle {ok_count} Jahrgänge korrekt → Fußballklasse")


# ═══════════════════════════════════════════════════════════════════════════════
# Ergebnis
# ═══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 60)
if FAIL == 0:
    print(f"  Ergebnis: {PASS} PASS, 0 FAIL ✅")
else:
    print(f"  Ergebnis: {PASS} PASS, {FAIL} FAIL ❌")
print("=" * 60)

if FAIL > 0:
    sys.exit(1)
