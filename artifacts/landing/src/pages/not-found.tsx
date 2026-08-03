import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { Activity, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[100dvh] flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="text-[120px] font-bold font-mono text-primary leading-none mb-4 opacity-50 glow-text">
          404
        </div>
        <h1 className="text-2xl font-bold mb-4 uppercase tracking-widest">
          Seite nicht gefunden
        </h1>
        <p className="text-muted-foreground mb-8">
          Die angeforderte Seite existiert nicht oder wurde verschoben. 
          Vielleicht haben Sie sich vertippt?
        </p>
        <Button asChild>
          <Link href="/">
            <ArrowLeft className="w-4 h-4 mr-2" /> Zurück zur Startseite
          </Link>
        </Button>
      </div>
    </div>
  );
}
