/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        surface: {
          DEFAULT: "var(--color-surface)",
          accent: "var(--color-surface-accent)",
        },
        text: {
          primary: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
        },
        primary: {
          DEFAULT: "var(--color-primary)",
          hover: "var(--color-primary-hover)",
        },
        border: {
          DEFAULT: "var(--color-border)",
        },
        icon: {
          DEFAULT: "var(--color-icon)",
        },
        active: {
          DEFAULT: "var(--color-active)",
        },
        // Direct palette aliases
        brand: {
          bg: "#EDF1D6",
          surface: "#FFFFFF",
          accent: "#9DC08B",
          dark: "#40513B",
          green: "#609966",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
