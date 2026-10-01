"use client";

/**
 * AutoWorth AI — Email Verification Page
 *
 * Reads ?token= from the URL, calls /auth/verify-email, shows result.
 */

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { verifyEmail } from "@/lib/auth";
import { getAPIError, apiClient } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error" | "resend_success">(() => token ? "loading" : "error");
  const [message, setMessage] = useState(() => token ? "" : "No verification token found in the URL.");
  const [email, setEmail] = useState("");
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }

    verifyEmail(token)
      .then(() => {
        setStatus("success");
        setMessage("Your email has been verified. You can now log in.");
      })
      .catch((err) => {
        setStatus("error");
        setMessage(getAPIError(err).message);
      });
  }, [token]);

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setResending(true);
    try {
      await apiClient.post("/auth/resend-verification", { email });
      setStatus("resend_success");
      setMessage("A new verification link has been sent to your email.");
    } catch (err) {
      setMessage(getAPIError(err).message);
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background text-foreground">
      <div className="w-full max-w-md rounded-2xl p-8 border text-center space-y-5 bg-card/50 border-border">
        {status === "loading" && (
          <>
            <Loader2 className="h-12 w-12 animate-spin text-violet-400 mx-auto" />
            <h2 className="text-xl font-semibold text-white">Verifying your email…</h2>
          </>
        )}

        {status === "success" && (
          <>
            <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto" />
            <h2 className="text-xl font-semibold text-white">Email verified!</h2>
            <p className="text-slate-400">{message}</p>
            <Link
              href="/login"
              className="inline-block px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 transition-all"
            >
              Sign in now
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <XCircle className="h-12 w-12 text-red-400 mx-auto" />
            <h2 className="text-xl font-semibold text-white">Verification failed</h2>
            <p className="text-slate-400">{message}</p>
            
            <form onSubmit={handleResend} className="pt-4 space-y-3">
              <p className="text-sm text-slate-300 font-medium">Need a new link?</p>
              <Input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Button type="submit" disabled={resending} className="w-full">
                {resending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Resend verification email
              </Button>
            </form>

            <div className="pt-2">
              <Link
                href="/login"
                className="text-violet-400 hover:text-violet-300 transition-colors text-sm"
              >
                Back to login
              </Link>
            </div>
          </>
        )}

        {status === "resend_success" && (
          <>
            <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto" />
            <h2 className="text-xl font-semibold text-white">Email Sent</h2>
            <p className="text-slate-400">{message}</p>
            <div className="pt-4">
              <Link
                href="/login"
                className="text-violet-400 hover:text-violet-300 transition-colors"
              >
                Back to login
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailClient() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center p-6 bg-background">
        <Loader2 className="h-12 w-12 animate-spin text-violet-400 mx-auto" />
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
