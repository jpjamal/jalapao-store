import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Jalapão Store | Gestão",
  description: "Produtos, estoque e resultados da Jalapão Store",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
