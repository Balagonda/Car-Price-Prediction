"use client";

/**
 * AutoWorth AI — Register Page
 *
 * Features:
 *  - React Hook Form + Zod validation
 *  - First name, last name, email, password, confirm password
 *  - Real-time password strength meter
 *  - Google OAuth option
 *  - Success state shows verification prompt
 */

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2, Mail, Lock, User, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/providers/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { getAPIError } from "@/lib/api-client";

// ── Validation Schema ────────────────────────
const registerSchema = z
  .object({
    first_name: z.string().min(1, "First name is required.").max(100),
    last_name: z.string().min(1, "Last name is required.").max(100),
    email: z.string().email("Please enter a valid email address."),
    password: z
      .string()
      .min(8, "At least 8 characters.")
      .regex(/[A-Z]/, "Must contain an uppercase letter.")
      .regex(/[0-9]/, "Must contain a number."),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match.",
    path: ["confirm_password"],
  });

type RegisterFormValues = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
};

// ── Password Strength ────────────────────────
function getPasswordStrength(password: string): {
  score: number;
  label: string;
  color: string;
} {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  if (score <= 1) return { score, label: "Weak", color: "#ef4444" };
  if (score <= 2) return { score, label: "Fair", color: "#f59e0b" };
  if (score <= 3) return { score, label: "Good", color: "#3b82f6" };
  return { score, label: "Strong", color: "#22c55e" };
}

export default function RegisterPage() {
  const { register: registerUser } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [registered, setRegistered] = useState(false);
  const [verificationToken, setVerificationToken] = useState<string | null>(null);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  const password = watch("password") ?? "";
  const strength = getPasswordStrength(password);

  // ── Submit ───────────────────────────────────
  async function onSubmit(values: RegisterFormValues) {
    try {
      const result = await registerUser({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        password: values.password,
      });
      setRegistered(true);
      if (result.verification_token) {
        setVerificationToken(result.verification_token);
      }
      toast.success("Account created!", {
        description: "Check your email to verify your account.",
      });
    } catch (err: unknown) {
      toast.error("Registration failed", { description: getAPIError(err).message });
    }
  }

  // ── Google OAuth ─────────────────────────────
  async function handleGoogleLogin() {
    setIsGoogleLoading(true);
    try {
      const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
      if (!clientId) {
        toast.error("Google OAuth not configured");
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

  // ── Success State ─────────────────────────────
  if (registered) {
    return (
      <div className="space-y-6 text-center">
        <div className="flex justify-center">
          <div
            className="w-20 h-20 rounded-full flex items-center justify-center"
            style={{ background: "rgba(99,102,241,0.15)" }}
          >
            <CheckCircle2 className="w-10 h-10 text-violet-400" />
          </div>
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white">Check your inbox</h2>
          <p className="text-slate-400 max-w-sm mx-auto">
            We&apos;ve sent a verification link to your email address. Click the
            link to activate your account.
          </p>
        </div>
        {verificationToken && (
          <div
            className="p-4 rounded-xl border border-violet-500/20 text-left"
            style={{ background: "rgba(99,102,241,0.08)" }}
          >
            <p className="text-xs text-slate-500 mb-1 font-mono uppercase tracking-wide">
              Dev mode — verification token
            </p>
            <p className="text-violet-300 text-sm font-mono break-all">
              {verificationToken}
            </p>
          </div>
        )}
        <Link
          href="/login"
          className="inline-block text-violet-400 hover:text-violet-300 transition-colors font-medium"
        >
          Back to sign in →
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-3xl font-bold text-white tracking-tight">
          Create account
        </h1>
        <p className="text-slate-400">
          Already registered?{" "}
          <Link
            href="/login"
            className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>

      {/* Google OAuth Button */}
      <button
        id="btn-google-register"
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
        <span className="text-slate-500 text-sm">or register with email</span>
        <div className="flex-1 h-px bg-white/10" />
      </div>

      {/* Register Form */}
      <form id="form-register" onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Name Row */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <label htmlFor="input-first-name" className="block text-sm font-medium text-slate-300">
              First name
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                id="input-first-name"
                placeholder="Ada"
                autoComplete="given-name"
                className={cn(
                  "pl-10 bg-white/5 border-white/10 text-white placeholder:text-slate-600",
                  "focus:border-violet-500/60 focus:ring-violet-500/20",
                  errors.first_name && "border-red-500/60"
                )}
                {...register("first_name")}
              />
            </div>
            {errors.first_name && (
              <p className="text-xs text-red-400">{errors.first_name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label htmlFor="input-last-name" className="block text-sm font-medium text-slate-300">
              Last name
            </label>
            <Input
              id="input-last-name"
              placeholder="Lovelace"
              autoComplete="family-name"
              className={cn(
                "bg-white/5 border-white/10 text-white placeholder:text-slate-600",
                "focus:border-violet-500/60 focus:ring-violet-500/20",
                errors.last_name && "border-red-500/60"
              )}
              {...register("last_name")}
            />
            {errors.last_name && (
              <p className="text-xs text-red-400">{errors.last_name.message}</p>
            )}
          </div>
        </div>

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
                "focus:border-violet-500/60 focus:ring-violet-500/20",
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
          <label htmlFor="input-password" className="block text-sm font-medium text-slate-300">
            Password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              id="input-password"
              type={showPassword ? "text" : "password"}
              placeholder="Min. 8 chars, 1 uppercase, 1 number"
              autoComplete="new-password"
              className={cn(
                "pl-10 pr-10 bg-white/5 border-white/10 text-white placeholder:text-slate-600",
                "focus:border-violet-500/60 focus:ring-violet-500/20",
                errors.password && "border-red-500/60"
              )}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          {/* Strength Meter */}
          {password.length > 0 && (
            <div className="space-y-1.5 mt-1">
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className="flex-1 h-1 rounded-full transition-all duration-300"
                    style={{
                      background:
                        i <= strength.score ? strength.color : "rgba(255,255,255,0.08)",
                    }}
                  />
                ))}
              </div>
              <p className="text-xs" style={{ color: strength.color }}>
                {strength.label} password
              </p>
            </div>
          )}
          {errors.password && (
            <p className="text-sm text-red-400">{errors.password.message}</p>
          )}
        </div>

        {/* Confirm Password */}
        <div className="space-y-2">
          <label htmlFor="input-confirm-password" className="block text-sm font-medium text-slate-300">
            Confirm password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              id="input-confirm-password"
              type={showConfirm ? "text" : "password"}
              placeholder="Repeat your password"
              autoComplete="new-password"
              className={cn(
                "pl-10 pr-10 bg-white/5 border-white/10 text-white placeholder:text-slate-600",
                "focus:border-violet-500/60 focus:ring-violet-500/20",
                errors.confirm_password && "border-red-500/60"
              )}
              {...register("confirm_password")}
            />
            <button
              type="button"
              onClick={() => setShowConfirm((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
            >
              {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirm_password && (
            <p className="text-sm text-red-400">{errors.confirm_password.message}</p>
          )}
        </div>

        {/* Terms */}
        <p className="text-xs text-slate-500">
          By creating an account you agree to our{" "}
          <Link href="/terms" className="text-violet-400 hover:text-violet-300">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link href="/privacy" className="text-violet-400 hover:text-violet-300">
            Privacy Policy
          </Link>
          .
        </p>

        {/* Submit */}
        <Button
          id="btn-register-submit"
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
              Creating account…
            </span>
          ) : (
            "Create account"
          )}
        </Button>
      </form>
    </div>
  );
}
