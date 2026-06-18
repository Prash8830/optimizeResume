/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0a0b0f',
        surface: '#12131c',
        elevated: '#1a1b27',
        border: '#1e1f2e',
        accent: '#e05252',
        'accent-hover': '#c94444',
        primary: '#f0f2ff',
        secondary: '#8a8eb8',
        muted: '#4e5270',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
