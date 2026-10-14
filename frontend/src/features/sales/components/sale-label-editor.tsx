"use client";
import { useEffect, useRef, useState } from "react";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { ErrorMessage } from "@/shared/components/feedback";
import {
  emptySaleLabel,
  abrirPdfVenda,
  baixarPdfVenda,
  lerZplVenda,
  validarZpl,
  type SaleLabelDraft,
} from "@/features/sales/label";

export function SaleLabelEditor({
  value,
  onChange,
  idPrefix,
  onBusyChange,
  allowPdfActions = false,
}: {
  value: SaleLabelDraft;
  onChange: (value: SaleLabelDraft) => void;
  idPrefix: string;
  onBusyChange?: (busy: boolean) => void;
  allowPdfActions?: boolean;
}) {
  const latest = useRef(onChange);
  const run = useRef(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  latest.current = onChange;

  useEffect(() => {
    const zpl = value.zpl;
    const currentRun = ++run.current;
    if (!zpl) {
      setBusy(false);
      onBusyChange?.(false);
      setError("");
      setStatus("");
      return;
    }
    const validation = validarZpl(zpl);
    if (validation) {
      setBusy(false);
      onBusyChange?.(false);
      setError(validation);
      setStatus("");
      return;
    }
    if (value.campos.nome && value.campos.cidade && value.campos.pedido) {
      setBusy(false);
      onBusyChange?.(false);
      setError("");
      setStatus("Dados salvos carregados. Confira ou corrija antes de gerar o PDF.");
      return;
    }
    const timer = window.setTimeout(async () => {
      setBusy(true);
      onBusyChange?.(true);
      setError("");
      setStatus("Lendo destinatário e número do pedido…");
      try {
        const campos = await lerZplVenda(zpl, setStatus);
        if (currentRun !== run.current) return;
        latest.current({ ...value, campos });
        setStatus(
          campos.nome || campos.cidade || campos.pedido
            ? "Etiqueta lida. Confira os dados antes de salvar."
            : "Etiqueta válida, mas os dados não puderam ser lidos automaticamente.",
        );
      } catch (err) {
        if (currentRun === run.current) setError((err as Error).message);
      } finally {
        if (currentRun === run.current) {
          setBusy(false);
          onBusyChange?.(false);
        }
      }
    }, 650);
    return () => {
      window.clearTimeout(timer);
      if (run.current === currentRun) run.current += 1;
    };
    // A leitura deve repetir apenas quando o conteúdo ZPL muda.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value.zpl]);

  async function readFile(file?: File) {
    if (!file) return;
    if (file.size > 5_000_000) {
      setError("O arquivo ultrapassa o limite de 5 MB.");
      return;
    }
    const zpl = await file.text();
    onChange({ ...emptySaleLabel(), zpl, source_name: file.name });
  }

  async function pdf(action: "download" | "print") {
    const janela = action === "print" ? window.open("", "_blank") : null;
    setBusy(true);
    onBusyChange?.(true);
    setError("");
    try {
      const campos = action === "download"
        ? await baixarPdfVenda(value, setStatus)
        : await abrirPdfVenda(value, janela, setStatus);
      onChange({ ...value, campos });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
      onBusyChange?.(false);
    }
  }

  const resumo = [
    value.campos.pedido && `Pedido ${value.campos.pedido}`,
    value.campos.nome,
    [value.campos.cidade, value.campos.uf].filter(Boolean).join(" / "),
  ].filter(Boolean);

  return (
    <div className="rounded-md border p-4 space-y-3">
      <div>
        <h3>Etiqueta ZPL (opcional)</h3>
        <p className="text-sm text-muted-foreground">
          Cole o código ou escolha o .txt. O número do pedido será preenchido automaticamente quando for localizado.
        </p>
      </div>
      <div>
        <label htmlFor={`${idPrefix}-file`}>Arquivo .txt</label>
        <Input
          id={`${idPrefix}-file`}
          type="file"
          accept=".txt,text/plain"
          disabled={busy}
          onChange={(event) => {
            void readFile(event.target.files?.[0]);
            event.currentTarget.value = "";
          }}
        />
      </div>
      <div>
        <label htmlFor={`${idPrefix}-zpl`}>Código ZPL</label>
        <textarea
          id={`${idPrefix}-zpl`}
          rows={5}
          value={value.zpl}
          className="w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm"
          placeholder="^XA ... ^XZ"
          onChange={(event) =>
            onChange({ ...emptySaleLabel(), zpl: event.target.value, source_name: value.source_name })
          }
        />
      </div>
      {value.zpl && (
        <button
          type="button"
          className="text-sm underline"
          disabled={busy}
          onClick={() => onChange(emptySaleLabel())}
        >
          Retirar etiqueta desta venda
        </button>
      )}
      {status && <p role="status" className="text-sm text-muted-foreground">{status}</p>}
      <ErrorMessage message={error} />
      {value.zpl && (
        <div className="grid sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2">
            <label htmlFor={`${idPrefix}-order`}>Número do pedido identificado</label>
            <Input id={`${idPrefix}-order`} maxLength={100} value={value.campos.pedido}
              onChange={(event) => onChange({
                ...value, campos: { ...value.campos, pedido: event.target.value.trim().toUpperCase() },
              })} />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor={`${idPrefix}-name`}>Nome do destinatário</label>
            <Input id={`${idPrefix}-name`} maxLength={200} value={value.campos.nome}
              onChange={(event) => onChange({
                ...value, campos: { ...value.campos, nome: event.target.value },
              })} />
          </div>
          <div>
            <label htmlFor={`${idPrefix}-city`}>Cidade</label>
            <Input id={`${idPrefix}-city`} maxLength={120} value={value.campos.cidade}
              onChange={(event) => onChange({
                ...value, campos: { ...value.campos, cidade: event.target.value },
              })} />
          </div>
          <div>
            <label htmlFor={`${idPrefix}-state`}>Estado / UF</label>
            <Input id={`${idPrefix}-state`} maxLength={60} value={value.campos.uf}
              onChange={(event) => onChange({
                ...value, campos: { ...value.campos, uf: event.target.value },
              })} />
          </div>
        </div>
      )}
      {resumo.length > 0 && (
        <p className="text-sm rounded-md bg-muted p-3">
          <strong>Leitura:</strong> {resumo.join(" · ")}
        </p>
      )}
      {allowPdfActions && value.zpl && !validarZpl(value.zpl) && (
        <div className="flex flex-col sm:flex-row gap-2">
          <Button type="button" variant="outline" disabled={busy} onClick={() => void pdf("download")}>
            Baixar PDF
          </Button>
          <Button type="button" variant="outline" disabled={busy} onClick={() => void pdf("print")}>
            Abrir para imprimir
          </Button>
        </div>
      )}
    </div>
  );
}
