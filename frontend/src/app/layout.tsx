import type { Metadata, Viewport } from "next";
import { BASE } from "@/lib/api";
import { ServiceWorker } from "@/components/service-worker";
import "./globals.css";

export const metadata: Metadata = {
  title: "Jalapão Store | Gestão",
  description: "Produtos, estoque e resultados da Jalapão Store",
  applicationName: "Jalapão Store",
  // arquivos de public/ levam o basePath à mão (ver app/manifest.ts); ícones: `npm run icons`
  icons: {
    icon: [{ url: `${BASE}/icons/favicon-48.png`, sizes: "48x48", type: "image/png" }],
    apple: [{ url: `${BASE}/icons/apple-touch-icon.png`, sizes: "180x180" }],
  },
  appleWebApp: { capable: true, title: "Jalapão Store", statusBarStyle: "black-translucent" },
  formatDetection: { telephone: false },
};

// cor da barra do sistema no app instalado, acompanhando o tema claro ou escuro
export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f7f2ea" },
    { media: "(prefers-color-scheme: dark)", color: "#17100a" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>
        {children}
        <ServiceWorker />
      </body>
    </html>
  );
}
