"use client";
import { useMemo, useState } from "react";
import Link from "next/link";
import { Input } from "@/shared/ui/input";
import { Card } from "@/shared/ui/card";
import { PageHeader } from "@/shared/components/page-header";
import { calcularRoas, taxasDoCanal, type Canal, type ClassificacaoRoas } from "@/features/tools/lib/roas";

/* Calculadora de ROAS (spec 038): quanto o anúncio precisa vender para cada R$ 1 gasto para empatar, dar
   visibilidade ou dar lucro. Simulação para decidir o gasto com Ads; nada é gravado. */

const brl = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const num = (v: string) => {
  const n = Number(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : 0;
};
const fmt = (v: number | null) => (v === null ? "—" : v.toFixed(2).replace(".", ","));
const dinheiro = (v: number) => v.toFixed(2).replace(".", ",");

const CANAIS: [Canal, string][] = [
  ["manual", "Digitar as taxas"],
  ["shopee", "Shopee"],
  ["meli_classico", "Mercado Livre Clássico"],
  ["meli_premium", "Mercado Livre Premium"],
];

const CLASSES: Record<ClassificacaoRoas, { texto: string; cor: string; dica: string }> = {
  perdendo: {
    texto: "Perdendo",
    cor: "text-destructive",
    dica: "O gasto com anúncio por venda é maior que o lucro: cada venda dá prejuízo.",
  },
  rentabilidade: {
    texto: "Rentabilidade",
    cor: "text-primary",
    dica: "O ROAS atual atinge o de rentabilidade: o anúncio deixa a parte do lucro que você definiu.",
  },
  visibilidade: {
    texto: "Visibilidade 50%",
    cor: "text-foreground",
    dica: "O anúncio gasta até metade do lucro por venda: bom para ganhar posição, com lucro menor.",
  },
  empate: {
    texto: "Empate",
    cor: "text-foreground",
    dica: "O anúncio gasta mais da metade do lucro (até todo ele): paga o gasto, mas sobra pouco.",
  },
};

export default function CalculadoraRoas() {
  const [custo, setCusto] = useState("");
  const [operacao, setOperacao] = useState("");
  const [preco, setPreco] = useState("");
  const [canal, setCanal] = useState<Canal>("manual");
  const [taxaPct, setTaxaPct] = useState("");
  const [taxaFixa, setTaxaFixa] = useState("");
  const [impostos, setImpostos] = useState("");
  const [frete, setFrete] = useState("");
  const [rentab, setRentab] = useState("10");
  const [gasto, setGasto] = useState("");

  // com um marketplace escolhido, as taxas vêm das mesmas regras da calculadora de taxas
  const doCanal = taxasDoCanal(canal, num(preco));
  const pct = doCanal ? doCanal.pct : num(taxaPct);
  const fixa = doCanal ? doCanal.fixa : num(taxaFixa);

  const r = useMemo(
    () =>
      calcularRoas({
        custo: num(custo),
        custosOperacao: num(operacao),
        preco: num(preco),
        taxaPct: pct,
        taxaFixa: fixa,
        impostosPct: num(impostos),
        frete: num(frete),
        rentabilidadePct: num(rentab),
        gastoAtual: num(gasto),
      }),
    [custo, operacao, preco, pct, fixa, impostos, frete, rentab, gasto],
  );

  const vazio = !(num(preco) > 0);
  const semLucro = !vazio && r.lucro <= 0;
  const classe = r.classificacao ? CLASSES[r.classificacao] : null;

  function campo(id: string, rotulo: string, valor: string, set: (v: string) => void, extra?: { dica?: string; bloqueado?: boolean }) {
    return (
      <div>
        <label htmlFor={id}>{rotulo}</label>
        <Input
          id={id}
          inputMode="decimal"
          value={valor}
          disabled={extra?.bloqueado}
          onChange={(e) => set(e.target.value)}
        />
        {extra?.dica && <p className="text-xs text-muted-foreground mt-1">{extra.dica}</p>}
      </div>
    );
  }

  return (
    <>
      <PageHeader
        back={{ href: "/ferramentas", label: "Ferramentas" }}
        eyebrow="Ferramentas · simulação"
        title="Calculadora de ROAS"
        description="Descubra quanto o anúncio precisa vender para cada R$ 1 gasto em Ads para empatar, ganhar visibilidade ou dar lucro."
      />

      <div className="grid lg:grid-cols-[1fr_380px] gap-6 items-start">
        <Card>
          <h2>Números do produto</h2>
          <div className="mb-4">
            <label htmlFor="roas-canal">Taxas do marketplace</label>
            <select id="roas-canal" value={canal} onChange={(e) => setCanal(e.target.value as Canal)}>
              {CANAIS.map(([valor, rotulo]) => (
                <option key={valor} value={valor}>
                  {rotulo}
                </option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground mt-1">
              Escolha um marketplace para preencher a taxa e a taxa fixa pelo preço de venda (as mesmas regras da
              calculadora de{" "}
              <Link className="underline" href="/ferramentas/calculadora">
                taxas de marketplace
              </Link>
              ), ou digite as suas.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {campo("roas-custo", "Preço de compra (R$)", custo, setCusto, { dica: "Ou o custo de produção da peça 3D." })}
            {campo("roas-operacao", "Custos da operação (R$)", operacao, setOperacao, { dica: "Embalagem, mão de obra, etc." })}
            {campo("roas-preco", "Preço de venda (R$)", preco, setPreco)}
            {campo("roas-impostos", "Impostos pagos (%)", impostos, setImpostos)}
            {campo("roas-taxa", "Taxa do marketplace (%)", doCanal ? dinheiro(doCanal.pct) : taxaPct, setTaxaPct, {
              bloqueado: !!doCanal,
            })}
            {campo("roas-fixa", "Taxa fixa do marketplace (R$)", doCanal ? dinheiro(doCanal.fixa) : taxaFixa, setTaxaFixa, {
              bloqueado: !!doCanal,
            })}
            {campo("roas-frete", "Custo do frete (R$) — opcional", frete, setFrete)}
            {campo("roas-rentab", "% do lucro para o ROAS de rentabilidade", rentab, setRentab, {
              dica: "Quanto do lucro você aceita gastar em anúncio por venda (padrão 10%).",
            })}
          </div>
          <div className="mt-5 border-t pt-4">
            <h3 className="mb-2">Seu anúncio hoje</h3>
            <div className="grid sm:grid-cols-2 gap-4">
              {campo("roas-gasto", "Gasto atual por venda (R$)", gasto, setGasto, {
                dica: "Quanto o anúncio gasta, em média, para fazer uma venda.",
              })}
            </div>
          </div>
        </Card>

        <Card>
          <h2>Lucro líquido por venda</h2>
          <p className={`money text-4xl mb-1 ${r.lucro < 0 && !vazio ? "text-destructive" : "text-primary"}`}>
            {vazio ? brl(0) : brl(r.lucro)}
          </p>
          {!vazio && (
            <p className="text-sm text-muted-foreground mb-4">
              Custo total {brl(r.custoTotal)}: taxas {brl(r.taxaMarketplace)}, impostos {brl(r.impostos)}.
            </p>
          )}
          {semLucro && (
            <p role="status" className="text-sm text-destructive mb-4">
              Sem lucro por venda: nenhum gasto em anúncio se paga. Aumente o preço ou reduza os custos.
            </p>
          )}

          <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-3">
            {(
              [
                ["ROAS de empate (100% do lucro)", fmt(r.empate), r.empate !== null ? `gasta até ${brl(r.gastoEmpate)}/venda` : ""],
                ["ROAS de visibilidade (50% do lucro)", fmt(r.visibilidade), r.visibilidade !== null ? `gasta até ${brl(r.gastoVisibilidade)}/venda` : ""],
                [
                  `ROAS de rentabilidade (${num(rentab) > 0 ? num(rentab) : 10}% do lucro)`,
                  fmt(r.rentabilidade),
                  r.rentabilidade !== null ? `gasta até ${brl(r.gastoRentabilidade)}/venda` : "",
                ],
              ] as [string, string, string][]
            ).map(([rotulo, valor, sub]) => (
              <div key={rotulo} className="contents">
                <dt className="text-muted-foreground text-sm self-center">{rotulo}</dt>
                <dd className="money text-right">
                  {valor}
                  {sub && <span className="block text-xs text-muted-foreground font-normal">{sub}</span>}
                </dd>
              </div>
            ))}
          </dl>

          <div className="mt-5 border-t pt-4">
            <p className="text-sm text-muted-foreground">ROAS atual</p>
            <p className="money text-2xl">{fmt(r.roasAtual)}</p>
            {classe ? (
              <>
                <p className={`font-semibold mt-1 ${classe.cor}`}>Classificação: {classe.texto}</p>
                <p className="text-sm text-muted-foreground mt-1">{classe.dica}</p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground mt-1">Informe o gasto atual por venda para classificar o anúncio.</p>
            )}
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <h2>Como ler</h2>
        <div className="text-sm text-muted-foreground space-y-3">
          <p>
            <b>ROAS</b> é quanto o anúncio vende para cada R$ 1 gasto nele. Aqui ele é calculado como o preço de venda
            dividido pelo que você pode gastar por venda (uma parte do lucro).
          </p>
          <p>
            <b>Empate</b> gasta todo o lucro da venda (lucro zero). <b>Visibilidade</b> gasta metade. <b>Rentabilidade</b>{" "}
            gasta só a porcentagem do lucro que você definiu. Quanto maior o ROAS do anúncio, mais ele rende por real gasto.
          </p>
          <p>
            Lucro líquido = preço de venda − preço de compra − custos da operação − taxa do marketplace (% e fixa) −
            impostos − frete.
          </p>
        </div>
      </Card>
    </>
  );
}
