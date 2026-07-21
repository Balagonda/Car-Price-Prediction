/**
 * AutoWorth AI — TypeScript Type Definitions
 *
 * Shared types matching backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/*.py
 */

// ──────────────────────────────────────────────
// API Response Envelope
// ──────────────────────────────────────────────
export interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ──────────────────────────────────────────────
// Auth & User
// ──────────────────────────────────────────────
export type UserRole = "guest" | "user" | "admin";

export interface Role {
  id: number;
  name: UserRole;
}

export interface User {
  id: string; // UUID
  first_name: string;
  last_name: string;
  email: string;
  profile_image_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  oauth_provider: string | null;
  role: Role;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
}

// ──────────────────────────────────────────────
// Vehicle Taxonomy
// ──────────────────────────────────────────────
export type FuelType =
  | "Petrol"
  | "Diesel"
  | "CNG"
  | "LPG"
  | "Electric"
  | "Hybrid";

export type TransmissionType = "Manual" | "Automatic" | "AMT" | "DCT" | "CVT";

export type OwnerType =
  | "First Owner"
  | "Second Owner"
  | "Third Owner"
  | "Fourth & Above Owner"
  | "Test Drive Car";

export type VehicleCategory =
  | "Hatchback"
  | "Sedan"
  | "SUV"
  | "MUV"
  | "Luxury"
  | "Electric"
  | "Commercial"
  | "Coupe"
  | "Convertible";

export type InsuranceStatus =
  | "Comprehensive"
  | "Third Party"
  | "Zero Depreciation"
  | "Expired"
  | "Not Available";

export interface Brand {
  id: number;
  name: string;
  logo_url: string | null;
}

export interface CarModel {
  id: number;
  name: string;
  brand_id: number;
}

export interface Variant {
  id: number;
  name: string;
  car_model_id: number;
}

export interface City {
  id: number;
  name: string;
  state: string;
}

// ──────────────────────────────────────────────
// Predictions
// ──────────────────────────────────────────────
export type FairPriceStatus = "Below Market" | "Fair" | "Above Market";

export interface ShapFeature {
  feature_name: string;
  feature_value: string | null;
  shap_value: number;
  impact_direction: "positive" | "negative";
  rank: number;
  human_readable_impact: string | null;
}

export interface Recommendation {
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  display_order: number;
}

export interface Prediction {
  id: string; // UUID
  estimated_price: number;
  confidence_score: number;
  price_range_min: number;
  price_range_max: number;
  fair_price_status: FairPriceStatus;
  depreciation_percent: number | null;
  showroom_price: number | null;
  cv_damage_detected: boolean | null;
  cv_damage_severity: string | null;
  cv_repair_cost_estimate: number | null;
  shap_results: ShapFeature[];
  recommendations: Recommendation[];
  is_pdf_generated: boolean;
  pdf_url: string | null;
  created_at: string;
}

export interface PredictionRequest {
  brand_id: number;
  car_model_id: number;
  variant_id?: number;
  city_id?: number;
  manufacturing_year: number;
  fuel_type: FuelType;
  transmission: TransmissionType;
  owner_type: OwnerType;
  seller_type: string;
  category: VehicleCategory;
  kilometers_driven: number;
  engine_cc?: number;
  mileage_kmpl?: number;
  seats?: number;
  insurance_status: InsuranceStatus;
}
