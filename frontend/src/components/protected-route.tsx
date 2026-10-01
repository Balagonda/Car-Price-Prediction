"use client";

/**
 * AutoWorth AI / AutoGreen — Protected Route Wrapper
 *
 * Client component that enforces authentication and authorization:
 *  - Unauthenticated users → redirect to /login
 *  - Authenticated but unverified → redirect to /verify-email
 *  - Authenticated but insufficient role → render fallback (403)
 */

import { useEffect, useState, type ReactNode } from "react";
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
  const [isMounted, setIsMounted] = useState(false);
  const { isLoading, isAuthenticated, isVerified, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted || isLoading) return;

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
  }, [isMounted, isLoading, isAuthenticated, isVerified, isAdmin, requiredRole, router]);

  const defaultSpinner = (
    <div className="flex min-h-screen items-center justify-center bg-surface">
      <div className="flex flex-col items-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-sm text-on-surface-variant font-medium">Loading...</p>
      </div>
    </div>
  );

  // Guarantee matching HTML between server SSR and initial client hydration
  if (!isMounted || isLoading) {
    return loadingFallback ?? defaultSpinner;
  }

  if (!isAuthenticated || !isVerified) return null;
  if (requiredRole === "admin" && !isAdmin) return null;

  return <>{children}</>;
}
