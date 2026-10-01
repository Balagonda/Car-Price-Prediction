"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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

export default function LoginPageClient() {
  const router = useRouter();
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

  async function onSubmit(values: LoginFormValues) {
    try {
      await login({
        email: values.email,
        password: values.password,
        remember_me: values.remember_me,
      });
      toast.success("Welcome back!", { description: "Logged in successfully." });
      router.push("/");
    } catch (err: unknown) {
      toast.error("Login failed", { description: getAPIError(err).message });
    }
  }

  async function handleGoogleLoginSuccess(credential: string) {
    try {
      await googleLogin(credential);
      toast.success("Welcome back!", { description: "Logged in via Google successfully." });
      router.push("/");
    } catch (err: unknown) {
      toast.error("Google Login failed", { description: getAPIError(err).message });
    }
  }

  return (
    <div className="bg-white/10 backdrop-blur-xl p-8 rounded-2xl border border-white/20 shadow-2xl space-y-6">
      {/* Header */}
      <div className="text-center lg:text-left space-y-1">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Welcome back</h1>
        <p className="text-sm text-white/80">Please enter your details to sign in to CarWorth.</p>
      </div>

      {/* Social Logins */}
      <div className="space-y-3">
        <div className="flex justify-center w-full">
          <GoogleLogin
            onSuccess={(credentialResponse) => {
              if (credentialResponse.credential) {
                handleGoogleLoginSuccess(credentialResponse.credential);
              }
            }}
            onError={() => {
              toast.error("Google Login failed", { description: "Could not authenticate with Google." });
            }}
            theme="outline"
            shape="pill"
            text="continue_with"
            width="100%"
          />
        </div>
      </div>

      {/* Divider */}
      <div className="relative flex items-center py-2">
        <div className="flex-grow border-t border-white/20" />
        <span className="flex-shrink-0 mx-4 text-xs font-semibold uppercase text-white/60 tracking-wider">
          Or continue with email
        </span>
        <div className="flex-grow border-t border-white/20" />
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Email Input */}
        <div>
          <label htmlFor="email" className="block text-xs font-bold text-white mb-1">
            Email address
          </label>
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-white/60 text-lg">
              mail
            </span>
            <input
              id="email"
              type="email"
              placeholder="john@example.com"
              autoComplete="email"
              className={`w-full bg-white/5 text-white placeholder:text-white/40 pl-10 pr-4 py-3 text-sm rounded-xl outline-none border transition-all ${
                errors.email ? "border-red-500" : "border-white/10 focus:border-primary focus:bg-white/10"
              }`}
              {...register("email")}
            />
          </div>
          {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
        </div>

        {/* Password Input */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="password" className="block text-xs font-bold text-white">
              Password
            </label>
            <Link href="/forgot-password" className="text-xs font-semibold text-emerald-400 hover:underline">
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-white/60 text-lg">
              lock
            </span>
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              autoComplete="current-password"
              className={`w-full bg-white/5 text-white placeholder:text-white/40 pl-10 pr-10 py-3 text-sm rounded-xl outline-none border transition-all ${
                errors.password ? "border-red-500" : "border-white/10 focus:border-primary focus:bg-white/10"
              }`}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/60 hover:text-white transition-colors"
            >
              <span className="material-symbols-outlined text-lg">
                {showPassword ? "visibility_off" : "visibility"}
              </span>
            </button>
          </div>
          {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
        </div>

        {/* Remember me */}
        <div className="flex items-center gap-2 pt-1">
          <input
            id="remember_me"
            type="checkbox"
            className="w-4 h-4 accent-primary rounded cursor-pointer"
            {...register("remember_me")}
          />
          <label htmlFor="remember_me" className="text-xs text-white/80 font-medium cursor-pointer">
            Remember me for 7 days
          </label>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-primary text-white font-bold py-3.5 rounded-xl hover:bg-emerald-800 transition-colors shadow-md text-sm flex items-center justify-center gap-2 mt-2 disabled:opacity-60"
        >
          {isSubmitting ? (
            <span>Signing in...</span>
          ) : (
            <>
              Sign In
              <span className="material-symbols-outlined text-base">arrow_forward</span>
            </>
          )}
        </button>
      </form>

      {/* Register Footer Link */}
      <div className="text-center pt-4 border-t border-white/20 mt-4">
        <p className="text-xs text-white/80">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-bold text-emerald-400 hover:underline ml-1">
            Sign up free
          </Link>
        </p>
      </div>
    </div>
  );
}
