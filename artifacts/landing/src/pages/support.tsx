import { Link } from "wouter";
import { Mail, FileText, ChevronRight } from "lucide-react";
import * as Accordion from "@radix-ui/react-accordion";
import { cn } from "@/lib/utils";
import React from "react";

const faqs = [
  {
    question: "Welche Diagnostik-Tests werden unterstützt?",
    answer: "Bruce Football Diagnostics unterstützt standardmäßig den FMS (Functional Movement Screen), Y-Balance Test, lineare Sprints (10m, 20m, 30m) mit Lichtschranken, verschiedene Sprungtests (CMJ, SJ) und Ausdauertests wie den Stufentest zur VO2max-Bestimmung."
  },
  {
    question: "Kann ich die Software offline nutzen?",
    answer: "Nein, die Plattform ist cloudbasiert, um Echtzeit-Vergleiche und automatische Backups zu gewährleisten. Für die Datenerfassung auf dem Platz wird eine Internetverbindung (Mobilfunk oder WLAN) benötigt."
  },
  {
    question: "Wie funktioniert die Generierung von Reports?",
    answer: "Reports werden als PDF generiert. Sobald die Testdaten eines Spielers oder einer Mannschaft erfasst sind, können Sie mit einem Klick einen detaillierten, medizinischen Bericht erstellen. Im Professional- und Enterprise-Plan wird dabei automatisch Ihr Vereinslogo eingebunden."
  },
  {
    question: "Sind die Daten sicher und DSGVO-konform?",
    answer: "Ja, der Schutz sensibler Gesundheits- und Leistungsdaten hat höchste Priorität. Unsere Server stehen in Deutschland. Die Plattform ist vollständig DSGVO-konform, wir nutzen keine Tracking-Tools und setzen nur technisch notwendige Session-Cookies ein."
  },
  {
    question: "Wie lange dauert das Onboarding?",
    answer: "Die Plattform ist extrem intuitiv. Für den Starter-Plan reicht meist ein kurzes Einrichtungscall (30 Min). Für größere Vereine (Professional/Enterprise) bieten wir dediziertes Onboarding an, bei dem wir gemeinsam Ihre Vereinsstruktur abbilden (meist in 1-2 Tagen abgeschlossen)."
  },
  {
    question: "Können wir unsere bestehenden Daten importieren?",
    answer: "Im Enterprise-Plan unterstützen wir den Import von historischen Daten über CSV-Vorlagen. Sprechen Sie uns darauf an, unser technisches Team hilft bei der Migration."
  },
  {
    question: "Wie wird die Asymmetrie gemessen und bewertet?",
    answer: "Beim Y-Balance Test und den FMS-Seitigkeitsübungen vergleicht das System automatisch die Werte der linken und rechten Körperhälfte. Wird ein kritischer Schwellenwert (z.B. >4cm Differenz beim Y-Balance) überschritten, warnt das System im Profil und auf dem Mannschafts-Dashboard."
  },
  {
    question: "Wie viele Accounts können wir anlegen?",
    answer: "Im Starter-Plan ist das System für einen Hauptnutzer (z.B. den leitenden Athletiktrainer) gedacht. Der Professional-Plan erlaubt bis zu 5 Trainer-Zugänge, der Enterprise-Plan unbegrenzte Accounts mit verschiedenen Rollen und Rechten."
  }
];

const AccordionItem = React.forwardRef<
  React.ElementRef<typeof Accordion.Item>,
  React.ComponentPropsWithoutRef<typeof Accordion.Item>
>(({ className, ...props }, ref) => (
  <Accordion.Item
    ref={ref}
    className={cn("border-b border-white/10", className)}
    {...props}
  />
));
AccordionItem.displayName = "AccordionItem";

const AccordionTrigger = React.forwardRef<
  React.ElementRef<typeof Accordion.Trigger>,
  React.ComponentPropsWithoutRef<typeof Accordion.Trigger>
>(({ className, children, ...props }, ref) => (
  <Accordion.Header className="flex">
    <Accordion.Trigger
      ref={ref}
      className={cn(
        "flex flex-1 items-center justify-between py-6 font-bold transition-all hover:text-primary [&[data-state=open]>svg]:rotate-90 text-left",
        className
      )}
      {...props}
    >
      {children}
      <ChevronRight className="h-5 w-5 shrink-0 transition-transform duration-200 text-muted-foreground" />
    </Accordion.Trigger>
  </Accordion.Header>
));
AccordionTrigger.displayName = Accordion.Trigger.displayName;

const AccordionContent = React.forwardRef<
  React.ElementRef<typeof Accordion.Content>,
  React.ComponentPropsWithoutRef<typeof Accordion.Content>
>(({ className, children, ...props }, ref) => (
  <Accordion.Content
    ref={ref}
    className="overflow-hidden text-sm data-[state=closed]:animate-out data-[state=open]:animate-in data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:slide-out-to-top-2 data-[state=open]:slide-in-from-top-2"
    {...props}
  >
    <div className={cn("pb-6 text-muted-foreground leading-relaxed", className)}>
      {children}
    </div>
  </Accordion.Content>
));
AccordionContent.displayName = Accordion.Content.displayName;

export default function Support() {
  return (
    <div className="min-h-[100dvh] flex flex-col pt-20">
      <div className="flex-1 py-12 md:py-24">
        <div className="container mx-auto px-4 max-w-4xl">
          
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">Support & FAQ</h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Alles was Sie über Bruce Football Diagnostics wissen müssen. 
              Finden Sie Antworten auf häufige Fragen oder kontaktieren Sie unseren Support.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
            <div className="bg-secondary/30 border border-white/5 p-6 rounded-lg flex items-start gap-4 hover:border-primary/30 transition-colors">
              <div className="w-12 h-12 bg-primary/10 text-primary rounded-lg flex items-center justify-center shrink-0">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold mb-2">Dokumentation</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Detaillierte Anleitungen zur Testdurchführung und Plattformnutzung.
                </p>
                <Link href="#" className="text-sm text-primary font-medium hover:underline inline-flex items-center">
                  Zur Anleitung <ChevronRight className="w-4 h-4 ml-1" />
                </Link>
              </div>
            </div>

            <div className="bg-secondary/30 border border-white/5 p-6 rounded-lg flex items-start gap-4 hover:border-primary/30 transition-colors">
              <div className="w-12 h-12 bg-primary/10 text-primary rounded-lg flex items-center justify-center shrink-0">
                <Mail className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold mb-2">Technischer Support</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Sie finden keine Antwort? Unser Team hilft Ihnen gerne weiter.
                </p>
                <Link href="/kontakt" className="text-sm text-primary font-medium hover:underline inline-flex items-center">
                  Nachricht schreiben <ChevronRight className="w-4 h-4 ml-1" />
                </Link>
              </div>
            </div>
          </div>

          <div className="bg-background border border-white/5 rounded-xl p-8 md:p-12">
            <h2 className="text-2xl font-bold mb-8 font-mono uppercase tracking-widest text-primary">Häufige Fragen</h2>
            <Accordion.Root type="single" collapsible className="w-full">
              {faqs.map((faq, index) => (
                <AccordionItem key={index} value={`item-${index}`}>
                  <AccordionTrigger className="text-lg">{faq.question}</AccordionTrigger>
                  <AccordionContent className="text-base">{faq.answer}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion.Root>
          </div>

        </div>
      </div>
    </div>
  );
}
