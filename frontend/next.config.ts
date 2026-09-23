import type { NextConfig } from "next";
const config: NextConfig = {
  basePath: "/jalapao-store",
  output: "standalone",
  poweredByHeader: false,
  async redirects() {
    return [
      { source: "/index.html", destination: "/", permanent: true },
      {
        source: "/produtos-3d.html",
        destination: "/produtos",
        permanent: true,
      },
      ...["impressao-3d", "calculadora", "etiquetas"].map((name) => ({
        source: `/${name}.html`,
        destination: `/ferramentas/${name}.html`,
        permanent: true,
      })),
    ];
  },
};
export default config;
