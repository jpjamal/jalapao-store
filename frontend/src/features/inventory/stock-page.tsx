"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { brl } from "@/shared/lib/format";
import { type Product } from "@/features/catalog/types";
import { type Page } from "@/shared/api/types";
import { allProducts } from "@/features/catalog/api";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { Field } from "@/shared/components/fields";
import { Input } from "@/shared/ui/input";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { FormActions } from "@/shared/components/form-actions";
import { PageHeader } from "@/shared/components/page-header";
import { Pagination } from "@/shared/components/pagination";
import { ProductPicker } from "@/features/catalog/components/product-picker";
import Link from "next/link";
import { useClientList, useListQuery } from "@/shared/hooks/use-list-query";
import {
  ClearFilters, DateRange, FilterSelect, ListToolbar, SearchBox, SortSelect,
} from "@/shared/components/list-toolbar";
import { SortableTh } from "@/shared/components/sortable-th";
import { type SortColumn } from "@/shared/lib/list";
type Movement = {
  id: string;
  product_name: string;
  delta: number;
  balance_after: number;
  reason: string;
  created_at: string;
  value_delta: string | null;
};
// Motivos mais comuns de ajuste manual; o campo continua aceitando texto livre.
const MOTIVOS = [
  "Compra / reposição",
  "Produção 3D",
  "Contagem de inventário",
  "Perda / defeito",
  "Devolução",
];

const positionColumns: SortColumn[] = [
  { key: "name", label: "Produto", kind: "text" },
  { key: "quantity", label: "Unidades", kind: "number" },
  { key: "stock_value", label: "Valor a custo", kind: "number" },
  { key: "average_cost", label: "Custo médio / un.", kind: "number" },
];
const movementColumns: SortColumn[] = [
  { key: "created_at", label: "Data", kind: "date" },
  { key: "product__name", label: "Produto", kind: "text" },
  { key: "delta", label: "Variação", kind: "number" },
  { key: "balance_after", label: "Saldo após", kind: "number" },
  { key: "value_delta", label: "Variação em R$", kind: "number" },
];

