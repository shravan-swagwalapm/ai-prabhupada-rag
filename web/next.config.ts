import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: { unoptimized: true },
  // Rewrites removed — same origin on Railway, dev uses proxy separately
};

export default nextConfig;
