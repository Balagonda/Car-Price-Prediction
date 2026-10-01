"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Download, AlertTriangle, CheckCircle, TrendingUp, TrendingDown, Car } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function PredictionResultsClient() {
  const { id } = useParams();
  const router = useRouter();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [prediction, setPrediction] = useState<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [images, setImages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isPosting, setIsPosting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [predRes, imgRes] = await Promise.all([
          apiClient.get(`/predictions/${id}`),
          apiClient.get(`/cv/${id}/images`).catch(() => ({ data: { data: { images: [] } } }))
        ]);
        setPrediction(predRes.data.data);
        
        let fetchedImages = imgRes.data?.data?.images || [];
        if (fetchedImages.length === 0 && typeof window !== "undefined") {
          const previewImage = sessionStorage.getItem(`preview_image_${id}`);
          if (previewImage) {
            fetchedImages = [{ image_url: previewImage, image_angle: 'FRONT' }];
          }
        }
        setImages(fetchedImages);
      } catch (err) {
        setError("Failed to load prediction results. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    
    if (id) {
        fetchData();
    }
  }, [id]);

  const handleDownloadReport = async () => {
    setIsDownloading(true);
    try {
        const res = await apiClient.get(`/predictions/${id}/report`, {
            responseType: 'blob', // Important for downloading files
        });
        
        // Create a blob URL and trigger download
        const url = window.URL.createObjectURL(new Blob([res.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `autoworth_report_${id}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (err) {
        alert("Failed to download the PDF report.");
    } finally {
        setIsDownloading(false);
    }
  };

  if (loading) {
      return (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
              <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="mt-4 text-lg font-medium text-gray-600">Analyzing vehicle data...</p>
          </div>
      );
  }

  if (error || !prediction) {
      return (
          <div className="max-w-3xl mx-auto py-10 px-4">
              <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
              </Alert>
          </div>
      );
  }

  // Format currency
  const formatInr = (val: number) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);

  // Prepare SHAP chart data
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const shapData = prediction.shap_results?.map((s: any) => ({
      name: s.feature_name,
      value: s.impact_direction === 'positive' ? s.shap_value : -s.shap_value,
      human_readable: s.human_readable_impact
  })) || [];

  return (
    <div className="w-full py-8 px-4 sm:px-6 lg:px-8 space-y-8 animate-in fade-in duration-700">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Valuation Dashboard</h1>
                <p className="text-gray-500 mt-1">ID: <span className="font-mono text-xs">{prediction.id}</span></p>
            </div>
            <Button 
                onClick={handleDownloadReport} 
                disabled={isDownloading}
                className="bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:text-slate-900"
            >
                {isDownloading ? (
                    <span className="flex items-center"><div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" /> Generating PDF...</span>
                ) : (
                    <><Download className="w-4 h-4 mr-2" /> Download Commercial Report</>
                )}
            </Button>
        </div>

        {prediction.confidence_warning && (
            <Alert className="bg-amber-50 border-amber-200 text-amber-800 dark:bg-amber-900/30 dark:border-amber-800 dark:text-amber-300">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Low Confidence Warning</AlertTitle>
                <AlertDescription>{prediction.confidence_warning}</AlertDescription>
            </Alert>
        )}

        {/* Hero Valuation */}
        <div className="mb-6">
            <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-600 to-indigo-700 text-white overflow-hidden relative">
                <div className="absolute top-0 right-0 p-8 opacity-10">
                    <Car className="w-48 h-48" />
                </div>
                <CardHeader>
                    <CardTitle className="text-blue-100 font-medium">Estimated Market Value</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-5xl md:text-7xl font-bold tracking-tighter">
                        {formatInr(prediction.estimated_price)}
                    </div>
                    <div className="mt-4 flex flex-wrap gap-4 items-center text-sm">
                        <div className="bg-white/20 px-3 py-1 rounded-full backdrop-blur-sm">
                            Range: {formatInr(prediction.price_range_min)} - {formatInr(prediction.price_range_max)}
                        </div>
                        <div className="bg-white/20 px-3 py-1 rounded-full backdrop-blur-sm flex items-center">
                            Confidence: {prediction.confidence_score}%
                        </div>
                        <div className={`px-3 py-1 rounded-full flex items-center font-semibold ${
                            prediction.fair_price_status === 'Fair' ? 'bg-green-400/30 text-green-100' :
                            prediction.fair_price_status === 'Below Market' ? 'bg-yellow-400/30 text-yellow-100' :
                            'bg-red-400/30 text-red-100'
                        }`}>
                            {prediction.fair_price_status === 'Fair' ? <CheckCircle className="w-4 h-4 mr-1" /> : 
                             prediction.fair_price_status === 'Below Market' ? <TrendingDown className="w-4 h-4 mr-1" /> : 
                             <TrendingUp className="w-4 h-4 mr-1" />}
                            {prediction.fair_price_status.replace('_', ' ').toUpperCase()}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>

        {/* Showcase Your Vehicle */}
        <div className="mb-6">
            <Card className="bg-white border border-gray-100 rounded-2xl shadow-sm p-6">
                <div className="text-center mb-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">Showcase Your Vehicle</h3>
                    <p className="text-sm text-gray-500">High-quality photos increase sale chances by up to 40%.</p>
                </div>
                
                {/* Main Image Preview */}
                <div className="relative rounded-2xl overflow-hidden border-2 border-dashed border-emerald-100 bg-gray-50 flex items-center justify-center mb-6 min-h-[400px] md:min-h-[500px] w-full p-2">
                    {images && images.length > 0 ? (
                        <>
                            <img src={images[0].image_url} alt="Vehicle Preview" className="w-full h-full max-h-[500px] object-contain rounded-xl" />
                            <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full flex items-center gap-1 shadow-md border border-gray-200">
                                <span className="text-xs font-semibold text-gray-700">1 / {images.length}</span>
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center text-gray-400">
                            <Car className="w-16 h-16 mb-2 opacity-50" />
                            <span className="font-medium">No images uploaded</span>
                        </div>
                    )}
                </div>

                {/* Thumbnails */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                    {images && images.length > 0 ? (
                        /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
                        images.map((img: any, idx: number) => (
                            <div key={idx} className="relative flex flex-col items-center justify-center gap-2 border border-gray-200 rounded-xl bg-white shadow-sm overflow-hidden h-24 group">
                                <img src={img.image_url} alt={img.image_angle} className="absolute inset-0 w-full h-full object-cover transition-transform group-hover:scale-105" />
                                <div className="absolute inset-0 bg-black/30"></div>
                                <span className="relative z-10 text-[10px] uppercase font-bold text-white text-center tracking-wider">{img.image_angle}</span>
                            </div>
                        ))
                    ) : (
                        ['Front', 'Rear', 'Left', 'Right', 'Interior'].map((angle, idx) => (
                            <div key={idx} className="flex flex-col items-center justify-center gap-2 p-4 border border-gray-200 rounded-xl bg-gray-50 shadow-sm h-24">
                                <Car className="w-6 h-6 text-gray-400" />
                                <span className="text-[10px] uppercase font-bold text-gray-400 text-center tracking-wider">{angle}</span>
                            </div>
                        ))
                    )}
                </div>
            </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* AI Price Drivers */}
            <Card className="shadow-sm border-gray-100 dark:border-gray-800">
                <CardHeader>
                    <CardTitle>AI Price Drivers</CardTitle>
                    <CardDescription>How specific features impacted the valuation</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={shapData} layout="vertical" margin={{ top: 5, right: 30, left: 60, bottom: 5 }}>
                                <XAxis type="number" hide />
                                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                                <Tooltip 
                                    formatter={(value: any) => [`₹${Math.abs(value).toLocaleString()}`, 'Impact']}
                                    cursor={{fill: 'transparent'}}
                                />
                                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                    {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                                    {shapData.map((entry: any, index: number) => (
                                        <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#10b981' : '#ef4444'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>

            {/* Computer Vision Scan */}
            <Card className="shadow-sm border-gray-100 dark:border-gray-800">
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Computer Vision Scan</CardTitle>
                    <CardDescription>Visual damage assessment</CardDescription>
                </CardHeader>
                <CardContent className="h-[300px] flex flex-col justify-center">
                    {prediction.cv_damage_detected ? (
                        <div className="space-y-4">
                            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 rounded-lg">
                                <div className="flex items-center text-red-600 dark:text-red-400 font-medium mb-1">
                                    <AlertTriangle className="w-4 h-4 mr-2" />
                                    Damage Detected
                                </div>
                                <p className="text-sm text-red-700 dark:text-red-300">Severity: {prediction.cv_damage_severity}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 mb-1">Estimated Repair Deduction</p>
                                <p className="text-xl font-bold text-gray-900 dark:text-white">-{formatInr(prediction.cv_repair_cost_estimate || 0)}</p>
                            </div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center text-emerald-500">
                            <CheckCircle className="w-16 h-16 mb-4 opacity-90" />
                            <span className="font-medium text-emerald-600">No exterior damage detected</span>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>


        {/* Action Buttons */}
        <div className="pt-12 pb-8 flex flex-col sm:flex-row justify-center gap-4">
            <Button 
                onClick={() => {
                    router.push("/dashboard");
                }}
                className="bg-primary hover:bg-emerald-700 text-white font-bold py-6 px-12 rounded-xl shadow-lg text-lg flex items-center gap-2 transition-all hover:scale-105"
            >
                Back to Dashboard
            </Button>
            <Button 
                onClick={async () => {
                    setIsPosting(true);
                    try {
                        await apiClient.post(`/predictions/${id}/list`);
                        router.push('/search');
                    } catch (err) {
                        alert("Failed to post listing.");
                        setIsPosting(false);
                    }
                }}
                disabled={isPosting}
                className="bg-primary hover:bg-emerald-700 text-white font-bold py-6 px-12 rounded-xl shadow-lg text-lg flex items-center gap-2 transition-all hover:scale-105"
            >
                {isPosting ? "Posting..." : "Post in Sell & Buy"}
            </Button>
        </div>
    </div>
  );
}
