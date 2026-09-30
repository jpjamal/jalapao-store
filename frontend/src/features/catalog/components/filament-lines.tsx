"use client";
import { brl } from "@/shared/lib/format";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { type Supply } from "@/features/supplies/types";
import { type LinhaFilamento } from "@/features/tools/lib/custo3d";

/* Linhas de filamento de uma peça multicolor (spec 024): cada linha é um filamento cadastrado e as
   gramas usadas dele. O custo é a soma das linhas, e o preço de cada uma é o que foi copiado
   quando a linha foi salva — mudar o filamento depois só avisa. */

export const MAX_LINHAS = 8;

export type FilamentLine = {
  /* chave estável da linha na tela: escolher o filamento não pode recriar a linha */
  uid: string;
  filament: string;
  grams: string;
  /* preço copiado quando a linha foi salva (vazio em linha nova) */
  roll_price?: string;
  roll_weight_g?: string;
  /* o filamento mudou de preço desde que a linha foi salva */
  outdated?: boolean;
  /* o dono pediu para trazer o preço atual do filamento */
  refresh: boolean;
};

/* Linhas no formato da conta (`calcular`): preço guardado na linha, ou o atual do filamento quando
   a linha é nova ou o dono pediu para atualizar. */
export function linesToCalc(lines: FilamentLine[], supplies: Supply[]): LinhaFilamento[] {
  return lines.flatMap((l) => {
    const supply = supplies.find((s) => s.id === l.filament);
    const useSaved = l.roll_price != null && l.roll_weight_g != null && !l.refresh;
    const precoRolo = useSaved ? l.roll_price : supply?.roll_price;
    const pesoRolo = useSaved ? l.roll_weight_g : supply?.roll_weight_g;
    if (!precoRolo || !pesoRolo) return [];
    return [{ gramas: l.grams, precoRolo, pesoRolo }];
  });
}

export function newFilamentLine(): FilamentLine {
  return { uid: crypto.randomUUID(), filament: "", grams: "", refresh: false };
}

export function FilamentLines({
  lines,
  onChange,
  supplies,
}: {
  lines: FilamentLine[];
  onChange: (lines: FilamentLine[]) => void;
  supplies: Supply[];
}) {
  const filaments = supplies.filter((s) => s.category_is_filament);
  const used = new Set(lines.map((l) => l.filament));
  const choices = (current: string) =>
    filaments.filter((s) => (s.active || s.id === current) && (!used.has(s.id) || s.id === current));
  const set = (index: number, patch: Partial<FilamentLine>) =>
    onChange(lines.map((l, i) => (i === index ? { ...l, ...patch } : l)));
  const calc = linesToCalc(lines, supplies);
  const gramas = calc.reduce((t, l) => t + Number(l.gramas || 0), 0);
  const custo = calc.reduce(
    (t, l) => t + (Number(l.gramas || 0) * Number(l.precoRolo)) / Number(l.pesoRolo),
    0,
  );
  const canAdd = lines.length < MAX_LINHAS && filaments.some((s) => s.active && !used.has(s.id));
  return (
    <div className="border rounded-md p-4 my-4">
      <h3>Filamentos da peça</h3>
      <p className="text-sm text-muted-foreground mb-3">
        Opcional. Escolha um filamento por cor e as gramas usadas de cada um: o custo vira a soma das
        linhas. Sem linhas, vale o preço por kg e o peso digitados abaixo.
      </p>
      {!filaments.length && (
        <p className="text-sm text-muted-foreground mb-3">
          Ainda não há filamentos cadastrados. Cadastre em Insumos para usá-los aqui.
        </p>
      )}
      {lines.map((l, i) => (
        <div key={l.uid} className="grid sm:grid-cols-[1fr_140px_auto] gap-3 items-end mb-3">
          <div>
            <label htmlFor={`fil-${i}`}>Filamento</label>
            <select
              id={`fil-${i}`}
              value={l.filament}
              onChange={(e) =>
                set(i, { filament: e.target.value, roll_price: undefined, roll_weight_g: undefined, outdated: false, refresh: false })
              }
            >
              <option value="">Escolha…</option>
              {choices(l.filament).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} — {s.material} {s.color}
                  {s.active ? "" : " (inativo)"}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor={`gr-${i}`}>Gramas</label>
            <Input
              id={`gr-${i}`}
              type="number"
              min="0.001"
              step="0.001"
              value={l.grams}
              onChange={(e) => set(i, { grams: e.target.value })}
              required
            />
          </div>
          <Button type="button" variant="outline" onClick={() => onChange(lines.filter((_, j) => j !== i))}>
            Remover
          </Button>
          {l.outdated && (
            <label className="sm:col-span-3 flex items-center gap-2 text-sm text-muted-foreground">
              <input
                type="checkbox"
                checked={l.refresh}
                onChange={(e) => set(i, { refresh: e.target.checked })}
              />
              O preço deste filamento mudou desde que a peça foi salva. Usar o preço atual?
            </label>
          )}
        </div>
      ))}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          type="button"
          variant="outline"
          disabled={!canAdd}
          onClick={() => onChange([...lines, newFilamentLine()])}
        >
          Adicionar filamento
        </Button>
        {lines.length > 0 && (
          <p className="text-sm">
            Total: <strong>{Number(gramas.toFixed(3))} g</strong> · filamento <strong className="money">{brl(custo)}</strong>
          </p>
        )}
      </div>
    </div>
  );
}
