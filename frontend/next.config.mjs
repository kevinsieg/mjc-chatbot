/** @type {import('next').NextConfig} */
const internalBackend =
  process.env.BACKEND_INTERNAL_URL || "http://backend:8000";

const frameAncestors = process.env.EMBED_FRAME_ANCESTORS || "*";

const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        source: "/embed",
        headers: [
          {
            key: "Content-Security-Policy",
            value: `frame-ancestors ${frameAncestors}`,
          },
        ],
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${internalBackend.replace(/\/$/, "")}/:path*`,
      },
    ];
  },
};

export default nextConfig;
