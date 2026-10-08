export type SaleItem = { id: string; product_name: string; quantity: number; unit_price: string };
export type Sale = {
  id: string;
  created_at: string;
  updated_at: string;
  channel: string;
  external_id: string;
  reference: string;
  gross: string;
  discount: string;
  platform_fee: string;
  shipping_cost: string;
  net: string;
  profit: string;
  status: string;
  received_at: string | null;
  items: SaleItem[];
  supplies?: { supply_name: string; requested: number; taken: number; shortfall: number }[];
};

export const channels: Record<string, string> = {
  direct: "Boca a boca", site: "Site Jalapão", mercado_livre: "Mercado Livre", shopee: "Shopee", other: "Outro",
};
