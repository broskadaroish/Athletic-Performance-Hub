export default function Impressum() {
  return (
    <div className="min-h-[100dvh] pt-20 pb-24">
      <div className="container mx-auto px-4 max-w-3xl">
        <h1 className="text-4xl font-bold mb-12">Impressum</h1>
        
        <div className="prose prose-invert prose-p:text-muted-foreground max-w-none">
          <p className="lead mb-8 text-xl">
            Angaben gemäß § 5 TMG
          </p>

          <div className="bg-secondary/20 p-8 rounded-lg border border-white/5 mb-8">
            <h2 className="text-xl font-bold mb-4 font-mono uppercase tracking-widest text-white mt-0">Betreiber der Website</h2>
            <p>
              Bruce Football UG (haftungsbeschränkt)<br />
              Musterstraße 1<br />
              10115 Berlin<br />
              Deutschland
            </p>

            <h3 className="text-lg font-bold mt-6 mb-2">Vertreten durch:</h3>
            <p>Geschäftsführer: Max Mustermann</p>
          </div>

          <h2 className="text-2xl font-bold mt-12 mb-4">Kontakt</h2>
          <p>
            Telefon: +49 (0) 30 12345678<br />
            E-Mail: info@brucefootball.de
          </p>

          <h2 className="text-2xl font-bold mt-12 mb-4">Registereintrag</h2>
          <p>
            Eintragung im Handelsregister.<br />
            Registergericht: Amtsgericht Charlottenburg (Berlin)<br />
            Registernummer: HRB 123456 B
          </p>

          <h2 className="text-2xl font-bold mt-12 mb-4">Umsatzsteuer-ID</h2>
          <p>
            Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br />
            DE 123 456 789
          </p>

          <h2 className="text-2xl font-bold mt-12 mb-4">Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h2>
          <p>
            Max Mustermann<br />
            Musterstraße 1<br />
            10115 Berlin
          </p>

          {/* Haftungshinweis Software */}
          <div className="mt-12 bg-primary/5 border border-primary/20 rounded-xl p-8">
            <h2 className="text-xl font-bold mb-4 font-mono uppercase tracking-widest text-primary mt-0">Hinweis zur Software</h2>
            <p className="text-muted-foreground leading-relaxed mb-3">
              Diese Software dient ausschließlich der sportlichen Athletikanalyse, Leistungsentwicklung, Trainingsplanung und Trainingsdokumentation.
            </p>
            <p className="text-muted-foreground leading-relaxed mb-3">
              Sie ersetzt keine medizinische Untersuchung, Diagnose oder Behandlung durch Ärztinnen, Ärzte oder andere medizinische Fachpersonen.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              Alle Auswertungen dienen ausschließlich der Unterstützung von Trainerinnen und Trainern im sportlichen Kontext.
            </p>
          </div>

          <div className="mt-10 pt-8 border-t border-white/10 text-sm text-muted-foreground">
            <h3 className="text-base font-bold text-white mb-2">Haftung für Inhalte</h3>
            <p className="mb-4">
              Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.
            </p>
            <p className="mb-4">
              Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.
            </p>

            <h3 className="text-base font-bold text-white mb-2 mt-6">Urheberrecht</h3>
            <p>
              Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet. Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche gekennzeichnet.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
