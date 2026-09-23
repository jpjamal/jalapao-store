"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { api, BASE } from "@/lib/api";
export default function Login() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
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
          {error && (
            <p role="alert" className="text-destructive whitespace-pre-wrap">
              {error}
            </p>
          )}
          <Button className="w-full" disabled={busy}>
            {busy ? "Entrando…" : "Entrar"}
          </Button>
        </form>
      </Card>
    </main>
  );
}
