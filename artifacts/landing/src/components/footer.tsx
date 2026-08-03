import { Link } from "wouter";
import { Activity } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-white/5 bg-background py-16 md:py-24">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 md:gap-8">
          <div className="md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-6">
              <Activity className="h-6 w-6 text-primary" />
              <span className="font-bold text-xl tracking-tight">
                BRUCE
              </span>
            </Link>
            <p className="text-muted-foreground text-sm font-mono max-w-xs leading-relaxed">
              Die wissenschaftliche Performance-Plattform für professionelle Fußballvereine.
            </p>
          </div>
          
          <div>
            <h4 className="font-bold mb-6 text-sm uppercase tracking-widest text-white">Produkt</h4>
            <ul className="space-y-4 text-sm text-muted-foreground">
              <li><Link href="/" className="hover:text-primary transition-colors">Funktionen</Link></li>
              <li><Link href="/" className="hover:text-primary transition-colors">Preise</Link></li>
              <li><a href="/app" className="hover:text-primary transition-colors">Login</a></li>
              <li><Link href="/register" className="hover:text-primary transition-colors">Demo anfragen</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-6 text-sm uppercase tracking-widest text-white">Unternehmen</h4>
            <ul className="space-y-4 text-sm text-muted-foreground">
              <li><Link href="/kontakt" className="hover:text-primary transition-colors">Kontakt</Link></li>
              <li><Link href="/support" className="hover:text-primary transition-colors">Support & FAQ</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-6 text-sm uppercase tracking-widest text-white">Rechtliches</h4>
            <ul className="space-y-4 text-sm text-muted-foreground">
              <li><Link href="/impressum" className="hover:text-primary transition-colors">Impressum</Link></li>
              <li><Link href="/datenschutz" className="hover:text-primary transition-colors">Datenschutz</Link></li>
              <li><Link href="/nutzungsbedingungen" className="hover:text-primary transition-colors">Nutzungsbedingungen</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-muted-foreground font-mono">
          <p>© {new Date().getFullYear()} Bruce Football UG (haftungsbeschränkt). Alle Rechte vorbehalten.</p>
          <p>Made in Berlin.</p>
        </div>
      </div>
    </footer>
  );
}
