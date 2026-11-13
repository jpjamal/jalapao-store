"use client";
import { useState } from "react";
import Link from "next/link";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Card } from "@/shared/ui/card";
import { api, BASE } from "@/shared/api/client";

/* Esqueci minha senha (spec 039): a resposta é a mesma exista ou não a conta. O link chega por
   e-mail, vale 1 hora e abre a página de senha nova. */
export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api<{ message: string }>("auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email: email.trim() }),
      });
      setMessage(r.message);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen grid place-items-center p-6">
      <Card className="w-full max-w-md">
        <img src={`${BASE}/assets/logo-jalapao.svg`} alt="Jalapão Store" className="w-40 mb-8" />
        <h1>Esqueci minha senha</h1>
        {message ? (
          <p role="status" className="mb-6 text-muted-foreground">
            {message} O link vale por 1 hora. Veja também a caixa de spam.
          </p>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <p className="text-muted-foreground">
              Informe o e-mail da sua conta. Enviamos um link para você criar uma senha nova.
            </p>
            <div>
              <label htmlFor="email">E-mail</label>
              <Input
                id="email"
                name="email"
                type="email"
                inputMode="email"
                autoComplete="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            {error && (
              <p role="alert" className="text-destructive whitespace-pre-wrap">
                {error}
              </p>
            )}
            <Button className="w-full" disabled={busy}>
              {busy ? "Enviando…" : "Enviar link"}
            </Button>
          </form>
        )}
        <p className="mt-6 text-center text-sm">
          <Link href="/login" className="underline">
            Voltar para entrar
          </Link>
        </p>
      </Card>
    </main>
  );
}
