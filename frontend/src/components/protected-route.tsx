"use client";

/**
 * AutoWorth AI — Protected Route Wrapper
 *
 * Client component that enforces authentication and authorization:
 *  - Unauthenticated users → redirect to /login
 *  - Authenticated but unverified → redirect to /verify-email
 *  - Authenticated but insufficient role → render fallback (403)
 *
 * Usage:
 *   <ProtectedRoute>…dashboard content…</ProtectedRoute>
 *   <ProtectedRoute requiredRole="admin">…admin content…</ProtectedRoute>
 */

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-context";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: "user" | "admin";
  /** Optional fallback shown while loading */
  loadingFallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  requiredRole,
  loadingFallback,
}: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated, isVerified, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    if (!isVerified) {
      router.replace("/verify-email");
      return;
    }

    if (requiredRole === "admin" && !isAdmin) {
      router.replace("/403");
    }
  }, [isLoading, isAuthenticated, isVerified, isAdmin, requiredRole, router]);

  if (isLoading) {
    return (
      loadingFallback ?? (
        <div className="flex min-h-screen items-center justify-center bg-[#0a0a0f]">
          <div className="flex flex-col items-center gap-4">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-violet-600 border-t-transparent" />
            <p className="text-sm text-slate-400">Loading…</p>
          </div>
        </div>
      )
    );
  }

  if (!isAuthenticated || !isVerified) return null;
  if (requiredRole === "admin" && !isAdmin) return null;

  return <>{children}</>;
}
