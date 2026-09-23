export const BASE = "/jalapao-store";
function flatten(value: unknown, prefix = ""): string[] {
  if (Array.isArray(value)) return value.flatMap((v) => flatten(v, prefix));
  if (value && typeof value === "object")
    return Object.entries(value).flatMap(([key, v]) =>
      flatten(
        v,
        ["errors", "detail", "non_field_errors"].includes(key)
          ? prefix
          : prefix
            ? `${prefix} / ${key}`
            : key,
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
