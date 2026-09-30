"use client";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { brl } from "@/shared/lib/format";
import { brlGrama } from "@/features/supplies/api";
import { type Supply, type SupplyCategory } from "@/features/supplies/types";
import { SupplyCategoriesPanel } from "@/features/supplies/components/supply-categories-panel";
import { SupplyActionForm, type SupplyAction } from "@/features/supplies/components/supply-action-form";
import { SupplyHistory } from "@/features/supplies/components/supply-history";
import { type Page } from "@/shared/api/types";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { FormActions } from "@/shared/components/form-actions";
import { PageHeader } from "@/shared/components/page-header";
import { Pagination } from "@/shared/components/pagination";
import { ErrorMessage, Empty } from "@/shared/components/feedback";
import { Field } from "@/shared/components/fields";

function SupplyForm({
  supply,
  categories,
  materials,
  done,
  cancel,
}: {
  supply: Supply | null;
  categories: SupplyCategory[];
  materials: string[];
  done: () => void;
  cancel: () => void;
}) {
  // o formulário abre no topo da página: com a lista longa, leva a tela até ele
  useEffect(() => {
    document.getElementById("form-insumo")?.scrollIntoView({ block: "start" });
  }, []);
  // ativas para escolher; a categoria atual continua aparecendo mesmo se foi desativada
  const options = categories.filter((c) => c.active || c.id === supply?.category);
  const [categoryId, setCategoryId] = useState(supply?.category || options[0]?.id || "");
  const isFilament = !!categories.find((c) => c.id === categoryId)?.is_filament;
  const [rollWeight, setRollWeight] = useState(supply?.roll_weight_g ?? "");
  const [rollPrice, setRollPrice] = useState(supply?.roll_price ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const perGram = Number(rollWeight) > 0 && rollPrice !== "" ? Number(rollPrice) / Number(rollWeight) : null;
  return (
    <Card id="form-insumo" className="mb-6">
      <h2>{supply ? "Editar insumo" : "Novo insumo"}</h2>
      <ErrorMessage message={error} />
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          const f = new FormData(e.currentTarget);
          const payload: Record<string, unknown> = {
            category: categoryId,
            name: f.get("name"),
            unit: f.get("unit"),
            notes: f.get("notes"),
            active: f.get("active") === "on",
          };
          if (isFilament) {
            payload.material = f.get("material");
            payload.color = f.get("color");
            payload.roll_weight_g = rollWeight;
            payload.roll_price = rollPrice;
          }
          try {
            await api(`supplies${supply ? `/${supply.id}` : ""}`, {
              method: supply ? "PATCH" : "POST",
              body: JSON.stringify(payload),
            });
            done();
          } catch (err) {
            setError((err as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="category">Categoria</label>
            <select
              id="category"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              required
            >
              {options.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                  {c.active ? "" : " (inativa)"}
                </option>
              ))}
            </select>
          </div>
          <Field name="name" label="Nome do insumo" value={supply?.name} required maxLength={120} />
          <Field
            name="unit"
            label={isFilament ? "Unidade (rolo)" : "Unidade"}
            value={supply?.unit ?? (isFilament ? "rolo" : "unidade")}
            required
            maxLength={30}
            key={isFilament ? "unit-fil" : "unit"}
          />
        </div>
        {isFilament && (
          <>
            <div className="grid md:grid-cols-4 gap-4 mt-4">
              <div>
                <label htmlFor="material">Material</label>
                <Input
                  id="material"
                  name="material"
                  list="materiais"
                  defaultValue={supply?.material}
                  required
                  maxLength={40}
                  placeholder="PLA, PETG…"
                />
                <datalist id="materiais">
                  {materials.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </div>
              <Field name="color" label="Cor" value={supply?.color} required maxLength={40} />
              <div>
                <label htmlFor="roll_weight_g">Peso do rolo (g)</label>
                <Input
                  id="roll_weight_g"
                  type="number"
                  min="0.001"
                  step="0.001"
                  value={rollWeight}
                  onChange={(e) => setRollWeight(e.target.value)}
                  required
                />
              </div>
              <div>
                <label htmlFor="roll_price">Preço do rolo (R$)</label>
                <Input
                  id="roll_price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={rollPrice}
                  onChange={(e) => setRollPrice(e.target.value)}
                  required
                />
              </div>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {perGram === null
                ? "Informe o peso e o preço do rolo para ver o preço por grama."
                : `Preço por grama: ${brlGrama(perGram)} · por kg: ${brl(perGram * 1000)}`}
            </p>
          </>
        )}
        <div className="mt-4">
          <Field name="notes" label="Observação" value={supply?.notes} maxLength={500} />
        </div>
        <label className="flex items-center gap-2 my-5">
          <input type="checkbox" name="active" defaultChecked={supply?.active ?? true} />
          Insumo ativo
        </label>
        <FormActions>
          <Button disabled={busy}>{busy ? "Salvando…" : "Salvar insumo"}</Button>
          <Button type="button" variant="outline" onClick={cancel} disabled={busy}>
            Cancelar
          </Button>
        </FormActions>
      </form>
    </Card>
  );
}

export default function Supplies() {
  const [data, setData] = useState<Page<Supply> | null>(null);
  const [categories, setCategories] = useState<SupplyCategory[] | null>(null);
  const [materials, setMaterials] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Supply | null | undefined>(undefined);
  const [showCategories, setShowCategories] = useState(false);
  // duas abas (spec 024): o cadastro com o saldo, e as compras e movimentos
  const [tab, setTab] = useState<"cadastro" | "historico">("cadastro");
  const [action, setAction] = useState<{ kind: SupplyAction; supply: Supply } | undefined>(undefined);
  const [notice, setNotice] = useState("");
  const [historyKey, setHistoryKey] = useState(0);
  const loadCategories = useCallback(() => {
    api<Page<SupplyCategory>>("supply-categories")
      .then((r) => setCategories(r.results))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    loadCategories();
    api<{ results: string[] }>("supplies/materials")
      .then((r) => setMaterials(r.results))
      .catch(() => setMaterials([]));
  }, [loadCategories]);
  const load = useCallback(() => {
    setError("");
    const params = new URLSearchParams({ search, page: String(page) });
    if (categoryFilter) params.set("category", categoryFilter);
    api<Page<Supply>>(`supplies?${params}`)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [search, page, categoryFilter]);
  useEffect(load, [load]);
  return (
    <>
      <PageHeader
        title="Insumos"
        description="O que a loja consome para fabricar, embalar e operar: filamento, embalagens, etiquetas, colas, ferramentas. Insumo não é produto: não se vende nem aparece em vendas e anúncios."
        actions={
          tab === "cadastro" ? (
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => setShowCategories((v) => !v)}>
                {showCategories ? "Fechar categorias" : "Gerenciar categorias"}
              </Button>
              <Button onClick={() => setEditing(null)}>Novo insumo</Button>
            </div>
          ) : undefined
        }
      />
      <div role="tablist" aria-label="Seções de Insumos" className="flex gap-2 mb-5">
        {(
          [
            ["cadastro", "Cadastro e estoque"],
            ["historico", "Compras e movimentos"],
          ] as const
        ).map(([id, label]) => (
          <Button
            key={id}
            role="tab"
            aria-selected={tab === id}
            variant={tab === id ? "default" : "outline"}
            onClick={() => setTab(id)}
          >
            {label}
          </Button>
        ))}
      </div>
      <ErrorMessage message={error} />
      {tab === "historico" && (
        <SupplyHistory
          refreshKey={historyKey}
          onChanged={() => {
            load();
          }}
        />
      )}
      {tab === "cadastro" && notice && (
        <p role="status" className="border border-[var(--success)] text-[var(--success)] rounded-md p-3 mb-4">
          {notice}
        </p>
      )}
      {tab === "cadastro" && action && (
        <SupplyActionForm
          key={`${action.kind}-${action.supply.id}`}
          supply={action.supply}
          action={action.kind}
          done={(message) => {
            setAction(undefined);
            setNotice(message);
            setHistoryKey((k) => k + 1);
            load();
          }}
          cancel={() => setAction(undefined)}
        />
      )}
      {tab === "cadastro" && showCategories && <SupplyCategoriesPanel onChanged={loadCategories} />}
      {tab === "cadastro" && editing !== undefined && categories && (
        <SupplyForm
          key={editing?.id || "new"}
          supply={editing}
          categories={categories}
          materials={materials}
          done={() => {
            setEditing(undefined);
            load();
            loadCategories();
          }}
          cancel={() => setEditing(undefined)}
        />
      )}
      {tab === "cadastro" && (
      <Card>
        <div className="flex flex-col sm:flex-row gap-3 mb-5">
          <Input
            aria-label="Buscar insumos"
            placeholder="Buscar por nome, cor ou material…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            type="search"
            className="sm:max-w-md"
          />
          <select
            aria-label="Filtrar por categoria"
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="sm:max-w-xs"
          >
            <option value="">Todas as categorias</option>
            {(categories || []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        {!data ? (
          <p role="status">Carregando insumos…</p>
        ) : !data.results.length ? (
          <Empty>Nenhum insumo encontrado.</Empty>
        ) : (
          <div className="overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Insumo</th>
                  <th>Categoria</th>
                  <th>Saldo</th>
                  <th>Preço do rolo</th>
                  <th>Por grama / por kg</th>
                  <th>Status</th>
                  <th>
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((s) => (
                  <tr key={s.id}>
                    <td data-role="title">
                      <strong>{s.name}</strong>
                      {s.category_is_filament && (
                        <p className="text-xs text-muted-foreground font-normal">
                          {[s.material, s.color].filter(Boolean).join(" · ")}
                          {s.roll_weight_g ? ` · rolo de ${Number(s.roll_weight_g)} g` : ""}
                        </p>
                      )}
                    </td>
                    <td data-label="Categoria">{s.category_name}</td>
                    <td data-label="Saldo">
                      <strong>{s.quantity}</strong> {s.unit}
                    </td>
                    <td data-label="Preço do rolo" className="money">
                      {s.roll_price != null ? brl(s.roll_price) : "—"}
                    </td>
                    <td data-label="Por grama / por kg" className="money">
                      {s.price_per_gram != null
                        ? `${brlGrama(s.price_per_gram)} / ${brl(s.price_per_kg ?? 0)}`
                        : "—"}
                    </td>
                    <td data-label="Status">{s.active ? "Ativo" : "Inativo"}</td>
                    <td data-role="actions">
                      <div className="flex flex-wrap gap-2">
                        {s.active && (
                          <Button size="sm" onClick={() => { setNotice(""); setAction({ kind: "buy", supply: s }); }}>
                            Comprar
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={s.quantity === 0}
                          onClick={() => { setNotice(""); setAction({ kind: "baixa", supply: s }); }}
                        >
                          Dar baixa
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => { setNotice(""); setAction({ kind: "ajuste", supply: s }); }}>
                          Ajustar
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => setEditing(s)}>
                          Editar
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          count={data?.count || 0}
          noun={["insumo", "insumos"]}
          page={page}
          hasNext={!!data?.next}
          onPage={setPage}
        />
      </Card>
      )}
    </>
  );
}
