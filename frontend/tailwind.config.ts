import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      colors: {
        fintech: {
          dark: "#080C14",
          base: "#0D131F",
          card: "#121927",
          surface: "#172134",
          hover: "#1D2A42",
          border: "#22314E",
          subtle: "rgba(255, 255, 255, 0.08)",
          accent: "#06B6D4",
          teal: "#14B8A6",
          emerald: "#10B981",
        },
        brand: {
          50: "#ecfeff",
          100: "#cffafe",
          200: "#a5f3fc",
          300: "#67e8f9",
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
          700: "#0e7490",
          800: "#155e75",
          900: "#164e63",
          950: "#083344",
        },
      },
      boxShadow: {
        "fintech": "0 10px 30px -10px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.2)",
        "card": "0 2px 10px 0 rgba(0, 0, 0, 0.25), 0 1px 2px -1px rgba(0, 0, 0, 0.2)",
        "elevated": "0 20px 35px -10px rgba(2, 6, 23, 0.7), 0 8px 12px -6px rgba(2, 6, 23, 0.5)",
        "glow-cyan": "0 0 25px -5px rgba(6, 182, 212, 0.25)",
        "glow-teal": "0 0 25px -5px rgba(20, 184, 166, 0.25)",
        "glow-indigo": "0 0 25px -5px rgba(99, 102, 241, 0.25)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-up": "slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "pulse-subtle": "pulseSubtle 3s ease-in-out infinite",
        "shimmer": "shimmer 2s infinite linear",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSubtle: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
