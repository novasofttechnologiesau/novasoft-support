/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        nova: {
          bg: "#0a0b0d",
          surface: "#131417",
          card: "#1a1c20",
          border: "#26282e",
          text: "#e6e7ea",
          muted: "#8b8f98",
          accent: "#3b82f6",
          accentDark: "#2563eb",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
