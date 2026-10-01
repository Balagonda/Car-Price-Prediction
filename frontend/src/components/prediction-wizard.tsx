"use client";

import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Camera, ChevronRight, ChevronLeft, CheckCircle2, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { getBrands, getModelsByBrand, getVariantsByModel, getCities, formatCityName, Brand, CarModel, Variant, City } from "@/lib/vehicles";

const predictionSchema = z.object({
  brand_id: z.coerce.number().min(1, "Brand is required"),
  car_model_id: z.coerce.number().min(1, "Model is required"),
  variant_id: z.coerce.number().optional(),
  city_id: z.coerce.number().optional(),
  manufacturing_year: z.coerce.number().min(1990).max(2025),
  fuel_type: z.enum(["Petrol", "Diesel", "CNG", "LPG", "Electric", "Hybrid"]),
  transmission: z.enum(["Manual", "Automatic", "AMT", "DCT", "CVT"]),
  owner_type: z.enum(["First Owner", "Second Owner", "Third Owner", "Fourth & Above Owner", "Test Drive Car"]),
  seller_type: z.enum(["Individual", "Dealer", "Trustmark Dealer"]),
  category: z.enum(["Hatchback", "Sedan", "SUV", "MUV", "Luxury", "Electric", "Commercial", "Coupe", "Convertible"]),
  kilometers_driven: z.coerce.number().min(0).max(1000000),
  engine_cc: z.coerce.number().min(50).max(10000).optional(),
  mileage_kmpl: z.coerce.number().min(0).max(100).optional(),
  seats: z.coerce.number().min(1).max(14).optional(),
  max_power_bhp: z.coerce.number().min(0).max(2000).optional(),
  insurance_status: z.enum(["Comprehensive", "Third Party", "Zero Depreciation", "Expired", "Not Available"]),
});

type PredictionFormValues = z.infer<typeof predictionSchema>;

const STEPS = [
  { id: 1, title: "Core Specs", description: "Basic vehicle details" },
  { id: 2, title: "Condition", description: "Mileage & Ownership" },
  { id: 3, title: "Images", description: "Optional damage scan" },
];

