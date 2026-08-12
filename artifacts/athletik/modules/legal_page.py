"""
Legal pages — Impressum, Datenschutzerklärung, AGB/Nutzungsbedingungen.

Alle drei Funktionen sind:
- Ohne Login erreichbar (via _legal_show mechanism in app.py)
- In der Über-Seite per Sub-Navigation erreichbar
- Mobile-optimiert (kein horizontal scroll, vernünftige Schriftgröße)
- Desktop-begrenzt (max-width:720px)
- translate="no" Wrapper gegen Browser-Auto-Übersetzung

Verwendete Kontaktadressen:
  support@aphsystem.de  — Support, Datenschutz, Anfragen (sichtbar)
  noreply@aphsystem.de  — Nur System-E-Mails (nicht verändern)
"""
import streamlit as st

_SUPPORT  = "support@aphsystem.de"
_NOREPLY  = "noreply@aphsystem.de"
_NAME     = "Athletic Performance Hub"
_ANBIETER = "Broska Daroish"
_ADRESSE  = "Am Remswasen 57, 73527 Schwäbisch Gmünd, Deutschland"


# ── Interne Hilfs-Renderer ─────────────────────────────────────────────────────

def _page_header(icon: str, title: str) -> None:
    st.markdown(
        f'<div translate="no" style="margin-bottom:16px">'
        f'<h2 style="color:#e6edf3;font-size:22px;font-weight:800;margin:0 0 6px">'
        f'{icon} {title}</h2>'
        f'<hr style="border-color:#21262d;margin:0"></div>',
        unsafe_allow_html=True,
    )


def _anbieter_block() -> None:
    st.markdown(
        '<div translate="no" style="background:#161b22;border:1px solid #30363d;'
        'border-radius:8px;padding:16px 18px;margin-bottom:16px;font-size:14px;'
        'line-height:1.8;color:#c9d1d9">'
        '<strong style="color:#e6edf3">Broska Daroish</strong><br>'
        'Athletic Performance Hub<br>'
        'Am Remswasen 57<br>'
        '73527 Schwäbisch Gmünd<br>'
        'Deutschland<br>'
        '<br>'
        'E-Mail: <a href="mailto:support@aphsystem.de" style="color:#58a6ff">'
        'support@aphsystem.de</a>'
        '</div>',
        unsafe_allow_html=True,
    )


def _max_width_open() -> None:
    st.markdown(
        '<div translate="no" style="max-width:720px;margin:0 auto;padding:0 4px">',
        unsafe_allow_html=True,
    )


def _max_width_close() -> None:
    st.markdown('</div>', unsafe_allow_html=True)


# ── Öffentliche Seiten ─────────────────────────────────────────────────────────

