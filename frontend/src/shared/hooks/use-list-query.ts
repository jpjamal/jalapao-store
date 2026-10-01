"use client";
import { useCallback, useEffect, useMemo, useState } from "react";
import { matchesSearch, nextSort, orderingParam, sortRows, type Cell, type Sort } from "@/shared/lib/list";

/* Espera o valor parar de mudar antes de usá-lo: a busca só vai ao servidor quando o dono para de digitar. */
export function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

/* Estado de ordenação de uma lista carregada por inteiro (a ordenação acontece na tela). */
export function useSort(initial: Sort = null) {
  const [sort, setSort] = useState<Sort>(initial);
  const toggle = useCallback((key: string) => setSort((current) => nextSort(current, key)), []);
  return { sort, setSort, toggle };
}

/* Estado de uma lista paginada pelo servidor (spec 027): busca, filtros, ordem e página, e a query pronta
   (`queryString`). Mudar a busca, um filtro ou a ordem volta à primeira página. */
export function useListQuery(initialFilters: Record<string, string> = {}) {
  const [search, setSearchState] = useState("");
  const debouncedSearch = useDebounced(search, 300);
  const [filters, setFilters] = useState<Record<string, string>>(initialFilters);
  const [sort, setSort] = useState<Sort>(null);
  const [page, setPage] = useState(1);

  const setSearch = useCallback((value: string) => {
    setSearchState(value);
    setPage(1);
  }, []);
  const setFilter = useCallback((key: string, value: string) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(1);
  }, []);
  const toggleSort = useCallback((key: string) => {
    setSort((current) => nextSort(current, key));
    setPage(1);
  }, []);
  const changeSort = useCallback((value: Sort) => {
    setSort(value);
    setPage(1);
  }, []);
  const clear = useCallback(() => {
    setSearchState("");
    setFilters(initialFilters);
    setPage(1);
    // a ordem escolhida não faz parte de "limpar filtros"
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const queryString = useMemo(() => {
    const params = new URLSearchParams({ page: String(page) });
    if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());
    for (const [key, value] of Object.entries(filters)) if (value) params.set(key, value);
    const ordering = orderingParam(sort);
    if (ordering) params.set("ordering", ordering);
    return params.toString();
  }, [page, debouncedSearch, filters, sort]);

  const hasActiveFilters = search.trim() !== "" || Object.entries(filters).some(([k, v]) => v !== (initialFilters[k] ?? ""));

  return {
    search, setSearch, filters, setFilter, sort, toggleSort, setSort: changeSort, page, setPage, queryString,
    hasActiveFilters, clear,
  };
}

/* Busca, filtros e ordenação de uma lista pequena, carregada por inteiro: tudo acontece na tela, com as mesmas
   regras do servidor (sem acento, número como número). `texts` diz onde a busca procura em cada linha, `filters`
   decide se a linha passa por cada filtro escolhido, e `getters` dá o valor de cada coluna ordenável. */
export function useClientList<T>(
  rows: T[] | null,
  options: {
    texts: (row: T) => unknown[];
    filters?: Record<string, (row: T, value: string) => boolean>;
    getters: Record<string, (row: T) => Cell>;
  },
) {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const { sort, setSort, toggle } = useSort();
  const setFilter = useCallback((key: string, value: string) => setFilters((c) => ({ ...c, [key]: value })), []);
  const clear = useCallback(() => {
    setSearch("");
    setFilters({});
  }, []);
  const visible = useMemo(() => {
    if (!rows) return null;
    let result = rows.filter((row) => matchesSearch(search, ...options.texts(row)));
    for (const [key, value] of Object.entries(filters)) {
      const test = options.filters?.[key];
      if (value && test) result = result.filter((row) => test(row, value));
    }
    return sortRows(result, sort, options.getters);
    // as funções de `options` descrevem a tela e não mudam de significado entre renderizações
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, search, filters, sort]);
  const hasActiveFilters = search.trim() !== "" || Object.values(filters).some(Boolean);
  return { visible, search, setSearch, filters, setFilter, sort, setSort, toggle, hasActiveFilters, clear };
}
