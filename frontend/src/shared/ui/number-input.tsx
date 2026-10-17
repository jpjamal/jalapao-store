"use client";
import * as React from "react";
import { cn } from "@/shared/lib/utils";

/* Campo numérico com máscara brasileira (1.234,56). O que o resto do app enxerga continua sendo o
   número "puro" ("1234.56"): `e.target.value` no onChange e o valor enviado no formulário.
   - dinheiro (step 0.01): os dígitos entram pela direita, como em maquininha (5 → 0,05; 12345 → 123,45);
   - demais decimais: digita-se com vírgula, limitado às casas do `step`;
   - inteiros (step 1): só dígitos, com ponto de milhar. */

export type NumberMask = "money" | "decimal";

type Props = Omit<React.ComponentProps<"input">, "type" | "value" | "defaultValue" | "step" | "min" | "max"> & {
  value?: string | number | null;
  defaultValue?: string | number | null;
  step?: string | number;
  min?: string | number;
  max?: string | number;
  /** Padrão: "money" quando o step é 0.01, senão "decimal". */
  mask?: NumberMask;
};

/** Casas decimais permitidas pelo step ("1" → 0, "0.001" → 3, "any"/sem step → sem limite). */
function decimalsOf(step: Props["step"]): number {
  if (step === undefined || step === "any") return Infinity;
  const [, frac = ""] = String(step).split(".");
  return frac.length;
}

const group = (int: string) => int.replace(/\B(?=(\d{3})+(?!\d))/g, ".");

/** "1234.5" → "1.234,5"; "12." → "12," (vírgula recém-digitada é mantida). */
export function formatNumber(canonical: string): string {
  if (!canonical || canonical === "-") return canonical;
  const neg = canonical.startsWith("-") ? "-" : "";
  const [int, frac] = canonical.replace("-", "").split(".");
  return `${neg}${group(int || "0")}${frac === undefined ? "" : `,${frac}`}`;
}

/** Valor que chega de fora (servidor, estado) → forma canônica deste campo. */
function toCanonical(v: Props["value"], money: boolean): string {
  if (v === undefined || v === null || v === "") return "";
  const s = String(v);
  if (!money) return s;
  const n = Number(s);
  if (!Number.isFinite(n)) return "";
  const [int, frac = ""] = s.replace("-", "").split(".");
  return `${n < 0 ? "-" : ""}${int.replace(/^0+(?=\d)/, "") || "0"}.${(frac + "00").slice(0, 2)}`;
}

/** Texto digitado → forma canônica. `null` = entrada inválida, mantém o valor anterior. */
function parse(text: string, o: { money: boolean; decimals: number; negative: boolean }): string {
  const neg = o.negative && text.trim().startsWith("-") ? "-" : "";
  if (o.money) {
    const digits = text.replace(/\D/g, "").replace(/^0+/, "");
    if (!digits) return text.replace(/\D/g, "") ? `${neg}0.00` : neg;
    const padded = digits.padStart(3, "0");
    return `${neg}${padded.slice(0, -2)}.${padded.slice(-2)}`;
  }
  // vírgula é o separador decimal; ponto vira decimal só quando digitado logo após até 3 dígitos
  // (os pontos que o próprio campo mostra são sempre de milhar)
  let t = text.replace(/[^\d,.]/g, "");
  const lastDot = t.endsWith(".") && !t.includes(",") && t.replace(/\./g, "").length <= 3 && o.decimals > 0;
  t = lastDot ? t.replace(/\./g, "").concat(",") : t.replace(/\./g, "");
  const [int = "", ...rest] = t.split(",");
  const hasComma = rest.length > 0 && o.decimals > 0;
  const frac = rest.join("").slice(0, Number.isFinite(o.decimals) ? o.decimals : 8);
  const intClean = int.replace(/^0+(?=\d)/, "");
  if (!intClean && !hasComma) return neg;
  return `${neg}${intClean || "0"}${hasComma ? `.${frac}` : ""}`;
}

export function NumberInput({
  value,
  defaultValue,
  onChange,
  step,
  min,
  max,
  mask,
  name,
  className,
  inputMode,
  required,
  disabled,
  ...rest
}: Props) {
  const money = (mask ?? (String(step) === "0.01" ? "money" : "decimal")) === "money";
  const decimals = money ? 2 : decimalsOf(step);
  const negative = min === undefined || Number(min) < 0;
  const controlled = value !== undefined;
  const initial = toCanonical(controlled ? value : defaultValue, money);
  const [inner, setInner] = React.useState(initial);
  const canonical = controlled ? toCanonical(value, money) : inner;
  // controlado: preserva o que o pai devolve, inclusive o estado intermediário "12." (vírgula digitada)
  const shown = controlled && String(value ?? "").endsWith(".") && !money ? String(value) : canonical;
  const ref = React.useRef<HTMLInputElement>(null);

  // form.reset() volta o campo ao valor inicial
  React.useEffect(() => {
    const form = ref.current?.form;
    if (!form) return;
    const onReset = () => setTimeout(() => setInner(initial), 0);
    form.addEventListener("reset", onReset);
    return () => form.removeEventListener("reset", onReset);
  }, [initial]);

  // o navegador não valida mínimo num campo de texto: avisa pelo próprio balão do formulário
  React.useEffect(() => {
    const n = Number(shown);
    ref.current?.setCustomValidity(
      shown && shown !== "-" && min !== undefined && n < Number(min)
        ? `Informe um valor de pelo menos ${formatNumber(String(min))}.`
        : "",
    );
  }, [shown, min]);

  return (
    <>
      <input
        {...rest}
        ref={ref}
        type="text"
        data-slot="input"
        inputMode={inputMode ?? (negative ? undefined : decimals > 0 ? "decimal" : "numeric")}
        autoComplete="off"
        required={required}
        disabled={disabled}
        value={formatNumber(shown)}
        onChange={(e) => {
          const next = parse(e.target.value, { money, decimals, negative });
          if (max !== undefined && next && Number(next) > Number(max)) return;
          setInner(next);
          // quem escuta só lê e.target.value: entrega o número puro, não o texto mascarado
          onChange?.({
            ...e,
            target: { ...e.target, value: next, name: name ?? e.target.name },
            currentTarget: { ...e.currentTarget, value: next },
          } as unknown as React.ChangeEvent<HTMLInputElement>);
        }}
        className={cn(
          "flex h-11 sm:h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base shadow-xs focus-visible:outline-2 focus-visible:outline-ring disabled:opacity-50",
          className,
        )}
      />
      {name && <input type="hidden" name={name} value={shown === "-" ? "" : shown} disabled={disabled} />}
    </>
  );
}
