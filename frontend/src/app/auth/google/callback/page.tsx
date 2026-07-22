"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/providers/auth-context";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function GoogleCallbackPage() {
  const { googleLogin } = useAuth();
  const router = useRouter();
  const loginAttempted = useRef(false);

  useEffect(() => {
    if (loginAttempted.current) return;

    const handleCallback = async () => {
      // Google redirects with fragment/hash containing id_token
      const hash = typeof window !== "undefined" ? window.location.hash : "";
      if (!hash) {
        toast.error("Authentication failed", {
          description: "No response received from Google.",
        });
        router.push("/login");
        return;
      }

      const params = new URLSearchParams(hash.substring(1)); // remove '#'
      const idToken = params.get("id_token");

      if (!idToken) {
        toast.error("Authentication failed", {
          description: "Google ID token not found in response.",
        });
        router.push("/login");
        return;
      }

      loginAttempted.current = true;
      try {
        await googleLogin(idToken);
        toast.success("Welcome back!", {
          description: "Google login successful.",
        });
        router.push("/dashboard");
      } catch (err: any) {
        toast.error("Login failed", {
          description: err.message || "An error occurred during Google authentication.",
        });
        router.push("/login");
      }
    };

    handleCallback();
  }, [googleLogin, router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <div className="flex flex-col items-center space-y-4 text-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <h2 className="text-xl font-semibold">Completing sign-in</h2>
        <p className="text-sm text-muted-foreground">
          Please wait while we verify your Google credentials.
        </p>
      </div>
    </div>
  );
}
