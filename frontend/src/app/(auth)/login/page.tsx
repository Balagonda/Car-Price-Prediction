"use client";

/**
 * AutoWorth AI — Login Page
 *
 * Features:
 *  - React Hook Form + Zod validation
 *  - Email/password with "remember me"
 *  - Google OAuth button
 *  - Error display via toast
 *  - Redirect to dashboard on success
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2, Mail, Lock } from "lucide-react";
import { useAuth } from "@/providers/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getAPIError } from "@/lib/api-client";

// ── Validation Schema ────────────────────────
const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(1, "Password is required."),
  remember_me: z.boolean(),
});

type LoginFormValues = {
  email: string;
  password: string;
  remember_me: boolean;
};

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", remember_me: false },
  });

  // ── Submit Handler ───────────────────────────
  async function onSubmit(values: LoginFormValues) {
    try {
      await login({
        email: values.email,
        password: values.password,
        remember_me: values.remember_me,
      });
      toast.success("Welcome back!", { description: "Logged in successfully." });
      router.push("/dashboard");
    } catch (err: unknown) {
      toast.error("Login failed", { description: getAPIError(err).message });
    }
  }

  // ── Google OAuth Handler ─────────────────────
  async function handleGoogleLogin() {
    setIsGoogleLoading(true);
    try {
      const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
      if (!clientId) {
        toast.error("Google OAuth not configured", {
          description: "NEXT_PUBLIC_GOOGLE_CLIENT_ID is not set.",
        });
        return;
      }
      const params = new URLSearchParams({
        client_id: clientId,
        redirect_uri: `${window.location.origin}/auth/google/callback`,
        response_type: "id_token",
        scope: "openid email profile",
        nonce: Math.random().toString(36).slice(2),
      });
      window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
    } finally {
      setIsGoogleLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-3xl font-bold text-white tracking-tight">
          Welcome back
        </h1>
        <p className="text-slate-400">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
          >
            Sign up free
          </Link>
        </p>
      </div>

      {/* Google OAuth Button */}
      <button
        id="btn-google-login"
        type="button"
        onClick={handleGoogleLogin}
        disabled={isGoogleLoading || isSubmitting}
        className={cn(
          "w-full flex items-center justify-center gap-3 py-3 px-4 rounded-xl",
          "border border-white/10 bg-white/5 text-white font-medium",
          "hover:bg-white/10 hover:border-white/20 transition-all duration-200",
          "disabled:opacity-50 disabled:cursor-not-allowed"
        )}
      >
        {isGoogleLoading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
          </svg>
        )}
        Continue with Google
      </button>

      {/* Divider */}
      <div className="flex items-center gap-4">
        <div className="flex-1 h-px bg-white/10" />
        <span className="text-slate-500 text-sm">or sign in with email</span>
        <div className="flex-1 h-px bg-white/10" />
      </div>

      {/* Login Form */}
      <form id="form-login" onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Email */}
        <div className="space-y-2">
          <label htmlFor="input-email" className="block text-sm font-medium text-slate-300">
            Email address
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              id="input-email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              className={cn(
                "pl-10 bg-white/5 border-white/10 text-white placeholder:text-slate-600",
                "focus:border-violet-500/60 focus:ring-violet-500/20 transition-colors",
                errors.email && "border-red-500/60"
              )}
              {...register("email")}
            />
          </div>
          {errors.email && (
            <p className="text-sm text-red-400">{errors.email.message}</p>
          )}
        </div>

        {/* Password */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="input-password" className="block text-sm font-medium text-slate-300">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              id="input-password"
              type={showPassword ? "text" : "password"}
              placeholder="Your password"
              autoComplete="current-password"
              className={cn(
                "pl-10 pr-10 bg-white/5 border-white/10 text-white placeholder:text-slate-600",
                "focus:border-violet-500/60 focus:ring-violet-500/20 transition-colors",
                errors.password && "border-red-500/60"
              )}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="text-sm text-red-400">{errors.password.message}</p>
          )}
        </div>

        {/* Remember Me */}
        <div className="flex items-center gap-3">
          <input
            id="checkbox-remember-me"
            type="checkbox"
            className="h-4 w-4 rounded border-white/20 bg-white/5 text-violet-500 focus:ring-violet-500/30"
            {...register("remember_me")}
          />
          <label
            htmlFor="checkbox-remember-me"
            className="text-slate-400 text-sm font-normal cursor-pointer"
          >
            Remember me for 7 days
          </label>
        </div>

        {/* Submit */}
        <Button
          id="btn-login-submit"
          type="submit"
          disabled={isSubmitting}
          className={cn(
            "w-full py-3 rounded-xl font-semibold text-white transition-all duration-200",
            "bg-gradient-to-r from-violet-600 to-indigo-600",
            "hover:from-violet-500 hover:to-indigo-500 hover:shadow-lg hover:shadow-violet-500/25",
            "disabled:opacity-60 disabled:cursor-not-allowed"
          )}
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Signing in…
            </span>
          ) : (
            "Sign in"
          )}
        </Button>
      </form>
    </div>
  );
}
