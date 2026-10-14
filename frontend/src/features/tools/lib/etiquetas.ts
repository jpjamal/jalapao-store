/* Gerador de etiquetas — ZPL → Labelary → PDF, com OCR para achar o destinatário.

   O ZPL da Shopee costuma ser uma imagem (~DG/^XG), sem nome em texto. A leitura
   compara regiões diferentes da etiqueta e escolhe o conjunto mais coerente de
   destinatário, CEP, cidade e UF; isso evita usar o remetente quando o layout muda. */

const API = "https://api.labelary.com/v1/printers";

export type Config = {
  tamanho: string;
  dpmm: string;
  pagina: string;
  rotacao: string;
  padrao: Padrao;
  ocr: boolean;
};

export type Padrao =
  | "nome"
  | "nome_cidade"
  | "nome_uf"
  | "nome_cidade_uf"
  | "curto_cidade"
  | "pedido"
  | "rastreio"
  | "arquivo";

export type Campos = {
  nome: string;
  cidade: string;
  uf: string;
  cep: string;
  pedido: string;
  rastreio: string;
};

export type Etiqueta = {
  id: number;
  arquivo: string;
  zpl: string;
  indice: number;
  campos: Campos;
  nome: string;
  png: string | null;
  estado: string;
  erro: boolean;
};

export const camposVazios = (): Campos => ({
  nome: "",
  cidade: "",
  uf: "",
  cep: "",
  pedido: "",
  rastreio: "",
});

export const sleep = (ms: number) =>
  new Promise<void>((r) => setTimeout(r, ms));

/* ---------- fila de requisições (respeita 3 req/s do plano grátis) ---------- */
type Job = {
  fn: () => Promise<unknown>;
  ok: (v: never) => void;
  erro: (e: unknown) => void;
};
const fila: Job[] = [];
let rodando = false;

export function naFila<T>(fn: () => Promise<T>): Promise<T> {
  return new Promise<T>((ok, erro) => {
    fila.push({ fn, ok: ok as Job["ok"], erro });
    puxar();
  });
}

async function puxar() {
  if (rodando || !fila.length) return;
  rodando = true;
  while (fila.length) {
    const job = fila.shift()!;
    try {
      job.ok((await job.fn()) as never);
    } catch (e) {
      job.erro(e);
    }
    await sleep(360);
  }
  rodando = false;
}

/* ---------- chamada ao Labelary ---------- */
export async function labelary(
  zpl: string,
  indice: number | null,
  accept: string,
  c: Config,
  aoAvisar?: (texto: string) => void,
  tentativa = 0,
): Promise<{ blob: Blob; total: number }> {
  const headers: Record<string, string> = {
    "Content-Type": "application/x-www-form-urlencoded",
    Accept: accept,
  };
  if (c.rotacao !== "0") headers["X-Rotation"] = c.rotacao;
  if (c.pagina && accept === "application/pdf")
    headers["X-Page-Size"] = c.pagina;

  const url = `${API}/${c.dpmm}dpmm/labels/${c.tamanho}/${indice === null ? "" : `${indice}/`}`;
  const r = await fetch(url, { method: "POST", headers, body: zpl });

  if (r.status === 429 && tentativa < 4) {
    const espera =
      (parseInt(r.headers.get("Retry-After") || "2", 10) + 1) * 1000;
    aoAvisar?.(`Limite da API atingido, aguardando ${espera / 1000}s...`);
    await sleep(espera);
    return labelary(zpl, indice, accept, c, aoAvisar, tentativa + 1);
  }
  if (!r.ok) {
    const msg = (await r.text()).slice(0, 300) || `HTTP ${r.status}`;
    throw new Error(msg);
  }
  return {
    blob: await r.blob(),
    total: parseInt(r.headers.get("X-Total-Count") || "1", 10),
  };
}

/* ---------- OCR ---------- */
type Worker = {
  recognize: (
    img: HTMLCanvasElement,
  ) => Promise<{ data: { text: string } }>;
  setParameters: (p: Record<string, string>) => Promise<unknown>;
};
type TesseractApi = {
  createWorker: (
    lang: string,
    oem: number,
    opc: Record<string, unknown>,
  ) => Promise<Worker>;
};
declare global {
  interface Window {
    Tesseract?: TesseractApi;
  }
}

