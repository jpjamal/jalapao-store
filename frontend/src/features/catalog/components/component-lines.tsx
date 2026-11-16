"use client";
import Link from "next/link";
import { brl } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { type Supply } from "@/features/supplies/types";
import { type LinhaComponente } from "@/features/tools/lib/custo3d";

/* Componentes que vão dentro da peça 3D (spec 041): LED, parafuso, cabo, base. Cada linha é um insumo
   (que não é filamento) e a quantidade por peça. O custo entra no custo da peça; ao registrar a produção,
   eles saem do estoque de insumos junto com o filamento. O custo de cada linha é o que foi copiado
   quando a linha foi salva — mudar o insumo depois só avisa, como no filamento. */

export const MAX_COMPONENTES = 20;

export type ComponentLine = {
  uid: string;
  supply: string;
  quantity: string;
  /* custo copiado quando a linha foi salva (vazio em linha nova) */
  unit_cost?: string;
  /* o insumo mudou de custo desde que a peça foi salva */
  outdated?: boolean;
  /* o dono pediu para trazer o custo atual do insumo */
  refresh: boolean;
};

/* custo usado na conta: o guardado na linha, ou o atual do insumo em linha nova ou quando o dono pediu */
function costOf(line: ComponentLine, supplies: Supply[]): number {
  if (line.unit_cost != null && !line.refresh) return Number(line.unit_cost);
  return Number(supplies.find((s) => s.id === line.supply)?.unit_cost ?? 0);
}

export function componentsToCalc(lines: ComponentLine[], supplies: Supply[]): LinhaComponente[] {
  return lines.filter((l) => l.supply).map((l) => ({ quantidade: l.quantity, custo: costOf(l, supplies) }));
}

export function componentsPayload(lines: ComponentLine[]) {
  return lines
    .filter((l) => l.supply)
    .map((l) => ({ supply: l.supply, quantity: Number(l.quantity), refresh_price: l.refresh }));
}

export function ComponentLines({
  lines,
  onChange,
  supplies,
}: {
  lines: ComponentLine[];
  onChange: (lines: ComponentLine[]) => void;
  supplies: Supply[];
}) {
  const options = supplies.filter(
    (s) => !s.category_is_filament && (s.active || lines.some((l) => l.supply === s.id)),
  );
  const set = (uid: string, patch: Partial<ComponentLine>) =>
    onChange(lines.map((l) => (l.uid === uid ? { ...l, ...patch } : l)));
  const total = componentsToCalc(lines, supplies).reduce((t, l) => t + Number(l.quantidade || 0) * Number(l.custo), 0);
  const semCusto = lines.some((l) => l.supply && costOf(l, supplies) === 0);
  return (
    <div className="border rounded-md p-4 my-4">
      <h3>Componentes da peça (opcional)</h3>
      <p className="text-sm text-muted-foreground mb-3">
        O que vai <strong>dentro</strong> de cada peça além do filamento: LED, parafuso, cabo, base. O custo entra no
        custo da peça e no preço sugerido. Ao registrar a produção, eles saem do estoque de insumos.
      </p>
      {options.length === 0 && (
        <p className="text-sm text-muted-foreground mb-3">
          Nenhum componente cadastrado. Cadastre em{" "}
          <Link href="/insumos" className="underline">
            Insumos
          </Link>
          , na categoria Componentes.
        </p>
      )}
      {lines.map((l, index) => (
        <div key={l.uid} className="grid grid-cols-2 md:grid-cols-[2fr_1fr_auto] gap-3 items-end mb-3">
          <div className="col-span-2 md:col-span-1">
            <label htmlFor={`comp-${index}`}>Componente</label>
            <select
              id={`comp-${index}`}
              value={l.supply}
              required
              onChange={(e) =>
                set(l.uid, { supply: e.target.value, unit_cost: undefined, outdated: false, refresh: false })
              }
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
            <label htmlFor={`compq-${index}`}>Quantidade por peça</label>
            <Input
              id={`compq-${index}`}
              type="number"
              min="1"
              step="1"
              required
              value={l.quantity}
              onChange={(e) => set(l.uid, { quantity: e.target.value })}
            />
          </div>
          <Button type="button" variant="ghost" onClick={() => onChange(lines.filter((o) => o.uid !== l.uid))}>
            Remover
          </Button>
          {l.outdated && (
            <label className="col-span-2 md:col-span-3 flex items-center gap-2 text-sm text-muted-foreground">
              <input type="checkbox" checked={l.refresh} onChange={(e) => set(l.uid, { refresh: e.target.checked })} />
              O custo deste componente mudou desde que a peça foi salva. Usar o custo atual?
            </label>
          )}
        </div>
      ))}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          type="button"
          variant="outline"
          disabled={options.length === 0 || lines.length >= Math.min(options.length, MAX_COMPONENTES)}
          onClick={() =>
            onChange([...lines, { uid: crypto.randomUUID(), supply: "", quantity: "1", refresh: false }])
          }
        >
          Adicionar componente
        </Button>
        {lines.length > 0 && (
          <p className="text-sm">
            Componentes: <strong className="money">{brl(total)}</strong> por peça
          </p>
        )}
      </div>
      {semCusto && (
        <p className="text-sm text-muted-foreground mt-2">
          Componente sem custo entra como R$ 0,00. Registre a compra ou um ajuste de entrada com custo em Insumos e
          depois marque &quot;usar o custo atual&quot; aqui.
        </p>
      )}
    </div>
  );
}
