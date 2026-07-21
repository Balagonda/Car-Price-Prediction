/**
 * AutoWorth AI — Auth API Functions
 *
 * Typed wrappers around apiClient for all authentication endpoints.
 * These functions are consumed by React Query mutations/queries in the auth context.
 */

import { apiClient } from "@/lib/api-client";
import type {
  APIResponse,
  TokenResponse,
  User,
} from "@/types";

// ──────────────────────────────────────────────
// Request Types
// ──────────────────────────────────────────────
export interface RegisterRequest {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface GoogleLoginRequest {
  id_token: string;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  profile_image_url?: string;
}

// ──────────────────────────────────────────────
// Register
// ──────────────────────────────────────────────
export async function registerUser(data: RegisterRequest): Promise<{
  user: User;
  verification_token?: string; // Only in DEBUG mode
}> {
  const res = await apiClient.post<
    APIResponse<{ user: User; verification_token?: string }>
  >("/auth/register", data);
  return res.data.data!;
}

// ──────────────────────────────────────────────
// Login
// ──────────────────────────────────────────────
export async function loginUser(data: LoginRequest): Promise<TokenResponse> {
  const res = await apiClient.post<APIResponse<TokenResponse>>(
    "/auth/login",
    data
  );
  return res.data.data!;
}

// ──────────────────────────────────────────────
// Google OAuth Login
// ──────────────────────────────────────────────
export async function googleLogin(id_token: string): Promise<TokenResponse> {
  const res = await apiClient.post<APIResponse<TokenResponse>>(
    "/auth/google-login",
    { id_token }
  );
  return res.data.data!;
}

// ──────────────────────────────────────────────
// Refresh Token
// ──────────────────────────────────────────────
export async function refreshToken(): Promise<TokenResponse> {
  const res = await apiClient.post<APIResponse<TokenResponse>>(
    "/auth/refresh"
  );
  return res.data.data!;
}

// ──────────────────────────────────────────────
// Logout
// ──────────────────────────────────────────────
export async function logoutUser(): Promise<void> {
  await apiClient.post("/auth/logout");
}

// ──────────────────────────────────────────────
// Get Current User
// ──────────────────────────────────────────────
export async function getCurrentUser(): Promise<User> {
  const res = await apiClient.get<APIResponse<User>>("/auth/me");
  return res.data.data!;
}

// ──────────────────────────────────────────────
// Update Profile
// ──────────────────────────────────────────────
export async function updateProfile(data: UpdateProfileRequest): Promise<User> {
  const res = await apiClient.patch<APIResponse<User>>("/auth/me", data);
  return res.data.data!;
}

// ──────────────────────────────────────────────
// Verify Email
// ──────────────────────────────────────────────
export async function verifyEmail(token: string): Promise<User> {
  const res = await apiClient.get<APIResponse<User>>(
    `/auth/verify-email?token=${token}`
  );
  return res.data.data!;
}
