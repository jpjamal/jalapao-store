"use client";
import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import {
  camposVazios,
  labelary,
  lerEtiqueta,
  naFila,
  nomeArquivo,
  nomeUnico,
  salvar,
  slug,
  type Config,
  type Etiqueta,
  type Padrao,
} from "@/lib/ferramentas/etiquetas";
import { PageHeader } from "@/components/page-header";

/* O ZPL da Shopee é uma imagem, não texto: o destinatário só sai por OCR sobre a
   etiqueta renderizada pelo Labelary. Toda essa lógica está em
   lib/ferramentas/etiquetas.ts, igual à da versão anterior. */

const padroes: [Padrao, string][] = [
  ["nome_cidade", "Nome e cidade"],
  ["nome", "Só o nome"],
  ["nome_uf", "Nome e estado"],
  ["nome_cidade_uf", "Nome, cidade e estado"],
  ["curto_cidade", "Primeiro e último nome, e cidade"],
  ["pedido", "ID do pedido"],
  ["rastreio", "Código de rastreio"],
  ["arquivo", "Nome do arquivo enviado"],
];

export default function Etiquetas() {
  const [cfg, setCfg] = useState<Config>({
    tamanho: "4x6",
    dpmm: "8",
    pagina: "A4",
    rotacao: "0",
    padrao: "nome_cidade",
    ocr: true,
  });
  const [etiquetas, setEtiquetas] = useState<Etiqueta[]>([]);
  const [registro, setRegistro] = useState("Envie um .txt com o ZPL.");
  const [colando, setColando] = useState(false);
  const [zplTexto, setZplTexto] = useState("");
  const [arrastando, setArrastando] = useState(false);
  const [pasta, setPasta] = useState<FileSystemDirectoryHandle | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [lupa, setLupa] = useState<string | null>(null);

  const contador = useRef(0);
  const entrada = useRef<HTMLInputElement>(null);
  // a fila é assíncrona e precisa enxergar o estado mais recente
  const atuais = useRef<Etiqueta[]>([]);
  const cfgRef = useRef(cfg);
  cfgRef.current = cfg;

  const log = useCallback((txt: string) => {
    setRegistro((r) => `${r}\n${txt}`);
  }, []);

  const guardar = (lista: Etiqueta[]) => {
    atuais.current = lista;
    setEtiquetas(lista);
  };
  const mexer = (id: number, mudanca: Partial<Etiqueta>) =>
    guardar(
      atuais.current.map((e) => (e.id === id ? { ...e, ...mudanca } : e)),
    );

  async function processar(zpl: string, origem: string) {
    const c = cfgRef.current;
    setOcupado(true);
    log(`\n▶ ${origem}: enviando para o Labelary...`);
    let primeira;
    try {
      primeira = await naFila(() => labelary(zpl, 0, "image/png", c, log));
    } catch (e) {
      log(`✗ ${origem}: ${(e as Error).message}`);
      setOcupado(false);
      return;
    }
    const total = primeira.total;
    log(`  ${total} etiqueta(s) encontrada(s).`);

    for (let i = 0; i < total; i++) {
      const et: Etiqueta = {
        id: ++contador.current,
        arquivo: origem,
        zpl,
        indice: i,
        campos: camposVazios(),
        nome: "",
        png: null,
        estado: "renderizando...",
        erro: false,
      };
      guardar([...atuais.current, et]);

      try {
        const png =
          i === 0
            ? primeira.blob
            : (await naFila(() => labelary(zpl, i, "image/png", c, log))).blob;
        mexer(et.id, {
          png: URL.createObjectURL(png),
          estado: c.ocr ? "lendo o nome..." : "pronta",
        });

        let campos = camposVazios();
        let estado = "pronta";
        let erro = false;
        if (c.ocr) {
          try {
            campos = await lerEtiqueta(png, log);
            estado = campos.nome
              ? "nome lido"
              : "não consegui ler o nome — digite";
            erro = !campos.nome;
          } catch (e) {
            estado = "OCR indisponível — digite o nome";
            erro = true;
            log(`  ⚠ OCR falhou: ${(e as Error).message}`);
          }
        }
        const nome = nomeArquivo({ ...et, campos }, c.padrao);
        mexer(et.id, { campos, estado, erro, nome });
        log(`  ${i + 1}/${total}: ${nome}.pdf`);
      } catch (e) {
        mexer(et.id, { estado: `erro: ${(e as Error).message}`, erro: true });
        log(`  ✗ etiqueta ${i + 1}: ${(e as Error).message}`);
      }
    }
    setOcupado(false);
  }

  async function receber(arquivos: File[]) {
    for (const f of arquivos) {
      const txt = await f.text();
      if (!/\^XA/i.test(txt)) {
        log(`✗ ${f.name}: não parece um arquivo ZPL (não achei ^XA).`);
        continue;
      }
      await processar(txt, f.name.replace(/\.[^.]+$/, ""));
    }
  }

  async function baixarUma(id: number) {
    const et = atuais.current.find((e) => e.id === id);
    if (!et) return;
    try {
      mexer(id, { estado: "gerando PDF..." });
      const res = await naFila(() =>
        labelary(et.zpl, et.indice, "application/pdf", cfgRef.current, log),
      );
      const nome = nomeUnico(
        et.nome || `etiqueta_${et.id}`,
        et.id,
        atuais.current,
      );
      await salvar(res.blob, `${nome}.pdf`, pasta, log);
      mexer(id, { nome, estado: `salva como ${nome}.pdf`, erro: false });
      log(`  ✓ ${nome}.pdf`);
    } catch (e) {
      mexer(id, {
        estado: `erro ao gerar PDF: ${(e as Error).message}`,
        erro: true,
      });
      log(`  ✗ ${(e as Error).message}`);
    }
  }

  const prontas = etiquetas.filter((e) => e.png);

  return (
    <>
      <PageHeader
        back={{ href: "/ferramentas", label: "Ferramentas" }}
        eyebrow="Ferramentas · expedição"
        title="Gerador de etiquetas"
        description="Envie o .txt com o ZPL do pedido e receba o PDF já nomeado pelo destinatário."
      />

      <div className="grid lg:grid-cols-[1fr_320px] gap-6 items-start">
        <div className="min-w-0">
          <div
            role="button"
            tabIndex={0}
            onClick={() => entrada.current?.click()}
            onKeyDown={(e) =>
              (e.key === "Enter" || e.key === " ") && entrada.current?.click()
            }
            onDragOver={(e) => {
              e.preventDefault();
              setArrastando(true);
            }}
            onDragLeave={() => setArrastando(false)}
            onDrop={(e) => {
              e.preventDefault();
              setArrastando(false);
              receber(Array.from(e.dataTransfer.files));
            }}
            className={`rounded-xl border-2 border-dashed p-10 text-center cursor-pointer transition-colors ${
              arrastando ? "border-primary bg-muted" : "border-input bg-card"
            }`}
          >
            <p className="font-semibold mb-1">
              Arraste o arquivo .txt do ZPL, ou toque para escolher
            </p>
            <p className="text-sm text-muted-foreground">
              aceita vários arquivos e várias etiquetas por arquivo
            </p>
          </div>
          <input
            ref={entrada}
            type="file"
            accept=".txt,text/plain"
            multiple
            hidden
            onChange={(e) => {
              receber(Array.from(e.target.files || []));
              e.target.value = "";
            }}
          />

          <div className="flex flex-wrap gap-2 mt-4">
            <Button variant="outline" onClick={() => setColando((v) => !v)}>
              Colar ZPL
            </Button>
            <Button
              variant="outline"
              disabled={!prontas.length}
              onClick={async () => {
                setOcupado(true);
                for (const et of atuais.current.filter((e) => e.png))
                  await baixarUma(et.id);
                log("Concluído.");
                setOcupado(false);
              }}
            >
              Baixar todas
            </Button>
            <Button
              variant="outline"
              disabled={!prontas.length}
              onClick={async () => {
                const et = atuais.current.find((e) => e.png);
                if (!et) return;
                try {
                  log("Gerando PDF único...");
                  const res = await naFila(() =>
                    labelary(
                      et.zpl,
                      null,
                      "application/pdf",
                      cfgRef.current,
                      log,
                    ),
                  );
                  await salvar(
                    res.blob,
                    `${slug(et.arquivo)}_todas.pdf`,
                    pasta,
                    log,
                  );
                  log(`  ✓ ${slug(et.arquivo)}_todas.pdf`);
                } catch (e) {
                  log(`  ✗ ${(e as Error).message}`);
                }
              }}
            >
              PDF único
            </Button>
            <Button
              variant="ghost"
              disabled={!etiquetas.length}
              onClick={() => {
                atuais.current.forEach(
                  (e) => e.png && URL.revokeObjectURL(e.png),
                );
                guardar([]);
                setRegistro("Lista limpa.");
              }}
            >
              Limpar
            </Button>
          </div>

          {colando && (
            <Card className="mt-4">
              <label htmlFor="zpl">Cole aqui o código ZPL</label>
              <textarea
                id="zpl"
                rows={6}
                spellCheck={false}
                className="font-mono text-xs"
                value={zplTexto}
                onChange={(e) => setZplTexto(e.target.value)}
              />
              <Button
                className="mt-3"
                disabled={!zplTexto.trim()}
                onClick={() => processar(zplTexto.trim(), "colado")}
              >
                Gerar a partir do texto
              </Button>
            </Card>
          )}

          <div className="grid sm:grid-cols-2 gap-4 mt-6">
            {etiquetas.map((et) => (
              <Card key={et.id} className="p-4">
                <div className="flex gap-4">
                  {et.png ? (
                    <img
                      src={et.png}
                      alt={`Etiqueta ${et.id}`}
                      onClick={() => setLupa(et.png)}
                      className="w-[104px] rounded cursor-zoom-in border"
                    />
                  ) : (
                    <div className="w-[104px] h-[156px] rounded bg-muted" />
                  )}
                  <div className="min-w-0">
                    <p className="font-semibold truncate">
                      {et.campos.nome || "(sem nome lido)"}
                    </p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {[
                        et.campos.cidade &&
                          `${et.campos.cidade}${et.campos.uf ? ` / ${et.campos.uf}` : ""}`,
                        et.campos.cep && `CEP ${et.campos.cep}`,
                        et.campos.pedido && `Pedido ${et.campos.pedido}`,
                        et.campos.rastreio,
                      ]
                        .filter(Boolean)
                        .map((t) => (
                          <span
                            key={t as string}
                            className="text-xs bg-muted rounded px-2 py-1"
                          >
                            {t as string}
                          </span>
                        ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-4">
                  <Input
                    value={et.nome}
                    spellCheck={false}
                    aria-label={`Nome do arquivo da etiqueta ${et.id}`}
                    onChange={(e) => mexer(et.id, { nome: e.target.value })}
                  />
                  <span className="text-sm text-muted-foreground">.pdf</span>
                </div>
                <div className="flex items-center justify-between gap-3 mt-3">
                  <span
                    className={`text-xs ${et.erro ? "text-destructive" : "text-muted-foreground"}`}
                  >
                    {et.estado}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!et.png}
                    onClick={() => baixarUma(et.id)}
                  >
                    Baixar PDF
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          <pre
            role="status"
            className="mt-6 text-xs bg-muted rounded-lg p-4 max-h-56 overflow-auto whitespace-pre-wrap"
          >
            {registro}
          </pre>
        </div>

        <Card>
          <h2>Ajustes</h2>
          <div className="grid gap-4">
            <div>
              <label htmlFor="tamanho">Tamanho da etiqueta</label>
              <select
                id="tamanho"
                value={cfg.tamanho}
                onChange={(e) => setCfg({ ...cfg, tamanho: e.target.value })}
              >
                <option value="4x6">4 × 6 pol (padrão Shopee)</option>
                <option value="4x4">4 × 4 pol</option>
                <option value="3x2">3 × 2 pol</option>
              </select>
            </div>
            <div>
              <label htmlFor="densidade">Densidade</label>
              <select
                id="densidade"
                value={cfg.dpmm}
                onChange={(e) => setCfg({ ...cfg, dpmm: e.target.value })}
              >
                <option value="8">203 dpi (8 dpmm)</option>
                <option value="12">300 dpi (12 dpmm)</option>
                <option value="6">152 dpi (6 dpmm)</option>
              </select>
            </div>
            <div>
              <label htmlFor="pagina">Página do PDF</label>
              <select
                id="pagina"
                value={cfg.pagina}
                onChange={(e) => setCfg({ ...cfg, pagina: e.target.value })}
              >
                <option value="">Do tamanho da etiqueta</option>
                <option value="A4">A4</option>
                <option value="Letter">Carta</option>
              </select>
            </div>
            <div>
              <label htmlFor="rotacao">Rotação</label>
              <select
                id="rotacao"
                value={cfg.rotacao}
                onChange={(e) => setCfg({ ...cfg, rotacao: e.target.value })}
              >
                <option value="0">Nenhuma</option>
                <option value="90">90°</option>
                <option value="180">180°</option>
                <option value="270">270°</option>
              </select>
            </div>
            <div>
              <label htmlFor="padrao">Nome do arquivo</label>
              <select
                id="padrao"
                value={cfg.padrao}
                onChange={(e) => {
                  const padrao = e.target.value as Padrao;
                  setCfg({ ...cfg, padrao });
                  guardar(
                    atuais.current.map((et) => ({
                      ...et,
                      nome: nomeArquivo(et, padrao),
                    })),
                  );
                }}
              >
                {padroes.map(([valor, rotulo]) => (
                  <option key={valor} value={valor}>
                    {rotulo}
                  </option>
                ))}
              </select>
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={cfg.ocr}
                onChange={(e) => setCfg({ ...cfg, ocr: e.target.checked })}
              />
              Ler o destinatário da etiqueta
            </label>
            {typeof window !== "undefined" && "showDirectoryPicker" in window ? (
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    const p = await (
                      window as unknown as {
                        showDirectoryPicker: (o: {
                          mode: string;
                        }) => Promise<FileSystemDirectoryHandle>;
                      }
                    ).showDirectoryPicker({ mode: "readwrite" });
                    setPasta(p);
                    log(`Os PDFs serão salvos em: ${p.name}`);
                  } catch (e) {
                    if ((e as Error).name !== "AbortError")
                      log("Escolha de pasta indisponível; os PDFs vão para Downloads.");
                  }
                }}
              >
                {pasta ? `Pasta: ${pasta.name}` : "Escolher pasta de destino"}
              </Button>
            ) : (
              <p className="text-sm text-muted-foreground">
                Neste navegador os PDFs caem na pasta de Downloads.
              </p>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            A etiqueta é desenhada pela API pública do Labelary (3 por segundo no
            plano grátis) e o nome sai por leitura da imagem — confira antes de
            imprimir.
          </p>
          {ocupado && (
            <p role="status" className="text-sm mt-3">
              Processando…
            </p>
          )}
        </Card>
      </div>

      {lupa && (
        <div
          role="dialog"
          aria-label="Etiqueta ampliada"
          onClick={() => setLupa(null)}
          className="fixed inset-0 bg-black/70 grid place-items-center p-6 z-50 cursor-zoom-out"
        >
          <img src={lupa} alt="Etiqueta ampliada" className="max-h-full rounded" />
        </div>
      )}
    </>
  );
}
