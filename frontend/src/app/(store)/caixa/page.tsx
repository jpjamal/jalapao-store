"use client";
import { useCallback, useEffect, useState } from "react";
import { api, brl, type Page } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Field, MoneyField } from "@/components/fields";
import { ErrorMessage, Empty } from "@/components/feedback";
import { FormActions } from "@/components/form-actions";
import { PageHeader } from "@/components/page-header";
import { Pagination } from "@/components/pagination";
type Entry = {
  id: string;
  direction: string;
  amount: string;
  description: string;
  occurred_on: string;
  sale: string | null;
  receipt: string | null;
};
export default function Cash() {
  const [rows, setRows] = useState<Page<Entry> | null>(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const load = useCallback(() => {
    api<Page<Entry>>(`cash?page=${page}`)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [page]);
  useEffect(load, [load]);
  return (
    <>
      <PageHeader
        title="Caixa"
        description="Recebimentos e despesas. Vendas pendentes só entram quando marcadas como recebidas."
      />
      <ErrorMessage message={error} />
      {notice && (
        <p role="status" className="text-success mb-4">
          {notice}
        </p>
      )}
      <Card className="mb-5">
        <h2>Lançamento manual</h2>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            const form = e.currentTarget;
            try {
              await api("cash", {
                method: "POST",
                body: JSON.stringify(Object.fromEntries(new FormData(form))),
              });
              form.reset();
              setNotice("Lançamento registrado.");
              load();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
        >
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label htmlFor="direction">Tipo</label>
              <select id="direction" name="direction">
                <option value="out">Saída / despesa</option>
                <option value="in">Entrada</option>
              </select>
            </div>
            <MoneyField name="amount" label="Valor (R$)" />
            <Field
              name="occurred_on"
              label="Data"
              type="date"
              value={new Date().toLocaleDateString("en-CA")}
              required
            />
            <Field
              name="description"
              label="Descrição"
              required
              maxLength={240}
            />
          </div>
          <p className="text-sm text-muted-foreground my-4">
            Lançamentos são preservados. Para corrigir um erro, registre um
            lançamento inverso com o motivo.
          </p>
          <FormActions>
            <Button disabled={busy}>
              {busy ? "Registrando…" : "Registrar lançamento"}
            </Button>
          </FormActions>
        </form>
      </Card>
      <Card>
        <h2>Movimentações de caixa</h2>
        {!rows ? (
          <p>Carregando…</p>
        ) : !rows.results.length ? (
          <Empty>Nenhum lançamento registrado.</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Descrição</th>
                  <th>Origem</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                {rows.results.map((r) => (
                  <tr key={r.id}>
                    <td data-label="Data">{r.occurred_on.split("-").reverse().join("/")}</td>
                    <td data-role="title">{r.description}</td>
                    <td data-label="Origem">{r.sale ? "Venda" : r.receipt ? "Compra de estoque" : "Manual"}</td>
                    <td
                      data-label="Valor"
                      className={`money ${r.direction === "in" ? "text-success" : "text-destructive"}`}
                    >
                      {r.direction === "in" ? "+" : "−"} {brl(r.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          count={rows?.count || 0}
          noun={["lançamento", "lançamentos"]}
          page={page}
          hasNext={!!rows?.next}
          onPage={setPage}
        />
      </Card>
    </>
  );
}
