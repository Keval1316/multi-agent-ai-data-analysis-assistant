/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
        display: ['Outfit', '"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
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
        brand: {
          bg: "#FFFBE9",
          surface: "#FFFFFF",
          accent: "#CEAB93",
          lightaccent: "#E3CAA5",
          dark: "#3E2723",
          primary: "#AD8B73",
          primaryDark: "#8C6542",
        }
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(62, 39, 35, 0.06)',
        'glass-hover': '0 20px 40px 0 rgba(62, 39, 35, 0.10)',
        'card': '0 4px 20px -2px rgba(62, 39, 35, 0.05)',
        'glow': '0 0 25px -5px rgba(173, 139, 115, 0.4)',
      },
      backgroundImage: {
        'grid-pattern': 'radial-gradient(circle, rgba(206, 171, 147, 0.25) 1px, transparent 1px)',
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
