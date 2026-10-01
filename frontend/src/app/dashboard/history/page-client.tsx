"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ProtectedRoute } from "@/components/protected-route";
import { apiClient } from "@/lib/api-client";
import { Loader2, ArrowLeft, Car, Calendar, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PredictionItem {
  id: string;
  estimated_price: number;
  confidence_score: number;
  fair_price_status: string;
  created_at: string;
}

function HistoryContent() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [predictions, setPredictions] = useState<PredictionItem[]>([]);

  useEffect(() => {
    apiClient.get("/predictions?page=1&page_size=50")
      .then(res => {
        setPredictions(res.data.data.items);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        <Button variant="ghost" onClick={() => router.push("/dashboard")} className="gap-2">
          <ArrowLeft className="h-4 w-4" /> Back to Dashboard
        </Button>
        
        <div>
          <h1 className="text-3xl font-bold">Prediction History</h1>
          <p className="text-muted-foreground mt-1">Your past vehicle valuation reports.</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-violet-500" />
          </div>
        ) : predictions.length === 0 ? (
          <div className="text-center py-20 bg-muted/20 rounded-2xl border border-border">
            <Car className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold">No predictions yet</h3>
            <p className="text-muted-foreground mt-2">Get your first vehicle valuation now.</p>
            <Button className="mt-6 bg-violet-600 hover:bg-violet-700" onClick={() => router.push("/dashboard/prediction")}>
              New Valuation
            </Button>
          </div>
        ) : (
          <div className="grid gap-4">
            <AnimatePresence>
              {predictions.map((p, i) => (
                <motion.div
                  key={p.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="p-5 rounded-2xl border bg-card text-card-foreground hover:shadow-md transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  onClick={() => router.push(`/dashboard/prediction/results/${p.id}`)}
                >
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">
                        {new Intl.DateTimeFormat("en-US", { dateStyle: "long" }).format(new Date(p.created_at))}
                      </span>
                    </div>
                    <div className="text-2xl font-bold">
                      ₹{(p.estimated_price / 100000).toFixed(2)} Lakh
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-right hidden sm:block">
                      <p className="text-sm font-medium text-muted-foreground">Confidence</p>
                      <p className="font-semibold text-emerald-500">{p.confidence_score}%</p>
                    </div>
                    <Button variant="outline" size="sm" className="gap-2 shrink-0">
                      View Report <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}

export default function HistoryPageClient() {
  return (
    <ProtectedRoute>
      <HistoryContent />
    </ProtectedRoute>
  );
}
