"use client";
import { useState } from "react";
import { api, brl } from "@/lib/api";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Empty } from "./feedback";
import { FormActions } from "./form-actions";

/* Spec 015 — importar vendas do Mercado Livre sob comando do dono: buscar mostra a prévia,
   importar cria as vendas (baixando estoque) e cancela as dos pedidos cancelados. */

type Item = { item_id: string; titulo: string; quantidade: number; preco: number; produto: string };
type Pedido = {
  order_id: string;
  data: string;
  status: string;
  itens: Item[];
  bruto: number;
  taxa: number;
  frete: number | null;
  liquido: number;
  problemas: string[];
  avisos: string[];
  situacao: "nova" | "importada" | "pendente" | "cancelar";
};
type Resultado = {
  importadas: string[];
  canceladas: string[];
  ignoradas: { order_id: string; motivo: string }[];
  falhas: { order_id: string; motivo: string }[];
};

const situacoes: Record<Pedido["situacao"], string> = {
  nova: "Nova — pronta para importar",
  importada: "Já importada",
  pendente: "Pendente — corrija antes",
  cancelar: "Cancelada no Mercado Livre — cancelar aqui",
};
const selecionavel = (p: Pedido) => p.situacao === "nova" || p.situacao === "cancelar";
const quando = (iso: string) => (iso ? new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "—");

export function ImportarVendasML({ onImportado }: { onImportado: () => void }) {
  const [dias, setDias] = useState(30);
  const [pedidos, setPedidos] = useState<Pedido[] | null>(null);
  const [escolhidos, setEscolhidos] = useState<string[]>([]);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [ocupado, setOcupado] = useState("");
  const [erro, setErro] = useState("");

  async function buscar() {
    setOcupado("buscar"); setErro(""); setResultado(null);
    try {
      const r = await api<{ pedidos: Pedido[] }>(`sales/ml-preview?days=${dias}`);
      setPedidos(r.pedidos);
      setEscolhidos(r.pedidos.filter(selecionavel).map((p) => p.order_id));
    } catch (e) { setErro((e as Error).message); }
    finally { setOcupado(""); }
  }

  async function importar() {
    setOcupado("importar"); setErro("");
    try {
      const r = await api<Resultado>("sales/ml-import", {
        method: "POST", body: JSON.stringify({ order_ids: escolhidos }),
      });
      setResultado(r);
      onImportado();
      await buscar();
    } catch (e) { setErro((e as Error).message); }
    finally { setOcupado(""); }
  }

  const alternar = (id: string) =>
    setEscolhidos((antes) => (antes.includes(id) ? antes.filter((i) => i !== id) : [...antes, id]));

  return (
    <Card className="mb-5">
      <h2>Importar vendas do Mercado Livre</h2>
      <p className="text-sm text-muted-foreground mb-4">
        Busca os pedidos pagos e cancelados. Nada muda até você importar: cada pedido vira uma venda
        com a taxa e o frete cobrados pelo Mercado Livre, baixa o estoque e fica a receber — entra no
        caixa quando você marcar como recebida.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 sm:items-end mb-4">
        <div>
          <label htmlFor="dias">Período</label>
          <select id="dias" value={dias} onChange={(e) => setDias(Number(e.target.value))} className="sm:w-48">
            {[7, 15, 30, 60, 90].map((d) => <option key={d} value={d}>Últimos {d} dias</option>)}
          </select>
        </div>
        <Button variant="outline" disabled={!!ocupado} onClick={() => void buscar()}>
          {ocupado === "buscar" ? "Buscando…" : "Buscar vendas"}
        </Button>
      </div>

      {erro && <p role="alert" className="text-sm text-destructive mb-3 whitespace-pre-wrap">{erro}</p>}

      {resultado && <div role="status" className="rounded-lg border border-[var(--success)] p-3 mb-4 text-sm">
        <p className="font-semibold">
          {resultado.importadas.length} importada{resultado.importadas.length === 1 ? "" : "s"},{" "}
          {resultado.canceladas.length} cancelada{resultado.canceladas.length === 1 ? "" : "s"}
          {resultado.falhas.length ? `, ${resultado.falhas.length} com falha` : ""}.
        </p>
        {[...resultado.falhas, ...resultado.ignoradas].map((f) => (
          <p key={f.order_id} className="text-muted-foreground">Pedido {f.order_id}: {f.motivo}</p>
        ))}
      </div>}

      {pedidos && (!pedidos.length ? <Empty>Nenhum pedido pago ou cancelado no período.</Empty> : <>
        <ul className="space-y-2">
          {pedidos.map((p) => (
            <li key={p.order_id} className={`rounded-lg border p-3 ${escolhidos.includes(p.order_id) ? "border-primary" : ""}`}>
              <label className={`flex gap-3 ${selecionavel(p) ? "cursor-pointer" : ""}`}>
                <input type="checkbox" className="h-5 w-5 mt-0.5 shrink-0 accent-[var(--primary)]"
                  disabled={!selecionavel(p)} checked={escolhidos.includes(p.order_id)}
                  onChange={() => alternar(p.order_id)} aria-label={`Selecionar pedido ${p.order_id}`} />
                <span className="min-w-0 grow">
                  <span className="flex flex-wrap justify-between gap-x-3">
                    <b>Pedido {p.order_id}</b>
                    <span className="text-sm text-muted-foreground">{quando(p.data)}</span>
                  </span>
                  {p.itens.map((i) => (
                    <span key={i.item_id} className="block text-sm">
                      {i.quantidade}× {i.produto || i.titulo}
                    </span>
                  ))}
                  <span className="grid grid-cols-2 sm:grid-cols-4 gap-x-3 text-sm mt-1">
                    <span>Bruto <b className="money">{brl(p.bruto)}</b></span>
                    <span>Taxa <b className="money">{brl(p.taxa)}</b></span>
                    <span>Frete <b className="money">{p.frete === null ? "?" : brl(p.frete)}</b></span>
                    <span>Líquido <b className="money">{brl(p.liquido)}</b></span>
                  </span>
                  <span className={`block text-xs mt-1 ${p.situacao === "pendente" ? "text-destructive" : "text-muted-foreground"}`}>
                    {situacoes[p.situacao]}
                  </span>
                  {[...p.problemas, ...p.avisos].map((m) => <span key={m} className="block text-xs text-destructive">{m}</span>)}
                </span>
              </label>
            </li>
          ))}
        </ul>
        <FormActions className="mt-4">
          <Button disabled={!escolhidos.length || !!ocupado} onClick={() => void importar()}>
            {ocupado === "importar" ? "Importando…" : `Importar ${escolhidos.length} selecionado${escolhidos.length === 1 ? "" : "s"}`}
          </Button>
        </FormActions>
      </>)}
    </Card>
  );
}
