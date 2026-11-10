/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Symbiote blacks
        'symbiote': {
          black: '#000000',
          dark: '#0a0a0a',
          panel: '#111214',
          surface: '#1a1c1e',
          border: '#222426',
        },
        // Web whites
        'web': {
          white: '#f4f4f6',
          dim: '#e8e8ea',
          muted: '#9a9a9e',
          faint: '#3a3a3e',
        },
        // Klyntar accent (green)
        'klyntar': '#00ff66',
        // Carnage red
        'carnage': '#ff0033',
      },
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      keyframes: {
        'tendril-pulse': {
          '0%, 100%': { opacity: '0.3', transform: 'scaleY(1)' },
          '50%': { opacity: '0.8', transform: 'scaleY(1.05)' },
        },
        'web-spin': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'symbiote-breathe': {
          '0%, 100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.02)' },
        },
        'glitch': {
          '0%, 100%': { transform: 'translate(0)', clipPath: 'inset(0 0 100% 0)' },
          '20%': { transform: 'translate(-2px, 1px)', clipPath: 'inset(10% 0 85% 0)' },
          '40%': { transform: 'translate(2px, -1px)', clipPath: 'inset(50% 0 40% 0)' },
          '60%': { transform: 'translate(-1px, 2px)', clipPath: 'inset(80% 0 10% 0)' },
          '80%': { transform: 'translate(1px, -2px)', clipPath: 'inset(30% 0 65% 0)' },
        },
        'glitch-text': {
          '0%, 90%, 100%': { transform: 'translate(0)', textShadow: '0 0 8px rgba(244,244,246,0.5)' },
          '92%': { transform: 'translate(-2px)', textShadow: '-2px 0 #ff0033, 2px 0 #00ff66' },
          '94%': { transform: 'translate(2px)', textShadow: '2px 0 #ff0033, -2px 0 #00ff66' },
          '96%': { transform: 'translate(-1px)', textShadow: '-1px 0 #ff0033' },
          '98%': { transform: 'translate(1px)', textShadow: '1px 0 #00ff66' },
        },
        'tendril-crawl': {
          '0%': { strokeDashoffset: '1000', opacity: '0' },
          '30%': { opacity: '0.6' },
          '70%': { opacity: '0.6' },
          '100%': { strokeDashoffset: '0', opacity: '0' },
        },
        'web-crawl': {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '60px 60px' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-left': {
          '0%': { opacity: '0', transform: 'translateX(-24px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'slide-in-right': {
          '0%': { opacity: '0', transform: 'translateX(24px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 4px rgba(0,255,102,0.4)' },
          '50%': { boxShadow: '0 0 12px rgba(0,255,102,0.9)' },
        },
        'blink': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        'symbiote-load': {
          '0%': { width: '0%', boxShadow: '0 0 10px rgba(0,255,102,0.3)' },
          '100%': { width: '100%', boxShadow: '0 0 20px rgba(0,255,102,0.8)' },
        },
        'tendril-grow': {
          '0%': { strokeDashoffset: '500', opacity: '0' },
          '100%': { strokeDashoffset: '0', opacity: '1' },
        },
      },
      animation: {
        'tendril-pulse': 'tendril-pulse 3s ease-in-out infinite',
        'web-spin': 'web-spin 20s linear infinite',
        'symbiote-breathe': 'symbiote-breathe 4s ease-in-out infinite',
        'glitch-text': 'glitch-text 8s ease-in-out infinite',
        'web-crawl': 'web-crawl 8s linear infinite',
        'fade-in-up': 'fade-in-up 0.5s ease-out forwards',
        'slide-in-left': 'slide-in-left 0.4s ease-out forwards',
        'slide-in-right': 'slide-in-right 0.4s ease-out forwards',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'blink': 'blink 1s step-end infinite',
        'symbiote-load': 'symbiote-load 2s ease-out forwards',
        'tendril-grow': 'tendril-grow 1.5s ease-out forwards',
      },
      backgroundImage: {
        'web-pattern': "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Cpath d='M0 0 L60 60 M60 0 L0 60 M30 0 L30 60 M0 30 L60 30' stroke='rgba(255,255,255,0.03)' stroke-width='0.5'/%3E%3C/svg%3E\")",
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'web-glow': '0 0 20px rgba(244,244,246,0.1)',
        'klyntar-glow': '0 0 20px rgba(0,255,102,0.3)',
        'carnage-glow': '0 0 20px rgba(255,0,51,0.3)',
        'inner-web': 'inset 0 0 20px rgba(244,244,246,0.03)',
      },
    },
  },
  plugins: [],
}
