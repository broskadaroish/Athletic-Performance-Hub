"""
Gemeinsame Warm-up-Datenquelle für Trainingsplan-UI und PDF.

Die Auswahl wird ohne neue Tabelle als trainingsplan-Zeile mit
bereich="Warm-up" gespeichert. Diese Datei enthält ausschließlich die
anzeigbaren Programme und die Übersetzung der gespeicherten Planzeile.
"""

from __future__ import annotations

import json

WARMUP_BEREICH = "Warm-up"
APH_STANDARD = "APH Standard-Warm-up"
FIFA_KOMPLETT = "FIFA 11+ komplett"
FIFA_INDIVIDUELL = "FIFA 11+ individuell"
KEIN_WARMUP = "Kein Warm-up"

WARMUP_OPTIONEN = [APH_STANDARD, FIFA_KOMPLETT, FIFA_INDIVIDUELL, KEIN_WARMUP]
FIFA_TEILE = ("Teil 1", "Teil 2", "Teil 3")

# Das bestehende APH-Programm bleibt fachlich unverändert; es ist nun die
# gemeinsame Quelle statt je einer hardcodierten UI- und PDF-Liste.
APH_STANDARD_ROWS = (
    ("Aktivierungslauf", "5 min", "Leichtes Joggen, Seitwärtsläufe, Rückwärtsläufe"),
    ("Hüftkreisen beidbeinig", "2×10", "Kontrolliert, langsam"),
    ("World's Greatest Stretch", "2×5/Seite", "Tief und kontrolliert"),
    ("Leg Swings vor/rück", "2×10/Seite", "Freies Pendeln, zunehmende Amplitude"),
    ("Leg Swings seitlich", "2×10/Seite", "Lateral, gestreckt"),
    ("Glute Bridge", "2×10", "Langsam, Becken oben halten 2 s"),
    ("Mini-Band Walk", "2×10 m", "Lateral, Knie leicht gebeugt"),
)

# Struktur und Übungsnamen folgen der bereitgestellten DFB/FIFA-11+-Vorlage.
# Für nicht eindeutig lesbare Wiederholungsangaben wird bewusst kein Wert
# ergänzt; die Vorlage bleibt die Durchführungsreferenz.
FIFA_11_PLUS = {
    "Teil 1": {
        "titel": "Laufübungen",
        "dauer_min": 8,
        "level": None,
        "uebungen": (
            "Laufen geradeaus",
            "Laufen Hüftdrehung nach außen",
            "Laufen Hüftdrehung nach innen",
            "Laufen Seitgalopp",
            "Laufen Schulterkontakt",
            "Laufen vor und zurück sprinten",
        ),
    },
    "Teil 2": {
        "titel": "Kraft · Plyometrie · Gleichgewicht",
        "dauer_min": 10,
        "level": {
            1: (
                "Unterarmstütz halten",
                "Seitlicher Unterarmstütz halten",
                "Oberschenkelrückseite Anfänger",
                "Einbeinstand mit dem Ball",
                "Kniebeugen auf die Zehenspitzen",
                "Springen: Sprünge nach oben",
            ),
            2: (
                "Unterarmstütz Beine wechselnd anheben",
                "Seitlicher Unterarmstütz Hüfte heben und senken",
                "Oberschenkelrückseite Fortgeschrittene",
                "Einbeinstand: Ball gegenseitig zuwerfen",
                "Kniebeugen Ausfallschritte",
                "Springen: Sprünge zur Seite",
            ),
            3: (
                "Unterarmstütz Bein anheben und halten",
                "Seitlicher Unterarmstütz Bein heben und senken",
                "Oberschenkelrückseite Profi",
                "Einbeinstand Gleichgewicht testen",
                "Kniebeugen auf einem Bein",
                "Springen: Kreuzsprünge",
            ),
        },
    },
    "Teil 3": {
        "titel": "Laufübungen · dynamischer Abschluss",
        "dauer_min": 8,
        "level": None,
        "uebungen": (
            "Laufen über das Spielfeld",
            "Laufen Hoch-Weit-Sprünge",
            "Laufen Richtungswechsel",
        ),
    },
}


