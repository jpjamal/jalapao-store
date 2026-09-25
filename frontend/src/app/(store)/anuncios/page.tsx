"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api, BASE, brl, type Page, type Product } from "@/lib/api";
import { ProductPicker } from "@/components/product-picker";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorMessage, Empty } from "@/components/feedback";
import {
  CategoriaEAtributos,
  RelatorioValidacao,
  type Atributos,
  type Categoria,
  type Relatorio,
} from "@/components/ml-anuncio";
import { FormActions } from "@/components/form-actions";
import { PageHeader } from "@/components/page-header";
import { ChevronLeft, ChevronRight, ImagePlus } from "lucide-react";

type Channel = "mercado_livre" | "shopee";
type ProductImage = {
  id: string;
  product: string;
  alt_text: string;
  position: number;
  width: number;
  height: number;
};
type Draft = {
  id: string;
  product: string;
  product_name: string;
  product_sku: string;
  channel: Channel;
  title: string;
  description: string;
  price: string | null;
  brand: string;
  model: string;
  condition: string;
  category_id: string;
  attributes: Atributos;
  image_ids: string[];
  published_item_id: string | null;
  pending_changes: boolean;
};
type Publicacao = {
  acao?: "publicado" | "atualizado";
  item_id: string;
  permalink: string;
  status: string;
  titulo: string;
  fotos: number;
  fotos_novas: number;
  estoque: number | null;
  avisos: string[];
};
const channels: Record<Channel, string> = {
  mercado_livre: "Mercado Livre",
  shopee: "Shopee",
};
const imageUrl = (id: string) => `${BASE}/api/product-images/${id}/content`;

