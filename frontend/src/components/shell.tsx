"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Button } from "./ui/button";
import { api, BASE } from "@/lib/api";
import {
  LayoutDashboard,
  Package,
  Images,
  Boxes,
  ShoppingBag,
  PackagePlus,
  Wallet,
  Calculator,
  Plug,
  LogOut,
  Menu,
  SearchCheck,
  X,
} from "lucide-react";

type Item = { href: string; label: string; Icon: typeof Package };
const groups: { title: string; items: Item[] }[] = [
  {
    title: "Loja",
    items: [
      { href: "/", label: "Visão geral", Icon: LayoutDashboard },
      { href: "/produtos", label: "Produtos", Icon: Package },
      { href: "/estoque", label: "Estoque", Icon: Boxes },
      { href: "/entradas", label: "Compras / produção", Icon: PackagePlus },
      { href: "/vendas", label: "Vendas", Icon: ShoppingBag },
      { href: "/caixa", label: "Caixa", Icon: Wallet },
    ],
  },
  {
    title: "Marketplaces",
    items: [
      { href: "/anuncios", label: "Anúncios", Icon: Images },
      { href: "/pesquisa-precos", label: "Pesquisa de mercado", Icon: SearchCheck },
      { href: "/integracoes", label: "Integrações", Icon: Plug },
    ],
  },
  {
    title: "Apoio",
    items: [{ href: "/ferramentas", label: "Ferramentas", Icon: Calculator }],
  },
];
const items = groups.flatMap((g) => g.items);

// Página atual também nas subpáginas (/ferramentas/etiquetas destaca Ferramentas).
function isActive(path: string, href: string) {
  return href === "/" ? path === "/" : path === href || path.startsWith(`${href}/`);
}

function Navigation({ path, onNavigate }: { path: string; onNavigate?: () => void }) {
  return (
    <nav aria-label="Menu principal" className="flex flex-col gap-5">
      {groups.map((group) => (
        <div key={group.title}>
          <p className="px-3 mb-1 text-xs tracking-[.2em] uppercase text-muted-foreground">
            {group.title}
          </p>
          <ul className="flex flex-col gap-0.5">
            {group.items.map(({ href, label, Icon }) => {
              const active = isActive(path, href);
              return (
                <li key={href}>
                  <Link
                    href={href}
                    onClick={onNavigate}
                    aria-current={active ? "page" : undefined}
                    className={`flex items-center gap-3 rounded-md px-3 min-h-11 text-[0.95rem] lg:text-sm lg:min-h-10 ${
                      active ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                    }`}
                  >
                    <Icon size={18} className="shrink-0" aria-hidden />
                    {label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

export function Shell({
  children,
  username,
}: {
  children: React.ReactNode;
  username: string;
}) {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const menuButton = useRef<HTMLButtonElement>(null);
  const drawer = useRef<HTMLDivElement>(null);
  const current = items.find((i) => isActive(path, i.href));

  // Menu do celular: fecha ao trocar de página e com Esc, trava a rolagem do fundo e
  // devolve o foco ao botão que abriu.
  useEffect(() => setOpen(false), [path]);
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    drawer.current?.querySelector<HTMLElement>("a, button")?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    const button = menuButton.current;
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKey);
      button?.focus();
    };
  }, [open]);

  async function logout() {
    try {
      await api("auth/logout", { method: "POST", body: "{}" });
      window.location.assign(`${BASE}/login`);
    } catch {
      setError("Falha ao sair. Tente novamente.");
    }
  }

  const footer = (
    <div className="border-t pt-4 text-sm">
      <p className="mb-2 px-3 text-muted-foreground">{username}</p>
      <Button variant="ghost" className="w-full justify-start" onClick={() => void logout()}>
        <LogOut size={16} aria-hidden /> Sair
      </Button>
      {error && <p role="alert" className="px-3 mt-2 text-destructive">{error}</p>}
    </div>
  );

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[240px_1fr]">
      <a
        href="#conteudo"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-card focus:px-4 focus:py-2"
      >
        Pular para o conteúdo
      </a>

      {/* celular e tablet: barra fina no topo */}
      <header className="lg:hidden sticky top-0 z-30 flex items-center gap-2 h-14 px-2 border-b bg-card/95 backdrop-blur">
        <Button
          ref={menuButton}
          variant="ghost"
          size="icon"
          aria-label="Abrir menu"
          aria-expanded={open}
          aria-controls="menu-celular"
          onClick={() => setOpen(true)}
        >
          <Menu size={22} aria-hidden />
        </Button>
        <p className="font-[family-name:var(--font-display)] font-semibold truncate">
          {current?.label ?? "Jalapão Store"}
        </p>
        <Link href="/" className="ml-auto shrink-0" aria-label="Ir para a visão geral">
          <img src={`${BASE}/assets/logo-jalapao.svg`} alt="" className="logo h-10 w-10 p-1" />
        </Link>
      </header>

      {open && (
        <div className="lg:hidden fixed inset-0 z-40" role="dialog" aria-modal="true" aria-label="Menu">
          <button
            type="button"
            aria-label="Fechar menu"
            tabIndex={-1}
            className="absolute inset-0 bg-black/50 cursor-default"
            onClick={() => setOpen(false)}
          />
          <div
            id="menu-celular"
            ref={drawer}
            className="absolute inset-y-0 left-0 w-[min(20rem,85vw)] bg-card border-r p-4 flex flex-col gap-4 overflow-y-auto shadow-xl"
          >
            <div className="flex items-center justify-between">
              <img src={`${BASE}/assets/logo-jalapao.svg`} alt="Jalapão Store" className="w-24" />
              <Button variant="ghost" size="icon" aria-label="Fechar menu" onClick={() => setOpen(false)}>
                <X size={22} aria-hidden />
              </Button>
            </div>
            <Navigation path={path} onNavigate={() => setOpen(false)} />
            <div className="mt-auto">{footer}</div>
          </div>
        </div>
      )}

      {/* computador: menu lateral fixo */}
      <aside className="hidden lg:flex flex-col gap-6 bg-card border-r p-5 sticky top-0 h-screen overflow-y-auto">
        <Link href="/">
          <img src={`${BASE}/assets/logo-jalapao.svg`} alt="Jalapão Store" className="w-32" />
        </Link>
        <Navigation path={path} />
        <div className="mt-auto">{footer}</div>
      </aside>

      <main id="conteudo" className="px-4 py-6 sm:px-6 md:px-9 md:py-9 max-w-[1440px] w-full mx-auto min-w-0">
        {children}
      </main>
    </div>
  );
}
