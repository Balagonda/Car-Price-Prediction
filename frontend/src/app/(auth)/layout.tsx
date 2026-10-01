import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: {
    default: "Authentication | CarWorth",
    template: "%s | CarWorth AI",
  },
};

/**
 * Auth route group layout — CarWorth Split-Screen Design:
 * Left:  CarWorth car showcase image panel with gradient overlay & brand taglines
 * Right: Form panel (rendered by child login/register pages)
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex relative bg-surface font-sans text-on-surface">
      {/* ── Background Car Showcase Image ───────────────────────── */}
      <div className="absolute inset-0 z-0">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/auth-car.jpg"
          alt="Premium vehicle showcasing CarWorth quality standard"
          className="w-full h-full object-cover"
        />
        {/* Brand Tint & Gradients */}
        <div className="absolute inset-0 bg-emerald-500/20 mix-blend-overlay" />
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-900/80 via-emerald-700/40 to-emerald-200/20" />
      </div>

      {/* ── Left Branded Car Panel ───────────────────────── */}
      <div className="hidden lg:flex lg:w-1/2 relative z-10 flex-col justify-between p-12">

        {/* Top Brand Header */}
        <div className="relative z-20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-xl shadow-lg">
              <span className="material-symbols-outlined text-2xl text-primary">directions_car</span>
            </div>
            <span className="text-white font-extrabold text-2xl tracking-tight">
              CarWorth <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-300">AI</span>
            </span>
          </div>
        </div>

        {/* Main Tagline & Copy */}
        <div className="relative z-20 space-y-6 max-w-lg">
          <div>
            <span className="inline-block px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-emerald-300 font-bold text-xs uppercase tracking-wider mb-3">
              Sustainable Rides & Transparent Deals
            </span>
            <h1 className="text-4xl md:text-5xl font-extrabold text-white leading-tight tracking-tight">
              Drive the Future with True Valuation.
            </h1>
            <p className="mt-4 text-emerald-100/90 text-base leading-relaxed">
              Join CarWorth&apos;s premium marketplace. Transparent AI vehicle valuations, IBB-certified listings, and seamless digital deals.
            </p>
          </div>


        </div>

        {/* Footer Note */}
        <div className="relative z-20 text-xs text-emerald-200/60">
          © 2026 CarWorth Marketplace & AI Engine. Driven by Transparency.
        </div>
      </div>

      {/* ── Right Form Panel ─────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-6 md:p-12 relative z-10">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
