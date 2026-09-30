# Frontend Jalapão Store

Next.js 16 App Router, React 19, TypeScript, Tailwind 4 e componentes shadcn/ui adaptados
ao design Jalapão. `npm ci` instala as versões exatas de package-lock.json; `npm run build`
valida TypeScript. Node 24 LTS. Docker multi-stage com saída standalone e usuário não-root.

Desenvolvimento: definir BACKEND_URL=http://127.0.0.1:8000, APP_ORIGIN=http://localhost:3000,
COOKIE_SECURE=false; executar `npm run dev`. Abrir http://localhost:3000/jalapao-store.
Produção standalone: Dockerfile copia `.next/standalone`, `.next/static` e public.

## Estrutura (spec 017)
Organizado pelos mesmos contextos do backend — detalhes em ../docs/architecture.md.
- `src/app/`: só rotas. Cada `page.tsx` tem uma linha que reexporta a tela da feature.
- `src/features/<contexto>/`: `*-page.tsx` (tela), `components/`, `types.ts`, `api.ts` ou `lib/`.
  Contextos: auth, dashboard, catalog, listings, inventory, sales, finance, integrations, tools.
- `src/shared/`: `api/client.ts` (cliente do BFF), `api/types.ts`, `ui/` (shadcn),
  `components/` (page-header, form-actions, pagination, fields, feedback), `layout/shell.tsx`,
  `lib/format.ts` e `lib/utils.ts`, `pwa/service-worker.tsx`.
- Regra: feature usa `shared/` e o que outra feature exporta; `shared/` não importa de features.

## Telas
- /login: usuário e senha, erros recebidos da API.
- /: estoque a custo, faturamento, lucro estimado, caixa, a receber, produtos ativos.
- /produtos: busca, paginação, cadastro/edição, parâmetros 3D e desativação.
  O SKU aparece após salvar e não é editável; a quantidade é administrada no estoque.
  Código de barras (GTIN/EAN) opcional, validado pelo backend; a busca e o campo de produto
  também encontram por ele (spec 021). Categoria no lugar do tipo, mais marca, modelo e peso
  (spec 022): a categoria de impressão 3D mostra os parâmetros de custo.
- /categorias: lista e cadastro de categorias; ativar/desativar, sem apagar (spec 022).
- /anuncios: rascunho por produto e canal, em etapas (produto e canal, conteúdo, fotos,
  categoria). Salvar não publica. No Mercado Livre: validar (simula sem criar), publicar
  com confirmação e, depois de publicado, "Salvar e enviar" manda as alterações ao anúncio
  — specs 009, 011 e 012.
- /pesquisa-precos: pesquisa de mercado no Mercado Livre, só leitura — mais vendidos por
  categoria e busca no catálogo, com link para ver os preços no site (spec 013).
- /estoque: entradas/saídas justificadas, valor e histórico. Produto por busca digitada.
- /entradas: compra/produção por produto (busca digitada), custo do lote, histórico e
  pagamento de compra e cancelamento de entrada lançada errada (o registro fica como
  cancelado, spec 023).
  Cadastro sugere custo; usuário confirma o valor real. Compra só gera caixa ao pagar;
  produção nunca gera despesa automática. Ajustes positivos exigem custo explícito.
- /vendas: seção opcional *Insumos usados* (baixa no saldo de insumos junto com a venda, com aviso do
  que faltou; spec 024), múltiplos itens, canal (boca a boca, Site Jalapão, Mercado Livre, Shopee, outro),
  descontos/taxas/frete, receber e cancelar. Produto de cada item por busca digitada.
  "Importar do Mercado Livre" traz os pedidos pagos com taxa e frete reais, em prévia, e
  cria as vendas só quando o dono manda (spec 015).
- /caixa: entradas/saídas, origem automática/manual e histórico preservado.
- /ferramentas: índice das três ferramentas.
- /ferramentas/impressao-3d: custo da peça e botão de salvar no catálogo, com SKU gerado pelo backend.
  Aceita peça multicolor: linhas de filamento cadastrado com as gramas de cada um (spec 024).
- /insumos: cadastro de insumos (filamento, embalagens, etiquetas, colas, ferramentas) com filtro por
  categoria e painel para gerenciar as categorias de insumo. Duas abas: *Cadastro e estoque* (saldo e as
  ações Comprar, Dar baixa, Ajustar, Editar) e *Compras e movimentos* (Pagar, Cancelar e o razão do
  saldo).
- /ferramentas/calculadora: taxas de Shopee e Mercado Livre, com a tabela de regras.
- /ferramentas/etiquetas: ZPL → Labelary → PDF nomeado pelo destinatário, com OCR.
- /integracoes: conectar Shopee e Mercado Livre, importar anúncios, vincular por SKU e
  ligar o envio de estoque por anúncio.
- /callback: retorno da autorização; troca o código por tokens assim que abre.

Todos os caminhos têm basePath /jalapao-store. Login protege tudo, ferramentas inclusive.
As contas ficam em `src/features/tools/lib/`, portadas linha a linha do site anterior e sem
nenhuma alteração de fórmula: `custo3d.ts` (a mesma conta de apps/catalog/domain/pricing.py),
`marketplace.ts` (faixas da Shopee e médias do Mercado Livre) e `etiquetas.ts` (fila do
Labelary, recortes do OCR e regras de nome de arquivo). Os HTML originais seguem em ../site
só para consulta e rollback — não são mais servidos nem copiados por script. Os endereços
antigos (`/calculadora.html`, `/ferramentas/calculadora.html` e afins) redirecionam para as
páginas novas, em next.config.ts.

`features/catalog/components/product-picker.tsx` é o campo de produto com busca: filtra por nome ou SKU
ignorando acento, navega por teclado e impede envio com nome digitado sem seleção.
Usado em vendas, entradas e estoque — ver ../docs/specs/004-busca-de-produto.

## Layout e componentes de tela
Pensado para celular e computador (reorganização no commit 6563091):
- `shared/layout/shell.tsx`: menu lateral agrupado no computador; no celular, barra fina no topo
  com menu em gaveta (fecha com Esc, ao tocar fora e ao trocar de página).
- `shared/components/page-header.tsx`: título, descrição, ações e link de volta, iguais em toda página.
- `shared/components/form-actions.tsx` e `shared/components/pagination.tsx`: botões de formulário e
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
- `public/sw.js` + `shared/pwa/service-worker.tsx`: service worker mínimo, registrado só em
  produção. Não guarda dados nem API — só a página `public/offline.html`, mostrada sem internet.
  Ao mudar essa página ou o ícone, trocar `VERSAO` em sw.js.
- Arquivos de public/ referenciados no manifesto e nos metadados levam o basePath à mão.

## Segurança e componentes
BFF valida Origin nas mutações, limita corpo e usa destinos de API permitidos. JWT em cookies
HttpOnly/Secure/SameSite=Lax, nunca em localStorage. Refresh com coalescência de concorrência
no processo Node; ao escalar para múltiplas réplicas, introduzir coordenação compartilhada.
Backend decide permissões. Front exibe erros 400/403 e envia 401 para login.
`components.json` documenta aliases shadcn; componentes em src/shared/ui são fonte editável.
Tokens semânticos mantêm as cores, tipografias e modo escuro do sistema anterior.

Todas as specs ficam em ../docs/specs (uma pasta por mudança); critérios gerais da interface
em ../docs/specs/001-platform e ../docs/specs/002-stock-cost.
