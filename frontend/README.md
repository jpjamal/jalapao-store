# Frontend Jalapão Store

Next.js 16 App Router, React 19, TypeScript, Tailwind 4 e componentes shadcn/ui adaptados
ao design Jalapão. `npm ci` instala as versões exatas de package-lock.json; `npm run build`
valida TypeScript. Node 24 LTS. Docker multi-stage com saída standalone e usuário não-root.

Desenvolvimento: definir BACKEND_URL=http://127.0.0.1:8000, APP_ORIGIN=http://localhost:3000,
COOKIE_SECURE=false; executar `npm run dev`. Abrir http://localhost:3000/jalapao-store.
Produção standalone: Dockerfile copia `.next/standalone`, `.next/static` e public.

## Telas
- /login: usuário e senha, erros recebidos da API.
- /: estoque a custo, faturamento, lucro estimado, caixa, a receber, produtos ativos.
- /produtos: busca, paginação, cadastro/edição, parâmetros 3D e desativação.
  O SKU aparece após salvar e não é editável; a quantidade é administrada no estoque.
- /anuncios: rascunho por produto e canal, em etapas (produto e canal, conteúdo, fotos,
  categoria). Salvar não publica. No Mercado Livre: validar (simula sem criar), publicar
  com confirmação e, depois de publicado, "Salvar e enviar" manda as alterações ao anúncio
  — specs 009, 011 e 012.
- /pesquisa-precos: pesquisa de mercado no Mercado Livre, só leitura — mais vendidos por
  categoria e busca no catálogo, com link para ver os preços no site (spec 013).
- /estoque: entradas/saídas justificadas, valor e histórico. Produto por busca digitada.
- /entradas: compra/produção por produto (busca digitada), custo do lote, histórico e
  pagamento de compra.
  Cadastro sugere custo; usuário confirma o valor real. Compra só gera caixa ao pagar;
  produção nunca gera despesa automática. Ajustes positivos exigem custo explícito.
- /vendas: múltiplos itens, canal, descontos/taxas/frete, receber e cancelar. Produto de
  cada item por busca digitada.
- /caixa: entradas/saídas, origem automática/manual e histórico preservado.
- /ferramentas: índice das três ferramentas.
- /ferramentas/impressao-3d: custo da peça e botão de salvar no catálogo, com SKU gerado pelo backend.
- /ferramentas/calculadora: taxas de Shopee e Mercado Livre, com a tabela de regras.
- /ferramentas/etiquetas: ZPL → Labelary → PDF nomeado pelo destinatário, com OCR.
- /integracoes: conectar Shopee e Mercado Livre, importar anúncios, vincular por SKU e
  ligar o envio de estoque por anúncio.
- /callback: retorno da autorização; troca o código por tokens assim que abre.

Todos os caminhos têm basePath /jalapao-store. Login protege tudo, ferramentas inclusive.
As contas ficam em `src/lib/ferramentas/`, portadas linha a linha do site anterior e sem
nenhuma alteração de fórmula: `custo3d.ts` (a mesma conta de apps/catalog/domain.py),
`marketplace.ts` (faixas da Shopee e médias do Mercado Livre) e `etiquetas.ts` (fila do
Labelary, recortes do OCR e regras de nome de arquivo). Os HTML originais seguem em ../site
só para consulta e rollback — não são mais servidos nem copiados por script. Os endereços
antigos (`/calculadora.html`, `/ferramentas/calculadora.html` e afins) redirecionam para as
páginas novas, em next.config.ts.

`components/product-picker.tsx` é o campo de produto com busca: filtra por nome ou SKU
ignorando acento, navega por teclado e impede envio com nome digitado sem seleção.
Usado em vendas, entradas e estoque — ver ../docs/specs/004-busca-de-produto.

## Layout e componentes de tela
Pensado para celular e computador (reorganização no commit 6563091):
- `components/shell.tsx`: menu lateral agrupado no computador; no celular, barra fina no topo
  com menu em gaveta (fecha com Esc, ao tocar fora e ao trocar de página).
- `components/page-header.tsx`: título, descrição, ações e link de volta, iguais em toda página.
- `components/form-actions.tsx` e `components/pagination.tsx`: botões de formulário e
  paginação padronizados — empilhados e com largura total no celular.
- Tabelas com `className="data-table"` viram cartões no celular: cada `<td>` leva
  `data-label` (nome da coluna), a célula que identifica a linha `data-role="title"` e a de
  botões `data-role="actions"`. O CSS está em `globals.css`.
- Alvos de toque de 44 px no celular e campos com 16 px (evita o zoom do iPhone).

## App instalável (PWA)
O sistema instala como app no Android e no iPhone ("Adicionar à tela inicial"), com o ícone
colorido da marca — spec 014.
- `src/app/manifest.ts`: manifesto servido em /jalapao-store/manifest.webmanifest.
- `public/icons/`: ícones gerados por `npm run icons` (`scripts/gerar-icones.mjs`) a partir de
  `brand/logo-jalapao-colorido.png`. Trocou o logo? Substitua o arquivo em `brand/` e rode de novo.
- `public/sw.js` + `components/service-worker.tsx`: service worker mínimo, registrado só em
  produção. Não guarda dados nem API — só a página `public/offline.html`, mostrada sem internet.
  Ao mudar essa página ou o ícone, trocar `VERSAO` em sw.js.
- Arquivos de public/ referenciados no manifesto e nos metadados levam o basePath à mão.

## Segurança e componentes
BFF valida Origin nas mutações, limita corpo e usa destinos de API permitidos. JWT em cookies
HttpOnly/Secure/SameSite=Lax, nunca em localStorage. Refresh com coalescência de concorrência
no processo Node; ao escalar para múltiplas réplicas, introduzir coordenação compartilhada.
Backend decide permissões. Front exibe erros 400/403 e envia 401 para login.
`components.json` documenta aliases shadcn; componentes em src/components/ui são fonte editável.
Tokens semânticos mantêm as cores, tipografias e modo escuro do sistema anterior.

Specs específicas em docs/specs; requisitos globais em ../docs/specs/001-platform.
