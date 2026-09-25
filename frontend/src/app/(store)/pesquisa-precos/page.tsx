"use client";
import { useState } from "react";
import { ExternalLink, Search } from "lucide-react";
import { api, brl } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Empty, ErrorMessage } from "@/components/feedback";
import { PageHeader } from "@/components/page-header";
import { NavegadorCategorias } from "@/components/ml-anuncio";

/* Spec 013 — pesquisa de preços no Mercado Livre. Só consulta: nada é gravado nem enviado. */

type Resumo = { quantidade: number; menor: number | null; mediana: number | null; maior: number | null };
type Produto = {
  id: string;
  nome: string;
  marca: string;
  modelo: string;
  foto: string;
  preco_vencedor: number | null;
  frete_gratis: boolean;
  link: string;
};
type Oferta = {
  item_id: string;
  preco: number | null;
  vendedor: string;
  condicao: string;
  frete_gratis: boolean;
  tipo_anuncio: string;
  full: boolean;
};
type Destaque = {
  posicao: number;
  id: string;
  tipo: string;
  nome: string;
  preco: number | null;
  foto: string;
  link: string;
};

const preco = (v: number | null) => (v === null ? "—" : brl(v));
const condicoes: Record<string, string> = { new: "Novo", used: "Usado", reconditioned: "Recondicionado" };
const tiposDeAnuncio: Record<string, string> = { gold_special: "Clássico", gold_pro: "Premium" };

function Faixa({ resumo, rotulo }: { resumo: Resumo; rotulo: string }) {
  if (!resumo.quantidade) return <p className="text-sm text-muted-foreground">Nenhum preço encontrado.</p>;
  return (
    <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
      {[
        ["Menor", preco(resumo.menor)],
        ["Mediana", preco(resumo.mediana)],
        ["Maior", preco(resumo.maior)],
        [rotulo, String(resumo.quantidade)],
      ].map(([nome, valor]) => (
        <div key={nome} className="rounded-lg border bg-background p-3">
          <dt className="text-xs text-muted-foreground">{nome}</dt>
          <dd className="money text-lg sm:text-xl">{valor}</dd>
        </div>
      ))}
    </dl>
  );
}

function Foto({ src, alt }: { src: string; alt: string }) {
  return src ? (
    <img src={src} alt={alt} loading="lazy" className="w-16 h-16 sm:w-20 sm:h-20 object-contain rounded-md bg-white shrink-0" />
  ) : (
    <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-md bg-muted shrink-0" aria-hidden />
  );
}

