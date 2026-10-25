# Plano

Página `frontend/src/features/tools/quote-page.tsx` (rota `app/(store)/ferramentas/orcamento`), cartão novo
em `tools-page.tsx`. Os produtos vêm de `products` (páginas de 100, filtrando `printing != null`), a foto de
`product-images?product=`. O cálculo é feito no navegador (`priceFrom`, em centavos). O documento é um
`<div id="orcamento-doc">` com estilos inline (fundo branco, independe do tema); a impressão copia o HTML e
as folhas de estilo para uma aba nova e espera as imagens antes de chamar `print()`.

O download usa o jsPDF (dependência nova, carregada sob demanda): `lib/orcamento-pdf.ts` desenha o PDF em A4
com texto vetorial; logo e fotos são baixados, reduzidos num canvas e embutidos. Recebe só os dados que o cliente
vê, então custo e margem não chegam a ele.
