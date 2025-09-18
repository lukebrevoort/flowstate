import type { NextConfig } from 'next';

// Only enable bundle analyzer during development when ANALYZE=true
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig: NextConfig = {
  /* config options here */
  // Optimize for production builds
  poweredByHeader: false,
  compress: true,
};

export default withBundleAnalyzer(nextConfig);
