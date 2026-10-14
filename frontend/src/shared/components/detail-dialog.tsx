"use client";
import { useEffect, useId, useRef, type KeyboardEvent, type MouseEvent, type ReactNode } from "react";
import { X } from "lucide-react";
import { Button } from "@/shared/ui/button";

/* Janela flutuante de visualização de um item da listagem (<dialog> nativo: Esc e clique fora fecham, o
   foco fica dentro). Os botões de ação da linha aparecem de novo aqui, com texto; ao usar um deles a
   janela fecha, para que a edição ou a confirmação que ele abrir não fique empilhada por cima. */
export function DetailDialog({
  title,
  subtitle,
  onClose,
  children,
  actions,
}: {
  title: string;
  subtitle?: ReactNode;
  onClose: () => void;
  children: ReactNode;
  actions?: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      className="m-auto w-[min(94vw,38rem)] max-h-[90dvh] overflow-y-auto rounded-xl border bg-card p-5 text-card-foreground shadow-lg backdrop:bg-black/50"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 id={titleId} className="break-words">
            {title}
          </h2>
          {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
        </div>
        <Button type="button" variant="outline" size="icon" aria-label="Fechar" title="Fechar" onClick={onClose}>
          <X size={18} aria-hidden />
        </Button>
      </div>
      <div className="space-y-4">{children}</div>
      {actions && (
        <div
          className="mt-5 flex flex-wrap gap-2 border-t pt-4"
          onClick={(e) => {
            if ((e.target as HTMLElement).closest("button,a")) onClose();
          }}
        >
          {actions}
        </div>
      )}
    </dialog>
  );
}

/** Pares rótulo/valor da janela de visualização. */
export function DetailList({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="grid grid-cols-[auto_minmax(0,1fr)] gap-x-4 gap-y-2 text-sm">
      {items
        .filter(([, valor]) => valor !== "" && valor != null && valor !== false)
        .map(([rotulo, valor]) => (
          <div key={rotulo} className="contents">
            <dt className="text-muted-foreground">{rotulo}</dt>
            <dd className="break-words text-right">{valor}</dd>
          </div>
        ))}
    </dl>
  );
}

/** Propriedades da `<tr>` clicável: abre a visualização, menos quando o clique foi num controle da linha. */
export function rowOpen(onOpen: () => void, extra = "") {
  return {
    className: `cursor-pointer hover:bg-muted/40 ${extra}`.trim(),
    onClick: (e: MouseEvent<HTMLElement>) => {
      if ((e.target as HTMLElement).closest("button,a,input,select,textarea,label")) return;
      onOpen();
    },
  };
}

/** O texto principal da linha, como botão: dá o mesmo acesso a quem usa o teclado e a leitores de tela. */
export function RowTitle({ onOpen, children }: { onOpen: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      className="w-full cursor-pointer text-left hover:underline focus-visible:underline"
      onClick={onOpen}
      onKeyDown={(e: KeyboardEvent<HTMLButtonElement>) => e.stopPropagation()}
    >
      {children}
    </button>
  );
}
