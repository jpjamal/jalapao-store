"use client";
import { useEffect, useRef, useState } from "react";
import { FileUp } from "lucide-react";
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
  const [dragging, setDragging] = useState(false);
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
    if (value.campos.pedido) {
      setBusy(false);
      onBusyChange?.(false);
      setError("");
      setStatus("Etiqueta carregada.");
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
          campos.pedido
            ? "Número do pedido lido; confira a referência acima."
            : "Etiqueta válida, mas o número do pedido não foi lido: digite-o na referência.",
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

  // Soltar um arquivo fora da área faria o navegador abri-lo e sair do sistema.
  useEffect(() => {
    const guard = (event: DragEvent) => {
      if (event.dataTransfer?.types.includes("Files")) event.preventDefault();
    };
    window.addEventListener("dragover", guard);
    window.addEventListener("drop", guard);
    return () => {
      window.removeEventListener("dragover", guard);
      window.removeEventListener("drop", guard);
    };
  }, []);

  async function readFile(file?: File) {
    if (!file) return;
    if (file.size > 5_000_000) {
      setError("O arquivo ultrapassa o limite de 5 MB.");
      return;
    }
    setError("");
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

  return (
    <div className="rounded-md border p-4 space-y-3">
      <div>
        <h3>Etiqueta ZPL (opcional)</h3>
        <p className="text-sm text-muted-foreground">
          Arraste o arquivo ou clique para escolher. O número do pedido será preenchido automaticamente quando for localizado.
        </p>
      </div>
      <div>
        <input
          id={`${idPrefix}-file`}
          type="file"
          accept=".txt,.zpl,text/plain,application/octet-stream"
          disabled={busy}
          className="sr-only"
          onChange={(event) => {
            void readFile(event.target.files?.[0]);
            event.currentTarget.value = "";
          }}
        />
        <label
          htmlFor={`${idPrefix}-file`}
          className={`flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-5 text-center transition-colors ${
            dragging ? "border-primary bg-muted" : "border-input hover:bg-muted/60"
          } ${busy ? "pointer-events-none opacity-50" : ""}`}
          onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
          onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
          onDragLeave={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
          }}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            void readFile(event.dataTransfer.files?.[0]);
          }}
        >
          <FileUp size={28} aria-hidden className="mb-2 text-primary" />
          <strong>{value.zpl ? "Etiqueta carregada" : "Arraste o arquivo ZPL aqui"}</strong>
          <span className="mt-1 text-sm text-muted-foreground">
            {value.zpl
              ? `${value.source_name || "ZPL salvo"} · arraste ou clique para substituir`
              : "ou clique para escolher um arquivo .txt ou .zpl"}
          </span>
        </label>
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
