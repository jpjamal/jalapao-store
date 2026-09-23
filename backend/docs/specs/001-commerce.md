# Contrato do domínio comercial

Requisitos fonte: ../../.. / docs/specs/001-platform/spec.md (AUTH/CAT/INV/SALE/CASH/ML).

## Relações
User 1:N Sale, Movement e CashEntry (autor); Product 1:1 PrintingProfile e Stock;
Product 1:N Movement, SaleItem e Listing; Sale 1:N SaleItem e CashEntry.
PK comercial UUID, SKU e legacy_id únicos. IDs externos não substituem PK local.
OutboxEvent recebe quantidade absoluta e versão no mesmo commit de cada movimento.

## Invariantes
Nenhuma quantidade negativa; linha de venda > 0. Operações de venda, estoque e caixa
atômicas. Locks de produto ordenados, trava de idempotência no PostgreSQL. Imutabilidade
histórica na API e no Admin. Produto pode ser editado sem recalcular vendas antigas.
Preço 3D calculado no backend com Decimal e arredondamento HALF_UP a centavos.
Não adicionar taxa estimada de calculadora a uma taxa real já informada na venda.

## Aceitação implementada
StoreTests cobre fórmula, permissões, JWT, idempotência, rollback multitem, recebimento,
cancelamento, relatórios e importação. ConcurrencyTests exige PostgreSQL e prova uma
única venda para a última unidade com dois compradores concorrentes.

## Evolução Mercado Livre (pendente)
OAuth state + PKCE + segredos criptografados no servidor; worker outbox/inbox deduplicado,
reconciliação periódica; distinguir stock multi-origem e Full. Notificações com resposta
rápida e processamento assíncrono. Não habilitar Listing.sync_enabled antes desses testes.
O callback atual é informativo: não armazena ou troca códigos OAuth.
