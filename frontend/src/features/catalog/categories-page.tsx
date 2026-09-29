"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { type Category } from "@/features/catalog/types";
import { type Page } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { FormActions } from "@/shared/components/form-actions";
import { PageHeader } from "@/shared/components/page-header";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { Field } from "@/shared/components/fields";

function CategoryForm({
  category,
  done,
  cancel,
}: {
  category: Category | null;
  done: () => void;
  cancel: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // com produtos dentro, o backend não deixa mudar o uso dos parâmetros 3D
  const locked = !!category && category.products_count > 0;
  return (
    <Card className="mb-6">
      <h2>{category ? "Editar categoria" : "Nova categoria"}</h2>
      <ErrorMessage message={error} />
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          const f = new FormData(e.currentTarget);
          const payload: Record<string, unknown> = {
            name: f.get("name"),
            active: f.get("active") === "on",
          };
          if (!locked) payload.uses_printing_profile = f.get("uses_printing_profile") === "on";
          try {
            await api(`categories${category ? `/${category.id}` : ""}`, {
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
        <div className="grid md:grid-cols-2 gap-4">
          <Field
            name="name"
            label="Nome da categoria"
            value={category?.name}
            required
            maxLength={100}
          />
        </div>
        <label className="flex items-center gap-2 mt-5">
          <input
            type="checkbox"
            name="uses_printing_profile"
            defaultChecked={category?.uses_printing_profile ?? false}
            disabled={locked}
          />
          Produção de impressão 3D (produtos dela usam os parâmetros de filamento, energia e tempo)
        </label>
        {locked && (
          <p className="mt-1 text-sm text-muted-foreground">
            Esta categoria já tem produtos, então essa opção não pode mais ser alterada.
          </p>
        )}
        <label className="flex items-center gap-2 my-5">
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
    </Card>
  );
}

export default function Categories() {
  const [data, setData] = useState<Page<Category> | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Category | null | undefined>(undefined);
  const load = useCallback(() => {
    setError("");
    api<Page<Category>>("categories")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(load, [load]);
  return (
    <>
      <PageHeader
        title="Categorias"
        description="Agrupam os produtos. Categoria não se apaga: desative para tirá-la da lista de escolha, e os produtos que já estão nela continuam."
        actions={<Button onClick={() => setEditing(null)}>Nova categoria</Button>}
      />
      <ErrorMessage message={error} />
      {editing !== undefined && (
        <CategoryForm
          key={editing?.id || "new"}
          category={editing}
          done={() => {
            setEditing(undefined);
            load();
          }}
          cancel={() => setEditing(undefined)}
        />
      )}
      <Card>
        {!data ? (
          <p role="status">Carregando categorias…</p>
        ) : !data.results.length ? (
          <Empty>Nenhuma categoria cadastrada.</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Categoria</th>
                  <th>Parâmetros 3D</th>
                  <th>Produtos</th>
                  <th>Status</th>
                  <th>
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((c) => (
                  <tr key={c.id}>
                    <td data-role="title">
                      <strong>{c.name}</strong>
                    </td>
                    <td data-label="Parâmetros 3D">{c.uses_printing_profile ? "Sim" : "Não"}</td>
                    <td data-label="Produtos">{c.products_count}</td>
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
    </>
  );
}
