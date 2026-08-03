/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        // — Brand (Phase 3 spec) —
        'sc-navy': '#1F4E79',          // Primary dark
        'sc-navy-deep': '#173A5C',     // Sidebar gradient floor
        'sc-navy-900': '#102A45',      // Deepest ink-navy
        'sc-royal': '#2E75B6',         // Primary
        'sc-royal-light': '#5B9BD5',   // Primary light
        'sc-royal-50': '#EAF2FB',      // Tint — active / hover surfaces
        // — Neutrals —
        'sc-bg': '#F3F6FA',            // Page background
        'sc-bg-soft': '#EDF1F7',       // Recessed panels
        'sc-surface': '#FFFFFF',
        'sc-border': '#E5EAF1',        // Hairline
        'sc-border-strong': '#D2DAE6',
        'sc-text': '#1D2A3A',
        'sc-text-soft': '#475467',
        'sc-text-muted': '#6B7689',
        // — Semantic —
        'sc-success': '#15803D',
        'sc-warning': '#B45309',
        'sc-danger': '#C2362F',
        'sc-info': '#0E7AB5',
        // — Semantic tints (nền mờ nhã — thay palette Tailwind thô bg-red-50…) —
        'sc-success-50': '#E7F4EC',
        'sc-warning-50': '#FCF1E4',
        'sc-danger-50': '#FBE9E8',
        'sc-info-50': '#E6F2FA',
        'sc-critical-50': '#FBE9E8',
        // — Severity (Alert) —
        'sc-critical': '#C2362F',
        'sc-high': '#C2410C',
        'sc-medium': '#B45309',
        'sc-low': '#0E7AB5',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Roboto Mono"', 'monospace'],
      },
      fontSize: {
        'xs': ['11px', '16px'],
        'sm': ['13px', '20px'],
        'base': ['14px', '22px'],
        'lg': ['16px', '24px'],
        'xl': ['20px', '28px'],
        '2xl': ['24px', '32px'],
        '3xl': ['32px', '40px'],
        'kpi': ['34px', '40px'],
      },
      spacing: {
        '1': '4px', '2': '8px', '3': '12px', '4': '16px', '5': '20px',
        '6': '24px', '8': '32px', '10': '40px', '12': '48px', '16': '64px',
        '18': '72px',
      },
      borderRadius: {
        'sm': '5px', 'md': '7px', 'lg': '10px', 'xl': '14px', '2xl': '18px',
      },
      boxShadow: {
        'sc-xs': '0 1px 2px 0 rgba(16, 42, 69, 0.06)',
        'sc-sm': '0 1px 3px 0 rgba(16, 42, 69, 0.08), 0 1px 2px -1px rgba(16, 42, 69, 0.05)',
        'sc-md': '0 6px 16px -4px rgba(16, 42, 69, 0.12), 0 2px 6px -2px rgba(16, 42, 69, 0.07)',
        'sc-lg': '0 16px 32px -8px rgba(16, 42, 69, 0.16), 0 6px 14px -6px rgba(16, 42, 69, 0.09)',
        'sc-xl': '0 28px 56px -14px rgba(16, 42, 69, 0.24)',
        'sc-focus': '0 0 0 3px rgba(46, 117, 182, 0.18)',
        'sc-glow': '0 0 0 1px rgba(46, 117, 182, 0.25), 0 8px 24px -8px rgba(46, 117, 182, 0.35)',
      },
      transitionTimingFunction: {
        'sc': 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
      keyframes: {
        'sc-fade-up': {
          '0%':   { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'sc-fade-in': {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'sc-scale-in': {
          '0%':   { opacity: '0', transform: 'scale(0.97)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'sc-pulse-ring': {
          '0%':   { transform: 'scale(0.8)', opacity: '0.55' },
          '70%':  { transform: 'scale(2.2)', opacity: '0' },
          '100%': { transform: 'scale(2.2)', opacity: '0' },
        },
        'sc-shimmer': {
          '0%':   { backgroundPosition: '-360px 0' },
          '100%': { backgroundPosition: '360px 0' },
        },
      },
      animation: {
        'sc-fade-up': 'sc-fade-up 0.5s cubic-bezier(0.22, 1, 0.36, 1) both',
        'sc-fade-in': 'sc-fade-in 0.4s ease both',
        'sc-scale-in': 'sc-scale-in 0.22s cubic-bezier(0.22, 1, 0.36, 1) both',
        'sc-pulse-ring': 'sc-pulse-ring 2s cubic-bezier(0.22, 1, 0.36, 1) infinite',
        'sc-shimmer': 'sc-shimmer 1.4s linear infinite',
      },
    },
  },
  plugins: [],
}
