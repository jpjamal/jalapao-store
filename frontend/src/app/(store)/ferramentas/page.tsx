import Link from "next/link";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/page-header";
export default function Tools() {
  return (
    <>
      <PageHeader
        title="Ferramentas da loja"
        description="As ferramentas que você já usa, com as mesmas regras de cálculo — agora dentro do sistema, sem sair da sessão."
      />
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
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
          <Link
            key={slug}
            href={`/ferramentas/${slug}`}
            className="group rounded-xl focus-visible:outline-2 focus-visible:outline-ring"
          >
            <Card className="h-full transition-colors group-hover:border-primary">
              <h2>{title}</h2>
              <p className="text-muted-foreground mb-6">{description}</p>
              <span className="text-primary font-semibold">Abrir ferramenta →</span>
            </Card>
          </Link>
        ))}
      </div>
      <p className="text-sm text-muted-foreground mt-6">
        Taxas da calculadora são estimativas preservadas do sistema anterior.
        Nas vendas, registre as taxas efetivamente cobradas.
      </p>
    </>
  );
}
