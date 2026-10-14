"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { type Page } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { FormActions } from "@/shared/components/form-actions";
import { PageHeader } from "@/shared/components/page-header";
import { useClientList } from "@/shared/hooks/use-list-query";
import { ClearFilters, FilterSelect, ListToolbar, SearchBox, SortSelect } from "@/shared/components/list-toolbar";
import { SortableTh } from "@/shared/components/sortable-th";
import { type SortColumn } from "@/shared/lib/list";
import { ListAction } from "@/shared/components/list-action";
import { DetailDialog, DetailList, RowTitle, rowOpen } from "@/shared/components/detail-dialog";

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

const accountColumns: SortColumn[] = [
  { key: "channel", label: "Canal", kind: "text" },
  { key: "name", label: "Loja", kind: "text" },
  { key: "token", label: "Token", kind: "text" },
  { key: "expires", label: "Autorização expira", kind: "date" },
  { key: "synced", label: "Última sincronia", kind: "date" },
];
const pendingColumns: SortColumn[] = [
  { key: "item_id", label: "Anúncio", kind: "text" },
  { key: "title", label: "Título", kind: "text" },
  { key: "sku", label: "Código no anúncio", kind: "text" },
];
const linkedColumns: SortColumn[] = [
  { key: "title", label: "Anúncio", kind: "text" },
  { key: "product", label: "Produto", kind: "text" },
  { key: "local", label: "Saldo aqui", kind: "number" },
  { key: "remote", label: "Saldo lá", kind: "number" },
  { key: "pushed", label: "Último envio", kind: "date" },
  { key: "sync", label: "Sincronizar", kind: "text" },
];

