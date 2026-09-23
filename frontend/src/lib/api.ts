export const BASE = "/jalapao-store";
const labels: Record<string, string> = {
  quantity: "Quantidade", product: "Produto", product_id: "Produto", name: "Nome",
  sku: "Código", kind: "Tipo", description: "Descrição", cost_price: "Custo",
  sale_price: "Preço", printing: "Impressão 3D", filament_price_kg: "Filamento",
  weight_g: "Peso", power_w: "Potência", hours: "Horas", minutes: "Minutos",
  energy_price_kwh: "Energia", labor_cost: "Mão de obra", fixed_cost: "Custo fixo",
  markup_percent: "Acréscimo", items: "Itens", discount: "Desconto",
  platform_fee: "Taxas", shipping_cost: "Frete", status: "Situação",
  amount: "Valor", direction: "Tipo", occurred_on: "Data", reason: "Motivo",
  delta: "Quantidade", username: "Usuário", password: "Senha", channel: "Canal",
  reference: "Referência", idempotency_key: "Identificação da tentativa",
};
function flatten(value: unknown, prefix = ""): string[] {
  if (Array.isArray(value)) return value.flatMap((v) => flatten(v, prefix));
  if (value && typeof value === "object")
    return Object.entries(value).flatMap(([key, v]) =>
      flatten(
        v,
        ["errors", "detail", "non_field_errors"].includes(key)
          ? prefix
          : prefix
            ? `${prefix} / ${labels[key] || key}`
            : labels[key] || key,
      ),
    );
  return [`${prefix ? `${prefix}: ` : ""}${String(value)}`];
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${BASE}/api/${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
    cache: "no-store",
  });
  const data = await res
    .json()
    .catch(() => ({ errors: { detail: "Resposta inválida do servidor." } }));
  if (!res.ok) {
    if (res.status === 401 && !path.startsWith("auth/"))
      window.location.assign(`${BASE}/login`);
    throw new Error(flatten(data).join("\n"));
  }
  return data as T;
}
export const brl = (v: string | number) =>
  Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
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
  sale_price: string;
  description: string;
  active: boolean;
  quantity: number;
  printing: Printing | null;
};
export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
