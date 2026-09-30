"use client";
import { useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { type Supply } from "@/features/supplies/types";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { FormActions } from "@/shared/components/form-actions";
import { ErrorMessage } from "@/shared/components/feedback";
import { Field } from "@/shared/components/fields";

/* Compra, baixa e ajuste do saldo de um insumo (spec 024, etapa 2). O saldo só muda por aqui:
   compra entra e fica a pagar, baixa ("usei 1 rolo") tira, ajuste corrige para mais ou para menos. */

export type SupplyAction = "buy" | "baixa" | "ajuste";

const today = () => new Date().toLocaleDateString("en-CA");

const titles: Record<SupplyAction, string> = {
  buy: "Comprar",
  baixa: "Dar baixa",
  ajuste: "Ajustar saldo",
};

export function SupplyActionForm({
  supply,
  action,
  done,
  cancel,
}: {
  supply: Supply;
  action: SupplyAction;
  done: (message: string) => void;
  cancel: () => void;
}) {
  // o formulário abre no topo da página: com a lista longa, leva a tela até ele
  useEffect(() => {
    document.getElementById("form-acao-insumo")?.scrollIntoView({ block: "start" });
  }, []);
  const [key] = useState(() => crypto.randomUUID());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const isFilament = supply.category_is_filament;
  const unit = supply.unit || "unidade";

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const f = new FormData(e.currentTarget);
    try {
      if (action === "buy") {
        await api("supply-receipts", {
          method: "POST",
          body: JSON.stringify({
            idempotency_key: key,
            supply_id: supply.id,
            quantity: Number(f.get("quantity")),
            unit_cost: f.get("unit_cost"),
            occurred_on: f.get("occurred_on"),
            supplier: f.get("supplier"),
            reference: f.get("reference"),
            notes: f.get("notes"),
          }),
        });
        done(`Compra de ${supply.name} registrada. Ela fica a pagar até você confirmar o pagamento.`);
      } else {
        const amount = Number(f.get("amount"));
        await api("supply-movements", {
          method: "POST",
          body: JSON.stringify({
            supply: supply.id,
            delta: action === "baixa" ? -Math.abs(amount) : amount,
            reason: f.get("reason"),
          }),
        });
        done(action === "baixa" ? "Baixa registrada." : "Saldo ajustado.");
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card id="form-acao-insumo" className="mb-6">
      <h2>
        {titles[action]} — {supply.name}
      </h2>
      <p className="text-sm text-muted-foreground mb-3">
        Saldo atual: <strong>{supply.quantity}</strong> {unit}
      </p>
      <ErrorMessage message={error} />
      <form onSubmit={submit}>
        {action === "buy" ? (
          <div className="grid md:grid-cols-3 gap-4">
            <Field name="quantity" label={`Quantidade (${unit})`} type="number" min="1" step="1" value="1" required />
            <Field
              name="unit_cost"
              label={isFilament ? "Preço do rolo (R$)" : "Custo unitário (R$)"}
              type="number"
              min="0"
              step="0.01"
              value={supply.roll_price ?? ""}
              required
            />
            <Field name="occurred_on" label="Data da compra" type="date" value={today()} max={today()} required />
            <Field name="supplier" label="Fornecedor" maxLength={200} />
            <Field name="reference" label="Referência / nota" maxLength={100} />
            <Field name="notes" label="Observação" maxLength={500} />
            {isFilament && (
              <p className="md:col-span-3 text-sm text-muted-foreground">
                O preço do rolo informado passa a ser o preço do filamento no cadastro (último preço pago).
                Peças já salvas não mudam: só aparece o aviso de preço desatualizado.
              </p>
            )}
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="amount">
                {action === "baixa" ? `Quantidade usada (${unit})` : `Ajuste (${unit}, use - para tirar)`}
              </label>
              <Input
                id="amount"
                name="amount"
                type="number"
                step="1"
                min={action === "baixa" ? "1" : undefined}
                required
              />
            </div>
            <div className="md:col-span-2">
              <label htmlFor="reason">Motivo</label>
              <Input
                id="reason"
                name="reason"
                maxLength={240}
                required
                placeholder={action === "baixa" ? "Usei em produção, envio…" : "Contagem, perda, correção…"}
              />
            </div>
          </div>
        )}
        <FormActions className="mt-4">
          <Button disabled={busy}>{busy ? "Salvando…" : titles[action]}</Button>
          <Button type="button" variant="outline" onClick={cancel} disabled={busy}>
            Cancelar
          </Button>
        </FormActions>
      </form>
    </Card>
  );
}
