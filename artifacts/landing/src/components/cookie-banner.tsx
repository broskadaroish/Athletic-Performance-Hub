import { useCookieConsent } from "@/hooks/use-cookie-consent";
import { Button } from "./ui/button";
import { Link } from "wouter";

export function CookieBanner() {
  const { consentGiven, acceptCookies } = useCookieConsent();

  if (consentGiven !== false) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6 animate-in slide-in-from-bottom-full duration-500">
      <div className="mx-auto max-w-4xl bg-secondary border border-white/10 rounded-lg p-6 shadow-2xl flex flex-col md:flex-row items-center gap-6 justify-between">
        <div className="text-sm text-muted-foreground">
          <p className="mb-2">
            <strong className="text-white">Wir nutzen nur notwendige Cookies.</strong>
          </p>
          <p>
            Um diese Website betreiben zu können, verwenden wir ausschließlich technisch notwendige Cookies. 
            Wir setzen keine Tracking- oder Analyse-Tools ein. Weitere Informationen finden Sie in unserer{" "}
            <Link href="/datenschutz" className="text-primary hover:underline">
              Datenschutzerklärung
            </Link>.
          </p>
        </div>
        <div className="flex-shrink-0 w-full md:w-auto">
          <Button onClick={acceptCookies} className="w-full md:w-auto">
            Verstanden
          </Button>
        </div>
      </div>
    </div>
  );
}
