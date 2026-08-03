import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useSubmitContact } from "@workspace/api-client-react";
import { useState } from "react";
import { CheckCircle2, Loader2, Send, MapPin, Mail, Clock } from "lucide-react";
import { Link } from "wouter";

const formSchema = z.object({
  name: z.string().min(2, "Name muss mindestens 2 Zeichen lang sein."),
  email: z.string().email("Bitte eine gültige E-Mail-Adresse eingeben."),
  subject: z.string().optional(),
  message: z.string().min(10, "Die Nachricht muss mindestens 10 Zeichen lang sein."),
  datenschutz: z.boolean().refine((val) => val === true, {
    message: "Sie müssen der Datenschutzerklärung zustimmen.",
  }),
});

export default function Kontakt() {
  const [success, setSuccess] = useState(false);
  const submitContact = useSubmitContact();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      email: "",
      subject: "",
      message: "",
      datenschutz: false,
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    submitContact.mutate(
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
      <div className="flex-1 py-12 md:py-24">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="text-center mb-16 max-w-2xl mx-auto">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">Kontaktieren Sie uns</h1>
            <p className="text-xl text-muted-foreground">
              Sie haben Fragen zu unserer Plattform, benötigen technischen Support 
              oder möchten Partner werden? Wir sind für Sie da.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 lg:gap-8">
            {/* Contact Info */}
            <div className="lg:col-span-1 space-y-8">
              <div className="bg-secondary/20 border border-white/5 p-8 rounded-lg">
                <h3 className="text-xl font-bold mb-6 font-mono uppercase tracking-widest text-primary">Hauptsitz</h3>
                <div className="space-y-6">
                  <div className="flex items-start gap-4">
                    <MapPin className="w-6 h-6 text-muted-foreground shrink-0 mt-1" />
                    <div>
                      <p className="font-medium text-white mb-1">Bruce Football UG</p>
                      <p className="text-muted-foreground">Musterstraße 1<br/>10115 Berlin<br/>Deutschland</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <Mail className="w-6 h-6 text-muted-foreground shrink-0 mt-1" />
                    <div>
                      <p className="font-medium text-white mb-1">E-Mail</p>
                      <a href="mailto:info@brucefootball.de" className="text-muted-foreground hover:text-primary transition-colors">
                        info@brucefootball.de
                      </a>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <Clock className="w-6 h-6 text-muted-foreground shrink-0 mt-1" />
                    <div>
                      <p className="font-medium text-white mb-1">Geschäftszeiten</p>
                      <p className="text-muted-foreground">Mo-Fr: 09:00 - 17:00 Uhr</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-primary/5 border border-primary/20 p-8 rounded-lg text-center">
                <h3 className="text-lg font-bold mb-3">Produktdemo?</h3>
                <p className="text-sm text-muted-foreground mb-6">
                  Wenn Sie sich für unsere Software interessieren, nutzen Sie am besten unser spezielles Anfrageformular.
                </p>
                <Button asChild variant="outline" className="w-full bg-transparent">
                  <Link href="/register">Demo anfragen</Link>
                </Button>
              </div>
            </div>

            {/* Contact Form */}
            <div className="lg:col-span-2">
              {success ? (
                <div className="bg-secondary/30 border border-white/5 rounded-lg p-12 text-center h-full flex flex-col items-center justify-center animate-in fade-in zoom-in duration-500">
                  <div className="w-16 h-16 bg-primary/20 text-primary rounded-full flex items-center justify-center mb-6">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <h2 className="text-2xl font-bold mb-4">Nachricht gesendet!</h2>
                  <p className="text-muted-foreground mb-8 max-w-md">
                    Vielen Dank für Ihre Nachricht. Unser Team wird sich schnellstmöglich um Ihr Anliegen kümmern und sich bei Ihnen melden.
                  </p>
                  <Button onClick={() => setSuccess(false)} variant="outline">
                    Weitere Nachricht senden
                  </Button>
                </div>
              ) : (
                <div className="bg-secondary/30 border border-white/5 p-8 md:p-10 rounded-lg">
                  <h2 className="text-2xl font-bold mb-8">Schreiben Sie uns</h2>
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

                      <FormField
                        control={form.control}
                        name="subject"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Betreff (optional)</FormLabel>
                            <FormControl>
                              <Input placeholder="Worum geht es?" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="message"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Nachricht *</FormLabel>
                            <FormControl>
                              <Textarea 
                                placeholder="Ihre Nachricht an uns..." 
                                className="min-h-[150px] resize-y"
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
                          <FormItem className="flex flex-row items-start space-x-3 space-y-0 py-2">
                            <FormControl>
                              <Checkbox
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                            <div className="space-y-1 leading-none">
                              <FormLabel className="text-sm font-normal text-muted-foreground cursor-pointer">
                                Ich habe die <Link href="/datenschutz" className="text-primary hover:underline">Datenschutzerklärung</Link> zur Kenntnis genommen. Ich stimme zu, dass meine Angaben zur Kontaktaufnahme gespeichert werden. *
                              </FormLabel>
                              <FormMessage />
                            </div>
                          </FormItem>
                        )}
                      />

                      <Button 
                        type="submit" 
                        className="h-12 w-full md:w-auto px-8"
                        disabled={submitContact.isPending}
                      >
                        {submitContact.isPending ? (
                          <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Wird gesendet...</>
                        ) : (
                          <><Send className="mr-2 h-4 w-4" /> Nachricht absenden</>
                        )}
                      </Button>
                    </form>
                  </Form>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
