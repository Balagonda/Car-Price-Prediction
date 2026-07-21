"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormDescription,
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
import { Camera, Car, MapPin, ChevronRight, ChevronLeft, CheckCircle2, AlertCircle } from "lucide-react";
import axios from "axios";

const predictionSchema = z.object({
  brand_id: z.coerce.number().min(1, "Brand is required"),
  car_model_id: z.coerce.number().min(1, "Model is required"),
  manufacturing_year: z.coerce.number().min(1990).max(2025),
  fuel_type: z.enum(["petrol", "diesel", "cng", "lpg", "electric"]),
  transmission: z.enum(["manual", "automatic"]),
  owner_type: z.enum(["first", "second", "third", "fourth_and_above"]),
  seller_type: z.enum(["individual", "dealer", "trustmark_dealer"]),
  category: z.enum(["hatchback", "sedan", "suv", "muv", "luxury", "other"]),
  kilometers_driven: z.coerce.number().min(0).max(1000000),
  engine_cc: z.coerce.number().min(50).max(10000).optional(),
  mileage_kmpl: z.coerce.number().min(0).max(100).optional(),
  seats: z.coerce.number().min(1).max(14).optional(),
  max_power_bhp: z.coerce.number().min(0).max(2000).optional(),
  insurance_status: z.enum(["comprehensive", "third_party", "zero_depreciation", "expired", "not_available"]),
});

type PredictionFormValues = z.infer<typeof predictionSchema>;

const STEPS = [
  { id: 1, title: "Core Specs", description: "Basic vehicle details" },
  { id: 2, title: "Condition", description: "Mileage & Ownership" },
  { id: 3, title: "Images", description: "Optional damage scan" },
];

