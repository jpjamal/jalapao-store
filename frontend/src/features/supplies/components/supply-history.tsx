"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { brl } from "@/shared/lib/format";
import { type SupplyMovement, type SupplyReceipt } from "@/features/supplies/types";
import { type Page } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { FormActions } from "@/shared/components/form-actions";
import { ConfirmDialog } from "@/shared/components/confirm-dialog";
import { PayDialogBody, PaySelectionBar, SelectBox } from "@/shared/components/pay-selection";
import { useSelection } from "@/shared/hooks/use-selection";
import { payInOrder } from "@/shared/lib/pay";
import { Pagination } from "@/shared/components/pagination";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { Field } from "@/shared/components/fields";
import { useClientList, useListQuery } from "@/shared/hooks/use-list-query";
import {
  ClearFilters, DateRange, FilterSelect, ListToolbar, SearchBox, SortSelect,
} from "@/shared/components/list-toolbar";
import { SortableTh } from "@/shared/components/sortable-th";
import { type SortColumn } from "@/shared/lib/list";

const today = () => new Date().toLocaleDateString("en-CA");
const receiptColumns: SortColumn[] = [
  { key: "occurred_on", label: "Data", kind: "date" },
  { key: "supply_name", label: "Insumo", kind: "text" },
  { key: "quantity", label: "Quantidade", kind: "number" },
  { key: "unit_cost", label: "Custo unitário", kind: "number" },
  { key: "total", label: "Total", kind: "number" },
  { key: "paid_at", label: "Pagamento", kind: "date" },
];
const movementColumns: SortColumn[] = [
  { key: "created_at", label: "Data", kind: "date" },
  { key: "supply__name", label: "Insumo", kind: "text" },
  { key: "delta", label: "Variação", kind: "number" },
  { key: "balance_after", label: "Saldo depois", kind: "number" },
];
// compra confirmada e ainda sem pagamento
const isPayable = (r: SupplyReceipt) => r.status === "confirmed" && !r.paid_at;
const dateBr = (iso: string) => iso.split("T")[0].split("-").reverse().join("/");