let workerOCR: Worker | null = null;

const TESSERACT_CDN =
  "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js";

function carregarScript(src: string) {
  return new Promise<void>((ok, err) => {
    if (document.querySelector(`script[src="${src}"]`)) return ok();
    const s = document.createElement("script");
    s.src = src;
    s.onload = () => ok();
    s.onerror = () => err(new Error("não consegui baixar o motor de OCR"));
    document.head.appendChild(s);
  });
}

export async function pegarWorker(aoAvisar?: (t: string) => void) {
  if (workerOCR) return workerOCR;
  if (!window.Tesseract) {
    aoAvisar?.("  baixando motor de OCR (só na primeira vez)...");
    await carregarScript(TESSERACT_CDN);
  }
  const tesseract = window.Tesseract;
  if (!tesseract)
    throw new Error("biblioteca de OCR não carregou (sem internet?)");
  workerOCR = await tesseract.createWorker("por", 1, {});
  return workerOCR;
}

// recorta um pedaço da etiqueta (frações 0..1), amplia e binariza para o OCR
export function recortar(
  img: HTMLImageElement,
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  escala: number,
  binarizar = true,
): HTMLCanvasElement {
  const cv = document.createElement("canvas");
  const lx = Math.round(img.width * (x1 - x0));
  const ly = Math.round(img.height * (y1 - y0));
  cv.width = lx * escala;
  cv.height = ly * escala;
  const ct = cv.getContext("2d")!;
  ct.imageSmoothingEnabled = true;
  ct.imageSmoothingQuality = "high";
  ct.fillStyle = "#fff";
  ct.fillRect(0, 0, cv.width, cv.height);
  ct.drawImage(
    img,
    Math.round(img.width * x0),
    Math.round(img.height * y0),
    lx,
    ly,
    0,
    0,
    cv.width,
    cv.height,
  );
  if (binarizar) {
    const d = ct.getImageData(0, 0, cv.width, cv.height);
    for (let p = 0; p < d.data.length; p += 4) {
      const v = d.data[p] < 140 ? 0 : 255;
      d.data[p] = d.data[p + 1] = d.data[p + 2] = v;
    }
    ct.putImageData(d, 0, 0);
  }
  return cv;
}

export async function lerEtiqueta(
  pngBlob: Blob,
  aoAvisar?: (t: string) => void,
): Promise<Campos> {
  const w = await pegarWorker(aoAvisar);
  const url = URL.createObjectURL(pngBlob);
  const img = await new Promise<HTMLImageElement>((ok, err) => {
    const i = new Image();
    i.onload = () => ok(i);
    i.onerror = () => err(new Error("preview inválido"));
    i.src = url;
  });

  try {
    // Primeiro tenta o recorte histórico, que é rápido e preciso no layout conhecido.
    const destinos = [
      (await w.recognize(recortar(img, 0.02, 0.45, 0.575, 0.665, 3))).data.text,
    ];
    aoAvisar?.("  conferindo nome, cidade e CEP...");
    destinos.push(
      (await w.recognize(recortar(img, 0, 0.39, 0.7, 0.76, 3))).data.text,
    );
    const leituras = destinos.map(candidatoDestino);
    const nomes = new Set(leituras.map((item) => item.campos.nome).filter(Boolean));
    const ceps = new Set(leituras.map((item) => item.campos.cep).filter(Boolean));
    if (Math.max(...leituras.map((item) => item.pontos)) < 10 || nomes.size > 1 || ceps.size > 1) {
      destinos.push(
        (await w.recognize(recortar(img, 0, 0.3, 1, 0.84, 2))).data.text,
      );
    }

    // Faixa do topo: ID do pedido e código de rastreio.
    const topo = (await w.recognize(recortar(img, 0.02, 0.17, 0.99, 0.25, 3))).data
      .text;
    let pedido = "";
    try {
      await w.setParameters({
        tessedit_char_whitelist: "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        tessedit_pageseg_mode: "7",
      });
      pedido = (
        await w.recognize(recortar(img, 0.025, 0.195, 0.36, 0.238, 6, false))
      ).data.text;
    } catch {
      /* a faixa larga ainda pode fornecer o número */
    } finally {
      await w.setParameters({
        tessedit_char_whitelist: "",
        tessedit_pageseg_mode: "3",
      });
    }
    return interpretar(destinos, topo, pedido);
  } finally {
    URL.revokeObjectURL(url);
  }
}