export default function PredictionWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<PredictionFormValues>({
    resolver: zodResolver(predictionSchema),
    defaultValues: {
      brand_id: 1, 
      car_model_id: 1,
      manufacturing_year: 2018,
      fuel_type: "petrol",
      transmission: "manual",
      owner_type: "first",
      seller_type: "individual",
      category: "sedan",
      kilometers_driven: 50000,
      engine_cc: 1200,
      mileage_kmpl: 18.5,
      seats: 5,
      max_power_bhp: 85,
      insurance_status: "comprehensive",
    },
  });

  const nextStep = async () => {
    let fieldsToValidate: any[] = [];
    if (currentStep === 1) {
        fieldsToValidate = ['brand_id', 'car_model_id', 'manufacturing_year', 'fuel_type', 'transmission', 'category'];
    } else if (currentStep === 2) {
        fieldsToValidate = ['kilometers_driven', 'owner_type', 'seller_type', 'insurance_status', 'engine_cc', 'seats'];
    }
    
    const isValid = await form.trigger(fieldsToValidate);
    if (isValid) {
        setCurrentStep((prev) => Math.min(prev + 1, STEPS.length));
    }
  };

  const prevStep = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const onSubmit = async (data: PredictionFormValues) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const token = localStorage.getItem("access_token");
      const res = await axios.post("http://localhost:8000/api/v1/predictions", data, {
          headers: {
              Authorization: `Bearer ${token}`
          }
      });
      
      const predictionId = res.data.data.id;
      router.push(`/dashboard/prediction/results/${predictionId}`);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || "An error occurred during prediction.");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">AI Vehicle Valuation</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">Get an instant, data-driven price estimate for your car.</p>
      </div>

      <div className="mb-8">
        <Progress value={(currentStep / STEPS.length) * 100} className="h-2" />
        <div className="flex justify-between mt-4">
          {STEPS.map((step) => (
            <div key={step.id} className={`flex flex-col items-center text-sm ${currentStep >= step.id ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 font-semibold ${currentStep >= step.id ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-gray-100 dark:bg-gray-800'}`}>
                {currentStep > step.id ? <CheckCircle2 className="w-5 h-5" /> : step.id}
              </div>
              <span className="font-medium">{step.title}</span>
            </div>
          ))}
        </div>
      </div>

      <Card className="border-0 shadow-lg bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle>{STEPS[currentStep - 1].title}</CardTitle>
          <CardDescription>{STEPS[currentStep - 1].description}</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              
              {/* STEP 1: Core Specs */}
              {currentStep === 1 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <FormField
                    control={form.control}
                    name="brand_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Brand</FormLabel>
                        <Select onValueChange={(val) => field.onChange(parseInt(val))} defaultValue={field.value.toString()}>
                          <FormControl>
                            <SelectTrigger><SelectValue placeholder="Select Brand" /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="1">Maruti Suzuki</SelectItem>
                            <SelectItem value="2">Hyundai</SelectItem>
                            <SelectItem value="3">Honda</SelectItem>
                            <SelectItem value="4">Toyota</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="car_model_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Model</FormLabel>
                        <Select onValueChange={(val) => field.onChange(parseInt(val))} defaultValue={field.value.toString()}>
                          <FormControl>
                            <SelectTrigger><SelectValue placeholder="Select Model" /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="1">Swift</SelectItem>
                            <SelectItem value="2">i20</SelectItem>
                            <SelectItem value="3">City</SelectItem>
                            <SelectItem value="4">Fortuner</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                   <FormField
                    control={form.control}
                    name="manufacturing_year"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Manufacturing Year</FormLabel>
                        <FormControl>
                          <Input type="number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="category"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Body Type</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger><SelectValue placeholder="Select Body Type" /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="hatchback">Hatchback</SelectItem>
                            <SelectItem value="sedan">Sedan</SelectItem>
                            <SelectItem value="suv">SUV</SelectItem>
                            <SelectItem value="muv">MUV</SelectItem>
                            <SelectItem value="luxury">Luxury</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="fuel_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Fuel Type</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger><SelectValue placeholder="Select Fuel Type" /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="petrol">Petrol</SelectItem>
                            <SelectItem value="diesel">Diesel</SelectItem>
                            <SelectItem value="cng">CNG</SelectItem>
                            <SelectItem value="electric">Electric</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                   <FormField
                    control={form.control}
                    name="transmission"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Transmission</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger><SelectValue placeholder="Select Transmission" /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="manual">Manual</SelectItem>
                            <SelectItem value="automatic">Automatic</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              )}

              {/* STEP 2: Condition & Metrics */}
              {currentStep === 2 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-right-8 duration-500">
                  <FormField
                    control={form.control}
                    name="kilometers_driven"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Kilometers Driven</FormLabel>
                        <FormControl>
                          <Input type="number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="owner_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Ownership</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger><SelectValue placeholder="Select Ownership" /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="first">1st Owner</SelectItem>
                            <SelectItem value="second">2nd Owner</SelectItem>
                            <SelectItem value="third">3rd Owner</SelectItem>
                            <SelectItem value="fourth_and_above">4th+ Owner</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="seller_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Seller Type</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger><SelectValue placeholder="Select Seller" /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="individual">Individual</SelectItem>
                            <SelectItem value="dealer">Dealer</SelectItem>
                            <SelectItem value="trustmark_dealer">Trustmark Dealer</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                   <FormField
                    control={form.control}
                    name="insurance_status"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Insurance Status</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger><SelectValue placeholder="Select Insurance" /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="comprehensive">Comprehensive</SelectItem>
                            <SelectItem value="third_party">Third Party</SelectItem>
                            <SelectItem value="zero_depreciation">Zero Dep</SelectItem>
                            <SelectItem value="expired">Expired</SelectItem>
                            <SelectItem value="not_available">Not Available</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                   <FormField
                    control={form.control}
                    name="engine_cc"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Engine (CC)</FormLabel>
                        <FormControl>
                          <Input type="number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                   <FormField
                    control={form.control}
                    name="seats"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Seats</FormLabel>
                        <FormControl>
                          <Input type="number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              )}

              {/* STEP 3: Images (Optional for now) */}
              {currentStep === 3 && (
                <div className="space-y-6 animate-in fade-in slide-in-from-right-8 duration-500 text-center py-10">
                  <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Camera className="w-10 h-10" />
                  </div>
                  <h3 className="text-xl font-medium">Upload Vehicle Photos</h3>
                  <p className="text-gray-500">Our CV Engine can detect external damage and adjust the valuation automatically.</p>
                  
                  <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-8 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Drag and drop images here, or click to browse</p>
                      <p className="text-xs text-gray-400 mt-2">(Supports JPG, PNG up to 5MB. Max 3 images: Front, Rear, Interior)</p>
                  </div>
                  <p className="text-sm text-gray-400 italic">Note: Image upload is mocked for this phase.</p>
                </div>
              )}

            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex justify-between border-t border-gray-100 dark:border-gray-800 pt-6">
          <Button 
            variant="outline" 
            onClick={prevStep} 
            disabled={currentStep === 1 || isSubmitting}
            type="button"
          >
            <ChevronLeft className="w-4 h-4 mr-2" /> Back
          </Button>
          
          {currentStep < STEPS.length ? (
            <Button onClick={nextStep} className="bg-blue-600 hover:bg-blue-700 text-white" type="button">
              Next <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={form.handleSubmit(onSubmit)} disabled={isSubmitting} className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white min-w-[140px]" type="button">
              {isSubmitting ? (
                  <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
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
