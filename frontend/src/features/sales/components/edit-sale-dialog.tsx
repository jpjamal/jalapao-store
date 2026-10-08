"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Field, MoneyField } from "@/shared/components/fields";
import { ErrorMessage } from "@/shared/components/feedback";
import { FormActions } from "@/shared/components/form-actions";
import { brl } from "@/shared/lib/format";
import { channels, type Sale } from "@/features/sales/types";

export function EditSaleDialog({ sale, onSaved, onClose }: {
  sale: Sale; onSaved: () => void; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const sending = useRef(false);
  const attempt = useRef({ body: "", key: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { dialog.current?.showModal(); }, []);
  return (
    <dialog ref={dialog} aria-labelledby="edit-sale-title"
      className="m-auto w-[min(94vw,40rem)] max-h-[90dvh] overflow-y-auto rounded-xl border bg-card p-5 text-card-foreground shadow-lg backdrop:bg-black/50"
      onCancel={(e) => { e.preventDefault(); if (!sending.current) onClose(); }}>
      <h2 id="edit-sale-title">Editar venda</h2>
      <p className="text-sm text-muted-foreground mb-4">
        Corrija o canal e os valores. Os produtos, quantidades e insumos usados são mantidos.
        {sale.external_id && " A correção é local e mantém o vínculo com o pedido importado."}
      </p>
      {sale.received_at && <p className="mb-4 text-sm">
        Venda já recebida: líquido atual de {brl(sale.net)}. Ao salvar, a diferença será registrada
        como entrada ou saída no Caixa, com a data de hoje.
      </p>}
      <form onSubmit={async (e) => {
        e.preventDefault();
        if (sending.current) return;
        const fields = new FormData(e.currentTarget);
        const body = JSON.stringify({
          expected_updated_at: sale.updated_at,
          channel: fields.get("edit-channel"), reference: fields.get("edit-reference"),
          discount: fields.get("edit-discount"), platform_fee: fields.get("edit-platform_fee"),
          shipping_cost: fields.get("edit-shipping_cost"),
          items: sale.items.map((item) => ({ id: item.id, unit_price: fields.get(`price-${item.id}`) })),
        });
        if (attempt.current.body !== body) attempt.current = { body, key: crypto.randomUUID() };
        sending.current = true;
        setBusy(true); setError("");
        try {
          await api(`sales/${sale.id}`, { method: "PATCH",
            body: JSON.stringify({ ...JSON.parse(body), request_key: attempt.current.key }) });
          onSaved();
        } catch (err) { setError((err as Error).message); }
        finally { sending.current = false; setBusy(false); }
      }}>
        <fieldset disabled={busy} className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div><label htmlFor="edit-channel">Canal de venda</label>
              <select id="edit-channel" name="edit-channel" defaultValue={sale.channel} autoFocus>
                {Object.entries(channels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </div>
            <Field name="edit-reference" label="Referência / número do pedido" value={sale.reference} maxLength={100} />
          </div>
          {sale.items.map((item) => <div key={item.id} className="border-b pb-3">
            <p className="mb-2">{item.quantity}× {item.product_name}</p>
            <MoneyField name={`price-${item.id}`} label={`Preço unitário de ${item.product_name} (R$)`} value={item.unit_price} />
          </div>)}
          <div className="grid sm:grid-cols-3 gap-4">
            <MoneyField name="edit-discount" label="Desconto (R$)" value={sale.discount} />
            <MoneyField name="edit-platform_fee" label="Taxas (R$)" value={sale.platform_fee} />
            <MoneyField name="edit-shipping_cost" label="Frete da loja (R$)" value={sale.shipping_cost} />
          </div>
          <ErrorMessage message={error} />
          <FormActions>
            <Button disabled={busy}>{busy ? "Salvando…" : "Salvar alterações"}</Button>
            <Button type="button" variant="outline" onClick={onClose} disabled={busy}>Cancelar</Button>
          </FormActions>
        </fieldset>
      </form>
    </dialog>
  );
}
