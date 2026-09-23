"use client";
import { useCallback, useEffect, useState } from "react";
import { api, brl, type Page, type Product } from "@/lib/api";
import { allProducts } from "@/lib/products";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/fields";
import { Empty, ErrorMessage } from "@/components/feedback";

type Receipt = {
  id: string;
  product_name: string;
  kind: string;
  quantity: number;
  unit_cost: string;
  total: string;
  occurred_on: string;
  supplier: string;
  reference: string;
  notes: string;
  paid_at: string | null;
};
const today = () => new Date().toLocaleDateString("en-CA");

export default function Receipts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [rows, setRows] = useState<Page<Receipt> | null>(null);
  const [page, setPage] = useState(1);
  const [kind, setKind] = useState("purchase");
  const [productId, setProductId] = useState("");
  const [cost, setCost] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [paying, setPaying] = useState<Receipt | null>(null);
  const load = useCallback(() => {
    Promise.all([allProducts(), api<Page<Receipt>>(`receipts?page=${page}`)])
      .then(([p, r]) => {
        setProducts(p);
        setRows(r);
      })
      .catch((e) => setError(e.message));
  }, [page]);
  useEffect(load, [load]);
  useEffect(() => setKey(crypto.randomUUID()), []);
  return (
    <>
      <h1>Compras e produção</h1>
      <p className="text-muted-foreground mb-7">
        Cada entrada guarda seu próprio custo e atualiza a média do estoque. O
        histórico das vendas é preservado.
      </p>
      <ErrorMessage message={error} />
      {notice && (
        <p role="status" className="text-success mb-4">
          {notice}
        </p>
      )}
      <Card className="mb-5">
        <h2>Nova entrada de estoque</h2>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            setNotice("");
            const form = e.currentTarget;
            const data = new FormData(form);
            try {
              await api("receipts", {
                method: "POST",
                body: JSON.stringify({
                  ...Object.fromEntries(data),
                  idempotency_key: key,
                  quantity: Number(quantity),
                }),
              });
              form.reset();
              setProductId("");
              setCost("");
              setQuantity("1");
              setKey(crypto.randomUUID());
              setNotice(
                "Entrada registrada. Quantidade e custo médio atualizados; o caixa não foi movimentado.",
              );
              load();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <fieldset disabled={busy} className="grid md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="kind">Origem</label>
              <select
                id="kind"
                name="kind"
                value={kind}
                onChange={(e) => setKind(e.target.value)}
              >
                <option value="purchase">Compra de produto</option>
                <option value="production">Produção própria / 3D</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label htmlFor="product_id">Produto</label>
              <select
                id="product_id"
                name="product_id"
                value={productId}
                required
                onChange={(e) => {
                  setProductId(e.target.value);
                  setCost(
                    products.find((p) => p.id === e.target.value)?.cost_price ||
                      "",
                  );
                }}
              >
                <option value="">Selecione…</option>
                {products
                  .filter((p) => p.active)
                  .map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} — {p.quantity} un.
                    </option>
                  ))}
              </select>
            </div>
            <div>
              <label htmlFor="quantity">Quantidade</label>
              <Input
                id="quantity"
                name="quantity"
                type="number"
                min="1"
                max="1000000"
                step="1"
                required
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="unit_cost">Custo por unidade (R$)</label>
              <Input
                id="unit_cost"
                name="unit_cost"
                type="number"
                min="0"
                step="0.01"
                required
                value={cost}
                onChange={(e) => setCost(e.target.value)}
              />
            </div>
            <Field
              name="occurred_on"
              label="Data da entrada"
              type="date"
              value={today()}
              max={today()}
              required
            />
            <Field
              name="supplier"
              label="Fornecedor / responsável (opcional)"
              maxLength={200}
            />
            <Field
              name="reference"
              label="Nota / lote / referência (opcional)"
              maxLength={100}
            />
            <Field name="notes" label="Observação (opcional)" maxLength={500} />
          </fieldset>
          <p className="my-4 font-semibold">
            Total da entrada: {brl(Number(cost) * Number(quantity))}
          </p>
          <p className="text-sm text-muted-foreground mb-4">
            Confira o custo sugerido pelo cadastro e informe o valor real deste
            lote.{" "}
            {kind === "purchase"
              ? "Inclua no custo os gastos de aquisição que quiser atribuir ao produto. Após registrar, marque a compra como paga quando houver a saída do dinheiro."
              : "Informe o custo de produzir cada unidade. Materiais e energia já pagos não devem ser lançados novamente no caixa."}{" "}
            A data é informativa: a média muda no momento do registro.
          </p>
          <Button disabled={busy || !key || !products.length}>
            {busy ? "Registrando…" : "Registrar entrada"}
          </Button>
        </form>
      </Card>
      {paying && (
        <Card className="mb-5">
          <h2>Pagar compra: {paying.product_name}</h2>
          <p className="mb-4">
            Saída de {brl(paying.total)} do caixa. Use somente se este pagamento
            ainda não foi lançado manualmente.
          </p>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              setError("");
              const data = Object.fromEntries(new FormData(e.currentTarget));
              try {
                await api(`receipts/${paying.id}/pay`, {
                  method: "POST",
                  body: JSON.stringify(data),
                });
                setPaying(null);
                setNotice(
                  "Compra paga. Saída registrada no caixa uma única vez.",
                );
                load();
              } catch (err) {
                setError((err as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <Field
              name="occurred_on"
              id="payment_date"
              label="Data do pagamento"
              type="date"
              value={today()}
              max={today()}
              required
            />
            <div className="flex gap-2 mt-4">
              <Button disabled={busy}>Confirmar pagamento</Button>
              <Button
                type="button"
                variant="outline"
                disabled={busy}
                onClick={() => setPaying(null)}
              >
                Voltar
              </Button>
            </div>
          </form>
        </Card>
      )}
      <Card>
        <h2>Histórico de entradas</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Um registro por produto. Use a mesma referência para itens da mesma
          compra. Entradas são preservadas; correções de quantidade ficam nos
          ajustes de estoque.
        </p>
        {!rows ? (
          <p>Carregando…</p>
        ) : !rows.results.length ? (
          <Empty>Nenhuma compra ou produção registrada.</Empty>
        ) : (
          <div className="overflow-auto">
            <table>
              <thead>
                <tr>
                  <th>Data / origem</th>
                  <th>Produto / referência</th>
                  <th>Quantidade</th>
                  <th>Custo unitário</th>
                  <th>Total</th>
                  <th>Pagamento</th>
                </tr>
              </thead>
              <tbody>
                {rows.results.map((r) => (
                  <tr key={r.id}>
                    <td>
                      {r.occurred_on.split("-").reverse().join("/")}
                      <br />
                      {r.kind === "purchase" ? "Compra" : "Produção"}
                    </td>
                    <td>
                      {r.product_name}
                      <div className="text-xs text-muted-foreground">
                        {[r.supplier, r.reference, r.notes]
                          .filter(Boolean)
                          .join(" · ")}
                      </div>
                    </td>
                    <td>{r.quantity}</td>
                    <td className="money">{brl(r.unit_cost)}</td>
                    <td className="money">{brl(r.total)}</td>
                    <td>
                      {r.kind === "production" ? (
                        "Sem saída automática"
                      ) : r.paid_at ? (
                        "Paga"
                      ) : (
                        <Button
                          variant="outline"
                          disabled={busy}
                          onClick={() => setPaying(r)}
                        >
                          Pagar {brl(r.total)}
                        </Button>
                      )}
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
