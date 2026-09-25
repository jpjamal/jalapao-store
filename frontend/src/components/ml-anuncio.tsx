"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

/* Spec 011 — o que é específico do Mercado Livre no rascunho: escolher a categoria a partir
   do título, preencher os atributos que ela pede e mostrar o relatório da validação.
   Nada aqui publica: consultar categoria e validar não criam anúncio. */

export type ValorAtributo = { value_id?: string; value_name: string };
export type Atributos = Record<string, ValorAtributo>;

type Sugestao = { category_id: string; category_name: string; domain_name: string };
type Atributo = {
  id: string;
  name: string;
  value_type: string;
  value_max_length: number | null;
  values: { id: string; name: string }[];
  allowed_units: string[];
  default_unit: string | null;
  required: boolean;
  conditional_required: boolean;
};
export type Categoria = {
  id: string;
  name: string;
  path: string[];
  listing_allowed: boolean;
  max_title_length: number | null;
  max_pictures_per_item: number | null;
  minimum_price: number | null;
};
type Achado = { nivel: string; origem: string; campo: string; mensagem: string; codigo: string };
export type Relatorio = {
  pode_publicar: boolean;
  simulado_no_mercado_livre: boolean;
  causas_de_foto_retiradas: number;
  categoria: { id: string; nome: string; caminho: string[] } | null;
  erros: Achado[];
  avisos: Achado[];
};

