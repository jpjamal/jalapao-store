"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Card } from "@/shared/ui/card";
import { api, BASE } from "@/shared/api/client";

const UNAVAILABLE = "Este link não está mais disponível";

/* Senha nova pelo link do e-mail (spec 039), sem login. Ao salvar, as sessões abertas da pessoa
   são encerradas e ela segue para o login. */
export default function ResetPassword({ code }: { code: string }) {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [unavailable, setUnavailable] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ email: string }>(`auth/reset-password/${code}`)
      .then((r) => setEmail(r.email))
      .catch((e: Error) => setUnavailable(e.message));
  }, [code]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password !== confirmation) {
      setError("As senhas não conferem.");
      return;
    }
    setBusy(true);
    try {
      await api(`auth/reset-password/${code}`, {
        method: "POST",
        body: JSON.stringify({ password, password_confirmation: confirmation }),
      });
      router.replace("/login?senha=nova");
    } catch (err) {
      const message = (err as Error).message;
      if (message.includes(UNAVAILABLE)) setUnavailable(message);
      else setError(message);
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen grid place-items-center p-6">
      <Card className="w-full max-w-md">
        <img src={`${BASE}/assets/logo-jalapao.svg`} alt="Jalapão Store" className="w-40 mb-8" />
        <h1>Criar senha nova</h1>
        {!email && !unavailable && (
          <p role="status" className="text-muted-foreground">
            Carregando…
          </p>
        )}
        {unavailable && (
          <>
            <p role="alert" className="mb-4 text-destructive">
              {unavailable}
            </p>
            <Link href="/esqueci-senha" className="underline">
              Pedir outro link
            </Link>
          </>
        )}
        {email && !unavailable && (
          <form onSubmit={submit} className="space-y-4">
            <p className="text-muted-foreground">
              Conta {email}. Ao salvar, as sessões abertas em outros aparelhos são encerradas.
            </p>
            <div>
              <label htmlFor="password">Senha nova</label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                required
                autoFocus
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Mínimo 8 caracteres, que não seja comum, só de números nem parecida com o usuário.
              </p>
            </div>
            <div>
              <label htmlFor="confirmation">Confirme a senha</label>
              <Input
                id="confirmation"
                type="password"
                autoComplete="new-password"
                required
                value={confirmation}
                onChange={(e) => setConfirmation(e.target.value)}
              />
            </div>
            {error && (
              <p role="alert" className="text-destructive whitespace-pre-wrap">
                {error}
              </p>
            )}
            <Button className="w-full" disabled={busy}>
              {busy ? "Salvando…" : "Salvar senha nova"}
            </Button>
          </form>
        )}
      </Card>
    </main>
  );
}
