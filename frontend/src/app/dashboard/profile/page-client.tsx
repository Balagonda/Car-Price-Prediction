"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/providers/auth-context";
import { getAPIError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, User, Shield, CheckCircle, Save, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";

function ProfileContent() {
  const router = useRouter();
  const { user, updateProfile, isAdmin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await updateProfile(formData);
      toast.success("Profile updated successfully!");
    } catch (error) {
      toast.error(getAPIError(error).message || "Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-surface text-on-surface flex flex-col font-sans">
      <Navbar />

      <main className="pt-20 pb-16 flex-1 max-w-4xl mx-auto px-4 md:px-8 w-full space-y-8">
        <Button
          variant="outline"
          onClick={() => router.push("/")}
          className="gap-2 border-surface-variant text-on-surface hover:bg-surface-container font-semibold"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Home
        </Button>

        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold text-on-surface flex items-center gap-3 tracking-tight">
            <User className="h-8 w-8 text-primary" /> My Profile
          </h1>
          <p className="text-on-surface-variant text-sm font-medium">
            Manage your account details and AutoGreen valuation preferences.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Avatar / Summary */}
          <div className="col-span-1 border border-surface-variant rounded-2xl p-6 bg-white text-on-surface mint-glow space-y-6 flex flex-col justify-between">
            <div className="flex flex-col items-center text-center">
              {user.profile_image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={user.profile_image_url}
                  alt="Profile"
                  className="w-24 h-24 rounded-full object-cover ring-4 ring-primary/30"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-primary text-white flex items-center justify-center text-3xl font-extrabold shadow-md">
                  {user.first_name?.[0] || "U"}
                  {user.last_name?.[0] || ""}
                </div>
              )}
              <h2 className="text-xl font-bold text-on-surface mt-4">
                {user.first_name} {user.last_name}
              </h2>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold mt-2 bg-mint-soft text-primary">
                {isAdmin ? <Shield className="h-3.5 w-3.5" /> : <User className="h-3.5 w-3.5" />}
                {user.role?.name || "User"}
              </span>
            </div>

            <div className="space-y-3 pt-4 border-t border-surface-variant">
              <div className="flex justify-between items-center text-xs font-semibold">
                <span className="text-on-surface-variant">Status</span>
                <span className="flex items-center gap-1 text-emerald-600 font-bold">
                  <CheckCircle className="h-4 w-4" /> Verified
                </span>
              </div>
              <div className="flex justify-between items-center text-xs font-semibold">
                <span className="text-on-surface-variant">Joined</span>
                <span className="font-bold text-on-surface">
                  {user.created_at
                    ? new Intl.DateTimeFormat("en-US", { month: "short", year: "numeric" }).format(
                        new Date(user.created_at)
                      )
                    : "Recently"}
                </span>
              </div>
            </div>
          </div>

          {/* Edit Form */}
          <div className="col-span-1 md:col-span-2 border border-surface-variant rounded-2xl p-6 bg-white text-on-surface mint-glow space-y-6">
            <h3 className="text-lg font-bold text-on-surface border-b border-surface-variant pb-3">
              Personal Information
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="first_name" className="text-xs font-bold text-on-surface">
                  First Name
                </Label>
                <Input
                  id="first_name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  className="bg-surface-container-low text-on-surface border-surface-variant text-sm font-medium focus:border-primary"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="last_name" className="text-xs font-bold text-on-surface">
                  Last Name
                </Label>
                <Input
                  id="last_name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  className="bg-surface-container-low text-on-surface border-surface-variant text-sm font-medium focus:border-primary"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-xs font-bold text-on-surface">
                Email Address
              </Label>
              <Input
                id="email"
                value={user.email || ""}
                disabled
                className="bg-surface-container-high text-on-surface-variant opacity-80 cursor-not-allowed text-sm font-medium border-surface-variant"
              />
              <p className="text-xs text-on-surface-variant">Email addresses cannot be changed directly.</p>
            </div>

            <div className="pt-4 flex justify-end">
              <Button
                onClick={handleSave}
                disabled={loading}
                className="gap-2 bg-primary text-white font-bold px-6 py-3 rounded-xl hover:bg-emerald-800 transition-colors shadow-md text-sm"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default function ProfilePageClient() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
