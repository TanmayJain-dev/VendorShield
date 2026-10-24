import type { Config } from "tailwindcss";

export default {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        tactical: {
          dark: "#0b0f19",
          panel: "#111827",
          border: "#1f2937",
          cyan: "#06b6d4",
          amber: "#f59e0b",
          emerald: "#10b981",
          rose: "#f43f5e"
        }
      },
    },
  },
  plugins: [],
} satisfies Config;
