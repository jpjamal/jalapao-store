"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Button } from "./ui/button";
import { api, BASE } from "@/lib/api";
import {
  LayoutDashboard,
  Package,
  Boxes,
  ShoppingBag,
  Wallet,
  Calculator,
  LogOut,
} from "lucide-react";
const navigation = [
  ["/", "Visão geral", LayoutDashboard],
  ["/produtos", "Produtos", Package],
  ["/estoque", "Estoque", Boxes],
  ["/vendas", "Vendas", ShoppingBag],
  ["/caixa", "Caixa", Wallet],
  ["/ferramentas", "Ferramentas", Calculator],
] as const;
export function Shell({
  children,
  username,
}: {
  children: React.ReactNode;
  username: string;
}) {
  const path = usePathname();
  const [error, setError] = useState("");
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[230px_1fr]">
      <aside className="bg-card border-b lg:border-r p-5 lg:sticky lg:top-0 lg:h-screen flex flex-col">
        <Link href="/" className="mb-8">
          <img
            src={`${BASE}/assets/logo-jalapao.svg`}
            alt="Jalapão Store"
            className="w-36"
          />
        </Link>
        <p className="text-xs tracking-[.2em] uppercase text-muted-foreground mb-4">
          Gestão da loja
        </p>
        <nav className="flex lg:flex-col gap-1 overflow-x-auto">
          {navigation.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              aria-current={path === href ? "page" : undefined}
              className={`flex items-center gap-3 rounded-md px-3 py-3 whitespace-nowrap ${path === href ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="mt-5 lg:mt-auto border-t pt-4 text-sm">
          <p className="mb-3 text-muted-foreground">{username}</p>
          <Button
            variant="ghost"
            onClick={async () => {
              try {
                await api("auth/logout", { method: "POST", body: "{}" });
                window.location.assign(`${BASE}/login`);
              } catch {
                setError("Falha ao sair. Tente novamente.");
              }
            }}
          >
            <LogOut size={16} /> Sair
          </Button>
          {error && <p role="alert">{error}</p>}
        </div>
      </aside>
      <main className="p-5 md:p-9 max-w-[1440px] w-full mx-auto min-w-0">
        {children}
      </main>
    </div>
  );
}
