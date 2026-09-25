// Gera os ícones do app instalável (PWA) a partir do logo colorido da marca.
// Uso: npm run icons   — rode de novo sempre que o logo mudar; os PNGs vão para o git.
//
// Origem: brand/logo-jalapao-colorido.png (fonte, fora de public/: não é servida), cópia de
// "Jalapao Midia/logos_ate_1MB/logo_jalapao_store_colorido.png" (1254×1254, fundo creme).
//
// - "any": o logo quadrado inteiro, só redimensionado;
// - "maskable": o logo reduzido sobre o mesmo creme, para caber na zona segura (círculo de
//   80% do lado) — o Android recorta o ícone em círculo, gota ou quadrado conforme o aparelho;
// - apple-touch-icon: iPhone, sem transparência.
import sharp from "sharp";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const raiz = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const logo = path.join(raiz, "brand/logo-jalapao-colorido.png");
const saida = path.join(raiz, "public/icons");
const FUNDO = "#fdfae9"; // o creme do próprio logo: sem emenda entre logo e margem

async function icone(nome, lado, escala = 1) {
  const interno = Math.round(lado * escala);
  const marca = await sharp(logo).resize(interno, interno, { kernel: "lanczos3" }).png().toBuffer();
  await sharp({ create: { width: lado, height: lado, channels: 4, background: FUNDO } })
    .composite([{ input: marca, gravity: "center" }])
    .png({ compressionLevel: 9, palette: true, quality: 90 }) // paleta: ícone leve, cor igual
    .toFile(path.join(saida, nome));
  console.log(`  ${nome} (${lado}×${lado})`);
}

await mkdir(saida, { recursive: true });
await icone("icon-192.png", 192);
await icone("icon-512.png", 512);
await icone("icon-maskable-512.png", 512, 0.8);
await icone("apple-touch-icon.png", 180);
await icone("favicon-48.png", 48);
