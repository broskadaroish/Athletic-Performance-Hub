"""
Zentrale Testanleitungen — Football Athletik Diagnostik.
Version 1.1 — alle 7 Test-Module vollständig befüllt.
"""
from __future__ import annotations

SICHERHEITSHINWEIS_ALLGEMEIN = (
    "Der Test ist sofort abzubrechen, wenn Schmerzen, Schwindel, Atemnot, "
    "Brustschmerzen, ungewöhnliche Schwäche oder andere auffällige Beschwerden "
    "auftreten. Die App bewertet keine medizinischen Beschwerden."
)

COMPLIANCE_HINWEIS = (
    "Diese Testanleitung dient der standardisierten sportlichen Durchführung und "
    "Dokumentation. Sie stellt keine medizinische Untersuchung, Diagnose oder "
    "Freigabe dar."
)

TEST_HELP: dict[str, dict] = {

    # ══════════════════════════════════════════════════════════════════════════
    # SPRINT
    # ══════════════════════════════════════════════════════════════════════════
    "sprint": {
        "name": "Sprint-Diagnostik",
        "kurzbeschreibung": "Lineare Beschleunigung und Maximalgeschwindigkeit über 5 m, 10 m, 20 m und 30 m — je 3 Versuche.",
        "ziel": (
            "Überprüfung der Beschleunigungsfähigkeit (0–10 m), der Übergangsphase "
            "(10–20 m) und der Maximalgeschwindigkeit (20–30 m). "
            "Der Beschleunigungsindex zeigt das Verhältnis von Startexplosivität zu Maximalgeschwindigkeit."
        ),
        "material": "Maßband oder vormarkierte Strecke, Hütchen (5 Stück), Lichtschranken oder Stoppuhr.",
        "aufbau": (
            "Startlinie markieren. Hütchen bei 5 m, 10 m, 20 m und 30 m aufstellen. "
            "Wenn vorhanden, Lichtschranken an den Messpunkten aufbauen. "
            "Untergrund muss eben, trocken und rutschfest sein. "
            "Hinter der 30-m-Linie mindestens 10 m Auslauffläche sicherstellen."
        ),
        "aufwaermung": (
            "Mindestens 10 Minuten allgemeines Aufwärmen. "
            "Anschließend 2–3 Steigerungsläufe über 30–40 m mit steigender Intensität (70 %, 85 %, 95 %). "
            "Kurze Sprung- und Aktivierungsübungen empfohlen."
        ),
        "durchfuehrung": (
            "Spieler startet selbstständig aus dem Stand hinter der Startlinie. "
            "Maximale Beschleunigung über die gesamte Strecke. "
            "Spieler läuft vollständig durch alle Messpunkte ohne abzubremsen. "
            "3 Versuche je Distanz mit ausreichend Erholungszeit."
        ),
        "trainerhinweis": (
            "Spieler muss deutlich hinter der Startlinie beginnen (mind. 30 cm). "
            "Keine Vor- oder Ausholbewegung vor dem Start zulässig. "
            "Spieler muss vollständig durch das Ziel laufen. "
            "Bei Lichtschranken: ganzer Körper muss passieren, nicht nur der vorgestreckte Arm."
        ),
        "versuche": "3 Versuche je Distanz. Der schnellste gültige Versuch wird gewertet.",
        "pause": "2–3 Minuten aktive Pause (lockeres Gehen) zwischen den Versuchen.",
        "messwert": "Zeit in Sekunden",
        "einheit": "Sekunden (s)",
        "gueltiger_versuch": "Korrekter Start hinter der Linie, maximale Beschleunigung, vollständiges Durchlaufen des Ziels.",
        "ungueltiger_versuch": "Frühstart, Ausrutschen, vorzeitiges Abbremsen, Behinderung, Ausholbewegung.",
        "fehler": [
            "Ausholbewegung vor dem Start — verfälscht die Startzeit",
            "Abbremsen kurz vor dem Ziel — gibt zu kurze gemessene Endzeit",
            "Arm beim Durchlaufen einer Lichtschranke vorstrecken — unrealistisch kurze Zeit",
            "Zu kurze Pause zwischen den Versuchen — Ermüdung verfälscht das Ergebnis",
        ],
        "sicherheit": (
            "Testfläche auf Nässe, Unebenheiten und Hindernisse prüfen. "
            "Mindestens 10 m Auslauffläche hinter der 30-m-Linie. "
            "Spieler bei Beschwerden sofort stoppen lassen."
        ),
        "bild_pfad": "assets/tests/sprint/sprint_setup.svg",
        "quelle": "Sporis et al. (2010); Stolen et al. (2005)",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None, "video_link": None, "video_titel": None, "video_quelle": None, "video_lizenz": None,
        "felder": {
            "sprint_5m":  {"label": "5 m",  "ziel": "Startexplosivität — erste Beschleunigungsschritte.", "kurzhilfe": "Schnellste Zeit über 5 m eintragen. 3 Versuche — bester zählt.", "eingabehilfe": "Zeit in Sekunden, z. B. 1.05", "einheit": "s", "bereich": "Sinnvoll: 0.90 – 1.60 s"},
            "sprint_10m": {"label": "10 m", "ziel": "Beschleunigungsleistung — 0 bis 10 Meter.", "kurzhilfe": "Schnellste Zeit über 10 m. Muss größer als 5-m-Zeit sein.", "eingabehilfe": "Zeit in Sekunden, z. B. 1.78", "einheit": "s", "bereich": "Sinnvoll: 1.60 – 2.50 s"},
            "sprint_20m": {"label": "20 m", "ziel": "Übergangsphase von Beschleunigung zu Maximalgeschwindigkeit.", "kurzhilfe": "Schnellste Zeit über 20 m. Muss größer als 10-m-Zeit sein.", "eingabehilfe": "Zeit in Sekunden, z. B. 3.10", "einheit": "s", "bereich": "Sinnvoll: 2.80 – 4.00 s"},
            "sprint_30m": {"label": "30 m", "ziel": "Maximalgeschwindigkeit — Phase 20 bis 30 Meter.", "kurzhilfe": "Schnellste Zeit über 30 m. Muss größer als 20-m-Zeit sein.", "eingabehilfe": "Zeit in Sekunden, z. B. 4.50", "einheit": "s", "bereich": "Sinnvoll: 3.90 – 5.50 s"},
        },
    },

    # ══════════════════════════════════════════════════════════════════════════
    # Y-BALANCE
    # ══════════════════════════════════════════════════════════════════════════
    "y_balance": {
        "name": "Y-Balance-Test",
        "kurzbeschreibung": "Dynamische Standbeinbalance in drei Richtungen — bewertet Gleichgewicht und Beinachsenstabilität.",
        "ziel": (
            "Messung der dynamischen Gleichgewichtsfähigkeit auf einem Standbein. "
            "Composite Score ≥ 89 % gilt als sportlich unauffällig. "
            "Seitenunterschiede > 4 cm je Richtung gelten als trainingsrelevant."
        ),
        "material": "Y-Balance-Kit oder Klebeband-Markierungen auf dem Boden (3 Arme: 0°, 135°, 225°), Maßband.",
        "aufbau": (
            "Standfläche markieren. Drei Messarme aufkleben oder Y-Balance-Kit verwenden: "
            "Anterior (vorwärts, 0°), Posteromedial (schräg hinten-innen, ~135°), "
            "Posterolateral (schräg hinten-außen, ~225°). "
            "Arme mindestens 120 cm lang markieren."
        ),
        "aufwaermung": "5–10 Minuten allgemeines Aufwärmen, je 3–6 Übungsversuche je Richtung und Seite.",
        "durchfuehrung": (
            "Spieler steht auf einem Bein auf der Standfläche. "
            "Mit dem freien Fuß so weit wie möglich entlang des Messarms schieben, ohne aufzusetzen. "
            "Beinlänge (ASIS bis Innenknöchel) vorher messen und eintragen. "
            "3 Messungen je Richtung und Seite — bester Wert wird verwendet."
        ),
        "trainerhinweis": (
            "Standbein muss gerade bleiben (kein Strecken oder übermäßiges Beugen). "
            "Ferse des Standbeins muss auf der Markierung bleiben. "
            "Der Schiebefoot darf den Boden kurz berühren, aber nicht belasten. "
            "Arme dürfen zur Balance genutzt werden."
        ),
        "versuche": "3 gültige Versuche je Richtung und Seite. Bester Wert zählt.",
        "pause": "Kurze Pause zwischen den Seiten (30–60 Sekunden).",
        "messwert": "Reichweite in cm je Richtung (Anterior, Posteromedial, Posterolateral) je Seite",
        "einheit": "cm",
        "gueltiger_versuch": "Standbein stabil, Ferse auf Markierung, Schiebefoot berührt Boden nur kurz.",
        "ungueltiger_versuch": "Standbein hebt ab, Ferse verlässt Markierung, Schiebefoot wird belastet, Gleichgewichtsverlust.",
        "fehler": [
            "Standferse verlässt die Markierung — Reichweite erscheint größer als tatsächlich",
            "Kniegelenk des Standbeins zu stark strecken — verfälscht Gleichgewichtsanforderung",
            "Schiebefoot wird belastet — Test ist ungültig",
            "Beinlänge nicht korrekt gemessen — Composite Score stimmt nicht",
        ],
        "sicherheit": (
            "Rutschfester Untergrund erforderlich. "
            "Bei Knie-, Sprunggelenk- oder Hüftbeschwerden Test aussetzen. "
            "Spieler soll sich an einer Wand oder Person stabilisieren dürfen (dann als Übung werten)."
        ),
        "bild_pfad": "assets/tests/y_balance/ybalance_setup.svg",
        "quelle": "Gribble et al. (2012); Plisky et al. (2006)",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None, "video_link": None, "video_titel": None, "video_quelle": None, "video_lizenz": None,
        "felder": {
            "beinlaenge":     {"label": "Beinlänge", "ziel": "Normierungsbasis für den Composite Score.", "kurzhilfe": "Beinlänge in cm messen: ASIS (Beckenvorsprung) bis Innenknöchel bei gestrecktem Knie. Z. B. 87.5", "eingabehilfe": "Länge in cm, z. B. 87.5", "einheit": "cm", "bereich": "Sinnvoll: 50 – 95 cm"},
            "anterior":       {"label": "Anterior", "ziel": "Vorwärts-Gleichgewicht, Sprunggelenkmobilität.", "kurzhilfe": "Reichweite in Vorwärtsrichtung (anterior) in cm. Besten Versuch eintragen.", "eingabehilfe": "Reichweite in cm, z. B. 65.0", "einheit": "cm", "bereich": "Sinnvoll: 40 – 90 cm", "bild_pfad": "assets/tests/y_balance/anterior.svg"},
            "posteromedial":  {"label": "Posteromedial", "ziel": "Hintere mediale Gleichgewichtsstabilität.", "kurzhilfe": "Reichweite schräg hinten-innen in cm. Besten Versuch eintragen.", "eingabehilfe": "Reichweite in cm, z. B. 110.0", "einheit": "cm", "bereich": "Sinnvoll: 80 – 145 cm", "bild_pfad": "assets/tests/y_balance/posteromedial.svg"},
            "posterolateral": {"label": "Posterolateral", "ziel": "Hintere laterale Gleichgewichtsstabilität.", "kurzhilfe": "Reichweite schräg hinten-außen in cm. Besten Versuch eintragen.", "eingabehilfe": "Reichweite in cm, z. B. 100.0", "einheit": "cm", "bereich": "Sinnvoll: 75 – 135 cm", "bild_pfad": "assets/tests/y_balance/posterolateral.svg"},
        },
    },

    # ══════════════════════════════════════════════════════════════════════════
    # FMS
    # ══════════════════════════════════════════════════════════════════════════
    "fms": {
        "name": "Functional Movement Screen (FMS)",
        "kurzbeschreibung": "7 Grundbewegungsmuster werden bilateral bewertet — Punkteskala 0 bis 3, Maximum 21 Punkte.",
        "ziel": (
            "Beurteilung der funktionellen Bewegungsqualität in 7 Grundmustern. "
            "Score ≤ 14 Punkte gilt als trainingsrelevant. "
            "Asymmetrien (gleiche Übung, verschiedene Seiten) zeigen seitenspezifischen Trainingsbedarf."
        ),
        "material": "FMS-Kit (Stab 122 cm, Hürde, Brett) oder entsprechende Hilfsmittel.",
        "aufbau": (
            "Ebene, rutschfeste Fläche. "
            "FMS-Brett auf den Boden legen. Hürde auf Hüfthöhe des Spielers einstellen. "
            "Stab bereithalten. Spieler barfuß oder in leichten Hallenschuhen."
        ),
        "aufwaermung": "5–10 Minuten allgemeines Aufwärmen, keine spezifische Vorbereitung auf die FMS-Muster.",
        "durchfuehrung": (
            "Jeden Test dreimal zeigen lassen. Bestes Ergebnis je Seite wird gewertet. "
            "Bewertung: 3 = korrekt ohne Kompensation, 2 = korrekt mit Kompensation, "
            "1 = nicht möglich, 0 = Schmerzen während des Tests. "
            "Bei bilateralen Tests: niedrigerer Seitenwert zählt."
        ),
        "trainerhinweis": (
            "Keine Hilfestellung oder Coaching während der Durchführung. "
            "Nur beobachten und bewerten. "
            "Bei Schmerzen (0 Punkte) sofort stoppen — keine weitere Belastung. "
            "Reihenfolge einhalten: Deep Squat → Hurdle Step → Inline Lunge → Shoulder → ASLR → Trunk → Rotary."
        ),
        "versuche": "Bis zu 3 Versuche je Muster. Bestes Ergebnis wird gewertet.",
        "pause": "Kurze Pause zwischen den Mustern, kein zeitlicher Druck.",
        "messwert": "Punkte je Muster (0–3), Gesamtscore (0–21)",
        "einheit": "Punkte",
        "gueltiger_versuch": "Bewegung wird vollständig und klar beobachtbar ausgeführt.",
        "ungueltiger_versuch": "Bewegung abgebrochen, zu kurz oder ohne klares Ergebnis — Versuch wiederholen.",
        "fehler": [
            "Coaching während der Ausführung — verändert das natürliche Bewegungsmuster",
            "Zu früh bewertet ohne vollständige Bewegungsausführung",
            "Höhere Seite bei Asymmetrien eingetragen statt niedrigerer",
            "Schuhwerk beeinflusst Beweglichkeit — immer barfuß oder gleiche Bedingung",
        ],
        "sicherheit": (
            "Bei Schmerzen (Bewertung 0) den Test sofort abbrechen. "
            "Keine Provokation von Beschwerden. "
            "Schwangere, akute Verletzungen und starke Schwellungen: Test aussetzen."
        ),
        "bild_pfad": "assets/tests/fms/fms_overview.svg",
        "quelle": "Cook et al. (2006); Functional Movement Systems",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None, "video_link": None, "video_titel": None, "video_quelle": None, "video_lizenz": None,
        "felder": {
            "deep_squat":       {"label": "Deep Squat",              "ziel": "Bilaterale Hüft-, Knie- und Sprunggelenkmobilität, Schulter- und Rumpfkontrolle.", "kurzhilfe": "Spieler hält Stab über Kopf und führt tiefe Kniebeuge aus. 3 = vollständig, 2 = mit Fersenkeil, 1 = nicht möglich, 0 = Schmerzen.", "eingabehilfe": "Wert 0, 1, 2 oder 3 eintragen", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3", "bild_pfad": "assets/tests/fms/deep_squat.svg"},
            "hurdle_step":      {"label": "Hurdle Step",             "ziel": "Einbeinige Standbeinsstabilität, Hüftmobilität, Koordination.", "kurzhilfe": "Spieler übersteigt Hürde auf Hüfthöhe ohne Berühren. Je Seite bewerten — niedrigere Seite zählt.", "eingabehilfe": "Wert 0, 1, 2 oder 3 je Seite", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3", "bild_pfad": "assets/tests/fms/hurdle_step.svg"},
            "inline_lunge":     {"label": "Inline Lunge",            "ziel": "Hüftmobilität, Kniestabilität, Rumpfkontrolle im Ausfallschritt.", "kurzhilfe": "Spieler führt Ausfallschritt auf Brett aus, Stab bleibt gerade. Je Seite bewerten.", "eingabehilfe": "Wert 0, 1, 2 oder 3 je Seite", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3", "bild_pfad": "assets/tests/fms/inline_lunge.svg"},
            "shoulder":         {"label": "Shoulder Mobility",       "ziel": "Schulterrotation und -mobilität — Innen-/Außenrotation kombiniert.", "kurzhilfe": "Beide Hände hinter Rücken — Abstand zwischen Fäusten messen. ≤ Handlänge = 3, ≤ 1.5 Handlänge = 2, sonst = 1. Schmerzprovokationstest extra.", "eingabehilfe": "Wert 0, 1, 2 oder 3 je Seite", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3", "bild_pfad": "assets/tests/fms/shoulder_mobility.svg"},
            "aslr":             {"label": "ASLR (Straight Leg Raise)","ziel": "Aktive Hüftbeugung, Hamstringsdehnbarkeit, Rumpfstabilität.", "kurzhilfe": "Spieler liegt, hebt gestrecktes Bein. Knöchel über Mittelpunkt Oberschenkel = 3, über Knie = 2, darunter = 1.", "eingabehilfe": "Wert 0, 1, 2 oder 3 je Seite", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3", "bild_pfad": "assets/tests/fms/aslr.svg"},
            "trunk_stability":  {"label": "Trunk Stability Push-up", "ziel": "Rumpfstabilität in der Sagittalebene beim Liegestütz.", "kurzhilfe": "Spieler führt Liegestütz aus, ohne dass Hüfte absackt. Männer Daumen auf Stirnhöhe = 3, Kinnnhöhe = 2. Frauen Kinnnhöhe = 3, Schlüsselbein = 2.", "eingabehilfe": "Wert 0, 1, 2 oder 3", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3", "bild_pfad": "assets/tests/fms/trunk_stability_pushup.svg"},
            "rotary_stability": {"label": "Rotary Stability",        "ziel": "Multiplanare Rumpfstabilität im Vierfüßlerstand.", "kurzhilfe": "Spieler streckt Arm und Gegenbein gleichzeitig — kein Ausweichen. Diagonal = 3, unilateral = 2, nicht möglich = 1.", "eingabehilfe": "Wert 0, 1, 2 oder 3 je Seite", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3", "bild_pfad": "assets/tests/fms/rotary_stability.svg"},
        },
    },

    # ══════════════════════════════════════════════════════════════════════════
    # SPRUNG / JUMP
    # ══════════════════════════════════════════════════════════════════════════
    "jump": {
        "name": "Sprung-Diagnostik",
        "kurzbeschreibung": "Explosivkraft, Reaktivkraft und Seitenasymmetrie — CMJ, Squat Jump, Drop Jump, Standweitsprung.",
        "ziel": (
            "Messung der Sprungkraft als Indikator für Explosivkraft und Reaktivkraft. "
            "Seitenvergleich CMJ rechts/links zeigt muskuläre Asymmetrie. "
            "RSI (Drop Jump) bewertet Reaktivkraft und Belastungstoleranz."
        ),
        "material": "Kontaktmatte oder Videoanalyse, ausreichend Kopffreiheit (> 3 m), rutschfester Untergrund.",
        "aufbau": (
            "Ebene, rutschfeste Fläche. Kontaktmatte oder Videomarkierung vorbereiten. "
            "Für Drop Jump: Absprungbox in 30–40 cm Höhe. "
            "Für Standweitsprung: Klebeband-Markierung als Absprunglinie."
        ),
        "aufwaermung": "10 Minuten allgemeines Aufwärmen, 3–5 submaximale CMJ-Versuche.",
        "durchfuehrung": (
            "CMJ beidbeinig: Aus dem Stand mit Gegenbewegung maximal abspringen, Arme frei. "
            "CMJ einbeinig: Gleiches Prinzip auf je einem Bein. "
            "Squat Jump: Aus 90°-Kniebeugeposition ohne Gegenbewegung abspringen, Hände in Hüfte. "
            "Drop Jump: Von Box springen, sofort maximal abspringen — minimale Kontaktzeit. "
            "Standweit: Aus dem Stand so weit wie möglich springen, beidbeinige Landung."
        ),
        "trainerhinweis": (
            "CMJ: Spieler soll Hände an Hüften lassen (nur Beine), wenn Armschwung ausgeschlossen sein soll. "
            "SJ: Keine sichtbare Gegenbewegung vor Absprung — sonst ungültig. "
            "Drop Jump: Absprungbox-Höhe notieren. Kontaktzeit so kurz wie möglich. "
            "Standweit: Beide Füße gleichzeitig landen, kein Ausfallschritt."
        ),
        "versuche": "3 Versuche je Testvariante. Bester Wert wird gewertet.",
        "pause": "30–60 Sekunden zwischen Versuchen, 2–3 Minuten zwischen Testvarianten.",
        "messwert": "Sprunghöhe in cm (CMJ, SJ, DJ), Kontaktzeit in Sekunden (DJ), Weite in cm (SWJ)",
        "einheit": "cm / s",
        "gueltiger_versuch": "Vollständiger Absprung, beidbeinige Landung (bei beidbeinigen Tests), keine Vorabstützung.",
        "ungueltiger_versuch": "Kein vollständiger Absprung, einseitige Landung bei beidbeinigem Test, Aufsetzen bei SJ.",
        "fehler": [
            "Gegenbewegung beim Squat Jump — gibt zu hohe Sprunghöhe",
            "Zu lange Kontaktzeit beim Drop Jump — RSI wird unterschätzt",
            "Armschwung beeinflusst Sprunghöhe — Bedingung für alle Versuche gleich halten",
            "Zu kurze Pause — Ermüdung verfälscht Folgeversuche",
        ],
        "sicherheit": (
            "Ausreichend Landeplatz. "
            "Knieprobleme, Sprunggelenksbeschwerden oder akute Schmerzen: Test aussetzen. "
            "Drop Jump nur auf sicherem, ebenen Untergrund."
        ),
        "bild_pfad": "assets/tests/jump/cmj_setup.svg",
        "quelle": "Bosco et al. (1983); Flanagan & Comyns (2008)",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None, "video_link": None, "video_titel": None, "video_quelle": None, "video_lizenz": None,
        "felder": {
            "cmj_beid":   {"label": "CMJ beidbeinig",        "ziel": "Beidbeinige Explosivkraft.", "kurzhilfe": "Sprunghöhe Countermovement Jump beidbeinig in cm. Besten Versuch eintragen.", "eingabehilfe": "Höhe in cm, z. B. 42.0", "einheit": "cm", "bereich": "Sinnvoll: 20 – 70 cm", "bild_pfad": "assets/tests/jump/cmj_setup.svg"},
            "cmj_r":      {"label": "CMJ einbeinig rechts",  "ziel": "Einbeinige Explosivkraft rechts.", "kurzhilfe": "Sprunghöhe einbeiniger CMJ rechts in cm. Ermöglicht Seitenvergleich.", "eingabehilfe": "Höhe in cm, z. B. 32.0", "einheit": "cm", "bereich": "Sinnvoll: 15 – 55 cm", "bild_pfad": "assets/tests/jump/cmj_einbein.svg"},
            "cmj_l":      {"label": "CMJ einbeinig links",   "ziel": "Einbeinige Explosivkraft links.", "kurzhilfe": "Sprunghöhe einbeiniger CMJ links in cm. Seitenasymmetrie > 10 % = trainingsrelevant.", "eingabehilfe": "Höhe in cm, z. B. 31.0", "einheit": "cm", "bereich": "Sinnvoll: 15 – 55 cm", "bild_pfad": "assets/tests/jump/cmj_einbein.svg"},
            "squat_jump": {"label": "Squat Jump",            "ziel": "Konzentrische Explosivkraft ohne Vorspannung.", "kurzhilfe": "Sprunghöhe aus 90°-Kniebeugeposition ohne Gegenbewegung. Hände an Hüfte.", "eingabehilfe": "Höhe in cm, z. B. 38.0", "einheit": "cm", "bereich": "Sinnvoll: 18 – 65 cm", "bild_pfad": "assets/tests/jump/squat_jump.svg"},
            "dj_hoehe":   {"label": "Drop Jump Höhe",        "ziel": "Reaktivkraft — Absprunghöhe nach Drop.", "kurzhilfe": "Sprunghöhe nach Drop Jump (von Box fallen, sofort abspringen) in cm.", "eingabehilfe": "Höhe in cm, z. B. 35.0", "einheit": "cm", "bereich": "Sinnvoll: 15 – 55 cm", "bild_pfad": "assets/tests/jump/drop_jump.svg"},
            "dj_kontakt": {"label": "Drop Jump Kontaktzeit", "ziel": "Reaktivkraft — Bodenkontaktzeit soll minimal sein.", "kurzhilfe": "Bodenkontaktzeit beim Drop Jump in Sekunden. Kürzer = reaktiver. RSI = Höhe / Kontaktzeit.", "eingabehilfe": "Zeit in Sekunden, z. B. 0.18", "einheit": "s", "bereich": "Sinnvoll: 0.08 – 0.40 s", "bild_pfad": "assets/tests/jump/drop_jump.svg"},
            "standweit":  {"label": "Standweitsprung",       "ziel": "Horizontale Explosivkraft.", "kurzhilfe": "Sprungweite in cm ab Absprunglinie bis hinterste Ferse bei der Landung.", "eingabehilfe": "Weite in cm, z. B. 215", "einheit": "cm", "bereich": "Sinnvoll: 100 – 320 cm", "bild_pfad": "assets/tests/jump/standweit.svg"},
        },
    },

    # ══════════════════════════════════════════════════════════════════════════
    # AGILITÄT / RICHTUNGSWECHSEL
    # ══════════════════════════════════════════════════════════════════════════
    "agility": {
        "name": "Agilität & Richtungswechsel",
        "kurzbeschreibung": "505-Test, 5-10-5 Shuttle, T-Test, Illinois Agility Run — Richtungswechselgeschwindigkeit und Abbremsstärke.",
        "ziel": (
            "Messung der Richtungswechselgeschwindigkeit als Schlüsselfähigkeit im Fußball. "
            "505-Test bewertet 180°-Wendung getrennt für rechts und links. "
            "T-Test und Illinois messen mehrdirektionale Agilität."
        ),
        "material": "Hütchen, Klebeband oder Kreide, Stoppuhr oder Lichtschranken, Maßband.",
        "aufbau": (
            "505-Test: 10 m Anlaufzone + 5 m Zeitmesszone + Wendepunkt markieren. "
            "5-10-5: Drei Linien im Abstand von 5 m markieren. "
            "T-Test: T-Form mit je 9,14 m vorwärts und 4,57 m seitwärts. "
            "Illinois: 10 m × 5 m Kurs mit 4 Hütchen-Slalompunkten."
        ),
        "aufwaermung": "10 Minuten allgemeines Aufwärmen, 2–3 Probeläufe mit 70–80 % Intensität.",
        "durchfuehrung": (
            "505-Test: Aus dem Stand anlaufen, 10 m Anlauf, letzten 5 m gestoppt, auf Linie wenden, zurücksprinten. "
            "Getrennt für rechts- und linksseitiges Wenden. "
            "5-10-5: Start aus dem Stand, 5 m zu einer Seite, 10 m zur anderen, 5 m zurück. "
            "T-Test: 9,14 m vorwärts, seitwärts links 4,57 m, rechts 9,14 m, links 4,57 m zurück, rückwärts zur Startlinie."
        ),
        "trainerhinweis": (
            "Spieler muss die Wendepunkte klar berühren (505: Linie vollständig übertreten). "
            "Keine Vorahnung der Wendeseite beim 5-10-5 — immer klar ansagen. "
            "T-Test: Seitwärtsbewegung, kein Überkreuzen der Beine. "
            "Reihenfolge: Erst alle Tests einer Art, dann nächster Test."
        ),
        "versuche": "2–3 Versuche je Test. Bester gültiger Versuch wird gewertet.",
        "pause": "2–3 Minuten zwischen den Versuchen.",
        "messwert": "Zeit in Sekunden",
        "einheit": "Sekunden (s)",
        "gueltiger_versuch": "Alle Wendepunkte klar berührt oder übertreten, korrekter Streckenverlauf.",
        "ungueltiger_versuch": "Wendepunkt nicht berührt, falsche Reihenfolge, Abkürzung der Strecke.",
        "fehler": [
            "Wendepunkt nicht vollständig berührt — zu kurze gemessene Zeit",
            "Beim T-Test Beine überkreuzen statt Seitwärtsschritte — verändert Bewegungsanforderung",
            "Zu kurze Pause — Ermüdung überlagert Agilität",
            "Illinois: Hütchen berühren ohne Strafe — immer Wiederholung ansagen",
        ],
        "sicherheit": (
            "Rutschfester Untergrund obligatorisch. "
            "Knie- und Sprunggelenksbeschwerden: Test aussetzen. "
            "Ausreichend Platz hinter den Endmarkierungen."
        ),
        "bild_pfad": "assets/tests/agility/test_505.svg",
        "quelle": "Draper & Lancaster (1985) — 505-Test; Johnson & Nelson (1986) — T-Test",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None, "video_link": None, "video_titel": None, "video_quelle": None, "video_lizenz": None,
        "felder": {
            "t505_r":  {"label": "505-Test rechts",   "ziel": "Richtungswechsel 180° nach rechts.", "kurzhilfe": "Zeit für den 5-m-Abschnitt (Zeitmesszone) beim Rechtswenden in Sekunden.", "eingabehilfe": "Zeit in Sekunden, z. B. 2.35", "einheit": "s", "bereich": "Sinnvoll: 1.80 – 3.20 s", "bild_pfad": "assets/tests/agility/test_505.svg"},
            "t505_l":  {"label": "505-Test links",    "ziel": "Richtungswechsel 180° nach links.", "kurzhilfe": "Zeit für den 5-m-Abschnitt beim Linkswenden. Seitendifferenz > 10 % = trainingsrelevant.", "eingabehilfe": "Zeit in Sekunden, z. B. 2.40", "einheit": "s", "bereich": "Sinnvoll: 1.80 – 3.20 s", "bild_pfad": "assets/tests/agility/test_505.svg"},
            "t5_10_5": {"label": "5-10-5 Shuttle",   "ziel": "Shuttle-Beschleunigung und Abbremsfähigkeit.", "kurzhilfe": "Gesamtzeit 5-10-5-Shuttle in Sekunden (5 m + 10 m + 5 m).", "eingabehilfe": "Zeit in Sekunden, z. B. 4.80", "einheit": "s", "bereich": "Sinnvoll: 3.80 – 6.00 s", "bild_pfad": "assets/tests/agility/shuttle_5_10_5.svg"},
            "t_test":  {"label": "T-Test",           "ziel": "Mehrdirektionale Agilität vorwärts, seitwärts, rückwärts.", "kurzhilfe": "Gesamtzeit T-Test in Sekunden.", "eingabehilfe": "Zeit in Sekunden, z. B. 9.50", "einheit": "s", "bereich": "Sinnvoll: 8.00 – 13.00 s", "bild_pfad": "assets/tests/agility/t_test.svg"},
            "illinois": {"label": "Illinois Agility", "ziel": "Gesamtagilität im Slalomkurs.", "kurzhilfe": "Gesamtzeit Illinois Agility Run in Sekunden.", "eingabehilfe": "Zeit in Sekunden, z. B. 15.50", "einheit": "s", "bereich": "Sinnvoll: 13.00 – 20.00 s", "bild_pfad": "assets/tests/agility/illinois.svg"},
        },
    },

    # ══════════════════════════════════════════════════════════════════════════
    # YO-YO / AUSDAUER
    # ══════════════════════════════════════════════════════════════════════════
    "yoyo": {
        "name": "Yo-Yo Ausdauer-Diagnostik",
        "kurzbeschreibung": "Yo-Yo Intermittent Recovery Test Level 1 (IR1) und Level 2 (IR2) — Standardtest im Fußball.",
        "ziel": (
            "Messung der intermittierenden Ausdauerleistungsfähigkeit — für Fußball besonders relevant, "
            "da das Spiel durch kurze intensive Aktionen und Erholungsphasen geprägt ist. "
            "Ergebnis ist die Gesamtlaufdistanz in Metern."
        ),
        "material": "Zwei Linien im Abstand von 20 m, Erholungszone 5 m (hinter der Startlinie), Audio-CD oder App mit Yo-Yo-Beeps, Maßband.",
        "aufbau": (
            "Start-/Ziellinie und Wendelinie im Abstand von 20 m markieren. "
            "5 m hinter der Startlinie: Erholungszone markieren (5 m bis zur dritten Linie). "
            "Spieler laufen pendeln zwischen Start und Wendelinie hin und zurück — "
            "dann 5 m in Erholungszone gehen/laufen, umkehren, bereit für nächsten Lauf."
        ),
        "aufwaermung": "10 Minuten allgemeines Aufwärmen. Testprotokoll erläutern, 2–3 Probeläufe.",
        "durchfuehrung": (
            "Spieler starten mit dem ersten Beep-Signal und laufen 20 m zur Wendelinie. "
            "Vor dem nächsten Beep-Signal zurück zur Startlinie. "
            "In der Erholungsphase (10 s bei IR1, 5 s bei IR2) in die Erholungszone und zurück. "
            "Test endet, wenn Spieler zweimal hintereinander die Linie vor dem Beep nicht erreicht."
        ),
        "trainerhinweis": (
            "Spieler muss die Linien mit einem Fuß berühren oder übertreten — kein Abschneiden. "
            "Erste Warnung bei Verpassen der Linie, zweite Warnung = Testende. "
            "Verbleibende Spieler nicht anfeuern (ablenkend). "
            "Distanz zählen: jede vollständig absolvierte 20-m-Strecke = 20 m."
        ),
        "versuche": "Einmaliger Maximaltest bis zur Erschöpfung.",
        "pause": "Kein weiterer Versuch. Mindestens 48 Stunden zwischen Yo-Yo-Tests.",
        "messwert": "Gesamtlaufdistanz in Metern",
        "einheit": "Meter (m)",
        "gueltiger_versuch": "Alle Linien rechtzeitig erreicht, Erholungszone korrekt durchlaufen.",
        "ungueltiger_versuch": "Zweimaliges Verpassen der Linie vor dem Beep — Testende.",
        "fehler": [
            "Startlinie abschneiden — Distanz wird zu groß gemessen",
            "Zu früh starten — verfälscht VO₂max-Schätzung",
            "Kühles Wetter ohne ausreichendes Aufwärmen — Leistung unterschätzt",
            "Außentemperatur und Untergrund (Halle vs. Rasen) beeinflussen das Ergebnis",
        ],
        "sicherheit": (
            "Test ist intensiv — nur für ausreichend aufgewärmte, beschwerdefreie Spieler. "
            "Bei Herzrhythmusstörungen, starker Erschöpfung oder Übelkeit sofort stoppen. "
            "Nach dem Test: Abwärmen, ausreichend trinken."
        ),
        "bild_pfad": "assets/tests/yoyo/yoyo_setup.svg",
        "quelle": "Bangsbo et al. (2008) — Yo-Yo IR1/IR2",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None, "video_link": None, "video_titel": None, "video_quelle": None, "video_lizenz": None,
        "felder": {
            "distanz":  {"label": "Erzielte Distanz", "ziel": "Gesamtlaufdistanz bis zum Testabbruch.", "kurzhilfe": "Gesamtlaufdistanz in Metern. Jede absolvierte Hin-und-Rück-Strecke = 40 m. Z. B. bei Stufe 15 = 920 m.", "eingabehilfe": "Distanz in Metern, z. B. 1200", "einheit": "m", "bereich": "Sinnvoll: 80 – 4000 m"},
            "hf_max":   {"label": "HF max (bpm)",     "ziel": "Belastungsintensität — maximale Herzfrequenz direkt nach Testende.", "kurzhilfe": "Maximale Herzfrequenz direkt nach Testabbruch in Schlägen pro Minute. Sofort messen (innerhalb 10 Sekunden).", "eingabehilfe": "Herzfrequenz in bpm, z. B. 192", "einheit": "bpm", "bereich": "Sinnvoll: 120 – 220 bpm"},
            "rpe":      {"label": "RPE (Borg 6–20)",   "ziel": "Subjektives Belastungsempfinden als ergänzende Information.", "kurzhilfe": "Borg-Skala: 6 = gar keine Anstrengung, 20 = maximale Anstrengung. Typisch nach Yo-Yo: 17–20.", "eingabehilfe": "Wert zwischen 6 und 20", "einheit": "Borg", "bereich": "6 bis 20"},
        },
    },

    # ══════════════════════════════════════════════════════════════════════════
    # KRAFT
    # ══════════════════════════════════════════════════════════════════════════
    "kraft": {
        "name": "Kraft-Diagnostik",
        "kurzbeschreibung": "Bankdrücken (1RM direkt oder Epley-Schätzung) und Rumpfkraftausdauer ventral, lateral und dorsal.",
        "ziel": (
            "Erfassung der Maximalkraft des Oberkörpers (Bankdrücken) und der "
            "Rumpfkraftausdauer in drei Ebenen. "
            "Relative Kraft (1RM / Körpergewicht) ermöglicht den Vergleich zwischen Spielern. "
            "Seitendifferenz lateral > 10 % und auffällige Ventral/Dorsal-Ratios gelten als trainingsrelevant."
        ),
        "material": "Hantelbank mit Langhantel und Scheiben, 2 Spotter, Matte, Liege oder Kasten für Biering-Sørensen, Fixiergurt, Stoppuhr.",
        "aufbau": (
            "Bankdrücken: Bank stabil aufstellen, Hantelablage prüfen, Gewichte mit Verschlüssen sichern. "
            "Rumpftests: Matte auslegen. "
            "Dorsal (Biering-Sørensen): Liege oder Kasten so vorbereiten, dass der Oberkörper frei über die Kante ragt "
            "und die Beine fixiert werden können."
        ),
        "aufwaermung": (
            "10 Minuten allgemeines Aufwärmen. "
            "Bankdrücken: progressive Laststeigerung (leichtes Gewicht 8–10 WH, mittleres 4–6 WH). "
            "Rumpftests: kurze Aktivierung, je 1 Probeposition ohne Zeitmessung."
        ),
        "durchfuehrung": (
            "Bankdrücken direkt: Last schrittweise steigern bis zur maximalen Einzelwiederholung — nur mit Sicherung. "
            "Bankdrücken Epley: Submaximalgewicht wählen, maximale saubere Wiederholungszahl (2–10) ausführen. "
            "Ventral: Unterarmstütz halten, 2 Versuche. "
            "Lateral: Seitstütz rechts und links je 1 Versuch. "
            "Dorsal: Oberkörper frei über der Kante horizontal halten, Beine fixiert."
        ),
        "trainerhinweis": (
            "Direkter 1RM-Test nur mit mindestens 2 Spottern und vollständigem Sicherheitsprotokoll. "
            "Rumpftests enden bei Formverlust (Hüfte sackt ab, Oberkörper sinkt unter die Horizontale) — "
            "Zeit bis zum ersten Formverlust werten. Keine Motivation über den Formverlust hinaus."
        ),
        "versuche": "Bankdrücken: 1 gültiger Maximalversuch bzw. 1 Submaximalsatz. Ventral: 2 Versuche (Bestwert). Lateral R/L und Dorsal: je 1 Versuch.",
        "pause": "Bankdrücken: 3–5 Minuten zwischen Maximalversuchen. Rumpftests: 2–3 Minuten zwischen den Positionen.",
        "messwert": "1RM in kg (direkt oder Epley-geschätzt), Haltedauer in Sekunden je Rumpfposition",
        "einheit": "kg / s",
        "gueltiger_versuch": "Bankdrücken: Hantel berührt Brust, vollständige Streckung, Gesäß bleibt auf der Bank. Rumpftests: korrekte Position bis zum Formverlust gehalten.",
        "ungueltiger_versuch": "Bankdrücken: Abfedern, Gesäß hebt ab, unvollständige Streckung. Rumpftests: Position von Beginn an nicht korrekt eingenommen.",
        "fehler": [
            "Bankdrücken ohne Spotter — Sicherheitsrisiko, Test nicht durchführen",
            "Epley-Formel mit > 10 Wiederholungen — Schätzung wird ungenau",
            "Plank mit abgesackter oder überhöhter Hüfte — Zeit wird zu lang gewertet",
            "Biering-Sørensen ohne Beckenkante an der Liegenkante — verfälscht die Hebelverhältnisse",
        ],
        "sicherheit": (
            "Direkter 1RM-Test erfordert Sicherung durch mindestens 2 Trainer, abgeschlossenes Aufwärmen "
            "und Technikbeherrschung. Bei Rückenbeschwerden dorsalen Test aussetzen. "
            "Sofortabbruch bei Schmerzen oder technischen Mängeln."
        ),
        "bild_pfad": "assets/tests/kraft/bankdruecken.svg",
        "quelle": "Epley (1985); Biering-Sørensen (1984); McGill et al. (1999)",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None, "video_link": None, "video_titel": None, "video_quelle": None, "video_lizenz": None,
        "felder": {
            "direktes_1rm":         {"label": "Direktes 1RM",            "ziel": "Maximalkraft Oberkörper — direkt gemessen.", "kurzhilfe": "Höchstes sauber gedrücktes Gewicht in kg. Nur mit vollständigem Sicherheitsprotokoll.", "eingabehilfe": "Gewicht in kg, z. B. 80.0", "einheit": "kg", "bereich": "Sinnvoll: 20 – 200 kg", "bild_pfad": "assets/tests/kraft/bankdruecken.svg"},
            "epley_gewicht":        {"label": "Epley Testgewicht",       "ziel": "Submaximalgewicht für die 1RM-Schätzung.", "kurzhilfe": "Gewicht des Submaximalsatzes in kg. Empfohlen: Last für 2–10 saubere Wiederholungen.", "eingabehilfe": "Gewicht in kg, z. B. 60.0", "einheit": "kg", "bereich": "Sinnvoll: 20 – 180 kg", "bild_pfad": "assets/tests/kraft/bankdruecken.svg"},
            "epley_wiederholungen": {"label": "Epley Wiederholungen",    "ziel": "Wiederholungszahl für die Epley-Formel.", "kurzhilfe": "Maximale saubere Wiederholungen mit dem Testgewicht. 1RM = Gewicht × (1 + WH/30).", "eingabehilfe": "Anzahl, z. B. 5", "einheit": "WH", "bereich": "Gültig: 1 – 10 WH", "bild_pfad": "assets/tests/kraft/bankdruecken.svg"},
            "ventral_sekunden":     {"label": "Ventral (Plank) V1",      "ziel": "Rumpfkraftausdauer der vorderen Kette.", "kurzhilfe": "Haltedauer Unterarmstütz Versuch 1 in Sekunden. Abbruch bei Formverlust.", "eingabehilfe": "Zeit in Sekunden, z. B. 90", "einheit": "s", "bereich": "Sinnvoll: 20 – 300 s", "bild_pfad": "assets/tests/kraft/plank_ventral.svg"},
            "ventral_versuch2":     {"label": "Ventral (Plank) V2",      "ziel": "Zweiter Versuch — Bestwert zählt.", "kurzhilfe": "Haltedauer Unterarmstütz Versuch 2 in Sekunden. Der längere Versuch wird gewertet.", "eingabehilfe": "Zeit in Sekunden, z. B. 95", "einheit": "s", "bereich": "Sinnvoll: 20 – 300 s", "bild_pfad": "assets/tests/kraft/plank_ventral.svg"},
            "lateral_rechts":       {"label": "Lateral rechts",          "ziel": "Seitliche Rumpfkraftausdauer rechts.", "kurzhilfe": "Haltedauer Seitstütz rechts in Sekunden. Ellbogen unter der Schulter, Füße gestapelt.", "eingabehilfe": "Zeit in Sekunden, z. B. 60", "einheit": "s", "bereich": "Sinnvoll: 15 – 240 s", "bild_pfad": "assets/tests/kraft/plank_lateral.svg"},
            "lateral_links":        {"label": "Lateral links",           "ziel": "Seitliche Rumpfkraftausdauer links — Seitenvergleich.", "kurzhilfe": "Haltedauer Seitstütz links in Sekunden. Seitendifferenz > 10 % = trainingsrelevant.", "eingabehilfe": "Zeit in Sekunden, z. B. 55", "einheit": "s", "bereich": "Sinnvoll: 15 – 240 s", "bild_pfad": "assets/tests/kraft/plank_lateral.svg"},
            "dorsal_sekunden":      {"label": "Dorsal (Biering-Sørensen)","ziel": "Rumpfkraftausdauer der hinteren Kette.", "kurzhilfe": "Haltedauer Biering-Sørensen in Sekunden. Oberkörper horizontal, Beine fixiert.", "eingabehilfe": "Zeit in Sekunden, z. B. 120", "einheit": "s", "bereich": "Sinnvoll: 30 – 300 s", "bild_pfad": "assets/tests/kraft/plank_dorsal.svg"},
        },
    },

    # ══════════════════════════════════════════════════════════════════════════
    # ANTHROPOMETRIE
    # ══════════════════════════════════════════════════════════════════════════
    "anthropometrie": {
        "name": "Anthropometrie",
        "kurzbeschreibung": "Körpermaße, BMI, Körperzusammensetzung und sportlicher Reifestatus (PHV-Schätzung).",
        "ziel": (
            "Erfassung anthropometrischer Basisdaten für trainingsplanerische Entscheidungen. "
            "PHV-Offset schätzt den Entwicklungsstand im Wachstumsprozess (Nachwuchs). "
            "Kein medizinischer Befund — rein sportliche Dokumentation."
        ),
        "material": "Stadiometer (Messgerät für Körpergröße), Personenwaage, Maßband, Sitzmessgerät oder Brett.",
        "aufbau": "Ruhige Umgebung, Spieler mit leichter Sportkleidung, ohne Schuhe.",
        "aufwaermung": "Nicht zutreffend — Ruhemessung vor dem Sport bevorzugt.",
        "durchfuehrung": (
            "Körpergröße: Spieler aufrecht an der Wand, Blick gerade, Messung am Scheitelpunkt. "
            "Körpergewicht: Morgens, nüchtern oder nach dem Training — immer gleiche Bedingung notieren. "
            "Sitzhöhe: Spieler aufrecht auf Boden sitzen, Messung vom Boden bis zum Scheitel. "
            "Beinlänge: Körpergröße minus Sitzhöhe, oder direktes Messen ASIS bis Innenknöchel. "
            "Armspann: Beide Arme waagerecht, Fingerspitze bis Fingerspitze. "
            "Körperfett: Methode dokumentieren (Caliper-Messung, BIA, DEXA)."
        ),
        "trainerhinweis": (
            "Immer gleiche Bedingungen für Verlaufsmessungen (Tageszeit, Kleidung, Messstelle). "
            "Körperfett-Methode im Verlauf nicht wechseln. "
            "PHV-Schätzung ist eine mathematische Näherung — keine medizinische Aussage. "
            "Messwerte vertraulich behandeln."
        ),
        "versuche": "Einfachmessung (oder Doppelmessung bei abweichenden Werten).",
        "pause": "Nicht zutreffend.",
        "messwert": "Verschiedene Maße in cm, kg und %",
        "einheit": "cm / kg / %",
        "gueltiger_versuch": "Standardisierte Messbedingungen eingehalten.",
        "ungueltiger_versuch": "Abweichende Bedingungen (Schuhe, andere Tageszeit) — im Bemerkungsfeld notieren.",
        "fehler": [
            "Schuhe vergessen — Größe erscheint 2–3 cm zu groß",
            "Körpergewicht nach dem Training ohne Hinweis — beeinflusst Verlauf",
            "Sitzhöhe falsch gemessen — PHV-Schätzung stimmt nicht",
            "Körperfett-Methode gewechselt — Verlaufsvergleich nicht möglich",
        ],
        "sicherheit": "Keine besonderen Sicherheitsanforderungen.",
        "bild_pfad": "assets/tests/anthropometrie/anthro_punkte.svg",
        "quelle": "Mirwald et al. (2002) — PHV-Schätzung; WHO — BMI-Klassifikation",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None, "video_link": None, "video_titel": None, "video_quelle": None, "video_lizenz": None,
        "felder": {
            "groesse":      {"label": "Körpergröße",    "ziel": "Grundmaß für alle weiteren Berechnungen.", "kurzhilfe": "Körpergröße in cm, aufrecht stehend ohne Schuhe, Blick geradeaus.", "eingabehilfe": "Größe in cm, z. B. 175.0", "einheit": "cm", "bereich": "Sinnvoll: 100 – 220 cm"},
            "gewicht":      {"label": "Körpergewicht",  "ziel": "Grundmaß für BMI und Körperzusammensetzung.", "kurzhilfe": "Gewicht in kg. Möglichst gleiche Bedingung wie bei Vortestungen (Tageszeit, Kleidung).", "eingabehilfe": "Gewicht in kg, z. B. 68.5", "einheit": "kg", "bereich": "Sinnvoll: 30 – 150 kg"},
            "koerperfett":  {"label": "Körperfettanteil","ziel": "Einschätzung der Körperzusammensetzung.", "kurzhilfe": "Körperfettanteil in %. Methode dokumentieren (Caliper, BIA, o. ä.).", "eingabehilfe": "Prozent, z. B. 12.5", "einheit": "%", "bereich": "Sinnvoll: 4 – 40 %"},
            "muskelmasse":  {"label": "Muskelmasse",    "ziel": "Anteil der Muskelmasse am Körpergewicht.", "kurzhilfe": "Muskelmasse in kg (BIA-Gerät) oder als % eintragen.", "eingabehilfe": "Wert in kg oder %, z. B. 32.0", "einheit": "kg", "bereich": "Sinnvoll: 25 – 65 kg"},
            "sitzhoehe":    {"label": "Sitzhöhe",       "ziel": "Für PHV-Schätzung nach Mirwald et al. (2002).", "kurzhilfe": "Aufrecht sitzen, Messung vom Boden bis zum Scheitel in cm. Für PHV-Berechnung wichtig!", "eingabehilfe": "Sitzhöhe in cm, z. B. 91.0", "einheit": "cm", "bereich": "Sinnvoll: 50 – 110 cm"},
            "beinlaenge":   {"label": "Beinlänge",      "ziel": "Abgeleitetes Maß für PHV-Schätzung.", "kurzhilfe": "Beinlänge = Körpergröße minus Sitzhöhe. Oder direkt messen (ASIS bis Innenknöchel).", "eingabehilfe": "Beinlänge in cm, z. B. 84.0", "einheit": "cm", "bereich": "Sinnvoll: 40 – 120 cm"},
            "armspann":     {"label": "Armspann",       "ziel": "Verhältnis zum Körperwuchs — ergänzende Information.", "kurzhilfe": "Beide Arme waagerecht ausgestreckt, Fingerspitze zu Fingerspitze in cm.", "eingabehilfe": "Armspann in cm, z. B. 178.0", "einheit": "cm", "bereich": "Sinnvoll: 100 – 250 cm"},
        },
    },
}
