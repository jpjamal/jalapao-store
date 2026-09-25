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
    <h1>Anúncios</h1>
    <p className="text-muted-foreground mb-7">
      Prepare um rascunho para cada canal. Salvar aqui não publica o anúncio.
    </p>
    <ErrorMessage message={error} />
    {notice && <p role="status" className="text-success mb-4">{notice}</p>}
    <Card className="mb-6">
      <h2>Escolha o produto e o canal</h2>
      <div className="grid md:grid-cols-2 gap-4 mt-4">
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
      {product && <p className="text-sm text-muted-foreground mt-4">
        SKU {product.sku} · estoque {product.quantity} un. · preço de referência {brl(product.sale_price)}
      </p>}
    </Card>
    {product ? <>
      <Card className="mb-6">
        <h2>Fotos do produto</h2>
        <p className="text-sm text-muted-foreground mb-4">
          JPG, PNG ou WebP, até 10 MB. Marque as fotos deste anúncio; use as setas para escolher a capa e a ordem.
        </p>
        <label htmlFor="photo-file">Adicionar foto</label>
        <Input id="photo-file" type="file" accept="image/jpeg,image/png,image/webp"
          disabled={busy} onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void upload(file);
            e.target.value = "";
          }} />
        {images.length ? <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
          {images.map((image) => {
            const position = selected.indexOf(image.id);
            return <div key={image.id} className="rounded-lg border p-2">
              <img src={imageUrl(image.id)} alt={image.alt_text || `Foto do produto ${product.name}`}
                className="w-full aspect-square object-contain" />
              <label className="flex items-center gap-2 mt-2 text-sm">
                <input type="checkbox" checked={position >= 0} onChange={() => setSelected((before) =>
                  position >= 0 ? before.filter((id) => id !== image.id) : [...before, image.id]
                )} /> Usar no anúncio
              </label>
              {position >= 0 && <div className="flex gap-2 items-center text-sm mt-2">
                <span>{position === 0 ? "Capa" : `${position + 1}ª foto`}</span>
                <Button size="sm" variant="outline" type="button" aria-label="Mover foto para antes"
                  disabled={position === 0} onClick={() => move(image.id, -1)}>↑</Button>
                <Button size="sm" variant="outline" type="button" aria-label="Mover foto para depois"
                  disabled={position === selected.length - 1} onClick={() => move(image.id, 1)}>↓</Button>
              </div>}
            </div>;
          })}
        </div> : <Empty>Nenhuma foto cadastrada para este produto.</Empty>}
      </Card>
      <Card>
        <h2>Rascunho para {channels[channel]}</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Todos os campos abaixo podem ficar vazios enquanto você prepara o anúncio.
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="md:col-span-2"><label htmlFor="draft-title">Título sugerido</label>
            <Input id="draft-title" maxLength={300} value={title} onChange={(e) => setTitle(e.target.value)} />
            {channel === "mercado_livre" && categoria?.max_title_length && <p
              className={`text-xs mt-1 ${title.length > categoria.max_title_length ? "text-destructive" : "text-muted-foreground"}`}>
              {title.length} de {categoria.max_title_length} caracteres aceitos pela categoria
            </p>}</div>
          <div className="md:col-span-2"><label htmlFor="draft-description">Descrição</label>
            <textarea id="draft-description" rows={8} value={description}
              onChange={(e) => setDescription(e.target.value)} className="w-full rounded-md border bg-background p-3" /></div>
          <div><label htmlFor="draft-price">Preço proposto (R$)</label>
            <Input id="draft-price" type="number" min="0" step="0.01" value={price}
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
          {channel === "mercado_livre" ? <CategoriaEAtributos
            titulo={title} categoryId={categoryId} onCategoria={setCategoryId}
            atributos={attributes} onAtributos={setAttributes} onInfo={setCategoria} />
          : <div><label htmlFor="draft-category">Código da categoria no canal</label>
            <Input id="draft-category" maxLength={80} value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)} /></div>}
        </div>
        {publicado && <p className="text-sm mb-3">
          Publicado no Mercado Livre como <b>{publicado}</b>
          {draft?.pending_changes
            ? " · há alterações no rascunho que ainda não foram enviadas ao anúncio."
            : " · o anúncio está igual ao rascunho."}
        </p>}
        <div className="flex flex-wrap gap-3 mt-5">
          <Button disabled={busy} onClick={() => void save()}>
            {busy ? "Aguarde…" : "Salvar rascunho"}
          </Button>
          {channel === "mercado_livre" && !publicado && <Button variant="outline" disabled={busy}
            onClick={() => void validar()}>Salvar e validar no Mercado Livre</Button>}
          {channel === "mercado_livre" && publicado && <Button variant="outline" disabled={busy}
            onClick={() => void enviar()}>{busy ? "Enviando…" : "Salvar e enviar ao Mercado Livre"}</Button>}
        </div>
        {channel === "mercado_livre" && <p className="text-xs text-muted-foreground mt-2">
          {publicado
            ? "Enviar atualiza no anúncio o preço, as fotos, os atributos e a descrição. Categoria e estoque não mudam por aqui."
            : "Validar confere o rascunho e simula a publicação no Mercado Livre sem criar o anúncio."}
        </p>}
        {relatorio && <RelatorioValidacao relatorio={relatorio} />}
        {podePublicar && !confirmando && <Button className="mt-4" disabled={busy}
          onClick={() => setConfirmando(true)}>Publicar no Mercado Livre</Button>}
        {podePublicar && confirmando && <div role="alertdialog" aria-labelledby="confirma-titulo"
          className="rounded-lg border border-primary p-4 mt-4">
          <p id="confirma-titulo" className="font-semibold mb-1">Publicar de verdade?</p>
          <p className="text-sm mb-3">
            O anúncio fica ativo no Mercado Livre com {selected.length} foto{selected.length === 1 ? "" : "s"},
            preço de R$ {price} e o estoque atual do produto como quantidade disponível. Para tirar
            do ar depois, é pelo painel do Mercado Livre.
          </p>
          <div className="flex flex-wrap gap-3">
            <Button disabled={busy} onClick={() => void publicar()}>
              {busy ? "Publicando…" : "Confirmar publicação"}
            </Button>
            <Button variant="outline" disabled={busy} onClick={() => setConfirmando(false)}>Cancelar</Button>
          </div>
        </div>}
        {/* o erro também aparece no topo, mas aqui fica à vista de quem acabou de clicar */}
        {error && (confirmando || relatorio || publicado) && <p role="alert"
          className="text-sm text-destructive mt-3 whitespace-pre-wrap">{error}</p>}
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
          {publicacao.permalink && <a className="underline text-sm" href={publicacao.permalink}
            target="_blank" rel="noopener noreferrer">Ver o anúncio no Mercado Livre</a>}
          {publicacao.avisos.map((a, i) => <p key={i} className="text-sm mt-1">! {a}</p>)}
        </div>}
      </Card>
    </> : <Card><Empty>Escolha um produto para preparar o anúncio.</Empty></Card>}
    {drafts.length > 0 && <Card className="mt-6">
      <h2>Rascunhos salvos</h2>
      <div className="overflow-auto"><table><thead><tr><th>Produto</th><th>Canal</th><th>Título</th><th>Situação</th><th></th></tr></thead>
        <tbody>{drafts.map((item) => <tr key={item.id}>
          <td>{item.product_name}<span className="block text-xs text-muted-foreground">{item.product_sku}</span></td>
          <td>{channels[item.channel]}</td><td>{item.title || "Sem título"}</td>
          <td>{item.published_item_id
            ? `Publicado · ${item.published_item_id}${item.pending_changes ? " · alterações não enviadas" : ""}`
            : "Rascunho"}</td>
          <td><Button size="sm" variant="outline" onClick={() => { setProductId(item.product); setChannel(item.channel); window.scrollTo(0, 0); }}>Editar</Button></td>
        </tr>)}</tbody></table></div>
    </Card>}
  </>;
}
