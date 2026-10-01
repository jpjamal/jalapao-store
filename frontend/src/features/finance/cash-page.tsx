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
import { useClientList, useListQuery } from "@/shared/hooks/use-list-query";
import {
  ClearFilters, DateRange, FilterSelect, ListToolbar, SearchBox, SortSelect,
} from "@/shared/components/list-toolbar";
import { SortableTh } from "@/shared/components/sortable-th";
import { type SortColumn } from "@/shared/lib/list";

/* categorias que o dono pode escolher: não são do sistema, estão ativas e combinam com o tipo */
const choosable = (categories: CashCategory[], direction: string) =>
  categories.filter(
    (c) => !c.is_system && c.active && (c.direction === "both" || c.direction === direction),
  );

const cashColumns: SortColumn[] = [
  { key: "occurred_on", label: "Data", kind: "date" },
  { key: "description", label: "Descrição", kind: "text" },
  { key: "category__name", label: "Categoria", kind: "text" },
  { key: "amount", label: "Valor", kind: "number" },
];
const summaryColumns: SortColumn[] = [
  { key: "name", label: "Categoria", kind: "text" },
  { key: "in_total", label: "Entradas", kind: "number" },
  { key: "out_total", label: "Saídas", kind: "number" },
  { key: "entries", label: "Lançamentos", kind: "number" },
];

export default function Cash() {
  const [rows, setRows] = useState<Page<CashEntry> | null>(null);
  const [categories, setCategories] = useState<CashCategory[]>([]);
  const [summary, setSummary] = useState<CashSummaryRow[]>([]);
  // busca, filtros, ordem e página da lista de lançamentos, no servidor (spec 027)
  const q = useListQuery({ direction: "", category: "", origin: "", date_from: "", date_to: "" });
  // o resumo por categoria é curto e já vem inteiro: busca e ordem acontecem na tela
  const summaryList = useClientList(summary, {
    texts: (s) => [s.category_name],
    getters: {
      name: (s) => s.category_name,
      in_total: (s) => s.in_total,
      out_total: (s) => s.out_total,
      entries: (s) => s.entries,
    },
  });
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
  const loadRows = useCallback(() => {
    api<Page<CashEntry>>(`cash?${q.queryString}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [q.queryString]);
  const loadSummary = useCallback(() => {
    api<CashSummaryRow[]>("cash/summary")
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(loadRows, [loadRows]);
  useEffect(loadSummary, [loadSummary]);
  const load = useCallback(() => {
    loadRows();
    loadSummary();
  }, [loadRows, loadSummary]);
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
          <ListToolbar>
            <SearchBox value={summaryList.search} onChange={summaryList.setSearch} placeholder="Nome da categoria…" />
            <SortSelect columns={summaryColumns} sort={summaryList.sort} onChange={summaryList.setSort} />
            <ClearFilters visible={summaryList.hasActiveFilters} onClick={summaryList.clear} />
          </ListToolbar>
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Categoria" sortKey="name" sort={summaryList.sort} onSort={summaryList.toggle} />
                  <SortableTh label="Entradas" sortKey="in_total" sort={summaryList.sort} onSort={summaryList.toggle} />
                  <SortableTh label="Saídas" sortKey="out_total" sort={summaryList.sort} onSort={summaryList.toggle} />
                  <SortableTh label="Lançamentos" sortKey="entries" sort={summaryList.sort} onSort={summaryList.toggle} />
                  <th>Conta no resultado</th>
                </tr>
              </thead>
              <tbody>
                {(summaryList.visible ?? []).map((s) => (
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
        <h2>Movimentações de caixa</h2>
        <ListToolbar>
          <SearchBox value={q.search} onChange={q.setSearch} placeholder="Descrição ou categoria…" />
          <FilterSelect
            label="Tipo"
            value={q.filters.direction}
            onChange={(v) => q.setFilter("direction", v)}
            options={[["in", "Entradas"], ["out", "Saídas"]]}
          />
          <FilterSelect
            label="Categoria"
            value={q.filters.category}
            onChange={(v) => q.setFilter("category", v)}
            options={categories.map((c) => [c.id, c.name])}
            allLabel="Todas"
          />
          <FilterSelect
            label="Origem"
            value={q.filters.origin}
            onChange={(v) => q.setFilter("origin", v)}
            options={Object.entries(originLabels)}
          />
          <DateRange
            from={q.filters.date_from}
            to={q.filters.date_to}
            onFrom={(v) => q.setFilter("date_from", v)}
            onTo={(v) => q.setFilter("date_to", v)}
          />
          <SortSelect columns={cashColumns} sort={q.sort} onChange={q.setSort} />
          <ClearFilters visible={q.hasActiveFilters} onClick={q.clear} />
        </ListToolbar>
        {!rows ? (
          <p>Carregando…</p>
        ) : !rows.results.length ? (
          <Empty>{q.hasActiveFilters ? "Nenhum lançamento encontrado com esses filtros." : "Nenhum lançamento registrado."}</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Data" sortKey="occurred_on" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Descrição" sortKey="description" sort={q.sort} onSort={q.toggleSort} />
                  <th>Origem</th>
                  <SortableTh label="Categoria" sortKey="category__name" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Valor" sortKey="amount" sort={q.sort} onSort={q.toggleSort} />
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
          page={q.page}
          hasNext={!!rows?.next}
          onPage={q.setPage}
        />
      </Card>
    </>
  );
}
