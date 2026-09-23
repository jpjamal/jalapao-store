import Link from "next/link";
import { Card } from "@/components/ui/card";
export default function Tools() {
  return (
    <>
      <h1>Ferramentas da loja</h1>
      <p className="text-muted-foreground mb-8">
        As ferramentas que você já usa, com as mesmas regras de cálculo — agora
        dentro do sistema, sem sair da sessão.
      </p>
      <div className="grid md:grid-cols-3 gap-5">
        {[
          [
            "impressao-3d",
            "Impressão 3D",
            "Filamento, energia, tempo e margem — e salva a peça no catálogo.",
          ],
          [
            "calculadora",
            "Taxas de marketplace",
            "Quanto sobra no bolso depois do que a plataforma retém.",
          ],
          [
            "etiquetas",
            "Etiquetas",
            "ZPL da Shopee vira PDF nomeado pelo destinatário.",
          ],
        ].map(([slug, title, description]) => (
          <Card key={slug}>
            <h2>{title}</h2>
            <p className="text-muted-foreground mb-6">{description}</p>
            <Link
              className="text-primary font-semibold"
              href={`/ferramentas/${slug}`}
            >
              Abrir ferramenta →
            </Link>
          </Card>
        ))}
      </div>
      <p className="text-sm text-muted-foreground mt-6">
        Taxas da calculadora são estimativas preservadas do sistema anterior.
        Nas vendas, registre as taxas efetivamente cobradas.
      </p>
    </>
  );
}
