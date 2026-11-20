import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/auth/:path*",
        destination: `${BACKEND_URL}/auth/:path*`,
      },
      {
        source: "/transactions/:path*",
        destination: `${BACKEND_URL}/transactions/:path*`,
      },
      {
        source: "/portfolios/:path*",
        destination: `${BACKEND_URL}/portfolios/:path*`,
      },
      {
        source: "/assets/:path*",
        destination: `${BACKEND_URL}/assets/:path*`,
      },
      {
        source: "/investment-goals/:path*",
        destination: `${BACKEND_URL}/investment-goals/:path*`,
      },
      {
        source: "/financial-profile/:path*",
        destination: `${BACKEND_URL}/financial-profile/:path*`,
      },
      {
        source: "/financial-analysis/:path*",
        destination: `${BACKEND_URL}/financial-analysis/:path*`,
      },
      {
        source: "/market-data/:path*",
        destination: `${BACKEND_URL}/market-data/:path*`,
      },
      {
        source: "/calculators/:path*",
        destination: `${BACKEND_URL}/calculators/:path*`,
      },
      {
        source: "/ai/:path*",
        destination: `${BACKEND_URL}/ai/:path*`,
      },
      {
        source: "/news/:path*",
        destination: `${BACKEND_URL}/news/:path*`,
      },
      {
        source: "/portfolio/:path*",
        destination: `${BACKEND_URL}/portfolio/:path*`,
      },
      {
        source: "/goals/:path*",
        destination: `${BACKEND_URL}/goals/:path*`,
      },
    ];
  },
};

export default nextConfig;
