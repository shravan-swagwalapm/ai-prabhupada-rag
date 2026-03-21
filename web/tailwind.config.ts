import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          50: '#fdf8e8', 100: '#f9edd0', 200: '#f0d89a',
          300: '#e4c064', 400: '#dbb85a', 500: '#c9a84c',
          600: '#a08940', 700: '#7a6a32', 800: '#544a24',
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
        sanctum: '#060403',
        'temple-dark': '#0c0908',
        altar: '#161009',
        card: { DEFAULT: '#1c150e', hover: '#231a12' },
      },
      fontFamily: {
        serif: ['Cormorant Garamond', 'Georgia', 'Cambria', 'Times New Roman', 'serif'],
        display: ['Cinzel', 'serif'],
      },
    },
  },
  plugins: [],
};
export default config;
