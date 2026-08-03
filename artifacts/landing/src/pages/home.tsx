import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import { Activity, ArrowRight, BarChart3, Users, FileText, CheckCircle2 } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col w-full">
      {/* Hero Section */}
      <section className="relative min-h-[90dvh] flex items-center pt-20 overflow-hidden">
        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwYXRoIGQ9Ik0wIDEwaDQwTTEwIDB2NDAiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAyKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9zdmc+')] z-0 pointer-events-none" />
        
        {/* Glow effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] pointer-events-none z-0" />

        <div className="container mx-auto px-4 z-10">
          <div className="max-w-4xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-mono mb-8 font-medium uppercase tracking-wider">
              <Activity className="w-3 h-3" />
              <span>Die wissenschaftliche Performance-Plattform</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-[1.1]">
              Diagnostik ohne <br className="hidden md:block" />
              <span className="text-muted-foreground">Kompromisse.</span>
            </h1>
            
            <p className="text-xl text-muted-foreground mb-10 max-w-2xl leading-relaxed">
              Professionelle Trainer und Sportwissenschaftler in der Bundesliga nutzen Bruce, 
              um Leistungsdaten zu erfassen, Verletzungsrisiken zu minimieren und Athleten weiterzuentwickeln.
            </p>
            
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <Button asChild size="lg" className="w-full sm:w-auto">
                <Link href="/register">Demo anfragen <ArrowRight className="w-4 h-4 ml-2" /></Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="w-full sm:w-auto bg-background/50 backdrop-blur-sm">
                <a href="/app">Zur App</a>
              </Button>
            </div>
            
            <div className="mt-16 flex items-center gap-6 text-sm text-muted-foreground font-mono uppercase tracking-widest">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-primary" /> Medizinische Präzision
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-primary" /> DSGVO Konform
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Section: The Instrument */}
      <section className="py-24 bg-secondary/30 border-y border-white/5 relative">
        <div className="container mx-auto px-4">
          <div className="mb-16 md:mb-24 flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="max-w-2xl">
              <h2 className="text-3xl md:text-5xl font-bold mb-4">Ein professionelles Instrument. Kein Spielzeug.</h2>
              <p className="text-xl text-muted-foreground">
                Entwickelt mit Athletiktrainern aus dem Profisport. Reduziert auf das Wesentliche, 
                optimiert für den Alltag am Platz.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-background border border-white/5 p-8 rounded-lg relative overflow-hidden group hover:border-primary/30 transition-colors">
              <div className="w-12 h-12 bg-secondary rounded-lg flex items-center justify-center mb-6 text-primary">
                <BarChart3 className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Präzise Diagnostik</h3>
              <p className="text-muted-foreground leading-relaxed">
                Standardisierte Testprotokolle für FMS, Y-Balance, Sprint, Sprung und Ausdauer. 
                Erfassen Sie Daten schnell und fehlerfrei direkt am Tablet auf dem Platz.
              </p>
            </div>
            
            <div className="bg-background border border-white/5 p-8 rounded-lg relative overflow-hidden group hover:border-primary/30 transition-colors">
              <div className="w-12 h-12 bg-secondary rounded-lg flex items-center justify-center mb-6 text-primary">
                <Users className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Asymmetrie-Tracking</h3>
              <p className="text-muted-foreground leading-relaxed">
                Automatische Erkennung von Seitendifferenzen und potenziellen Verletzungsrisiken. 
                Verfolgen Sie die Entwicklung über Zeit und greifen Sie proaktiv ein.
              </p>
            </div>

            <div className="bg-background border border-white/5 p-8 rounded-lg relative overflow-hidden group hover:border-primary/30 transition-colors">
              <div className="w-12 h-12 bg-secondary rounded-lg flex items-center justify-center mb-6 text-primary">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Medizinische Reports</h3>
              <p className="text-muted-foreground leading-relaxed">
                Generieren Sie mit einem Klick druckfertige PDF-Reports mit Ihrem Vereinslogo 
                für Trainer, medizinischen Stab oder Elterngespräche.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-24" id="preise">
        <div className="container mx-auto px-4">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4">Investition in Performance</h2>
            <p className="text-xl text-muted-foreground">
              Transparente Modelle für jede Vereinsgröße. Von der einzelnen Mannschaft bis zum gesamten NLZ.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* Starter Plan */}
            <div className="bg-secondary/20 border border-white/5 p-8 rounded-lg flex flex-col">
              <div className="mb-6">
                <h3 className="text-xl font-bold font-mono uppercase tracking-widest text-muted-foreground mb-2">Starter</h3>
                <div className="text-4xl font-bold">1 Mannschaft</div>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">Alle Testprotokolle</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">Basis-Reports</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">Bis zu 35 Spieler</span>
                </li>
              </ul>
              <Button asChild variant="outline" className="w-full">
                <Link href="/register">Interesse wecken</Link>
              </Button>
            </div>

            {/* Professional Plan (Highlighted) */}
            <div className="bg-secondary/40 border border-primary/50 p-8 rounded-lg flex flex-col relative transform md:-translate-y-4 shadow-2xl">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-primary text-primary-foreground px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest">
                Am beliebtesten
              </div>
              <div className="mb-6 mt-2">
                <h3 className="text-xl font-bold font-mono uppercase tracking-widest text-primary mb-2">Professional</h3>
                <div className="text-4xl font-bold">Bis 5 Teams</div>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-white">Alles aus Starter</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-white">Vergleichs-Dashboard</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-white">Vereinslogo in PDFs</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-white">Asymmetrie-Warnungen</span>
                </li>
              </ul>
              <Button asChild className="w-full">
                <Link href="/register">Demo vereinbaren</Link>
              </Button>
            </div>

            {/* Enterprise Plan */}
            <div className="bg-secondary/20 border border-white/5 p-8 rounded-lg flex flex-col">
              <div className="mb-6">
                <h3 className="text-xl font-bold font-mono uppercase tracking-widest text-muted-foreground mb-2">Enterprise</h3>
                <div className="text-4xl font-bold">Ganzer Verein</div>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">Unbegrenzte Teams</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">Unbegrenzte Accounts</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                  <span className="text-muted-foreground">Persönlicher Onboarding-Manager</span>
                </li>
              </ul>
              <Button asChild variant="outline" className="w-full">
                <Link href="/register">Kontakt aufnehmen</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 border-t border-white/5 bg-background relative overflow-hidden">
        <div className="absolute inset-0 bg-primary/5 pointer-events-none" />
        <div className="container mx-auto px-4 relative z-10 text-center max-w-3xl">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">Bereit für den nächsten Schritt?</h2>
          <p className="text-xl text-muted-foreground mb-10">
            Erleben Sie Bruce Football Diagnostics live. Buchen Sie eine unverbindliche Demo 
            und wir zeigen Ihnen, wie die Plattform Ihren Verein voranbringt.
          </p>
          <Button asChild size="lg" className="h-14 px-10 text-base">
            <Link href="/register">Jetzt Demo anfragen <ArrowRight className="w-5 h-5 ml-2" /></Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
