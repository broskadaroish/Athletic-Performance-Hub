import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { CheckCircle2, ArrowLeft } from "lucide-react";
import { Link } from "wouter";

const formSchema = z.object({
  email: z.string().email("Bitte eine gültige E-Mail-Adresse eingeben."),
});

export default function ForgotPassword() {
  const [success, setSuccess] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    // In a real app, this would call an API endpoint
    setTimeout(() => {
      setSuccess(true);
    }, 1000);
  }

  return (
    <div className="min-h-[100dvh] flex flex-col pt-20">
      <div className="flex-1 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full">
          <Link href="/login" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary transition-colors mb-8">
            <ArrowLeft className="w-4 h-4 mr-2" /> Zurück zum Login
          </Link>

          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-3">Passwort vergessen</h1>
            <p className="text-muted-foreground">
              Geben Sie Ihre E-Mail-Adresse ein. Wir senden Ihnen einen Link zum Zurücksetzen Ihres Passworts.
            </p>
          </div>

          {success ? (
            <div className="bg-secondary/30 border border-white/5 rounded-lg p-8 text-center animate-in fade-in zoom-in duration-300">
              <div className="w-12 h-12 bg-primary/20 text-primary rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold mb-2">E-Mail gesendet</h2>
              <p className="text-muted-foreground text-sm">
                Wir haben Ihnen eine E-Mail mit weiteren Anweisungen geschickt. 
                Bitte überprüfen Sie auch Ihren Spam-Ordner.
              </p>
            </div>
          ) : (
            <div className="bg-secondary/30 border border-white/5 p-8 rounded-lg">
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                  
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>E-Mail</FormLabel>
                        <FormControl>
                          <Input placeholder="max@verein.de" type="email" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button 
                    type="submit" 
                    className="w-full h-12"
                    disabled={form.formState.isSubmitting}
                  >
                    {form.formState.isSubmitting ? "Wird gesendet..." : "Passwort zurücksetzen"}
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
