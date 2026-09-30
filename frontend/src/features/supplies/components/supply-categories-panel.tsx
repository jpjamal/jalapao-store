"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { type SupplyCategory } from "@/features/supplies/types";
import { type Page } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { FormActions } from "@/shared/components/form-actions";
import { ErrorMessage } from "@/shared/components/feedback";
import { Field } from "@/shared/components/fields";

function CategoryForm({
  category,
  done,
  cancel,
}: {
  category: SupplyCategory | null;
  done: () => void;
  cancel: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // com insumos dentro, o backend não deixa mudar se a categoria é de filamento
  const locked = !!category && category.supplies_count > 0;
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
          active: f.get("active") === "on",
        };
        if (!locked) payload.is_filament = f.get("is_filament") === "on";
        try {
          await api(`supply-categories${category ? `/${category.id}` : ""}`, {
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
      <h3>{category ? "Editar categoria" : "Nova categoria de insumo"}</h3>
      <ErrorMessage message={error} />
      <div className="grid md:grid-cols-2 gap-4">
        <Field name="name" label="Nome da categoria" value={category?.name} required maxLength={100} />
      </div>
      <label className="flex items-center gap-2 mt-4">
        <input
          type="checkbox"
          name="is_filament"
          defaultChecked={category?.is_filament ?? false}
          disabled={locked}
        />
        É de filamento (os insumos dela têm material, cor e dados do rolo)
      </label>
      {locked && (
        <p className="mt-1 text-sm text-muted-foreground">
          Esta categoria já tem insumos, então essa opção não pode mais ser alterada.
        </p>
      )}
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

/* Cadastro das categorias de insumo, aberto dentro da tela de Insumos. */
export function SupplyCategoriesPanel({ onChanged }: { onChanged: () => void }) {
  const [rows, setRows] = useState<SupplyCategory[] | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<SupplyCategory | null | undefined>(undefined);
  const load = useCallback(() => {
    setError("");
    api<Page<SupplyCategory>>("supply-categories")
      .then((r) => setRows(r.results))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);
  return (
    <Card className="mb-6">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <h2>Categorias de insumo</h2>
        <Button size="sm" onClick={() => setEditing(null)}>
          Nova categoria
        </Button>
      </div>
      <p className="text-sm text-muted-foreground mb-4">
        Categoria não se apaga: desative para tirá-la da lista de escolha. Os insumos que já estão
        nela continuam.
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
      {!rows ? (
        <p role="status">Carregando categorias…</p>
      ) : (
        <div className="overflow-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Categoria</th>
                <th>Filamento</th>
                <th>Insumos</th>
                <th>Status</th>
                <th>
                  <span className="sr-only">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id}>
                  <td data-role="title">
                    <strong>{c.name}</strong>
                  </td>
                  <td data-label="Filamento">{c.is_filament ? "Sim" : "Não"}</td>
                  <td data-label="Insumos">{c.supplies_count}</td>
                  <td data-label="Status">{c.active ? "Ativa" : "Inativa"}</td>
                  <td data-role="actions">
                    <Button variant="outline" size="sm" onClick={() => setEditing(c)}>
                      Editar
                    </Button>
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
