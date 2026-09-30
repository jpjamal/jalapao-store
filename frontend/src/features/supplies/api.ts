import { api } from "@/shared/api/client";
import { type Page } from "@/shared/api/types";
import { type Supply } from "@/features/supplies/types";

/* Todos os insumos, página a página (o backend entrega 100 por vez). */
export async function allSupplies() {
  const result: Supply[] = [];
  let page = 1;
  while (true) {
    const data = await api<Page<Supply>>(`supplies?page=${page}`);
    result.push(...data.results);
    if (!data.next) return result;
    page++;
  }
}

/* Preço por grama tem casas demais para o `brl`: mostra até 4 casas (R$ 0,0899). */
export function brlGrama(valor: string | number | null | undefined) {
  if (valor == null || valor === "") return "—";
  return `R$ ${Number(valor).toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  })}`;
}
