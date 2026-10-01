"use client";
import { useId } from "react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { directionLabel, type Sort, type SortColumn } from "@/shared/lib/list";

/* Barra acima de cada listagem (spec 027): busca, filtros, período e "Ordenar por", iguais em todas as telas. */

export function ListToolbar({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-wrap items-end gap-3 mb-5">{children}</div>;
}

export function SearchBox({
  value,
  onChange,
  label = "Buscar",
  placeholder = "Buscar…",
}: {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
}) {
  const id = useId();
  return (
    <div className="grow sm:grow-0 sm:w-72">
      <label htmlFor={id}>{label}</label>
      <Input
        id={id}
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

export function FilterSelect({
  label,
  value,
  onChange,
  options,
  allLabel = "Todos",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: [value: string, label: string][];
  allLabel?: string;
}) {
  const id = useId();
  return (
    <div className="min-w-36">
      <label htmlFor={id}>{label}</label>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">{allLabel}</option>
        {options.map(([v, text]) => (
          <option key={v} value={v}>
            {text}
          </option>
        ))}
      </select>
    </div>
  );
}

/* período em dias: "de" e "até" valem o dia inteiro */
export function DateRange({
  from,
  to,
  onFrom,
  onTo,
}: {
  from: string;
  to: string;
  onFrom: (value: string) => void;
  onTo: (value: string) => void;
}) {
  const fromId = useId();
  const toId = useId();
  return (
    <>
      <div>
        <label htmlFor={fromId}>De</label>
        <Input id={fromId} type="date" value={from} max={to || undefined} onChange={(e) => onFrom(e.target.value)} />
      </div>
      <div>
        <label htmlFor={toId}>Até</label>
        <Input id={toId} type="date" value={to} min={from || undefined} onChange={(e) => onTo(e.target.value)} />
      </div>
    </>
  );
}

/* "Ordenar por": o mesmo estado dos cabeçalhos, e a única forma de ordenar no celular */
export function SortSelect({
  columns,
  sort,
  onChange,
}: {
  columns: SortColumn[];
  sort: Sort;
  onChange: (sort: Sort) => void;
}) {
  const id = useId();
  return (
    <div className="min-w-48">
      <label htmlFor={id}>Ordenar por</label>
      <select
        id={id}
        value={sort ? `${sort.key}|${sort.dir}` : ""}
        onChange={(e) => {
          if (!e.target.value) return onChange(null);
          const [key, dir] = e.target.value.split("|");
          onChange({ key, dir: dir as "asc" | "desc" });
        }}
      >
        <option value="">Ordem padrão</option>
        {columns.flatMap((c) =>
          (["asc", "desc"] as const).map((dir) => (
            <option key={`${c.key}|${dir}`} value={`${c.key}|${dir}`}>
              {c.label} ({directionLabel(c.kind, dir)})
            </option>
          )),
        )}
      </select>
    </div>
  );
}

export function ClearFilters({ visible, onClick }: { visible: boolean; onClick: () => void }) {
  if (!visible) return null;
  return (
    <Button type="button" variant="ghost" onClick={onClick}>
      Limpar filtros
    </Button>
  );
}
