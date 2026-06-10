import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone copies only the runtime files Next actually needs into
  // .next/standalone/, so the production image is small enough to ship
  // through ECR without dragging the full node_modules tree along.
  output: "standalone",
};

export default nextConfig;
