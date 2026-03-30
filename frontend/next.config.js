/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Проксирование запросов к API для удобства в деве
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://api:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
