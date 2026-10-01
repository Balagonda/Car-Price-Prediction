"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";

export default function ForbiddenPageClient() {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-card border border-border rounded-2xl p-8 text-center space-y-6">
        <div className="mx-auto w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mb-4">
          <ShieldAlert className="w-8 h-8 text-destructive" />
        </div>
        <h1 className="text-3xl font-bold text-foreground">Access Denied</h1>
        <p className="text-muted-foreground">
          You do not have the required permissions to view this page. If you believe this is a mistake, please contact support.
        </p>
        <div className="pt-4 flex justify-center">
          <Button onClick={() => router.push('/dashboard')} variant="default">
            Return to Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
