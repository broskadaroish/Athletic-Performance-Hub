import { Link, useLocation } from "wouter";
import { Button } from "./ui/button";
import { Activity } from "lucide-react";

export function Navbar() {
  const [location] = useLocation();

  const navLinks = [
    { name: "Start", href: "/" },
    { name: "Kontakt", href: "/kontakt" },
    { name: "Support", href: "/support" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-20 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="h-10 w-10 bg-primary/10 text-primary flex items-center justify-center rounded group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
            <Activity className="h-6 w-6" />
          </div>
          <span className="font-bold text-xl tracking-tight">
            BRUCE <span className="font-mono font-normal text-muted-foreground text-sm uppercase tracking-widest ml-1">Diagnostics</span>
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`text-sm font-medium tracking-wide hover:text-primary transition-colors ${
                location === link.href ? "text-primary" : "text-muted-foreground"
              }`}
            >
              {link.name}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-4">
          <a href="/app" className="hidden md:block text-sm font-medium text-muted-foreground hover:text-white transition-colors">
            Anmelden
          </a>
          <Button asChild size="sm">
            <Link href="/register">Demo anfragen</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
