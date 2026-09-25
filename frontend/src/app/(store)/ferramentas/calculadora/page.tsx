"use client";
import { useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
  calcularMarket,
  porcento,
  tabelaVigente,
  type Market,
  type PlanoMeli,
} from "@/lib/ferramentas/marketplace";
import { PageHeader } from "@/components/page-header";

/* As faixas e alíquotas vivem em lib/ferramentas/marketplace.ts e são as mesmas
   de antes. Isto aqui é simulação para escolher preço: na venda registrada valem
   as taxas efetivamente cobradas, digitadas no formulário de venda. */

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export default function Calculadora() {
  const [market, setMarket] = useState<Market>("shopee");
  const [custo, setCusto] = useState("");
  const [preco, setPreco] = useState("");
  const [recarga, setRecarga] = useState("0");
  const [taxaCpf, setTaxaCpf] = useState("0");
  const [plano, setPlano] = useState<PlanoMeli>("classico");

  const t = useMemo(() => tabelaVigente(), []);
  const r = useMemo(
    () =>
      calcularMarket({
        market,
        custo: parseFloat(custo) || 0,
        preco: parseFloat(preco) || 0,
        recarga: parseFloat(recarga) || 0,
        taxaCpf: parseFloat(taxaCpf) || 0,
        plano,
      }),
    [market, custo, preco, recarga, taxaCpf, plano],
  );

  const shopee = market === "shopee";
  const futuro = t.jaValendo ? null : (
    <span className="text-xs opacity-70"> vale a partir de 1º/10</span>
  );

  return (
    <>
      <PageHeader
        back={{ href: "/ferramentas", label: "Ferramentas" }}
        eyebrow="Ferramentas · simulação"
        title="Taxas de marketplace"
        description="Quanto sobra no bolso depois do que a plataforma retém. Use para escolher o preço antes de anunciar."
      />

      <div className="flex gap-2 mb-6" role="group" aria-label="Marketplace">
        {(
          [
            ["shopee", "Shopee"],
            ["meli", "Mercado Livre"],
          ] as const
        ).map(([valor, rotulo]) => (
          <button
            key={valor}
            type="button"
            aria-pressed={market === valor}
            onClick={() => setMarket(valor)}
            className={`rounded-md px-4 h-11 sm:h-10 grow sm:grow-0 text-sm font-medium cursor-pointer border ${
              market === valor
                ? "bg-primary text-primary-foreground border-transparent"
                : "border-input hover:bg-muted"
            }`}
          >
            {rotulo}
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-[1fr_380px] gap-6 items-start">
        <Card>
          <h2>Números da venda</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="custo">Custo do produto (R$)</label>
              <Input
                id="custo"
                type="number"
                min="0"
                step="0.01"
                inputMode="decimal"
                value={custo}
                onChange={(e) => setCusto(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="preco">Preço de venda (R$)</label>
              <Input
                id="preco"
                type="number"
                min="0"
                step="0.01"
                inputMode="decimal"
                value={preco}
                onChange={(e) => setPreco(e.target.value)}
              />
            </div>
            {shopee ? (
              <>
                <div>
                  <label htmlFor="recarga">Recarga automática de Ads (%)</label>
                  <Input
                    id="recarga"
                    type="number"
                    min="0"
                    step="0.1"
                    inputMode="decimal"
                    value={recarga}
                    onChange={(e) => setRecarga(e.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="taxaCpf">Vendedor</label>
                  <select
                    id="taxaCpf"
                    value={taxaCpf}
                    onChange={(e) => setTaxaCpf(e.target.value)}
                  >
                    <option value="0">CNPJ, ou CPF até 450 pedidos</option>
                    <option value="3">
                      CPF acima de 450 pedidos em 90 dias (+R$ 3,00)
                    </option>
                  </select>
                </div>
              </>
            ) : (
              <div>
                <label htmlFor="plano">Tipo de anúncio</label>
                <select
                  id="plano"
                  value={plano}
                  onChange={(e) => setPlano(e.target.value as PlanoMeli)}
                >
                  <option value="classico">Clássico</option>
                  <option value="premium">Premium (12× sem juros)</option>
                </select>
              </div>
            )}
          </div>
        </Card>

        <Card>
          <h2>
            Lucro líquido no bolso · {shopee ? "Shopee" : "Mercado Livre"}
          </h2>
          <p
            className={`money text-4xl mb-5 ${r.lucro < 0 ? "text-destructive" : "text-primary"}`}
          >
            {brl(r.lucro)}
          </p>
          <dl className="grid grid-cols-2 gap-y-3">
            {(
              [
                ["Taxas da plataforma", brl(r.taxas)],
                ["Taxa fixa aplicada", r.encargo],
                shopee ? ["Comissão da faixa", r.comissaoFaixa] : null,
                shopee ? ["Recarga de Ads", brl(r.recarga)] : null,
                ["Depósito da plataforma", brl(r.deposito)],
                ["Margem sobre o preço", porcento(r.margem)],
                ["Markup sobre o custo", porcento(r.markup)],
              ].filter(Boolean) as [string, string][]
            ).map(([rotulo, valor]) => (
              <div key={rotulo} className="contents">
                <dt className="text-muted-foreground text-sm self-center">
                  {rotulo}
                </dt>
                <dd className="money text-right">{valor}</dd>
              </div>
            ))}
          </dl>
          <p className="text-sm text-muted-foreground mt-4">
            O depósito é o que {shopee ? "a Shopee" : "o Mercado Livre"} manda
            para você, antes de tirar o custo do produto.
          </p>
        </Card>
      </div>

      <Card className="mt-6">
        <h2>Regras e taxas</h2>
        {shopee ? (
          <>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Faixa de preço</th>
                  <th>Comissão</th>
                  <th>Taxa fixa</th>
                  <th>Subsídio Pix</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td data-role="title">
                    Abaixo de R$ {t.limiteMetade},00{futuro}
                  </td>
                  <td data-label="Comissão" className="money">20%</td>
                  <td data-label="Taxa fixa">metade do preço</td>
                  <td data-label="Subsídio Pix">—</td>
                </tr>
                <tr>
                  <td data-role="title">Até R$ 79,99</td>
                  <td data-label="Comissão" className="money">20%</td>
                  <td data-label="Taxa fixa" className="money">
                    <b className="text-destructive">{brl(t.taxaPrimeira)}</b>
                    {futuro}
                  </td>
                  <td data-label="Subsídio Pix">—</td>
                </tr>
                <tr>
                  <td data-role="title">R$ 80 a R$ 99,99</td>
                  <td data-label="Comissão" className="money">14%</td>
                  <td data-label="Taxa fixa" className="money">R$ 16,00</td>
                  <td data-label="Subsídio Pix" className="money">5%</td>
                </tr>
                <tr>
                  <td data-role="title">R$ 100 a R$ 199,99</td>
                  <td data-label="Comissão" className="money">14%</td>
                  <td data-label="Taxa fixa" className="money">R$ 20,00</td>
                  <td data-label="Subsídio Pix" className="money">5%</td>
                </tr>
                <tr>
                  <td data-role="title">R$ 200 a R$ 499,99</td>
                  <td data-label="Comissão" className="money">14%</td>
                  <td data-label="Taxa fixa" className="money">R$ 26,00</td>
                  <td data-label="Subsídio Pix" className="money">5%</td>
                </tr>
                <tr>
                  <td data-role="title">Acima de R$ 500</td>
                  <td data-label="Comissão" className="money">14%</td>
                  <td data-label="Taxa fixa" className="money">R$ 26,00</td>
                  <td data-label="Subsídio Pix" className="money">até 8%</td>
                </tr>
              </tbody>
            </table>
            <div className="text-sm text-muted-foreground mt-4 space-y-3">
              {t.jaValendo ? (
                <p>Tabela com o ajuste de 1º de outubro de 2026 aplicado.</p>
              ) : (
                <p>
                  <b>Atenção ao período de transição:</b> a taxa fixa da primeira
                  faixa já está aqui com o ajuste que só passa a valer em{" "}
                  <b>1º de outubro de 2026</b> (R$ 4,00 → R$ 4,50, e o teto do
                  meio-preço de R$ 8 para R$ 9). Até lá o extrato da Shopee ainda
                  vem com R$ 4,00, então nessa faixa a calculadora mostra R$ 0,50
                  a menos de lucro por item do que você realmente recebe — erra
                  para o lado seguro.
                </p>
              )}
              <p>
                Vendedor CNPJ; o vendedor CPF paga R$ 3,00 por item a mais depois
                de 450 pedidos em 90 dias (o seletor acima). O programa de frete
                grátis é obrigatório e os 6% dele já estão embutidos na comissão —
                por isso o extrato mostra duas linhas, comissão e taxa de serviço,
                que somam o valor da tabela; a taxa de transação também já está
                dentro.
              </p>
              <p>
                <b>O subsídio Pix não muda o que você recebe:</b> a Shopee
                desconta do comprador e abate o mesmo valor da própria comissão —
                só o valor da nota fiscal fica menor.
              </p>
              <p>
                <b>Não entram nesta conta:</b> os 2,5% de campanha de destaque, a
                taxa de até R$ 10,00 por devolução com culpa do vendedor e o cupom
                que você oferece — a Shopee desconta o cupom antes de aplicar a
                comissão.
              </p>
            </div>
          </>
        ) : (
          <>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Tipo de anúncio</th>
                  <th>Comissão média</th>
                  <th>Regra abaixo de R$ 79</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td data-role="title">Clássico</td>
                  <td data-label="Comissão média" className="money">~11% a 14%</td>
                  <td data-label="Regra abaixo de R$ 79">
                    Abaixo de R$ 79 paga taxa fixa por unidade; acima, só
                    comissão.
                  </td>
                </tr>
                <tr>
                  <td data-role="title">Premium (12× sem juros)</td>
                  <td data-label="Comissão média" className="money">~15% a 19%</td>
                  <td data-label="Regra abaixo de R$ 79">Inclui o custo do parcelamento sem juros ao comprador.</td>
                </tr>
              </tbody>
            </table>
            <p className="text-sm text-muted-foreground mt-4">
              Médias de mercado para categorias gerais — a comissão do Mercado
              Livre muda por categoria, confira a sua no anúncio antes de fechar o
              preço.
            </p>
          </>
        )}
      </Card>
    </>
  );
}