export default function Integracoes() {
  const [contas, setContas] = useState<Account[]>([]);
  const [viewingAccount, setViewingAccount] = useState<Account | null>(null);
  const [viewingListing, setViewingListing] = useState<Listing | null>(null);
  const [viewingPending, setViewingPending] = useState<{ item_id: string; title: string; sku: string } | null>(null);
  const [vinculos, setVinculos] = useState<Listing[]>([]);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [ocupado, setOcupado] = useState("");
  const [pendentes, setPendentes] = useState<{ item_id: string; title: string; sku: string }[]>(
    [],
  );
  // listas curtas, já carregadas por inteiro: busca, filtros e ordem acontecem na tela (spec 027)
  const accountList = useClientList(contas, {
    texts: (c) => [c.channel_label, c.name, c.external_id],
    filters: {
      channel: (c, v) => c.channel === v,
      token: (c, v) => (v === "valid" ? c.token_valido : !c.token_valido),
    },
    getters: {
      channel: (c) => c.channel_label,
      name: (c) => c.name || c.external_id,
      token: (c) => c.token_valido,
      expires: (c) => c.authorization_expires_at,
      synced: (c) => c.last_synced_at,
    },
  });
  const pendingList = useClientList(pendentes, {
    texts: (p) => [p.item_id, p.title, p.sku],
    getters: { item_id: (p) => p.item_id, title: (p) => p.title, sku: (p) => p.sku },
  });
  const linkedList = useClientList(vinculos, {
    texts: (v) => [v.title, v.item_id, v.product_name, v.product_sku, v.marketplace],
    filters: {
      marketplace: (v, value) => v.marketplace === value,
      sync: (v, value) => (value === "on" ? v.sync_enabled : !v.sync_enabled),
    },
    getters: {
      title: (v) => v.title || v.item_id,
      product: (v) => v.product_name,
      local: (v) => v.local_stock,
      remote: (v) => v.remote_stock,
      pushed: (v) => v.stock_pushed_at,
      sync: (v) => v.sync_enabled,
    },
  });

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

  function accountActions(c: Account, text: boolean) {
    return (
      <>
        <ListAction
          showText={text}
          kind="import"
          label="Importar anúncios"
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
        />
        <ListAction
          showText={text}
          kind="stock"
          label="Enviar estoque"
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
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Canais de venda"
        title="Integrações"
        description="Conecte a loja do marketplace, espelhe os anúncios e escolha quais deles recebem o saldo do seu estoque."
      />

      <ErrorMessage message={erro} />
      {viewingAccount && (
        <DetailDialog
          title={viewingAccount.name || viewingAccount.external_id}
          subtitle={viewingAccount.channel_label}
          onClose={() => setViewingAccount(null)}
          actions={accountActions(viewingAccount, true)}
        >
          <DetailList
            items={[
              ["Código da loja", viewingAccount.external_id],
              ["Token", viewingAccount.token_valido ? "Válido" : "Vai renovar"],
              [
                "Autorização expira",
                viewingAccount.authorization_days_left !== null
                  ? `${quando(viewingAccount.authorization_expires_at)} · ${viewingAccount.authorization_days_left} dia${viewingAccount.authorization_days_left === 1 ? "" : "s"}`
                  : quando(viewingAccount.authorization_expires_at),
              ],
              ["Última sincronia", quando(viewingAccount.last_synced_at)],
              ["Último erro", viewingAccount.last_error],
            ]}
          />
        </DetailDialog>
      )}
      {viewingListing && (
        <DetailDialog
          title={viewingListing.title || viewingListing.item_id}
          subtitle={`${viewingListing.marketplace} · ${viewingListing.item_id}`}
          onClose={() => setViewingListing(null)}
        >
          <DetailList
            items={[
              ["Produto", viewingListing.product_name],
              ["Código do produto", viewingListing.product_sku],
              ["Saldo aqui", String(viewingListing.local_stock ?? "—")],
              ["Saldo lá", String(viewingListing.remote_stock ?? "—")],
              ["Último envio", quando(viewingListing.stock_pushed_at)],
              ["Sincronizar estoque", viewingListing.sync_enabled ? "Sim" : "Não"],
            ]}
          />
        </DetailDialog>
      )}
      {viewingPending && (
        <DetailDialog
          title={viewingPending.title}
          subtitle="Anúncio sem produto correspondente"
          onClose={() => setViewingPending(null)}
        >
          <DetailList
            items={[
              ["Anúncio", viewingPending.item_id],
              ["Código no anúncio", viewingPending.sku || "— sem código —"],
            ]}
          />
        </DetailDialog>
      )}
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
            <ListToolbar>
              <SearchBox value={accountList.search} onChange={accountList.setSearch} placeholder="Canal ou loja…" />
              <FilterSelect
                label="Canal"
                value={accountList.filters.channel ?? ""}
                onChange={(v) => accountList.setFilter("channel", v)}
                options={Array.from(new Map(contas.map((c) => [c.channel, c.channel_label])).entries())}
              />
              <FilterSelect
                label="Token"
                value={accountList.filters.token ?? ""}
                onChange={(v) => accountList.setFilter("token", v)}
                options={[["valid", "Válido"], ["renew", "Vai renovar"]]}
              />
              <SortSelect columns={accountColumns} sort={accountList.sort} onChange={accountList.setSort} />
              <ClearFilters visible={accountList.hasActiveFilters} onClick={accountList.clear} />
            </ListToolbar>
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Canal" sortKey="channel" sort={accountList.sort} onSort={accountList.toggle} />
                  <SortableTh label="Loja" sortKey="name" sort={accountList.sort} onSort={accountList.toggle} />
                  <SortableTh label="Token" sortKey="token" sort={accountList.sort} onSort={accountList.toggle} />
                  <SortableTh label="Autorização expira" sortKey="expires" sort={accountList.sort} onSort={accountList.toggle} />
                  <SortableTh label="Última sincronia" sortKey="synced" sort={accountList.sort} onSort={accountList.toggle} />
                  <th><span className="sr-only">Ações</span></th>
                </tr>
              </thead>
              <tbody>
                {(accountList.visible ?? []).map((c) => (
                  <tr key={c.id} {...rowOpen(() => setViewingAccount(c))}>
                    <td data-role="title"><RowTitle onOpen={() => setViewingAccount(c)}>{c.channel_label}</RowTitle></td>
                    <td data-label="Loja">{c.name || c.external_id}</td>
                    <td data-label="Token">{c.token_valido ? "válido" : "vai renovar"}</td>
                    <td data-label="Autorização expira">
                      <span>
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
                      </span>
                    </td>
                    <td data-label="Última sincronia">{quando(c.last_synced_at)}</td>
                    <td data-role="actions">
                      <div className="flex flex-wrap gap-2 justify-end">
                      {accountActions(c, false)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <FormActions>
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
        </FormActions>
      </Card>

      {pendentes.length > 0 && (
        <Card className="mb-6">
          <h2>Anúncios sem produto correspondente</h2>
          <p className="text-muted-foreground mb-4">
            O casamento é pelo código (SKU). Estes anúncios não bateram com nenhum
            produto — nenhum produto foi criado. Cadastre com o mesmo código, ou
            ajuste o código do anúncio no marketplace, e importe de novo.
          </p>
          <ListToolbar>
            <SearchBox value={pendingList.search} onChange={pendingList.setSearch} placeholder="Anúncio, título ou código…" />
            <SortSelect columns={pendingColumns} sort={pendingList.sort} onChange={pendingList.setSort} />
            <ClearFilters visible={pendingList.hasActiveFilters} onClick={pendingList.clear} />
          </ListToolbar>
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Anúncio" sortKey="item_id" sort={pendingList.sort} onSort={pendingList.toggle} />
                  <SortableTh label="Título" sortKey="title" sort={pendingList.sort} onSort={pendingList.toggle} />
                  <SortableTh label="Código no anúncio" sortKey="sku" sort={pendingList.sort} onSort={pendingList.toggle} />
                </tr>
              </thead>
              <tbody>
                {(pendingList.visible ?? []).map((p) => (
                  <tr key={p.item_id} {...rowOpen(() => setViewingPending(p))}>
                    <td data-label="Anúncio" className="money">{p.item_id}</td>
                    <td data-role="title"><RowTitle onOpen={() => setViewingPending(p)}>{p.title}</RowTitle></td>
                    <td data-label="Código no anúncio" className="money">{p.sku || "— sem código —"}</td>
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
        {vinculos.length > 0 && (
          <ListToolbar>
            <SearchBox value={linkedList.search} onChange={linkedList.setSearch} placeholder="Anúncio, produto ou código…" />
            <FilterSelect
              label="Marketplace"
              value={linkedList.filters.marketplace ?? ""}
              onChange={(v) => linkedList.setFilter("marketplace", v)}
              options={Array.from(new Set(vinculos.map((v) => v.marketplace))).map((m) => [m, m])}
            />
            <FilterSelect
              label="Sincronização"
              value={linkedList.filters.sync ?? ""}
              onChange={(v) => linkedList.setFilter("sync", v)}
              options={[["on", "Ligada"], ["off", "Desligada"]]}
            />
            <SortSelect columns={linkedColumns} sort={linkedList.sort} onChange={linkedList.setSort} />
            <ClearFilters visible={linkedList.hasActiveFilters} onClick={linkedList.clear} />
          </ListToolbar>
        )}
        {!vinculos.length ? (
          <Empty>Nenhum anúncio vinculado.</Empty>
        ) : !linkedList.visible?.length ? (
          <Empty>Nenhum anúncio encontrado com esses filtros.</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <SortableTh label="Anúncio" sortKey="title" sort={linkedList.sort} onSort={linkedList.toggle} />
                  <SortableTh label="Produto" sortKey="product" sort={linkedList.sort} onSort={linkedList.toggle} />
                  <SortableTh label="Saldo aqui" sortKey="local" sort={linkedList.sort} onSort={linkedList.toggle} />
                  <SortableTh label="Saldo lá" sortKey="remote" sort={linkedList.sort} onSort={linkedList.toggle} />
                  <SortableTh label="Último envio" sortKey="pushed" sort={linkedList.sort} onSort={linkedList.toggle} />
                  <SortableTh label="Sincronizar" sortKey="sync" sort={linkedList.sort} onSort={linkedList.toggle} />
                </tr>
              </thead>
              <tbody>
                {linkedList.visible.map((v) => (
                  <tr key={v.id} {...rowOpen(() => setViewingListing(v))}>
                    <td data-role="title">
                      <RowTitle onOpen={() => setViewingListing(v)}>
                      {v.title || v.item_id}
                      <span className="block text-xs text-muted-foreground font-normal">
                        {v.marketplace} · {v.item_id}
                      </span>
                      </RowTitle>
                    </td>
                    <td data-label="Produto">
                      <span>
                        {v.product_name}
                        <span className="block text-xs text-muted-foreground">
                          {v.product_sku}
                        </span>
                      </span>
                    </td>
                    <td data-label="Saldo aqui" className="money">{v.local_stock ?? "—"}</td>
                    <td data-label="Saldo lá" className="money">{v.remote_stock ?? "—"}</td>
                    <td data-label="Último envio">{quando(v.stock_pushed_at)}</td>
                    <td data-label="Sincronizar">
                      <label className="flex items-center gap-2 min-h-11 md:min-h-0 cursor-pointer">
                        <input
                          type="checkbox"
                          className="h-5 w-5 accent-[var(--primary)]"
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
          <li>Publicar e editar anúncio: no Mercado Livre é pela tela Anúncios; na Shopee, ainda pelo painel dela.</li>
          <li>Vendas do Mercado Livre entram pela tela Vendas → Importar do Mercado Livre, quando você mandar; as da Shopee, ainda à mão.</li>
          <li>Empurrar preço — decisão comercial, fica fora por enquanto.</li>
          <li>Mercado Livre — conexão, importação e envio manual de estoque; anúncios com variações ou depósitos ambíguos exigem configuração posterior.</li>
        </ul>
      </Card>
    </>
  );
}
