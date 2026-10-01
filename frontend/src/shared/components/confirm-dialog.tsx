"use client";
import { useEffect, useRef } from "react";
import { Button } from "@/shared/ui/button";
import { ErrorMessage } from "@/shared/components/feedback";
import { FormActions } from "@/shared/components/form-actions";

/* Janela flutuante de confirmação (<dialog> nativo: Esc fecha, o foco fica dentro e o fundo não clica).
   O erro da ação aparece dentro da janela, porque a página atrás fica coberta. */
export function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel,
  busy = false,
  error = "",
  onConfirm,
  onCancel,
}: {
  open: boolean;
  title: string;
  children: React.ReactNode;
  confirmLabel: string;
  busy?: boolean;
  error?: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-labelledby="confirm-dialog-title"
      className="m-auto w-[min(92vw,26rem)] rounded-xl border bg-card p-5 text-card-foreground shadow-lg backdrop:bg-black/50"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onCancel();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onCancel();
      }}
    >
      {open && (
        <>
          <h2 id="confirm-dialog-title" className="mb-2">
            {title}
          </h2>
          <div className="mb-4 text-sm">{children}</div>
          <ErrorMessage message={error} />
          <FormActions>
            <Button type="button" disabled={busy} onClick={onConfirm}>
              {busy ? "Aguarde…" : confirmLabel}
            </Button>
            <Button type="button" variant="outline" disabled={busy} onClick={onCancel}>
              Cancelar
            </Button>
          </FormActions>
        </>
      )}
    </dialog>
  );
}
