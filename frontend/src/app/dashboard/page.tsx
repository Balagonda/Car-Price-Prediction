"use client";

/**
 * AutoWorth AI — Dashboard Page
 *
 * Protected route — requires authenticated + verified user.
 * Phase 2 stub: shows welcome card with user info and role badge.
 * Full dashboard UI implemented in Phase 3.
 */

import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-context";
import { ProtectedRoute } from "@/components/protected-route";
import { Button } from "@/components/ui/button";
import { Car, LogOut, Shield, User, CheckCircle, Clock, BarChart3 } from "lucide-react";

function DashboardContent() {
  const { user, logout, isAdmin } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  const roleColors: Record<string, { bg: string; text: string; label: string }> = {
    admin: {
      bg: "rgba(239,68,68,0.12)",
      text: "#f87171",
      label: "Administrator",
    },
    user: {
      bg: "rgba(99,102,241,0.12)",
      text: "#818cf8",
      label: "Registered User",
    },
    guest: {
      bg: "rgba(148,163,184,0.12)",
      text: "#94a3b8",
      label: "Guest",
    },
  };

  const roleName = user?.role?.name ?? "user";
  const roleStyle = (roleColors[roleName] ?? roleColors["user"])!;

  return (
    <div
      className="min-h-screen"
      style={{ background: "#0a0a0f" }}
    >
      {/* Background */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,0.12) 0%, transparent 70%)",
        }}
      />

      {/* Nav */}
      <nav className="relative z-10 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm"
              style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
            >
              A
            </div>
            <span className="text-white font-semibold">AutoWorth AI</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-slate-400 text-sm hidden sm:block">
              {user?.email}
            </span>
            <Button
              id="btn-logout"
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-slate-400 hover:text-white hover:bg-white/5 gap-2"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:block">Sign out</span>
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 py-12 space-y-8">
        {/* Welcome Header */}
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-white">
            Welcome back, {user?.first_name}! 👋
          </h1>
          <p className="text-slate-400">
            Your AI-powered vehicle valuation dashboard
          </p>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Profile Card */}
          <div
            className="col-span-1 rounded-2xl p-6 border space-y-4"
            style={{
              background: "rgba(255,255,255,0.03)",
              borderColor: "rgba(255,255,255,0.07)",
            }}
          >
            {/* Avatar */}
            <div className="flex items-center gap-4">
              {user?.profile_image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={user.profile_image_url}
                  alt="Profile"
                  className="w-14 h-14 rounded-full object-cover ring-2 ring-violet-500/30"
                />
              ) : (
                <div
                  className="w-14 h-14 rounded-full flex items-center justify-center text-white text-xl font-bold"
                  style={{
                    background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
                  }}
                >
                  {user?.first_name?.[0]}
                  {user?.last_name?.[0]}
                </div>
              )}
              <div>
                <p className="text-white font-semibold text-lg leading-tight">
                  {user?.first_name} {user?.last_name}
                </p>
                {/* Role badge */}
                <span
                  className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium mt-1"
                  style={{ background: roleStyle.bg, color: roleStyle.text }}
                >
                  {isAdmin ? (
                    <Shield className="h-3 w-3" />
                  ) : (
                    <User className="h-3 w-3" />
                  )}
                  {roleStyle.label}
                </span>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-2 pt-2 border-t border-white/5">
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                <span className="text-slate-300">
                  {user?.email}
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                {user?.is_verified ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                    <span className="text-slate-400">Email verified</span>
                  </>
                ) : (
                  <>
                    <Clock className="h-4 w-4 text-amber-400 flex-shrink-0" />
                    <span className="text-amber-400">Email not verified</span>
                  </>
                )}
              </div>
              {user?.oauth_provider && (
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-blue-400 flex-shrink-0" />
                  <span className="text-slate-400">
                    Signed in via {user.oauth_provider}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div
            className="col-span-1 md:col-span-2 rounded-2xl p-6 border"
            style={{
              background: "rgba(255,255,255,0.03)",
              borderColor: "rgba(255,255,255,0.07)",
            }}
          >
            <h2 className="text-white font-semibold text-lg mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                {
                  id: "btn-new-valuation",
                  icon: Car,
                  label: "New Valuation",
                  desc: "Get an instant AI price estimate",
                  gradient: "from-violet-600 to-indigo-600",
                  available: true,
                },
                {
                  id: "btn-my-reports",
                  icon: BarChart3,
                  label: "My Reports",
                  desc: "View past valuations",
                  gradient: "from-slate-700 to-slate-600",
                  available: false,
                },
              ].map((action) => (
                <button
                  key={action.label}
                  id={action.id}
                  disabled={!action.available}
                  className={`
                    flex items-start gap-4 p-4 rounded-xl text-left transition-all
                    ${action.available
                      ? "hover:scale-[1.02] hover:shadow-lg cursor-pointer"
                      : "opacity-50 cursor-not-allowed"
                    }
                  `}
                  style={{
                    background: `linear-gradient(135deg, ${action.available ? "rgba(99,102,241,0.15)" : "rgba(255,255,255,0.04)"}, transparent)`,
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                >
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center bg-gradient-to-br ${action.gradient} flex-shrink-0`}
                  >
                    <action.icon className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-white font-medium">{action.label}</p>
                    <p className="text-slate-500 text-sm mt-0.5">{action.desc}</p>
                    {!action.available && (
                      <span className="text-xs text-slate-600 mt-1 block">
                        Available in Phase 3
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Phase notice */}
        <div
          className="rounded-xl px-5 py-4 border border-violet-500/20 flex items-start gap-3"
          style={{ background: "rgba(99,102,241,0.06)" }}
        >
          <div className="w-5 h-5 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <div className="w-2 h-2 rounded-full bg-violet-400" />
          </div>
          <div>
            <p className="text-violet-300 font-medium text-sm">Phase 2 complete — Auth is live</p>
            <p className="text-slate-500 text-sm mt-0.5">
              Phase 3 will unlock the full prediction dashboard, vehicle catalog, and SHAP explainability reports.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  );
}
