# Manueller Reparaturablauf: technischer Einzeltrainer zu Verein

Dieser Ablauf ist absichtlich **kein** Migrationsskript und führt keine
Datenänderung selbstständig aus. Er darf erst nach Prüfung und einer
gesicherten Datenbanksicherung auf der produktiven Instanz ausgeführt werden.

## Voraussetzungen

1. Die Version mit dem serverseitigen Konvertierungsservice ist produktiv
   verfügbar.
2. Ein aktiver Superadmin führt den Vorgang aus.
3. Vor der Änderung existiert eine wiederherstellbare Datenbanksicherung.
4. Die Vorprüfung bestätigt für den Zielmandanten:
   - `ist_technischer_mandant = 1`,
    - genau ein **aktives** direkt über `benutzer.verein_id` zugeordnetes
      Benutzerkonto,
    - eine bestehende **aktive** `trainer_mandanten`-Zuordnung dieses
      Benutzerkontos zum Zielmandanten,
    - keine weitere aktive `trainer_mandanten`-Zuordnung dieses Benutzerkontos
      zu einem anderen Verein,
   - ein Vertrags-/Lizenzdatensatz auf dem technischen Mandanten.

Bei Abweichungen nicht fortfahren. Insbesondere mehrere direkt zugeordnete
Benutzerkonten erfordern zuerst eine fachliche Klärung; die Konvertierung
blockiert diesen Fall bewusst.

## Ausführung über die Superadmin-Oberfläche

1. In **Lizenzverwaltung** den technischen Einzeltrainer öffnen.
2. `VEREIN_BASIC` oder `VEREIN_PRO` auswählen.
3. Den Hinweis zur Mandanten-Konvertierung prüfen. Status-, Ablauf- und
   Testphasenfelder in diesem Dialog werden absichtlich nicht angewendet.
4. Einmal speichern, den Bestätigungshinweis lesen und ein zweites Mal
   speichern.
5. Die Erfolgsmeldung abwarten und die Ansicht neu laden.

Der Ablauf nutzt ausschließlich den zentralen, atomaren
Konvertierungsservice. Er legt keine neue Vereins-ID an und verändert weder
Spielerzuordnungen noch Kundennummer, Stripe-Customer-ID, Subscription-ID,
Lizenzstatus, Testphase oder Lizenzende.

Der Dialog **„+ Lizenz zuweisen“** ist für diesen Fall ausdrücklich nicht
geeignet: Er zeigt nur echte Standalone-Einzeltrainer ohne Mandant an.

## Nachprüfung

In allen drei Superadmin-Ansichten kontrollieren:

- **Kundenverwaltung:** genau ein Vertragspartner vom Typ „Verein“ mit der
  Kundennummer des bisherigen technischen Mandanten.
- **Lizenzverwaltung:** genau ein Vereinseintrag mit dem gewählten
  Vereinspaket; kein zusätzlicher Einzeltrainer-Vertragspartner.
- **Vereinsverwaltung:** derselbe Vereinsdatensatz ist sichtbar.

Zusätzlich kontrollieren:

- `vereine.ist_technischer_mandant = 0`,
- das zugehörige Benutzerkonto hat Rolle `Vereinsadmin`,
- die aktive `trainer_mandanten`-Zuordnung trägt ebenfalls
  `Vereinsadmin`,
- Spieler besitzen weiterhin dieselbe `verein_id`,
- der Audit-Log enthält `einzeltrainer_zu_verein_konvertiert`.

## Abbruch und Wiederherstellung

Ein Rückwechsel ist nicht automatisiert implementiert. Wenn die Vorprüfung
scheitert oder die Nachprüfung nicht stimmt, keine manuellen SQL-Updates
vornehmen. Den Vorgang beenden und bei einer bereits erfolgten Änderung die
vorher erstellte Datenbanksicherung nach dem Betriebsprozess wiederherstellen.