"""
safety_texts.py
───────────────
Zentrale Datei für alle Pflicht- und Sicherheitshinweise der App.
Alle Seiten, PDFs und E-Mails beziehen ihre Hinweise ausschließlich
von hier — kein widersprüchlicher Text an anderen Stellen.
"""

# ─── Versionierung ────────────────────────────────────────────────────────────

ZWECKBESTIMMUNG_VERSION = "1.0"

# ─── Zweckbestimmung (vollständiger Pflichttext) ──────────────────────────────

ZWECKBESTIMMUNG_TITEL = "Zweckbestimmung und Anwendungshinweise"

ZWECKBESTIMMUNG_TEXT = """\
Diese Anwendung dient ausschliesslich der Dokumentation, Organisation und \
sportlichen Auswertung von Trainings- und Leistungstests.

Die angezeigten Ergebnisse, Bewertungen, Ampelfarben, Hinweise und \
Trainingsempfehlungen stellen keine medizinische Diagnose, Untersuchung, \
Behandlung oder Freigabe dar.

Die Anwendung ersetzt keine aerztliche, physiotherapeutische oder sonstige \
medizinische Untersuchung und Beratung.

Bei Schmerzen, Verletzungsverdacht, Schwindel, Atemproblemen, ungewoehnlicher \
Erschoepfung oder anderen gesundheitlichen Beschwerden darf die betroffene \
Person nicht allein aufgrund einer App-Auswertung weitertrainieren. In solchen \
Faellen ist eine medizinisch qualifizierte Fachperson hinzuzuziehen.

Der Anwender bleibt fuer die Auswahl, Durchfuehrung und Anpassung des \
Trainings verantwortlich.

Bei Kindern und Jugendlichen muessen Alter, Entwicklungsstand, aktueller \
Gesundheitszustand und Belastbarkeit beruecksichtigt werden.\
"""

# Unicode-Version für die Bildschirmanzeige (mit Umlauten)
ZWECKBESTIMMUNG_TEXT_DISPLAY = """\
Diese Anwendung dient **ausschließlich** der Dokumentation, Organisation und \
sportlichen Auswertung von Trainings- und Leistungstests.

Die angezeigten Ergebnisse, Bewertungen, Ampelfarben, Hinweise und \
Trainingsempfehlungen stellen **keine medizinische Diagnose, Untersuchung, \
Behandlung oder Freigabe** dar.

Die Anwendung **ersetzt keine** ärztliche, physiotherapeutische oder sonstige \
medizinische Untersuchung und Beratung.

Bei Schmerzen, Verletzungsverdacht, Schwindel, Atemproblemen, ungewöhnlicher \
Erschöpfung oder anderen gesundheitlichen Beschwerden darf die betroffene \
Person **nicht allein aufgrund einer App-Auswertung weitertrainieren**. In \
solchen Fällen ist eine medizinisch qualifizierte Fachperson hinzuzuziehen.

Der Anwender bleibt für die Auswahl, Durchführung und Anpassung des Trainings \
verantwortlich.

Bei Kindern und Jugendlichen müssen Alter, Entwicklungsstand, aktueller \
Gesundheitszustand und Belastbarkeit berücksichtigt werden.\
"""

# ─── Ampeltexte ───────────────────────────────────────────────────────────────

AMPEL_GRUEN = (
    "Im Rahmen der vorliegenden sportlichen Testdaten aktuell kein auffälliger Wert. "
    "Dies ist keine medizinische Freigabe."
)

AMPEL_GELB = (
    "Beobachtungsbedürftiger sportlicher Testwert. "
    "Training anpassen, erneut testen und bei Beschwerden fachlich abklären lassen."
)

AMPEL_ROT = (
    "Deutlich auffälliger sportlicher Testwert oder gemeldete Beschwerden. "
    "Keine automatische Trainingsfreigabe. "
    "Trainerische Prüfung und gegebenenfalls medizinische Abklärung erforderlich."
)

AMPEL_FUSSZEILE = (
    "Die Ampelfarbe basiert nur auf den eingegebenen Daten "
    "und ersetzt keine medizinische Beurteilung."
)

# ─── Trainingsplan-Hinweis ────────────────────────────────────────────────────

TRAININGSPLAN_HINWEIS = (
    "Dieser Plan ist eine allgemeine sportliche Trainingsempfehlung auf "
    "Grundlage der eingegebenen Daten. Er muss durch eine qualifizierte "
    "Trainingsperson geprüft, angepasst und beaufsichtigt werden. "
    "Er ersetzt keine medizinische oder physiotherapeutische Behandlung."
)

TRAININGSPLAN_BESCHWERDEN_SPERRE = (
    "Aufgrund der angegebenen Beschwerden wird derzeit keine automatische "
    "Belastungsempfehlung erstellt."
)

# ─── Wachstum / Anthropometrie ────────────────────────────────────────────────

PHV_HINWEIS = (
    "Die angezeigte Einschätzung des Wachstums- oder Reifestatus ist eine "
    "rechnerische Schätzung. Sie stellt keine medizinische, pädiatrische "
    "oder endokrinologische Beurteilung dar."
)

# ─── FMS / Y-Balance ──────────────────────────────────────────────────────────

FMS_HINWEIS = (
    "FMS- und Y-Balance-Ergebnisse sind keine zuverlässige Vorhersage "
    "einer Verletzung. Die dargestellten Werte dienen als sportliche "
    "Orientierung und allgemeine Trainingsempfehlung."
)

# ─── Beschwerden ──────────────────────────────────────────────────────────────

BESCHWERDEN_HINWEIS = (
    "Es wurden Beschwerden angegeben. Die App kann deren Ursache oder Schwere "
    "nicht beurteilen. Die weitere Belastung muss verantwortungsvoll geprüft "
    "werden. Bei starken, anhaltenden oder zunehmenden Beschwerden ist eine "
    "medizinische Fachperson hinzuzuziehen."
)

# ─── Test-Abbruchhinweis ──────────────────────────────────────────────────────

ABBRUCH_HINWEIS = (
    "Der Test ist sofort abzubrechen, wenn Schmerzen, Schwindel, Atemnot, "
    "Brustschmerzen, ungewöhnliche Schwäche oder andere auffällige Beschwerden "
    "auftreten."
)

# ─── PDF-Fußzeile (jede Seite) ────────────────────────────────────────────────

PDF_FUSSZEILE = (
    "Sportliche Trainings- und Dokumentationshilfe \u2013 "
    "keine medizinische Diagnose oder Freigabe."
)

# Kurzversion für Header/Cards
KURZ_HINWEIS = "Sportliche Auswertung \u2013 keine medizinische Diagnose oder Freigabe."

# ─── E-Mail-Vorschlagstext ────────────────────────────────────────────────────

EMAIL_NACHRICHT_VORLAGE = """\
Guten Tag,

anbei erhalten Sie das sportliche Testprotokoll.

Die enthaltenen Ergebnisse und Hinweise dienen ausschließlich der \
Trainingsdokumentation und sportlichen Orientierung. Sie stellen keine \
medizinische Diagnose oder Freigabe dar.

Freundliche Grüße

{trainername}\
"""