type Candidato = { campos: Campos; pontos: number; cep: string };

const PREFIXO_ENDERECO =
  /^(rua|r\.?|av\.?|avenida|travessa|alameda|rodovia|estrada|quadra|qd\.?|lote|casa|apto|apt\.?|bloco|bairro|complemento)\b/i;
const ROTULO =
  /^(destinat[aá]rio|remetente|nome|endere[cç]o|cidade|munic[ií]pio|estado|uf|cep|pedido|n[uú]mero do pedido|rastreio)\s*:?\s*$/i;

function limparLinha(valor: string): string {
  return valor.replace(/[|_]+/g, " ").replace(/\s{2,}/g, " ").trim();
}

function linhasDoDestinatario(texto: string): { linhas: string[]; ancorado: boolean } {
  let linhas = String(texto || "")
    .split(/\r?\n/)
    .map(limparLinha)
    .filter((linha) => linha && /[A-Za-zÀ-ÿ0-9]/.test(linha));
  const inicio = linhas.findIndex((linha) => /destinat/i.test(linha));
  if (inicio >= 0) linhas = linhas.slice(inicio + 1);
  const fim = linhas.findIndex((linha) => /remetente/i.test(linha));
  if (fim >= 0) linhas = linhas.slice(0, fim);
  return { linhas: linhas.filter((linha) => !ROTULO.test(linha)), ancorado: inicio >= 0 };
}

function cepDaLinha(linha: string): string {
  const numerica = linha.toUpperCase().replace(/[OQ]/g, "0");
  const achado = numerica.match(/\b(\d{5})\s*[-.]?\s*(\d{3})\b/);
  return achado ? `${achado[1]}${achado[2]}` : "";
}

function retirarCep(linha: string): string {
  return linha.replace(/\b[0-9OQ]{5}\s*[-.]?\s*[0-9OQ]{3}\b/gi, " ");
}

function ufDaLinha(linha: string): string {
  const limpa = linha.replace(/\b\d{5}\s*[-.]?\s*\d{3}\b/g, " ").trim();
  const siglaDireta = limpa.match(/(?:^|[\s/\-])([A-Z]{2})(?:$|[\s/\-])/);
  if (siglaDireta && Object.values(UF).includes(siglaDireta[1])) return siglaDireta[1];
  const chave = slug(limpa.replace(/^(estado|uf)\s*:?\s*/i, "")).replace(/_/g, " ");
  return UF[chave] || "";
}

function textoSemRotulo(linha: string): string {
  return limparLinha(linha.replace(/^(nome|cidade|munic[ií]pio|estado|uf|cep)\s*:?\s*/i, ""));
}

