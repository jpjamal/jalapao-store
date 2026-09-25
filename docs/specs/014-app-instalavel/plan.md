# Plano

## Onde cada coisa fica

| Onde | O quê |
|---|---|
| `frontend/brand/logo-jalapao-colorido.png` | fonte do ícone (1254×1254, fundo creme) |
| `frontend/scripts/gerar-icones.mjs` (`npm run icons`) | gera `public/icons/`: 192, 512, maskable 512, apple-touch 180, favicon 48 — com `sharp`, que já vem com o Next |
| `frontend/src/app/manifest.ts` | manifesto pelo recurso nativo do Next (`MetadataRoute.Manifest`) |
| `frontend/src/app/layout.tsx` | ícones, `appleWebApp`, `themeColor` claro/escuro |
| `frontend/public/sw.js` | service worker: só a página sem conexão e o ícone dela |
| `frontend/public/offline.html` | página sem conexão, autocontida (CSS embutido) |
| `frontend/src/components/service-worker.tsx` | registro, só em produção, sem quebrar se falhar |

## Decisões
**basePath à mão.** O Next acrescenta `/jalapao-store` nos links que ele gera, mas não dentro
do manifesto nem nos caminhos de `public/` passados em `metadata.icons`. Esses caminhos usam a
constante `BASE` de `lib/api.ts`.

**Paleta nos PNGs.** Os ícones saem com paleta de cores (`palette: true`): 360 KB → 90 KB no de
512 px, sem diferença visível.

**Sem biblioteca de PWA.** Manifesto nativo do Next e um service worker de 30 linhas cobrem o
necessário; uma biblioteca traria cache de páginas, que aqui é indesejado.
