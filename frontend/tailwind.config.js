import animate from 'tailwindcss-animate'

/*
 * Collector's Vault theme. Semantic colours (background, card, primary...)
 * follow shadcn/ui and read the CSS variables in src/index.css.
 * The gray and blue scales are re-tuned (warm neutrals, champagne gold) so
 * screens not yet moved to the semantic colours already match the look.
 * Contrast: blue-600 #7a5d1c takes white text (6.2:1) and reads on bone
 * gray-50 (5.5:1); gray-500 #6a665c on white is 5.7:1.
 */
const gold = {
  50: '#faf6ec',
  100: '#f3e9cf',
  200: '#e6d3a3',
  300: '#d9bd7c',
  400: '#c9a45c',
  500: '#a3823a',
  600: '#7a5d1c',
  700: '#644c16',
  800: '#4e3b11',
  900: '#3d2f0f',
  950: '#261d09',
}

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Helvetica Neue"', 'Helvetica', 'Arial', 'system-ui', 'sans-serif'],
      },
      letterSpacing: {
        vault: '0.24em',
      },
      colors: {
        gray: {
          50: '#f4f1ea',
          100: '#ebe6da',
          200: '#d9d3c4',
          300: '#bfb8a8',
          400: '#8e8a7f',
          500: '#6a665c',
          600: '#57534a',
          700: '#25241f',
          800: '#121211',
          900: '#0b0b0c',
          950: '#070707',
        },
        blue: gold,
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        gold: 'hsl(var(--gold))',
        positive: 'hsl(var(--positive))',
        negative: 'hsl(var(--negative))',
        primary: {
          ...gold,
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius))',
        sm: 'calc(var(--radius))',
      },
    },
  },
  plugins: [animate],
}
