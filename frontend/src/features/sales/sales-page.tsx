"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/shared/api/client";
import { brl } from "@/shared/lib/format";
import { type Product } from "@/features/catalog/types";
import { type Page } from "@/shared/api/types";
import { allProducts } from "@/features/catalog/api";
import { allSupplies } from "@/features/supplies/api";
import { type Supply } from "@/features/supplies/types";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Field, MoneyField } from "@/shared/components/fields";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { ProductPicker } from "@/features/catalog/components/product-picker";
import { FormActions } from "@/shared/components/form-actions";
import { PageHeader } from "@/shared/components/page-header";
import { ImportarVendasML } from "@/features/sales/components/importar-vendas-ml";
import { Pagination } from "@/shared/components/pagination";
type Item = { product_name: string; quantity: number; unit_price: string };
/* insumo usado na venda (spec 024): o que foi pedido e o que de fato foi baixado do saldo */
type SaleSupply = { supply_name: string; requested: number; taken: number; shortfall: number };
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
  supplies?: SaleSupply[];
};
type Draft = { product_id: string; quantity: number; unit_price: string };
type SupplyDraft = { supply_id: string; quantity: number };
const channels: Record<string, string> = {
  direct: "Boca a boca",
  site: "Site Jalapão",
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
  const [importando, setImportando] = useState(false);
  // insumos que a loja pode usar na venda (caixa, etiqueta…); sem permissão a lista vem vazia
  const [supplies, setSupplies] = useState<Supply[]>([]);
  const [usedSupplies, setUsedSupplies] = useState<SupplyDraft[]>([]);
  // por que a lista de insumos veio vazia: falha ao carregar (ex.: sem permissão) ou nada cadastrado
  const [suppliesError, setSuppliesError] = useState("");
  const [key, setKey] = useState(() => crypto.randomUUID());
  const [items, setItems] = useState<Draft[]>([
    { product_id: "", quantity: 1, unit_price: "0" },
  ]);
  const load = useCallback(() => {
    Promise.all([
      allProducts(),
      api<Page<Sale>>(`sales?page=${page}`),
      allSupplies().then(
        (s) => ({ list: s, failure: "" }),
        (e: Error) => ({ list: [] as Supply[], failure: e.message }),
      ),
    ])
      .then(([p, r, s]) => {
        setProducts(p);
        setRows(r);
        setSupplies(s.list);
        setSuppliesError(s.failure);
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
      <PageHeader
        title="Vendas"
        description="Da saída do produto ao dinheiro recebido. Venda de marketplace, do site ou direta: todas baixam o estoque e entram no caixa ao receber."
        actions={<>
          <Button aria-expanded={open} onClick={() => { setOpen(!open); setImportando(false); }}>
            {open ? "Fechar formulário" : "Nova venda"}
          </Button>
          <Button variant="outline" aria-expanded={importando}
            onClick={() => { setImportando(!importando); setOpen(false); }}>
            {importando ? "Fechar importação" : "Importar do Mercado Livre"}
          </Button>
        </>}
      />
      {importando && <ImportarVendasML onImportado={load} />}
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
                const sale = await api<Sale>("sales", {
                  method: "POST",
                  body: JSON.stringify({
                    ...data,
                    items,
                    supplies: usedSupplies.filter((u) => u.supply_id),
                    idempotency_key: key,
                  }),
                });
                // falta de saldo de insumo não impede a venda: baixa só o que tem e avisa o que faltou
                const faltou = (sale.supplies || []).filter((u) => u.shortfall > 0);
                setNotice(
                  "Venda registrada. O estoque foi atualizado; marque como recebida quando o dinheiro entrar." +
                    (faltou.length
                      ? ` Faltou saldo de insumo: ${faltou
                          .map((u) => `${u.supply_name} (pedido ${u.requested}, baixado ${u.taken})`)
                          .join("; ")}. Confira o estoque de insumos.`
                      : ""),
                );
                setOpen(false);
                setItems([{ product_id: "", quantity: 1, unit_price: "0" }]);
                setUsedSupplies([]);
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
                  className="grid grid-cols-2 md:grid-cols-[2fr_1fr_1fr_auto] gap-3 items-end border-b pb-4"
                >
                  <div className="col-span-2 md:col-span-1">
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
                    className="col-span-2 md:col-span-1"
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
              className="my-4 w-full sm:w-auto"
              onClick={() =>
                setItems([
                  ...items,
                  { product_id: "", quantity: 1, unit_price: "0" },
                ])
              }
            >
              Adicionar item
            </Button>
            {(
              <div className="border rounded-md p-4 mb-5">
                <h3>Insumos usados (opcional)</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Caixa, etiqueta e outros: dão baixa no saldo de insumos junto com a venda. Se faltar saldo, a
                  venda continua e o insumo é baixado só até onde tem.
                </p>
                {suppliesError ? (
                  <p role="alert" className="text-sm text-destructive mb-3">
                    Não foi possível carregar os insumos: {suppliesError}
                  </p>
                ) : supplies.length === 0 ? (
                  <p className="text-sm text-muted-foreground mb-3">
                    Ainda não há insumos cadastrados. Cadastre em{" "}
                    <Link href="/insumos" className="underline">
                      Insumos
                    </Link>{" "}
                    (e registre uma compra para ter saldo) para usá-los aqui.
                  </p>
                ) : null}
                {usedSupplies.map((u, index) => (
                  <div key={index} className="grid grid-cols-2 md:grid-cols-[2fr_1fr_auto] gap-3 items-end mb-3">
                    <div className="col-span-2 md:col-span-1">
                      <label htmlFor={`sup-${index}`}>Insumo</label>
                      <select
                        id={`sup-${index}`}
                        value={u.supply_id}
                        onChange={(e) =>
                          setUsedSupplies(
                            usedSupplies.map((r, i) => (i === index ? { ...r, supply_id: e.target.value } : r)),
                          )
                        }
                        required
                      >
                        <option value="">Escolha…</option>
                        {supplies
                          .filter(
                            (s) => s.id === u.supply_id || !usedSupplies.some((r) => r.supply_id === s.id),
                          )
                          .map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name} — saldo {s.quantity} {s.unit}
                            </option>
                          ))}
                      </select>
                    </div>
                    <div>
                      <label htmlFor={`supq-${index}`}>Quantidade</label>
                      <Input
                        id={`supq-${index}`}
                        type="number"
                        min="1"
                        step="1"
                        required
                        value={u.quantity}
                        onChange={(e) =>
                          setUsedSupplies(
                            usedSupplies.map((r, i) =>
                              i === index ? { ...r, quantity: Number(e.target.value) } : r,
                            ),
                          )
                        }
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setUsedSupplies(usedSupplies.filter((_, i) => i !== index))}
                    >
                      Remover
                    </Button>
                  </div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  disabled={supplies.length === 0 || usedSupplies.length >= supplies.length}
                  onClick={() => setUsedSupplies([...usedSupplies, { supply_id: "", quantity: 1 }])}
                >
                  Adicionar insumo
                </Button>
              </div>
            )}
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
            <FormActions>
              <Button disabled={busy}>
                {busy ? "Registrando…" : "Confirmar venda e baixar estoque"}
              </Button>
            </FormActions>
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
            <table className="data-table">
              <thead>
                <tr>
                  <th>Venda</th>
                  <th>Canal</th>
                  <th>Bruto / líquido</th>
                  <th>Lucro</th>
                  <th>Situação</th>
                  <th><span className="sr-only">Ações</span></th>
                </tr>
              </thead>
              <tbody>
                {rows.results.map((s) => (
                  <tr key={s.id}>
                    <td data-role="title">
                      <p>
                        {new Date(s.created_at).toLocaleDateString("pt-BR")}{" "}
                        {s.reference && `· ${s.reference}`}
                      </p>
                      {s.items.map((i, n) => (
                        <p key={n} className="text-xs text-muted-foreground">
                          {i.quantity}× {i.product_name}
                        </p>
                      ))}
                      {(s.supplies || []).map((u, n) => (
                        <p key={`sup-${n}`} className="text-xs text-muted-foreground">
                          Insumo: {u.taken}× {u.supply_name}
                          {u.shortfall > 0 ? ` (faltou ${u.shortfall} de ${u.requested})` : ""}
                        </p>
                      ))}
                    </td>
                    <td data-label="Canal">{channels[s.channel] || s.channel}</td>
                    <td data-label="Bruto / líquido" className="money">
                      {brl(s.gross)}
                      <p className="text-xs text-muted-foreground">
                        Líquido {brl(s.net)}
                      </p>
                    </td>
                    <td data-label="Lucro" className="money">{brl(s.profit)}</td>
                    <td data-label="Situação">
                      {s.status === "cancelled"
                        ? "Cancelada"
                        : s.received_at
                          ? "Recebida"
                          : "A receber"}
                    </td>
                    <td data-role="actions">
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
        <Pagination
          count={rows?.count || 0}
          noun={["venda", "vendas"]}
          page={page}
          hasNext={!!rows?.next}
          onPage={setPage}
        />
      </Card>
    </>
  );
}
