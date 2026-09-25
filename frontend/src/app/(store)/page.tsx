"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, brl } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { ErrorMessage } from "@/components/feedback";
import { PageHeader } from "@/components/page-header";
type Certificate = {
  expires_at: string;
  days_left: number;
  alert: boolean;
} | null;
type AuthorizationAlert = {
  channel: string;
  channel_label: string;
  name: string;
  days_left: number;
  expires_at: string;
};
type Summary = {
  stock_value: string;
  gross: string;
  profit: string;
  receivable: string;
  cash_balance: string;
  product_count: number;
  certificate?: Certificate;
  authorization_alerts?: AuthorizationAlert[];
};

/* A autorização de uma loja de marketplace vence calada: o token renova normalmente até o
   dia em que não renova mais, e a sincronia simplesmente para. Aviso antes, no painel. */
function AvisoAutorizacao({ avisos }: { avisos: AuthorizationAlert[] }) {
  if (!avisos.length) return null;
  return (
    <div
      role="alert"
      className="border border-destructive text-destructive rounded-md p-4 mb-6"
    >
      <b>Autorização de marketplace perto de vencer.</b>
      <ul className="list-disc pl-5 mt-2 space-y-1">
        {avisos.map((a) => (
          <li key={`${a.channel}-${a.name}`}>
            {a.channel_label} · {a.name} —{" "}
            {a.days_left < 0
              ? "já venceu"
              : `${a.days_left} dia${a.days_left === 1 ? "" : "s"}`}
            , até{" "}
            {new Date(a.expires_at).toLocaleDateString("pt-BR")}
          </li>
        ))}
      </ul>
      <p className="mt-2">
        Quando vencer, a sincronia para sem avisar.{" "}
        <Link href="/integracoes" className="underline font-semibold">
          Autorizar de novo
        </Link>
        .
      </p>
    </div>
  );
}

/* O certificado é de IP, com perfil shortlived: dura ~6 dias e o certbot tenta
   renovar a cada 12h. Se a renovação falhar em silêncio o site cai — então o
   painel passa a mostrar os dias restantes, e grita quando encurtam demais. */
function AvisoCertificado({ cert }: { cert: Certificate }) {
  if (!cert) return null;
  const dias = cert.days_left;
  const quando = new Date(cert.expires_at).toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
  if (!cert.alert)
    return (
      <p className="text-sm text-muted-foreground mt-6">
        Certificado HTTPS válido por mais {dias} dia{dias === 1 ? "" : "s"}, até{" "}
        {quando}. A renovação é automática.
      </p>
    );
  return (
    <div
      role="alert"
      className="border border-destructive text-destructive rounded-md p-4 mb-6"
    >
      <b>
        {dias < 0
          ? "O certificado HTTPS venceu."
          : `O certificado HTTPS vence em ${dias} dia${dias === 1 ? "" : "s"} (${quando}).`}
      </b>{" "}
      A renovação automática devia ter acontecido antes disso — provavelmente
      falhou. Confira o certbot na VPS com{" "}
      <code>docker compose … logs --tail 100 certbot</code> antes que o site saia
      do ar.
    </div>
  );
}
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
      <PageHeader
        eyebrow="O dia a dia da sua loja"
        title="Visão geral"
        description="Acompanhe o que você tem, vendeu e recebeu."
      />
      <ErrorMessage message={error} />
      {data?.authorization_alerts?.length ? (
        <AvisoAutorizacao avisos={data.authorization_alerts} />
      ) : null}
      {data?.certificate?.alert && <AvisoCertificado cert={data.certificate} />}
      {!data && !error ? (
        <p role="status">Carregando indicadores…</p>
      ) : (
        data && (
          <div className="grid grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4">
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
              <Card key={title} className="p-3 sm:p-6">
                <p className="text-sm sm:text-base text-muted-foreground mb-2 sm:mb-4">{title}</p>
                <p className="money text-lg sm:text-3xl mb-1 sm:mb-3">{value}</p>
                <p className="text-xs sm:text-sm text-muted-foreground">{help}</p>
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
        <div className="flex flex-col sm:flex-row gap-1 sm:gap-5 text-primary font-semibold">
          <Link href="/estoque" className="py-2">Movimentar estoque →</Link>
          <Link href="/vendas" className="py-2">Registrar venda →</Link>
        </div>
      </Card>
      {data?.certificate && !data.certificate.alert && (
        <AvisoCertificado cert={data.certificate} />
      )}
    </>
  );
}
