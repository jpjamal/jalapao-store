import type { MetadataRoute } from "next";
import { BASE } from "@/lib/api";

/* Manifesto do app instalável (spec 014). O Next serve em /jalapao-store/manifest.webmanifest e
   põe o <link rel="manifest"> em todas as páginas. Caminhos de arquivos de public/ levam o
   basePath à mão: o Next não o acrescenta dentro do manifesto. Ícones: `npm run icons`. */
export default function manifest(): MetadataRoute.Manifest {
  return {
    id: `${BASE}/`,
    name: "Jalapão Store · Gestão",
    short_name: "Jalapão Store",
    description: "Produtos, estoque, vendas e anúncios da Jalapão Store.",
    lang: "pt-BR",
    start_url: `${BASE}/`,
    scope: `${BASE}/`,
    display: "standalone",
    orientation: "portrait",
    background_color: "#17100a",
    theme_color: "#17100a",
    categories: ["business", "productivity"],
    icons: [
      { src: `${BASE}/icons/icon-192.png`, sizes: "192x192", type: "image/png", purpose: "any" },
      { src: `${BASE}/icons/icon-512.png`, sizes: "512x512", type: "image/png", purpose: "any" },
      { src: `${BASE}/icons/icon-maskable-512.png`, sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Nova venda", url: `${BASE}/vendas`, icons: [{ src: `${BASE}/icons/icon-192.png`, sizes: "192x192" }] },
      { name: "Anúncios", url: `${BASE}/anuncios`, icons: [{ src: `${BASE}/icons/icon-192.png`, sizes: "192x192" }] },
      { name: "Estoque", url: `${BASE}/estoque`, icons: [{ src: `${BASE}/icons/icon-192.png`, sizes: "192x192" }] },
    ],
  };
}
