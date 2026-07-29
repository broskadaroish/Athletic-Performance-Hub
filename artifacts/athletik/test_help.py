"""
Zentrale Testanleitungen — Football Athletik Diagnostik.

Struktur je Test-ID:
    name, kurzbeschreibung, ziel, material, aufbau, aufwaermung,
    durchfuehrung, trainerhinweis, versuche, pause, messwert,
    einheit, gueltiger_versuch, ungueltiger_versuch, fehler,
    sicherheit, bild_pfad, quelle, version, datum,
    felder: { field_id: { label, kurzhilfe, eingabehilfe, einheit, bereich, ziel } }

Erweiterung um Video-Felder (vorbereitet, noch nicht aktiv):
    video_lokal, video_link, video_titel, video_quelle, video_lizenz
"""
from __future__ import annotations

# ─── Pflicht-Texte (Compliance) ──────────────────────────────────────────────

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

# ─── Zentrale Hilfedatenbank ──────────────────────────────────────────────────

TEST_HELP: dict[str, dict] = {

    # ══════════════════════════════════════════════════════════════════════════
    # SPRINT
    # ══════════════════════════════════════════════════════════════════════════
    "sprint": {
        "name": "Sprint-Diagnostik",
        "kurzbeschreibung": (
            "Lineare Beschleunigung und Maximalgeschwindigkeit über 5 m, 10 m, "
            "20 m und 30 m — je 3 Versuche."
        ),
        "ziel": (
            "Überprüfung der Beschleunigungsfähigkeit (0–10 m), der Übergangsphase "
            "(10–20 m) und der Maximalgeschwindigkeit (20–30 m). "
            "Der Beschleunigungsindex zeigt das Verhältnis von Startexplosivität "
            "zu Maximalgeschwindigkeit."
        ),
        "material": (
            "Maßband oder vormarkierte Strecke, Hütchen (5 Stück), "
            "Lichtschranken oder Stoppuhr."
        ),
        "aufbau": (
            "Startlinie markieren. Hütchen bei 5 m, 10 m, 20 m und 30 m aufstellen. "
            "Wenn vorhanden, Lichtschranken an den Messpunkten aufbauen. "
            "Untergrund muss eben, trocken und rutschfest sein. "
            "Hinter der 30-m-Linie mindestens 10 m Auslauffläche sicherstellen."
        ),
        "aufwaermung": (
            "Mindestens 10 Minuten allgemeines Aufwärmen. "
            "Anschließend 2–3 Steigerungsläufe über 30–40 m mit steigender "
            "Intensität (70 %, 85 %, 95 %). "
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
            "Bei Lichtschranken: ganzer Körper muss die Schranke passieren, "
            "nicht nur der vorgestreckte Arm."
        ),
        "versuche": "3 Versuche je Distanz. Der schnellste gültige Versuch wird gewertet.",
        "pause": "2–3 Minuten aktive Pause (lockeres Gehen) zwischen den Versuchen.",
        "messwert": "Zeit in Sekunden",
        "einheit": "Sekunden (s)",
        "gueltiger_versuch": (
            "Korrekter Start hinter der Linie ohne Ausholbewegung, "
            "maximale Beschleunigung, vollständiges Durchlaufen des Ziels "
            "ohne vorzeitiges Abbremsen."
        ),
        "ungueltiger_versuch": (
            "Frühstart (Bewegung vor Startkommando), Ausrutschen, "
            "vorzeitiges Abbremsen vor dem Ziel, Behinderung durch Dritte, "
            "Ausholbewegung beim Start."
        ),
        "fehler": [
            "Ausholbewegung vor dem Start — verfälscht die Reaktions-/Startzeit",
            "Abbremsen kurz vor dem Ziel — gibt zu kurze gemessene Endzeit",
            "Arm beim Durchlaufen einer Lichtschranke vorstrecken — gibt unrealistisch kurze Zeit",
            "Zu kurze Pause zwischen den Versuchen — Ermüdung verfälscht das Ergebnis",
            "Unebene oder rutschige Testfläche — erhöht Verletzungsrisiko und verfälscht Zeiten",
        ],
        "sicherheit": (
            "Testfläche vor dem Test auf Nässe, Unebenheiten und Hindernisse prüfen. "
            "Mindestens 10 m Auslauffläche hinter der 30-m-Linie sicherstellen. "
            "Spieler bei Beschwerden sofort stoppen lassen. "
            "Kein Testen bei Schmerzen, Verletzungen oder Krankheit."
        ),
        "bild_pfad": "assets/tests/sprint/sprint_setup.svg",
        "quelle": "Sporis et al. (2010); Stolen et al. (2005)",
        "version": "1.0",
        "datum": "2026-07-29",
        "video_lokal": None,
        "video_link": None,
        "video_titel": None,
        "video_quelle": None,
        "video_lizenz": None,
        "felder": {
            "sprint_5m": {
                "label": "5 m",
                "ziel": "Messung der Startexplosivität — Reaktion und erste Beschleunigungsschritte.",
                "kurzhilfe": (
                    "Schnellste Zeit über 5 Meter eintragen. "
                    "3 Versuche — bester Versuch zählt. "
                    "Typischer Bereich: 0.90 – 1.60 Sekunden."
                ),
                "eingabehilfe": "Zeit in Sekunden, z. B. 1.05",
                "einheit": "Sekunden (s)",
                "bereich": "Sinnvoller Bereich: 0.90 – 1.60 s",
            },
            "sprint_10m": {
                "label": "10 m",
                "ziel": "Messung der Beschleunigungsleistung — Phase 0 bis 10 Meter.",
                "kurzhilfe": (
                    "Schnellste Zeit über 10 Meter eintragen. "
                    "Die 10-m-Zeit muss größer als die 5-m-Zeit sein. "
                    "Typischer Bereich: 1.60 – 2.50 Sekunden."
                ),
                "eingabehilfe": "Zeit in Sekunden, z. B. 1.78",
                "einheit": "Sekunden (s)",
                "bereich": "Sinnvoller Bereich: 1.60 – 2.50 s",
            },
            "sprint_20m": {
                "label": "20 m",
                "ziel": "Messung der Übergangsphase — Beschleunigung zu Maximalgeschwindigkeit.",
                "kurzhilfe": (
                    "Schnellste Zeit über 20 Meter eintragen. "
                    "Die 20-m-Zeit muss größer als die 10-m-Zeit sein. "
                    "Typischer Bereich: 2.80 – 4.00 Sekunden."
                ),
                "eingabehilfe": "Zeit in Sekunden, z. B. 3.10",
                "einheit": "Sekunden (s)",
                "bereich": "Sinnvoller Bereich: 2.80 – 4.00 s",
            },
            "sprint_30m": {
                "label": "30 m",
                "ziel": "Messung der Maximalgeschwindigkeit — Phase 20 bis 30 Meter.",
                "kurzhilfe": (
                    "Schnellste Zeit über 30 Meter eintragen. "
                    "Die 30-m-Zeit muss größer als die 20-m-Zeit sein. "
                    "Typischer Bereich: 3.90 – 5.50 Sekunden."
                ),
                "eingabehilfe": "Zeit in Sekunden, z. B. 4.50",
                "einheit": "Sekunden (s)",
                "bereich": "Sinnvoller Bereich: 3.90 – 5.50 s",
            },
        },
    },

    # ══════════════════════════════════════════════════════════════════════════
    # STUBS — werden in Phase 3 schrittweise ausgebaut
    # ══════════════════════════════════════════════════════════════════════════
    "y_balance": {
        "name": "Y-Balance-Test",
        "kurzbeschreibung": "Dynamische Gleichgewichts- und Stabilitätsdiagnostik — 3 Richtungen je Bein.",
        "bild_pfad": None,
        "version": "stub",
        "datum": "2026-07-29",
        "felder": {
            "beinlaenge": {"label": "Beinlänge", "kurzhilfe": "Beinlänge in cm messen (ASIS bis Innenknöchel). Z. B. 87.5", "einheit": "cm", "bereich": "Sinnvoller Bereich: 50 – 90 cm"},
            "anterior": {"label": "Anterior", "kurzhilfe": "Reichweite in Vorwärtsrichtung in cm. Z. B. 65", "einheit": "cm", "bereich": "Sinnvoller Bereich: 40 – 90 cm"},
            "posteromedial": {"label": "Posteromedial", "kurzhilfe": "Reichweite schräg hinten-innen in cm. Z. B. 110", "einheit": "cm", "bereich": "Sinnvoller Bereich: 80 – 140 cm"},
            "posterolateral": {"label": "Posterolateral", "kurzhilfe": "Reichweite schräg hinten-außen in cm. Z. B. 100", "einheit": "cm", "bereich": "Sinnvoller Bereich: 75 – 130 cm"},
        },
    },
    "fms": {
        "name": "Functional Movement Screen",
        "kurzbeschreibung": "Bewertung von 7 grundlegenden Bewegungsmustern mit Punkteskala 0–3.",
        "bild_pfad": None,
        "version": "stub",
        "datum": "2026-07-29",
        "felder": {
            "deep_squat": {"label": "Deep Squat", "kurzhilfe": "Bewertung 0–3: 3 = symmetrisch korrekt, 2 = korrekt mit Kompensation, 1 = nicht möglich, 0 = Schmerzen.", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3"},
            "hurdle_step": {"label": "Hurdle Step", "kurzhilfe": "Je Seite bewerten (0–3). Niedrigere Seite zählt.", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3"},
            "inline_lunge": {"label": "Inline Lunge", "kurzhilfe": "Je Seite bewerten (0–3). Niedrigere Seite zählt.", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3"},
            "shoulder": {"label": "Shoulder Mobility", "kurzhilfe": "Je Seite bewerten (0–3). Niedrigere Seite zählt.", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3"},
            "aslr": {"label": "Active Straight Leg Raise", "kurzhilfe": "Je Seite bewerten (0–3). Niedrigere Seite zählt.", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3"},
            "trunk_stability": {"label": "Trunk Stability Push-up", "kurzhilfe": "Bewertung 0–3.", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3"},
            "rotary_stability": {"label": "Rotary Stability", "kurzhilfe": "Je Seite bewerten (0–3). Niedrigere Seite zählt.", "einheit": "Punkte", "bereich": "0, 1, 2 oder 3"},
        },
    },
    "jump": {
        "name": "Sprung-Diagnostik",
        "kurzbeschreibung": "Explosivkraft, Reaktivkraft und Seitenasymmetrie — CMJ, SJ, DJ, Standweit.",
        "bild_pfad": None,
        "version": "stub",
        "datum": "2026-07-29",
        "felder": {
            "cmj_beid": {"label": "CMJ beidbeinig", "kurzhilfe": "Sprunghöhe Countermovement Jump beidbeinig in cm. Z. B. 42", "einheit": "cm", "bereich": "Sinnvoller Bereich: 20 – 70 cm"},
            "cmj_r": {"label": "CMJ rechts", "kurzhilfe": "Sprunghöhe einbeiniger CMJ rechts in cm. Z. B. 32", "einheit": "cm", "bereich": "Sinnvoller Bereich: 15 – 55 cm"},
            "cmj_l": {"label": "CMJ links", "kurzhilfe": "Sprunghöhe einbeiniger CMJ links in cm. Z. B. 31", "einheit": "cm", "bereich": "Sinnvoller Bereich: 15 – 55 cm"},
            "squat_jump": {"label": "Squat Jump", "kurzhilfe": "Sprunghöhe aus der Kniebeuge ohne Gegenbewegung in cm. Z. B. 38", "einheit": "cm", "bereich": "Sinnvoller Bereich: 18 – 65 cm"},
            "dj_hoehe": {"label": "Drop Jump Höhe", "kurzhilfe": "Sprunghöhe nach Drop Jump in cm. Z. B. 36", "einheit": "cm", "bereich": "Sinnvoller Bereich: 15 – 55 cm"},
            "dj_kontakt": {"label": "DJ Kontaktzeit", "kurzhilfe": "Bodenkontaktzeit beim Drop Jump in Sekunden. Z. B. 0.18", "einheit": "Sekunden", "bereich": "Sinnvoller Bereich: 0.08 – 0.35 s"},
            "standweit": {"label": "Standweitsprung", "kurzhilfe": "Sprungweite in cm. Z. B. 215", "einheit": "cm", "bereich": "Sinnvoller Bereich: 100 – 320 cm"},
        },
    },
    "agility": {
        "name": "Richtungswechsel-Diagnostik",
        "kurzbeschreibung": "Agilität und Richtungswechselgeschwindigkeit — 505, 5-10-5, T-Test, Illinois.",
        "bild_pfad": None,
        "version": "stub",
        "datum": "2026-07-29",
        "felder": {
            "t505_r": {"label": "505-Test rechts", "kurzhilfe": "Zeit rechts wenden in Sekunden. Zeitmesszone: 5 m vor und nach der Wendelinie. Z. B. 2.35", "einheit": "Sekunden", "bereich": "Sinnvoller Bereich: 1.80 – 3.20 s"},
            "t505_l": {"label": "505-Test links", "kurzhilfe": "Zeit links wenden in Sekunden. Z. B. 2.40", "einheit": "Sekunden", "bereich": "Sinnvoller Bereich: 1.80 – 3.20 s"},
            "t5_10_5": {"label": "5-10-5", "kurzhilfe": "Gesamtzeit 5-10-5-Test in Sekunden. Z. B. 4.80", "einheit": "Sekunden", "bereich": "Sinnvoller Bereich: 3.80 – 6.00 s"},
            "t_test": {"label": "T-Test", "kurzhilfe": "Gesamtzeit T-Test in Sekunden. Z. B. 9.50", "einheit": "Sekunden", "bereich": "Sinnvoller Bereich: 8.00 – 13.00 s"},
            "illinois": {"label": "Illinois-Test", "kurzhilfe": "Gesamtzeit Illinois-Test in Sekunden. Z. B. 15.50", "einheit": "Sekunden", "bereich": "Sinnvoller Bereich: 13.00 – 20.00 s"},
        },
    },
    "yoyo": {
        "name": "Yo-Yo Ausdauer-Diagnostik",
        "kurzbeschreibung": "Intermittierende Ausdauer — Yo-Yo Intermittent Recovery Test Level 1 und 2.",
        "bild_pfad": None,
        "version": "stub",
        "datum": "2026-07-29",
        "felder": {
            "distanz": {"label": "Erzielte Distanz", "kurzhilfe": "Gesamtlaufstrecke beim Yo-Yo-Test in Metern. Jede absolvierte Stufe = 40 m. Z. B. 1200", "einheit": "Meter", "bereich": "Sinnvoller Bereich: 80 – 4000 m"},
            "hf_max": {"label": "HF max", "kurzhilfe": "Maximale Herzfrequenz direkt nach dem Testende in Schlägen pro Minute. Z. B. 192", "einheit": "bpm", "bereich": "Sinnvoller Bereich: 120 – 220 bpm"},
            "rpe": {"label": "RPE (Borg 6–20)", "kurzhilfe": "Subjektives Belastungsempfinden nach Borg (6 = keine Anstrengung, 20 = maximale Anstrengung). Z. B. 17", "einheit": "Borg-Skala", "bereich": "6 bis 20"},
        },
    },
    "anthropometrie": {
        "name": "Anthropometrie",
        "kurzbeschreibung": "Körpermaße, BMI, Körperzusammensetzung und sportlicher Reifestatus.",
        "bild_pfad": None,
        "version": "stub",
        "datum": "2026-07-29",
        "felder": {
            "groesse": {"label": "Körpergröße", "kurzhilfe": "Körpergröße in cm, aufrecht stehend ohne Schuhe. Z. B. 175", "einheit": "cm", "bereich": "Sinnvoller Bereich: 100 – 220 cm"},
            "gewicht": {"label": "Körpergewicht", "kurzhilfe": "Körpergewicht in kg, möglichst nach dem Sport ohne schwere Kleidung. Z. B. 68", "einheit": "kg", "bereich": "Sinnvoller Bereich: 30 – 150 kg"},
            "koerperfett": {"label": "Körperfettanteil", "kurzhilfe": "Körperfettanteil in Prozent. Z. B. 12.5", "einheit": "%", "bereich": "Sinnvoller Bereich: 4 – 40 %"},
            "muskelmasse": {"label": "Muskelmasse", "kurzhilfe": "Muskelmasse in Prozent der Körpermasse. Z. B. 42.0", "einheit": "%", "bereich": "Sinnvoller Bereich: 25 – 65 %"},
            "sitzhoehe": {"label": "Sitzhöhe", "kurzhilfe": "Sitzhöhe in cm (Scheitel bis Sitzfläche, aufrecht sitzend). Z. B. 91", "einheit": "cm", "bereich": "Sinnvoller Bereich: 50 – 110 cm"},
            "beinlaenge": {"label": "Beinlänge", "kurzhilfe": "Beinlänge in cm (Körpergröße minus Sitzhöhe). Z. B. 84", "einheit": "cm", "bereich": "Sinnvoller Bereich: 40 – 120 cm"},
            "armspann": {"label": "Armspann", "kurzhilfe": "Armspann in cm, beide Arme waagerecht ausgestreckt, Fingerspitze zu Fingerspitze. Z. B. 178", "einheit": "cm", "bereich": "Sinnvoller Bereich: 100 – 250 cm"},
        },
    },
}
