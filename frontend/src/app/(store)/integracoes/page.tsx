"use client";
import { useCallback, useEffect, useState } from "react";
import { api, type Page } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorMessage, Empty } from "@/components/feedback";

type Account = {
  id: string;
  channel: string;
  channel_label: string;
  external_id: string;
  name: string;
  active: boolean;
  token_valido: boolean;
  authorization_expires_at: string | null;
  authorization_days_left: number | null;
  last_synced_at: string | null;
  last_error: string;
};

type Listing = {
  id: string;
  marketplace: string;
  item_id: string;
  title: string;
  product_name: string;
  product_sku: string;
  local_stock: number | null;
  remote_stock: number | null;
  sync_enabled: boolean;
  stock_pushed_at: string | null;
};

const quando = (v: string | null) =>
  v ? new Date(v).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "—";

export default function Integracoes() {
  const [contas, setContas] = useState<Account[]>([]);
  const [vinculos, setVinculos] = useState<Listing[]>([]);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [ocupado, setOcupado] = useState("");
  const [pendentes, setPendentes] = useState<{ item_id: string; title: string; sku: string }[]>(
    [],
  );

  const carregar = useCallback(() => {
    Promise.all([
      api<Page<Account>>("integrations"),
      api<Page<Listing>>("listings"),
    ])
      .then(([c, v]) => {
        setContas(c.results);
        setVinculos(v.results);
      })
      .catch((e) => setErro((e as Error).message));
  }, []);
  useEffect(carregar, [carregar]);

  async function acao(nome: string, chamada: () => Promise<unknown>) {
    setOcupado(nome);
    setErro("");
    setAviso("");
    try {
      await chamada();
      carregar();
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setOcupado("");
    }
  }

  return (
    <>
      <p className="text-xs tracking-widest uppercase text-muted-foreground mb-3">
        Canais de venda
      </p>
      <h1>Integrações</h1>
      <p className="text-muted-foreground mb-8">
        Conecte a loja do marketplace, espelhe os anúncios e escolha quais deles
        recebem o saldo do seu estoque.
      </p>

      <ErrorMessage message={erro} />
      {aviso && (
        <p role="status" className="text-success mb-4">
          {aviso}
        </p>
      )}

      <Card className="mb-6">
        <h2>Lojas conectadas</h2>
        {!contas.length ? (
          <>
            <Empty>Nenhuma loja conectada ainda.</Empty>
            <p className="text-sm text-muted-foreground mb-4">
              Conectar abre a página do marketplace para você autorizar. Ao voltar, a
              loja aparece aqui. Nada do seu catálogo é alterado nesse passo.
            </p>
          </>
        ) : (
          <div className="overflow-auto mb-4">
            <table>
              <thead>
                <tr>
                  <th>Canal</th>
                  <th>Loja</th>
                  <th>Token</th>
                  <th>Autorização expira</th>
                  <th>Última sincronia</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {contas.map((c) => (
                  <tr key={c.id}>
                    <td>{c.channel_label}</td>
                    <td>{c.name || c.external_id}</td>
                    <td>{c.token_valido ? "válido" : "vai renovar"}</td>
                    <td>
                      {quando(c.authorization_expires_at)}
                      {c.authorization_days_left !== null && (
                        <span
                          className={`block text-xs ${
                            c.authorization_days_left <= 15
                              ? "text-destructive"
                              : "text-muted-foreground"
                          }`}
                        >
                          {c.authorization_days_left} dia
                          {c.authorization_days_left === 1 ? "" : "s"}
                        </span>
                      )}
                    </td>
                    <td>{quando(c.last_synced_at)}</td>
                    <td className="whitespace-nowrap text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={!!ocupado}
                        onClick={() =>
                          acao("importar", async () => {
                            const r = await api<{
                              total: number;
                              vinculos_novos: number;
                              pendentes: typeof pendentes;
                            }>(`integrations/${c.id}/import-listings`, {
                              method: "POST",
                              body: "{}",
                            });
                            setPendentes(r.pendentes || []);
                            setAviso(
                              `${r.total} anúncio(s) lidos, ${r.vinculos_novos} vínculo(s) novo(s), ${r.pendentes.length} sem produto correspondente.`,
                            );
                          })
                        }
                      >
                        Importar anúncios
                      </Button>{" "}
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={!!ocupado}
                        onClick={() =>
                          acao("estoque", async () => {
                            const r = await api<{
                              enviados: number;
                              ignorados: number;
                              falhas: string[];
                            }>(`integrations/${c.id}/push-stock`, {
                              method: "POST",
                              body: "{}",
                            });
                            setAviso(
                              `${r.enviados} envio(s) de saldo, ${r.ignorados} sem nada a fazer` +
                                (r.falhas.length ? `, ${r.falhas.length} falha(s)` : "."),
                            );
                          })
                        }
                      >
                        Enviar estoque
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Button
          disabled={!!ocupado}
          onClick={() =>
            acao("conectar", async () => {
              const r = await api<{ url: string }>(
                "integrations/auth-link?channel=shopee",
              );
              window.location.assign(r.url);
            })
          }
        >
          {ocupado === "conectar" ? "Abrindo…" : "Conectar loja da Shopee"}
        </Button>
        {" "}
        <Button
          variant="outline"
          disabled={!!ocupado}
          onClick={() =>
            acao("conectar-ml", async () => {
              const r = await api<{ url: string }>("integrations/ml-auth-link", {
                method: "POST", body: "{}",
              });
              window.location.assign(r.url);
            })
          }
        >
          {ocupado === "conectar-ml" ? "Abrindo…" : "Conectar Mercado Livre"}
        </Button>
      </Card>

      {pendentes.length > 0 && (
        <Card className="mb-6">
          <h2>Anúncios sem produto correspondente</h2>
          <p className="text-muted-foreground mb-4">
            O casamento é pelo código (SKU). Estes anúncios não bateram com nenhum
            produto — nenhum produto foi criado. Cadastre com o mesmo código, ou
            ajuste o código do anúncio no marketplace, e importe de novo.
          </p>
          <div className="overflow-auto">
            <table>
              <thead>
                <tr>
                  <th>Anúncio</th>
                  <th>Título</th>
                  <th>Código no anúncio</th>
                </tr>
              </thead>
              <tbody>
                {pendentes.map((p) => (
                  <tr key={p.item_id}>
                    <td className="money">{p.item_id}</td>
                    <td>{p.title}</td>
                    <td className="money">{p.sku || "— sem código —"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Card>
        <h2>Anúncios vinculados</h2>
        <p className="text-muted-foreground mb-4">
          O interruptor começa desligado. Ligado, toda mudança de saldo local passa
          a ser levada para o anúncio quando você mandar enviar. O saldo do
          marketplace nunca sobrescreve o daqui.
        </p>
        {!vinculos.length ? (
          <Empty>Nenhum anúncio vinculado.</Empty>
        ) : (
          <div className="overflow-auto">
            <table>
              <thead>
                <tr>
                  <th>Anúncio</th>
                  <th>Produto</th>
                  <th>Saldo aqui</th>
                  <th>Saldo lá</th>
                  <th>Último envio</th>
                  <th>Sincronizar</th>
                </tr>
              </thead>
              <tbody>
                {vinculos.map((v) => (
                  <tr key={v.id}>
                    <td>
                      {v.title || v.item_id}
                      <span className="block text-xs text-muted-foreground">
                        {v.marketplace} · {v.item_id}
                      </span>
                    </td>
                    <td>
                      {v.product_name}
                      <span className="block text-xs text-muted-foreground">
                        {v.product_sku}
                      </span>
                    </td>
                    <td className="money">{v.local_stock ?? "—"}</td>
                    <td className="money">{v.remote_stock ?? "—"}</td>
                    <td>{quando(v.stock_pushed_at)}</td>
                    <td>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={v.sync_enabled}
                          disabled={!!ocupado}
                          onChange={(e) =>
                            acao("interruptor", () =>
                              api(`listings/${v.id}`, {
                                method: "PATCH",
                                body: JSON.stringify({
                                  sync_enabled: e.target.checked,
                                }),
                              }),
                            )
                          }
                        />
                        <span className="sr-only">
                          Sincronizar estoque de {v.product_name}
                        </span>
                      </label>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card className="mt-6">
        <h2>O que ainda não é feito por aqui</h2>
        <ul className="text-muted-foreground list-disc pl-5 space-y-1">
          <li>Publicar ou editar anúncio — o cadastro continua sendo no painel do marketplace.</li>
          <li>Importar pedido e taxa real da venda — entra em etapa própria.</li>
          <li>Empurrar preço — decisão comercial, fica fora por enquanto.</li>
          <li>Mercado Livre — conexão, importação e envio manual de estoque; anúncios com variações ou depósitos ambíguos exigem configuração posterior.</li>
        </ul>
      </Card>
    </>
  );
}
