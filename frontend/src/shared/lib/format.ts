/** Valor em reais, no formato brasileiro (R$ 1.234,56). */
export const brl = (v: string | number) =>
  Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
