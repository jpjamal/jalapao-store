import { Card } from "@/components/ui/card";
import { BASE } from "@/lib/api";
export default function Tools() {
  return (
    <>
      <h1>Ferramentas da loja</h1>
      <p className="text-muted-foreground mb-8">
        As ferramentas que você já usa, com as mesmas regras de cálculo.
      </p>
      <div className="grid md:grid-cols-3 gap-5">
        {[
          [
            "impressao-3d",
            "Impressão 3D",
            "Simule filamento, energia, tempo e margem.",
          ],
          [
            "calculadora",
            "Taxas de marketplace",
            "Compare estimativas de venda por plataforma.",
          ],
          ["etiquetas", "Etiquetas", "Prepare etiquetas e arquivos ZPL."],
        ].map(([slug, title, description]) => (
          <Card key={slug}>
            <h2>{title}</h2>
            <p className="text-muted-foreground mb-6">{description}</p>
            <a
              className="text-primary font-semibold"
              href={`${BASE}/ferramentas/${slug}.html`}
            >
              Abrir ferramenta →
            </a>
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
