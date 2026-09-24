"use client";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { Product } from "@/lib/api";

/* Campo de produto com busca por digitação.

   A lista de peças cresce e um <select> obriga a rolar procurando com o olho.
   Aqui você digita parte do nome (ou do código) e a lista filtra. Acento não
   atrapalha: "luminaria" acha "Luminária".

   O input visível é o que carrega o `required`. Se você digitar e sair sem
   escolher nada da lista, o texto é apagado no blur — assim o navegador barra o
   envio, em vez de deixar passar um formulário com nome escrito e produto
   nenhum selecionado. */

const semAcento = (s: string) =>
  s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();

const TETO = 50; // não desenha a lista inteira quando o catálogo crescer

export function ProductPicker({
  products,
  value,
  onChange,
  id,
  name,
  required,
  disabled,
  placeholder = "Digite para procurar…",
  mostrarQuantidade = true,
  somenteAtivos = true,
}: {
  products: Product[];
  value: string;
  onChange: (id: string, product: Product | null) => void;
  id?: string;
  /** cria um input oculto com este nome, para formulários que leem FormData */
  name?: string;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  mostrarQuantidade?: boolean;
  /** ajuste de inventário também alcança produto desativado */
  somenteAtivos?: boolean;
}) {
  const gerado = useId();
  const campoId = id || gerado;
  const listaId = `${campoId}-lista`;

  const [texto, setTexto] = useState("");
  const [aberto, setAberto] = useState(false);
  const [ativo, setAtivo] = useState(0);
  const caixa = useRef<HTMLDivElement>(null);

  const rotulo = (p: Product) =>
    mostrarQuantidade ? `${p.name} — ${p.quantity} un.` : p.name;

  const escolhido = useMemo(
    () => products.find((p) => p.id === value) || null,
    [products, value],
  );

  // quando a escolha muda de fora (edição, limpar formulário), o texto acompanha
  useEffect(() => {
    if (!aberto) setTexto(escolhido ? rotulo(escolhido) : "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [escolhido, aberto]);

  const filtrados = useMemo(() => {
    const busca = semAcento(texto.trim());
    const base = somenteAtivos ? products.filter((p) => p.active) : products;
    if (!busca || (escolhido && texto === rotulo(escolhido))) return base;
    return base.filter(
      (p) =>
        semAcento(p.name).includes(busca) || semAcento(p.sku).includes(busca),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [products, texto, escolhido, somenteAtivos]);

  const visiveis = filtrados.slice(0, TETO);

  // clique fora fecha e devolve o texto ao que estava escolhido
  useEffect(() => {
    if (!aberto) return;
    const fora = (e: MouseEvent) => {
      if (!caixa.current?.contains(e.target as Node)) fechar();
    };
    document.addEventListener("mousedown", fora);
    return () => document.removeEventListener("mousedown", fora);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aberto, escolhido]);

  function fechar() {
    setAberto(false);
    setTexto(escolhido ? rotulo(escolhido) : "");
  }

  function escolher(p: Product) {
    onChange(p.id, p);
    setTexto(rotulo(p));
    setAberto(false);
  }

  function aoTeclar(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!aberto) {
        setAberto(true);
        setAtivo(0);
        return;
      }
      const passo = e.key === "ArrowDown" ? 1 : -1;
      setAtivo((i) => (i + passo + visiveis.length) % Math.max(visiveis.length, 1));
    } else if (e.key === "Enter") {
      if (aberto && visiveis[ativo]) {
        e.preventDefault();
        escolher(visiveis[ativo]);
      }
    } else if (e.key === "Escape") {
      if (aberto) {
        e.preventDefault();
        fechar();
      }
    }
  }

  return (
    <div className="relative" ref={caixa}>
      <input
        id={campoId}
        type="text"
        role="combobox"
        autoComplete="off"
        spellCheck={false}
        aria-expanded={aberto}
        aria-controls={listaId}
        aria-autocomplete="list"
        aria-activedescendant={
          aberto && visiveis[ativo] ? `${listaId}-${ativo}` : undefined
        }
        required={required}
        disabled={disabled}
        placeholder={placeholder}
        value={texto}
        onChange={(e) => {
          setTexto(e.target.value);
          setAberto(true);
          setAtivo(0);
          // apagou tudo: a escolha também some
          if (!e.target.value.trim() && value) onChange("", null);
        }}
        onFocus={() => {
          setAberto(true);
          setAtivo(0);
        }}
        onKeyDown={aoTeclar}
        onBlur={() => {
          // dá tempo do clique na opção acontecer antes de fechar
          setTimeout(() => {
            setAberto(false);
            setTexto(escolhido ? rotulo(escolhido) : "");
          }, 150);
        }}
        className="w-full border border-input rounded-md bg-background p-[0.55rem]"
      />
      {name && <input type="hidden" name={name} value={value} />}

      {aberto && (
        <ul
          id={listaId}
          role="listbox"
          className="absolute z-30 left-0 right-0 mt-1 max-h-64 overflow-auto rounded-md border bg-card shadow-lg"
        >
          {visiveis.length === 0 ? (
            <li className="px-3 py-3 text-sm text-muted-foreground">
              Nenhum produto com esse nome.
            </li>
          ) : (
            visiveis.map((p, i) => (
              <li
                key={p.id}
                id={`${listaId}-${i}`}
                role="option"
                aria-selected={p.id === value}
                onMouseEnter={() => setAtivo(i)}
                onMouseDown={(e) => {
                  e.preventDefault(); // não deixa o blur disparar antes do clique
                  escolher(p);
                }}
                className={`px-3 py-2 cursor-pointer flex justify-between gap-3 ${
                  i === ativo ? "bg-muted" : ""
                }`}
              >
                <span className="truncate">{p.name}</span>
                {mostrarQuantidade && (
                  <span className="money text-sm text-muted-foreground shrink-0">
                    {p.quantity} un.
                  </span>
                )}
              </li>
            ))
          )}
          {filtrados.length > TETO && (
            <li className="px-3 py-2 text-xs text-muted-foreground border-t">
              e mais {filtrados.length - TETO} — escreva mais para afunilar
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
