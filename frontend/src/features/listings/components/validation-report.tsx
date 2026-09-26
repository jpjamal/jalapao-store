"use client";
import type { Relatorio } from "@/features/listings/types";

/* Relatório da validação do rascunho no Mercado Livre: erros impedem publicar, avisos não. */
export function RelatorioValidacao({ relatorio }: { relatorio: Relatorio }) {
  const { pode_publicar, simulado_no_mercado_livre, erros, avisos } = relatorio;
  return (
    <div
      role="status"
      className={`rounded-lg border p-4 mt-5 ${
        pode_publicar ? "border-[var(--success)]" : "border-destructive"
      }`}
    >
      <p className="font-semibold mb-2">
        {pode_publicar
          ? "Pronto para publicar no Mercado Livre."
          : erros.length
            ? `${erros.length} ${erros.length === 1 ? "problema impede" : "problemas impedem"} a publicação.`
            : "Não foi possível concluir a validação."}
      </p>
      <p className="text-sm text-muted-foreground mb-3">
        {simulado_no_mercado_livre
          ? "Conferido aqui e simulado no Mercado Livre, sem criar anúncio."
          : "Conferido só aqui: corrija os itens básicos para a simulação no Mercado Livre rodar."}
        {relatorio.causas_de_foto_retiradas > 0 &&
          " As fotos são conferidas aqui; na simulação elas não vão."}
      </p>
      {erros.length > 0 && (
        <ul className="space-y-1 mb-3">
          {erros.map((e, i) => (
            <li key={i} className="text-destructive text-sm">
              ✕ {e.mensagem}
              {e.origem === "mercado_livre" && (
                <span className="text-muted-foreground"> · Mercado Livre{e.codigo ? ` (${e.codigo})` : ""}</span>
              )}
            </li>
          ))}
        </ul>
      )}
      {avisos.length > 0 && (
        <ul className="space-y-1">
          {avisos.map((a, i) => (
            <li key={i} className="text-sm">
              ! {a.mensagem}
              {a.origem === "mercado_livre" && (
                <span className="text-muted-foreground"> · Mercado Livre</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
