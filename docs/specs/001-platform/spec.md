# 001 — Gestão Jalapão Store

Status: implementação autorizada em 2026-09-23. Monorepositório, uma loja, BRL.

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
