"use client";
import { useCallback, useEffect, useState } from "react";
import { api, brl, type Product, type Page } from "@/lib/api";
import { allProducts } from "@/lib/products";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field, MoneyField } from "@/components/fields";
import { ErrorMessage, Empty } from "@/components/feedback";
import { ProductPicker } from "@/components/product-picker";
type Item = { product_name: string; quantity: number; unit_price: string };
type Sale = {
  id: string;
  created_at: string;
  channel: string;
  reference: string;
  gross: string;
  net: string;
  profit: string;
  status: string;
  received_at: string | null;
  items: Item[];
};
type Draft = { product_id: string; quantity: number; unit_price: string };
const channels: Record<string, string> = {
  direct: "Boca a boca",
  mercado_livre: "Mercado Livre",
  shopee: "Shopee",
  other: "Outro",
};
export default function Sales() {
  const [products, setProducts] = useState<Product[]>([]);
  const [rows, setRows] = useState<Page<Sale> | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const [key, setKey] = useState(() => crypto.randomUUID());
  const [items, setItems] = useState<Draft[]>([
    { product_id: "", quantity: 1, unit_price: "0" },
  ]);
  const load = useCallback(() => {
    Promise.all([allProducts(), api<Page<Sale>>(`sales?page=${page}`)])
      .then(([p, r]) => {
        setProducts(p);
        setRows(r);
      })
      .catch((e) => setError(e.message));
  }, [page]);
  useEffect(load, [load]);
  function update(index: number, patch: Partial<Draft>) {
    setItems(items.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }
  async function action(id: string, kind: "receive" | "cancel") {
    if (
      kind === "cancel" &&
      !window.confirm(
        "Cancelar esta venda, repor o estoque e estornar eventual recebimento?",
      )
    )
      return;
    setBusy(true);
    setError("");
    try {
      await api(`sales/${id}/${kind}`, { method: "POST", body: "{}" });
      setNotice(
        kind === "receive"
          ? "Recebimento registrado."
          : "Venda cancelada e estoque reposto.",
      );
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="flex justify-between gap-4">
        <div>
          <h1>Vendas</h1>
          <p className="text-muted-foreground mb-7">
            Da saída do produto ao dinheiro recebido.
          </p>
        </div>
        <Button onClick={() => setOpen(!open)}>
          {open ? "Fechar formulário" : "Nova venda"}
        </Button>
      </div>
      <ErrorMessage message={error} />
      {notice && (
        <p role="status" className="text-success mb-4">
          {notice}
        </p>
      )}
      {open && (
        <Card className="mb-5">
          <h2>Registrar venda</h2>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              setError("");
              const form = e.currentTarget;
              const data = Object.fromEntries(new FormData(form));
              try {
                await api("sales", {
                  method: "POST",
                  body: JSON.stringify({
                    ...data,
                    items,
                    idempotency_key: key,
                  }),
                });
                setNotice(
                  "Venda registrada. O estoque foi atualizado; marque como recebida quando o dinheiro entrar.",
                );
                setOpen(false);
                setItems([{ product_id: "", quantity: 1, unit_price: "0" }]);
                setKey(crypto.randomUUID());
                load();
              } catch (err) {
                setError((err as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            <div className="grid md:grid-cols-2 gap-4 mb-5">
              <div>
                <label htmlFor="channel">Canal de venda</label>
                <select id="channel" name="channel">
                  {Object.entries(channels).map(([v, l]) => (
                    <option key={v} value={v}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
              <Field
                name="reference"
                label="Referência / número do pedido"
                maxLength={100}
              />
            </div>
            <div className="space-y-3">
              {items.map((item, index) => (
                <div
                  key={index}
                  className="grid md:grid-cols-[2fr_1fr_1fr_auto] gap-3 items-end border-b pb-4"
                >
                  <div>
                    <label htmlFor={`item-${index}`}>Produto</label>
                    <ProductPicker
                      id={`item-${index}`}
                      required
                      products={products}
                      value={item.product_id}
                      onChange={(id, p) =>
                        update(index, {
                          product_id: id,
                          unit_price: p?.sale_price || "0",
                        })
                      }
                    />
                  </div>
                  <div>
                    <label htmlFor={`qty-${index}`}>Quantidade</label>
                    <Input
                      id={`qty-${index}`}
                      type="number"
                      min="1"
                      step="1"
                      required
                      value={item.quantity}
                      onChange={(e) =>
                        update(index, { quantity: Number(e.target.value) })
                      }
                    />
                  </div>
                  <div>
                    <label htmlFor={`price-${index}`}>
                      Preço unitário (R$)
                    </label>
                    <Input
                      id={`price-${index}`}
                      type="number"
                      min="0"
                      step="0.01"
                      required
                      value={item.unit_price}
                      onChange={(e) =>
                        update(index, { unit_price: e.target.value })
                      }
                    />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    disabled={items.length === 1}
                    onClick={() =>
                      setItems(items.filter((_, i) => i !== index))
                    }
                  >
                    Remover
                  </Button>
                </div>
              ))}
            </div>
            <Button
              type="button"
              variant="outline"
              className="my-4"
              onClick={() =>
                setItems([
                  ...items,
                  { product_id: "", quantity: 1, unit_price: "0" },
                ])
              }
            >
              Adicionar item
            </Button>
            <div className="grid md:grid-cols-3 gap-4">
              <MoneyField name="discount" label="Desconto total (R$)" />
              <MoneyField
                name="platform_fee"
                label="Taxas reais da plataforma (R$)"
              />
              <MoneyField
                name="shipping_cost"
                label="Frete pago pela loja (R$)"
              />
            </div>
            <p className="my-5">
              Valor bruto:{" "}
              <strong className="money">
                {brl(
                  items.reduce(
                    (sum, i) => sum + i.quantity * Number(i.unit_price),
                    0,
                  ),
                )}
              </strong>
            </p>
            <Button disabled={busy}>
              {busy ? "Registrando…" : "Confirmar venda e baixar estoque"}
            </Button>
          </form>
        </Card>
      )}
      <Card>
        <h2>Histórico de vendas</h2>
        {!rows ? (
          <p role="status">Carregando…</p>
        ) : !rows.results.length ? (
          <Empty>Nenhuma venda registrada.</Empty>
        ) : (
          <div className="overflow-auto">
            <table>
              <thead>
                <tr>
                  <th>Venda</th>
                  <th>Canal</th>
                  <th>Bruto / líquido</th>
                  <th>Lucro</th>
                  <th>Situação</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {rows.results.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <p>
                        {new Date(s.created_at).toLocaleDateString("pt-BR")}{" "}
                        {s.reference && `· ${s.reference}`}
                      </p>
                      {s.items.map((i, n) => (
                        <p key={n} className="text-xs text-muted-foreground">
                          {i.quantity}× {i.product_name}
                        </p>
                      ))}
                    </td>
                    <td>{channels[s.channel] || s.channel}</td>
                    <td className="money">
                      {brl(s.gross)}
                      <p className="text-xs text-muted-foreground">
                        Líquido {brl(s.net)}
                      </p>
                    </td>
                    <td className="money">{brl(s.profit)}</td>
                    <td>
                      {s.status === "cancelled"
                        ? "Cancelada"
                        : s.received_at
                          ? "Recebida"
                          : "A receber"}
                    </td>
                    <td>
                      <div className="flex gap-2">
                        {s.status !== "cancelled" && (
                          <>
                            {!s.received_at && (
                              <Button
                                size="sm"
                                disabled={busy}
                                onClick={() => action(s.id, "receive")}
                              >
                                Receber
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={busy}
                              onClick={() => action(s.id, "cancel")}
                            >
                              Cancelar
                            </Button>
                          </>
                        )}
                      </div>
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
