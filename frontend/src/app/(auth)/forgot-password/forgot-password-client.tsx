"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { ArrowLeft, Loader2, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { apiClient, getAPIError } from "@/lib/api-client";

const schema = z.object({
  email: z.string().email("Please enter a valid email address."),
});

type FormValues = z.infer<typeof schema>;

export default function ForgotPasswordClient() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  });

  async function onSubmit(data: FormValues) {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await apiClient.post("/auth/forgot-password", data);
      setSuccess(response.data.data || { reset_token: null });
    } catch (err) {
      setError(getAPIError(err).message || "An error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background text-foreground">
      {/* Left side */}
      <div className="flex-1 flex flex-col justify-center px-6 sm:px-12 md:px-20 lg:px-32 py-12">
        <Link href="/login" className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground mb-12 w-max transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to login
        </Link>
        
        <div className="max-w-md w-full mx-auto md:mx-0">
          <h1 className="text-3xl font-bold mb-2">Forgot Password</h1>
          <p className="text-muted-foreground mb-8">
            Enter your email address and we&apos;ll send you a link to reset your password.
          </p>
          
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm font-medium">
              {error}
            </div>
          )}

          {success ? (
            <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center space-y-4">
              <Mail className="w-10 h-10 text-emerald-500 mx-auto" />
              <h3 className="text-lg font-semibold text-emerald-500">Check your email</h3>
              <p className="text-muted-foreground text-sm">
                If an account exists for {form.getValues().email}, you will receive a password reset link shortly.
              </p>
              {success.reset_token && (
                <div className="mt-4 p-4 bg-background border border-border rounded-lg text-left">
                  <p className="text-xs font-semibold text-muted-foreground mb-2">DEVELOPMENT MODE ONLY:</p>
                  <Link 
                    href={`/reset-password?token=${success.reset_token}`}
                    className="text-violet-500 hover:underline break-all text-sm block"
                  >
                    Click here to reset your password
                  </Link>
                </div>
              )}
              <Button variant="outline" className="mt-4" onClick={() => setSuccess(null)}>
                Try another email
              </Button>
            </div>
          ) : (
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email address</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="name@example.com"
                          className="h-12 bg-background border-input"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button 
                  type="submit" 
                  className="w-full h-12 text-base font-semibold bg-violet-600 hover:bg-violet-700 text-white transition-all" 
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Sending link...</>
                  ) : (
                    "Send Reset Link"
                  )}
                </Button>
              </form>
            </Form>
          )}
        </div>
      </div>

      {/* Right side background */}
      <div 
        className="hidden md:flex flex-1 relative bg-muted"
        style={{
          background: "radial-gradient(circle at center, rgba(99,102,241,0.2) 0%, transparent 70%) #0a0a0f"
        }}
      >
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-20" />
      </div>
    </div>
  );
}
