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
  has_label: boolean;
  label_order_id: string;
  label_filename: string;
  items: SaleItem[];
  supplies?: { supply_name: string; requested: number; taken: number; shortfall: number }[];
};

export type SaleLabel = {
  zpl: string;
  source_name: string;
  order_id: string;
  recipient_name: string;
  recipient_city: string;
  recipient_state: string;
  created_at: string;
  updated_at: string;
};

export const channels: Record<string, string> = {
  direct: "Boca a boca", site: "Site Jalapão", mercado_livre: "Mercado Livre", shopee: "Shopee", other: "Outro",
};
