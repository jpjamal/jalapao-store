"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Card } from "@/shared/ui/card";
import { api, BASE } from "@/shared/api/client";
export default function Login() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [emailOn, setEmailOn] = useState(false);
  const [senhaNova, setSenhaNova] = useState(false);
  useEffect(() => {
    // "Esqueci minha senha" só aparece com o envio de e-mail ligado (spec 039)
    api<{ email_configured: boolean }>("auth/resources")
      .then((r) => setEmailOn(r.email_configured))
      .catch(() => setEmailOn(false));
    setSenhaNova(new URLSearchParams(window.location.search).get("senha") === "nova");
  }, []);
  return (
    <main className="min-h-screen grid place-items-center p-6">
      <Card className="w-full max-w-md">
        <img
          src={`${BASE}/assets/logo-jalapao.svg`}
          alt="Jalapão Store"
          className="w-40 mb-8"
        />
        <p className="uppercase tracking-widest text-xs text-muted-foreground mb-3">
          Gestão da loja
        </p>
        <h1>Bem-vindo de volta.</h1>
        <p className="mb-6 text-muted-foreground">
          Seus produtos, estoque e resultados em um só lugar.
        </p>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            const data = new FormData(e.currentTarget);
            try {
              await api("auth/login", {
                method: "POST",
                body: JSON.stringify(Object.fromEntries(data)),
              });
              router.replace("/");
              router.refresh();
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
            }
          }}
          className="space-y-4"
        >
          <div>
            <label htmlFor="username">Usuário</label>
            <Input
              id="username"
              name="username"
              autoComplete="username"
              required
              autoFocus
            />
          </div>
          <div>
            <label htmlFor="password">Senha</label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </div>
          {senhaNova && !error && (
            <p role="status" className="text-sm text-primary">
              Senha nova criada. Entre com ela.
            </p>
          )}
          {error && (
            <p role="alert" className="text-destructive whitespace-pre-wrap">
              {error}
            </p>
          )}
          <Button className="w-full" disabled={busy}>
            {busy ? "Entrando…" : "Entrar"}
          </Button>
          {emailOn && (
            <p className="text-center text-sm">
              <Link href="/esqueci-senha" className="underline">
                Esqueci minha senha
              </Link>
            </p>
          )}
        </form>
      </Card>
    </main>
  );
}
