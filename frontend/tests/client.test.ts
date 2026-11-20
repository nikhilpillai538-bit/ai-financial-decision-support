import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  apiClient,
  ApiError,
  setApiAuthToken,
  setOnUnauthorized,
} from "../src/lib/api/client";

describe("Typed API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    setApiAuthToken(null);
  });

  it("injects Authorization header when token is present", async () => {
    setApiAuthToken("test-jwt-token-xyz");

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: "ok" }),
    });
    global.fetch = mockFetch;

    await apiClient("/test-endpoint");

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/test-endpoint");
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer test-jwt-token-xyz");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("appends query parameters cleanly", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: [] }),
    });
    global.fetch = mockFetch;

    await apiClient("/items", {
      params: { limit: 10, offset: 20, active: true },
    });

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("limit=10");
    expect(url).toContain("offset=20");
    expect(url).toContain("active=true");
  });

  it("transforms 401 response and triggers unauthorized callback", async () => {
    const mockCallback = vi.fn();
    setOnUnauthorized(mockCallback);

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Token expired" }),
    });

    await expect(apiClient("/protected")).rejects.toThrow(ApiError);
    expect(mockCallback).toHaveBeenCalledTimes(1);
  });

  it("handles FastAPI validation error detail array", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [
          { loc: ["body", "email"], msg: "value is not a valid email address" },
        ],
      }),
    });

    try {
      await apiClient("/auth/register", { method: "POST", body: "{}" });
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(422);
      expect(err.detail).toContain("value is not a valid email address");
    }
  });

  it("transforms network disconnect into ApiError with status 0", async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error("Failed to fetch"));

    try {
      await apiClient("/network-fail");
    } catch (err: any) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(0);
      expect(err.message).toContain("Failed to connect to backend server");
    }
  });
});
