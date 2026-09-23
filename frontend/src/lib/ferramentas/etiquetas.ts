/* Gerador de etiquetas — ZPL → Labelary → PDF, com OCR para achar o destinatário.

   Porte literal de site/etiquetas.html: mesmos recortes, mesmos limiares, mesmas
   regras de nome de arquivo. O ZPL da Shopee é uma imagem (~DG/^XG) e não tem
   texto dentro, então o nome do destinatário só sai lendo a etiqueta renderizada. */

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

  // bloco do destinatário (abaixo da tarja DESTINATÁRIO, antes do remetente)
  const t1 = (await w.recognize(recortar(img, 0.02, 0.45, 0.575, 0.665, 3))).data
    .text;

  // faixa do topo: ID do pedido e código de rastreio
  const t2 = (await w.recognize(recortar(img, 0.02, 0.18, 0.99, 0.24, 3))).data
    .text;

  // o ID do pedido é curto e sem espaço: lê de novo só ele, ampliado e
  // com o alfabeto travado em maiúsculas + números (evita trocar J por I)
  let t3 = "";
  try {
    await w.setParameters({
      tessedit_char_whitelist: "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
      tessedit_pageseg_mode: "7",
    });
    t3 = (await w.recognize(recortar(img, 0.04, 0.203, 0.3, 0.232, 6, false)))
      .data.text;
  } catch {
    /* segue com a leitura da faixa larga */
  } finally {
    await w.setParameters({
      tessedit_char_whitelist: "",
      tessedit_pageseg_mode: "3",
    });
  }

  URL.revokeObjectURL(url);
  return interpretar(t1, t2, t3);
}

export function interpretar(
  textoDest: string,
  textoTopo: string,
  textoPedido: string,
): Campos {
  const linhas = (textoDest || "")
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s && !/destinat/i.test(s) && /[A-Za-zÀ-ÿ0-9]/.test(s));

  const campos = camposVazios();

  // nome = primeira linha com cara de nome (só letras, pelo menos duas palavras)
  for (const l of linhas) {
    const limpo = l
      .replace(/[^A-Za-zÀ-ÿ' .-]/g, "")
      .replace(/\s{2,}/g, " ")
      .trim();
    if (
      limpo.length >= 5 &&
      limpo.split(/\s+/).length >= 2 &&
      !/^(rua|av|avenida|travessa|alameda|rodovia|estrada|quadra|qd|lote|casa|apto|apt)\b/i.test(
        limpo,
      )
    ) {
      campos.nome = limpo;
      break;
    }
  }
  // o CEP ancora cidade (linha de cima) e estado (linha de baixo)
  const iCep = linhas.findIndex((l) => /^\d{5}-?\d{3}$/.test(l.replace(/\s/g, "")));
  if (iCep > 0) {
    campos.cep = linhas[iCep].replace(/\D/g, "");
    campos.cidade = linhas[iCep - 1] || "";
    campos.uf = linhas[iCep + 1] || "";
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

/* ---------- nome do arquivo ---------- */
export function slug(s: unknown): string {
  return String(s || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 70);
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
  if (padrao === "nome_cidade") base = [c.nome, c.cidade].filter(Boolean).join(" ");
  else if (padrao === "nome_uf") base = [c.nome, uf].filter(Boolean).join(" ");
  else if (padrao === "nome_cidade_uf")
    base = [c.nome, c.cidade, uf].filter(Boolean).join(" ");
  else if (padrao === "curto_cidade")
    base = [curto, c.cidade].filter(Boolean).join(" ");
  else if (padrao === "pedido") base = c.pedido;
  else if (padrao === "rastreio") base = c.rastreio;
  else if (padrao === "arquivo") base = `${et.arquivo} ${et.indice + 1}`;
  else base = c.nome;
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
