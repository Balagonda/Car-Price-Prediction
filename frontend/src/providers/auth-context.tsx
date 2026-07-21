"use client";

/**
 * AutoWorth AI — Auth Context & Provider
 *
 * Global authentication state manager using React Context + TanStack Query.
 *
 * Provides:
 *  - user: Current authenticated user (null if unauthenticated)
 *  - isLoading: True while hydrating from /auth/me on mount
 *  - isAuthenticated: True when user is not null
 *  - isAdmin: True when user role is "admin"
 *  - isVerified: True when user.is_verified
 *  - login(data): Authenticate and store access token
 *  - register(data): Create account
 *  - googleLogin(idToken): OAuth login
 *  - logout(): Clear token and session
 *  - updateProfile(data): Patch current user
 */

import {
  createContext,
  useCallback,
  useContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getCurrentUser,
  loginUser,
  registerUser,
  googleLogin,
  logoutUser,
  updateProfile,
  type LoginRequest,
  type RegisterRequest,
  type UpdateProfileRequest,
} from "@/lib/auth";
import type { User } from "@/types";
import { getAPIError } from "@/lib/api-client";

// ──────────────────────────────────────────────
// Context Types
// ──────────────────────────────────────────────
interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isVerified: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<{ verification_token?: string }>;
  googleLogin: (idToken: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: UpdateProfileRequest) => Promise<void>;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ──────────────────────────────────────────────
// Provider
// ──────────────────────────────────────────────
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  // ── Token helpers ────────────────────────────
  const getToken = () =>
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const setToken = (token: string) =>
    typeof window !== "undefined" && localStorage.setItem("access_token", token);

  const clearToken = () =>
    typeof window !== "undefined" && localStorage.removeItem("access_token");

  // ── Hydrate user from /auth/me on mount ──────
  const {
    data: user = null,
    isLoading,
  } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentUser,
    enabled: !!getToken(),  // Only run if we have a token
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  // ── Login mutation ───────────────────────────
  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: (data) => {
      setToken(data.access_token);
      queryClient.setQueryData(["auth", "me"], data.user);
      setError(null);
    },
    onError: (err) => {
      setError(getAPIError(err).message);
    },
  });

  // ── Register mutation ─────────────────────────
  const registerMutation = useMutation({
    mutationFn: registerUser,
    onSuccess: () => setError(null),
    onError: (err) => {
      setError(getAPIError(err).message);
    },
  });

  // ── Google login mutation ────────────────────
  const googleLoginMutation = useMutation({
    mutationFn: (idToken: string) => googleLogin(idToken),
    onSuccess: (data) => {
      setToken(data.access_token);
      queryClient.setQueryData(["auth", "me"], data.user);
      setError(null);
    },
    onError: (err) => {
      setError(getAPIError(err).message);
    },
  });

  // ── Logout mutation ──────────────────────────
  const logoutMutation = useMutation({
    mutationFn: logoutUser,
    onSettled: () => {
      clearToken();
      queryClient.setQueryData(["auth", "me"], null);
      queryClient.clear();
    },
  });

  // ── Update profile mutation ──────────────────
  const updateProfileMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(["auth", "me"], updatedUser);
      setError(null);
    },
    onError: (err) => {
      setError(getAPIError(err).message);
    },
  });

  // ── Public API ───────────────────────────────
  const login = useCallback(
    async (data: LoginRequest) => {
      await loginMutation.mutateAsync(data);
    },
    [loginMutation]
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      const result = await registerMutation.mutateAsync(data);
      return { verification_token: result?.verification_token };
    },
    [registerMutation]
  );

  const googleLoginHandler = useCallback(
    async (idToken: string) => {
      await googleLoginMutation.mutateAsync(idToken);
    },
    [googleLoginMutation]
  );

  const logout = useCallback(async () => {
    await logoutMutation.mutateAsync();
  }, [logoutMutation]);

  const updateProfileHandler = useCallback(
    async (data: UpdateProfileRequest) => {
      await updateProfileMutation.mutateAsync(data);
    },
    [updateProfileMutation]
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user: user ?? null,
      isLoading,
      isAuthenticated: !!user,
      isAdmin: user?.role?.name === "admin",
      isVerified: user?.is_verified ?? false,
      login,
      register,
      googleLogin: googleLoginHandler,
      logout,
      updateProfile: updateProfileHandler,
      error,
      clearError,
    }),
    [
      user,
      isLoading,
      login,
      register,
      googleLoginHandler,
      logout,
      updateProfileHandler,
      error,
      clearError,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ──────────────────────────────────────────────
// Hook
// ──────────────────────────────────────────────
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return ctx;
}
