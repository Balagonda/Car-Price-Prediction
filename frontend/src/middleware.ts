import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const CANONICAL_HOST = "frontend-tau-sandy-39.vercel.app";

/**
 * Middleware to redirect authentication routes on preview deployments
 * to the canonical production domain. This prevents Google OAuth
 * "origin_mismatch" (Error 400) caused by dynamic preview URL hashes.
 */
export function middleware(request: NextRequest) {
  const host = request.headers.get("host") || "";

  // If user visits auth routes on a preview deployment hash (*.vercel.app)
  if (
    host.endsWith(".vercel.app") &&
    host !== CANONICAL_HOST &&
    (request.nextUrl.pathname.startsWith("/login") ||
      request.nextUrl.pathname.startsWith("/register") ||
      request.nextUrl.pathname.startsWith("/auth"))
  ) {
    const url = request.nextUrl.clone();
    url.host = CANONICAL_HOST;
    url.protocol = "https";
    url.port = "";
    return NextResponse.redirect(url, 307);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/login", "/register", "/auth/:path*"],
};
