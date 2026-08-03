import { useGetMaintenanceStatus } from "@workspace/api-client-react";
import { Link, useLocation } from "wouter";
import { AlertTriangle, Home, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect } from "react";

export default function Wartung() {
  const [, setLocation] = useLocation();
  const { data, isLoading, isError } = useGetMaintenanceStatus({
    query: {
      retry: false, // Don't retry maintenance check if API is down
    }
  });

  // If maintenance is explicitly false, redirect home
  useEffect(() => {
    if (data?.maintenance === false) {
      setLocation("/");
    }
  }, [data, setLocation]);

  return (
    <div className="min-h-[100dvh] flex items-center justify-center p-4 bg-background relative overflow-hidden">
      {/* Hazard stripes background */}
      <div 
        className="absolute top-0 left-0 right-0 h-2 opacity-50 z-0" 
        style={{
          backgroundImage: "repeating-linear-gradient(45deg, hsl(var(--primary)), hsl(var(--primary)) 10px, transparent 10px, transparent 20px)"
        }}
      />
      
      <div className="max-w-md w-full text-center relative z-10">
        <div className="w-20 h-20 bg-secondary/50 border border-primary/20 rounded-full flex items-center justify-center mx-auto mb-8 relative">
          <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping opacity-20" />
          <AlertTriangle className="w-10 h-10 text-primary" />
        </div>
        
        <h1 className="text-3xl font-bold mb-4">Wartungsarbeiten</h1>
        
        <div className="bg-secondary/30 border border-white/5 p-6 rounded-lg mb-8">
          <p className="text-muted-foreground mb-4">
            Wir führen aktuell geplante Wartungsarbeiten durch, um die Performance 
            und Stabilität unserer Diagnostik-Plattform weiter zu verbessern.
          </p>
          
          {data?.message && (
            <div className="bg-background/50 border border-primary/20 p-4 rounded text-sm text-white font-mono">
              <span className="text-primary block text-xs uppercase tracking-widest mb-1">Status-Update:</span>
              {data.message}
            </div>
          )}

          {isError && (
            <div className="bg-background/50 border border-primary/20 p-4 rounded text-sm text-white font-mono">
              <span className="text-primary block text-xs uppercase tracking-widest mb-1">Status-Update:</span>
              System-Update läuft. Wir sind in Kürze wieder erreichbar.
            </div>
          )}
        </div>
        
        <p className="text-sm text-muted-foreground mb-8">
          Bitte versuchen Sie es in ein paar Minuten erneut. 
          Bestehende Diagnostik-Daten sind sicher und von der Wartung nicht betroffen.
        </p>

        <div className="flex items-center justify-center gap-4">
          <Button onClick={() => window.location.reload()} variant="default">
            Status prüfen
          </Button>
          <Button asChild variant="outline">
            <a href="mailto:support@brucefootball.de">Support kontaktieren</a>
          </Button>
        </div>
      </div>
    </div>
  );
}
