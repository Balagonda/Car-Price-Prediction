"use client";

/**
 * AutoWorth AI — Email Verification Page
 *
 * Reads ?token= from the URL, calls /auth/verify-email, shows result.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { verifyEmail } from "@/lib/auth";
import { getAPIError } from "@/lib/api-client";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error">(() => token ? "loading" : "error");
  const [message, setMessage] = useState(() => token ? "" : "No verification token found in the URL.");

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

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{ background: "#0a0a0f" }}
    >
      <div
        className="w-full max-w-md rounded-2xl p-8 border text-center space-y-5"
        style={{
          background: "rgba(255,255,255,0.03)",
          borderColor: "rgba(255,255,255,0.07)",
        }}
      >
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
            <Link
              href="/login"
              className="text-violet-400 hover:text-violet-300 transition-colors"
            >
              Back to login
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
