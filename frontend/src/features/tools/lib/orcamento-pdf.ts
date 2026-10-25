/* PDF do orçamento (spec 036): desenhado direto no jsPDF, com texto de verdade (selecionável) e as
   imagens reduzidas. Recebe só o que o cliente vê: custo e margem nunca chegam até aqui. */

export type QuotePdfItem = {
  name: string;
  description: string;
  qty: number;
  unit: number;
  total: number;
  photoUrl?: string;
};

export type QuotePdfData = {
  client: string;
  contact: string;
  issued: Date;
  /** `null` quando o orçamento não tem validade */
  until: Date | null;
  lead: string;
  notes: string;
  discount: number;
  shipping: number;
  subtotal: number;
  total: number;
  instagram: string;
  logoUrl: string;
  items: QuotePdfItem[];
};

type Img = { data: string; w: number; h: number };

const brl = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const dateBr = (d: Date) => d.toLocaleDateString("pt-BR");

/** Baixa a imagem e a devolve como data URL (JPEG sobre fundo branco; PNG se `png`), já em tamanho de PDF. */
async function loadImage(url: string, png = false): Promise<Img | null> {
  try {
    const blob = await (await fetch(url)).blob();
    const objectUrl = URL.createObjectURL(blob);
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = reject;
      el.src = objectUrl;
    });
    URL.revokeObjectURL(objectUrl);
    const scale = Math.min(1, (png ? 300 : 400) / Math.max(img.naturalWidth, img.naturalHeight));
    const w = Math.max(1, Math.round(img.naturalWidth * scale));
    const h = Math.max(1, Math.round(img.naturalHeight * scale));
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    if (!png) {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, w, h);
    }
    ctx.drawImage(img, 0, 0, w, h);
    return { data: canvas.toDataURL(png ? "image/png" : "image/jpeg", 0.85), w, h };
  } catch {
    return null;
  }
}

