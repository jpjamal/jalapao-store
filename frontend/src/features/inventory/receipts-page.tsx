"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { brl } from "@/shared/lib/format";
import { type Page } from "@/shared/api/types";
import { type Product } from "@/features/catalog/types";
import { allProducts } from "@/features/catalog/api";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Field } from "@/shared/components/fields";
import { Empty, ErrorMessage } from "@/shared/components/feedback";
import { ProductPicker } from "@/features/catalog/components/product-picker";
import { FormActions } from "@/shared/components/form-actions";
import { ConfirmDialog } from "@/shared/components/confirm-dialog";
import { PayDialogBody, PaySelectionBar, SelectBox } from "@/shared/components/pay-selection";
import { useSelection } from "@/shared/hooks/use-selection";
import { payInOrder } from "@/shared/lib/pay";
import { PageHeader } from "@/shared/components/page-header";
import { Pagination } from "@/shared/components/pagination";
import { useListQuery } from "@/shared/hooks/use-list-query";
import {
  ClearFilters, DateRange, FilterSelect, ListToolbar, SearchBox, SortSelect,
} from "@/shared/components/list-toolbar";
import { SortableTh } from "@/shared/components/sortable-th";
import { type SortColumn } from "@/shared/lib/list";

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
  status: string;
};
// compra confirmada e ainda sem pagamento (produção não gera saída; cancelada não se paga)
const isPayable = (r: Receipt) => r.kind === "purchase" && r.status === "confirmed" && !r.paid_at;
const today = () => new Date().toLocaleDateString("en-CA");
const receiptColumns: SortColumn[] = [
  { key: "occurred_on", label: "Data", kind: "date" },
  { key: "product_name", label: "Produto", kind: "text" },
  { key: "quantity", label: "Quantidade", kind: "number" },
  { key: "unit_cost", label: "Custo unitário", kind: "number" },
  { key: "total", label: "Total", kind: "number" },
  { key: "paid_at", label: "Pagamento", kind: "date" },
];

