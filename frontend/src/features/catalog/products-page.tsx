"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/shared/api/client";
import { brl } from "@/shared/lib/format";
import { type Category, type Product, type Printing } from "@/features/catalog/types";
import { FilamentLines, type FilamentLine } from "@/features/catalog/components/filament-lines";
import { allSupplies } from "@/features/supplies/api";
import { type Supply } from "@/features/supplies/types";
import { type Page } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { useListQuery } from "@/shared/hooks/use-list-query";
import { ClearFilters, FilterSelect, ListToolbar, SearchBox, SortSelect } from "@/shared/components/list-toolbar";
import { SortableTh } from "@/shared/components/sortable-th";
import { type SortColumn } from "@/shared/lib/list";
import { FormActions } from "@/shared/components/form-actions";
import { PageHeader } from "@/shared/components/page-header";
import { Pagination } from "@/shared/components/pagination";
import { Card } from "@/shared/ui/card";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { Field, MoneyField } from "@/shared/components/fields";
import { StockQuantity, linhaDeEstoque } from "@/shared/components/stock-quantity";

const defaults: Printing = {
  filament_price_kg: "115",
  weight_g: "45",
  power_w: "200",
  hours: 0,
  minutes: 0,
  energy_price_kwh: "1.56",
  labor_cost: "0",
  fixed_cost: "0",
  markup_percent: "100",
};
function ProductForm({
  product,
  categories,
  done,
  cancel,
}: {
  product: Product | null;
  categories: Category[];
  done: () => void;
  cancel: () => void;
}) {
  // ativas para escolher; a categoria atual do produto continua aparecendo mesmo se foi desativada
  const options = categories.filter((c) => c.active || c.id === product?.category);
  // produto novo começa na categoria comum mais antiga, a mesma que o backend usa sem escolha
  const padrao = options
    .filter((c) => !c.uses_printing_profile)
    .sort((a, b) => a.created_at.localeCompare(b.created_at))[0];
  const [categoryId, setCategoryId] = useState(
    product?.category || padrao?.id || options[0]?.id || "",
  );
  const usesPrinting = !!categories.find((c) => c.id === categoryId)?.uses_printing_profile;
  // filamentos da peça multicolor (spec 024); sem linhas vale o preço por kg e o peso digitados
  const [lines, setLines] = useState<FilamentLine[]>(() =>
    (product?.printing?.filaments || []).map((l) => ({
      uid: crypto.randomUUID(),
      filament: l.filament,
      grams: String(Number(l.grams)),
      roll_price: l.roll_price,
      roll_weight_g: l.roll_weight_g,
      outdated: l.price_outdated,
      refresh: false,
    })),
  );
  const [supplies, setSupplies] = useState<Supply[]>([]);
  useEffect(() => {
    allSupplies()
      .then(setSupplies)
      .catch(() => setSupplies([]));
  }, []);
  const withLines = lines.length > 0;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const profile = product?.printing || defaults;
  // o formulário abre no topo da página: com a lista longa, leva a tela até ele
  useEffect(() => {
    document.getElementById("form-produto")?.scrollIntoView({ block: "start" });
  }, []);
  return (
    <Card id="form-produto" className="mb-6">
      <h2>{product ? "Editar produto" : "Novo produto"}</h2>
      <ErrorMessage message={error} />
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          const f = new FormData(e.currentTarget);
          const payload: Record<string, unknown> = {
            name: f.get("name"),
            gtin: f.get("gtin"),
            category: categoryId,
            brand: f.get("brand"),
            model: f.get("model"),
            // nome próprio no formulário: "weight_g" já é o filamento nos parâmetros 3D
            weight_g: f.get("product_weight_g") || null,
            description: f.get("description"),
            active: f.get("active") === "on",
          };
          if (usesPrinting) {
            // com linhas, o peso e o preço por kg vêm delas e o servidor calcula
            const manual = Object.keys(defaults).filter(
              (k) => !(withLines && ["weight_g", "filament_price_kg"].includes(k)),
            );
            payload.printing = {
              ...Object.fromEntries(manual.map((k) => [k, f.get(k)])),
              filaments: lines.map((l) => ({
                filament: l.filament,
                grams: l.grams,
                refresh_price: l.refresh,
              })),
            };
          } else {
            payload.cost_price = f.get("cost_price");
            payload.sale_price = f.get("sale_price");
          }
          try {
            await api(`products${product ? `/${product.id}` : ""}`, {
              method: product ? "PATCH" : "POST",
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
        <div className="grid md:grid-cols-3 gap-4">
          <Field
            name="name"
            label="Nome do produto"
            value={product?.name}
            required
            maxLength={200}
          />
          <div>
            <label>Código (SKU)</label>
            <p className="mt-2 text-sm text-muted-foreground">
              {product?.sku || "Gerado automaticamente ao salvar"}
            </p>
          </div>
          <div>
            <label htmlFor="category">Categoria</label>
            <select
              id="category"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              required
            >
              {options.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                  {c.active ? "" : " (inativa)"}
                </option>
              ))}
            </select>
          </div>
          <Field
            name="brand"
            label="Marca"
            value={product?.brand}
            maxLength={100}
          />
          <Field
            name="model"
            label="Modelo"
            value={product?.model}
            maxLength={100}
          />
          <Field
            name="product_weight_g"
            label="Peso do produto (g)"
            type="number"
            min="0"
            step="0.001"
            value={product?.weight_g ?? ""}
          />
          <Field
            name="gtin"
            label="Código de barras (GTIN/EAN) — opcional"
            value={product?.gtin ?? ""}
            inputMode="numeric"
            maxLength={30}
            placeholder="8, 12, 13 ou 14 dígitos"
          />
          <div className="md:col-span-3">
            <Field
              name="description"
              label="Descrição"
              value={product?.description}
            />
          </div>
        </div>
        {usesPrinting ? (
          <>
            <p className="my-4 text-muted-foreground">
              Custo e preço sugerido são calculados a partir dos parâmetros
              abaixo. Margem é o acréscimo sobre o custo.
            </p>
            <FilamentLines lines={lines} onChange={setLines} supplies={supplies} />
            <div className="grid md:grid-cols-3 gap-4">
              {withLines ? (
                <p className="md:col-span-3 text-sm text-muted-foreground">
                  Peso e custo do filamento vêm das linhas de filamento acima.
                </p>
              ) : (
                <>
                  <MoneyField
                    name="filament_price_kg"
                    label="Filamento (R$/kg)"
                    value={profile.filament_price_kg}
                  />
                  <Field
                    name="weight_g"
                    label="Peso (g)"
                    value={profile.weight_g}
                    type="number"
                    min="0.001"
                    step="0.001"
                    required
                  />
                </>
              )}
              <MoneyField
                name="power_w"
                label="Potência (W)"
                value={profile.power_w}
              />
              <Field
                name="hours"
                label="Horas"
                type="number"
                min="0"
                step="1"
                value={profile.hours}
                required
              />
              <Field
                name="minutes"
                label="Minutos"
                type="number"
                min="0"
                max="59"
                step="1"
                value={profile.minutes}
                required
              />
              <Field
                name="energy_price_kwh"
                label="Energia (R$/kWh)"
                type="number"
                min="0"
                step="0.0001"
                value={profile.energy_price_kwh}
                required
              />
              <MoneyField
                name="labor_cost"
                label="Mão de obra (R$)"
                value={profile.labor_cost}
              />
              <MoneyField
                name="fixed_cost"
                label="Custo fixo (R$)"
                value={profile.fixed_cost}
              />
              <MoneyField
                name="markup_percent"
                label="Acréscimo sobre custo (%)"
                value={profile.markup_percent}
              />
            </div>
          </>
        ) : (
          <div className="grid md:grid-cols-2 gap-4 mt-4">
            <MoneyField
              name="cost_price"
              label="Custo de referência (R$)"
              value={product?.cost_price}
            />
            <MoneyField
              name="sale_price"
              label="Preço de venda (R$)"
              value={product?.sale_price}
            />
          </div>
        )}
        <label className="flex items-center gap-2 my-5">
          <input
            type="checkbox"
            name="active"
            defaultChecked={product?.active ?? true}
          />
          Produto ativo
        </label>
        <FormActions>
          <Button disabled={busy}>
            {busy ? "Salvando…" : "Salvar produto"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={cancel}
            disabled={busy}
          >
            Cancelar
          </Button>
        </FormActions>
      </form>
    </Card>
  );
}
const productColumns: SortColumn[] = [
  { key: "name", label: "Produto", kind: "text" },
  { key: "category__name", label: "Categoria", kind: "text" },
  { key: "cost_price", label: "Custo de referência", kind: "number" },
  { key: "sale_price", label: "Preço", kind: "number" },
  { key: "stock__quantity", label: "Estoque", kind: "number" },
  { key: "active", label: "Status", kind: "text" },
];

export default function Products() {
  const [data, setData] = useState<Page<Product> | null>(null);
  const [error, setError] = useState("");
  // busca, filtros, ordem e página (spec 027): a ordem e os filtros valem para a lista inteira, no servidor
  const q = useListQuery({ category: "", active: "", in_stock: "" });
  const [editing, setEditing] = useState<Product | null | undefined>(undefined);
  const [categories, setCategories] = useState<Category[] | null>(null);
  useEffect(() => {
    api<Page<Category>>("categories")
      .then((r) => setCategories(r.results))
      .catch((e) => setError(e.message));
  }, []);
  const load = useCallback(() => {
    setError("");
    api<Page<Product>>(`products?${q.queryString}`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [q.queryString]);
  useEffect(load, [load]);
  return (
    <>
      <PageHeader
        title="Produtos"
        description="O custo de referência sugere novas compras ou produções. Alterá-lo não muda o estoque já adquirido."
        actions={<Button onClick={() => setEditing(null)}>Novo produto</Button>}
      />
      <ErrorMessage message={error} />
      {editing !== undefined && categories && (
        <ProductForm
          key={editing?.id || "new"}
          product={editing}
          categories={categories}
          done={() => {
            setEditing(undefined);
            load();
          }}
          cancel={() => setEditing(undefined)}
        />
      )}
      <Card>
        <ListToolbar>
          <SearchBox
            value={q.search}
            onChange={q.setSearch}
            placeholder="Nome, código, marca, modelo ou categoria…"
          />
          <FilterSelect
            label="Categoria"
            value={q.filters.category}
            onChange={(v) => q.setFilter("category", v)}
            options={(categories || []).map((c) => [c.id, c.name])}
            allLabel="Todas"
          />
          <FilterSelect
            label="Situação"
            value={q.filters.active}
            onChange={(v) => q.setFilter("active", v)}
            options={[["true", "Ativos"], ["false", "Inativos"]]}
          />
          <FilterSelect
            label="Estoque"
            value={q.filters.in_stock}
            onChange={(v) => q.setFilter("in_stock", v)}
            options={[["true", "Com saldo"], ["false", "Sem saldo"]]}
          />
          <SortSelect columns={productColumns} sort={q.sort} onChange={q.setSort} />
          <ClearFilters visible={q.hasActiveFilters} onClick={q.clear} />
        </ListToolbar>
        {!data ? (
          <p role="status">Carregando catálogo…</p>
        ) : !data.results.length ? (
          <Empty>Nenhum produto encontrado.</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Produto" sortKey="name" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Categoria" sortKey="category__name" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Custo de referência" sortKey="cost_price" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Preço" sortKey="sale_price" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Estoque" sortKey="stock__quantity" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Status" sortKey="active" sort={q.sort} onSort={q.toggleSort} />
                  <th>
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((p) => (
                  <tr key={p.id} className={linhaDeEstoque(p.quantity)}>
                    <td data-role="title">
                      <strong>{p.name}</strong>
                      <p className="text-xs text-muted-foreground font-normal">
                        {p.sku}
                        {p.gtin ? ` · ${p.gtin}` : ""}
                      </p>
                      {(p.brand || p.model) && (
                        <p className="text-xs text-muted-foreground font-normal">
                          {[p.brand, p.model].filter(Boolean).join(" ")}
                        </p>
                      )}
                    </td>
                    <td data-label="Categoria">{p.category_name}</td>
                    <td data-label="Custo de referência" className="money">{brl(p.cost_price)}</td>
                    <td data-label="Preço" className="money">{brl(p.sale_price)}</td>
                    <td data-label="Estoque"><StockQuantity quantity={p.quantity} /></td>
                    <td data-label="Status">{p.active ? "Ativo" : "Inativo"}</td>
                    <td data-role="actions">
                      <div className="flex flex-wrap items-center justify-end md:justify-start gap-x-3 gap-y-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditing(p)}
                      >
                        Editar
                      </Button>
                      <Link className="text-sm underline py-2" href={`/anuncios?product=${p.id}`}>
                        Fotos e anúncios
                      </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          count={data?.count || 0}
          noun={["produto", "produtos"]}
          page={q.page}
          hasNext={!!data?.next}
          onPage={q.setPage}
        />
      </Card>
    </>
  );
}
