"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { ErrorMessage } from "@/shared/components/feedback";
import { FormActions } from "@/shared/components/form-actions";
import { SaleLabelEditor } from "@/features/sales/components/sale-label-editor";
import {
  abrirPdfVenda,
  baixarPdfVenda,
  emptySaleLabel,
  lerZplVenda,
  validarZpl,
  type SaleLabelDraft,
} from "@/features/sales/label";
import type { Sale, SaleLabel } from "@/features/sales/types";

export function SaleLabelDialog({ sale, onSaved, onClose }: {
  sale: Sale;
  onSaved: () => void;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [draft, setDraft] = useState<SaleLabelDraft>(emptySaleLabel);
  const [loading, setLoading] = useState(sale.has_label);
  const [reading, setReading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    dialog.current?.showModal();
    if (!sale.has_label) return;
    api<SaleLabel>(`sales/${sale.id}/label`)
      .then((saved) =>
        setDraft({
          zpl: saved.zpl,
          source_name: saved.source_name,
          campos: {
            ...emptySaleLabel().campos,
            pedido: saved.order_id,
            nome: saved.recipient_name,
            cidade: saved.recipient_city,
            uf: saved.recipient_state,
          },
        }),
      )
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false));
  }, [sale.has_label, sale.id]);

  async function ensuredDraft() {
    const validation = validarZpl(draft.zpl);
    if (validation) throw new Error(validation);
    if (draft.campos.nome || draft.campos.cidade || draft.campos.pedido) return draft;
    const campos = await lerZplVenda(draft.zpl, setStatus);
    const next = { ...draft, campos };
    setDraft(next);
    return next;
  }

  async function run(task: (ready: SaleLabelDraft) => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await task(await ensuredDraft());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <dialog
      ref={dialog}
      aria-labelledby="sale-label-title"
      className="m-auto w-[min(94vw,44rem)] max-h-[90dvh] overflow-y-auto rounded-xl border bg-card p-5 text-card-foreground shadow-lg backdrop:bg-black/50"
      onCancel={(event) => { event.preventDefault(); if (!busy && !reading) onClose(); }}
    >
      <h2 id="sale-label-title">Etiqueta da venda</h2>
      <p className="text-sm text-muted-foreground mb-4">
        {sale.reference || "Venda sem referência"}. O ZPL salvo pode gerar novamente o PDF para baixar ou imprimir.
      </p>
      {loading ? <p role="status">Carregando etiqueta…</p> : (
        <SaleLabelEditor
          value={draft}
          onChange={setDraft}
          idPrefix={`sale-label-${sale.id}`}
          onBusyChange={setReading}
        />
      )}
      {status && <p role="status" className="text-sm text-muted-foreground mt-3">{status}</p>}
      <ErrorMessage message={error} />
      <FormActions className="mt-5">
        <Button disabled={busy || reading || loading || !draft.zpl} onClick={() => run(async (ready) => {
          await api(`sales/${sale.id}/label`, {
            method: "PUT",
            body: JSON.stringify({
              zpl: ready.zpl,
              source_name: ready.source_name,
              order_id: sale.reference || ready.campos.pedido,
              recipient_name: ready.campos.nome,
              recipient_city: ready.campos.cidade,
              recipient_state: ready.campos.uf,
            }),
          });
          onSaved();
        })}>
          {busy ? "Processando…" : sale.has_label ? "Salvar etiqueta" : "Adicionar à venda"}
        </Button>
        <Button type="button" variant="outline" disabled={busy || reading || !draft.zpl}
          onClick={() => run(async (ready) => {
            const campos = await baixarPdfVenda(ready, setStatus);
            setDraft({ ...ready, campos });
          })}>
          Baixar PDF
        </Button>
        <Button type="button" variant="outline" disabled={busy || reading || !draft.zpl}
          onClick={() => {
            const janela = window.open("", "_blank");
            void run(async (ready) => {
              const campos = await abrirPdfVenda(ready, janela, setStatus);
              setDraft({ ...ready, campos });
            });
          }}>
          Abrir para imprimir
        </Button>
        <Button type="button" variant="ghost" disabled={busy || reading} onClick={onClose}>Fechar</Button>
      </FormActions>
    </dialog>
  );
}
