"use client";
import { useCallback, useEffect, useState } from "react";
import { api, brl, type Product, type Page } from "@/lib/api";
import { allProducts } from "@/lib/products";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Field } from "@/components/fields";
import { ErrorMessage, Empty } from "@/components/feedback";
import { ProductPicker } from "@/components/product-picker";
import Link from "next/link";
type Movement = {
  id: string;
  product_name: string;
  delta: number;
  balance_after: number;
  reason: string;
  created_at: string;
  value_delta: string | null;
};
export default function Inventory() {
  const [products, setProducts] = useState<Product[]>([]);
  const [rows, setRows] = useState<Page<Movement> | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [delta, setDelta] = useState(0);
  // o produto é estado, e não campo do formulário: form.reset() não limparia
  // o input oculto do seletor de busca
  const [produtoId, setProdutoId] = useState("");
  const load = useCallback(() => {
    Promise.all([allProducts(), api<Page<Movement>>(`movements?page=${page}`)])
      .then(([p, m]) => {
        setProducts(p);
        setRows(m);
      })
      .catch((e) => setError(e.message));
  }, [page]);
  useEffect(load, [load]);
  return (
    <>
      <h1>Estoque</h1>
      <p className="text-muted-foreground mb-7">
        Para reposição, use{" "}
        <Link href="/entradas" className="underline">
          Compras / produção
        </Link>
        . Aqui ficam os ajustes de inventário. Vendas baixam o estoque
        automaticamente.
      </p>
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
            <Field name="reason" label="Motivo" required maxLength={240} />
            <Button disabled={busy || !products.length}>
              {busy ? "Registrando…" : "Registrar movimento"}
            </Button>
          </form>
        </Card>
        <Card>
          <h2>Posição atual</h2>
          <div className="overflow-auto">
            <table>
              <thead>
                <tr>
                  <th>Produto</th>
                  <th>Unidades</th>
                  <th>Valor a custo</th>
                  <th>Custo médio / un.</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id}>
                    <td>{p.name}</td>
                    <td>{p.quantity}</td>
                    <td className="money">{brl(p.stock_value)}</td>
                    <td className="money">
                      {p.quantity ? brl(p.average_cost) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!products.length && <Empty>Nenhum produto cadastrado.</Empty>}
          </div>
        </Card>
      </div>
      <Card className="mt-5">
        <h2>Histórico de movimentações</h2>
        {!rows ? (
          <p>Carregando…</p>
        ) : !rows.results.length ? (
          <Empty>Nenhuma movimentação registrada.</Empty>
        ) : (
          <div className="overflow-auto">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Produto</th>
                  <th>Variação</th>
                  <th>Saldo após</th>
                  <th>Motivo</th>
                  <th>Variação em R$</th>
                </tr>
              </thead>
              <tbody>
                {rows.results.map((m) => (
                  <tr key={m.id}>
                    <td>{new Date(m.created_at).toLocaleString("pt-BR")}</td>
                    <td>{m.product_name}</td>
                    <td>
                      {m.delta > 0 ? "+" : ""}
                      {m.delta}
                    </td>
                    <td>{m.balance_after}</td>
                    <td>{m.reason}</td>
                    <td className="money">
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
        <div className="flex gap-2 mt-4">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Anterior
          </Button>
          <Button
            variant="outline"
            disabled={!rows?.next}
            onClick={() => setPage(page + 1)}
          >
            Próxima
          </Button>
        </div>
      </Card>
    </>
  );
}
