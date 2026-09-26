# 001 — Gestão Jalapão Store

Status: implementação autorizada em 2026-09-23. Monorepositório, uma loja, BRL.

Evolução: a spec 002-stock-cost substitui a avaliação por custo corrente abaixo por
custo médio móvel e acrescenta compras/produção. A integração com marketplaces, que aqui era
só preparação (ML-01), foi implementada depois: specs 005, 006 e 011 a 015 (conexão, anúncios,
publicação, pesquisa e importação de vendas). As demais regras permanecem válidas.

## Objetivo e limites
Substituir o armazenamento JSON por PostgreSQL e oferecer uma interface Next.js com
autenticação Django/JWT. Preservar calculadoras, etiquetas, manuais e identidade visual.
Integração Mercado Livre nesta etapa é preparação de modelo/contrato; não publica anúncios,
não sincroniza estoque externo e não recebe pedidos reais automaticamente.

## Requisitos e aceitação
- AUTH-01: login por usuário/senha, renovação e logout; anônimo não acessa dados comerciais.
  Permissões Django distintas para leitura, cadastro e operações financeiras.
- CAT-01: produto com UUID, SKU único, nome, tipo, custo e preço não negativos, ativo/inativo.
  Parâmetros 3D em relação um-para-um; cálculo decimal mantém a fórmula existente.
- INV-01: saldo nunca negativo; toda entrada/saída tem motivo, autor e data. Saldo só muda
  por serviço transacional com bloqueio de linha. Valor do estoque = quantidade × custo atual.
- SALE-01: venda com um ou mais itens, canal (direta, Mercado Livre, Shopee ou outro),
  descontos, taxas e frete suportado pela loja em reais. Custo/preço são snapshots.
  Confirmar baixa estoque de todos os itens atomicamente; repetir a mesma chave não duplica.
- SALE-02: cancelamento único repõe estoque e estorna recebimento, preservando histórico.
- CASH-01: venda pendente não aumenta caixa. Receber registra entrada líquida uma vez.
  Lançamentos manuais positivos com direção entrada/saída; saldo é soma assinada.
- REPORT-01: faturamento, lucro estimado, saldo de caixa, contas a receber e estoque em reais
  são conceitos distintos. Lucro = receita menos descontos, taxas, frete e custo dos itens.
- MIG-01: importar JSON uma vez por ID legado, sem inventar quantidade; importação repetida
  não sobrescreve edições novas. Backup antes do corte e possibilidade de rollback.
- UI-01: login, painel, produtos/3D, estoque, vendas e caixa; erros do backend visíveis,
  estados de carregamento/vazio e prevenção de envio duplo. Ferramentas antigas acessíveis.
- OPS-01: containers independentes, PostgreSQL sem porta pública, migrations, healthchecks,
  segredos fora do Git, build e testes antes do deploy via GitHub.
- ML-01: callback público exato /jalapao-store/callback; sem credenciais OAuth, responder
  explicação de integração indisponível, nunca simular conexão bem-sucedida.

## Decisões iniciais
Estoque em unidades inteiras; custo corrente para avaliação, custo congelado por venda para
lucro. Sem contabilidade fiscal, múltiplas empresas, compras, devolução parcial ou reservas
nesta entrega. Ajustes de estoque não geram caixa automaticamente. Taxas históricas não são
recalculadas por estimativas; o usuário informa os valores efetivos da plataforma.

## Cenários obrigatórios
Venda acima do saldo rejeitada sem efeitos; uma linha inválida reverte toda a venda;
requisição repetida retorna venda existente; mesma chave com conteúdo diferente é rejeitada;
cancelar duas vezes não repõe duas vezes; receber duas vezes não duplica caixa;
trocar custo do produto não altera lucro anterior; usuário sem permissão recebe 403.

## Contrato de implementação (backend)
Antes em `backend/docs/specs/001-commerce.md`, consolidado aqui na spec 017.
- Relações: User 1:N Sale, Movement e CashEntry (autor); Product 1:1 PrintingProfile e Stock;
  Product 1:N Movement, SaleItem e Listing; Sale 1:N SaleItem e CashEntry. PK comercial UUID;
  SKU e legacy_id únicos; IDs externos não substituem a PK local.
- Nenhuma quantidade negativa; linha de venda com quantidade > 0. Venda, estoque e caixa em
  transação única; bloqueio dos produtos em ordem fixa e trava de idempotência no PostgreSQL.
- Histórico imutável na API e no Admin. Editar produto não recalcula vendas antigas.
- Preço 3D calculado no backend em Decimal, arredondado HALF_UP a centavos.
- Taxa estimada da calculadora nunca se soma à taxa real informada na venda.
- OutboxEvent recebe quantidade absoluta e versão no mesmo commit de cada movimento.
- Concorrência provada só em PostgreSQL: dois compradores da última unidade geram uma venda.

## Critérios da interface
Antes em `frontend/docs/specs/001-management-ui.md`, consolidado aqui na spec 017.
- Login inválido mostra erro; válido leva ao painel. Anônimo é levado ao login.
- Cadastro não aceita valores negativos; minutos entre 0 e 59. O backend valida tudo, mesmo
  com o navegador contornado.
- Formulário não é limpo em erro; botão de envio fica desabilitado durante a gravação.
- Listas com estado vazio e paginação; quantidade indisponível mostra o motivo da recusa.
- Nova venda usa chave UUID mantida entre tentativas e renovada após sucesso.
- Lançamento manual de caixa não é apagado: correção por lançamento inverso.
- Dados sensíveis fora do HTML estático e do armazenamento local. Moeda pt-BR; datas no fuso do
  navegador; banco em UTC com contexto comercial America/Sao_Paulo.
- Logotipo legível nos dois temas. Em telas pequenas as tabelas viram cartões (reorganização
  para celular, commit 6563091).
