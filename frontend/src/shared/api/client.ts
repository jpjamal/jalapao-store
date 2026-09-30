/* Cliente da API: todas as chamadas passam pelo BFF (app/api/[...path]/route.ts), que guarda
   o JWT em cookie httpOnly. Erros do backend viram mensagem legível, com o nome do campo em
   português (`labels`). 401 fora do login leva à tela de login. */
export const BASE = "/jalapao-store";
const labels: Record<string, string> = {
  quantity: "Quantidade",
  product: "Produto",
  product_id: "Produto",
  name: "Nome",
  sku: "Código",
  kind: "Tipo",
  category: "Categoria",
  receipt: "Compra",
  supply: "Insumo",
  supply_id: "Insumo",
  material: "Material",
  color: "Cor",
  roll_weight_g: "Peso do rolo",
  roll_price: "Preço do rolo",
  unit: "Unidade",
  is_filament: "Categoria de filamento",
  filaments: "Filamentos",
  filament: "Filamento",
  grams: "Gramas",
  brand: "Marca",
  model: "Modelo",
  uses_printing_profile: "Usa parâmetros de impressão 3D",
  description: "Descrição",
  cost_price: "Custo",
  sale_price: "Preço",
  printing: "Impressão 3D",
  filament_price_kg: "Filamento",
  weight_g: "Peso",
  power_w: "Potência",
  hours: "Horas",
  minutes: "Minutos",
  energy_price_kwh: "Energia",
  labor_cost: "Mão de obra",
  fixed_cost: "Custo fixo",
  markup_percent: "Acréscimo",
  items: "Itens",
  discount: "Desconto",
  platform_fee: "Taxas",
  shipping_cost: "Frete",
  status: "Situação",
  amount: "Valor",
  direction: "Tipo",
  occurred_on: "Data",
  reason: "Motivo",
  delta: "Quantidade",
  username: "Usuário",
  password: "Senha",
  channel: "Canal",
  reference: "Referência",
  idempotency_key: "Identificação da tentativa",
  unit_cost: "Custo unitário",
  supplier: "Fornecedor",
  notes: "Observação",
  integration: "Marketplace",
  category_id: "Categoria",
  q: "Busca",
  gtin: "Código de barras",
  order_ids: "Pedidos",
  days: "Período",
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
