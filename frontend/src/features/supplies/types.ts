/* Tipos dos insumos, no formato da API (valores decimais chegam como texto). */
export type SupplyCategory = {
  id: string;
  name: string;
  is_filament: boolean;
  /* a compra paga entra como despesa no Resultado do negócio */
  counts_as_expense: boolean;
  active: boolean;
  supplies_count: number;
  created_at: string;
};

export type Supply = {
  id: string;
  category: string;
  category_name: string;
  category_is_filament: boolean;
  name: string;
  unit: string;
  notes: string;
  active: boolean;
  material: string;
  color: string;
  roll_weight_g: string | null;
  roll_price: string | null;
  price_per_gram: string | null;
  price_per_kg: string | null;
  /* saldo atual em rolos ou unidades */
  quantity: number;
  /* custo de cada unidade que sai numa venda: o da última compra ou ajuste de entrada com custo (spec 040) */
  unit_cost: string | null;
  /* parte do saldo que sai sem custo numa venda (já contada como despesa ou sem custo conhecido) */
  uncosted: number;
};

export type SupplyReceipt = {
  id: string;
  supply: string;
  supply_name: string;
  quantity: number;
  unit_cost: string;
  total: string;
  counts_as_expense_snapshot: boolean;
  occurred_on: string;
  supplier: string;
  reference: string;
  notes: string;
  paid_at: string | null;
  status: string;
};

export type SupplyMovement = {
  id: string;
  supply: string;
  supply_name: string;
  delta: number;
  balance_after: number;
  reason: string;
  unit_cost: string | null;
  created_at: string;
};
