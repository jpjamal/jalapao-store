import { useState } from "react";

/* Seleção por caixinhas (spec 028). `rows` são as linhas que podem ser marcadas e que estão na tela: o que
   saiu da tela (outro filtro, ordem ou página) sai da seleção sozinho, porque só se conta quem está em `rows`. */
export function useSelection<T extends { id: string }>(rows: T[]) {
  const [ids, setIds] = useState<Set<string>>(new Set());
  const selected = rows.filter((r) => ids.has(r.id));
  const allChecked = rows.length > 0 && selected.length === rows.length;
  return {
    selected,
    has: (id: string) => ids.has(id),
    allChecked,
    someChecked: selected.length > 0 && !allChecked,
    toggle: (id: string) =>
      setIds((cur) => {
        const next = new Set(cur);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return next;
      }),
    toggleAll: () => setIds(allChecked ? new Set() : new Set(rows.map((r) => r.id))),
    clear: () => setIds(new Set()),
  };
}
