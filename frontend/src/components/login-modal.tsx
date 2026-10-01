"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useAuth } from "@/providers/auth-context";
import { getAPIError } from "@/lib/api-client";
import { GoogleLogin } from "@react-oauth/google";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z.string().min(1, "Password is required."),
  remember_me: z.boolean(),
});

type LoginFormValues = z.infer<typeof loginSchema>;

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const { login, googleLogin } = useAuth();
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", remember_me: false },
  });

  if (!isOpen) return null;

  async function onSubmit(values: LoginFormValues) {
    try {
      await login({
        email: values.email,
        password: values.password,
        remember_me: values.remember_me,
      });
      toast.success("Welcome back!", { description: "Logged in successfully to AutoGreen." });
      onClose();
    } catch (err: unknown) {
      toast.error("Login failed", { description: getAPIError(err).message });
    }
  }

  async function handleGoogleLoginSuccess(credential: string) {
    try {
      await googleLogin(credential);
      toast.success("Welcome back!", { description: "Logged in via Google successfully." });
      onClose();
    } catch (err: unknown) {
      toast.error("Google Login failed", { description: getAPIError(err).message });
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl p-6 md:p-8 max-w-md w-full border border-surface-variant mint-glow relative animate-in fade-in zoom-in">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-on-surface-variant hover:text-primary transition-colors p-1 rounded-full hover:bg-surface-container"
        >
          <span className="material-symbols-outlined text-xl">close</span>
        </button>

        {/* Brand Header */}
        <div className="text-center space-y-1 mb-6">
          <div className="w-10 h-10 rounded-xl bg-primary text-white flex items-center justify-center mx-auto mb-2 font-bold shadow-md">
            <span className="material-symbols-outlined text-xl">directions_car</span>
          </div>
          <h2 className="text-2xl font-extrabold text-on-surface tracking-tight">Sign In to AutoGreen</h2>
          <p className="text-xs text-on-surface-variant">Access your valuations, saved listings, and dealer quotes.</p>
        </div>

        {/* Google OAuth */}
        <div className="flex justify-center w-full mb-4">
          <GoogleLogin
            onSuccess={(credentialResponse) => {
              if (credentialResponse.credential) {
                handleGoogleLoginSuccess(credentialResponse.credential);
              }
            }}
            onError={() => {
              toast.error("Google Authentication failed");
            }}
            theme="outline"
            shape="pill"
            text="continue_with"
            width="100%"
          />
        </div>

        {/* Divider */}
        <div className="relative flex items-center py-2 mb-4">
          <div className="flex-grow border-t border-surface-variant" />
          <span className="flex-shrink-0 mx-3 text-[11px] font-bold text-on-surface-variant uppercase tracking-wider">
            Or with email
          </span>
          <div className="flex-grow border-t border-surface-variant" />
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="modal-email" className="block text-xs font-bold text-on-surface mb-1">
              Email address
            </label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-base">
                mail
              </span>
              <input
                id="modal-email"
                type="email"
                placeholder="john@example.com"
                autoComplete="email"
                className={`w-full bg-surface-container-low pl-10 pr-4 py-3 text-xs rounded-xl outline-none border transition-all ${
                  errors.email ? "border-red-500" : "border-transparent focus:border-primary"
                }`}
                {...register("email")}
              />
            </div>
            {errors.email && <p className="text-[11px] text-red-500 mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="modal-password" className="block text-xs font-bold text-on-surface">
                Password
              </label>
              <Link
                href="/forgot-password"
                onClick={onClose}
                className="text-[11px] font-semibold text-primary hover:underline"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-base">
                lock
              </span>
              <input
                id="modal-password"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                autoComplete="current-password"
                className={`w-full bg-surface-container-low pl-10 pr-10 py-3 text-xs rounded-xl outline-none border transition-all ${
                  errors.password ? "border-red-500" : "border-transparent focus:border-primary"
                }`}
                {...register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-primary"
              >
                <span className="material-symbols-outlined text-base">
                  {showPassword ? "visibility_off" : "visibility"}
                </span>
              </button>
            </div>
            {errors.password && <p className="text-[11px] text-red-500 mt-1">{errors.password.message}</p>}
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              id="modal-remember_me"
              type="checkbox"
              className="w-3.5 h-3.5 accent-primary rounded cursor-pointer"
              {...register("remember_me")}
            />
            <label htmlFor="modal-remember_me" className="text-[11px] text-on-surface-variant cursor-pointer">
              Remember me for 7 days
            </label>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-primary text-white font-bold py-3.5 rounded-xl hover:bg-emerald-800 transition-colors shadow-md text-xs flex items-center justify-center gap-2 mt-2 disabled:opacity-60"
          >
            {isSubmitting ? (
              <span>Signing in...</span>
            ) : (
              <>
                Sign In to Account
                <span className="material-symbols-outlined text-base">arrow_forward</span>
              </>
            )}
          </button>
        </form>

        <div className="text-center pt-4 mt-4 border-t border-surface-variant">
          <p className="text-xs text-on-surface-variant">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              onClick={onClose}
              className="font-bold text-primary hover:underline ml-1"
            >
              Sign up free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