function pareceNome(linha: string): boolean {
  const valor = textoSemRotulo(linha)
    .replace(/[^A-Za-zÀ-ÿ' .-]/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
  return (
    valor.length >= 5 &&
    valor.split(/\s+/).length >= 2 &&
    !PREFIXO_ENDERECO.test(valor) &&
    !/(destinat|remetente|declara[cç][aã]o|conte[uú]do|transportadora|shopee|correios|entrega|frete|pacote)/i.test(valor)
  );
}

function candidatoDestino(texto: string): Candidato {
  const { linhas, ancorado } = linhasDoDestinatario(texto);
  const campos = camposVazios();
  const iCep = linhas.findIndex((linha) => cepDaLinha(linha));
  if (iCep >= 0) campos.cep = cepDaLinha(linhas[iCep]);

  if (iCep >= 0) {
    const mesmaLinha = textoSemRotulo(
      retirarCep(linhas[iCep]),
    );
    campos.uf = ufDaLinha(mesmaLinha);
    const cidadeMesmaLinha = mesmaLinha
      .replace(new RegExp(`(?:[/\\-]\\s*)?${campos.uf}$`, "i"), "")
      .trim();
    if (cidadeMesmaLinha && !PREFIXO_ENDERECO.test(cidadeMesmaLinha)) campos.cidade = cidadeMesmaLinha;

    for (const indice of [iCep - 1, iCep + 1, iCep - 2, iCep + 2]) {
      if (indice < 0 || indice >= linhas.length) continue;
      const original = linhas[indice];
      const linha = textoSemRotulo(original);
      if (!campos.cidade && /^(cidade|munic[ií]pio)\s*:/i.test(original)) campos.cidade = linha;
      if (!campos.uf) campos.uf = ufDaLinha(linha);
      if (
        !campos.cidade &&
        linha &&
        !ufDaLinha(linha) &&
        !PREFIXO_ENDERECO.test(linha) &&
        !/\d/.test(linha) &&
        !pareceNome(linha)
      )
        campos.cidade = linha;
    }
    // No layout conhecido, a cidade fica imediatamente acima do CEP, mesmo com duas palavras.
    const acima = textoSemRotulo(linhas[iCep - 1] || "");
    if (acima && !PREFIXO_ENDERECO.test(acima) && !/\d/.test(acima) && !ufDaLinha(acima))
      campos.cidade = acima;
    if (ufDaLinha(acima)) {
      const acimaDoEstado = textoSemRotulo(linhas[iCep - 2] || "");
      if (acimaDoEstado && !PREFIXO_ENDERECO.test(acimaDoEstado) && !/\d/.test(acimaDoEstado))
        campos.cidade = acimaDoEstado;
    }
    const abaixo = textoSemRotulo(linhas[iCep + 1] || "");
    if (!campos.cidade && abaixo && !PREFIXO_ENDERECO.test(abaixo) && !/\d/.test(abaixo)) {
      const depois = textoSemRotulo(linhas[iCep + 2] || "");
      if (ufDaLinha(depois) || /^(cidade|munic[ií]pio)\s*:/i.test(linhas[iCep + 1] || ""))
        campos.cidade = abaixo;
    }
  }

  const limiteNome = iCep >= 0 ? iCep : linhas.length;
  for (let indice = 0; indice < limiteNome; indice++) {
    const linha = linhas[indice];
    if (linha === campos.cidade || cepDaLinha(linha) || ufDaLinha(linha) || !pareceNome(linha)) continue;
    campos.nome = textoSemRotulo(linha)
      .replace(/[^A-Za-zÀ-ÿ' .-]/g, "")
      .replace(/\s{2,}/g, " ")
      .trim();
    break;
  }

  const pontos = pontuarCampos(campos) + (ancorado ? 3 : 0);
  return { campos, pontos, cep: campos.cep };
}

export function pontuarCampos(campos: Campos): number {
  return (campos.nome ? 5 : 0) + (campos.cep ? 4 : 0) + (campos.cidade ? 3 : 0) + (campos.uf ? 2 : 0);
}

export function interpretar(
  textoDest: string | string[],
  textoTopo: string,
  textoPedido: string,
): Campos {
  const candidatos = (Array.isArray(textoDest) ? textoDest : [textoDest])
    .map(candidatoDestino)
    .sort((a, b) => b.pontos - a.pontos);
  const campos = candidatos[0]?.campos || camposVazios();
  // Completa lacunas somente com uma leitura do mesmo CEP; evita misturar remetente e destinatário.
  for (const candidato of candidatos.slice(1)) {
    if (campos.cep && candidato.cep && candidato.cep !== campos.cep) continue;
    for (const campo of ["nome", "cidade", "uf", "cep"] as const)
      if (!campos[campo] && candidato.campos[campo]) campos[campo] = candidato.campos[campo];
  }
  const topo = (textoTopo || "").replace(/\s+/g, " ");
  const r = topo.match(/\b[A-Z]{2}\s?\d{9}\s?[A-Z]{2}\b/);
  if (r) campos.rastreio = r[0].replace(/\s/g, "");
  const p = topo.match(/\b\d{7}[A-Z0-9]{5,10}\b/);
  if (p) campos.pedido = p[0];

  // leitura dedicada do ID do pedido tem prioridade sobre a da faixa larga
  const so = String(textoPedido || "")
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "");
  const p2 = so.match(/\d{7}[A-Z0-9]{5,10}/);
  if (p2) campos.pedido = p2[0];
  return campos;
}

export function extrairPedidoZpl(zpl: string): string {
  const camposTexto = Array.from(
    String(zpl || "").toUpperCase().matchAll(/\^FD([^\^]{1,250})\^FS/g),
    (achado) => achado[1],
  ).join(" ");
  const candidatos = camposTexto.match(/\b\d{7}[A-Z0-9]{5,10}\b/g) || [];
  return candidatos[0] || "";
}

/* ---------- nome do arquivo ---------- */
export function slug(s: unknown): string {
  return String(s || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 120);
}

// estado por extenso na etiqueta -> sigla no nome do arquivo
const UF: Record<string, string> = {
  acre: "AC",
  alagoas: "AL",
  amapa: "AP",
  amazonas: "AM",
  bahia: "BA",
  ceara: "CE",
  "distrito federal": "DF",
  "espirito santo": "ES",
  goias: "GO",
  maranhao: "MA",
  "mato grosso": "MT",
  "mato grosso do sul": "MS",
  "minas gerais": "MG",
  para: "PA",
  paraiba: "PB",
  parana: "PR",
  pernambuco: "PE",
  piaui: "PI",
  "rio de janeiro": "RJ",
  "rio grande do norte": "RN",
  "rio grande do sul": "RS",
  rondonia: "RO",
  roraima: "RR",
  "santa catarina": "SC",
  "sao paulo": "SP",
  sergipe: "SE",
  tocantins: "TO",
};

export function sigla(estado: string): string {
  const chave = slug(estado).replace(/_/g, " ");
  if (UF[chave]) return UF[chave];
  const s = String(estado || "").trim();
  return s.length === 2 ? s.toUpperCase() : s; // já veio como sigla, ou não reconheci
}

export function nomeArquivo(
  et: Pick<Etiqueta, "campos" | "arquivo" | "indice" | "id">,
  padrao: Padrao,
): string {
  const c = et.campos || camposVazios();
  const partes = String(c.nome || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  const curto =
    partes.length > 1 ? `${partes[0]} ${partes[partes.length - 1]}` : c.nome || "";
  const uf = sigla(c.uf);
  let base = "";
  if (padrao === "nome_cidade") base = [c.pedido, c.nome, c.cidade].filter(Boolean).join(" ");
  else if (padrao === "nome_uf") base = [c.pedido, c.nome, uf].filter(Boolean).join(" ");
  else if (padrao === "nome_cidade_uf")
    base = [c.pedido, c.nome, c.cidade, uf].filter(Boolean).join(" ");
  else if (padrao === "curto_cidade")
    base = [c.pedido, curto, c.cidade].filter(Boolean).join(" ");
  else if (padrao === "pedido") base = c.pedido;
  else if (padrao === "rastreio") base = [c.pedido, c.rastreio].filter(Boolean).join(" ");
  else if (padrao === "arquivo") base = [c.pedido, et.arquivo, et.indice + 1].filter(Boolean).join(" ");
  else base = [c.pedido, c.nome].filter(Boolean).join(" ");
  return (
    slug(base) || slug(`${et.arquivo}_${et.indice + 1}`) || `etiqueta_${et.id}`
  );
}

export function nomeUnico(
  nome: string,
  id: number,
  etiquetas: Etiqueta[],
): string {
  let n = nome;
  let i = 2;
  while (etiquetas.some((e) => e.id !== id && e.nome === n)) n = `${nome}_${i++}`;
  return n;
}

/* ---------- salvar ---------- */
export async function salvar(
  blob: Blob,
  nome: string,
  pasta: FileSystemDirectoryHandle | null,
  aoAvisar?: (t: string) => void,
) {
  if (pasta) {
    try {
      const fh = await pasta.getFileHandle(nome, { create: true });
      const w = await fh.createWritable();
      await w.write(blob);
      await w.close();
      return;
    } catch (e) {
      aoAvisar?.(
        `  ⚠ não deu para salvar na pasta (${(e as Error).message}), baixando normal.`,
      );
    }
  }
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = nome;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 20000);
  await sleep(250);
}
