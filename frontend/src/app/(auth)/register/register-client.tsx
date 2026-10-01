"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useAuth } from "@/providers/auth-context";
import { GoogleLogin } from "@react-oauth/google";
import { getAPIError } from "@/lib/api-client";

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
    terms: z.boolean().refine((val) => val === true, "You must agree to the Terms & Conditions."),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match.",
    path: ["confirm_password"],
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterClient() {
  const { register: registerUser, googleLogin } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [registered, setRegistered] = useState(false);
  const [verificationToken, setVerificationToken] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      first_name: "",
      last_name: "",
      email: "",
      password: "",
      confirm_password: "",
      terms: false,
    },
  });

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

  async function handleGoogleLoginSuccess(credential: string) {
    try {
      await googleLogin(credential);
      toast.success("Welcome to CarWorth!", { description: "Registered via Google successfully." });
    } catch (err: unknown) {
      toast.error("Google Authentication failed", { description: getAPIError(err).message });
    }
  }

  if (registered) {
    return (
      <div className="bg-white/10 backdrop-blur-xl p-8 rounded-2xl border border-white/20 shadow-2xl space-y-6 text-center">
        <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
          <span className="material-symbols-outlined text-3xl">mark_email_read</span>
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-white">Check your inbox</h2>
          <p className="text-xs text-white/80 max-w-sm mx-auto leading-relaxed">
            We&apos;ve sent a verification link to your email address. Click the link to activate your CarWorth account.
          </p>
        </div>

        {verificationToken && (
          <div className="p-4 rounded-xl bg-surface-container-low border border-surface-variant text-left">
            <p className="text-[10px] text-on-surface-variant font-mono uppercase">Dev mode token:</p>
            <p className="text-xs text-primary font-mono break-all">{verificationToken}</p>
          </div>
        )}

        <Link
          href="/login"
          className="inline-flex items-center gap-2 text-sm font-bold text-emerald-400 hover:underline"
        >
          Proceed to Sign In
          <span className="material-symbols-outlined text-base">arrow_forward</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white/10 backdrop-blur-xl p-8 rounded-2xl border border-white/20 shadow-2xl space-y-6">
      {/* Header */}
      <div className="text-center lg:text-left space-y-1">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Join CarWorth</h1>
        <p className="text-sm text-white/80">Create your account to start exploring premium vehicles.</p>
      </div>

      {/* Google OAuth Button */}
      <div className="flex justify-center w-full">
        <GoogleLogin
          onSuccess={(credentialResponse) => {
            if (credentialResponse.credential) {
              handleGoogleLoginSuccess(credentialResponse.credential);
            }
          }}
          onError={() => {
            toast.error("Google Authentication failed", { description: "Could not authenticate with Google." });
          }}
          theme="outline"
          shape="pill"
          text="signup_with"
          width="100%"
        />
      </div>

      {/* Divider */}
      <div className="relative flex items-center py-1">
        <div className="flex-grow border-t border-white/20" />
        <span className="flex-shrink-0 mx-4 text-xs font-semibold uppercase text-white/60 tracking-wider">
          Or register with email
        </span>
        <div className="flex-grow border-t border-white/20" />
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Name Row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="first_name" className="block text-xs font-bold text-white mb-1">
              First name
            </label>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-white/60 text-lg">
                person
              </span>
              <input
                id="first_name"
                placeholder="Ada"
                className={`w-full bg-white/5 text-white placeholder:text-white/40 pl-10 pr-3 py-3 text-sm rounded-xl outline-none border transition-all ${
                  errors.first_name ? "border-red-500" : "border-white/10 focus:border-primary focus:bg-white/10"
                }`}
                {...register("first_name")}
              />
            </div>
            {errors.first_name && <p className="text-xs text-red-500 mt-1">{errors.first_name.message}</p>}
          </div>

          <div>
            <label htmlFor="last_name" className="block text-xs font-bold text-white mb-1">
              Last name
            </label>
            <input
              id="last_name"
              placeholder="Lovelace"
              className={`w-full bg-white/5 text-white placeholder:text-white/40 px-4 py-3 text-sm rounded-xl outline-none border transition-all ${
                errors.last_name ? "border-red-500" : "border-white/10 focus:border-primary focus:bg-white/10"
              }`}
              {...register("last_name")}
            />
            {errors.last_name && <p className="text-xs text-red-500 mt-1">{errors.last_name.message}</p>}
          </div>
        </div>

        {/* Email */}
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
              className={`w-full bg-white/5 text-white placeholder:text-white/40 pl-10 pr-4 py-3 text-sm rounded-xl outline-none border transition-all ${
                errors.email ? "border-red-500" : "border-white/10 focus:border-primary focus:bg-white/10"
              }`}
              {...register("email")}
            />
          </div>
          {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
        </div>

        {/* Password */}
        <div>
          <label htmlFor="password" className="block text-xs font-bold text-white mb-1">
            Password
          </label>
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-white/60 text-lg">
              lock
            </span>
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
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

        {/* Confirm Password */}
        <div>
          <label htmlFor="confirm_password" className="block text-xs font-bold text-white mb-1">
            Confirm password
          </label>
          <input
            id="confirm_password"
            type="password"
            placeholder="Repeat password"
            className={`w-full bg-white/5 text-white placeholder:text-white/40 px-4 py-3 text-sm rounded-xl outline-none border transition-all ${
              errors.confirm_password ? "border-red-500" : "border-white/10 focus:border-primary focus:bg-white/10"
            }`}
            {...register("confirm_password")}
          />
          {errors.confirm_password && (
            <p className="text-xs text-red-500 mt-1">{errors.confirm_password.message}</p>
          )}
        </div>

        {/* Terms */}
        <div className="flex items-start gap-2 pt-1">
          <input
            id="terms"
            type="checkbox"
            className="w-4 h-4 mt-0.5 accent-primary rounded cursor-pointer"
            {...register("terms")}
          />
          <label htmlFor="terms" className="text-xs text-white/80 font-medium cursor-pointer">
            I agree to the <a href="#" className="text-emerald-400 font-bold hover:underline">Terms & Conditions</a> and <a href="#" className="text-emerald-400 font-bold hover:underline">Privacy Policy</a>.
          </label>
        </div>
        {errors.terms && <p className="text-xs text-red-500">{errors.terms.message}</p>}

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-primary-container text-on-primary-container font-bold py-3.5 rounded-xl hover:bg-emerald-500 transition-colors shadow-md text-sm flex items-center justify-center gap-2 mt-2 disabled:opacity-60"
        >
          {isSubmitting ? (
            <span>Creating account...</span>
          ) : (
            <>
              Create Account
              <span className="material-symbols-outlined text-base">arrow_forward</span>
            </>
          )}
        </button>
      </form>

      {/* Login Footer Link */}
      <div className="text-center pt-4 border-t border-white/20 mt-4">
        <p className="text-xs text-white/80">
          Already have an account?{" "}
          <Link href="/login" className="font-bold text-emerald-400 hover:underline ml-1">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