export function CategoriaEAtributos({
  titulo,
  categoryId,
  onCategoria,
  atributos,
  onAtributos,
  onInfo,
}: {
  titulo: string;
  categoryId: string;
  onCategoria: (id: string) => void;
  atributos: Atributos;
  onAtributos: (a: Atributos) => void;
  onInfo: (c: Categoria | null) => void;
}) {
  const [sugestoes, setSugestoes] = useState<Sugestao[]>([]);
  const [campos, setCampos] = useState<Atributo[]>([]);
  const [categoria, setCategoria] = useState<Categoria | null>(null);
  const [carregando, setCarregando] = useState("");
  const [erro, setErro] = useState("");

  // categoria escolhida → busca os atributos que ela pede
  useEffect(() => {
    const id = categoryId.trim();
    if (!id) {
      setCampos([]);
      setCategoria(null);
      onInfo(null);
      return;
    }
    let vivo = true;
    setCarregando("atributos");
    setErro("");
    api<{ category: Categoria; attributes: Atributo[] }>(
      `listing-drafts/ml-attributes?category_id=${encodeURIComponent(id)}`,
    )
      .then((r) => {
        if (!vivo) return;
        setCampos(r.attributes);
        setCategoria(r.category);
        onInfo(r.category);
      })
      .catch((e) => vivo && setErro((e as Error).message))
      .finally(() => vivo && setCarregando(""));
    return () => {
      vivo = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryId]);

  async function sugerir() {
    setCarregando("sugestao");
    setErro("");
    try {
      setSugestoes(
        await api<Sugestao[]>(`listing-drafts/ml-categories?q=${encodeURIComponent(titulo)}`),
      );
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setCarregando("");
    }
  }

  function definir(id: string, valor: ValorAtributo | null) {
    const novo = { ...atributos };
    if (valor && (valor.value_name || valor.value_id)) novo[id] = valor;
    else delete novo[id];
    onAtributos(novo);
  }

  const obrigatorios = campos.filter((c) => c.required);
  const pendentes = obrigatorios.filter((c) => !atributos[c.id]?.value_name && !atributos[c.id]?.value_id);

  return (
    <div className="sm:col-span-2 space-y-4">
      <div>
        <p className="font-medium mb-1">Categoria no Mercado Livre</p>
        <NavegadorCategorias categoryId={categoryId} onCategoria={onCategoria} />
        <Button
          type="button"
          variant="outline"
          className="mt-2"
          disabled={titulo.trim().length < 3 || carregando === "sugestao"}
          onClick={() => void sugerir()}
        >
          {carregando === "sugestao" ? "Buscando…" : "Sugerir pelo título"}
        </Button>
        {sugestoes.length > 0 && (
          <ul className="mt-2 space-y-1">
            {sugestoes.map((s, i) => (
              <li key={s.category_id}>
                <button
                  type="button"
                  className={`text-left w-full rounded-md border px-3 py-2 hover:bg-muted cursor-pointer ${
                    s.category_id === categoryId ? "border-primary" : ""
                  }`}
                  onClick={() => {
                    onCategoria(s.category_id);
                    setSugestoes([]);
                  }}
                >
                  <b>{s.category_name}</b>{" "}
                  <span className="text-sm text-muted-foreground">
                    {s.category_id}
                    {i === 0 ? " · mais provável" : ""}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {categoria && (
          <p className="text-sm text-muted-foreground mt-2">
            {categoria.path.join(" › ") || categoria.name}
            {!categoria.listing_allowed && (
              <span className="text-destructive">
                {" "}
                — não aceita anúncio, escolha uma categoria mais específica
              </span>
            )}
          </p>
        )}
        {erro && (
          <p role="alert" className="text-sm text-destructive mt-2">
            {erro}
          </p>
        )}
      </div>

      {carregando === "atributos" && <p role="status">Carregando atributos da categoria…</p>}

      {campos.length > 0 && (
        <details open={pendentes.length > 0} className="rounded-lg border p-4">
          <summary className="cursor-pointer font-semibold">
            Atributos da categoria
            <span className="text-sm font-normal text-muted-foreground">
              {" "}
              — {obrigatorios.length} obrigatório{obrigatorios.length === 1 ? "" : "s"}
              {pendentes.length > 0 ? `, ${pendentes.length} sem valor` : ", todos preenchidos"}
            </span>
          </summary>
          <p className="text-sm text-muted-foreground my-3">
            Marca e modelo preenchidos acima valem para os atributos de mesmo nome, se você não
            preencher aqui.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {campos.map((c) => (
              <CampoAtributo
                key={c.id}
                campo={c}
                valor={atributos[c.id]}
                onChange={(v) => definir(c.id, v)}
              />
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

function CampoAtributo({
  campo,
  valor,
  onChange,
}: {
  campo: Atributo;
  valor?: ValorAtributo;
  onChange: (v: ValorAtributo | null) => void;
}) {
  const id = `attr-${campo.id}`;
  const rotulo = (
    <label htmlFor={id}>
      {campo.name}
      {campo.required && <span className="text-destructive"> *</span>}
      {!campo.required && campo.conditional_required && (
        <span className="text-muted-foreground text-xs"> (pode ser exigido)</span>
      )}
    </label>
  );

  if (campo.values.length > 0) {
    return (
      <div>
        {rotulo}
        <select
          id={id}
          value={valor?.value_id || ""}
          onChange={(e) => {
            const escolhido = campo.values.find((v) => v.id === e.target.value);
            onChange(escolhido ? { value_id: escolhido.id, value_name: escolhido.name } : null);
          }}
        >
          <option value="">—</option>
          {campo.values.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (campo.value_type === "number_unit") {
    const [numero, unidade] = (valor?.value_name || "").split(" ");
    const unidadeAtual = unidade || campo.default_unit || campo.allowed_units[0] || "";
    return (
      <div>
        {rotulo}
        <div className="flex gap-2">
          <Input
            id={id}
            type="number"
            min="0"
            step="any"
            value={numero || ""}
            onChange={(e) =>
              onChange(e.target.value ? { value_name: `${e.target.value} ${unidadeAtual}`.trim() } : null)
            }
          />
          <select
            aria-label={`Unidade de ${campo.name}`}
            className="max-w-24"
            value={unidadeAtual}
            onChange={(e) => numero && onChange({ value_name: `${numero} ${e.target.value}` })}
          >
            {campo.allowed_units.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
        </div>
      </div>
    );
  }

  return (
    <div>
      {rotulo}
      <Input
        id={id}
        type={campo.value_type === "number" ? "number" : "text"}
        maxLength={campo.value_max_length || 255}
        value={valor?.value_name || ""}
        onChange={(e) => onChange(e.target.value ? { value_name: e.target.value } : null)}
      />
    </div>
  );
}

export function RelatorioValidacao({ relatorio }: { relatorio: Relatorio }) {
  const { pode_publicar, simulado_no_mercado_livre, erros, avisos } = relatorio;
  return (
    <div
      role="status"
      className={`rounded-lg border p-4 mt-5 ${
        pode_publicar ? "border-[var(--success)]" : "border-destructive"
      }`}
    >
      <p className="font-semibold mb-2">
        {pode_publicar
          ? "Pronto para publicar no Mercado Livre."
          : erros.length
            ? `${erros.length} ${erros.length === 1 ? "problema impede" : "problemas impedem"} a publicação.`
            : "Não foi possível concluir a validação."}
      </p>
      <p className="text-sm text-muted-foreground mb-3">
        {simulado_no_mercado_livre
          ? "Conferido aqui e simulado no Mercado Livre, sem criar anúncio."
          : "Conferido só aqui: corrija os itens básicos para a simulação no Mercado Livre rodar."}
        {relatorio.causas_de_foto_retiradas > 0 &&
          " As fotos são conferidas aqui; na simulação elas não vão."}
      </p>
      {erros.length > 0 && (
        <ul className="space-y-1 mb-3">
          {erros.map((e, i) => (
            <li key={i} className="text-destructive text-sm">
              ✕ {e.mensagem}
              {e.origem === "mercado_livre" && (
                <span className="text-muted-foreground"> · Mercado Livre{e.codigo ? ` (${e.codigo})` : ""}</span>
              )}
            </li>
          ))}
        </ul>
      )}
      {avisos.length > 0 && (
        <ul className="space-y-1">
          {avisos.map((a, i) => (
            <li key={i} className="text-sm">
              ! {a.mensagem}
              {a.origem === "mercado_livre" && (
                <span className="text-muted-foreground"> · Mercado Livre</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

type NoCategoria = {
  id: string;
  name: string;
  path: { id: string; name: string }[];
  listing_allowed: boolean;
  children: { id: string; name: string }[];
};

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