def warmup_meta_kodieren(art: str, level: int = 1,
                         teile: list[str] | tuple[str, ...] | None = None,
                         aph_dauer_min: int | None = None) -> str:
    """Kompaktes, robust lesbares Metadatenformat innerhalb einer Planzeile."""
    payload = {
        "art": art,
        "level": max(1, min(3, int(level or 1))),
        "teile": list(teile or FIFA_TEILE),
    }
    if art == APH_STANDARD and aph_dauer_min is not None:
        payload["aph_dauer_min"] = max(0, int(aph_dauer_min))
    return "WARMUP_META:" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def warmup_meta_lesen(row: dict | None) -> dict:
    """Liest eine Warm-up-Planzeile; None bedeutet Legacy-APH-Standard."""
    if not row or row.get("bereich") != WARMUP_BEREICH:
        return {
            "art": APH_STANDARD, "level": 1, "teile": list(FIFA_TEILE),
            "aph_dauer_min": None, "legacy": True,
        }

    raw = str(row.get("notiz") or "")
    if raw.startswith("WARMUP_META:"):
        try:
            value = json.loads(raw[len("WARMUP_META:"):])
            art = value.get("art")
            if art in WARMUP_OPTIONEN:
                teile = [teil for teil in value.get("teile", FIFA_TEILE) if teil in FIFA_TEILE]
                return {
                    "art": art,
                    "level": max(1, min(3, int(value.get("level") or 1))),
                    "teile": teile or list(FIFA_TEILE),
                    "aph_dauer_min": (
                        max(0, int(value["aph_dauer_min"]))
                        if value.get("aph_dauer_min") is not None else None
                    ),
                    "legacy": False,
                }
        except (TypeError, ValueError, json.JSONDecodeError):
            pass

    art = str(row.get("uebung") or APH_STANDARD)
    return {
        "art": art if art in WARMUP_OPTIONEN else APH_STANDARD,
        "level": max(1, min(3, int(row.get("rpe") or 1))),
        "teile": list(FIFA_TEILE),
        "aph_dauer_min": None,
        "legacy": False,
    }


def warmup_details(art: str, level: int = 1,
                   teile: list[str] | tuple[str, ...] | None = None,
                   aph_dauer_min: int = 8) -> dict:
    """Erzeugt die gemeinsame UI-/PDF-Anzeige für eine Warm-up-Auswahl."""
    level = max(1, min(3, int(level or 1)))
    teile = [teil for teil in (teile or FIFA_TEILE) if teil in FIFA_TEILE]

    if art == KEIN_WARMUP:
        return {"titel": KEIN_WARMUP, "dauer_min": 0, "zeilen": [], "hinweis": ""}

    if art == APH_STANDARD:
        return {
            "titel": APH_STANDARD,
            "dauer_min": int(aph_dauer_min),
            "zeilen": [
                {"teil": "APH", "uebung": name, "volumen": volumen, "hinweis": hinweis}
                for name, volumen, hinweis in APH_STANDARD_ROWS
            ],
            "hinweis": "Standard-Aktivierung",
        }

    if art == FIFA_KOMPLETT:
        teile = list(FIFA_TEILE)
    elif art != FIFA_INDIVIDUELL:
        art = APH_STANDARD
        return warmup_details(art, level, teile, aph_dauer_min)

    zeilen: list[dict] = []
    dauer = 0
    for teil in teile:
        config = FIFA_11_PLUS[teil]
        dauer += config["dauer_min"]
        if teil == "Teil 2":
            uebungen = config["level"][level]
            teil_label = f"Teil 2 · Level {level}"
        else:
            uebungen = config["uebungen"]
            teil_label = teil
        for uebung in uebungen:
            zeilen.append({
                "teil": teil_label,
                "uebung": uebung,
                "volumen": "gemäß FIFA-11+-Vorlage",
                "hinweis": config["titel"],
            })

    komplett = art == FIFA_KOMPLETT
    return {
        "titel": "FIFA 11+ komplett" if komplett else "FIFA 11+ individuell",
        "dauer_min": dauer,
        "zeilen": zeilen,
        "hinweis": (
            f"Teil 1 + Teil 2 (Level {level}) + Teil 3"
            if komplett else
            f"{' + '.join(teile)}" + (f" · Teil 2 Level {level}" if "Teil 2" in teile else "")
        ),
    }