export function PredictionWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [brands, setBrands] = useState<Brand[]>([]);
  const [models, setModels] = useState<CarModel[]>([]);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [imageFile, setImageFile] = useState<File | null>(null);

  const form = useForm<PredictionFormValues>({
    resolver: zodResolver(predictionSchema) as any,
    defaultValues: {
      brand_id: undefined,
      car_model_id: undefined,
      variant_id: undefined,
      manufacturing_year: 2018,
      fuel_type: "Petrol",
      transmission: "Manual",
      owner_type: "First Owner",
      seller_type: "Individual",
      category: "Sedan",
      kilometers_driven: 50000,
      engine_cc: 1200,
      mileage_kmpl: 18.5,
      seats: 5,
      max_power_bhp: 85,
      insurance_status: "Comprehensive",
    } as Partial<PredictionFormValues>,
  });

  const selectedBrand = form.watch("brand_id");
  const selectedModel = form.watch("car_model_id");

  useEffect(() => {
    getBrands().then(setBrands).catch(console.error);
    getCities().then(setCities).catch(console.error);
  }, []);

  useEffect(() => {
    if (selectedBrand && selectedBrand > 0) {
      getModelsByBrand(selectedBrand).then(setModels).catch(console.error);
    } else {
      setModels([]);
    }
  }, [selectedBrand]);

  useEffect(() => {
    if (selectedModel && selectedModel > 0) {
      getVariantsByModel(selectedModel).then(setVariants).catch(console.error);
    } else {
      setVariants([]);
    }
  }, [selectedModel]);

  const nextStep = async () => {
    let fieldsToValidate: any[] = [];
    if (currentStep === 1) {
      fieldsToValidate = ['brand_id', 'car_model_id', 'variant_id', 'manufacturing_year', 'fuel_type', 'transmission', 'category'];
    } else if (currentStep === 2) {
      fieldsToValidate = ['kilometers_driven', 'owner_type', 'seller_type', 'insurance_status', 'engine_cc', 'seats', 'city_id', 'mileage_kmpl'];
    }
    
    const isValid = await form.trigger(fieldsToValidate);
    if (isValid) {
      setCurrentStep((prev) => Math.min(prev + 1, STEPS.length));
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => Math.max(prev - 1, 1));
    }
  };

  const onSubmit = async (data: PredictionFormValues) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const payload = { ...data };
      if (!payload.variant_id || payload.variant_id < 0) delete payload.variant_id;
      if (!payload.city_id || payload.city_id < 0) delete payload.city_id;

      const res = await apiClient.post("/predictions", payload);
      const predictionId = res.data.data.id;
      
      if (imageFile) {
        // Save to sessionStorage for quick preview on result page (in case backend upload fails due to missing Cloudinary config)
        await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => {
            sessionStorage.setItem(`preview_image_${predictionId}`, reader.result as string);
            resolve(null);
          };
          reader.readAsDataURL(imageFile);
        });

        const formData = new FormData();
        formData.append("prediction_id", predictionId);
        formData.append("front_image", imageFile);
        
        try {
          const token = localStorage.getItem("access_token");
          const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
          await fetch(`${baseUrl}/api/v1/cv/analyze`, {
            method: "POST",
            headers: token ? { "Authorization": `Bearer ${token}` } : {},
            body: formData
          });
        } catch (cvErr) {
          console.error("CV Analysis failed but prediction succeeded", cvErr);
        }
      }
      
      router.push(`/dashboard/prediction/results/${predictionId}`);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError("Session expired. Redirecting to login...");
        setTimeout(() => router.push("/login"), 1500);
      } else if (err.response?.status === 422) {
        setError("Validation error: " + JSON.stringify(err.response?.data?.detail));
      } else {
        setError(err.response?.data?.detail?.message || "An error occurred during prediction.");
      }
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full space-y-6">
      <div className="mb-6">
        <Progress value={(currentStep / STEPS.length) * 100} className="h-2 bg-surface-container" />
        <div className="flex justify-between mt-4">
          {STEPS.map((step) => (
            <div
              key={step.id}
              className={`flex flex-col items-center text-xs ${
                currentStep >= step.id ? "text-primary font-bold" : "text-on-surface-variant"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center mb-1.5 font-bold transition-colors ${
                  currentStep >= step.id
                    ? "bg-mint-soft text-primary border-2 border-primary"
                    : "bg-surface-container border border-surface-variant text-on-surface-variant"
                }`}
              >
                {currentStep > step.id ? <CheckCircle2 className="w-5 h-5 text-primary" /> : step.id}
              </div>
              <span>{step.title}</span>
            </div>
          ))}
        </div>
      </div>

      <Card className="border border-surface-variant bg-card mint-glow rounded-2xl">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-bold text-on-surface">
            {STEPS[currentStep - 1]?.title}
          </CardTitle>
          <CardDescription className="text-xs text-on-surface-variant">
            {STEPS[currentStep - 1]?.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive" className="border-red-500 bg-red-50 text-red-800 rounded-xl">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle className="font-bold text-xs">Error</AlertTitle>
              <AlertDescription className="text-xs">{error}</AlertDescription>
            </Alert>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-4">
              {/* STEP 1: Core Specs */}
              {currentStep === 1 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in duration-300">
                  <FormField
                    control={form.control}
                    name="brand_id"
                    render={({ field }) => {
                      const selectedBrandName = brands.find((b) => b.id === field.value)?.name;
                      return (
                        <FormItem>
                          <FormLabel className="text-xs font-bold text-on-surface">Brand</FormLabel>
                          <Select
                            onValueChange={(val) => {
                              const num = parseInt(val || "0");
                              field.onChange(num);
                              form.setValue("car_model_id", undefined as any);
                              form.setValue("variant_id", undefined as any);
                            }}
                            value={field.value ? String(field.value) : ""}
                          >
                            <FormControl>
                              <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                                <SelectValue placeholder="Select Brand">{selectedBrandName}</SelectValue>
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent className="bg-card border-surface-variant">
                              {brands.map((brand) => (
                                <SelectItem key={brand.id} value={brand.id.toString()}>
                                  {brand.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage className="text-xs text-red-500" />
                        </FormItem>
                      );
                    }}
                  />

                  <FormField
                    control={form.control}
                    name="car_model_id"
                    render={({ field }) => {
                      const selectedModelName = models.find((m) => m.id === field.value)?.name;
                      return (
                        <FormItem>
                          <FormLabel className="text-xs font-bold text-on-surface">Model</FormLabel>
                          <Select
                            onValueChange={(val) => {
                              const num = parseInt(val || "0");
                              field.onChange(num);
                              form.setValue("variant_id", undefined as any);
                            }}
                            value={field.value ? String(field.value) : ""}
                          >
                            <FormControl>
                              <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                                <SelectValue placeholder="Select Model">{selectedModelName}</SelectValue>
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent className="bg-card border-surface-variant">
                              {models.map((model) => (
                                <SelectItem key={model.id} value={model.id.toString()}>
                                  {model.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage className="text-xs text-red-500" />
                        </FormItem>
                      );
                    }}
                  />

                  <FormField
                    control={form.control}
                    name="variant_id"
                    render={({ field }) => {
                      const selectedVariantName = variants.find((v) => v.id === field.value)?.name;
                      return (
                        <FormItem>
                          <FormLabel className="text-xs font-bold text-on-surface">Variant (Optional)</FormLabel>
                          <Select
                            onValueChange={(val) => field.onChange(parseInt(val || "0"))}
                            value={field.value ? String(field.value) : ""}
                          >
                            <FormControl>
                              <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                                <SelectValue placeholder="Select Variant">{selectedVariantName}</SelectValue>
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent className="bg-card border-surface-variant">
                              {variants.map((variant) => (
                                <SelectItem key={variant.id} value={variant.id.toString()}>
                                  {variant.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage className="text-xs text-red-500" />
                        </FormItem>
                      );
                    }}
                  />

                  <FormField
                    control={form.control}
                    name="manufacturing_year"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Manufacturing Year</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            className="bg-surface-container-low border-surface-variant rounded-xl text-sm"
                          />
                        </FormControl>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="category"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Body Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                              <SelectValue placeholder="Select Body Type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent className="bg-card border-surface-variant">
                            <SelectItem value="Hatchback">Hatchback</SelectItem>
                            <SelectItem value="Sedan">Sedan</SelectItem>
                            <SelectItem value="SUV">SUV</SelectItem>
                            <SelectItem value="MUV">MUV</SelectItem>
                            <SelectItem value="Luxury">Luxury</SelectItem>
                            <SelectItem value="Electric">Electric</SelectItem>
                            <SelectItem value="Commercial">Commercial</SelectItem>
                            <SelectItem value="Coupe">Coupe</SelectItem>
                            <SelectItem value="Convertible">Convertible</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="fuel_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Fuel Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                              <SelectValue placeholder="Select Fuel Type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent className="bg-card border-surface-variant">
                            <SelectItem value="Petrol">Petrol</SelectItem>
                            <SelectItem value="Diesel">Diesel</SelectItem>
                            <SelectItem value="CNG">CNG</SelectItem>
                            <SelectItem value="LPG">LPG</SelectItem>
                            <SelectItem value="Electric">Electric</SelectItem>
                            <SelectItem value="Hybrid">Hybrid</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="transmission"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Transmission</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                              <SelectValue placeholder="Select Transmission" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent className="bg-card border-surface-variant">
                            <SelectItem value="Manual">Manual</SelectItem>
                            <SelectItem value="Automatic">Automatic</SelectItem>
                            <SelectItem value="AMT">AMT</SelectItem>
                            <SelectItem value="DCT">DCT</SelectItem>
                            <SelectItem value="CVT">CVT</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />
                </div>
              )}

              {/* STEP 2: Condition */}
              {currentStep === 2 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in duration-300">
                  <FormField
                    control={form.control}
                    name="city_id"
                    render={({ field }) => {
                      const selectedCityName = cities.find((c) => c.id === field.value)?.name;
                      return (
                        <FormItem>
                          <FormLabel className="text-xs font-bold text-on-surface">City (Optional)</FormLabel>
                          <Select
                            onValueChange={(val) => field.onChange(parseInt(val || "0"))}
                            value={field.value?.toString() || ""}
                          >
                            <FormControl>
                              <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                                <SelectValue placeholder="Select City">{selectedCityName ? formatCityName(selectedCityName) : ""}</SelectValue>
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent className="bg-card border-surface-variant">
                              {cities.map((city) => (
                                <SelectItem key={city.id} value={city.id.toString()}>
                                  {formatCityName(city.name)}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage className="text-xs text-red-500" />
                        </FormItem>
                      );
                    }}
                  />

                  <FormField
                    control={form.control}
                    name="kilometers_driven"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Kilometers Driven</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            className="bg-surface-container-low border-surface-variant rounded-xl text-sm"
                          />
                        </FormControl>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="mileage_kmpl"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Mileage (kmpl)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            className="bg-surface-container-low border-surface-variant rounded-xl text-sm"
                          />
                        </FormControl>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="owner_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Ownership</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                              <SelectValue placeholder="Select Ownership" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent className="bg-card border-surface-variant">
                            <SelectItem value="First Owner">1st Owner</SelectItem>
                            <SelectItem value="Second Owner">2nd Owner</SelectItem>
                            <SelectItem value="Third Owner">3rd Owner</SelectItem>
                            <SelectItem value="Fourth & Above Owner">4th+ Owner</SelectItem>
                            <SelectItem value="Test Drive Car">Test Drive Car</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="seller_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Seller Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                              <SelectValue placeholder="Select Seller" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent className="bg-card border-surface-variant">
                            <SelectItem value="Individual">Individual</SelectItem>
                            <SelectItem value="Dealer">Dealer</SelectItem>
                            <SelectItem value="Trustmark Dealer">Trustmark Dealer</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="insurance_status"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Insurance Status</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger className="bg-surface-container-low border-surface-variant rounded-xl text-sm">
                              <SelectValue placeholder="Select Insurance" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent className="bg-card border-surface-variant">
                            <SelectItem value="Comprehensive">Comprehensive</SelectItem>
                            <SelectItem value="Third Party">Third Party</SelectItem>
                            <SelectItem value="Zero Depreciation">Zero Dep</SelectItem>
                            <SelectItem value="Expired">Expired</SelectItem>
                            <SelectItem value="Not Available">Not Available</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="engine_cc"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Engine (CC)</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            className="bg-surface-container-low border-surface-variant rounded-xl text-sm"
                          />
                        </FormControl>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="seats"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-bold text-on-surface">Seats</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            className="bg-surface-container-low border-surface-variant rounded-xl text-sm"
                          />
                        </FormControl>
                        <FormMessage className="text-xs text-red-500" />
                      </FormItem>
                    )}
                  />
                </div>
              )}

              {/* STEP 3: Images */}
              {currentStep === 3 && (
                <div className="space-y-6 animate-in fade-in duration-300">
                  <div className="text-center">
                    <h3 className="text-lg font-bold text-on-surface">Showcase Your Vehicle</h3>
                    <p className="text-xs text-on-surface-variant mt-1">
                      High-quality photos increase sale chances by up to 40%.
                    </p>
                  </div>

                  <div 
                    onClick={() => document.getElementById("file-upload")?.click()}
                    className="border-2 border-dashed border-[#2ecc71]/40 hover:border-primary rounded-3xl p-8 transition-colors bg-white cursor-pointer relative flex flex-col items-center justify-center min-h-[220px]"
                  >
                    <input
                      id="file-upload"
                      type="file"
                      accept="image/jpeg, image/png, image/webp"
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          setImageFile(e.target.files[0] || null);
                        }
                      }}
                      className="hidden"
                    />
                    
                    <div className="w-14 h-14 bg-mint-soft text-primary rounded-full flex items-center justify-center mb-4">
                      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                    </div>

                    <p className="text-sm font-bold text-on-surface">Click to Upload or Drag & Drop</p>
                    <p className="text-xs text-on-surface-variant mt-1">Support for JPG, PNG and HEIC (Max 10MB per file)</p>
                    <p className="text-xs text-primary font-semibold mt-3">Maximum of 20 photos</p>

                    {imageFile && (
                      <div className="absolute inset-0 bg-white/95 rounded-3xl flex flex-col items-center justify-center p-4">
                        <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mb-2">
                          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                        <p className="text-xs font-bold text-on-surface max-w-[80%] truncate">Selected: {imageFile.name}</p>
                        <p className="text-[10px] text-on-surface-variant mt-1">Click again to change</p>
                      </div>
                    )}
                  </div>

                  {/* Profile Quick Buttons */}
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
                    {[
                      { 
                        id: "front", 
                        label: "FRONT PROFILE", 
                        icon: (
                          <svg className="w-6 h-6 mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-3.8-1.7-4.2c-.4-.4-1.2-.8-1.8-.8H8.5c-.6 0-1.4.4-1.8.8C6.3 6.2 5 10 5 10s-2.7.6-4.5 1.1C.2 11.3 0 12.1 0 13v3c0 .6.4 1 1 1h2m0 0c0 1.1.9 2 2 2s2-.9 2-2M3 17h14m0 0c0 1.1.9 2 2 2s2-.9 2-2" />
                          </svg>
                        )
                      },
                      { 
                        id: "rear", 
                        label: "REAR PROFILE", 
                        icon: (
                          <svg className="w-6 h-6 mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 17H3c-.6 0-1-.4-1-1v-3c0-.9.7-1.7 1.5-1.9C5.3 10.6 8 10 8 10s1.3-3.8 1.7-4.2c.4-.4 1.2-.8 1.8-.8h3c.6 0 1.4.4 1.8.8.4.4 1.7 4.2 1.7 4.2s2.7.6 4.5 1.1c.3.1.5.9.5 1.8v3c0 .6-.4 1-1 1h-2m0 0c0 1.1-.9 2-2 2s-2-.9-2-2m-8 0c0 1.1-.9 2-2 2s-2-.9-2-2" />
                          </svg>
                        )
                      },
                      { 
                        id: "left", 
                        label: "LEFT SIDE", 
                        icon: (
                          <svg className="w-6 h-6 mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2 13h20M4 13V9a2 2 0 012-2h12a2 2 0 012 2v4M5 17a2 2 0 100-4 2 2 0 000 4zm14 0a2 2 0 100-4 2 2 0 000 4z" />
                          </svg>
                        )
                      },
                      { 
                        id: "right", 
                        label: "RIGHT SIDE", 
                        icon: (
                          <svg className="w-6 h-6 mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2 13h20M4 13V9a2 2 0 012-2h12a2 2 0 012 2v4M5 17a2 2 0 100-4 2 2 0 000 4zm14 0a2 2 0 100-4 2 2 0 000 4z" />
                          </svg>
                        )
                      },
                      { 
                        id: "interior", 
                        label: "INTERIOR", 
                        icon: (
                          <svg className="w-6 h-6 mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 22a10 10 0 100-20 10 10 0 000 20zm0-18v16M4 12h16" />
                          </svg>
                        )
                      }
                    ].map((btn) => (
                      <button
                        key={btn.id}
                        type="button"
                        onClick={() => document.getElementById("file-upload")?.click()}
                        className="flex flex-col items-center justify-center p-3 rounded-2xl border border-surface-variant hover:border-primary hover:bg-surface transition-all text-center min-h-[90px] w-full"
                      >
                        <div className="text-on-surface-variant hover:text-primary mb-1">
                          {btn.icon}
                        </div>
                        <span className="text-[8px] font-bold tracking-wider text-on-surface-variant">{btn.label}</span>
                      </button>
                    ))}
                  </div>

                </div>
              )}
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex justify-between border-t border-surface-variant pt-4">
          <Button
            variant="outline"
            onClick={prevStep}
            disabled={isSubmitting || currentStep === 1}
            type="button"
            className="border-surface-variant text-on-surface hover:bg-surface-container text-base px-6 py-6 font-bold rounded-xl"
          >
            <ChevronLeft className="w-5 h-5 mr-1" /> Back
          </Button>

          {currentStep < STEPS.length ? (
            <Button
              onClick={nextStep}
              className="bg-primary text-white text-base px-6 py-6 font-bold hover:bg-emerald-800 rounded-xl"
              type="button"
            >
              Next <ChevronRight className="w-5 h-5 ml-1" />
            </Button>
          ) : (
            <Button
              onClick={form.handleSubmit(onSubmit as any)}
              disabled={isSubmitting}
              className="bg-primary text-white text-base px-6 py-6 font-bold hover:bg-emerald-800 rounded-xl min-w-[150px]"
              type="button"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-1.5">
                  <svg
                    className="animate-spin h-3.5 w-3.5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  Predicting...
                </span>
              ) : (
                <span>Generate Valuation</span>
              )}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
