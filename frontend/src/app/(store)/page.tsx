"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, brl } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { ErrorMessage } from "@/components/feedback";
type Summary = {
  stock_value: string;
  gross: string;
  profit: string;
  receivable: string;
  cash_balance: string;
  product_count: number;
};
export default function Dashboard() {
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Summary>("dashboard")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <>
      <p className="text-xs tracking-widest uppercase text-muted-foreground mb-3">
        O dia a dia da sua loja
      </p>
      <h1>Visão geral</h1>
      <p className="text-muted-foreground mb-8">
        Acompanhe o que você tem, vendeu e recebeu.
      </p>
      <ErrorMessage message={error} />
      {!data && !error ? (
        <p role="status">Carregando indicadores…</p>
      ) : (
        data && (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            {[
              [
                "Estoque a custo",
                brl(data.stock_value),
                "Valor das unidades pelo custo médio",
              ],
              [
                "Faturamento",
                brl(data.gross),
                "Valor bruto das vendas confirmadas",
              ],
              [
                "Lucro estimado",
                brl(data.profit),
                "Após custo, descontos, taxas e frete",
              ],
              [
                "Saldo de caixa",
                brl(data.cash_balance),
                "Entradas recebidas menos saídas",
              ],
              [
                "A receber",
                brl(data.receivable),
                "Vendas ainda sem recebimento",
              ],
              [
                "Produtos ativos",
                data.product_count,
                "Catálogo disponível para venda",
              ],
            ].map(([title, value, help]) => (
              <Card key={title}>
                <p className="text-muted-foreground mb-4">{title}</p>
                <p className="money text-3xl mb-3">{value}</p>
                <p className="text-sm text-muted-foreground">{help}</p>
              </Card>
            ))}
          </div>
        )
      )}
      <Card className="mt-8">
        <h2>Comece pelo estoque</h2>
        <p className="text-muted-foreground mb-4">
          Os produtos antigos mantêm seus parâmetros. Informe as quantidades
          disponíveis antes de registrar a primeira venda.
        </p>
        <div className="flex gap-5 text-primary font-semibold">
          <Link href="/estoque">Movimentar estoque →</Link>
          <Link href="/vendas">Registrar venda →</Link>
        </div>
      </Card>
    </>
  );
}
