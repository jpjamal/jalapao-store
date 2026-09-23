"use client";
import { useCallback, useEffect, useState } from "react";
import { api, brl, type Product, type Page, type Printing } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ErrorMessage, Empty } from "@/components/feedback";
import { Field, MoneyField } from "@/components/fields";

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
  done,
  cancel,
}: {
  product: Product | null;
  done: () => void;
  cancel: () => void;
}) {
  const [kind, setKind] = useState(product?.kind || "resale");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const profile = product?.printing || defaults;
  return (
    <Card className="mb-6">
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
            sku: f.get("sku"),
            description: f.get("description"),
            kind,
            active: f.get("active") === "on",
          };
          if (kind === "printing") {
            payload.printing = Object.fromEntries(
              Object.keys(defaults).map((k) => [k, f.get(k)]),
            );
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
          <Field
            name="sku"
            label="Código (SKU)"
            value={product?.sku}
            required
            maxLength={80}
          />
          <div>
            <label htmlFor="kind">Tipo</label>
            <select
              id="kind"
              value={kind}
              onChange={(e) => setKind(e.target.value)}
            >
              <option value="resale">Revenda</option>
              <option value="printing">Impressão 3D</option>
            </select>
          </div>
          <div className="md:col-span-3">
            <Field
              name="description"
              label="Descrição"
              value={product?.description}
            />
          </div>
        </div>
        {kind === "printing" ? (
          <>
            <p className="my-4 text-muted-foreground">
              Custo e preço sugerido são calculados a partir dos parâmetros
              abaixo. Margem é o acréscimo sobre o custo.
            </p>
            <div className="grid md:grid-cols-3 gap-4">
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
        <div className="flex gap-3">
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
        </div>
      </form>
    </Card>
  );
}
export default function Products() {
  const [data, setData] = useState<Page<Product> | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Product | null | undefined>(undefined);
  const load = useCallback(() => {
    setError("");
    api<Page<Product>>(
      `products?search=${encodeURIComponent(search)}&page=${page}`,
    )
      .then(setData)
      .catch((e) => setError(e.message));
  }, [search, page]);
  useEffect(load, [load]);
  return (
    <>
      <div className="flex justify-between items-start gap-4">
        <div>
          <h1>Produtos</h1>
          <p className="text-muted-foreground mb-7">
            O custo de referência sugere novas compras ou produções. Alterá-lo não muda o estoque já adquirido.
          </p>
        </div>
        <Button onClick={() => setEditing(null)}>Novo produto</Button>
      </div>
      <ErrorMessage message={error} />
      {editing !== undefined && (
        <ProductForm
          key={editing?.id || "new"}
          product={editing}
          done={() => {
            setEditing(undefined);
            load();
          }}
          cancel={() => setEditing(undefined)}
        />
      )}
      <Card>
        <Input
          aria-label="Buscar produtos"
          placeholder="Buscar por nome ou código…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="max-w-md mb-5"
        />
        {!data ? (
          <p role="status">Carregando catálogo…</p>
        ) : !data.results.length ? (
          <Empty>Nenhum produto encontrado.</Empty>
        ) : (
          <div className="overflow-auto">
            <table>
              <thead>
                <tr>
                  <th>Produto</th>
                  <th>Tipo</th>
                  <th>Custo de referência</th>
                  <th>Preço</th>
                  <th>Estoque</th>
                  <th>Status</th>
                  <th>
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <strong>{p.name}</strong>
                      <p className="text-xs text-muted-foreground">{p.sku}</p>
                    </td>
                    <td>
                      {p.kind === "printing" ? "Impressão 3D" : "Revenda"}
                    </td>
                    <td className="money">{brl(p.cost_price)}</td>
                    <td className="money">{brl(p.sale_price)}</td>
                    <td>{p.quantity}</td>
                    <td>{p.active ? "Ativo" : "Inativo"}</td>
                    <td>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditing(p)}
                      >
                        Editar
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="flex justify-between items-center mt-5 text-sm">
          <span>{data?.count || 0} produtos</span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              disabled={!data?.next}
              onClick={() => setPage(page + 1)}
            >
              Próxima
            </Button>
          </div>
        </div>
      </Card>
    </>
  );
}
