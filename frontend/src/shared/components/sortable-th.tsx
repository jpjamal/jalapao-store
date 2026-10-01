import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { type Sort } from "@/shared/lib/list";

/* Cabeçalho de coluna clicável (spec 027): 1º clique crescente, 2º decrescente, 3º ordem padrão. A seta
   mostra a coluna e a direção ativas. No celular o cabeçalho some, e quem ordena é o seletor "Ordenar por". */
export function SortableTh({
  label,
  sortKey,
  sort,
  onSort,
}: {
  label: string;
  sortKey: string;
  sort: Sort;
  onSort: (key: string) => void;
}) {
  const active = sort?.key === sortKey;
  const Icon = !active ? ArrowUpDown : sort.dir === "asc" ? ArrowUp : ArrowDown;
  return (
    <th aria-sort={!active ? "none" : sort.dir === "asc" ? "ascending" : "descending"}>
      <button
        type="button"
        onClick={() => onSort(sortKey)}
        className="inline-flex items-center gap-1 text-left hover:underline [font:inherit] [letter-spacing:inherit] [text-transform:inherit]"
      >
        {label}
        <Icon size={14} aria-hidden="true" className={active ? "" : "opacity-40"} />
      </button>
    </th>
  );
}
