"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { User } from "@/types";
import { authApi } from "@/lib/api/auth";
import { setApiAuthToken, setOnUnauthorized } from "@/lib/api/client";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "afds_access_token";
const REFRESH_KEY = "afds_refresh_token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleLogout = useCallback(async () => {
    const refreshToken = typeof window !== "undefined" ? sessionStorage.getItem(REFRESH_KEY) : null;
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch {}
    }

    if (typeof window !== "undefined") {
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(REFRESH_KEY);
    }
    setApiAuthToken(null);
    setToken(null);
    setUser(null);
    setError(null);
    router.push("/login");
  }, [router]);

  // Hook up 401 callback from client
  useEffect(() => {
    setOnUnauthorized(() => {
      handleLogout();
    });
  }, [handleLogout]);

  // Restore session on mount
  useEffect(() => {
    async function restoreSession() {
      if (typeof window === "undefined") {
        setIsLoading(false);
        return;
      }

      const storedToken = sessionStorage.getItem(TOKEN_KEY);
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      setApiAuthToken(storedToken);
      setToken(storedToken);

      try {
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
      } catch {
        // Attempt token refresh if available
        const refreshToken = sessionStorage.getItem(REFRESH_KEY);
        if (refreshToken) {
          try {
            const tokenRes = await authApi.refreshToken(refreshToken);
            sessionStorage.setItem(TOKEN_KEY, tokenRes.access_token);
            sessionStorage.setItem(REFRESH_KEY, tokenRes.refresh_token);
            setApiAuthToken(tokenRes.access_token);
            setToken(tokenRes.access_token);
            const refreshedUser = await authApi.getCurrentUser();
            setUser(refreshedUser);
          } catch {
            await handleLogout();
          }
        } else {
          await handleLogout();
        }
      } finally {
        setIsLoading(false);
      }
    }

    restoreSession();
  }, [handleLogout]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const tokenRes = await authApi.login(email, password);
      sessionStorage.setItem(TOKEN_KEY, tokenRes.access_token);
      sessionStorage.setItem(REFRESH_KEY, tokenRes.refresh_token);
      setApiAuthToken(tokenRes.access_token);
      setToken(tokenRes.access_token);

      const currentUser = await authApi.getCurrentUser();
      setUser(currentUser);
      router.push("/overview");
    } catch (err: any) {
      setError(err?.detail || err?.message || "Login failed. Please check credentials.");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await authApi.register(email, password);
      // Auto login after registration
      await login(email, password);
    } catch (err: any) {
      setError(err?.detail || err?.message || "Registration failed.");
      setIsLoading(false);
      throw err;
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        error,
        login,
        register,
        logout: handleLogout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
