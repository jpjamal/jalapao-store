"use client";
import { useEffect, useState } from "react";
import { api } from "@/shared/api/client";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import type { Atributo, Atributos, Categoria, Sugestao, ValorAtributo } from "@/features/listings/types";
import { NavegadorCategorias } from "@/features/listings/components/category-navigator";

/* Spec 011 — o que é específico do Mercado Livre no rascunho: escolher a categoria a partir
   do título, preencher os atributos que ela pede e mostrar o relatório da validação.
   Nada aqui publica: consultar categoria e validar não criam anúncio. */

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
