import {
  camposVazios,
  extrairPedidoZpl,
  labelary,
  lerEtiqueta,
  naFila,
  nomeArquivo,
  salvar,
  type Campos,
  type Config,
} from "@/features/tools/lib/etiquetas";

export const SALE_LABEL_CONFIG: Config = {
  tamanho: "4x6",
  dpmm: "8",
  pagina: "",
  rotacao: "0",
  padrao: "nome_cidade_uf",
  ocr: true,
};

export type SaleLabelDraft = {
  zpl: string;
  source_name: string;
  campos: Campos;
};

export const emptySaleLabel = (): SaleLabelDraft => ({
  zpl: "",
  source_name: "",
  campos: camposVazios(),
});

export function validarZpl(zpl: string): string {
  if (!zpl.trim()) return "Adicione o código ZPL ou escolha um arquivo .txt.";
  if (zpl.length > 5_000_000) return "O arquivo ultrapassa o limite de 5 MB.";
  const upper = zpl.toUpperCase();
  if (!upper.includes("^XA") || !upper.includes("^XZ"))
    return "O conteúdo não parece uma etiqueta ZPL completa (^XA ... ^XZ).";
  return "";
}

export async function lerZplVenda(
  zpl: string,
  aoAvisar?: (texto: string) => void,
): Promise<Campos> {
  const erro = validarZpl(zpl);
  if (erro) throw new Error(erro);
  const renderizada = await naFila(() =>
    labelary(zpl, 0, "image/png", SALE_LABEL_CONFIG, aoAvisar),
  );
  const campos = await lerEtiqueta(renderizada.blob, aoAvisar);
  campos.pedido ||= extrairPedidoZpl(zpl);
  return campos;
}

export async function gerarPdfVenda(
  draft: SaleLabelDraft,
  aoAvisar?: (texto: string) => void,
): Promise<{ blob: Blob; filename: string; campos: Campos }> {
  const erro = validarZpl(draft.zpl);
  if (erro) throw new Error(erro);
  let campos = draft.campos;
  if (!campos.nome || !campos.cidade || !campos.pedido)
    campos = await lerZplVenda(draft.zpl, aoAvisar);
  campos.pedido ||= extrairPedidoZpl(draft.zpl);
  const pdf = await naFila(() =>
    labelary(draft.zpl, null, "application/pdf", SALE_LABEL_CONFIG, aoAvisar),
  );
  const base = nomeArquivo(
    {
      campos,
      arquivo: draft.source_name.replace(/\.[^.]+$/, "") || "etiqueta",
      indice: 0,
      id: 1,
    },
    SALE_LABEL_CONFIG.padrao,
  );
  return { blob: pdf.blob, filename: `${base}.pdf`, campos };
}

export async function baixarPdfVenda(
  draft: SaleLabelDraft,
  aoAvisar?: (texto: string) => void,
) {
  const pdf = await gerarPdfVenda(draft, aoAvisar);
  await salvar(pdf.blob, pdf.filename, null, aoAvisar);
  return pdf.campos;
}

export async function abrirPdfVenda(
  draft: SaleLabelDraft,
  janela: Window | null,
  aoAvisar?: (texto: string) => void,
) {
  if (!janela) throw new Error("O navegador bloqueou a nova aba. Permita pop-ups para imprimir.");
  try {
    const pdf = await gerarPdfVenda(draft, aoAvisar);
    const url = URL.createObjectURL(pdf.blob);
    janela.location.href = url;
    setTimeout(() => URL.revokeObjectURL(url), 120_000);
    return pdf.campos;
  } catch (error) {
    janela.close();
    throw error;
  }
}
