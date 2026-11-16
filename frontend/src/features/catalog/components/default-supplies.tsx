"use client";
import Link from "next/link";
import { type Supply } from "@/features/supplies/types";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { brl } from "@/shared/lib/format";

/* Embalagem padrão do produto (spec 040): insumos (caixa, saco, etiqueta…) que a venda já traz
   preenchidos, por unidade vendida. Na venda dá para trocar ou tirar. Filamento não entra: o custo
   dele já está na peça. */

export type KitLine = { uid: string; supply: string; quantity: string };

export function DefaultSupplies({
  lines,
  onChange,
  supplies,
}: {
  lines: KitLine[];
  onChange: (next: KitLine[]) => void;
  supplies: Supply[];
}) {
  const options = supplies.filter(
    (s) => !s.category_is_filament && (s.active || lines.some((l) => l.supply === s.id)),
  );
  const update = (uid: string, patch: Partial<KitLine>) =>
    onChange(lines.map((l) => (l.uid === uid ? { ...l, ...patch } : l)));
  const cost = lines.reduce((sum, l) => {
    const s = supplies.find((x) => x.id === l.supply);
    return sum + (s?.unit_cost ? Number(s.unit_cost) * Number(l.quantity || 0) : 0);
  }, 0);
  return (
    <div className="border rounded-md p-4 mt-5">
      <h3>Embalagem padrão (opcional)</h3>
      <p className="text-sm text-muted-foreground mb-3">
        Caixa, saco e outros insumos usados para enviar <strong>uma unidade</strong> deste produto. Ao registrar
        a venda eles já vêm preenchidos (multiplicados pela quantidade) e o custo deles sai do lucro da venda.
      </p>
      {options.length === 0 && (
        <p className="text-sm text-muted-foreground mb-3">
          Nenhuma embalagem cadastrada. Cadastre em{" "}
          <Link href="/insumos" className="underline">
            Insumos
          </Link>
          , na categoria Embalagens.
        </p>
      )}
      {lines.map((l, index) => (
        <div key={l.uid} className="grid grid-cols-2 md:grid-cols-[2fr_1fr_auto] gap-3 items-end mb-3">
          <div className="col-span-2 md:col-span-1">
            <label htmlFor={`kit-${index}`}>Insumo</label>
            <select
              id={`kit-${index}`}
              value={l.supply}
              required
              onChange={(e) => update(l.uid, { supply: e.target.value })}
            >
              <option value="">Escolha…</option>
              {options
                .filter((s) => s.id === l.supply || !lines.some((o) => o.supply === s.id))
                .map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                    {s.unit_cost != null ? ` — ${brl(s.unit_cost)} cada` : " — sem custo ainda"}
                    {s.active ? "" : " (inativo)"}
                  </option>
                ))}
            </select>
          </div>
          <div>
            <label htmlFor={`kitq-${index}`}>Quantidade por unidade</label>
            <Input
              id={`kitq-${index}`}
              type="number"
              min="1"
              step="1"
              required
              value={l.quantity}
              onChange={(e) => update(l.uid, { quantity: e.target.value })}
            />
          </div>
          <Button type="button" variant="ghost" onClick={() => onChange(lines.filter((o) => o.uid !== l.uid))}>
            Remover
          </Button>
        </div>
      ))}
      <div className="flex flex-wrap items-center gap-4">
        <Button
          type="button"
          variant="outline"
          disabled={options.length === 0 || lines.length >= options.length}
          onClick={() => onChange([...lines, { uid: crypto.randomUUID(), supply: "", quantity: "1" }])}
        >
          Adicionar insumo
        </Button>
        {lines.length > 0 && (
          <p className="text-sm text-muted-foreground">
            Custo atual da embalagem: <strong className="money">{brl(cost)}</strong> por unidade
          </p>
        )}
      </div>
    </div>
  );
}
