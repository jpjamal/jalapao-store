"use client";
import { useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import type { NoCategoria } from "@/features/listings/types";

/* Árvore de categorias vinda direto do Mercado Livre: começa no primeiro nível e desce
   até uma categoria final, que é a única onde o anúncio entra. */
export function NavegadorCategorias({
  categoryId,
  onCategoria,
  onAbrir,
}: {
  categoryId: string;
  onCategoria: (id: string) => void;
  /** avisa cada categoria aberta, de qualquer nível (a pesquisa de preços usa) */
  onAbrir?: (categoria: { id: string; name: string; path: string[] }) => void;
}) {
  const [no, setNo] = useState<NoCategoria | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");

  async function abrir(id: string) {
    setCarregando(true);
    setErro("");
    try {
      const r = await api<NoCategoria>(
        `listing-drafts/ml-category-tree${id ? `?category_id=${encodeURIComponent(id)}` : ""}`,
      );
      setNo(r);
      onAbrir?.({ id: r.id, name: r.name, path: r.path.map((p) => p.name) });
      if (r.id && r.listing_allowed && r.id !== categoryId) onCategoria(r.id);
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setCarregando(false);
    }
  }

  // rascunho aberto ou sugestão escolhida: posiciona a árvore na categoria
  useEffect(() => {
    if (!no || categoryId !== no.id) void abrir(categoryId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryId]);

  const final = no && no.id && no.listing_allowed;
  return (
    <div className="rounded-lg border p-3">
      <nav aria-label="Caminho da categoria" className="flex flex-wrap items-center gap-1 text-sm mb-2">
        <button type="button" className="underline cursor-pointer" onClick={() => void abrir("")}>
          Todas
        </button>
        {no?.path.map((p) => (
          <span key={p.id} className="flex items-center gap-1">
            ›
            <button
              type="button"
              className={p.id === no.id ? "font-semibold" : "underline cursor-pointer"}
              disabled={p.id === no.id}
              onClick={() => void abrir(p.id)}
            >
              {p.name}
            </button>
          </span>
        ))}
      </nav>
      {carregando && <p role="status" className="text-sm">Carregando categorias…</p>}
      {erro && (
        <p role="alert" className="text-sm text-destructive">
          {erro}
        </p>
      )}
      {final && (
        <p className="text-sm text-[var(--success)]">
          ✓ Categoria final escolhida ({no.id}).
        </p>
      )}
      {no && no.children.length > 0 && (
        <>
          <p className="text-sm text-muted-foreground mb-2">
            {no.id ? "Escolha uma subcategoria:" : "Escolha a categoria:"}
          </p>
          <ul className="grid sm:grid-cols-2 gap-1 max-h-72 overflow-y-auto">
            {no.children.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  className="text-left w-full rounded-md border px-3 py-2 text-sm hover:bg-muted cursor-pointer"
                  onClick={() => void abrir(c.id)}
                >
                  {c.name}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