export default function Receipts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [rows, setRows] = useState<Page<Receipt> | null>(null);
  // busca, filtros, ordem e página do histórico, no servidor (spec 027)
  const q = useListQuery({ kind: "", status: "", paid: "", date_from: "", date_to: "" });
  const [kind, setKind] = useState("purchase");
  const [productId, setProductId] = useState("");
  const [cost, setCost] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  // compras na janela de pagamento (uma ou várias); vazio = janela fechada (spec 028)
  const [paying, setPaying] = useState<Receipt[]>([]);
  const [payError, setPayError] = useState("");
  const loadProducts = useCallback(() => {
    allProducts()
      .then(setProducts)
      .catch((e) => setError(e.message));
  }, []);
  const loadRows = useCallback(() => {
    api<Page<Receipt>>(`receipts?${q.queryString}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [q.queryString]);
  useEffect(loadProducts, [loadProducts]);
  useEffect(loadRows, [loadRows]);
  // o aviso fica no topo e a lista embaixo: depois de pagar, leva a tela até o aviso
  useEffect(() => {
    if (notice) document.getElementById("aviso-pagamento")?.scrollIntoView({ block: "center" });
  }, [notice]);
  const payable = (rows?.results ?? []).filter(isPayable);
  const sel = useSelection(payable);
  const load = useCallback(() => {
    loadProducts();
    loadRows();
  }, [loadProducts, loadRows]);
  useEffect(() => setKey(crypto.randomUUID()), []);
  async function confirmPay() {
    if (!paying.length) return;
    setBusy(true);
    setPayError("");
    const r = await payInOrder(
      paying,
      (item) => api(`receipts/${item.id}/pay`, { method: "POST", body: JSON.stringify({ occurred_on: today() }) }),
      (item) => `${item.quantity} × ${item.product_name} (${brl(item.total)})`,
    );
    setBusy(false);
    if (r.paid.length) {
      setNotice(r.paid.length === 1 ? "Compra paga. Saída registrada no caixa uma única vez." : `${r.paid.length} compras pagas. Uma saída no caixa para cada uma.`);
      sel.clear();
      load();
    }
    setPaying(r.rest);
    setPayError(r.error);
  }
  async function cancel(r: Receipt) {
    const nome = r.kind === "purchase" ? "compra" : "produção";
    if (
      !window.confirm(
        `Cancelar esta ${nome} de ${r.quantity} × ${r.product_name}? O estoque volta ao que era antes` +
          `${r.paid_at ? " e o pagamento é estornado no caixa" : ""}. O registro continua no histórico como cancelado.`,
      )
    )
      return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api(`receipts/${r.id}/cancel`, { method: "POST", body: "{}" });
      setNotice("Entrada cancelada e estoque ajustado.");
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
        title="Compras e produção"
        description="Cada entrada guarda seu próprio custo e atualiza a média do estoque. O histórico das vendas é preservado."
      />
      <ErrorMessage message={error} />
      {notice && (
        <p id="aviso-pagamento" role="status" className="text-success mb-4">
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
          <fieldset disabled={busy} className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
              <ProductPicker
                id="product_id"
                name="product_id"
                required
                products={products}
                value={productId}
                onChange={(id, p) => {
                  setProductId(id);
                  setCost(p?.cost_price || "");
                }}
              />
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
          <FormActions>
            <Button disabled={busy || !key || !products.length}>
              {busy ? "Registrando…" : "Registrar entrada"}
            </Button>
          </FormActions>
        </form>
      </Card>
      <ConfirmDialog
        open={paying.length > 0}
        title={paying.length > 1 ? "Pagar compras?" : "Pagar compra?"}
        confirmLabel="Confirmar pagamento"
        busy={busy}
        error={payError}
        onConfirm={confirmPay}
        onCancel={() => setPaying([])}
      >
        <PayDialogBody
          items={paying.map((r) => ({ id: r.id, label: `${r.quantity} × ${r.product_name}`, total: r.total }))}
        />
      </ConfirmDialog>
      <Card>
        <h2>Histórico de entradas</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Um registro por produto. Use a mesma referência para itens da mesma
          compra. Entrada lançada errada pode ser cancelada enquanto o produto não
          tiver outra movimentação depois dela; o registro continua aqui como
          cancelado. Depois disso, corrija pelos ajustes de estoque.
        </p>
        <ListToolbar>
          <SearchBox
            value={q.search}
            onChange={q.setSearch}
            placeholder="Produto, fornecedor, referência ou observação…"
          />
          <FilterSelect
            label="Origem"
            value={q.filters.kind}
            onChange={(v) => q.setFilter("kind", v)}
            options={[["purchase", "Compra"], ["production", "Produção"]]}
          />
          <FilterSelect
            label="Situação"
            value={q.filters.status}
            onChange={(v) => q.setFilter("status", v)}
            options={[["confirmed", "Confirmadas"], ["cancelled", "Canceladas"]]}
          />
          <FilterSelect
            label="Pagamento"
            value={q.filters.paid}
            onChange={(v) => q.setFilter("paid", v)}
            options={[["true", "Pagas"], ["false", "A pagar"]]}
          />
          <DateRange
            from={q.filters.date_from}
            to={q.filters.date_to}
            onFrom={(v) => q.setFilter("date_from", v)}
            onTo={(v) => q.setFilter("date_to", v)}
          />
          <SortSelect columns={receiptColumns} sort={q.sort} onChange={q.setSort} />
          <ClearFilters visible={q.hasActiveFilters} onClick={q.clear} />
        </ListToolbar>
        <PaySelectionBar
          count={sel.selected.length}
          total={sel.selected.reduce((acc, r) => acc + Number(r.total), 0)}
          busy={busy}
          onPay={() => { setPayError(""); setPaying(sel.selected); }}
          onClear={sel.clear}
        />
        {!rows ? (
          <p>Carregando…</p>
        ) : !rows.results.length ? (
          <Empty>
            {q.hasActiveFilters ? "Nenhuma entrada encontrada com esses filtros." : "Nenhuma compra ou produção registrada."}
          </Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>
                    <SelectBox
                      checked={sel.allChecked}
                      indeterminate={sel.someChecked}
                      onChange={sel.toggleAll}
                      label="Selecionar todas as compras a pagar desta lista"
                    />
                  </th>
                  <SortableTh label="Data / origem" sortKey="occurred_on" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Produto / referência" sortKey="product_name" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Quantidade" sortKey="quantity" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Custo unitário" sortKey="unit_cost" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Total" sortKey="total" sort={q.sort} onSort={q.toggleSort} />
                  <SortableTh label="Pagamento" sortKey="paid_at" sort={q.sort} onSort={q.toggleSort} />
                  <th>
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.results.map((r) => (
                  <tr
                    key={r.id}
                    className={r.status === "cancelled" ? "opacity-60" : undefined}
                  >
                    <td data-label="Selecionar">
                      {isPayable(r) && (
                        <SelectBox
                          checked={sel.has(r.id)}
                          onChange={() => sel.toggle(r.id)}
                          label={`Selecionar ${r.product_name} para pagar`}
                        />
                      )}
                    </td>
                    <td data-label="Data / origem">
                      <span>
                        {r.occurred_on.split("-").reverse().join("/")}
                        <br />
                        {r.kind === "purchase" ? "Compra" : "Produção"}
                      </span>
                    </td>
                    <td data-role="title">
                      {r.product_name}
                      <div className="text-xs text-muted-foreground">
                        {[r.supplier, r.reference, r.notes]
                          .filter(Boolean)
                          .join(" · ")}
                      </div>
                    </td>
                    <td data-label="Quantidade">{r.quantity}</td>
                    <td data-label="Custo unitário" className="money">{brl(r.unit_cost)}</td>
                    <td data-label="Total" className="money">{brl(r.total)}</td>
                    <td data-label="Pagamento">
                      {r.status === "cancelled" ? (
                        "Cancelada"
                      ) : r.kind === "production" ? (
                        "Sem saída automática"
                      ) : r.paid_at ? (
                        "Paga"
                      ) : (
                        <Button
                          variant="outline"
                          disabled={busy}
                          onClick={() => { setPayError(""); setPaying([r]); }}
                        >
                          Pagar {brl(r.total)}
                        </Button>
                      )}
                    </td>
                    <td data-role="actions">
                      {r.status !== "cancelled" && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy}
                          onClick={() => cancel(r)}
                        >
                          Cancelar
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          count={rows?.count || 0}
          noun={["entrada", "entradas"]}
          page={q.page}
          hasNext={!!rows?.next}
          onPage={q.setPage}
        />
      </Card>
    </>
  );
}
