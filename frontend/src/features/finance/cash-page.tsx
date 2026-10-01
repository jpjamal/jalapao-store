"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { brl } from "@/shared/lib/format";
import { type Page } from "@/shared/api/types";
import {
  originLabels,
  type CashCategory,
  type CashEntry,
  type CashSummaryRow,
} from "@/features/finance/types";
import { CashCategoriesPanel } from "@/features/finance/components/cash-categories-panel";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Field, MoneyField } from "@/shared/components/fields";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { FormActions } from "@/shared/components/form-actions";
import { PageHeader } from "@/shared/components/page-header";
import { Pagination } from "@/shared/components/pagination";

/* categorias que o dono pode escolher: não são do sistema, estão ativas e combinam com o tipo */
const choosable = (categories: CashCategory[], direction: string) =>
  categories.filter(
    (c) => !c.is_system && c.active && (c.direction === "both" || c.direction === direction),
  );

export default function Cash() {
  const [rows, setRows] = useState<Page<CashEntry> | null>(null);
  const [categories, setCategories] = useState<CashCategory[]>([]);
  const [summary, setSummary] = useState<CashSummaryRow[]>([]);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState("");
  const [direction, setDirection] = useState("out");
  const [showCategories, setShowCategories] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const loadCategories = useCallback(() => {
    api<Page<CashCategory>>("cash-categories")
      .then((r) => setCategories(r.results))
      .catch((e) => setError(e.message));
  }, []);
  const load = useCallback(() => {
    const params = new URLSearchParams({ page: String(page) });
    if (filter) params.set("category", filter);
    api<Page<CashEntry>>(`cash?${params}`)
      .then(setRows)
      .catch((e) => setError(e.message));
    api<CashSummaryRow[]>("cash/summary")
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, [page, filter]);
  useEffect(load, [load]);
  useEffect(loadCategories, [loadCategories]);

  const toClassify = summary.find((s) => s.is_system && s.category_name === "A classificar")?.entries ?? 0;
  const options = choosable(categories, direction);

  async function reclassify(entry: CashEntry, category: string) {
    setError("");
    setNotice("");
    try {
      await api(`cash/${entry.id}`, { method: "PATCH", body: JSON.stringify({ category }) });
      setNotice("Categoria do lançamento atualizada.");
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <PageHeader
        title="Caixa"
        description="Recebimentos e despesas. Vendas pendentes só entram quando marcadas como recebidas."
        actions={
          <Button variant="outline" onClick={() => setShowCategories((v) => !v)}>
            {showCategories ? "Fechar categorias" : "Gerenciar categorias"}
          </Button>
        }
      />
      <ErrorMessage message={error} />
      {notice && (
        <p role="status" className="text-success mb-4">
          {notice}
        </p>
      )}
      {toClassify > 0 && (
        <p role="status" className="border border-[var(--cerrado)] rounded-md p-3 mb-5">
          {toClassify} {toClassify === 1 ? "lançamento ainda está" : "lançamentos ainda estão"} em{" "}
          <strong>A classificar</strong> e fora do Resultado do negócio. Escolha a categoria de cada um na lista
          abaixo.
        </p>
      )}
      {showCategories && <CashCategoriesPanel onChanged={loadCategories} />}
      <Card className="mb-5">
        <h2>Lançamento manual</h2>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            const form = e.currentTarget;
            try {
              await api("cash", {
                method: "POST",
                body: JSON.stringify(Object.fromEntries(new FormData(form))),
              });
              form.reset();
              setDirection("out");
              setNotice("Lançamento registrado.");
              load();
              loadCategories();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label htmlFor="direction">Tipo</label>
              <select
                id="direction"
                name="direction"
                value={direction}
                onChange={(e) => setDirection(e.target.value)}
              >
                <option value="out">Saída / despesa</option>
                <option value="in">Entrada</option>
              </select>
            </div>
            <div>
              <label htmlFor="category">Categoria</label>
              <select id="category" name="category" required defaultValue="" key={direction}>
                <option value="">Escolha…</option>
                {options.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                    {c.counts_in_result ? "" : " (fora do resultado)"}
                  </option>
                ))}
              </select>
            </div>
            <MoneyField name="amount" label="Valor (R$)" />
            <Field
              name="occurred_on"
              label="Data"
              type="date"
              value={new Date().toLocaleDateString("en-CA")}
              required
            />
            <div className="sm:col-span-2">
              <Field name="description" label="Descrição" required maxLength={240} />
            </div>
          </div>
          <p className="text-sm text-muted-foreground my-4">
            Lançamentos são preservados. Para corrigir valor, data ou descrição, registre um lançamento inverso
            com o motivo; só a categoria pode ser trocada depois.
          </p>
          <FormActions>
            <Button disabled={busy}>{busy ? "Registrando…" : "Registrar lançamento"}</Button>
          </FormActions>
        </form>
      </Card>
      {summary.length > 0 && (
        <Card className="mb-5">
          <h2>Por categoria</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Soma de todos os lançamentos. "Conta no resultado" mostra o que entra no Resultado do negócio da tela
            inicial.
          </p>
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Categoria</th>
                  <th>Entradas</th>
                  <th>Saídas</th>
                  <th>Lançamentos</th>
                  <th>Conta no resultado</th>
                </tr>
              </thead>
              <tbody>
                {summary.map((s) => (
                  <tr key={s.category}>
                    <td data-role="title">{s.category_name}</td>
                    <td data-label="Entradas" className="money text-success">
                      {Number(s.in_total) > 0 ? brl(s.in_total) : "—"}
                    </td>
                    <td data-label="Saídas" className="money text-destructive">
                      {Number(s.out_total) > 0 ? brl(s.out_total) : "—"}
                    </td>
                    <td data-label="Lançamentos">{s.entries}</td>
                    <td data-label="Conta no resultado">{s.is_system ? "—" : s.counts_in_result ? "Sim" : "Não"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2>Movimentações de caixa</h2>
          <select
            aria-label="Filtrar por categoria"
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value);
              setPage(1);
            }}
            className="sm:max-w-xs"
          >
            <option value="">Todas as categorias</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        {!rows ? (
          <p>Carregando…</p>
        ) : !rows.results.length ? (
          <Empty>Nenhum lançamento registrado.</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Descrição</th>
                  <th>Origem</th>
                  <th>Categoria</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                {rows.results.map((r) => (
                  <tr key={r.id}>
                    <td data-label="Data">{r.occurred_on.split("-").reverse().join("/")}</td>
                    <td data-role="title">{r.description}</td>
                    <td data-label="Origem">{originLabels[r.origin] ?? r.origin}</td>
                    <td data-label="Categoria">
                      {r.origin === "manual" ? (
                        <select
                          aria-label={`Categoria de ${r.description}`}
                          value={r.category}
                          onChange={(e) => reclassify(r, e.target.value)}
                        >
                          {/* a categoria atual aparece mesmo sendo "A classificar" ou inativa */}
                          {!choosable(categories, r.direction).some((c) => c.id === r.category) && (
                            <option value={r.category} disabled>
                              {r.category_name}
                            </option>
                          )}
                          {choosable(categories, r.direction).map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name}
                            </option>
                          ))}
                        </select>
                      ) : (
                        r.category_name
                      )}
                    </td>
                    <td
                      data-label="Valor"
                      className={`money ${r.direction === "in" ? "text-success" : "text-destructive"}`}
                    >
                      {r.direction === "in" ? "+" : "−"} {brl(r.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          count={rows?.count || 0}
          noun={["lançamento", "lançamentos"]}
          page={page}
          hasNext={!!rows?.next}
          onPage={setPage}
        />
      </Card>
    </>
  );
}
