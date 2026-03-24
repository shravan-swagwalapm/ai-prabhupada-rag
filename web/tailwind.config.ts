import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          50: '#fdf8e8', 100: '#f9edd0', 200: '#f0d89a',
          300: '#e4c064', 400: '#dbb85a', 500: '#c9a84c',
          600: '#8B7332', 700: '#6a5828', 800: '#4a3e1c',
          900: '#2e2916', DEFAULT: '#c9a84c',
        },
        vermillion: {
          50: '#fef0ec', 300: '#e07050', 500: '#c24d2c',
          700: '#8a3620', DEFAULT: '#c24d2c',
        },
        tulsi: {
          50: '#edf5eb', 500: '#4a8c3f', 700: '#356b2d',
          DEFAULT: '#4a8c3f',
        },
        sanctum: '#FAF6EF',
        'temple-dark': '#F5EDE0',
        altar: '#FFFFFF',
        card: { DEFAULT: '#FFFFFF', hover: '#FBF7F0' },
        'krishna-blue': { DEFAULT: '#1A3A6B', light: '#2A5298' },
      },
      fontFamily: {
        serif: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['Georgia', 'serif'],
      },
    },
  },
  plugins: [],
};
export default config;
