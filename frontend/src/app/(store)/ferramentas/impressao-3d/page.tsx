"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  brl,
  calcular,
  horasTexto,
  num,
  type Entradas3D,
} from "@/lib/ferramentas/custo3d";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ErrorMessage } from "@/components/feedback";

/* A conta vive em lib/ferramentas/custo3d.ts e é a mesma de antes.
   Esta tela só coleta os números e mostra o resultado. */

const CHAVE = "jalapao_impressao3d";

const vazio: Entradas3D = {
  precoKg: "115",
  gramas: "",
  consumo: "200",
  horas: "",
  minutos: "",
  kwh: "1.56",
  maoDeObra: "",
  custoFixo: "",
  margem: "100",
};

/* o que descreve a impressora, e não a peça: volta preenchido na próxima visita */
const daMaquina = ["precoKg", "consumo", "kwh"] as const;

const campos: {
  chave: keyof Entradas3D;
  rotulo: string;
  dica?: string;
  passo?: string;
}[] = [
  { chave: "precoKg", rotulo: "Filamento (R$ por kg)", passo: "0.01" },
  { chave: "gramas", rotulo: "Peso da peça (g)", passo: "0.1" },
  { chave: "consumo", rotulo: "Consumo da impressora (W)", passo: "1" },
  { chave: "horas", rotulo: "Tempo — horas", passo: "1" },
  { chave: "minutos", rotulo: "Tempo — minutos", passo: "1" },
  { chave: "kwh", rotulo: "Energia (R$ por kWh)", passo: "0.0001" },
  { chave: "maoDeObra", rotulo: "Mão de obra (R$)", passo: "0.01" },
  { chave: "custoFixo", rotulo: "Custos fixos (R$)", passo: "0.01" },
  { chave: "margem", rotulo: "Margem de lucro (%)", passo: "1" },
];

const paraApi = {
  precoKg: "filament_price_kg",
  gramas: "weight_g",
  consumo: "power_w",
  horas: "hours",
  minutos: "minutes",
  kwh: "energy_price_kwh",
  maoDeObra: "labor_cost",
  custoFixo: "fixed_cost",
  margem: "markup_percent",
} as const;