export default function PesquisaPrecos() {
  const [modo, setModo] = useState<"produto" | "categoria">("produto");
  const [busca, setBusca] = useState("");
  const [produtos, setProdutos] = useState<Produto[] | null>(null);
  const [escolhido, setEscolhido] = useState<Produto | null>(null);
  const [ofertas, setOfertas] = useState<{ resumo: Resumo; ofertas: Oferta[] } | null>(null);
  const [categoriaId, setCategoriaId] = useState("");
  const [aberta, setAberta] = useState<{ id: string; name: string; path: string[] } | null>(null);
  const [destaques, setDestaques] = useState<{ resumo: Resumo; itens: Destaque[] } | null>(null);
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
    setEscolhido(null);
    setOfertas(null);
    void consultar<{ produtos: Produto[] }>("produtos", `integrations/price-products?${parametro}`,
      (r) => setProdutos(r.produtos));
  }

  function verOfertas(p: Produto) {
    setEscolhido(p);
    setOfertas(null);
    void consultar<{ resumo: Resumo; ofertas: Oferta[] }>("ofertas",
      `integrations/price-offers?product_id=${encodeURIComponent(p.id)}`, (r) => {
        setOfertas(r);
        document.getElementById("ofertas")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
  }

  function verMaisVendidos() {
    if (!aberta?.id) return;
    void consultar<{ resumo: Resumo; itens: Destaque[] }>("destaques",
      `integrations/price-best-sellers?category_id=${encodeURIComponent(aberta.id)}`, setDestaques);
  }

  return <>
    <PageHeader
      eyebrow="Marketplaces"
      title="Pesquisa de preços"
      description="Veja por quanto um produto está sendo vendido no Mercado Livre, ou o que mais vende numa categoria. Só consulta: nada muda na sua conta."
    />

    <div className="flex gap-2 mb-5" role="group" aria-label="Tipo de pesquisa">
      {([["produto", "Por produto"], ["categoria", "Mais vendidos da categoria"]] as const).map(([valor, rotulo]) => (
        <button key={valor} type="button" aria-pressed={modo === valor} onClick={() => { setModo(valor); setErro(""); }}
          className={`rounded-md px-4 h-11 sm:h-10 grow sm:grow-0 text-sm font-medium cursor-pointer border ${
            modo === valor ? "bg-primary text-primary-foreground border-transparent" : "border-input hover:bg-muted"}`}>
          {rotulo}
        </button>
      ))}
    </div>

    <ErrorMessage message={erro} />

    {modo === "produto" ? <>
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
          Pesquisa no catálogo do Mercado Livre — funciona melhor com produtos de marca (eletrônicos,
          acessórios). Peças autorais, como as impressas em 3D, costumam não estar no catálogo: para
          elas, use os mais vendidos da categoria.
        </p>
      </Card>

      {produtos && <Card className="mb-5">
        <h2>Produtos encontrados</h2>
        {!produtos.length ? <Empty>Nenhum produto do catálogo encontrado. Tente outras palavras ou o código de barras.</Empty> :
          <ul className="grid lg:grid-cols-2 gap-3">
            {produtos.map((p) => <li key={p.id} className={`flex gap-3 rounded-lg border p-3 ${escolhido?.id === p.id ? "border-primary" : ""}`}>
              <Foto src={p.foto} alt={p.nome} />
              <div className="min-w-0 grow">
                <p className="font-semibold leading-snug">{p.nome}</p>
                {(p.marca || p.modelo) && <p className="text-xs text-muted-foreground">{[p.marca, p.modelo].filter(Boolean).join(" · ")}</p>}
                <p className="mt-1 text-sm">
                  <span className="text-muted-foreground">Preço na página do produto: </span>
                  <b className="money">{preco(p.preco_vencedor)}</b>
                  {p.frete_gratis && <span className="ml-2 text-xs text-success">frete grátis</span>}
                </p>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2">
                  <Button size="sm" variant="outline" disabled={!!carregando} onClick={() => verOfertas(p)}>
                    {carregando === "ofertas" && escolhido?.id === p.id ? "Carregando…" : "Ver todas as ofertas"}
                  </Button>
                  {p.link && <a href={p.link} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm underline py-2">
                    Abrir no Mercado Livre <ExternalLink size={14} aria-hidden /></a>}
                </div>
              </div>
            </li>)}
          </ul>}
      </Card>}

      {escolhido && ofertas && <Card id="ofertas" className="mb-5 scroll-mt-20">
        <h2>Ofertas de {escolhido.nome}</h2>
        <Faixa resumo={ofertas.resumo} rotulo="Ofertas" />
        {ofertas.ofertas.length > 0 && <div className="overflow-auto"><table className="data-table">
          <thead><tr><th>Preço</th><th>Condição</th><th>Envio</th><th>Tipo de anúncio</th><th>Anúncio</th></tr></thead>
          <tbody>{ofertas.ofertas.map((o) => <tr key={o.item_id}>
            <td data-role="title" className="money">{preco(o.preco)}</td>
            <td data-label="Condição">{condicoes[o.condicao] || o.condicao || "—"}</td>
            <td data-label="Envio">{[o.full && "Full", o.frete_gratis && "Frete grátis"].filter(Boolean).join(" · ") || "—"}</td>
            <td data-label="Tipo de anúncio">{tiposDeAnuncio[o.tipo_anuncio] || o.tipo_anuncio || "—"}</td>
            <td data-label="Anúncio" className="money">{o.item_id}</td>
          </tr>)}</tbody>
        </table></div>}
      </Card>}
    </> : <>
      <Card className="mb-5">
        <p className="font-medium mb-1">Categoria</p>
        <NavegadorCategorias categoryId={categoriaId} onCategoria={setCategoriaId}
          onAbrir={(c) => { setAberta(c); setDestaques(null); }} />
        <Button className="mt-3 w-full sm:w-auto" disabled={!aberta?.id || !!carregando} onClick={verMaisVendidos}>
          {carregando === "destaques" ? "Consultando…" : aberta?.id ? `Ver os mais vendidos de ${aberta.name}` : "Escolha uma categoria"}
        </Button>
      </Card>

      {destaques && <Card className="mb-5">
        <h2>Mais vendidos{aberta?.name ? ` em ${aberta.name}` : ""}</h2>
        <Faixa resumo={destaques.resumo} rotulo="Com preço" />
        {!destaques.itens.length ? <Empty>O Mercado Livre não devolveu mais vendidos para esta categoria.</Empty> :
          <ol className="space-y-2">
            {destaques.itens.map((d) => <li key={d.id} className="flex items-center gap-3 rounded-lg border p-3">
              <span className="w-8 text-center font-semibold text-muted-foreground shrink-0">{d.posicao}º</span>
              <Foto src={d.foto} alt={d.nome} />
              <div className="min-w-0 grow">
                <p className="font-semibold leading-snug">{d.nome}</p>
                <p className="money text-sm">{preco(d.preco)}</p>
              </div>
              {d.link && <a href={d.link} target="_blank" rel="noopener noreferrer" aria-label={`Abrir ${d.nome} no Mercado Livre`}
                className="shrink-0 p-3 -m-2 text-muted-foreground hover:text-foreground"><ExternalLink size={18} aria-hidden /></a>}
            </li>)}
          </ol>}
        {destaques.itens.some((d) => d.preco === null) && <p className="text-xs text-muted-foreground mt-3">
          Alguns itens vêm do Mercado Livre sem preço nesta consulta; eles aparecem com “—”.
        </p>}
      </Card>}
    </>}
  </>;
}
