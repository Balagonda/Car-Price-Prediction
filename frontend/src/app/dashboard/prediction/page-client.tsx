"use client";

import React from "react";
import { PredictionWizard } from "@/components/prediction-wizard";
import { Navbar } from "@/components/navbar";
import { ProtectedRoute } from "@/components/protected-route";

export default function PredictionPageClient() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-surface flex flex-col font-sans">
        <Navbar />
        <main className="pt-24 pb-16 flex-1 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="mb-6">
            <h1 className="text-3xl font-extrabold text-on-surface tracking-tight">AI Vehicle Valuation</h1>
            <p className="mt-1 text-sm text-on-surface-variant font-medium">
              Get an instant, data-driven price estimate for your car.
            </p>
          </div>
          <PredictionWizard />
        </main>
      </div>
    </ProtectedRoute>
  );
}
