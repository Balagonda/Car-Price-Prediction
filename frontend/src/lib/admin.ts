import { apiClient } from "./api-client";
import type { APIResponse } from "@/types";

export interface HealthStatus {
  api_status: string;
  db_status: string;
  cloudinary_status: string;
  api_latency_ms: number;
  active_model_version: string | null;
  uptime_seconds: number;
}

export interface ChartData {
  name: string;
  count: number;
}

export interface AnalyticsKPIs {
  total_users: number;
  active_users: number;
  total_predictions: number;
  predictions_today: number;
  success_rate_percent: number;
  most_searched_brands: ChartData[];
  city_breakdowns: ChartData[];
}

export interface AnalyticsResponse {
  kpis: AnalyticsKPIs;
  health: HealthStatus;
}

export interface ActivityLogResponse {
  id: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  ip_address: string | null;
  extra_data: string | null;
  user_id: string | null;
  created_at: string;
}

export interface DatasetUploadResponse {
  dataset_id: string;
  name: string;
  version: string;
  row_count: number;
  column_count: number;
  duplicate_rows_removed: number;
  invalid_rows_removed: number;
  message: string;
}

export interface ModelVersionResponse {
  id: string;
  version_tag: string;
  status: string;
  r2_score: number | null;
  rmse: number | null;
  mae: number | null;
  cross_val_score: number | null;
  training_time_seconds: number | null;
  training_samples: number | null;
  created_at: string;
}

export interface MLModelResponse {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  versions: ModelVersionResponse[];
  created_at: string;
}

export async function getAnalytics(): Promise<AnalyticsResponse> {
  const { data } = await apiClient.get<APIResponse<AnalyticsResponse>>("/api/v1/admin/analytics");
  return data.data;
}

export async function getActivityLogs(): Promise<ActivityLogResponse[]> {
  const { data } = await apiClient.get<APIResponse<ActivityLogResponse[]>>("/api/v1/admin/activity");
  return data.data;
}

export async function uploadDataset(file: File, mode: string, version: string): Promise<DatasetUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("mode", mode);
  formData.append("version", version);

  const { data } = await apiClient.post<APIResponse<DatasetUploadResponse>>("/api/v1/admin/datasets/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data.data;
}

export async function getModels(): Promise<MLModelResponse[]> {
  const { data } = await apiClient.get<APIResponse<MLModelResponse[]>>("/api/v1/admin/models");
  return data.data;
}

export async function trainModel(dataset_path: string, version_tag: string): Promise<{version_tag: string, status: string}> {
  const { data } = await apiClient.post<APIResponse<{version_tag: string, status: string}>>("/api/v1/admin/models/train", {
    dataset_path,
    version_tag
  });
  return data.data;
}

export async function activateModel(version_id: string): Promise<ModelVersionResponse> {
  const { data } = await apiClient.post<APIResponse<ModelVersionResponse>>(`/api/v1/admin/models/${version_id}/activate`);
  return data.data;
}