export default function Inventory() {
  const [products, setProducts] = useState<Product[]>([]);
  const [rows, setRows] = useState<Page<Movement> | null>(null);
  // histórico: paginado, então busca, filtros e ordem vão ao servidor (spec 027)
  const q = useListQuery({ direction: "", date_from: "", date_to: "" });
  // posição atual: todos os produtos já estão carregados, então busca e ordem acontecem na tela
  const position = useClientList(products, {
    texts: (p) => [p.name, p.sku, p.category_name, p.brand, p.model],
    filters: {
      category: (p, v) => p.category === v,
      balance: (p, v) => (v === "with" ? p.quantity > 0 : p.quantity === 0),
    },
    getters: {
      name: (p) => p.name,
      quantity: (p) => p.quantity,
      stock_value: (p) => p.stock_value,
      average_cost: (p) => (p.quantity ? p.average_cost : null),
    },
  });
  const categoryOptions = Array.from(new Map(products.map((p) => [p.category, p.category_name])).entries());
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [delta, setDelta] = useState(0);
  // o produto é estado, e não campo do formulário: form.reset() não limparia
  // o input oculto do seletor de busca
  const [produtoId, setProdutoId] = useState("");
  const [motivo, setMotivo] = useState("");
  const loadProducts = useCallback(() => {
    allProducts()
      .then(setProducts)
      .catch((e) => setError(e.message));
  }, []);
  const loadMovements = useCallback(() => {
    api<Page<Movement>>(`movements?${q.queryString}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [q.queryString]);
  useEffect(loadProducts, [loadProducts]);
  useEffect(loadMovements, [loadMovements]);
  const load = useCallback(() => {
    loadProducts();
    loadMovements();
  }, [loadProducts, loadMovements]);
  return (
    <>
      <PageHeader
        title="Estoque"
        description={<>
          Para reposição, use{" "}
          <Link href="/entradas" className="underline">Compras / produção</Link>. Aqui ficam os
          ajustes de inventário. Vendas baixam o estoque automaticamente.
        </>}
      />
      <ErrorMessage message={error} />
      {notice && (
        <p role="status" className="text-success mb-4">
          {notice}
        </p>
      )}
      <div className="grid xl:grid-cols-[1fr_2fr] gap-5">
        <Card>
          <h2>Ajustar inventário</h2>
          <form
            className="space-y-4"
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              setError("");
              setNotice("");
              const form = e.currentTarget;
              const f = new FormData(form);
              try {
                await api("movements", {
                  method: "POST",
                  body: JSON.stringify({
                    product: produtoId,
                    delta: Number(f.get("delta")),
                    reason: f.get("reason"),
                    ...(delta > 0 ? { unit_cost: f.get("unit_cost") } : {}),
                  }),
                });
                setNotice("Movimentação registrada.");
                form.reset();
                setDelta(0);
                setMotivo("");
                setProdutoId("");
                load();
              } catch (err) {
                setError((err as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <div>
              <label htmlFor="product">Produto</label>
              <ProductPicker
                id="product"
                required
                products={products}
                value={produtoId}
                onChange={(id) => setProdutoId(id)}
                somenteAtivos={false}
              />
            </div>
            <Field
              name="delta"
              label="Quantidade (+ entrada / − saída)"
              type="number"
              step="1"
              required
              onChange={(e) => setDelta(Number(e.target.value))}
            />
            {delta > 0 && (
              <Field
                name="unit_cost"
                label="Custo unitário da entrada (R$)"
                type="number"
                min="0"
                step="0.01"
                required
              />
            )}
            <p className="text-sm text-muted-foreground">
              Ajustes não movimentam caixa. Saídas usam o custo médio; entradas
              exigem o custo conhecido.
            </p>
            <div>
              <label htmlFor="reason">Motivo</label>
              <div className="flex flex-wrap gap-2 mb-2">
                {MOTIVOS.map((m) => (
                  <button
                    key={m}
                    type="button"
                    aria-pressed={motivo === m}
                    className={`rounded-full border px-4 min-h-10 sm:min-h-8 text-sm cursor-pointer hover:bg-muted ${
                      motivo === m ? "border-primary bg-muted" : ""
                    }`}
                    onClick={() => setMotivo(m)}
                  >
                    {m}
                  </button>
                ))}
              </div>
              <Input
                id="reason"
                name="reason"
                required
                maxLength={240}
                placeholder="Escolha acima ou escreva"
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
              />
            </div>
            <FormActions>
              <Button disabled={busy || !products.length}>
                {busy ? "Registrando…" : "Registrar movimento"}
              </Button>
            </FormActions>
          </form>
        </Card>
        <Card>
          <h2>Posição atual</h2>
          <ListToolbar>
            <SearchBox
              value={position.search}
              onChange={position.setSearch}
              placeholder="Nome, código, marca ou categoria…"
            />
            <FilterSelect
              label="Categoria"
              value={position.filters.category ?? ""}
              onChange={(v) => position.setFilter("category", v)}
              options={categoryOptions}
              allLabel="Todas"
            />
            <FilterSelect
              label="Saldo"
              value={position.filters.balance ?? ""}
              onChange={(v) => position.setFilter("balance", v)}
              options={[["with", "Com saldo"], ["without", "Sem saldo"]]}
            />
            <SortSelect columns={positionColumns} sort={position.sort} onChange={position.setSort} />
            <ClearFilters visible={position.hasActiveFilters} onClick={position.clear} />
          </ListToolbar>
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Produto" sortKey="name" sort={position.sort} onSort={position.toggle} />
                  <SortableTh label="Unidades" sortKey="quantity" sort={position.sort} onSort={position.toggle} />
                  <SortableTh label="Valor a custo" sortKey="stock_value" sort={position.sort} onSort={position.toggle} />
                  <SortableTh label="Custo médio / un." sortKey="average_cost" sort={position.sort} onSort={position.toggle} />
                </tr>
              </thead>
              <tbody>
                {(position.visible ?? []).map((p) => (
                  <tr key={p.id}>
                    <td data-role="title">{p.name}</td>
                    <td data-label="Unidades">{p.quantity}</td>
                    <td data-label="Valor a custo" className="money">{brl(p.stock_value)}</td>
                    <td data-label="Custo médio / un." className="money">
                      {p.quantity ? brl(p.average_cost) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!products.length && <Empty>Nenhum produto cadastrado.</Empty>}
            {products.length > 0 && !position.visible?.length && (
              <Empty>Nenhum produto encontrado com esses filtros.</Empty>
            )}
          </div>
        </Card>
      </div>
      <Card className="mt-5">
        <h2>Histórico de movimentações</h2>
        <ListToolbar>
          <SearchBox value={q.search} onChange={q.setSearch} placeholder="Produto, código ou motivo…" />
          <FilterSelect
            label="Tipo"
            value={q.filters.direction}
            onChange={(v) => q.setFilter("direction", v)}
            options={[["in", "Entradas"], ["out", "Saídas"]]}
          />
          <DateRange
            from={q.filters.date_from}
            to={q.filters.date_to}
            onFrom={(v) => q.setFilter("date_from", v)}
            onTo={(v) => q.setFilter("date_to", v)}
          />
          <SortSelect columns={movementColumns} sort={q.sort} onChange={q.setSort} />
          <ClearFilters visible={q.hasActiveFilters} onClick={q.clear} />
        </ListToolbar>
        {!rows ? (
          <p>Carregando…</p>
        ) : !rows.results.length ? (
          <Empty>{q.hasActiveFilters ? "Nenhuma movimentação encontrada com esses filtros." : "Nenhuma movimentação registrada."}</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Data" sortKey="created_at" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Produto" sortKey="product__name" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Variação" sortKey="delta" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Saldo após" sortKey="balance_after" sort={q.sort} onSort={q.toggleSort} />
                  <th>Motivo</th>
                  <SortableTh label="Variação em R$" sortKey="value_delta" sort={q.sort} onSort={q.toggleSort} />
                </tr>
              </thead>
              <tbody>
                {rows.results.map((m) => (
                  <tr key={m.id}>
                    <td data-label="Data">{new Date(m.created_at).toLocaleString("pt-BR")}</td>
                    <td data-role="title">{m.product_name}</td>
                    <td data-label="Variação">
                      {m.delta > 0 ? "+" : ""}
                      {m.delta}
                    </td>
                    <td data-label="Saldo após">{m.balance_after}</td>
                    <td data-label="Motivo">{m.reason}</td>
                    <td data-label="Variação em R$" className="money">
                      {m.value_delta === null
                        ? "Anterior ao controle de custos"
                        : brl(m.value_delta)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          count={rows?.count || 0}
          noun={["movimentação", "movimentações"]}
          page={q.page}
          hasNext={!!rows?.next}
          onPage={q.setPage}
        />
      </Card>
    </>
  );
}
