/** @type {import('next').NextConfig} */

// URL base del backend (mismo valor que usa lib/api.ts y hooks/use-websocket.ts).
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_WS_URL = API_BASE_URL.replace(/^https:\/\//, 'wss://').replace(/^http:\/\//, 'ws://');
const isDev = process.env.NODE_ENV !== 'production';

// V2 (CSP Header Not Set): 'unsafe-inline' en style-src es necesario porque
// Radix UI posiciona overlays con el atributo style="" inline. 'unsafe-eval'
// en script-src solo se habilita en desarrollo (Fast Refresh de Next.js).
const cspDirectives = [
  `default-src 'self'`,
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ''}`,
  `style-src 'self' 'unsafe-inline'`,
  `img-src 'self' data: blob:`,
  `font-src 'self' data:`,
  `connect-src 'self' ${API_BASE_URL} ${API_WS_URL}`,
  `base-uri 'self'`,
  `object-src 'none'`,
  `form-action 'self'`,
  `frame-ancestors 'none'`,
].join('; ');

const nextConfig = {
  output: 'standalone',
  // V4 (Server Leaks Info via X-Powered-By): oculta el header que anuncia Next.js.
  poweredByHeader: false,
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          // V2 (CSP Header Not Set)
          { key: 'Content-Security-Policy', value: cspDirectives },
          // V3 (Missing Anti-clickjacking Header)
          { key: 'X-Frame-Options', value: 'DENY' },
          // V5 (X-Content-Type-Options Header Missing)
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ]
  },
}

export default nextConfig