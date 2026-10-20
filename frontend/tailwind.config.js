/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0B0F19',
          card: '#111827',
          border: '#1F2937',
          hover: '#374151'
        },
        brand: {
          blue: '#3B82F6',
          purple: '#8B5CF6',
          cyan: '#06B6D4',
          green: '#10B981',
          red: '#EF4444',
          yellow: '#F59E0B'
        }
      }
    },
  },
  plugins: [],
}
