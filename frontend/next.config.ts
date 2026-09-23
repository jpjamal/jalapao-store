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
      // as ferramentas viraram páginas do app: tanto o endereço do site antigo
      // quanto o da cópia servida em public/ levam para a página nova
      ...["impressao-3d", "calculadora", "etiquetas"].flatMap((name) =>
        [`/${name}.html`, `/ferramentas/${name}.html`].map((source) => ({
          source,
          destination: `/ferramentas/${name}`,
          permanent: true,
        })),
      ),
    ];
  },
};
export default config;
