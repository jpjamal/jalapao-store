"use client";
import { useState } from "react";
import { ExternalLink, Search } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Empty, ErrorMessage } from "@/components/feedback";
import { PageHeader } from "@/components/page-header";
import { NavegadorCategorias } from "@/components/ml-anuncio";

/* Spec 013 — pesquisa no Mercado Livre: produtos do catálogo e mais vendidos por categoria.
   Só consulta. Preço de concorrente não vem pela API; o link leva ao Mercado Livre para ver. */

type Cartao = {
  id: string;
  nome: string;
  familia: string;
  marca: string;
  modelo: string;
  foto: string;
  link: string;
  posicao?: number;
};

function Foto({ src, alt }: { src: string; alt: string }) {
  return src ? (
    <img src={src} alt={alt} loading="lazy" className="w-16 h-16 sm:w-20 sm:h-20 object-contain rounded-md bg-white shrink-0" />
  ) : (
    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-md bg-muted shrink-0" aria-hidden />
  );
}

function Linha({ c }: { c: Cartao }) {
  return (
    <li className="flex items-center gap-3 rounded-lg border p-3">
      {c.posicao !== undefined && (
        <span className="w-8 text-center font-semibold text-muted-foreground shrink-0">{c.posicao}º</span>
      )}
      <Foto src={c.foto} alt={c.nome} />
      <div className="min-w-0 grow">
        <p className="font-semibold leading-snug">{c.nome}</p>
        {(c.marca || c.modelo) && (
          <p className="text-xs text-muted-foreground">{[c.marca, c.modelo].filter(Boolean).join(" · ")}</p>
        )}
        {c.link && (
          <a href={c.link} target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm underline py-2">
            Ver preços no Mercado Livre <ExternalLink size={14} aria-hidden />
          </a>
        )}
      </div>
    </li>
  );
}

export default function PesquisaMercado() {
  const [modo, setModo] = useState<"produto" | "categoria">("categoria");
  const [busca, setBusca] = useState("");
  const [produtos, setProdutos] = useState<Cartao[] | null>(null);
  const [categoriaId, setCategoriaId] = useState("");
  const [aberta, setAberta] = useState<{ id: string; name: string; path: string[] } | null>(null);
  const [destaques, setDestaques] = useState<Cartao[] | null>(null);
  const [carregando, setCarregando] = useState("");
  const [erro, setErro] = useState("");

  async function consultar<T>(rotulo: string, caminho: string, depois: (r: T) => void) {
    setCarregando(rotulo);
    setErro("");
    try {
      depois(await api<T>(caminho));
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setCarregando("");
    }
  }

  function pesquisar(e: React.FormEvent) {
    e.preventDefault();
    const termo = busca.trim();
    // só números e comprido o bastante: é código de barras (EAN/GTIN)
    const parametro = /^\d{8,14}$/.test(termo) ? `gtin=${termo}` : `q=${encodeURIComponent(termo)}`;
    void consultar<{ produtos: Cartao[] }>("produtos", `integrations/price-products?${parametro}`,
      (r) => setProdutos(r.produtos));
  }

  function verMaisVendidos() {
    if (!aberta?.id) return;
    void consultar<{ itens: Cartao[] }>("destaques",
      `integrations/price-best-sellers?category_id=${encodeURIComponent(aberta.id)}`, (r) => setDestaques(r.itens));
  }

  return <>
    <PageHeader
      eyebrow="Marketplaces"
      title="Pesquisa de mercado"
      description="O que mais vende em cada categoria do Mercado Livre e quais produtos existem no catálogo. Só consulta: nada muda na sua conta."
    />

    <div className="flex gap-2 mb-5" role="group" aria-label="Tipo de pesquisa">
      {([["categoria", "Mais vendidos da categoria"], ["produto", "Buscar produto"]] as const).map(([valor, rotulo]) => (
        <button key={valor} type="button" aria-pressed={modo === valor} onClick={() => { setModo(valor); setErro(""); }}
          className={`rounded-md px-4 h-11 sm:h-10 grow sm:grow-0 text-sm font-medium cursor-pointer border ${
            modo === valor ? "bg-primary text-primary-foreground border-transparent" : "border-input hover:bg-muted"}`}>
          {rotulo}
        </button>
      ))}
    </div>

    <ErrorMessage message={erro} />

    {modo === "categoria" ? <>
      <Card className="mb-5">
        <p className="font-medium mb-1">Categoria</p>
        <NavegadorCategorias categoryId={categoriaId} onCategoria={setCategoriaId}
          onAbrir={(c) => { setAberta(c); setDestaques(null); }} />
        <Button className="mt-3 w-full sm:w-auto" disabled={!aberta?.id || !!carregando} onClick={verMaisVendidos}>
          {carregando === "destaques" ? "Consultando…" : aberta?.id ? `Ver os mais vendidos de ${aberta.name}` : "Escolha uma categoria"}
        </Button>
        <p className="text-xs text-muted-foreground mt-3">
          Pode ser qualquer nível: uma categoria inteira ou uma subcategoria.
        </p>
      </Card>

      {destaques && <Card className="mb-5">
        <h2>Mais vendidos{aberta?.name ? ` em ${aberta.name}` : ""}</h2>
        {!destaques.length ? <Empty>O Mercado Livre não devolveu mais vendidos para esta categoria.</Empty> :
          <ol className="space-y-2">{destaques.map((d) => <Linha key={d.id} c={d} />)}</ol>}
      </Card>}
    </> : <>
      <Card className="mb-5">
        <form onSubmit={pesquisar} role="search" className="flex flex-col sm:flex-row gap-3 sm:items-end">
          <div className="grow">
            <label htmlFor="busca">Produto ou código de barras</label>
            <Input id="busca" type="search" value={busca} maxLength={200} autoComplete="off"
              placeholder="Ex.: carregador turbo 20W, ou 7891234567890"
              onChange={(e) => setBusca(e.target.value)} />
          </div>
          <Button disabled={busca.trim().length < 3 || !!carregando}>
            <Search size={16} aria-hidden /> {carregando === "produtos" ? "Pesquisando…" : "Pesquisar"}
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-3">
          Busca no catálogo do Mercado Livre — funciona melhor com produtos de marca (eletrônicos,
          acessórios). Peças autorais, como as impressas em 3D, costumam não estar no catálogo.
        </p>
      </Card>

      {produtos && <Card className="mb-5">
        <h2>Produtos encontrados</h2>
        {!produtos.length ? <Empty>Nenhum produto do catálogo encontrado. Tente outras palavras ou o código de barras.</Empty> :
          <ul className="grid lg:grid-cols-2 gap-2">{produtos.map((p) => <Linha key={p.id} c={p} />)}</ul>}
      </Card>}
    </>}

    <p className="text-xs text-muted-foreground">
      O Mercado Livre não entrega o preço dos concorrentes para este tipo de consulta; o link abre a
      busca do produto no site, onde os anúncios aparecem com preço.
    </p>
  </>;
}