def page_impressum() -> None:
    """Impressum gemäß § 5 DDG."""
    _page_header("📋", "Impressum")

    st.markdown("*Angaben gemäß § 5 DDG*")
    st.markdown("")

    _anbieter_block()

    st.markdown("### Verantwortlich für den Inhalt")
    st.markdown(
        '<div translate="no" style="font-size:14px;line-height:1.8;color:#c9d1d9">'
        'Broska Daroish<br>'
        'Am Remswasen 57<br>'
        '73527 Schwäbisch Gmünd<br>'
        'Deutschland'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    st.markdown(
        f'### <span translate="no">Athletic Performance Hub</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Athletic Performance Hub ist eine digitale Plattform zur Unterstützung von "
        "Trainern und Vereinen bei sportlicher Leistungsdiagnostik, Trainingsplanung, "
        "Trainingssteuerung und Dokumentation der sportlichen Entwicklung von Athleten."
    )

    st.markdown("### Hinweis zu sportlichen Auswertungen")
    st.markdown(
        "Die über Athletic Performance Hub bereitgestellten Testergebnisse, Scores, "
        "Auswertungen, Auffälligkeiten, Trainingsschwerpunkte und Trainingsempfehlungen "
        "dienen ausschließlich der sportlichen Leistungsdiagnostik und Trainingsplanung.\n\n"
        "Sie stellen **keine medizinische Diagnose** dar und ersetzen keine ärztliche, "
        "physiotherapeutische oder sonstige medizinische Untersuchung oder Behandlung.\n\n"
        "Bei Schmerzen, Verletzungen oder gesundheitlichen Beschwerden sollte eine "
        "entsprechend qualifizierte medizinische Fachperson hinzugezogen werden."
    )

    st.markdown("### Haftung für Inhalte")
    st.markdown(
        "Die Inhalte und Funktionen von Athletic Performance Hub werden mit Sorgfalt "
        "entwickelt und bereitgestellt.\n\n"
        "Eine Gewähr dafür, dass sämtliche sportlichen Auswertungen und "
        "Trainingsempfehlungen für jeden Athleten und jede individuelle Situation geeignet "
        "sind, wird nicht übernommen.\n\n"
        "Die fachliche Entscheidung über die konkrete Anwendung von Trainingsmaßnahmen "
        "verbleibt beim verantwortlichen Trainer bzw. der jeweils zuständigen Fachperson."
    )

    st.markdown("### Urheberrecht")
    st.markdown(
        "Die vom Anbieter erstellten Inhalte, Texte, Strukturen, Auswertungslogiken, "
        "Trainingslogiken, Darstellungen und sonstigen Bestandteile von Athletic Performance "
        "Hub unterliegen, soweit gesetzlich geschützt, dem deutschen Urheberrecht.\n\n"
        "Eine Vervielfältigung, Bearbeitung, Verbreitung oder sonstige Nutzung außerhalb "
        "der gesetzlich zulässigen Grenzen bedarf der vorherigen Zustimmung des "
        "Rechteinhabers."
    )
    st.markdown(
        '<div translate="no" style="font-size:13px;color:#8b949e;margin-top:12px">'
        '© 2026 Broska Daroish – Athletic Performance Hub. Alle Rechte vorbehalten.'
        '</div>',
        unsafe_allow_html=True,
    )


def page_datenschutz() -> None:
    """Datenschutzerklärung gemäß DSGVO."""
    _page_header("🔒", "Datenschutzerklärung")

    # 1. Verantwortlicher
    st.markdown("### 1. Verantwortlicher")
    st.markdown(
        "Verantwortlich für die Verarbeitung personenbezogener Daten im Zusammenhang "
        "mit Athletic Performance Hub ist:"
    )
    _anbieter_block()

    # 2. Allgemeine Hinweise
    st.markdown("### 2. Allgemeine Hinweise")
    st.markdown(
        "Der Schutz personenbezogener Daten ist uns wichtig.\n\n"
        "Athletic Performance Hub verarbeitet personenbezogene Daten ausschließlich im "
        "Rahmen der geltenden datenschutzrechtlichen Vorschriften, insbesondere der "
        "Datenschutz-Grundverordnung (DSGVO), des Bundesdatenschutzgesetzes (BDSG) und "
        "der einschlägigen Vorschriften für digitale Dienste.\n\n"
        "Diese Datenschutzerklärung informiert darüber, welche personenbezogenen Daten "
        "bei der Nutzung von Athletic Performance Hub verarbeitet werden, zu welchen "
        "Zwecken dies erfolgt und welche Rechte betroffene Personen besitzen."
    )

    # 3. Hosting
    st.markdown("### 3. Hosting und technische Bereitstellung")
    st.markdown(
        "Athletic Performance Hub wird produktiv auf Server-Infrastruktur der "
        '<span translate="no">IONOS SE, Elgendorfer Straße 57, 56410 Montabaur, Deutschland</span>'
        ", betrieben.\n\n"
        "Im Rahmen des Hostings können personenbezogene Daten verarbeitet werden, "
        "die bei der Nutzung der Anwendung entstehen oder innerhalb der Anwendung "
        "gespeichert werden. Dazu können insbesondere gehören:",
        unsafe_allow_html=True,
    )
    st.markdown(
        "- IP-Adresse\n"
        "- Zeitpunkt des Zugriffs\n"
        "- technische Verbindungsinformationen\n"
        "- Server- und Fehlerprotokolle\n"
        "- Benutzer- und Accountdaten\n"
        "- innerhalb der Anwendung gespeicherte Daten"
    )
    st.markdown(
        "Die Verarbeitung erfolgt zur sicheren, stabilen und funktionsfähigen "
        "Bereitstellung von Athletic Performance Hub.\n\n"
        "Soweit IONOS personenbezogene Daten in unserem Auftrag verarbeitet, erfolgt "
        "dies auf Grundlage einer Auftragsverarbeitung gemäß Art. 28 DSGVO."
    )

    # 4. Entwicklung
    st.markdown("### 4. Entwicklung und Softwarebereitstellung")
    st.markdown(
        "Für die Entwicklung von Athletic Performance Hub werden Entwicklungs- und "
        "Versionsverwaltungssysteme eingesetzt.\n\n"
        "Der Anwendungscode wird unter anderem mit "
        '<span translate="no">Replit</span>'
        " entwickelt und über "
        '<span translate="no">GitHub</span>'
        " verwaltet bzw. für die Bereitstellung auf der Produktivumgebung verwendet.\n\n"
        "Die produktiven Benutzer-, Spieler-, Diagnose- und Trainingsdaten werden nach "
        "dem vorgesehenen Systemaufbau nicht als Bestandteil des Quellcode-Repositories "
        "gespeichert.\n\n"
        "Produktive Datenbanken, Zugangsdaten, Passwörter, SMTP-Passwörter, "
        "Session-Tokens und sonstige Secrets dürfen insbesondere nicht im für die "
        "Quellcodeverwaltung bestimmten Repository gespeichert werden.",
        unsafe_allow_html=True,
    )

    # 5. Registrierung
    st.markdown("### 5. Registrierung und Benutzerkonto")
    st.markdown(
        "Für die Nutzung von Athletic Performance Hub kann die Erstellung eines "
        "Benutzerkontos erforderlich sein. Dabei können insbesondere folgende Daten "
        "verarbeitet werden:"
    )
    st.markdown(
        "- Vorname, Nachname\n"
        "- Benutzername\n"
        "- E-Mail-Adresse\n"
        "- Passwort in technisch gesicherter Form\n"
        "- Trainer- oder Vereinszuordnung\n"
        "- Vereins- bzw. Organisationsname\n"
        "- Rechnungsanschrift\n"
        "- Vertragsdaten\n"
        "- Paket- und Lizenzinformationen\n"
        "- Registrierungsdatum\n"
        "- E-Mail-Verifizierungsstatus\n"
        "- Accountstatus\n"
        "- Zeitpunkt des letzten Logins"
    )
    st.markdown(
        "Die Verarbeitung erfolgt insbesondere zur Durchführung des Nutzungs- bzw. "
        "Vertragsverhältnisses, zur Benutzerverwaltung, zur Authentifizierung und zur "
        "Sicherheit der Anwendung.\n\n"
        "Rechtsgrundlage ist insbesondere Art. 6 Abs. 1 lit. b DSGVO, soweit die "
        "Verarbeitung zur Durchführung eines Vertrags oder vorvertraglicher Maßnahmen "
        "erforderlich ist. Soweit gesetzliche Pflichten bestehen, kann die Verarbeitung "
        "außerdem auf Art. 6 Abs. 1 lit. c DSGVO beruhen."
    )

    # 6. E-Mail-Verifikation
    st.markdown("### 6. E-Mail-Verifikation")
    st.markdown(
        "Nach der Registrierung kann eine Bestätigung der angegebenen E-Mail-Adresse "
        "erforderlich sein.\n\n"
        "Hierfür wird ein zeitlich begrenzter Verifizierungslink bzw. "
        "Verifizierungstoken erzeugt und an die hinterlegte E-Mail-Adresse versendet.\n\n"
        "Die Verarbeitung dient insbesondere der Überprüfung der angegebenen "
        "E-Mail-Adresse und dem Schutz vor missbräuchlichen Registrierungen."
    )

    # 7. Passwort vergessen
    st.markdown("### 7. Passwort vergessen und Benutzername vergessen")
    st.markdown(
        "Athletic Performance Hub bietet Funktionen zur Wiederherstellung des Zugangs.\n\n"
        "Beim Zurücksetzen eines Passworts wird ein zeitlich begrenzter Sicherheitslink "
        "bzw. Token an die hinterlegte und berechtigte E-Mail-Adresse versendet.\n\n"
        "Passwörter werden nicht im Klartext per E-Mail versendet.\n\n"
        "Bei einer zulässigen Benutzername-Erinnerung kann der zum Konto gehörende "
        "Benutzername an die hinterlegte E-Mail-Adresse übermittelt werden."
    )

    # 8. E-Mail-Versand
    st.markdown("### 8. E-Mail-Versand")
    st.markdown(
        "Für System- und Supportkommunikation werden E-Mail-Dienste von "
        '<span translate="no">IONOS</span>'
        " verwendet.\n\n"
        "Automatische System-E-Mails können insbesondere über "
        '[noreply@aphsystem.de](mailto:noreply@aphsystem.de)'
        " versendet werden. Dazu gehören beispielsweise:\n\n"
        "- Registrierungsbestätigung\n"
        "- E-Mail-Verifikation\n"
        "- Passwort-Reset\n"
        "- Benutzername-Erinnerung\n"
        "- sicherheits- oder kontobezogene Nachrichten\n\n"
        "Für Supportanfragen wird verwendet: "
        '[support@aphsystem.de](mailto:support@aphsystem.de)\n\n'
        "Wenn Sie uns per E-Mail kontaktieren, werden die von Ihnen übermittelten "
        "Daten zur Bearbeitung der Anfrage verarbeitet.",
        unsafe_allow_html=True,
    )

    # 9. Spieler- und Athletendaten
    st.markdown("### 9. Spieler- und Athletendaten")
    st.markdown(
        "Trainer und Vereine können innerhalb von Athletic Performance Hub Spieler bzw. "
        "Athleten verwalten. Je nach Nutzung der Funktionen können insbesondere folgende "
        "Daten verarbeitet werden:"
    )
    st.markdown(
        "- Vorname und Nachname\n"
        "- Geburtsdatum bzw. Geburtsjahr\n"
        "- Alter, Verein, Mannschaft, Spielposition, Spielbein\n"
        "- sportbezogene Profildaten\n"
        "- Körpergröße, Gewicht\n"
        "- sportliche Leistungsdaten\n"
        "- Trainingsdaten, Testhistorien, Entwicklungsdaten\n"
        "- Trainerbeobachtungen und Notizen"
    )
    st.markdown(
        "Die Daten dienen insbesondere der Organisation, sportlichen "
        "Leistungsdiagnostik, Trainingsplanung, Trainingssteuerung und Dokumentation "
        "der sportlichen Entwicklung."
    )

    # 10. Leistungsdiagnostische Daten
    st.markdown("### 10. Leistungsdiagnostische Daten")
    st.markdown(
        "Athletic Performance Hub ermöglicht die Erfassung und Auswertung verschiedener "
        "sportlicher Tests. Dazu können insbesondere gehören:\n\n"
        "**FMS-Daten:** Ergebnisse einzelner Bewegungsaufgaben, Gesamtwerte, "
        "Seitenunterschiede, sportbezogene Auffälligkeiten\n\n"
        "**Y-Balance-Daten:** Reichweiten, Seitenunterschiede, Composite Scores, "
        "sportbezogene Auffälligkeiten\n\n"
        "**Sprintdaten:** Sprintzeiten, Zwischenzeiten, Geschwindigkeit, "
        "Beschleunigungswerte, Leistungsentwicklung\n\n"
        "Weitere sportliche Test- und Leistungsdaten können verarbeitet werden, soweit "
        "entsprechende Funktionen von Athletic Performance Hub genutzt werden."
    )

    # 11. Trainingsdaten
    st.markdown("### 11. Trainingsdaten und Trainingspläne")
    st.markdown(
        "Athletic Performance Hub verarbeitet Daten zur Erstellung und Verwaltung von "
        "Trainingsplänen. Dazu können insbesondere gehören:"
    )
    st.markdown(
        "- Trainingsschwerpunkte, Übungen\n"
        "- Trainingsdauer, Belastungsparameter\n"
        "- Trainingshäufigkeit, absolvierte Einheiten\n"
        "- Notizen, Trainingshistorie\n"
        "- Änderungen und Ergänzungen von Trainingsplänen"
    )
    st.markdown("Die Verarbeitung dient der sportlichen Trainingsplanung und Dokumentation.")

    # 12. Verletzungen
    st.markdown("### 12. Verletzungen und gesundheitsbezogene Angaben")
    st.markdown(
        "Soweit innerhalb von Athletic Performance Hub Angaben über Verletzungen, "
        "Schmerzen, gesundheitliche Einschränkungen oder vergleichbare Informationen "
        "gespeichert werden, können Gesundheitsdaten und damit besondere Kategorien "
        "personenbezogener Daten im Sinne des Art. 9 DSGVO betroffen sein.\n\n"
        "Für solche Daten gelten erhöhte datenschutzrechtliche Anforderungen.\n\n"
        "Trainer und Vereine dürfen solche Informationen nur erfassen, wenn hierfür eine "
        "geeignete Rechtsgrundlage nach Art. 9 DSGVO besteht.\n\n"
        "Athletic Performance Hub stellt keine medizinischen Diagnosen."
    )

    # 13. Minderjährige
    st.markdown("### 13. Minderjährige Athleten")
    st.markdown(
        "Athletic Performance Hub kann für die sportliche Betreuung minderjähriger "
        "Athleten eingesetzt werden.\n\n"
        "Trainer und Vereine, die personenbezogene Daten Minderjähriger in Athletic "
        "Performance Hub eintragen, sind dafür verantwortlich, dass die Verarbeitung "
        "dieser Daten rechtmäßig erfolgt und erforderliche Informationen, Zustimmungen "
        "oder Einwilligungen eingeholt werden.\n\n"
        "Dies gilt insbesondere bei besonders schutzbedürftigen bzw. "
        "gesundheitsbezogenen Daten."
    )

    # 14. Verantwortlichkeit Trainer
    st.markdown("### 14. Verantwortlichkeit von Trainern und Vereinen")
    st.markdown(
        "Soweit Trainer oder Vereine eigenständig personenbezogene Daten ihrer Spieler "
        "bzw. Athleten in Athletic Performance Hub eingeben und über Zwecke und "
        "wesentliche Mittel der Verarbeitung entscheiden, sind die jeweiligen "
        "datenschutzrechtlichen Rollen nach den Umständen des konkreten "
        "Nutzungsverhältnisses zu bestimmen.\n\n"
        "Soweit Athletic Performance Hub personenbezogene Daten im Auftrag eines "
        "Trainers oder Vereins verarbeitet, ist eine Vereinbarung zur "
        "Auftragsverarbeitung gemäß Art. 28 DSGVO abzuschließen.\n\n"
        "Für Vereins- und Geschäftskunden sollte daher bei entsprechender "
        "Auftragsverarbeitung eine entsprechende AVV bereitgestellt werden."
    )

    # 15. Mandantentrennung
    st.markdown("### 15. Mandantentrennung")
    st.markdown(
        "Athletic Performance Hub ist als mandantenfähige Anwendung aufgebaut.\n\n"
        "Daten verschiedener Trainer und Vereine werden logisch voneinander getrennt.\n\n"
        "Ein Trainer oder Verein soll grundsätzlich ausschließlich auf die Daten "
        "zugreifen können, die seinem eigenen Kunden- bzw. Organisationsbereich "
        "zugeordnet sind und für die entsprechende Berechtigungen bestehen.\n\n"
        "Administrative Zugriffe können im erforderlichen Umfang für Betrieb, Support, "
        "Sicherheit, Fehlerbehebung und Kundenverwaltung erfolgen."
    )

    # 16. Session-Cookie
    st.markdown("### 16. Session-Cookie")
    st.markdown(
        "Athletic Performance Hub verwendet einen technisch notwendigen Session-Cookie, "
        "um einen angemeldeten Benutzer während seiner Sitzung zu authentifizieren und "
        "die Anmeldung bei internen Seitenwechseln aufrechtzuerhalten.\n\n"
        "Hierfür wird insbesondere die Sitzungskennung **ath_sid** verwendet.\n\n"
        "Der Cookie dient der Authentifizierung und Sicherheit der Anwendung. "
        "Er wird nicht für Werbe- oder Trackingzwecke eingesetzt."
    )

    # 17. Keine Werbe-Cookies
    st.markdown("### 17. Keine Werbe- oder Tracking-Cookies")
    st.markdown(
        "Nach dem derzeit vorgesehenen Aufbau verwendet Athletic Performance Hub keine "
        "eigenen Cookies für personalisierte Werbung oder Marketingtracking.\n\n"
        "Sollte zukünftig ein Analyse-, Marketing- oder vergleichbarer nicht technisch "
        "notwendiger Dienst integriert werden, wird diese Datenschutzerklärung "
        "entsprechend angepasst und, soweit erforderlich, eine Einwilligung eingeholt."
    )

    # 18. Sicherheitsprotokolle
    st.markdown("### 18. Server- und Sicherheitsprotokolle")
    st.markdown(
        "Zur Sicherstellung eines stabilen und sicheren Betriebs können technische "
        "Protokolldaten verarbeitet werden. Hierzu können insbesondere gehören:"
    )
    st.markdown(
        "- IP-Adresse, Datum und Uhrzeit\n"
        "- aufgerufene Ressource\n"
        "- technische Fehler\n"
        "- Login- und Sicherheitsereignisse\n"
        "- Browser- und Geräteinformationen"
    )
    st.markdown(
        "Die Verarbeitung dient insbesondere der technischen Bereitstellung, "
        "Fehleranalyse, IT-Sicherheit und Missbrauchsprävention."
    )

    # 19. Datensicherheit
    st.markdown("### 19. Datensicherheit")
    st.markdown(
        "Athletic Performance Hub setzt technische und organisatorische Maßnahmen ein, "
        "um personenbezogene Daten vor Verlust, unberechtigtem Zugriff und Manipulation "
        "zu schützen. Hierzu gehören nach dem vorgesehenen System insbesondere:"
    )
    st.markdown(
        "- Benutzer- und Rollenverwaltung\n"
        "- Mandantentrennung\n"
        "- E-Mail-Verifikation\n"
        "- sichere Passwortspeicherung\n"
        "- Sessionverwaltung\n"
        "- Zugriffsbeschränkungen\n"
        "- HTTPS-verschlüsselte Übertragung\n"
        "- serverseitige Zugriffskontrollen\n"
        "- Datensicherungen"
    )
    st.markdown(
        "Die Sicherheitsmaßnahmen werden entsprechend der technischen Entwicklung "
        "überprüft und weiterentwickelt."
    )

    # 20. Datensicherung
    st.markdown("### 20. Datensicherung")
    st.markdown(
        "Zur Vermeidung unbeabsichtigten Datenverlusts können Sicherungskopien der "
        "produktiven Daten erstellt werden.\n\n"
        "Sicherungen dienen ausschließlich der Wiederherstellung nach technischen "
        "Störungen, Datenverlust oder vergleichbaren Ereignissen.\n\n"
        "Der Zugriff auf Sicherungen ist auf berechtigte administrative Zwecke "
        "zu beschränken."
    )

    # 21. Speicherdauer
    st.markdown("### 21. Speicherdauer")
    st.markdown(
        "Personenbezogene Daten werden nur so lange gespeichert, wie sie für den "
        "jeweiligen Verarbeitungszweck erforderlich sind oder gesetzliche "
        "Aufbewahrungspflichten bestehen.\n\n"
        "Account-, Vertrags- und Rechnungsdaten können aufgrund handels- oder "
        "steuerrechtlicher Anforderungen über das Ende des Vertrags hinaus gespeichert "
        "werden.\n\n"
        "Eine Kündigung führt daher nicht zwingend zur sofortigen Löschung sämtlicher "
        "Daten.\n\n"
        "Nicht mehr erforderliche personenbezogene Daten werden gelöscht oder, soweit "
        "eine Löschung aufgrund gesetzlicher Aufbewahrungspflichten noch nicht zulässig "
        "ist, für andere Verarbeitungszwecke gesperrt."
    )

    # 22. Kündigung und Löschung
    st.markdown("### 22. Kündigung und Löschung")
    st.markdown(
        "Die Kündigung eines Athletic-Performance-Hub-Vertrags und die "
        "datenschutzrechtliche Löschung personenbezogener Daten sind voneinander zu "
        "unterscheiden.\n\n"
        "Durch eine Kündigung kann der Zugang zum Dienst entsprechend dem "
        "Vertragsverhältnis beendet oder eingeschränkt werden.\n\n"
        "Löschanfragen werden unter Berücksichtigung gesetzlicher "
        "Aufbewahrungspflichten und bestehender Rechte und Pflichten bearbeitet."
    )

    # 23. Empfänger
    st.markdown("### 23. Empfänger personenbezogener Daten")
    st.markdown(
        "Personenbezogene Daten werden nur weitergegeben, wenn hierfür eine gesetzliche "
        "Grundlage besteht, dies zur Vertragserfüllung erforderlich ist oder ein "
        "Dienstleister im Rahmen einer zulässigen Auftragsverarbeitung eingesetzt wird.\n\n"
        "Zu den derzeit für den Produktivbetrieb relevanten technischen Dienstleistern "
        "gehört insbesondere:"
    )
    st.markdown(
        '<div translate="no" style="background:#161b22;border:1px solid #30363d;'
        'border-radius:8px;padding:14px 16px;margin:8px 0;font-size:14px;'
        'line-height:1.7;color:#c9d1d9">'
        '<strong>IONOS SE</strong><br>'
        'Elgendorfer Straße 57<br>'
        '56410 Montabaur<br>'
        'Deutschland<br>'
        '<em style="color:#8b949e;font-size:12px">Server-/Hosting-Infrastruktur und E-Mail-Dienste</em>'
        '</div>',
        unsafe_allow_html=True,
    )

    # 24. Drittlandübermittlung
    st.markdown("### 24. Drittlandübermittlung")
    st.markdown(
        "Produktive Spieler- und Kundendaten sollen nach der derzeitigen Architektur "
        "auf der hierfür vorgesehenen IONOS-Infrastruktur verarbeitet werden.\n\n"
        "Werden zukünftig Dienste eingesetzt, bei denen personenbezogene Daten "
        "außerhalb des Europäischen Wirtschaftsraums verarbeitet werden, werden die "
        "gesetzlichen Anforderungen an internationale Datenübermittlungen berücksichtigt "
        "und diese Datenschutzerklärung entsprechend angepasst."
    )

    # 25. Automatisierte Auswertungen
    st.markdown("### 25. Automatisierte Auswertungen")
    st.markdown(
        "Athletic Performance Hub kann auf Grundlage eingegebener Test- und "
        "Trainingsdaten automatisiert Scores, Auffälligkeiten, Trainingsschwerpunkte "
        "und Trainingsvorschläge erzeugen.\n\n"
        "Diese Funktionen dienen als Unterstützung für Trainer und Vereine.\n\n"
        "Die endgültige fachliche Trainingsentscheidung verbleibt beim verantwortlichen "
        "Nutzer. Die Auswertungen stellen keine medizinische Diagnose dar."
    )

    # 26. Rechte betroffener Personen
    st.markdown("### 26. Rechte betroffener Personen")
    st.markdown(
        "Betroffene Personen haben bei Vorliegen der gesetzlichen Voraussetzungen "
        "insbesondere das Recht auf:"
    )
    st.markdown(
        "- Auskunft gemäß Art. 15 DSGVO\n"
        "- Berichtigung gemäß Art. 16 DSGVO\n"
        "- Löschung gemäß Art. 17 DSGVO\n"
        "- Einschränkung der Verarbeitung gemäß Art. 18 DSGVO\n"
        "- Datenübertragbarkeit gemäß Art. 20 DSGVO\n"
        "- Widerspruch gemäß Art. 21 DSGVO\n"
        "- Widerruf einer Einwilligung mit Wirkung für die Zukunft"
    )
    st.markdown(
        "Zur Ausübung dieser Rechte kann eine Anfrage gerichtet werden an: "
        "[support@aphsystem.de](mailto:support@aphsystem.de)"
    )

    # 27. Beschwerderecht
    st.markdown("### 27. Beschwerderecht")
    st.markdown(
        "Betroffene Personen haben außerdem das Recht, sich bei einer "
        "Datenschutzaufsichtsbehörde über die Verarbeitung ihrer personenbezogenen "
        "Daten zu beschweren."
    )

    # 28. Änderung der Datenschutzerklärung
    st.markdown("### 28. Änderung der Datenschutzerklärung")
    st.markdown(
        "Athletic Performance Hub wird weiterentwickelt.\n\n"
        "Diese Datenschutzerklärung kann deshalb angepasst werden, wenn sich "
        "Funktionen, technische Dienstleister, Verarbeitungen oder gesetzliche "
        "Anforderungen ändern.\n\n"
        "Es gilt die jeweils aktuelle innerhalb von Athletic Performance Hub bzw. "
        "auf der Website veröffentlichte Fassung."
    )
    st.markdown(
        '<div style="font-size:12px;color:#8b949e;margin-top:16px">'
        'Stand: 12. August 2026'
        '</div>',
        unsafe_allow_html=True,
    )


def page_agb() -> None:
    """Allgemeine Geschäfts- und Nutzungsbedingungen."""
    _page_header("📄", "Allgemeine Geschäfts- und Nutzungsbedingungen")
    st.markdown(
        '<div translate="no" style="font-size:14px;color:#8b949e;margin-bottom:16px">'
        'Athletic Performance Hub — Broska Daroish<br>'
        'Am Remswasen 57, 73527 Schwäbisch Gmünd, Deutschland<br>'
        'E-Mail: <a href="mailto:support@aphsystem.de" style="color:#58a6ff">'
        'support@aphsystem.de</a>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### 1. Geltungsbereich")
    st.markdown(
        "Diese Allgemeinen Geschäfts- und Nutzungsbedingungen gelten für Verträge über "
        "die Nutzung der Softwareplattform Athletic Performance Hub.\n\n"
        "Athletic Performance Hub richtet sich insbesondere an Trainer, Vereine und "
        "andere berechtigte Organisationen bzw. Personen aus dem Sportbereich."
    )

    st.markdown("### 2. Leistungsgegenstand")
    st.markdown(
        "Athletic Performance Hub ist eine digitale Plattform zur sportlichen "
        "Leistungsdiagnostik, Athletenverwaltung, Trainingsplanung, "
        "Trainingssteuerung und Dokumentation.\n\n"
        "Je nach gebuchtem Paket können insbesondere Funktionen zur "
        "Spielerverwaltung, FMS-, Y-Balance- und Sprintdiagnostik, Trainingsplanung, "
        "Entwicklungsdokumentation, Berichterstellung und weitere sportbezogene "
        "Funktionen bereitgestellt werden.\n\n"
        "Der konkrete Leistungsumfang richtet sich nach dem bei Vertragsschluss "
        "vereinbarten Paket."
    )

    st.markdown("### 3. Registrierung")
    st.markdown(
        "Für die Nutzung ist grundsätzlich ein Benutzerkonto erforderlich.\n\n"
        "Der Kunde ist verpflichtet, vollständige und zutreffende Angaben zu machen.\n\n"
        "Die angegebene E-Mail-Adresse kann vor Freischaltung verifiziert werden."
    )

    st.markdown("### 4. Zugangsdaten")
    st.markdown(
        "Benutzer sind verpflichtet, ihre Zugangsdaten vertraulich zu behandeln und "
        "gegen unberechtigten Zugriff zu schützen.\n\n"
        "Eine unberechtigte Weitergabe von Zugangsdaten ist nicht zulässig.\n\n"
        "Bei Verdacht auf Missbrauch ist der Support unverzüglich unter "
        "[support@aphsystem.de](mailto:support@aphsystem.de) zu informieren."
    )

    st.markdown("### 5. Trainer- und Vereinskonten")
    st.markdown(
        "Athletic Performance Hub kann unterschiedliche Kontotypen und "
        "Berechtigungsstufen bereitstellen.\n\n"
        "Hierzu gehören insbesondere Trainer- und Vereinskonten sowie innerhalb von "
        "Vereinskonten gegebenenfalls weitere berechtigte Benutzer."
    )

    st.markdown("### 6. Pakete und Lizenzen")
    st.markdown(
        "Umfang, Benutzeranzahl, Spieleranzahl und verfügbare Funktionen richten sich "
        "nach dem jeweils vereinbarten Paket bzw. der zugewiesenen Lizenz."
    )

    st.markdown("### 7. Preise und Zahlung")
    st.markdown(
        "Es gelten die zum Zeitpunkt des Vertragsschlusses vereinbarten Preise.\n\n"
        "Zahlungsweise, Abrechnungszeitraum und Fälligkeit richten sich nach dem "
        "jeweiligen Vertrag bzw. Paket."
    )

    st.markdown("### 8. Vertragslaufzeit")
    st.markdown(
        "Beginn, Mindestlaufzeit und gegebenenfalls Verlängerung des Vertrags richten "
        "sich nach dem bei Vertragsschluss ausgewählten bzw. vereinbarten Tarif."
    )

    st.markdown("### 9. Kündigung")
    st.markdown(
        "Verträge können unter Einhaltung der jeweils vereinbarten "
        "Kündigungsbedingungen gekündigt werden.\n\n"
        "Soweit Athletic Performance Hub eine Online-Kündigungsfunktion bereitstellt, "
        "kann die Kündigung darüber erklärt werden.\n\n"
        "Der Eingang einer elektronischen Kündigung wird entsprechend bestätigt."
    )

    st.markdown("### 10. Auswirkungen einer Kündigung")
    st.markdown(
        "Eine Kündigung führt nicht automatisch zur sofortigen technischen Löschung "
        "sämtlicher gespeicherter Daten.\n\n"
        "Nach Vertragsende kann der Zugang zu Athletic Performance Hub eingeschränkt "
        "oder deaktiviert werden.\n\n"
        "Die weitere Speicherung bzw. Löschung personenbezogener Daten richtet sich "
        "nach gesetzlichen Anforderungen und der Datenschutzerklärung."
    )

    st.markdown("### 11. Nutzung der Plattform")
    st.markdown(
        "Athletic Performance Hub darf ausschließlich im Rahmen der vertraglich "
        "eingeräumten Nutzungsrechte verwendet werden. Insbesondere untersagt sind:"
    )
    st.markdown(
        "- unberechtigte Zugriffe auf fremde Konten oder Daten\n"
        "- Umgehung technischer Beschränkungen\n"
        "- Weitergabe von Zugängen an unberechtigte Personen\n"
        "- vorsätzliche Beeinträchtigung des Systems\n"
        "- Einbringen von Schadsoftware\n"
        "- rechtswidrige Nutzung der Plattform"
    )

    st.markdown("### 12. Verantwortung für Athletendaten")
    st.markdown(
        "Der Kunde ist dafür verantwortlich, dass personenbezogene Daten von Spielern, "
        "Athleten, Eltern oder anderen Personen rechtmäßig in Athletic Performance Hub "
        "eingegeben und verarbeitet werden dürfen.\n\n"
        "Dies gilt insbesondere für Daten Minderjähriger und gesundheitsbezogene "
        "Informationen."
    )

    st.markdown("### 13. Datenschutz und Auftragsverarbeitung")
    st.markdown(
        "Soweit Athletic Performance Hub personenbezogene Daten im Auftrag des Kunden "
        "verarbeitet und die gesetzlichen Voraussetzungen einer Auftragsverarbeitung "
        "vorliegen, schließen die Parteien eine Vereinbarung zur Auftragsverarbeitung "
        "gemäß Art. 28 DSGVO."
    )

    st.markdown("### 14. Leistungsdiagnostik")
    st.markdown(
        "Athletic Performance Hub unterstützt Trainer bei der strukturierten "
        "Auswertung sportlicher Leistungsdaten.\n\n"
        "Testergebnisse und Scores müssen im sportlichen Gesamtkontext betrachtet "
        "werden.\n\n"
        "Die Plattform kann Trainingsschwerpunkte und Auffälligkeiten darstellen."
    )

    st.markdown("### 15. Keine medizinische Diagnose")
    st.markdown(
        "Athletic Performance Hub ist kein medizinisches Diagnose- oder "
        "Behandlungssystem.\n\n"
        "Scores, Auffälligkeiten, Risikohinweise und Trainingsempfehlungen stellen "
        "keine medizinische Diagnose dar.\n\n"
        "Bei Verletzungen, Schmerzen oder gesundheitlichen Beschwerden ist eine "
        "entsprechend qualifizierte medizinische Fachperson hinzuzuziehen."
    )

    st.markdown("### 16. Trainingsvorschläge")
    st.markdown(
        "Automatisch oder regelbasiert erzeugte Trainingsvorschläge dienen als "
        "Unterstützung.\n\n"
        "Der verantwortliche Trainer entscheidet, ob Übungen, Trainingsumfang und "
        "Belastung für den jeweiligen Athleten geeignet sind.\n\n"
        "Alter, Leistungsstand, Trainingszustand, Belastbarkeit, Beschwerden und "
        "sonstige relevante individuelle Faktoren sind dabei zu berücksichtigen."
    )

    st.markdown("### 17. Verfügbarkeit")
    st.markdown(
        "Der Anbieter bemüht sich um eine hohe Verfügbarkeit von Athletic Performance "
        "Hub.\n\n"
        "Eine jederzeit vollständig unterbrechungsfreie Verfügbarkeit kann technisch "
        "nicht garantiert werden.\n\n"
        "Vorübergehende Einschränkungen können insbesondere aufgrund von Wartung, "
        "Updates, Sicherheitsmaßnahmen, technischen Störungen oder Ausfällen externer "
        "Infrastruktur auftreten."
    )

    st.markdown("### 18. Updates")
    st.markdown(
        "Athletic Performance Hub wird fortlaufend weiterentwickelt.\n\n"
        "Der Anbieter darf Fehlerbehebungen, Sicherheitsupdates und technische "
        "Verbesserungen durchführen.\n\n"
        "Wesentliche vertraglich geschuldete Leistungen werden nicht ohne rechtlichen "
        "bzw. vertraglichen Grund entzogen."
    )

    st.markdown("### 19. Datensicherheit und Datensicherung")
    st.markdown(
        "Der Anbieter trifft angemessene technische und organisatorische Maßnahmen "
        "zum Schutz der gespeicherten Daten.\n\n"
        "Hierzu können insbesondere Zugriffskontrollen, Mandantentrennung und "
        "Datensicherungen gehören.\n\n"
        "Eine absolute Sicherheit gegen sämtliche technisch möglichen Risiken kann "
        "nicht gewährleistet werden."
    )

    st.markdown("### 20. Mandantentrennung")
    st.markdown(
        "Daten verschiedener Kunden werden logisch voneinander getrennt.\n\n"
        "Ein Trainer oder Verein darf grundsätzlich nur auf die seinem Kundenbereich "
        "zugeordneten Daten zugreifen."
    )

    st.markdown("### 21. Haftung")
    st.markdown(
        "Die Haftung des Anbieters richtet sich nach den gesetzlichen Vorschriften.\n\n"
        "Gesetzlich zwingende Haftungsansprüche, insbesondere wegen Vorsatz, grober "
        "Fahrlässigkeit sowie bei Verletzung von Leben, Körper oder Gesundheit, "
        "bleiben unberührt."
    )

    st.markdown("### 22. Verantwortung für Trainingsentscheidungen")
    st.markdown(
        "Athletic Performance Hub ist ein unterstützendes Softwarewerkzeug.\n\n"
        "Die fachliche Verantwortung für die konkrete Trainingsgestaltung, "
        "Belastungssteuerung und Beurteilung der Einsatzfähigkeit eines Athleten "
        "verbleibt beim verantwortlichen Trainer bzw. der zuständigen Fachperson."
    )

    st.markdown("### 23. Rechte an der Software")
    st.markdown(
        "Software, Design, Struktur, Texte, Grafiken, Auswertungslogiken und sonstige "
        "vom Anbieter entwickelte Bestandteile von Athletic Performance Hub dürfen nur "
        "im Rahmen der eingeräumten Nutzungsrechte verwendet werden.\n\n"
        "Eine nicht gestattete Vervielfältigung, Weitergabe, Veröffentlichung oder "
        "kommerzielle Verwertung ist nicht zulässig."
    )

    st.markdown("### 24. Sperrung")
    st.markdown(
        "Bei konkretem Verdacht auf Missbrauch, erhebliche Sicherheitsgefährdungen "
        "oder schwerwiegende Vertragsverstöße kann der Zugang im erforderlichen Umfang "
        "vorübergehend gesperrt werden."
    )

    st.markdown("### 25. Support")
    st.markdown(
        "Supportanfragen können gerichtet werden an: "
        "[support@aphsystem.de](mailto:support@aphsystem.de)\n\n"
        "Die Adresse [noreply@aphsystem.de](mailto:noreply@aphsystem.de) dient "
        "ausschließlich dem automatisierten Systemversand und ist nicht als "
        "Supportadresse vorgesehen."
    )

    st.markdown("### 26. Änderungen dieser Bedingungen")
    st.markdown(
        "Änderungen dieser Bedingungen erfolgen unter Beachtung der gesetzlichen "
        "Voraussetzungen.\n\n"
        "Soweit für eine Änderung die Zustimmung des Kunden erforderlich ist, wird "
        "diese entsprechend eingeholt."
    )

    st.markdown("### 27. Anwendbares Recht")
    st.markdown(
        "Es gilt das Recht der Bundesrepublik Deutschland unter Beachtung zwingender "
        "gesetzlicher Vorschriften."
    )

    st.markdown("### 28. Schlussbestimmungen")
    st.markdown(
        "Sollten einzelne Bestimmungen unwirksam sein oder werden, richten sich die "
        "Rechtsfolgen nach den gesetzlichen Vorschriften."
    )
    st.markdown(
        '<div style="font-size:12px;color:#8b949e;margin-top:16px">'
        'Stand: 12. August 2026'
        '</div>',
        unsafe_allow_html=True,
    )
