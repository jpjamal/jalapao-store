"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { brl } from "@/shared/lib/format";
import { type SupplyMovement, type SupplyReceipt } from "@/features/supplies/types";
import { type Page } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { FormActions } from "@/shared/components/form-actions";
import { Pagination } from "@/shared/components/pagination";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { Field } from "@/shared/components/fields";

const today = () => new Date().toLocaleDateString("en-CA");
const dateBr = (iso: string) => iso.split("T")[0].split("-").reverse().join("/");

/* Segunda aba de Insumos: compras (pagar e cancelar) e o razão de todas as mudanças de saldo. */
export function SupplyHistory({ refreshKey, onChanged }: { refreshKey: number; onChanged: () => void }) {
  const [receipts, setReceipts] = useState<Page<SupplyReceipt> | null>(null);
  const [movements, setMovements] = useState<Page<SupplyMovement> | null>(null);
  const [receiptPage, setReceiptPage] = useState(1);
  const [movementPage, setMovementPage] = useState(1);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [paying, setPaying] = useState<SupplyReceipt | null>(null);

  const load = useCallback(() => {
    Promise.all([
      api<Page<SupplyReceipt>>(`supply-receipts?page=${receiptPage}`),
      api<Page<SupplyMovement>>(`supply-movements?page=${movementPage}`),
    ])
      .then(([r, m]) => {
        setReceipts(r);
        setMovements(m);
      })
      .catch((e) => setError(e.message));
  }, [receiptPage, movementPage]);
  // refreshKey: o cadastro mexeu no saldo (compra, baixa, ajuste) e esta aba recarrega ao abrir
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, [load, refreshKey]);

  async function pay(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!paying) return;
    setBusy(true);
    setError("");
    setNotice("");
    const f = new FormData(e.currentTarget);
    try {
      await api(`supply-receipts/${paying.id}/pay`, {
        method: "POST",
        body: JSON.stringify({ occurred_on: f.get("occurred_on") }),
      });
      setPaying(null);
      setNotice("Pagamento registrado: saiu do caixa uma vez.");
      load();
      onChanged();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
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
        <p role="status" className="border border-[var(--success)] text-[var(--success)] rounded-md p-3 mb-4">
          {notice}
        </p>
      )}
      {paying && (
        <Card className="mb-6">
          <h2>Pagar compra</h2>
          <p className="text-muted-foreground mb-3">
            {paying.quantity} × {paying.supply_name} · {brl(paying.total)}. Gera uma saída no caixa, uma
            única vez.
          </p>
          <form onSubmit={pay}>
            <Field
              name="occurred_on"
              id="supply_payment_date"
              label="Data do pagamento"
              type="date"
              value={today()}
              max={today()}
              required
            />
            <FormActions className="mt-4">
              <Button disabled={busy}>Confirmar pagamento</Button>
              <Button type="button" variant="outline" disabled={busy} onClick={() => setPaying(null)}>
                Voltar
              </Button>
            </FormActions>
          </form>
        </Card>
      )}
      <Card className="mb-6">
        <h2>Compras de insumo</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Compra entra no saldo na hora e fica a pagar. Compra lançada errada pode ser cancelada enquanto o
          insumo não tiver outra movimentação depois dela; o registro continua aqui como cancelado.
        </p>
        {!receipts ? (
          <p>Carregando…</p>
        ) : !receipts.results.length ? (
          <Empty>Nenhuma compra de insumo registrada.</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Insumo / referência</th>
                  <th>Quantidade</th>
                  <th>Custo unitário</th>
                  <th>Total</th>
                  <th>Pagamento</th>
                  <th>
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {receipts.results.map((r) => (
                  <tr key={r.id} className={r.status === "cancelled" ? "opacity-60" : undefined}>
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
                        <Button variant="outline" disabled={busy} onClick={() => setPaying(r)}>
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
          page={receiptPage}
          hasNext={!!receipts?.next}
          onPage={setReceiptPage}
        />
      </Card>
      <Card>
        <h2>Movimentos do saldo</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Todas as mudanças de saldo: compras, baixas, ajustes e cancelamentos. O histórico não é apagado.
        </p>
        {!movements ? (
          <p>Carregando…</p>
        ) : !movements.results.length ? (
          <Empty>Nenhum movimento ainda.</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Insumo</th>
                  <th>Variação</th>
                  <th>Saldo depois</th>
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
          page={movementPage}
          hasNext={!!movements?.next}
          onPage={setMovementPage}
        />
      </Card>
    </>
  );
}
