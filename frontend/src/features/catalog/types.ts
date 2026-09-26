/* Tipos do catálogo, no formato da API (valores decimais chegam como texto). */
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
};
export type Product = {
  id: string;
  sku: string;
  name: string;
  kind: string;
  cost_price: string;
  stock_value: string;
  average_cost: string;
  sale_price: string;
  description: string;
  active: boolean;
  quantity: number;
  printing: Printing | null;
};
