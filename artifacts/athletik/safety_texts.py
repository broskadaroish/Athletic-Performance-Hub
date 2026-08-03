"""
safety_texts.py
───────────────
Zentrale Datei für alle Pflicht- und Sicherheitshinweise der App.
Alle Seiten, PDFs und E-Mails beziehen ihre Hinweise ausschließlich
von hier — kein widersprüchlicher Text an anderen Stellen.

Bruce Football Performance Diagnostics ist kein Medizinprodukt.
Die Software dient ausschließlich der sportlichen Athletikanalyse,
Leistungsentwicklung, Trainingsplanung und Trainingsdokumentation.
"""

# ─── Versionierung ────────────────────────────────────────────────────────────

ZWECKBESTIMMUNG_VERSION = "2.0"

# ─── Offizieller Haftungshinweis (Pflichttext) ───────────────────────────────

HAFTUNGSHINWEIS = (
    "Diese Software dient ausschließlich der sportlichen Athletikanalyse, "
    "Leistungsentwicklung, Trainingsplanung und Trainingsdokumentation.\n\n"
    "Sie ersetzt keine medizinische Untersuchung, Diagnose oder Behandlung "
    "durch Ärztinnen, Ärzte oder andere medizinische Fachpersonen.\n\n"
    "Alle Auswertungen dienen ausschließlich der Unterstützung von "
    "Trainerinnen und Trainern im sportlichen Kontext."
)

HAFTUNGSHINWEIS_KURZ = (
    "Diese Software dient ausschließlich der sportlichen Athletikanalyse, "
    "Leistungsentwicklung, Trainingsplanung und Trainingsdokumentation. "
    "Sie ersetzt keine medizinische Untersuchung, Diagnose oder Behandlung "
    "durch Ärztinnen, Ärzte oder andere medizinische Fachpersonen. "
    "Alle Auswertungen dienen ausschließlich der Unterstützung von "
    "Trainerinnen und Trainern im sportlichen Kontext."
)

# ─── Zweckbestimmung (vollständiger Pflichttext) ──────────────────────────────

ZWECKBESTIMMUNG_TITEL = "Zweckbestimmung und Anwendungshinweise"

ZWECKBESTIMMUNG_TEXT = """\
Diese Anwendung dient ausschliesslich der Dokumentation, Organisation und \
sportlichen Auswertung von Trainings- und Leistungstests.

Die angezeigten Ergebnisse, Bewertungen, Ampelfarben, Hinweise und \
Trainingsempfehlungen sind sportliche Orientierungswerte. \
Sie stellen keine Sportfreigabe und keinen Ersatz fuer eine \
aerztliche Untersuchung dar.

Die Anwendung ersetzt keine aerztliche oder therapeutische Fachberatung.

Bei Schmerzen, Verletzungsverdacht, Schwindel, Atemproblemen, ungewoehnlicher \
Erschoepfung oder anderen gesundheitlichen Beschwerden darf die betroffene \
Person nicht allein aufgrund einer App-Auswertung weitertrainieren. In solchen \
Faellen ist eine qualifizierte Fachperson hinzuzuziehen.

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
Trainingsempfehlungen sind sportliche Orientierungswerte. \
Sie stellen **keine Sportfreigabe** und keinen Ersatz für eine \
ärztliche Untersuchung dar.

Die Anwendung **ersetzt keine** ärztliche oder therapeutische Fachberatung.

Bei Schmerzen, Verletzungsverdacht, Schwindel, Atemproblemen, ungewöhnlicher \
Erschöpfung oder anderen gesundheitlichen Beschwerden darf die betroffene \
Person **nicht allein aufgrund einer App-Auswertung weitertrainieren**. In \
solchen Fällen ist eine qualifizierte Fachperson hinzuzuziehen.

Der Anwender bleibt für die Auswahl, Durchführung und Anpassung des Trainings \
verantwortlich.

Bei Kindern und Jugendlichen müssen Alter, Entwicklungsstand, aktueller \
Gesundheitszustand und Belastbarkeit berücksichtigt werden.\
"""

# ─── Ampeltexte ───────────────────────────────────────────────────────────────

AMPEL_GRUEN = (
    "Im Rahmen der vorliegenden sportlichen Testdaten aktuell kein auffälliger Wert. "
    "Kein Ersatz für eine ärztliche Untersuchung."
)

AMPEL_GELB = (
    "Beobachtungsbedürftiger sportlicher Testwert. "
    "Training anpassen, erneut testen und bei Beschwerden fachlich abklären lassen."
)

AMPEL_ROT = (
    "Deutlich auffälliger sportlicher Testwert oder gemeldete Beschwerden. "
    "Keine automatische Trainingsfreigabe. "
    "Trainerische Prüfung und bei anhaltenden Beschwerden fachärztliche Abklärung empfohlen."
)

AMPEL_FUSSZEILE = (
    "Die Ampelfarbe basiert nur auf den eingegebenen Daten "
    "und dient ausschließlich als sportliche Orientierung."
)

# ─── Trainingsplan-Hinweis ────────────────────────────────────────────────────

TRAININGSPLAN_HINWEIS = (
    "Dieser Plan ist eine allgemeine sportliche Trainingsempfehlung auf "
    "Grundlage der eingegebenen Daten. Er muss durch eine qualifizierte "
    "Trainingsperson geprüft, angepasst und beaufsichtigt werden. "
    "Er ersetzt keine ärztliche oder therapeutische Fachberatung."
)

TRAININGSPLAN_BESCHWERDEN_SPERRE = (
    "Aufgrund der angegebenen Beschwerden wird derzeit keine automatische "
    "Belastungsempfehlung erstellt."
)

# ─── Wachstum / Anthropometrie ────────────────────────────────────────────────

PHV_HINWEIS = (
    "Die angezeigte Einschätzung des Wachstums- oder Reifestatus ist eine "
    "rechnerische Schätzung auf Basis sportlicher Testdaten. "
    "Sie dient ausschließlich der Trainingssteuerung und ist kein Ersatz "
    "für eine ärztliche Beurteilung."
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
    "qualifizierte Fachperson hinzuzuziehen."
)

# ─── Test-Abbruchhinweis ──────────────────────────────────────────────────────

ABBRUCH_HINWEIS = (
    "Der Test ist sofort abzubrechen, wenn Schmerzen, Schwindel, Atemnot, "
    "Brustschmerzen, ungewöhnliche Schwäche oder andere auffällige Beschwerden "
    "auftreten."
)

# ─── PDF-Fußzeile (jede Seite) ────────────────────────────────────────────────

PDF_FUSSZEILE = (
    "Sportliche Athletikanalyse und Trainingsdokumentation \u2013 "
    "kein Ersatz für eine ärztliche Untersuchung."
)

# Kurzversion für Header/Cards
KURZ_HINWEIS = "Sportliche Auswertung \u2013 kein Ersatz für eine ärztliche Untersuchung."

# ─── E-Mail-Vorschlagstext ────────────────────────────────────────────────────

EMAIL_NACHRICHT_VORLAGE = """\
Guten Tag,

anbei erhalten Sie das sportliche Testprotokoll.

Die enthaltenen Ergebnisse und Hinweise dienen ausschließlich der \
Trainingsdokumentation und sportlichen Orientierung. Sie stellen keinen \
Ersatz für eine ärztliche Untersuchung dar.

Freundliche Grüße

{trainername}\
"""
