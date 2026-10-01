"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { ThemeToggle } from "./theme-toggle";
import { useAuth } from "@/providers/auth-context";
import { LoginModal } from "./login-modal";

function SearchParamsHandler({
  onOpenModal,
  isAuthenticated,
}: {
  onOpenModal: () => void;
  isAuthenticated: boolean;
}) {
  const searchParams = useSearchParams();
  useEffect(() => {
    if (searchParams.get("login") === "true" && !isAuthenticated) {
      onOpenModal();
    }
  }, [searchParams, isAuthenticated, onOpenModal]);
  return null;
}

export function Navbar() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout, isAdmin } = useAuth();
  const [city, setCity] = useState("Mumbai");
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);

  const navLinks = [
    { href: "/", label: "Home" },
    { href: "/valuation", label: "Valuation" },
    { href: "/search", label: "Buy&Sell used cars" },
  ];

  return (
    <>
      <Suspense fallback={null}>
        <SearchParamsHandler
          onOpenModal={() => setIsLoginModalOpen(true)}
          isAuthenticated={isAuthenticated}
        />
      </Suspense>

      <header className="fixed top-0 left-0 w-full z-50 glass-nav border-b border-surface-variant transition-all">
        <div className="max-w-7xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-9 h-9 rounded-xl bg-primary text-white flex items-center justify-center font-bold text-base shadow-sm group-hover:scale-105 transition-transform">
                <span className="material-symbols-outlined text-xl">directions_car</span>
              </div>
              <span className="font-bold text-xl tracking-tight text-primary">
                AutoGreen <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary-container/20 text-primary">AI</span>
              </span>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
              {navLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`transition-colors duration-200 py-1 ${
                      isActive
                        ? "text-primary border-b-2 border-primary font-semibold"
                        : "text-on-surface-variant hover:text-primary"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-3 md:gap-4">
            <ThemeToggle />

            {/* Auth / Account Controls */}
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                {isAdmin && (
                  <Link
                    href="/admin"
                    className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-100 text-amber-700 text-xs font-bold hover:bg-amber-200 transition-colors"
                  >
                    <span className="material-symbols-outlined text-base">admin_panel_settings</span>
                    <span className="hidden sm:inline">Admin</span>
                  </Link>
                )}
                <Link
                  href="/dashboard/profile"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-mint-soft text-primary text-xs font-bold hover:bg-primary-container/30 transition-colors"
                >
                  <span className="material-symbols-outlined text-base">account_circle</span>
                  <span className="hidden sm:inline max-w-[100px] truncate">
                    {user?.first_name || "Profile"}
                  </span>
                </Link>
                <button
                  onClick={() => logout()}
                  title="Sign Out"
                  className="p-1.5 rounded-full text-on-surface-variant hover:text-red-500 transition-colors"
                >
                  <span className="material-symbols-outlined text-lg">logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsLoginModalOpen(true)}
                  className="text-xs font-bold text-primary px-3.5 py-2 rounded-xl border border-primary/30 hover:bg-mint-soft transition-colors flex items-center gap-1"
                >
                  <span className="material-symbols-outlined text-base">login</span>
                  <span>Sign In</span>
                </button>
                <Link
                  href="/register"
                  className="hidden sm:flex text-xs font-bold bg-primary text-white px-3.5 py-2 rounded-xl hover:bg-emerald-800 transition-colors shadow-sm"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Login Modal Component */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
      />
    </>
  );
}
