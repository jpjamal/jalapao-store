/* Taxas de marketplace — simulação, não valor real de venda.
   Porte literal da conta que estava em site/calculadora.html. Os números são
   regra de negócio do dono da loja: não mexer sem ele pedir.

   Nas vendas de verdade quem manda são as taxas efetivamente cobradas, digitadas
   no registro da venda. Esta tela só ajuda a escolher preço antes de anunciar. */

export type Market = "shopee" | "meli";
export type PlanoMeli = "classico" | "premium";

export type Faixa = {
  comissao: number;
  taxaFixa: number;
  nome: string;
};

/* Em 01/10/2026 a taxa fixa da primeira faixa passa de R$ 4,00 para R$ 4,50, e com
   ela o teto do "metade do preço" (que é sempre o dobro da taxa fixa) vai de R$ 8
   para R$ 9. O resto da tabela não muda.

   Esses valores estão ANTECIPADOS por decisão do dono da loja: a calculadora já usa
   R$ 4,50 antes da data. Até 01/10 o extrato da Shopee ainda vem com R$ 4,00, então
   nessa faixa a conta fica R$ 0,50 mais conservadora por item. */
export const AJUSTE_OUTUBRO = new Date(2026, 9, 1); // 1º de outubro de 2026

export function tabelaVigente(hoje?: Date) {
  const jaValendo = (hoje || new Date()) >= AJUSTE_OUTUBRO;
  return { taxaPrimeira: 4.5, limiteMetade: 9, jaValendo };
}

export function faixaShopee(preco: number, hoje?: Date): Faixa {
  const t = tabelaVigente(hoje);
  if (preco < t.limiteMetade)
    return {
      comissao: 0.2,
      taxaFixa: preco * 0.5,
      nome: `abaixo de R$ ${t.limiteMetade}`,
    };
  if (preco <= 79.99)
    return { comissao: 0.2, taxaFixa: t.taxaPrimeira, nome: "até R$ 79,99" };
  if (preco <= 99.99)
    return { comissao: 0.14, taxaFixa: 16.0, nome: "R$ 80 a R$ 99,99" };
  if (preco <= 199.99)
    return { comissao: 0.14, taxaFixa: 20.0, nome: "R$ 100 a R$ 199,99" };
  if (preco <= 499.99)
    return { comissao: 0.14, taxaFixa: 26.0, nome: "R$ 200 a R$ 499,99" };
  return { comissao: 0.14, taxaFixa: 26.0, nome: "acima de R$ 500" };
}

export type EntradasMarket = {
  market: Market;
  custo: number;
  preco: number;
  /** percentual do pedido que a Shopee retém e converte em saldo de Ads */
  recarga: number;
  /** R$ 3,00 por item para vendedor CPF acima de 450 pedidos em 90 dias */
  taxaCpf: number;
  plano: PlanoMeli;
};

export type ResultadoMarket = {
  vazio: boolean;
  taxas: number;
  recarga: number;
  deposito: number;
  lucro: number;
  margem: number;
  markup: number;
  encargo: string;
  comissaoFaixa: string;
};

const money = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export function calcularMarket(e: EntradasMarket): ResultadoMarket {
  const vazio: ResultadoMarket = {
    vazio: true,
    taxas: 0,
    recarga: 0,
    deposito: 0,
    lucro: 0,
    margem: 0,
    markup: 0,
    encargo: money(0),
    comissaoFaixa: "—",
  };
  if (!e.preco) return vazio;

  let taxasTotais = 0;
  let encargo = money(0);
  let comissaoFaixa = "—";

  if (e.market === "shopee") {
    // Tabela oficial vigente desde 01/03/2026: a alíquota vem da faixa de preço,
    // não é mais escolha do vendedor — o programa de frete grátis virou obrigatório
    // e os 6% dele já estão embutidos.
    const faixa = faixaShopee(e.preco);
    taxasTotais = e.preco * faixa.comissao + faixa.taxaFixa + e.taxaCpf;
    encargo =
      money(faixa.taxaFixa) + (e.taxaCpf ? ` + ${money(e.taxaCpf)} CPF` : "");
    comissaoFaixa = `${(faixa.comissao * 100).toFixed(0)}% · ${faixa.nome}`;
  } else {
    const comissao = e.plano === "classico" ? 0.13 : 0.175;
    let extra = 0;
    if (e.preco < 79.0) {
      extra = 6.5; // tarifa média de baixo valor
      encargo = "R$ 6,50 · baixo valor";
    } else {
      encargo = "R$ 0,00 · isento acima de R$ 79";
    }
    taxasTotais = e.preco * comissao + extra;
  }

  // recarga automática sai do que você recebe: desconta como qualquer dedução
  const pctRecarga = e.market === "shopee" ? e.recarga : 0;
  const recarga = e.preco * (pctRecarga / 100);

  // o que o marketplace deposita: preço menos tudo que ele retém, sem o custo do produto
  const deposito = e.preco - taxasTotais - recarga;
  const lucro = e.preco - e.custo - taxasTotais - recarga;
  const margem = (lucro / e.preco) * 100;
  const markup = e.custo > 0 ? (lucro / e.custo) * 100 : 0;

  return {
    vazio: false,
    taxas: taxasTotais,
    recarga,
    deposito,
    lucro,
    margem,
    markup,
    encargo,
    comissaoFaixa,
  };
}

export const porcento = (v: number) => `${v.toFixed(1).replace(".", ",")}%`;
