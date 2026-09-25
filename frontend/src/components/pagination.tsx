import { Button } from "./ui/button";

/* Rodapé de lista paginada: total à esquerda, navegação à direita. */
export function Pagination({
  count,
  noun,
  page,
  hasNext,
  onPage,
}: {
  count: number;
  noun: [string, string];
  page: number;
  hasNext: boolean;
  onPage: (page: number) => void;
}) {
  return (
    <div className="flex flex-wrap justify-between items-center gap-3 mt-5 text-sm">
      <span aria-live="polite">
        {count} {count === 1 ? noun[0] : noun[1]}
      </span>
      <nav aria-label="Paginação" className="flex gap-2">
        <Button variant="outline" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Anterior
        </Button>
        <Button variant="outline" disabled={!hasNext} onClick={() => onPage(page + 1)}>
          Próxima
        </Button>
      </nav>
    </div>
  );
}
