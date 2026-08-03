export default function Nutzungsbedingungen() {
  return (
    <div className="min-h-[100dvh] pt-20 pb-24">
      <div className="container mx-auto px-4 max-w-3xl">
        <h1 className="text-4xl font-bold mb-12">Nutzungsbedingungen</h1>
        
        <div className="prose prose-invert prose-p:text-muted-foreground prose-li:text-muted-foreground max-w-none">
          <p className="lead mb-8 text-xl">
            Allgemeine Geschäftsbedingungen für die Nutzung der Bruce Football Diagnostics SaaS-Plattform.
          </p>

          <h2 className="text-2xl font-bold mt-12 mb-4 font-mono uppercase tracking-widest text-primary">§ 1 Geltungsbereich, Vertragsgegenstand</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Diese Allgemeinen Geschäftsbedingungen (AGB) gelten für alle Verträge über die Nutzung der von der Bruce Football UG (haftungsbeschränkt), Musterstraße 1, 10115 Berlin (im Folgenden „Anbieter“) angebotenen webbasierten Softwarelösung „Bruce Football Diagnostics“ (im Folgenden „Software“) zwischen dem Anbieter und Kunden (im Folgenden „Kunde“).</li>
            <li>Die Software richtet sich ausschließlich an Unternehmer (§ 14 BGB), juristische Personen des öffentlichen Rechts oder öffentlich-rechtliche Sondervermögen. Verbraucher (§ 13 BGB) sind von der Nutzung ausgeschlossen.</li>
            <li>Vertragsgegenstand ist die Bereitstellung der Software zur Nutzung über das Internet als „Software as a Service“ (SaaS) sowie die Bereitstellung von Speicherplatz für die vom Kunden durch Nutzung der Software erzeugten Daten.</li>
          </ol>

          <h2 className="text-2xl font-bold mt-12 mb-4 font-mono uppercase tracking-widest text-primary">§ 2 Leistungsumfang und Nutzungsrecht</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Der Anbieter stellt dem Kunden die Software in ihrer jeweils aktuellen Version am Routerausgang des Rechenzentrums, in dem der Server mit der Software steht, zur Nutzung bereit.</li>
            <li>Die genaue Ausgestaltung des Leistungsumfangs (z.B. Anzahl der Mannschaften, Speicherplatz, Funktionsumfang) richtet sich nach dem vom Kunden gewählten Plan (Starter, Professional oder Enterprise).</li>
            <li>Der Anbieter räumt dem Kunden für die Dauer des Vertrages ein nicht ausschließliches, nicht übertragbares und nicht unterlizenzierbares Recht ein, die Software bestimmungsgemäß im vereinbarten Umfang zu nutzen.</li>
            <li>Der Kunde darf die Software nur für seine eigenen geschäftlichen bzw. sportlichen Zwecke nutzen. Eine Überlassung an Dritte ist untersagt.</li>
          </ol>

          <h2 className="text-2xl font-bold mt-12 mb-4 font-mono uppercase tracking-widest text-primary">§ 3 Pflichten des Kunden</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Der Kunde ist verpflichtet, die Zugangsdaten (Benutzernamen, Passwörter) geheim zu halten und vor dem unberechtigten Zugriff Dritter zu schützen.</li>
            <li>Der Kunde hat selbst dafür Sorge zu tragen, dass die von ihm eingesetzte Hardware und Software (z.B. Browser) den technischen Anforderungen für die Nutzung der Software entsprechen. Eine Internetverbindung ist zwingend erforderlich.</li>
            <li>Der Kunde ist für die Rechtmäßigkeit der von ihm in die Software eingestellten Daten (insbesondere Leistungs- und Gesundheitsdaten von Spielern) allein verantwortlich. Er hat sicherzustellen, dass die erforderlichen Einwilligungen der betroffenen Personen (Spieler/Erziehungsberechtigte) vorliegen (Art. 9 DSGVO).</li>
          </ol>

          <h2 className="text-2xl font-bold mt-12 mb-4 font-mono uppercase tracking-widest text-primary">§ 4 Vergütung und Zahlungsbedingungen</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Für die Nutzung der Software zahlt der Kunde die für den gewählten Plan vereinbarte Vergütung.</li>
            <li>Die Vergütung ist, sofern nicht anders vereinbart, monatlich oder jährlich im Voraus fällig.</li>
            <li>Alle Preise verstehen sich zuzüglich der jeweils geltenden gesetzlichen Umsatzsteuer.</li>
            <li>Kommt der Kunde mit der Zahlung in Verzug, ist der Anbieter berechtigt, den Zugang zur Software bis zur vollständigen Zahlung zu sperren.</li>
          </ol>

          <h2 className="text-2xl font-bold mt-12 mb-4 font-mono uppercase tracking-widest text-primary">§ 5 Haftungsbeschränkung</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Der Anbieter haftet unbeschränkt für Vorsatz und grobe Fahrlässigkeit sowie nach dem Produkthaftungsgesetz. Bei leichter Fahrlässigkeit haftet der Anbieter nur bei Verletzung einer wesentlichen Vertragspflicht (Kardinalpflicht), deren Erfüllung die ordnungsgemäße Durchführung des Vertrages überhaupt erst ermöglicht und auf deren Einhaltung der Kunde regelmäßig vertrauen darf.</li>
            <li>In Fällen leichter Fahrlässigkeit ist die Haftung auf den vertragstypischen, vorhersehbaren Schaden begrenzt.</li>
            <li>Der Anbieter übernimmt keine medizinische Verantwortung. Die aus der Software generierten Reports und Warnungen (z.B. Asymmetrie-Hinweise) ersetzen keine medizinische Diagnose durch einen Arzt.</li>
          </ol>

          <h2 className="text-2xl font-bold mt-12 mb-4 font-mono uppercase tracking-widest text-primary">§ 6 Laufzeit und Kündigung</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Der Vertrag wird auf unbestimmte Zeit geschlossen. Die Mindestlaufzeit beträgt je nach gewählten Plan einen Monat oder ein Jahr.</li>
            <li>Der Vertrag kann von beiden Seiten mit einer Frist von 14 Tagen zum Ende der jeweiligen Abrechnungsperiode (Monat oder Jahr) gekündigt werden.</li>
            <li>Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt unberührt.</li>
            <li>Mit Beendigung des Vertrages hat der Anbieter dem Kunden dessen Daten auf Verlangen in einem gängigen Format herauszugeben. Nach Ablauf von 30 Tagen nach Vertragsende werden die Daten des Kunden gelöscht, sofern keine gesetzlichen Aufbewahrungspflichten entgegenstehen.</li>
          </ol>

          <h2 className="text-2xl font-bold mt-12 mb-4 font-mono uppercase tracking-widest text-primary">§ 7 Schlussbestimmungen</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Es gilt ausschließlich das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts.</li>
            <li>Ausschließlicher Gerichtsstand für alle Streitigkeiten aus oder im Zusammenhang mit diesem Vertrag ist Berlin.</li>
            <li>Sollten einzelne Bestimmungen dieser AGB unwirksam sein oder werden, so wird hierdurch die Wirksamkeit der übrigen Bestimmungen nicht berührt.</li>
          </ol>

          <p className="mt-12 text-sm">Stand: Januar 2024</p>
        </div>
      </div>
    </div>
  );
}
