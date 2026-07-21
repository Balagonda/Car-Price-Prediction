"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Download, AlertTriangle, CheckCircle, TrendingUp, TrendingDown } from "lucide-react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function PredictionResults() {
  const { id } = useParams();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    const fetchPrediction = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const res = await axios.get(`http://localhost:8000/api/v1/predictions/${id}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        setPrediction(res.data.data);
      } catch (err) {
        setError("Failed to load prediction results. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    
    if (id) {
        fetchPrediction();
    }
  }, [id]);

  const handleDownloadReport = async () => {
    setIsDownloading(true);
    try {
        const token = localStorage.getItem("access_token");
        const res = await axios.get(`http://localhost:8000/api/v1/predictions/${id}/report`, {
            headers: { Authorization: `Bearer ${token}` },
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
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8 animate-in fade-in duration-700">
        
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2 border-0 shadow-lg bg-gradient-to-br from-blue-600 to-indigo-700 text-white overflow-hidden relative">
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
                            prediction.fair_price_status === 'fair' ? 'bg-green-400/30 text-green-100' :
                            prediction.fair_price_status === 'below_market' ? 'bg-yellow-400/30 text-yellow-100' :
                            'bg-red-400/30 text-red-100'
                        }`}>
                            {prediction.fair_price_status === 'fair' ? <CheckCircle className="w-4 h-4 mr-1" /> : 
                             prediction.fair_price_status === 'below_market' ? <TrendingDown className="w-4 h-4 mr-1" /> : 
                             <TrendingUp className="w-4 h-4 mr-1" />}
                            {prediction.fair_price_status.replace('_', ' ').toUpperCase()}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* CV Damage Panel (Phase 4 mock visual) */}
            <Card className="border-0 shadow-md">
                <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Computer Vision Scan</CardTitle>
                    <CardDescription>Visual damage assessment</CardDescription>
                </CardHeader>
                <CardContent>
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
                        <div className="flex flex-col items-center justify-center h-32 text-green-600 dark:text-green-500">
                            <CheckCircle className="w-12 h-12 mb-2 opacity-50" />
                            <span className="font-medium">No exterior damage detected</span>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* AI Explainability Panel (SHAP) */}
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

            {/* Recommendations */}
            <Card className="shadow-sm border-gray-100 dark:border-gray-800 flex flex-col">
                <CardHeader>
                    <CardTitle>AI Insights & Recommendations</CardTitle>
                    <CardDescription>Actionable advice based on our ML analysis</CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                    <ScrollArea className="h-[300px] pr-4">
                        <div className="space-y-4">
                            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                            {prediction.recommendations?.map((rec: any, idx: number) => (
                                <div key={idx} className="flex gap-4 p-4 rounded-lg bg-gray-50 dark:bg-slate-800/50 border border-gray-100 dark:border-slate-700">
                                    <div className="flex-shrink-0 mt-1">
                                        {rec.priority === 'high' ? <AlertTriangle className="text-amber-500 w-5 h-5" /> : 
                                         <CheckCircle className="text-blue-500 w-5 h-5" />}
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-gray-900 dark:text-white">{rec.title}</h4>
                                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{rec.description}</p>
                                    </div>
                                </div>
                            ))}
                            {(!prediction.recommendations || prediction.recommendations.length === 0) && (
                                <p className="text-sm text-gray-500 text-center py-8">No specific recommendations at this time.</p>
                            )}
                        </div>
                    </ScrollArea>
                </CardContent>
            </Card>
        </div>

        {/* Similar Vehicles Grid */}
        <div className="pt-6">
            <h3 className="text-xl font-bold mb-4">Comparable Market Vehicles</h3>
            <p className="text-sm text-gray-500 mb-6">Found {prediction.similar_vehicles?.length || 0} similar vehicles currently listed or recently sold.</p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {prediction.similar_vehicles?.map((car: any, idx: number) => (
                    <Card key={idx} className="shadow-sm hover:shadow-md transition-shadow">
                        <CardHeader className="p-4 pb-2">
                            <div className="flex justify-between items-start">
                                <CardTitle className="text-base font-semibold truncate" title={`${car.manufacturing_year} ${car.brand} ${car.model}`}>
                                    {car.manufacturing_year} {car.model}
                                </CardTitle>
                            </div>
                            <CardDescription className="text-xs">{car.brand}</CardDescription>
                        </CardHeader>
                        <CardContent className="p-4 pt-2">
                            <div className="text-lg font-bold text-blue-600 dark:text-blue-400 mb-2">
                                {formatInr(car.selling_price)}
                            </div>
                            <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                                <div className="flex justify-between"><span>Driven:</span> <span>{(car.kilometers_driven/1000).toFixed(1)}k km</span></div>
                                <div className="flex justify-between"><span>Fuel:</span> <span className="capitalize">{car.fuel_type}</span></div>
                                <div className="flex justify-between"><span>Owner:</span> <span className="capitalize">{car.owner_type}</span></div>
                            </div>
                        </CardContent>
                        <CardFooter className="p-4 pt-0 border-t border-gray-100 dark:border-gray-800 mt-2">
                            <div className="w-full text-center text-xs font-medium text-gray-500 mt-2">
                                Match: {car.similarity_score}%
                            </div>
                        </CardFooter>
                    </Card>
                ))}
            </div>
        </div>
    </div>
  );
}
