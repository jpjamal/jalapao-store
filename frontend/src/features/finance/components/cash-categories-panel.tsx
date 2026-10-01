"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { type CashCategory } from "@/features/finance/types";
import { type Page } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { FormActions } from "@/shared/components/form-actions";
import { ErrorMessage } from "@/shared/components/feedback";
import { Field } from "@/shared/components/fields";
import { useClientList } from "@/shared/hooks/use-list-query";
import { ClearFilters, FilterSelect, ListToolbar, SearchBox, SortSelect } from "@/shared/components/list-toolbar";
import { SortableTh } from "@/shared/components/sortable-th";
import { type SortColumn } from "@/shared/lib/list";

const directionLabel = { in: "Entrada", out: "Saída", both: "Entrada ou saída" } as const;
const columns: SortColumn[] = [
  { key: "name", label: "Categoria", kind: "text" },
  { key: "direction", label: "Vale para", kind: "text" },
  { key: "counts_in_result", label: "Conta no resultado", kind: "text" },
  { key: "entries_count", label: "Lançamentos", kind: "number" },
  { key: "active", label: "Status", kind: "text" },
];

function CategoryForm({
  category,
  done,
  cancel,
}: {
  category: CashCategory | null;
  done: () => void;
  cancel: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // com lançamentos dentro, o backend não deixa mudar a direção
  const locked = !!category && category.entries_count > 0;
  return (
    <form
      className="border rounded-md p-4 mb-4"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        const f = new FormData(e.currentTarget);
        const payload: Record<string, unknown> = {
          name: f.get("name"),
          counts_in_result: f.get("counts_in_result") === "on",
          active: f.get("active") === "on",
        };
        if (!locked) payload.direction = f.get("direction");
        try {
          await api(`cash-categories${category ? `/${category.id}` : ""}`, {
            method: category ? "PATCH" : "POST",
            body: JSON.stringify(payload),
          });
          done();
        } catch (err) {
          setError((err as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <h3>{category ? "Editar categoria" : "Nova categoria do Caixa"}</h3>
      <ErrorMessage message={error} />
      <div className="grid md:grid-cols-2 gap-4">
        <Field name="name" label="Nome da categoria" value={category?.name} required maxLength={100} />
        <div>
          <label htmlFor="cat-direction">Vale para</label>
          <select
            id="cat-direction"
            name="direction"
            defaultValue={category?.direction ?? "out"}
            disabled={locked}
          >
            <option value="out">Saída / despesa</option>
            <option value="in">Entrada</option>
            <option value="both">Entrada ou saída</option>
          </select>
        </div>
      </div>
      {locked && (
        <p className="mt-1 text-sm text-muted-foreground">
          Esta categoria já tem lançamentos, então a direção não pode mais ser alterada.
        </p>
      )}
      <label className="flex items-center gap-2 mt-4">
        <input type="checkbox" name="counts_in_result" defaultChecked={category?.counts_in_result ?? true} />
        Conta no Resultado do negócio (despesa ou receita da loja)
      </label>
      <p className="text-sm text-muted-foreground mt-1">
        Deixe desmarcado para o que só movimenta dinheiro, como empréstimo, aporte e retirada do dono, ou
        para o que já está no custo da peça. Vale também para os lançamentos antigos.
      </p>
      <label className="flex items-center gap-2 my-4">
        <input type="checkbox" name="active" defaultChecked={category?.active ?? true} />
        Categoria ativa
      </label>
      <FormActions>
        <Button disabled={busy}>{busy ? "Salvando…" : "Salvar categoria"}</Button>
        <Button type="button" variant="outline" onClick={cancel} disabled={busy}>
          Cancelar
        </Button>
      </FormActions>
    </form>
  );
}

/* Cadastro das categorias do Caixa, aberto dentro da tela do Caixa (spec 026). As categorias do
   sistema aparecem, mas só os lançamentos automáticos as usam e elas não se editam. */
export function CashCategoriesPanel({ onChanged }: { onChanged: () => void }) {
  const [rows, setRows] = useState<CashCategory[] | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<CashCategory | null | undefined>(undefined);
  const list = useClientList(rows, {
    texts: (c) => [c.name],
    filters: {
      direction: (c, v) => c.direction === v,
      status: (c, v) => (v === "active" ? c.active : !c.active),
      system: (c, v) => (v === "system" ? c.is_system : !c.is_system),
    },
    getters: {
      name: (c) => c.name,
      direction: (c) => directionLabel[c.direction],
      counts_in_result: (c) => c.counts_in_result,
      entries_count: (c) => c.entries_count,
      active: (c) => c.active,
    },
  });
  const load = useCallback(() => {
    setError("");
    api<Page<CashCategory>>("cash-categories")
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);
  return (
    <Card className="mb-6">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <h2>Categorias do Caixa</h2>
        <Button size="sm" onClick={() => setEditing(null)}>
          Nova categoria
        </Button>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Categoria não se apaga: desative para tirá-la da lista de escolha. As marcadas como "do sistema" são
        usadas sozinhas pelos lançamentos automáticos (vendas, compras, insumos e estornos).
      </p>
      <ErrorMessage message={error} />
      {editing !== undefined && (
        <CategoryForm
          key={editing?.id || "new"}
          category={editing}
          done={() => {
            setEditing(undefined);
            load();
            onChanged();
          }}
          cancel={() => setEditing(undefined)}
        />
      )}
      <ListToolbar>
        <SearchBox value={list.search} onChange={list.setSearch} placeholder="Nome da categoria…" />
        <FilterSelect
          label="Vale para"
          value={list.filters.direction ?? ""}
          onChange={(v) => list.setFilter("direction", v)}
          options={[["in", "Entrada"], ["out", "Saída"], ["both", "Entrada ou saída"]]}
        />
        <FilterSelect
          label="Situação"
          value={list.filters.status ?? ""}
          onChange={(v) => list.setFilter("status", v)}
          options={[["active", "Ativas"], ["inactive", "Inativas"]]}
        />
        <FilterSelect
          label="Tipo"
          value={list.filters.system ?? ""}
          onChange={(v) => list.setFilter("system", v)}
          options={[["mine", "Minhas"], ["system", "Do sistema"]]}
        />
        <SortSelect columns={columns} sort={list.sort} onChange={list.setSort} />
        <ClearFilters visible={list.hasActiveFilters} onClick={list.clear} />
      </ListToolbar>
      {!rows ? (
        <p role="status">Carregando categorias…</p>
      ) : (
        <div className="overflow-auto">
          <table className="data-table">
            <thead>
              <tr>
                <SortableTh label="Categoria" sortKey="name" sort={list.sort} onSort={list.toggle} />
                <SortableTh label="Vale para" sortKey="direction" sort={list.sort} onSort={list.toggle} />
                <SortableTh label="Conta no resultado" sortKey="counts_in_result" sort={list.sort} onSort={list.toggle} />
                <SortableTh label="Lançamentos" sortKey="entries_count" sort={list.sort} onSort={list.toggle} />
                <SortableTh label="Status" sortKey="active" sort={list.sort} onSort={list.toggle} />
                <th>
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {(list.visible ?? []).map((c) => (
                <tr key={c.id}>
                  <td data-role="title">
                    <strong>{c.name}</strong>
                    {c.is_system && (
                      <p className="text-xs text-muted-foreground font-normal">do sistema</p>
                    )}
                  </td>
                  <td data-label="Vale para">{directionLabel[c.direction]}</td>
                  <td data-label="Conta no resultado">{c.is_system ? "—" : c.counts_in_result ? "Sim" : "Não"}</td>
                  <td data-label="Lançamentos">{c.entries_count}</td>
                  <td data-label="Status">{c.active ? "Ativa" : "Inativa"}</td>
                  <td data-role="actions">
                    {!c.is_system && (
                      <Button variant="outline" size="sm" onClick={() => setEditing(c)}>
                        Editar
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
