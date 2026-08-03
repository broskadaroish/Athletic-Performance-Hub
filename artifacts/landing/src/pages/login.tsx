import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Activity, ArrowRight } from "lucide-react";
import { Link } from "wouter";

const formSchema = z.object({
  email: z.string().email("Bitte eine gültige E-Mail-Adresse eingeben."),
  password: z.string().min(1, "Passwort ist erforderlich."),
});

export default function Login() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Redirects to Streamlit app which handles actual auth
    window.location.href = "/app";
  }

  return (
    <div className="min-h-[100dvh] flex flex-col relative overflow-hidden">
      {/* Background styling */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwYXRoIGQ9Ik0wIDEwaDQwTTEwIDB2NDAiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAyKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9zdmc+')] z-0 pointer-events-none" />
      
      <div className="flex-1 flex items-center justify-center py-12 px-4 z-10">
        <div className="max-w-md w-full">
          <div className="text-center mb-10">
            <Link href="/" className="inline-flex items-center justify-center w-16 h-16 bg-secondary/50 border border-white/10 rounded-2xl mb-6 text-primary hover:border-primary/50 transition-colors">
              <Activity className="w-8 h-8" />
            </Link>
            <h1 className="text-3xl font-bold mb-2">Willkommen zurück</h1>
            <p className="text-muted-foreground">Melden Sie sich an, um auf Ihre Diagnostik-Daten zuzugreifen.</p>
          </div>

          <div className="bg-secondary/30 border border-white/5 p-8 rounded-xl shadow-2xl backdrop-blur-sm">
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

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel>Passwort</FormLabel>
                        <Link href="/forgot-password" className="text-xs text-muted-foreground hover:text-primary transition-colors">
                          Passwort vergessen?
                        </Link>
                      </div>
                      <FormControl>
                        <Input placeholder="••••••••" type="password" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Button 
                  type="submit" 
                  className="w-full h-12 text-base"
                >
                  Anmelden <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </form>
            </Form>

            <div className="mt-8 pt-6 border-t border-white/5 text-center text-sm text-muted-foreground">
              Noch keinen Account?{" "}
              <Link href="/register" className="text-primary font-medium hover:underline">
                Demo anfragen
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
