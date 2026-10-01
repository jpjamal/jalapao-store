/* Busca, ordenação e filtros das listagens (spec 027): regras puras, sem tela.

   Lista paginada ordena e filtra no servidor (a ordem vale para a lista inteira); lista pequena, carregada por
   inteiro, ordena e busca aqui mesmo, com estas funções. Texto ordena em português e sem acento; número ordena
   como número, mesmo vindo como texto da API ("10" depois de "9"). */

export type SortDir = "asc" | "desc";
export type Sort = { key: string; dir: SortDir } | null;
/* o tipo da coluna só serve para escrever a direção em português no seletor "Ordenar por" */
export type SortKind = "text" | "number" | "date";
export type SortColumn = { key: string; label: string; kind: SortKind };

/* 1º clique crescente, 2º decrescente, 3º volta à ordem padrão da tela */
export function nextSort(current: Sort, key: string): Sort {
  if (!current || current.key !== key) return { key, dir: "asc" };
  return current.dir === "asc" ? { key, dir: "desc" } : null;
}

/* valor do `?ordering=` do backend: o nome do campo, com "-" na frente quando decrescente */
export function orderingParam(sort: Sort): string {
  return sort ? `${sort.dir === "desc" ? "-" : ""}${sort.key}` : "";
}

/* minúsculas e sem acento: o mesmo tratamento do backend, para a busca da tela e a do servidor concordarem */
export function fold(text: unknown): string {
  return String(text ?? "")
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase();
}

/* todas as palavras da busca precisam aparecer, cada uma em algum dos textos da linha */
export function matchesSearch(term: string, ...texts: unknown[]): boolean {
  const words = fold(term).split(/\s+/).filter(Boolean);
  if (!words.length) return true;
  const haystack = texts.map(fold);
  return words.every((word) => haystack.some((text) => text.includes(word)));
}

const collator = new Intl.Collator("pt-BR", { sensitivity: "base", numeric: true });
const NUMERIC = /^-?\d+(\.\d+)?$/;
export type Cell = string | number | boolean | null | undefined;

const isEmpty = (v: Cell) => v === null || v === undefined || v === "";
const asNumber = (v: Cell): number | null => {
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  return typeof v === "string" && NUMERIC.test(v) ? Number(v) : null;
};

/* compara dois valores: número como número, o resto como texto em português */
export function compareCells(a: Cell, b: Cell): number {
  const x = asNumber(a);
  const y = asNumber(b);
  if (x !== null && y !== null) return x - y;
  return collator.compare(String(a), String(b));
}

/* ordena uma cópia das linhas pela coluna escolhida; valor vazio vai sempre para o fim */
export function sortRows<T>(rows: T[], sort: Sort, getters: Record<string, (row: T) => Cell>): T[] {
  const get = sort ? getters[sort.key] : undefined;
  if (!sort || !get) return rows;
  const factor = sort.dir === "desc" ? -1 : 1;
  return [...rows].sort((a, b) => {
    const x = get(a);
    const y = get(b);
    if (isEmpty(x) || isEmpty(y)) return isEmpty(x) === isEmpty(y) ? 0 : isEmpty(x) ? 1 : -1;
    return factor * compareCells(x, y);
  });
}

/* texto da direção no seletor, conforme o tipo da coluna */
export function directionLabel(kind: SortKind, dir: SortDir): string {
  if (kind === "number") return dir === "asc" ? "menor primeiro" : "maior primeiro";
  if (kind === "date") return dir === "asc" ? "mais antigo primeiro" : "mais recente primeiro";
  return dir === "asc" ? "A → Z" : "Z → A";
}
