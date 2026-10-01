"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ProtectedRoute } from "@/components/protected-route";
import { apiClient } from "@/lib/api-client";
import { Loader2, ArrowLeft, Heart, Calendar, ExternalLink, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FavoriteItem {
  id: number;
  prediction_id: string;
  created_at: string;
  prediction: {
    id: string;
    estimated_price: number;
    confidence_score: number;
    fair_price_status: string;
    created_at: string;
  };
}

function FavoritesContent() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);

  const fetchFavorites = () => {
    setLoading(true);
    apiClient.get("/favorites?page=1&page_size=50")
      .then(res => {
        setFavorites(res.data.data.items);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchFavorites();
  }, []);

  const handleRemove = async (predictionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.delete(`/favorites/${predictionId}`);
      setFavorites(prev => prev.filter(f => f.prediction_id !== predictionId));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        <Button variant="ghost" onClick={() => router.push("/dashboard")} className="gap-2">
          <ArrowLeft className="h-4 w-4" /> Back to Dashboard
        </Button>
        
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Heart className="h-8 w-8 text-pink-500 fill-pink-500" /> Favorites
          </h1>
          <p className="text-muted-foreground mt-1">Your saved vehicle valuation reports.</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-pink-500" />
          </div>
        ) : favorites.length === 0 ? (
          <div className="text-center py-20 bg-muted/20 rounded-2xl border border-border">
            <Heart className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold">No favorites yet</h3>
            <p className="text-muted-foreground mt-2">Save predictions to view them here later.</p>
            <Button className="mt-6 bg-pink-600 hover:bg-pink-700 text-white" onClick={() => router.push("/dashboard/history")}>
              View History
            </Button>
          </div>
        ) : (
          <div className="grid gap-4">
            <AnimatePresence>
              {favorites.map((fav, i) => (
                <motion.div
                  key={fav.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ delay: i * 0.05 }}
                  className="p-5 rounded-2xl border bg-card text-card-foreground hover:shadow-md transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  onClick={() => router.push(`/dashboard/prediction/results/${fav.prediction_id}`)}
                >
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm text-muted-foreground">
                        Valuated on {new Intl.DateTimeFormat("en-US", { dateStyle: "long" }).format(new Date(fav.prediction.created_at))}
                      </span>
                    </div>
                    <div className="text-2xl font-bold text-pink-500">
                      ₹{(fav.prediction.estimated_price / 100000).toFixed(2)} Lakh
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <Button variant="outline" size="sm" className="gap-2 shrink-0">
                      Report <ExternalLink className="h-4 w-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                      onClick={(e) => handleRemove(fav.prediction_id, e)}
                    >
                      <Trash2 className="h-4 w-4" />
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

export default function FavoritesPageClient() {
  return (
    <ProtectedRoute>
      <FavoritesContent />
    </ProtectedRoute>
  );
}