/* Segunda aba de Insumos: compras (pagar e cancelar) e o razão de todas as mudanças de saldo. */
export function SupplyHistory({ refreshKey, onChanged }: { refreshKey: number; onChanged: () => void }) {
  const [receipts, setReceipts] = useState<Page<SupplyReceipt> | null>(null);
  const [movements, setMovements] = useState<Page<SupplyMovement> | null>(null);
  // cada lista tem a sua busca, filtros, ordem e página, no servidor (spec 027)
  const rq = useListQuery({ status: "", paid: "", date_from: "", date_to: "" });
  const mq = useListQuery({ direction: "", date_from: "", date_to: "" });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  // compras na janela de pagamento (uma ou várias); vazio = janela fechada (spec 028)
  const [paying, setPaying] = useState<SupplyReceipt[]>([]);
  const [payError, setPayError] = useState("");

  const payable = (receipts?.results ?? []).filter(isPayable);
  const sel = useSelection(payable);

  const loadReceipts = useCallback(() => {
    api<Page<SupplyReceipt>>(`supply-receipts?${rq.queryString}`)
      .then(setReceipts)
      .catch((e) => setError(e.message));
  }, [rq.queryString]);
  const loadMovements = useCallback(() => {
    api<Page<SupplyMovement>>(`supply-movements?${mq.queryString}`)
      .then(setMovements)
      .catch((e) => setError(e.message));
  }, [mq.queryString]);
  const load = useCallback(() => {
    loadReceipts();
    loadMovements();
  }, [loadReceipts, loadMovements]);
  // refreshKey: o cadastro mexeu no saldo (compra, baixa, ajuste) e esta aba recarrega ao abrir
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(loadReceipts, [loadReceipts, refreshKey]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(loadMovements, [loadMovements, refreshKey]);
  // o aviso fica no topo e a lista embaixo: depois de pagar, leva a tela até o aviso
  useEffect(() => {
    if (notice) document.getElementById("aviso-pagamento")?.scrollIntoView({ block: "center" });
  }, [notice]);

  async function pay() {
    if (!paying.length) return;
    setBusy(true);
    setPayError("");
    const r = await payInOrder(
      paying,
      (item) => api(`supply-receipts/${item.id}/pay`, { method: "POST", body: JSON.stringify({ occurred_on: today() }) }),
      (item) => `${item.quantity} × ${item.supply_name} (${brl(item.total)})`,
    );
    setBusy(false);
    if (r.paid.length) {
      setNotice(r.paid.length === 1 ? "Pagamento registrado: saiu do caixa uma vez." : `${r.paid.length} pagamentos registrados: uma saída no caixa para cada compra.`);
      sel.clear();
      load();
      onChanged();
    }
    setPaying(r.rest);
    setPayError(r.error);
  }

  async function cancel(r: SupplyReceipt) {
    if (
      !window.confirm(
        `Cancelar a compra de ${r.quantity} × ${r.supply_name}? O saldo volta ao que era antes` +
          `${r.paid_at ? " e o pagamento é estornado no caixa" : ""}. O registro continua no histórico como cancelado.`,
      )
    )
      return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api(`supply-receipts/${r.id}/cancel`, { method: "POST", body: "{}" });
      setNotice("Compra cancelada e saldo ajustado.");
      load();
      onChanged();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <ErrorMessage message={error} />
      {notice && (
        <p id="aviso-pagamento" role="status" className="border border-[var(--success)] text-[var(--success)] rounded-md p-3 mb-4">
          {notice}
        </p>
      )}
      <ConfirmDialog
        open={paying.length > 0}
        title={paying.length > 1 ? "Pagar compras?" : "Pagar compra?"}
        confirmLabel="Confirmar pagamento"
        busy={busy}
        error={payError}
        onConfirm={pay}
        onCancel={() => setPaying([])}
      >
        <PayDialogBody
          items={paying.map((r) => ({ id: r.id, label: `${r.quantity} × ${r.supply_name}`, total: r.total }))}
        />
      </ConfirmDialog>
      <Card className="mb-6">
        <h2>Compras de insumo</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Compra entra no saldo na hora e fica a pagar. Compra lançada errada pode ser cancelada enquanto o
          insumo não tiver outra movimentação depois dela; o registro continua aqui como cancelado.
        </p>
        <ListToolbar>
          <SearchBox
            value={rq.search}
            onChange={rq.setSearch}
            placeholder="Insumo, fornecedor, referência ou observação…"
          />
          <FilterSelect
            label="Situação"
            value={rq.filters.status}
            onChange={(v) => rq.setFilter("status", v)}
            options={[["confirmed", "Confirmadas"], ["cancelled", "Canceladas"]]}
          />
          <FilterSelect
            label="Pagamento"
            value={rq.filters.paid}
            onChange={(v) => rq.setFilter("paid", v)}
            options={[["true", "Pagas"], ["false", "A pagar"]]}
          />
          <DateRange
            from={rq.filters.date_from}
            to={rq.filters.date_to}
            onFrom={(v) => rq.setFilter("date_from", v)}
            onTo={(v) => rq.setFilter("date_to", v)}
          />
          <SortSelect columns={receiptColumns} sort={rq.sort} onChange={rq.setSort} />
          <ClearFilters visible={rq.hasActiveFilters} onClick={rq.clear} />
        </ListToolbar>
        <PaySelectionBar
          count={sel.selected.length}
          total={sel.selected.reduce((acc, r) => acc + Number(r.total), 0)}
          busy={busy}
          onPay={() => { setPayError(""); setPaying(sel.selected); }}
          onClear={sel.clear}
        />
        {!receipts ? (
          <p>Carregando…</p>
        ) : !receipts.results.length ? (
          <Empty>
            {rq.hasActiveFilters ? "Nenhuma compra encontrada com esses filtros." : "Nenhuma compra de insumo registrada."}
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
                  <SortableTh label="Data" sortKey="occurred_on" sort={rq.sort} onSort={rq.toggleSort} />
                  <SortableTh label="Insumo / referência" sortKey="supply_name" sort={rq.sort} onSort={rq.toggleSort} />
                  <SortableTh label="Quantidade" sortKey="quantity" sort={rq.sort} onSort={rq.toggleSort} />
                  <SortableTh label="Custo unitário" sortKey="unit_cost" sort={rq.sort} onSort={rq.toggleSort} />
                  <SortableTh label="Total" sortKey="total" sort={rq.sort} onSort={rq.toggleSort} />
                  <SortableTh label="Pagamento" sortKey="paid_at" sort={rq.sort} onSort={rq.toggleSort} />
                  <th>
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {receipts.results.map((r) => (
                  <tr key={r.id} className={r.status === "cancelled" ? "opacity-60" : undefined}>
                    <td data-label="Selecionar">
                      {isPayable(r) && (
                        <SelectBox
                          checked={sel.has(r.id)}
                          onChange={() => sel.toggle(r.id)}
                          label={`Selecionar ${r.supply_name} para pagar`}
                        />
                      )}
                    </td>
                    <td data-label="Data">{dateBr(r.occurred_on)}</td>
                    <td data-role="title">
                      {r.supply_name}
                      <div className="text-xs text-muted-foreground">
                        {[r.supplier, r.reference, r.notes].filter(Boolean).join(" · ")}
                      </div>
                    </td>
                    <td data-label="Quantidade">{r.quantity}</td>
                    <td data-label="Custo unitário" className="money">
                      {brl(r.unit_cost)}
                    </td>
                    <td data-label="Total" className="money">
                      {brl(r.total)}
                    </td>
                    <td data-label="Pagamento">
                      {r.status === "cancelled" ? (
                        "Cancelada"
                      ) : r.paid_at ? (
                        "Paga"
                      ) : (
                        <Button variant="outline" disabled={busy} onClick={() => { setPayError(""); setPaying([r]); }}>
                          Pagar {brl(r.total)}
                        </Button>
                      )}
                    </td>
                    <td data-role="actions">
                      {r.status !== "cancelled" && (
                        <Button size="sm" variant="outline" disabled={busy} onClick={() => cancel(r)}>
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
          count={receipts?.count || 0}
          noun={["compra", "compras"]}
          page={rq.page}
          hasNext={!!receipts?.next}
          onPage={rq.setPage}
        />
      </Card>
      <Card>
        <h2>Movimentos do saldo</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Todas as mudanças de saldo: compras, baixas, ajustes e cancelamentos. O histórico não é apagado.
        </p>
        <ListToolbar>
          <SearchBox value={mq.search} onChange={mq.setSearch} placeholder="Insumo ou motivo…" />
          <FilterSelect
            label="Tipo"
            value={mq.filters.direction}
            onChange={(v) => mq.setFilter("direction", v)}
            options={[["in", "Entradas"], ["out", "Saídas"]]}
          />
          <DateRange
            from={mq.filters.date_from}
            to={mq.filters.date_to}
            onFrom={(v) => mq.setFilter("date_from", v)}
            onTo={(v) => mq.setFilter("date_to", v)}
          />
          <SortSelect columns={movementColumns} sort={mq.sort} onChange={mq.setSort} />
          <ClearFilters visible={mq.hasActiveFilters} onClick={mq.clear} />
        </ListToolbar>
        {!movements ? (
          <p>Carregando…</p>
        ) : !movements.results.length ? (
          <Empty>
            {mq.hasActiveFilters ? "Nenhum movimento encontrado com esses filtros." : "Nenhum movimento ainda."}
          </Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Data" sortKey="created_at" sort={mq.sort} onSort={mq.toggleSort} />
                  <SortableTh label="Insumo" sortKey="supply__name" sort={mq.sort} onSort={mq.toggleSort} />
                  <SortableTh label="Variação" sortKey="delta" sort={mq.sort} onSort={mq.toggleSort} />
                  <SortableTh label="Saldo depois" sortKey="balance_after" sort={mq.sort} onSort={mq.toggleSort} />
                  <th>Motivo</th>
                </tr>
              </thead>
              <tbody>
                {movements.results.map((m) => (
                  <tr key={m.id}>
                    <td data-label="Data">{dateBr(m.created_at)}</td>
                    <td data-role="title">{m.supply_name}</td>
                    <td data-label="Variação" className="money">
                      {m.delta > 0 ? `+${m.delta}` : m.delta}
                    </td>
                    <td data-label="Saldo depois" className="money">
                      {m.balance_after}
                    </td>
                    <td data-label="Motivo">{m.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          count={movements?.count || 0}
          noun={["movimento", "movimentos"]}
          page={mq.page}
          hasNext={!!movements?.next}
          onPage={mq.setPage}
        />
      </Card>
    </>
  );
}
