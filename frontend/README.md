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
- /estoque: entradas/saídas justificadas, valor e histórico.
- /entradas: compra/produção por produto, custo do lote, histórico e pagamento de compra.
  Cadastro sugere custo; usuário confirma o valor real. Compra só gera caixa ao pagar;
  produção nunca gera despesa automática. Ajustes positivos exigem custo explícito.
- /vendas: múltiplos itens, canal, descontos/taxas/frete, receber e cancelar.
- /caixa: entradas/saídas, origem automática/manual e histórico preservado.
- /ferramentas: índice das três ferramentas.
- /ferramentas/impressao-3d: custo da peça e botão de salvar no catálogo.
- /ferramentas/calculadora: taxas de Shopee e Mercado Livre, com a tabela de regras.
- /ferramentas/etiquetas: ZPL → Labelary → PDF nomeado pelo destinatário, com OCR.
- /callback: endereço futuro do Mercado Livre; integração ainda não ativada.

Todos os caminhos têm basePath /jalapao-store. Login protege tudo, ferramentas inclusive.
As contas ficam em `src/lib/ferramentas/`, portadas linha a linha do site anterior e sem
nenhuma alteração de fórmula: `custo3d.ts` (a mesma conta de apps/catalog/domain.py),
`marketplace.ts` (faixas da Shopee e médias do Mercado Livre) e `etiquetas.ts` (fila do
Labelary, recortes do OCR e regras de nome de arquivo). Os HTML originais seguem em ../site
só para consulta e rollback — não são mais servidos nem copiados por script. Os endereços
antigos (`/calculadora.html`, `/ferramentas/calculadora.html` e afins) redirecionam para as
páginas novas, em next.config.ts.

## Segurança e componentes
BFF valida Origin nas mutações, limita corpo e usa destinos de API permitidos. JWT em cookies
HttpOnly/Secure/SameSite=Lax, nunca em localStorage. Refresh com coalescência de concorrência
no processo Node; ao escalar para múltiplas réplicas, introduzir coordenação compartilhada.
Backend decide permissões. Front exibe erros 400/403 e envia 401 para login.
`components.json` documenta aliases shadcn; componentes em src/components/ui são fonte editável.
Tokens semânticos mantêm as cores, tipografias e modo escuro do sistema anterior.

Specs específicas em docs/specs; requisitos globais em ../docs/specs/001-platform.
