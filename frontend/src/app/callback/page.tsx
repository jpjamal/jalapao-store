import Link from "next/link";
import { Card } from "@/components/ui/card";
export default function Callback() {
  return (
    <main className="min-h-screen grid place-items-center p-6">
      <Card className="max-w-xl">
        <h1>Mercado Livre</h1>
        <p className="mb-6">
          O endereço de retorno está preparado. A integração ainda não foi
          ativada: nenhuma conta foi vinculada e nenhum anúncio ou estoque foi
          alterado.
        </p>
        <Link href="/" className="text-primary">
          Voltar à Jalapão Store →
        </Link>
      </Card>
    </main>
  );
}
