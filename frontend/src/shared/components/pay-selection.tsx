import { useEffect, useRef } from "react";
import { brl } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";

/* Caixa de seleção que aceita o estado "algumas marcadas" (spec 028). */
export function SelectBox({
  checked,
  indeterminate = false,
  onChange,
  label,
}: {
  checked: boolean;
  indeterminate?: boolean;
  onChange: () => void;
  label: string;
}) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.indeterminate = indeterminate;
  }, [indeterminate]);
  return <input ref={ref} type="checkbox" checked={checked} onChange={onChange} aria-label={label} />;
}

/* Faixa acima da lista com o que está marcado para pagar. */
export function PaySelectionBar({
  count,
  total,
  busy,
  onPay,
  onClear,
}: {
  count: number;
  total: number;
  busy: boolean;
  onPay: () => void;
  onClear: () => void;
}) {
  if (!count) return null;
  return (
    <div role="status" className="flex flex-wrap items-center gap-3 rounded-md border p-3 mb-4">
      <span>
        {count} {count === 1 ? "compra selecionada" : "compras selecionadas"} · total <strong>{brl(total)}</strong>
      </span>
      <Button size="sm" disabled={busy} onClick={onPay}>
        Pagar selecionadas
      </Button>
      <Button size="sm" variant="outline" disabled={busy} onClick={onClear}>
        Limpar seleção
      </Button>
    </div>
  );
}

/* Conteúdo da janela de confirmação: uma compra ou a lista do lote. */
export function PayDialogBody({ items }: { items: { id: string; label: string; total: string | number }[] }) {
  const sum = items.reduce((acc, i) => acc + Number(i.total), 0);
  return (
    <>
      {items.length === 1 ? (
        <p>
          {items[0].label} · <strong>{brl(items[0].total)}</strong>
        </p>
      ) : (
        <>
          <ul className="max-h-48 overflow-auto space-y-1">
            {items.map((i) => (
              <li key={i.id} className="flex justify-between gap-3">
                <span>{i.label}</span>
                <span className="money">{brl(i.total)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2">
            {items.length} compras · total <strong>{brl(sum)}</strong>
          </p>
        </>
      )}
      <p className="text-muted-foreground mt-2">
        Registra uma saída no caixa para cada compra, uma única vez, com a data de hoje. Use somente se esses
        pagamentos ainda não foram lançados manualmente.
      </p>
    </>
  );
}