export default function Impressao3D() {
  const [entradas, setEntradas] = useState<Entradas3D>(vazio);
  const [nome, setNome] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [aviso, setAviso] = useState("");
  const [erro, setErro] = useState("");

  // valores da impressora ficam guardados neste navegador; a peça não
  useEffect(() => {
    try {
      const cru = localStorage.getItem(CHAVE);
      if (cru) setEntradas((e) => ({ ...e, ...JSON.parse(cru) }));
    } catch {
      /* navegador sem localStorage: segue com os padrões */
    }
  }, []);

  const trocar = (chave: keyof Entradas3D, valor: string) => {
    setEntradas((e) => {
      const novo = { ...e, [chave]: valor };
      if ((daMaquina as readonly string[]).includes(chave)) {
        try {
          localStorage.setItem(
            CHAVE,
            JSON.stringify(
              Object.fromEntries(daMaquina.map((k) => [k, novo[k]])),
            ),
          );
        } catch {
          /* sem localStorage, só não guarda */
        }
      }
      return novo;
    });
  };

  const r = useMemo(() => calcular(entradas), [entradas]);

  async function salvar() {
    if (!nome.trim()) {
      setErro("Informe o nome do produto.");
      return;
    }
    setSalvando(true);
    setErro("");
    setAviso("");
    try {
      const printing = Object.fromEntries(
        Object.entries(paraApi).map(([meu, deles]) => [
          deles,
          Number(entradas[meu as keyof Entradas3D] || 0),
        ]),
      );
      await api("products", {
        method: "POST",
        body: JSON.stringify({
          name: nome.trim(),
          kind: "printing",
          sku: `3D-${crypto.randomUUID().slice(0, 12)}`,
          printing,
        }),
      });
      setAviso(`"${nome.trim()}" entrou no catálogo da loja.`);
      setNome("");
    } catch (e) {
      setErro((e as Error).message);
    } finally {
      setSalvando(false);
    }
  }

  const linhas: [string, string, string?][] = [
    ["Filamento", brl(r.filamento), `${num(entradas.gramas)} g`],
    ["Energia", brl(r.energia), `${r.kwhGastos.toFixed(3)} kWh`],
    ["Mão de obra", brl(r.maoDeObra)],
    ["Custos fixos", brl(r.custoFixo)],
  ];

  return (
    <>
      <p className="text-xs tracking-widest uppercase text-muted-foreground mb-3">
        Ferramentas · simulação
      </p>
      <h1>Custo de impressão 3D</h1>
      <p className="text-muted-foreground mb-8">
        Filamento, energia, tempo e margem. A mesma conta que o catálogo usa para
        sugerir o preço de uma peça.
      </p>

      <div className="grid lg:grid-cols-[1fr_380px] gap-6 items-start">
        <Card>
          <h2>Dados da peça e da impressora</h2>
          <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {campos.map((c) => (
              <div key={c.chave}>
                <label htmlFor={c.chave}>{c.rotulo}</label>
                <Input
                  id={c.chave}
                  type="number"
                  min="0"
                  step={c.passo}
                  inputMode="decimal"
                  value={String(entradas[c.chave] ?? "")}
                  onChange={(e) => trocar(c.chave, e.target.value)}
                />
              </div>
            ))}
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            Filamento, consumo e preço do kWh ficam guardados neste navegador —
            na próxima peça já vêm preenchidos. O tempo entra em horas e minutos
            separados de propósito: 4 h 30 não é 4,30.
          </p>
        </Card>

        <Card>
          <h2>Resultado</h2>
          {!r.completo && (
            <p className="text-sm text-muted-foreground mb-4">
              Preencha filamento, peso, consumo, tempo e energia para a conta
              fechar.
            </p>
          )}
          <dl className="grid grid-cols-2 gap-y-3 mb-5">
            {linhas.map(([rotulo, valor, extra]) => (
              <div key={rotulo} className="contents">
                <dt className="text-muted-foreground text-sm self-center">
                  {rotulo}
                  {extra ? (
                    <span className="block text-xs opacity-70">{extra}</span>
                  ) : null}
                </dt>
                <dd className="money text-right">{valor}</dd>
              </div>
            ))}
            <div className="contents">
              <dt className="text-muted-foreground text-sm self-center">
                Tempo de impressão
              </dt>
              <dd className="money text-right">{horasTexto(r.tempoHoras)}</dd>
            </div>
          </dl>
          <div className="border-t pt-4 grid grid-cols-2 gap-y-3">
            <span className="text-muted-foreground text-sm self-center">
              Custo total
            </span>
            <span className="money text-right text-lg">
              {brl(r.custoTotal)}
            </span>
            <span className="text-muted-foreground text-sm self-center">
              Lucro
            </span>
            <span className="money text-right">{brl(r.lucro)}</span>
            <span className="text-sm self-center font-semibold">
              Preço sugerido
            </span>
            <span className="money text-right text-2xl text-primary">
              {brl(r.precoFinal)}
            </span>
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <h2>Guardar no catálogo</h2>
        <p className="text-muted-foreground mb-4">
          Salva a peça como produto de impressão 3D com estes parâmetros. O
          estoque começa em zero — a quantidade entra depois, em compras e
          produção.
        </p>
        <ErrorMessage message={erro} />
        {aviso && (
          <p
            role="status"
            className="border border-[var(--success)] text-[var(--success)] rounded-md p-3 mb-4"
          >
            {aviso}{" "}
            <Link href="/produtos" className="font-semibold underline">
              ver no catálogo
            </Link>
          </p>
        )}
        <div className="flex flex-wrap gap-3 items-end">
          <div className="grow min-w-60">
            <label htmlFor="nomeProduto">Nome do produto</label>
            <Input
              id="nomeProduto"
              value={nome}
              maxLength={200}
              placeholder="Luminária Air Form"
              onChange={(e) => setNome(e.target.value)}
            />
          </div>
          <Button onClick={salvar} disabled={salvando || !r.completo}>
            {salvando ? "Salvando…" : "Salvar produto"}
          </Button>
        </div>
      </Card>
    </>
  );
}
