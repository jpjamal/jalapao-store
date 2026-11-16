import { type Supply } from "@/features/supplies/types";

/* Saldo de um insumo para a tela. Filamento é contado em gramas desde a spec 041: mostra também quantos
   rolos isso dá, para não precisar fazer conta de cabeça. */
export function saldoTexto(supply: Pick<Supply, "quantity" | "unit" | "category_is_filament" | "roll_weight_g">) {
  const base = `${supply.quantity.toLocaleString("pt-BR")} ${supply.unit}`;
  return supply.category_is_filament ? `${base}${rolosTexto(supply.quantity, supply.roll_weight_g)}` : base;
}

/* "≈ 1,3 rolo" a partir das gramas e do peso do rolo; vazio sem peso do rolo */
export function rolosTexto(grams: number, rollWeight: string | null) {
  const peso = Number(rollWeight || 0);
  if (!peso) return "";
  const rolos = grams / peso;
  const texto = rolos.toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  return ` (≈ ${texto} ${rolos >= 2 ? "rolos" : "rolo"})`;
}
