"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { apiClient, getAPIError } from "@/lib/api-client";
import Link from "next/link";

const schema = z.object({
  new_password: z.string().min(8, "Password must be at least 8 characters"),
  confirm_password: z.string(),
}).refine(data => data.new_password === data.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});

type FormValues = z.infer<typeof schema>;

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const router = useRouter();
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { new_password: "", confirm_password: "" },
  });

  if (!token) {
    return (
      <div className="max-w-md w-full mx-auto text-center space-y-4">
        <XCircle className="w-12 h-12 text-destructive mx-auto" />
        <h2 className="text-xl font-semibold text-foreground">Invalid Reset Link</h2>
        <p className="text-muted-foreground">The password reset link is invalid or missing.</p>
        <Button onClick={() => router.push("/forgot-password")}>Request a new link</Button>
      </div>
    );
  }

  async function onSubmit(data: FormValues) {
    setIsSubmitting(true);
    setError(null);
    try {
      await apiClient.post("/auth/reset-password", {
        token,
        new_password: data.new_password,
      });
      setSuccess(true);
    } catch (err) {
      setError(getAPIError(err).message || "Failed to reset password.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="max-w-md w-full mx-auto md:mx-0">
      <h1 className="text-3xl font-bold mb-2">Reset Password</h1>
      <p className="text-muted-foreground mb-8">
        Create a new strong password for your account.
      </p>
      
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm font-medium">
          {error}
        </div>
      )}

      {success ? (
        <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center space-y-4">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
          <h3 className="text-lg font-semibold text-emerald-500">Password Reset!</h3>
          <p className="text-muted-foreground text-sm">
            Your password has been changed successfully.
          </p>
          <Button className="mt-4 w-full bg-violet-600 hover:bg-violet-700" onClick={() => router.push("/login")}>
            Sign In Now
          </Button>
        </div>
      ) : (
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>New Password</FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      className="h-12 bg-background border-input"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm Password</FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder="••••••••"
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
                <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Resetting...</>
              ) : (
                "Reset Password"
              )}
            </Button>
          </form>
        </Form>
      )}
    </div>
  );
}

export default function ResetPasswordClient() {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background text-foreground">
      <div className="flex-1 flex flex-col justify-center px-6 sm:px-12 md:px-20 lg:px-32 py-12">
        <Suspense fallback={<Loader2 className="h-8 w-8 animate-spin text-violet-500 mx-auto" />}>
          <ResetPasswordContent />
        </Suspense>
      </div>
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
