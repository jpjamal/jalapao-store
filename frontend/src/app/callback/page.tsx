"use client";
import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { api, BASE } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { ErrorMessage } from "@/components/feedback";

/* Retorno da autorização. O state do Mercado Livre é validado no backend. */

function Troca() {
  const params = useSearchParams();
  const code = params.get("code");
  const shopId = params.get("shop_id");
  const state = params.get("state");
  const canal = shopId ? "shopee" : state ? "mercado_livre" : "";
  const erroOAuth = params.get("error");

  const [estado, setEstado] = useState<"parado" | "trocando" | "pronto">("parado");
  const [erro, setErro] = useState("");
  const [loja, setLoja] = useState("");
  const iniciado = useRef(false);

  useEffect(() => {
    if (!code || !canal || (canal === "shopee" && !shopId) || (canal === "mercado_livre" && !state)) return;
    if (iniciado.current) return;
    iniciado.current = true;
    setEstado("trocando");
    api<{ name: string; external_id: string }>("integrations/connect", {
      method: "POST",
      body: JSON.stringify(canal === "shopee"
        ? { channel: canal, code, external_id: shopId }
        : { channel: canal, code, state }),
    })
      .then((c) => {
        setLoja(c.name || c.external_id);
        setEstado("pronto");
      })
      .catch((e) => {
        setErro((e as Error).message);
        setEstado("pronto");
      });
  }, [code, shopId, state, canal]);

  if (!code) {
    return (
      <>
        <h1>Endereço de retorno</h1>
        {erroOAuth && <ErrorMessage message="O Mercado Livre não autorizou a conexão. Inicie novamente em Integrações." />}
        <p className="mb-6">
          É para cá que o marketplace devolve depois da autorização. Abrir esta
          página direto não faz nada — comece por{" "}
          <Link href="/integracoes" className="text-primary">
            Integrações
          </Link>
          .
        </p>
      </>
    );
  }

  return (
    <>
      <h1>Autorização</h1>
      <ErrorMessage message={erro} />
      {estado === "trocando" && <p role="status">Guardando a autorização…</p>}
      {estado === "pronto" && !erro && (
        <p className="mb-6">
          Loja <b>{loja}</b> conectada. Nada do catálogo foi alterado — o próximo
          passo é importar os anúncios, em Integrações.
        </p>
      )}
      {estado === "pronto" && erro && (
        <p className="mb-6 text-muted-foreground">
          O código de autorização vale poucos minutos. Se expirou, comece de novo
          em Integrações.
        </p>
      )}
      <Link href="/integracoes" className="text-primary">
        Ir para Integrações →
      </Link>
    </>
  );
}

export default function Callback() {
  return (
    <main className="min-h-screen grid place-items-center p-6">
      <Card className="max-w-xl">
        <Suspense fallback={<p role="status">Carregando…</p>}>
          <Troca />
        </Suspense>
        <p className="text-sm text-muted-foreground mt-6">
          É preciso estar logado na Jalapão Store para a autorização ser guardada.{" "}
          <a href={`${BASE}/login`} className="underline">
            Entrar
          </a>
        </p>
      </Card>
    </main>
  );
}
