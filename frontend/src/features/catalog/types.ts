/* Tipos do catálogo, no formato da API (valores decimais chegam como texto). */
export type PrintingFilament = {
  filament: string;
  filament_name: string;
  material: string;
  color: string;
  grams: string;
  roll_price: string;
  roll_weight_g: string;
  price_per_kg: string;
  price_outdated: boolean;
};
/* Componente que vai dentro da peça 3D (spec 041): o custo foi copiado do insumo quando a linha foi salva. */
export type PrintingComponent = {
  supply: string;
  supply_name: string;
  unit: string;
  quantity: number;
  unit_cost: string;
  price_outdated: boolean;
};
export type Printing = {
  filament_price_kg: string;
  weight_g: string;
  power_w: string;
  hours: number;
  minutes: number;
  energy_price_kwh: string;
  labor_cost: string;
  fixed_cost: string;
  markup_percent: string;
  filaments?: PrintingFilament[];
  components?: PrintingComponent[];
};
export type Category = {
  id: string;
  name: string;
  uses_printing_profile: boolean;
  active: boolean;
  products_count: number;
  created_at: string;
};
export type Product = {
  id: string;
  sku: string;
  gtin: string | null;
  name: string;
  category: string;
  category_name: string;
  brand: string;
  model: string;
  weight_g: string | null;
  cost_price: string;
  stock_value: string;
  average_cost: string;
  sale_price: string;
  description: string;
  active: boolean;
  quantity: number;
  printing: Printing | null;
  /* embalagem padrão: insumos sugeridos na venda, por unidade vendida (spec 040) */
  default_supplies?: { supply: string; supply_name: string; quantity: number }[];
};
