"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { Plus, Printer, Trash2 } from "lucide-react";
import { api, BASE } from "@/shared/api/client";
import { type Page } from "@/shared/api/types";
import { type Product } from "@/features/catalog/types";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { PageHeader } from "@/shared/components/page-header";
import { ErrorMessage, Empty } from "@/shared/components/feedback";

/* Orçamento de peças 3D (spec 036): escolhe produtos 3D, define a margem de cada um e gera um documento
   para o cliente só com o valor final. Nada é guardado: o documento sai na hora (imprimir ou salvar em PDF).
   O custo e a margem ficam só nesta tela; nunca entram no documento. */

type Line = { key: string; product: Product; qty: string; margin: string; price: string };
type Photo = { id: string; alt_text: string };

const INSTAGRAM = "@storejalapao";

const num = (v: string) => {
  const n = Number(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : 0;
};
const cents = (n: number) => Math.round(n * 100) / 100;
const brl = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const money = (n: number) => n.toFixed(2).replace(".", ",");
const imageUrl = (id: string) => `${BASE}/api/product-images/${id}/content`;
const dateBr = (d: Date) => d.toLocaleDateString("pt-BR");

/** Preço que a margem dá sobre o custo da peça. */
const priceFrom = (cost: number, margin: number) => cents(cost * (1 + margin / 100));

function newLine(product: Product): Line {
  const cost = num(product.cost_price);
  const margin = num(product.printing?.markup_percent ?? "0");
  // sem custo cadastrado a margem não diz nada: parte do preço de venda do produto
  const price = cost > 0 ? priceFrom(cost, margin) : num(product.sale_price);
  return {
    key: `${product.id}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    product,
    qty: "1",
    margin: cost > 0 ? String(margin) : "",
    price: price ? money(price) : "",
  };
}

async function loadPrintProducts(): Promise<Product[]> {
  const all: Product[] = [];
  for (let page = 1; page <= 10; page++) {
    const r = await api<Page<Product>>(`products?active=true&ordering=name&page=${page}`);
    all.push(...r.results);
    if (!r.next) break;
  }
  return all.filter((p) => p.printing);
}

export default function Orcamento() {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [error, setError] = useState("");
  const [lines, setLines] = useState<Line[]>([]);
  const [photos, setPhotos] = useState<Record<string, Photo | null>>({});
  // produtos marcados na lista para entrar de uma vez no orçamento
  const [picked, setPicked] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [client, setClient] = useState("");
  const [contact, setContact] = useState("");
  const [validity, setValidity] = useState("7");
  const [lead, setLead] = useState("");
  const [notes, setNotes] = useState("");
  const [discount, setDiscount] = useState("");
  const [shipping, setShipping] = useState("");
  const doc = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadPrintProducts()
      .then(setProducts)
      .catch((e) => setError((e as Error).message));
  }, []);

  // a primeira foto de cada produto do orçamento, para ilustrar o item
  useEffect(() => {
    const missing = lines
      .map((l) => l.product.id)
      .filter((id, i, all) => all.indexOf(id) === i && !(id in photos));
    missing.forEach((id) => {
      setPhotos((before) => ({ ...before, [id]: null }));
      api<Page<Photo>>(`product-images?product=${id}`)
        .then((r) => setPhotos((before) => ({ ...before, [id]: r.results[0] ?? null })))
        .catch(() => undefined);
    });
  }, [lines, photos]);

  const options = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (products ?? []).filter((p) => !term || `${p.name} ${p.sku}`.toLowerCase().includes(term));
  }, [products, search]);

  const inQuoteIds = lines.map((l) => l.product.id);
  const available = options.filter((p) => !inQuoteIds.includes(p.id));

  function setLine(key: string, patch: Partial<Line>) {
    setLines((before) => before.map((l) => (l.key === key ? { ...l, ...patch } : l)));
  }
  function changeMargin(l: Line, value: string) {
    const cost = num(l.product.cost_price);
    setLine(l.key, {
      margin: value,
      price: cost > 0 && value.trim() !== "" ? money(priceFrom(cost, num(value))) : l.price,
    });
  }
  function changePrice(l: Line, value: string) {
    const cost = num(l.product.cost_price);
    setLine(l.key, {
      price: value,
      margin: cost > 0 && value.trim() !== "" ? String(cents((num(value) / cost - 1) * 100)) : l.margin,
    });
  }

  const qtyOf = (l: Line) => Math.max(0, Math.floor(num(l.qty)));
  const subtotal = lines.reduce((sum, l) => sum + num(l.price) * qtyOf(l), 0);
  const total = Math.max(0, subtotal - num(discount) + num(shipping));
  const issued = new Date();
  const until = new Date(issued.getTime() + Math.max(0, Math.floor(num(validity))) * 86_400_000);
  const ready = lines.length > 0 && lines.every((l) => num(l.price) > 0 && qtyOf(l) >= 1);

  // O documento vai para uma aba própria (fundo branco, só ele), onde o navegador imprime ou salva em PDF.
  function print() {
    const node = doc.current;
    if (!node) return;
    const win = window.open("", "_blank");
    if (!win) {
      setError("O navegador bloqueou a nova aba. Permita pop-ups para gerar o orçamento.");
      return;
    }
    setError("");
    const styles = Array.from(document.querySelectorAll("link[rel=stylesheet], style"))
      .map((el) => el.outerHTML)
      .join("");
    win.document.write(
      `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">` +
        `<title>Orçamento${client ? ` - ${client}` : ""}</title>${styles}` +
        `<style>html,body{background:#fff!important;margin:0}body{padding:16px}@page{margin:12mm}</style>` +
        `</head><body>${node.outerHTML}</body></html>`,
    );
    win.document.close();
    // imprime só depois de as imagens carregarem (no máximo ~6 s)
    let tries = 0;
    const wait = window.setInterval(() => {
      tries += 1;
      const done = Array.from(win.document.images).every((img) => img.complete);
      if (done || tries > 30) {
        window.clearInterval(wait);
        win.focus();
        win.print();
      }
    }, 200);
  }

  const row = { display: "flex", justifyContent: "space-between" } as const;

  return (
    <>
      <PageHeader
        title="Orçamento"
        description="Escolha produtos 3D, ajuste a margem de cada um e gere o orçamento para o cliente, só com o valor final."
        back={{ href: "/ferramentas", label: "Ferramentas" }}
        actions={
          <Button type="button" disabled={!ready} onClick={print}>
            <Printer size={18} aria-hidden className="mr-2" /> Gerar PDF / imprimir
          </Button>
        }
      />
      <ErrorMessage message={error} />

      <Card className="mb-5">
        <h2>1. Produtos 3D</h2>
        {!products ? (
          <p role="status">Carregando…</p>
        ) : !products.length ? (
          <Empty>Nenhum produto 3D cadastrado. Crie um em Ferramentas → Impressão 3D.</Empty>
        ) : (
          <div>
            <div className="grid gap-3 sm:grid-cols-[1fr_auto_auto] items-end mb-3">
              <div>
                <label htmlFor="q-search">Buscar</label>
                <Input id="q-search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Nome ou código" />
              </div>
              <Button type="button" variant="outline"
                onClick={() => setPicked(Array.from(new Set([...picked, ...available.map((p) => p.id)])))}
                disabled={!available.length}>
                Marcar todos{search.trim() ? " os encontrados" : ""} ({available.length})
              </Button>
              <Button type="button" variant="outline" onClick={() => setPicked([])} disabled={!picked.length}>
                Limpar marcados
              </Button>
            </div>
            {!options.length ? (
              <Empty>Nenhum produto 3D encontrado.</Empty>
            ) : (
              <ul className="max-h-80 overflow-auto rounded-lg border divide-y" aria-label="Produtos 3D">
                {options.map((p) => {
                  const inQuote = inQuoteIds.includes(p.id);
                  return (
                    <li key={p.id}>
                      <label className={`flex items-center gap-3 px-3 min-h-11 cursor-pointer hover:bg-muted/50 ${inQuote ? "opacity-60" : ""}`}>
                        <input type="checkbox" className="h-5 w-5 accent-[var(--primary)]" disabled={inQuote}
                          checked={inQuote || picked.includes(p.id)}
                          onChange={(e) => setPicked((before) => e.target.checked ? [...before, p.id] : before.filter((id) => id !== p.id))} />
                        <span className="min-w-0 flex-1">
                          <span className="block break-words">{p.name}</span>
                          <span className="block text-xs text-muted-foreground">{p.sku}</span>
                        </span>
                        <span className="money text-sm">{inQuote ? "No orçamento" : brl(num(p.sale_price))}</span>
                      </label>
                    </li>
                  );
                })}
              </ul>
            )}
            <div className="mt-3">
              <Button type="button" disabled={!picked.length}
                onClick={() => {
                  const chosen = (products ?? []).filter((x) => picked.includes(x.id) && !inQuoteIds.includes(x.id));
                  setLines((before) => [...before, ...chosen.map(newLine)]);
                  setPicked([]);
                }}>
                <Plus size={18} aria-hidden className="mr-2" />
                {picked.length ? `Adicionar ${picked.length} ao orçamento` : "Marque os produtos para adicionar"}
              </Button>
            </div>
          </div>
        )}

        {lines.length > 0 && (
          <ul className="mt-5 space-y-3">
            {lines.map((l) => {
              const cost = num(l.product.cost_price);
              return (
                <li key={l.key} className="rounded-lg border p-3">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <p className="font-semibold min-w-0 break-words">{l.product.name}</p>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      aria-label={`Tirar ${l.product.name} do orçamento`}
                      title="Tirar do orçamento"
                      onClick={() => setLines((before) => before.filter((x) => x.key !== l.key))}
                    >
                      <Trash2 size={18} aria-hidden />
                    </Button>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div>
                      <label htmlFor={`q-qty-${l.key}`}>Quantidade</label>
                      <Input id={`q-qty-${l.key}`} inputMode="numeric" value={l.qty}
                        onChange={(e) => setLine(l.key, { qty: e.target.value.replace(/\D/g, "") })} />
                    </div>
                    <div>
                      <label htmlFor={`q-margin-${l.key}`}>Margem de lucro (%)</label>
                      <Input id={`q-margin-${l.key}`} inputMode="decimal" value={l.margin} disabled={cost <= 0}
                        onChange={(e) => changeMargin(l, e.target.value)} />
                    </div>
                    <div>
                      <label htmlFor={`q-price-${l.key}`}>Valor unitário (R$)</label>
                      <Input id={`q-price-${l.key}`} inputMode="decimal" value={l.price}
                        onChange={(e) => changePrice(l, e.target.value)} />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total do item</p>
                      <p className="money font-semibold pt-2">{brl(num(l.price) * qtyOf(l))}</p>
                    </div>
                  </div>
                  {cost <= 0 && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Sem custo cadastrado: o valor parte do preço de venda do produto e a margem não se aplica.
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </Card>

      <Card className="mb-5">
        <h2>2. Dados do orçamento</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label htmlFor="q-client">Cliente</label>
            <Input id="q-client" maxLength={120} value={client} onChange={(e) => setClient(e.target.value)} />
          </div>
          <div>
            <label htmlFor="q-contact">Contato (telefone ou e-mail)</label>
            <Input id="q-contact" maxLength={120} value={contact} onChange={(e) => setContact(e.target.value)} />
          </div>
          <div>
            <label htmlFor="q-validity">Validade (dias)</label>
            <Input id="q-validity" inputMode="numeric" value={validity}
              onChange={(e) => setValidity(e.target.value.replace(/\D/g, ""))} />
          </div>
          <div>
            <label htmlFor="q-lead">Prazo de produção</label>
            <Input id="q-lead" maxLength={120} placeholder="Ex.: 5 dias úteis" value={lead}
              onChange={(e) => setLead(e.target.value)} />
          </div>
          <div>
            <label htmlFor="q-discount">Desconto (R$)</label>
            <Input id="q-discount" inputMode="decimal" value={discount} onChange={(e) => setDiscount(e.target.value)} />
          </div>
          <div>
            <label htmlFor="q-shipping">Frete (R$)</label>
            <Input id="q-shipping" inputMode="decimal" value={shipping} onChange={(e) => setShipping(e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="q-notes">Observações</label>
            <textarea id="q-notes" rows={3} maxLength={800} value={notes} onChange={(e) => setNotes(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Cor, material, condições de pagamento…" />
          </div>
        </div>
      </Card>

      <Card>
        <h2>3. Orçamento para o cliente</h2>
        <p className="text-sm text-muted-foreground mb-4">
          É isto que o cliente recebe: sem custo e sem margem. Use o botão no alto da página para salvar em PDF ou
          imprimir.
        </p>
        {!lines.length ? (
          <Empty>Adicione ao menos um produto para ver o orçamento.</Empty>
        ) : (
          <div className="overflow-auto">
            <div
              id="orcamento-doc"
              ref={doc}
              style={{
                background: "#fff", color: "#1c1917", padding: 24, borderRadius: 8, border: "1px solid #e7e5e4",
                minWidth: 560, fontSize: 14, lineHeight: 1.45, fontFamily: "Arial, Helvetica, sans-serif",
              }}
            >
              <div style={{ ...row, alignItems: "center", gap: 16, marginBottom: 20 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={`${BASE}/assets/logo-jalapao.png`} alt="Jalapão Store" style={{ height: 64, width: "auto" }} />
                  <div>
                    <p style={{ fontWeight: 700, fontSize: 18, margin: 0 }}>Jalapão Store</p>
                    <p style={{ margin: 0, color: "#57534e" }}>Peças em impressão 3D</p>
                    <p style={{ margin: 0, color: "#57534e" }}>Instagram {INSTAGRAM}</p>
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontWeight: 700, fontSize: 18, margin: 0 }}>ORÇAMENTO</p>
                  <p style={{ margin: 0, color: "#57534e" }}>Emitido em {dateBr(issued)}</p>
                  {num(validity) > 0 && <p style={{ margin: 0, color: "#57534e" }}>Válido até {dateBr(until)}</p>}
                </div>
              </div>

              {(client || contact) && (
                <div style={{ marginBottom: 16 }}>
                  <p style={{ margin: 0, color: "#57534e" }}>Para</p>
                  {client && <p style={{ margin: 0, fontWeight: 600 }}>{client}</p>}
                  {contact && <p style={{ margin: 0 }}>{contact}</p>}
                </div>
              )}

              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #1c1917", textAlign: "left" }}>
                    <th style={{ padding: "6px 4px" }}>Produto</th>
                    <th style={{ padding: "6px 4px", textAlign: "right" }}>Qtd.</th>
                    <th style={{ padding: "6px 4px", textAlign: "right" }}>Valor unit.</th>
                    <th style={{ padding: "6px 4px", textAlign: "right" }}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((l) => {
                    const photo = photos[l.product.id];
                    return (
                      <tr key={l.key} style={{ borderBottom: "1px solid #e7e5e4", verticalAlign: "middle" }}>
                        <td style={{ padding: "8px 4px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            {photo && (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img src={imageUrl(photo.id)} alt={photo.alt_text || l.product.name}
                                style={{ width: 64, height: 64, objectFit: "contain", background: "#fafaf9", borderRadius: 4 }} />
                            )}
                            <div>
                              <p style={{ margin: 0, fontWeight: 600 }}>{l.product.name}</p>
                              {l.product.description && (
                                <p style={{ margin: 0, color: "#57534e", fontSize: 12 }}>
                                  {l.product.description.slice(0, 140)}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: "8px 4px", textAlign: "right" }}>{qtyOf(l)}</td>
                        <td style={{ padding: "8px 4px", textAlign: "right", whiteSpace: "nowrap" }}>{brl(num(l.price))}</td>
                        <td style={{ padding: "8px 4px", textAlign: "right", whiteSpace: "nowrap" }}>
                          {brl(num(l.price) * qtyOf(l))}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              <div style={{ marginTop: 14, marginLeft: "auto", width: 260 }}>
                <div style={row}><span>Subtotal</span><span>{brl(subtotal)}</span></div>
                {num(discount) > 0 && <div style={row}><span>Desconto</span><span>− {brl(num(discount))}</span></div>}
                {num(shipping) > 0 && <div style={row}><span>Frete</span><span>{brl(num(shipping))}</span></div>}
                <div style={{ ...row, fontWeight: 700, fontSize: 18, borderTop: "2px solid #1c1917", marginTop: 6, paddingTop: 6 }}>
                  <span>Total</span><span>{brl(total)}</span>
                </div>
              </div>

              {(lead || notes) && (
                <div style={{ marginTop: 20 }}>
                  {lead && <p style={{ margin: "0 0 6px" }}><strong>Prazo de produção:</strong> {lead}</p>}
                  {notes && <p style={{ margin: 0, whiteSpace: "pre-line" }}><strong>Observações:</strong> {notes}</p>}
                </div>
              )}
              <p style={{ marginTop: 24, color: "#57534e", fontSize: 12 }}>
                Jalapão Store · Instagram {INSTAGRAM} · Obrigado pela preferência!
              </p>
            </div>
          </div>
        )}
      </Card>
    </>
  );
}
