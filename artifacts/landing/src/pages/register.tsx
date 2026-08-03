import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useSubmitLead } from "@workspace/api-client-react";
import { useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CheckCircle2, Loader2, ArrowRight } from "lucide-react";
import { Link } from "wouter";

const formSchema = z.object({
  name: z.string().min(2, "Name muss mindestens 2 Zeichen lang sein."),
  email: z.string().email("Bitte eine gültige E-Mail-Adresse eingeben."),
  vereinsname: z.string().min(2, "Vereinsname muss mindestens 2 Zeichen lang sein."),
  telefon: z.string().optional(),
  spieleranzahl: z.string().optional(),
  plan: z.string().optional(),
  nachricht: z.string().optional(),
  datenschutz: z.boolean().refine((val) => val === true, {
    message: "Sie müssen der Datenschutzerklärung zustimmen.",
  }),
});

export default function Register() {
  const [success, setSuccess] = useState(false);
  const submitLead = useSubmitLead();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      email: "",
      vereinsname: "",
      telefon: "",
      spieleranzahl: "",
      plan: "",
      nachricht: "",
      datenschutz: false,
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    submitLead.mutate(
      { data: values },
      {
        onSuccess: () => {
          setSuccess(true);
        },
      }
    );
  }

  return (
    <div className="min-h-[100dvh] flex flex-col pt-20">
      <div className="flex-1 flex items-center justify-center py-12 px-4">
        <div className="max-w-xl w-full">
          <div className="mb-10 text-center">
            <h1 className="text-3xl md:text-4xl font-bold mb-4">Demo anfragen</h1>
            <p className="text-muted-foreground">
              Hinterlassen Sie uns Ihre Daten. Wir melden uns umgehend bei Ihnen, 
              um einen Termin für eine persönliche Präsentation zu vereinbaren.
            </p>
          </div>

          {success ? (
            <div className="bg-secondary/50 border border-white/5 rounded-lg p-12 text-center animate-in fade-in zoom-in duration-500">
              <div className="w-16 h-16 bg-primary/20 text-primary rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h2 className="text-2xl font-bold mb-4">Anfrage erfolgreich gesendet</h2>
              <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                Vielen Dank für Ihr Interesse an Bruce Diagnostics. Wir haben Ihre Anfrage erhalten 
                und werden uns in Kürze mit Ihnen in Verbindung setzen.
              </p>
              <Button asChild>
                <Link href="/">Zurück zur Startseite</Link>
              </Button>
            </div>
          ) : (
            <div className="bg-secondary/30 border border-white/5 p-8 rounded-lg">
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormField
                      control={form.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Name *</FormLabel>
                          <FormControl>
                            <Input placeholder="Max Mustermann" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>E-Mail *</FormLabel>
                          <FormControl>
                            <Input placeholder="max@verein.de" type="email" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormField
                      control={form.control}
                      name="vereinsname"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Vereinsname *</FormLabel>
                          <FormControl>
                            <Input placeholder="1. FC Musterstadt" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="telefon"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Telefon (optional)</FormLabel>
                          <FormControl>
                            <Input placeholder="+49 123 456789" type="tel" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FormField
                      control={form.control}
                      name="spieleranzahl"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Anzahl der Spieler</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Bitte wählen" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="< 20">Weniger als 20</SelectItem>
                              <SelectItem value="20-50">20 - 50</SelectItem>
                              <SelectItem value="50-100">50 - 100</SelectItem>
                              <SelectItem value="100+">Mehr als 100</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name="plan"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Plan-Interesse</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Bitte wählen" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="starter">Starter (1 Mannschaft)</SelectItem>
                              <SelectItem value="professional">Professional (bis 5)</SelectItem>
                              <SelectItem value="enterprise">Enterprise (unbegrenzt)</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="nachricht"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Nachricht (optional)</FormLabel>
                        <FormControl>
                          <Textarea 
                            placeholder="Gibt es bestimmte Themen, die wir in der Demo fokussieren sollen?" 
                            className="resize-none"
                            {...field} 
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="datenschutz"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start space-x-3 space-y-0 p-4 border border-white/5 rounded-md bg-background/50">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel className="text-sm font-normal text-muted-foreground">
                            Ich stimme zu, dass meine Angaben zur Kontaktaufnahme gespeichert werden. 
                            Weitere Informationen finden Sie in der <Link href="/datenschutz" className="text-primary hover:underline">Datenschutzerklärung</Link>. *
                          </FormLabel>
                          <FormMessage />
                        </div>
                      </FormItem>
                    )}
                  />

                  <Button 
                    type="submit" 
                    className="w-full h-14 text-base"
                    disabled={submitLead.isPending}
                  >
                    {submitLead.isPending ? (
                      <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Wird gesendet...</>
                    ) : (
                      <>Demo anfragen <ArrowRight className="ml-2 h-5 w-5" /></>
                    )}
                  </Button>
                </form>
              </Form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
