/* Tipos do Caixa, no formato da API (valores decimais chegam como texto). */
export type CashCategory = {
  id: string;
  name: string;
  /* "in" entrada, "out" saída, "both" serve para as duas (só a do sistema "A classificar") */
  direction: "in" | "out" | "both";
  /* conta no Resultado do negócio (despesa ou receita que entra no resultado) */
  counts_in_result: boolean;
  active: boolean;
  /* categoria do sistema: só dos lançamentos automáticos, não se edita nem se escolhe */
  is_system: boolean;
  entries_count: number;
};

export type CashEntry = {
  id: string;
  direction: string;
  amount: string;
  description: string;
  occurred_on: string;
  category: string;
  category_name: string;
  origin: CashOrigin;
};

export type CashOrigin =
  | "sale"
  | "sale_refund"
  | "sale_adjustment"
  | "purchase"
  | "purchase_refund"
  | "supply"
  | "supply_refund"
  | "manual";

export const originLabels: Record<CashOrigin, string> = {
  sale: "Venda",
  sale_refund: "Estorno de venda",
  sale_adjustment: "Correção de venda",
  purchase: "Compra de estoque",
  purchase_refund: "Estorno de compra de estoque",
  supply: "Compra de insumo",
  supply_refund: "Estorno de compra de insumo",
  manual: "Manual",
};

export type CashSummaryRow = {
  category: string;
  category_name: string;
  is_system: boolean;
  counts_in_result: boolean;
  entries: number;
  in_total: string;
  out_total: string;
};
