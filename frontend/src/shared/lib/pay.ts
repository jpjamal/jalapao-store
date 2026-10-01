/* Pagamento em lote (spec 028): paga uma compra de cada vez, na ordem da tela, e para na primeira que falhar.
   Devolve as que faltam pagar e a mensagem de erro (vazia se tudo foi pago). O que já foi pago continua pago. */
export async function payInOrder<T extends { id: string }>(
  items: T[],
  payOne: (item: T) => Promise<unknown>,
  label: (item: T) => string,
): Promise<{ paid: T[]; rest: T[]; error: string }> {
  const paid: T[] = [];
  for (const item of items) {
    try {
      await payOne(item);
      paid.push(item);
    } catch (err) {
      const done = paid.length ? `${paid.length} de ${items.length} já foram pagas. ` : "";
      return {
        paid,
        rest: items.slice(paid.length),
        error: `${done}Parou em ${label(item)}: ${(err as Error).message}`,
      };
    }
  }
  return { paid, rest: [], error: "" };
}
