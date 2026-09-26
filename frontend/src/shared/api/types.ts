/** Página de lista do backend (paginação do DRF). */
export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
