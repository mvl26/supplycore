/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        'sc-navy': '#1F4E79',         // Primary dark
        'sc-royal': '#2E75B6',        // Primary
        'sc-royal-light': '#5B9BD5',  // Primary light
        'sc-bg': '#F7F9FC',           // Page background
        'sc-surface': '#FFFFFF',
        'sc-border': '#E5E9F0',
        'sc-text': '#1F2937',
        'sc-text-muted': '#6B7280',
        // Semantic
        'sc-success': '#16A34A',
        'sc-warning': '#F59E0B',
        'sc-danger': '#DC2626',
        'sc-info': '#0EA5E9',
        // Severity (Alert)
        'sc-critical': '#DC2626',
        'sc-high': '#EA580C',
        'sc-medium': '#F59E0B',
        'sc-low': '#0EA5E9',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"Roboto Mono"', '"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        // Phase 3 type scale
        'xs': ['11px', '16px'],
        'sm': ['13px', '20px'],
        'base': ['14px', '22px'],
        'lg': ['16px', '24px'],
        'xl': ['20px', '28px'],
        '2xl': ['24px', '32px'],
        '3xl': ['32px', '40px'],
        'kpi': ['36px', '44px'],
      },
      spacing: {
        // 4px base scale
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '5': '20px',
        '6': '24px',
        '8': '32px',
        '10': '40px',
        '12': '48px',
        '16': '64px',
      },
      borderRadius: {
        'sm': '4px',
        'md': '6px',
        'lg': '8px',
        'xl': '12px',
      },
      boxShadow: {
        'sc-sm': '0 1px 2px 0 rgba(31, 78, 121, 0.05)',
        'sc-md': '0 4px 6px -1px rgba(31, 78, 121, 0.1), 0 2px 4px -2px rgba(31, 78, 121, 0.05)',
        'sc-lg': '0 10px 15px -3px rgba(31, 78, 121, 0.1), 0 4px 6px -4px rgba(31, 78, 121, 0.05)',
      },
    },
  },
  plugins: [],
}