export default function Anuncios() {
  const [products, setProducts] = useState<Product[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [productId, setProductId] = useState("");
  const [channel, setChannel] = useState<Channel>("mercado_livre");
  const [images, setImages] = useState<ProductImage[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [condition, setCondition] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [attributes, setAttributes] = useState<Atributos>({});
  const [categoria, setCategoria] = useState<Categoria | null>(null);
  const [relatorio, setRelatorio] = useState<Relatorio | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [publicacao, setPublicacao] = useState<Publicacao | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    const [productsPage, draftsPage] = await Promise.all([
      api<Page<Product>>("products"),
      api<Page<Draft>>("listing-drafts"),
    ]);
    setProducts(productsPage.results);
    setDrafts(draftsPage.results);
  }, []);
  useEffect(() => {
    setProductId(new URLSearchParams(window.location.search).get("product") || "");
    load().catch((e) => setError((e as Error).message));
  }, [load]);

  const product = products.find((item) => item.id === productId);
  const draft = useMemo(
    () => drafts.find((item) => item.product === productId && item.channel === channel),
    [drafts, productId, channel],
  );
  useEffect(() => {
    if (!productId) { setImages([]); return; }
    let active = true;
    api<Page<ProductImage>>(`product-images?product=${productId}`)
      .then((page) => { if (active) setImages(page.results); })
      .catch((e) => { if (active) setError((e as Error).message); });
    return () => { active = false; };
  }, [productId]);
  useEffect(() => {
    setTitle(draft?.title || "");
    setDescription(draft?.description || "");
    setPrice(draft?.price || "");
    setBrand(draft?.brand || "");
    setModel(draft?.model || "");
    setCondition(draft?.condition || "");
    setCategoryId(draft?.category_id || "");
    setAttributes(draft?.attributes || {});
    setSelected(draft?.image_ids || []);
    setRelatorio(null);
    setConfirmando(false);
  }, [draft, productId, channel]);

  async function upload(file: File) {
    if (!productId) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const body = new FormData();
      body.append("product", productId);
      body.append("file", file);
      const result = await fetch(`${BASE}/api/product-images`, { method: "POST", body });
      const data = await result.json();
      if (!result.ok) throw new Error(
        Object.values(data.errors || data).flat().join(" ") || "Falha ao enviar foto."
      );
      setImages((before) => [...before, data as ProductImage]);
      setSelected((before) => [...before, (data as ProductImage).id]);
      setNotice("Foto adicionada ao produto. Salve o rascunho para usá-la neste canal.");
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  function move(id: string, direction: number) {
    setSelected((before) => {
      const next = [...before];
      const index = next.indexOf(id);
      const target = index + direction;
      if (index < 0 || target < 0 || target >= next.length) return before;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  async function gravar(): Promise<string> {
    const salvo = await api<Draft>(`listing-drafts${draft ? `/${draft.id}` : ""}`, {
        method: draft ? "PATCH" : "POST",
        body: JSON.stringify({
          ...(draft ? {} : { product: productId, channel }), title, description,
          price: price || null, brand, model, condition, category_id: categoryId,
          attributes, image_ids: selected,
        }),
      });
    await load();
    return salvo.id;
  }

  async function save() {
    if (!productId) return;
    setBusy(true); setError(""); setNotice(""); setRelatorio(null);
    try {
      await gravar();
      setNotice("Rascunho salvo. Nenhum anúncio ou estoque foi enviado ao marketplace.");
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  // Salva antes: a validação confere o rascunho gravado, não o que está só na tela.
  async function validar() {
    if (!productId) return;
    setBusy(true); setError(""); setNotice(""); setRelatorio(null);
    try {
      const id = await gravar();
      setRelatorio(await api<Relatorio>(`listing-drafts/${id}/validate`, { method: "POST", body: "{}" }));
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  // Publicar cria o anúncio de verdade. O backend valida de novo antes e recusa se o
  // rascunho já foi publicado, então um segundo clique não duplica o anúncio.
  async function publicar() {
    if (!draft) return;
    setBusy(true); setError(""); setNotice(""); setPublicacao(null);
    try {
      const r = await api<Publicacao>(`listing-drafts/${draft.id}/publish`, { method: "POST", body: "{}" });
      setPublicacao({ ...r, acao: "publicado" });
      setRelatorio(null);
      setConfirmando(false);
      await load();
    } catch (e) { setError((e as Error).message); setConfirmando(false); }
    finally { setBusy(false); }
  }

  // Cria ou substitui a descrição do anúncio já publicado e mostra o que ficou gravado lá.
  // Rascunho publicado: salva e manda ao anúncio o que mudou (preço, fotos, atributos, descrição).
  async function enviar() {
    if (!draft) return;
    setBusy(true); setError(""); setNotice(""); setPublicacao(null);
    try {
      await gravar();
      const r = await api<Publicacao>(`listing-drafts/${draft.id}/push`, { method: "POST", body: "{}" });
      setPublicacao({ ...r, acao: "atualizado" });
      await load();
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }

  const publicado = draft?.published_item_id || "";
  const podePublicar = channel === "mercado_livre" && !publicado && relatorio?.pode_publicar;

  return <>
    <PageHeader
      eyebrow="Marketplaces"
      title="Anúncios"
      description="Prepare um rascunho para cada canal. Salvar não publica; publicar e enviar alterações são ações à parte."
    />
    <ErrorMessage message={error} />
    {notice && <p role="status" className="text-success mb-4">{notice}</p>}

    <Card className="mb-5">
      <h2>1. Produto e canal</h2>
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label htmlFor="draft-product">Produto</label>
          <ProductPicker products={products} value={productId}
            onChange={(id) => { setProductId(id); setNotice(""); }} id="draft-product"
            mostrarQuantidade={false} somenteAtivos={false} />
        </div>
        <div>
          <label htmlFor="draft-channel">Canal</label>
          <select id="draft-channel" value={channel} onChange={(e) => setChannel(e.target.value as Channel)}>
            <option value="mercado_livre">Mercado Livre</option>
            <option value="shopee">Shopee</option>
          </select>
        </div>
      </div>
      {product && <dl className="flex flex-wrap gap-x-5 gap-y-1 text-sm text-muted-foreground mt-4">
        <div><dt className="inline">SKU </dt><dd className="inline">{product.sku}</dd></div>
        <div><dt className="inline">Estoque </dt><dd className="inline">{product.quantity} un.</dd></div>
        <div><dt className="inline">Preço de referência </dt><dd className="inline">{brl(product.sale_price)}</dd></div>
      </dl>}
      {publicado && <p className={`mt-4 rounded-md border px-3 py-2 text-sm ${
        draft?.pending_changes ? "border-primary" : "border-[var(--success)]"}`}>
        <b>Publicado no Mercado Livre · {publicado}</b>
        <span className="block text-muted-foreground">
          {draft?.pending_changes
            ? "Há alterações no rascunho que ainda não foram enviadas ao anúncio."
            : "O anúncio está igual ao rascunho."}
        </span>
      </p>}
    </Card>

    {product ? <>
      <Card className="mb-5">
        <h2>2. Conteúdo</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Pode ficar incompleto enquanto você prepara o anúncio para {channels[channel]}.
        </p>
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2"><label htmlFor="draft-title">Título</label>
            <Input id="draft-title" maxLength={300} value={title} onChange={(e) => setTitle(e.target.value)} />
            {channel === "mercado_livre" && categoria?.max_title_length && <p
              className={`text-xs mt-1 ${title.length > categoria.max_title_length ? "text-destructive" : "text-muted-foreground"}`}>
              {title.length} de {categoria.max_title_length} caracteres aceitos pela categoria
            </p>}</div>
          <div className="sm:col-span-2"><label htmlFor="draft-description">Descrição</label>
            <textarea id="draft-description" rows={8} value={description}
              onChange={(e) => setDescription(e.target.value)} className="w-full rounded-md border bg-background p-3" /></div>
          <div><label htmlFor="draft-price">Preço (R$)</label>
            <Input id="draft-price" type="number" inputMode="decimal" min="0" step="0.01" value={price}
              onChange={(e) => setPrice(e.target.value)} /></div>
          <div><label htmlFor="draft-condition">Condição</label>
            <select id="draft-condition" value={condition} onChange={(e) => setCondition(e.target.value)}>
              <option value="">A definir</option><option value="new">Novo</option>
              <option value="used">Usado</option><option value="reconditioned">Recondicionado</option>
            </select></div>
          <div><label htmlFor="draft-brand">Marca</label>
            <Input id="draft-brand" maxLength={100} value={brand} onChange={(e) => setBrand(e.target.value)} /></div>
          <div><label htmlFor="draft-model">Modelo</label>
            <Input id="draft-model" maxLength={100} value={model} onChange={(e) => setModel(e.target.value)} /></div>
        </div>
      </Card>

      <Card className="mb-5">
        <h2>3. Fotos</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Toque na foto para usar ou tirar do anúncio. A primeira marcada é a capa; use as setas para
          mudar a ordem. JPG ou PNG, até 10 MB.
        </p>
        <label htmlFor="photo-file"
          className={`flex items-center justify-center gap-2 rounded-lg border border-dashed min-h-14 px-4 text-sm cursor-pointer hover:bg-muted ${busy ? "opacity-50 pointer-events-none" : ""}`}>
          <ImagePlus size={18} aria-hidden /> Adicionar foto do produto
        </label>
        <input id="photo-file" type="file" className="sr-only" accept="image/jpeg,image/png,image/webp"
          disabled={busy} onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void upload(file);
            e.target.value = "";
          }} />
        {images.length ? <ul className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 mt-4">
          {images.map((image) => {
            const position = selected.indexOf(image.id);
            const usada = position >= 0;
            return <li key={image.id} className={`rounded-lg border-2 p-1.5 ${usada ? "border-primary" : "border-transparent bg-muted/40"}`}>
              <button type="button" aria-pressed={usada}
                aria-label={usada ? `Tirar a foto ${position + 1} do anúncio` : "Usar esta foto no anúncio"}
                className="relative block w-full cursor-pointer rounded-md overflow-hidden"
                onClick={() => setSelected((before) =>
                  usada ? before.filter((id) => id !== image.id) : [...before, image.id])}>
                <img src={imageUrl(image.id)} alt={image.alt_text || `Foto do produto ${product.name}`}
                  className={`w-full aspect-square object-contain bg-background ${usada ? "" : "opacity-60"}`} />
                <span className={`absolute top-1.5 left-1.5 rounded-full px-2 py-0.5 text-xs font-semibold ${
                  usada ? "bg-primary text-primary-foreground" : "bg-card text-muted-foreground border"}`}>
                  {usada ? (position === 0 ? "Capa" : `${position + 1}ª`) : "Não usada"}
                </span>
              </button>
              {usada && <div className="flex justify-center gap-2 mt-1.5">
                <Button size="sm" variant="outline" type="button" aria-label="Mover foto para antes"
                  disabled={position === 0} onClick={() => move(image.id, -1)}><ChevronLeft size={16} aria-hidden /></Button>
                <Button size="sm" variant="outline" type="button" aria-label="Mover foto para depois"
                  disabled={position === selected.length - 1} onClick={() => move(image.id, 1)}><ChevronRight size={16} aria-hidden /></Button>
              </div>}
            </li>;
          })}
        </ul> : <Empty>Nenhuma foto cadastrada para este produto.</Empty>}
        {images.length > 0 && <p className="text-sm text-muted-foreground mt-3" aria-live="polite">
          {selected.length} de {images.length} foto{images.length === 1 ? "" : "s"} no anúncio
        </p>}
      </Card>

      <Card className="mb-5">
        <h2>4. Categoria{channel === "mercado_livre" ? " e atributos" : ""}</h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {channel === "mercado_livre" ? <CategoriaEAtributos
            titulo={title} categoryId={categoryId} onCategoria={setCategoryId}
            atributos={attributes} onAtributos={setAttributes} onInfo={setCategoria} />
          : <div><label htmlFor="draft-category">Código da categoria no canal</label>
            <Input id="draft-category" maxLength={80} value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)} /></div>}
        </div>
      </Card>

      {/* ações sempre à mão: no celular a barra fica presa ao pé da tela */}
      <div className="sticky bottom-0 z-20 -mx-4 sm:mx-0 border-t sm:border bg-background/95 backdrop-blur px-4 py-3 sm:rounded-xl sm:bg-card sm:p-4 mb-5">
        <FormActions>
          {channel === "mercado_livre" && !publicado && <Button disabled={busy}
            onClick={() => void validar()}>{busy ? "Aguarde…" : "Salvar e validar no Mercado Livre"}</Button>}
          {channel === "mercado_livre" && publicado && <Button disabled={busy}
            onClick={() => void enviar()}>{busy ? "Enviando…" : "Salvar e enviar ao Mercado Livre"}</Button>}
          <Button variant={channel === "mercado_livre" ? "outline" : "default"} disabled={busy} onClick={() => void save()}>
            {busy && channel !== "mercado_livre" ? "Salvando…" : "Salvar rascunho"}
          </Button>
        </FormActions>
        {channel === "mercado_livre" && <p className="text-xs text-muted-foreground mt-2 hidden sm:block">
          {publicado
            ? "Enviar atualiza no anúncio o preço, as fotos, os atributos e a descrição. Categoria e estoque não mudam por aqui."
            : "Validar confere o rascunho e simula a publicação no Mercado Livre sem criar o anúncio."}
        </p>}
        {/* o erro também aparece no topo, mas aqui fica à vista de quem acabou de clicar */}
        {error && <p role="alert" className="text-sm text-destructive mt-2 whitespace-pre-wrap">{error}</p>}
      </div>

      {(relatorio || publicacao || podePublicar) && <Card className="mb-5">
        <h2>Resultado</h2>
        {relatorio && <RelatorioValidacao relatorio={relatorio} />}
        {podePublicar && !confirmando && <FormActions className="mt-4">
          <Button disabled={busy} onClick={() => setConfirmando(true)}>Publicar no Mercado Livre</Button>
        </FormActions>}
        {podePublicar && confirmando && <div role="alertdialog" aria-labelledby="confirma-titulo"
          aria-describedby="confirma-texto" className="rounded-lg border border-primary p-4 mt-4">
          <p id="confirma-titulo" className="font-semibold mb-1">Publicar de verdade?</p>
          <p id="confirma-texto" className="text-sm mb-3">
            O anúncio fica ativo no Mercado Livre com {selected.length} foto{selected.length === 1 ? "" : "s"},
            preço de {brl(price || 0)} e o estoque atual do produto como quantidade disponível. Para tirar
            do ar depois, é pelo painel do Mercado Livre.
          </p>
          <FormActions>
            <Button disabled={busy} onClick={() => void publicar()}>
              {busy ? "Publicando…" : "Confirmar publicação"}
            </Button>
            <Button variant="outline" disabled={busy} onClick={() => setConfirmando(false)}>Cancelar</Button>
          </FormActions>
        </div>}
        {publicacao && <div role="status" className="rounded-lg border border-[var(--success)] p-4 mt-4">
          <p className="font-semibold">
            {publicacao.acao === "publicado" ? "Publicado no Mercado Livre" : "Anúncio atualizado"}: {publicacao.item_id}
          </p>
          <p className="text-sm">
            {publicacao.fotos} foto{publicacao.fotos === 1 ? "" : "s"}
            {publicacao.acao === "atualizado" && ` (${publicacao.fotos_novas} nova${publicacao.fotos_novas === 1 ? "" : "s"})`}
            {publicacao.acao === "publicado" && publicacao.estoque !== null &&
              `, ${publicacao.estoque} unidade${publicacao.estoque === 1 ? "" : "s"} disponíve${publicacao.estoque === 1 ? "l" : "is"}`}
            {publicacao.status ? ` · situação: ${publicacao.status}` : ""}.
            {publicacao.acao === "publicado" && " A sincronização de estoque fica desligada até você ligar em Integrações."}
          </p>
          {publicacao.permalink && <a className="inline-block underline text-sm py-2" href={publicacao.permalink}
            target="_blank" rel="noopener noreferrer">Ver o anúncio no Mercado Livre</a>}
          {publicacao.avisos.map((a, i) => <p key={i} className="text-sm mt-1">! {a}</p>)}
        </div>}
      </Card>}
    </> : <Card className="mb-5"><Empty>Escolha um produto para preparar o anúncio.</Empty></Card>}

    {drafts.length > 0 && <Card>
      <h2>Rascunhos salvos</h2>
      <div className="overflow-auto"><table className="data-table">
        <thead><tr><th>Produto</th><th>Canal</th><th>Título</th><th>Situação</th><th><span className="sr-only">Ações</span></th></tr></thead>
        <tbody>{drafts.map((item) => <tr key={item.id}>
          <td data-role="title">{item.product_name}<span className="block text-xs text-muted-foreground font-normal">{item.product_sku}</span></td>
          <td data-label="Canal">{channels[item.channel]}</td>
          <td data-label="Título">{item.title || "Sem título"}</td>
          <td data-label="Situação">{item.published_item_id
            ? `Publicado · ${item.published_item_id}${item.pending_changes ? " · alterações não enviadas" : ""}`
            : "Rascunho"}</td>
          <td data-role="actions"><Button size="sm" variant="outline" onClick={() => {
            setProductId(item.product); setChannel(item.channel); window.scrollTo({ top: 0, behavior: "smooth" });
          }}>Editar</Button></td>
        </tr>)}</tbody></table></div>
    </Card>}
  </>;
}
