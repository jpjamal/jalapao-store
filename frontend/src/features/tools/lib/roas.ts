/* Calculadora de ROAS (spec 038): a mesma conta da calculadora de ROAS do Conectando Vendedores.
   ROAS = quanto se vende para cada R$ 1 gasto em anúncios. Os três "ROAS de ..." são o ROAS mínimo para o
   anúncio gastar, por venda, 100%, 50% ou X% do lucro. */

import { faixaShopee } from "@/features/tools/lib/marketplace";

export type EntradasRoas = {
  /** preço de compra ou custo de produção */
  custo: number;
  /** custos da operação (embalagem, mão de obra...) */
  custosOperacao: number;
  preco: number;
  taxaPct: number;
  taxaFixa: number;
  impostosPct: number;
  frete: number;
  /** % do lucro que o ROAS de rentabilidade aceita gastar (padrão do site: 10) */
  rentabilidadePct: number;
  /** quanto o anúncio gasta hoje por venda; 0 = não informado */
  gastoAtual: number;
};

export type ClassificacaoRoas = "perdendo" | "rentabilidade" | "visibilidade" | "empate";

export type ResultadoRoas = {
  taxaMarketplace: number;
  impostos: number;
  custoTotal: number;
  lucro: number;
  /** `null` quando o lucro é zero ou negativo: nenhum gasto em anúncio se paga */
  empate: number | null;
  visibilidade: number | null;
  rentabilidade: number | null;
  /** gasto máximo por venda em cada ROAS (parte do lucro) */
  gastoEmpate: number;
  gastoVisibilidade: number;
  gastoRentabilidade: number;
  roasAtual: number | null;
  classificacao: ClassificacaoRoas | null;
};

export function calcularRoas(e: EntradasRoas): ResultadoRoas {
  const taxaMarketplace = e.preco * (e.taxaPct / 100) + e.taxaFixa;
  const impostos = e.preco * (e.impostosPct / 100);
  const custoTotal = e.custo + e.custosOperacao + taxaMarketplace + impostos + e.frete;
  const lucro = e.preco - custoTotal;
  const pct = e.rentabilidadePct > 0 ? e.rentabilidadePct : 10;

  const temLucro = e.preco > 0 && lucro > 0;
  const empate = temLucro ? e.preco / lucro : null;
  const visibilidade = temLucro ? e.preco / (lucro * 0.5) : null;
  const rentabilidade = temLucro ? e.preco / (lucro * (pct / 100)) : null;

  let roasAtual: number | null = null;
  let classificacao: ClassificacaoRoas | null = null;
  if (e.gastoAtual > 0 && e.preco > 0) {
    roasAtual = e.preco / e.gastoAtual;
    if (e.gastoAtual > lucro) classificacao = "perdendo";
    else if (rentabilidade !== null && roasAtual >= rentabilidade) classificacao = "rentabilidade";
    else if (visibilidade !== null && roasAtual >= visibilidade) classificacao = "visibilidade";
    else classificacao = "empate";
  }

  const parte = (f: number) => (temLucro ? lucro * f : 0);
  return {
    taxaMarketplace,
    impostos,
    custoTotal,
    lucro,
    empate,
    visibilidade,
    rentabilidade,
    gastoEmpate: parte(1),
    gastoVisibilidade: parte(0.5),
    gastoRentabilidade: parte(pct / 100),
    roasAtual,
    classificacao,
  };
}

export type Canal = "manual" | "shopee" | "meli_classico" | "meli_premium";

/** Taxa e taxa fixa que cada marketplace cobra para um preço, pelas mesmas regras da calculadora de taxas. */
export function taxasDoCanal(canal: Canal, preco: number): { pct: number; fixa: number } | null {
  if (canal === "manual" || !(preco > 0)) return null;
  if (canal === "shopee") {
    const faixa = faixaShopee(preco);
    return { pct: faixa.comissao * 100, fixa: faixa.taxaFixa };
  }
  return { pct: canal === "meli_classico" ? 13 : 17.5, fixa: preco < 79 ? 6.5 : 0 };
}
