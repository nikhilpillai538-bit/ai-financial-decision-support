import { apiClient } from "./client";
import { TokenResponse, User } from "@/types";

export const authApi = {
  async register(email: string, password: string):Promise<User> {
    return apiClient<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    return apiClient<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return apiClient<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },

  async getCurrentUser(): Promise<User> {
    return apiClient<User>("/auth/me");
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },
};
