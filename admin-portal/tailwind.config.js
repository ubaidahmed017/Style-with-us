/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Brand palette (matches the mobile app).
        brand: {
          50: '#efeefe',
          100: '#dcd9ff',
          300: '#9d97ff',
          400: '#847dff',
          500: '#6c63ff',
          600: '#5a51e6',
          700: '#4a42d4',
        },
        accent: '#ff6584',
        // Dark surfaces.
        ink: {
          900: '#0f0f23',
          800: '#16162b',
          700: '#1a1a2e',
          600: '#1f2b47',
          500: '#2a2a45',
        },
      },
      boxShadow: {
        glow: '0 10px 30px -10px rgba(108,99,255,0.5)',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #6c63ff 0%, #9d4edd 100%)',
      },
    },
  },
  plugins: [],
}
