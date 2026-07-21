import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: {
    default: "Authentication",
    template: "%s | AutoWorth AI",
  },
};

/**
 * Auth route group layout — premium split-screen design:
 *  Left:  Branded panel with gradient, tagline, and animated background
 *  Right: Form panel (rendered by child pages)
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex bg-[#0a0a0f]">
      {/* ── Left Branded Panel ───────────────────────── */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden flex-col justify-between p-12">
        {/* Animated gradient background */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 80% 80% at 50% -20%, rgba(99,102,241,0.25) 0%, transparent 60%), " +
              "radial-gradient(ellipse 60% 60% at 80% 80%, rgba(139,92,246,0.15) 0%, transparent 60%), " +
              "#0a0a0f",
          }}
        />

        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), " +
              "linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />

        {/* Floating orbs */}
        <div
          className="absolute top-1/4 left-1/4 w-64 h-64 rounded-full opacity-10 blur-3xl"
          style={{ background: "radial-gradient(circle, #6366f1, transparent)" }}
        />
        <div
          className="absolute bottom-1/3 right-1/4 w-48 h-48 rounded-full opacity-10 blur-3xl"
          style={{ background: "radial-gradient(circle, #8b5cf6, transparent)" }}
        />

        {/* Logo */}
        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg"
              style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
            >
              A
            </div>
            <span className="text-white font-semibold text-xl tracking-tight">
              AutoWorth AI
            </span>
          </div>
        </div>

        {/* Main tagline */}
        <div className="relative z-10 space-y-6">
          <div>
            <h1 className="text-5xl font-bold text-white leading-tight tracking-tight">
              Know your car&apos;s
              <br />
              <span
                style={{
                  background: "linear-gradient(135deg, #818cf8, #c084fc)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                true worth.
              </span>
            </h1>
            <p className="mt-4 text-slate-400 text-lg max-w-md leading-relaxed">
              AI-powered valuations for India&apos;s used car market. Transparent,
              accurate, and explainable — backed by ML and Computer Vision.
            </p>
          </div>

          {/* Stats */}
          <div className="flex gap-8">
            {[
              { value: "98%", label: "Accuracy" },
              { value: "2.4s", label: "Avg. speed" },
              { value: "50k+", label: "Valuations" },
            ].map((stat) => (
              <div key={stat.label}>
                <div
                  className="text-2xl font-bold"
                  style={{
                    background: "linear-gradient(135deg, #818cf8, #c084fc)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                  }}
                >
                  {stat.value}
                </div>
                <div className="text-slate-500 text-sm mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom quote */}
        <div className="relative z-10">
          <p className="text-slate-600 text-sm">
            &ldquo;The smartest way to price used cars in India.&rdquo;
          </p>
        </div>
      </div>

      {/* ── Right Form Panel ─────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-6 relative">
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "radial-gradient(circle at center, rgba(99,102,241,0.8) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="relative z-10 w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