export async function buildQuotePdf(d: QuotePdfData): Promise<Blob> {
  const { jsPDF } = await import("jspdf");
  const logo = await loadImage(d.logoUrl, true);
  const photos = await Promise.all(d.items.map((i) => (i.photoUrl ? loadImage(i.photoUrl) : Promise.resolve(null))));

  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const W = 210;
  const H = 297;
  const M = 15;
  const INK: [number, number, number] = [28, 25, 23];
  const GREY: [number, number, number] = [87, 83, 78];
  const LINE: [number, number, number] = [214, 211, 209];
  const colQty = 128;
  const colUnit = 160;
  const colTotal = W - M;
  let y = M;

  const text = (s: string, x: number, yy: number, opt: { size?: number; bold?: boolean; color?: [number, number, number]; align?: "left" | "right" | "center" } = {}) => {
    doc.setFont("helvetica", opt.bold ? "bold" : "normal");
    doc.setFontSize(opt.size ?? 10);
    doc.setTextColor(...(opt.color ?? INK));
    doc.text(s, x, yy, { align: opt.align ?? "left" });
  };
  const rule = (yy: number, width = 0.2, color = LINE) => {
    doc.setDrawColor(...color);
    doc.setLineWidth(width);
    doc.line(M, yy, W - M, yy);
  };
  const wrap = (s: string, width: number, size: number) => {
    doc.setFontSize(size);
    return doc.splitTextToSize(s, width) as string[];
  };
  const tableHead = () => {
    text("Produto", M, y, { bold: true });
    text("Qtd.", colQty, y, { bold: true, align: "right" });
    text("Valor unit.", colUnit, y, { bold: true, align: "right" });
    text("Total", colTotal, y, { bold: true, align: "right" });
    rule(y + 2, 0.5, INK);
    y += 8;
  };
  const ensure = (need: number, head = false) => {
    if (y + need > H - 20) {
      doc.addPage();
      y = M;
      if (head) tableHead();
    }
  };

  // cabeçalho: logo e dados da loja à esquerda, número do documento à direita
  let textX = M;
  if (logo) {
    const lh = 20;
    const lw = (logo.w / logo.h) * lh;
    doc.addImage(logo.data, "PNG", M, y, lw, lh);
    textX = M + lw + 4;
  }
  text("Jalapão Store", textX, y + 6, { size: 15, bold: true });
  text("Peças em impressão 3D", textX, y + 11.5, { size: 9, color: GREY });
  text(`Instagram ${d.instagram}`, textX, y + 16.5, { size: 9, color: GREY });
  text("ORÇAMENTO", W - M, y + 6, { size: 15, bold: true, align: "right" });
  text(`Emitido em ${dateBr(d.issued)}`, W - M, y + 11.5, { size: 9, color: GREY, align: "right" });
  if (d.until) text(`Válido até ${dateBr(d.until)}`, W - M, y + 16.5, { size: 9, color: GREY, align: "right" });
  y += 26;
  rule(y);
  y += 8;

  if (d.client || d.contact) {
    text("Para", M, y, { size: 9, color: GREY });
    y += 5;
    if (d.client) {
      text(d.client, M, y, { size: 11, bold: true });
      y += 5;
    }
    if (d.contact) {
      text(d.contact, M, y, { size: 10 });
      y += 5;
    }
    y += 4;
  }

  tableHead();
  d.items.forEach((item, i) => {
    const photo = photos[i];
    const box = 16;
    const textX2 = photo ? M + box + 4 : M;
    const nameLines = wrap(item.name, colQty - 18 - textX2, 10);
    const descLines = item.description ? wrap(item.description.slice(0, 140), colQty - 18 - textX2, 8).slice(0, 2) : [];
    const textH = nameLines.length * 4.6 + descLines.length * 3.6;
    const rowH = Math.max(photo ? box : 0, textH) + 5;
    ensure(rowH, true);
    if (photo) {
      const ratio = Math.min(box / photo.w, box / photo.h);
      const pw = photo.w * ratio;
      const ph = photo.h * ratio;
      doc.addImage(photo.data, "JPEG", M + (box - pw) / 2, y - 3 + (box - ph) / 2, pw, ph);
    }
    let ty = y + (photo ? Math.max(0, (box - textH) / 2) : 0);
    nameLines.forEach((line) => {
      text(line, textX2, ty, { size: 10, bold: true });
      ty += 4.6;
    });
    descLines.forEach((line) => {
      text(line, textX2, ty - 0.4, { size: 8, color: GREY });
      ty += 3.6;
    });
    text(String(item.qty), colQty, y, { align: "right" });
    text(brl(item.unit), colUnit, y, { align: "right" });
    text(brl(item.total), colTotal, y, { align: "right" });
    y += rowH - 2;
    rule(y);
    y += 5;
  });

  // totais
  ensure(32);
  y += 2;
  const line = (label: string, value: string, bold = false, size = 10) => {
    text(label, colUnit - 22, y, { size, bold });
    text(value, colTotal, y, { size, bold, align: "right" });
    y += size > 10 ? 7 : 5.5;
  };
  line("Subtotal", brl(d.subtotal));
  if (d.discount > 0) line("Desconto", `- ${brl(d.discount)}`);
  if (d.shipping > 0) line("Frete", brl(d.shipping));
  rule(y - 3, 0.5, INK);
  y += 2;
  line("Total", brl(d.total), true, 13);

  if (d.lead || d.notes) {
    y += 6;
    if (d.lead) {
      const lines = wrap(`Prazo de produção: ${d.lead}`, W - 2 * M, 10);
      ensure(lines.length * 5 + 4);
      lines.forEach((l) => {
        text(l, M, y, { size: 10 });
        y += 5;
      });
      y += 2;
    }
    if (d.notes) {
      const lines = wrap(`Observações: ${d.notes}`, W - 2 * M, 10);
      lines.forEach((l) => {
        ensure(6);
        text(l, M, y, { size: 10 });
        y += 5;
      });
    }
  }

  // rodapé e numeração em todas as páginas
  const pages = doc.getNumberOfPages();
  for (let p = 1; p <= pages; p++) {
    doc.setPage(p);
    text(`Jalapão Store · Instagram ${d.instagram} · Obrigado pela preferência!`, W / 2, H - 10, {
      size: 8,
      color: GREY,
      align: "center",
    });
    if (pages > 1) text(`Página ${p} de ${pages}`, W - M, H - 10, { size: 8, color: GREY, align: "right" });
  }
  return doc.output("blob");
}
